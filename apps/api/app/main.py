"""Agent Observability API — skeleton.

Commercial core of the platform. This skeleton implements:

- Span ingestion in two formats:
    * POST /v1/ingest — our simple JSON batch format ({"spans": [...]}).
    * POST /v1/traces — OTLP/JSON (what the SDKs send via the OTel exporter).
- SQLite persistence.
- API-key auth stub.

Honest TODOs (do not ship as-is):
- TODO: replace SQLite with ClickHouse for production trace storage.
- TODO: real key management — hashed, per-project keys with scopes,
  rotation and revocation, stored in Postgres. Never ship the dev default.
- TODO: multi-tenancy, rate limiting, retention policies, Stripe billing.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

# OTLP protobuf decoding (the OTel SDKs send protobuf by default).
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# TODO: real key management (see module docstring). The dev default exists only
# so the skeleton runs locally with zero setup.
API_KEY = os.environ.get("API_KEY", "dev-key")
DB_PATH = os.environ.get(
    "DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "spans.db")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Agent Observability API", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Storage — SQLite stub
# ---------------------------------------------------------------------------
# TODO: replace with ClickHouse. SQLite is here only so the skeleton runs
# with zero infrastructure. The store_span()/list_spans() boundary is the seam
# where the ClickHouse client will plug in.


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                span_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                attributes TEXT NOT NULL DEFAULT '{}',
                raw TEXT NOT NULL DEFAULT '{}',
                received_at REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spans_received ON spans(received_at DESC)"
        )


def store_span(
    trace_id: str,
    span_id: str,
    name: str,
    attributes: dict[str, Any],
    raw: dict[str, Any],
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO spans (trace_id, span_id, name, attributes, raw, received_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                trace_id,
                span_id,
                name,
                json.dumps(attributes),
                json.dumps(raw),
                time.time(),
            ),
        )


def list_spans(limit: int, offset: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT trace_id, span_id, name, attributes, received_at FROM spans"
            " ORDER BY received_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [
        {
            "trace_id": r["trace_id"],
            "span_id": r["span_id"],
            "name": r["name"],
            "attributes": json.loads(r["attributes"]),
            "received_at": r["received_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Auth — stub
# ---------------------------------------------------------------------------


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    # TODO: validate against a real key store (hashed, per-project keys).
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


# ---------------------------------------------------------------------------
# Ingest models
# ---------------------------------------------------------------------------


class IngestBatch(BaseModel):
    """Our simple JSON batch format: {"spans": [{trace_id, span_id, ...}]}."""

    spans: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OTLP/JSON parsing (what the OTel SDKs actually send)
# ---------------------------------------------------------------------------


def _otlp_value(value: dict[str, Any]) -> Any:
    # OTLP JSON encodes int/double as strings.
    if "stringValue" in value:
        return value["stringValue"]
    if "boolValue" in value:
        return value["boolValue"]
    if "intValue" in value:
        return int(value["intValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "arrayValue" in value:
        return [_otlp_value(v) for v in value["arrayValue"].get("values", [])]
    if "kvlistValue" in value:
        return {
            item["key"]: _otlp_value(item.get("value", {}))
            for item in value["kvlistValue"].get("values", [])
            if "key" in item
        }
    return None


def _otlp_attrs(attrs: list[dict[str, Any]] | None) -> dict[str, Any]:
    return {
        a["key"]: _otlp_value(a.get("value", {}))
        for a in (attrs or [])
        if "key" in a
    }


def spans_from_otlp(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten an OTLP/JSON ExportTraceServiceRequest into our span records."""
    out: list[dict[str, Any]] = []
    for rs in payload.get("resourceSpans", []):
        resource_attrs = _otlp_attrs(rs.get("resource", {}).get("attributes"))
        for scope in rs.get("scopeSpans", []):
            for span in scope.get("spans", []):
                attributes = dict(resource_attrs)
                attributes.update(_otlp_attrs(span.get("attributes")))
                out.append(
                    {
                        "trace_id": span.get("traceId", ""),
                        "span_id": span.get("spanId", ""),
                        "name": span.get("name", ""),
                        "attributes": attributes,
                    }
                )
    return out


def _proto_value(value: Any) -> Any:
    kind = value.WhichOneof("value")
    if kind == "string_value":
        return value.string_value
    if kind == "bool_value":
        return value.bool_value
    if kind == "int_value":
        return value.int_value
    if kind == "double_value":
        return value.double_value
    if kind == "array_value":
        return [_proto_value(v) for v in value.array_value.values]
    if kind == "kvlist_value":
        return {kv.key: _proto_value(kv.value) for kv in value.kvlist_value.values}
    return None


def spans_from_otlp_proto(body: bytes) -> list[dict[str, Any]]:
    """Flatten an OTLP/protobuf ExportTraceServiceRequest into span records."""
    request = ExportTraceServiceRequest()
    request.ParseFromString(body)
    out: list[dict[str, Any]] = []
    for rs in request.resource_spans:
        resource_attrs = {a.key: _proto_value(a.value) for a in rs.resource.attributes}
        for scope in rs.scope_spans:
            for span in scope.spans:
                attributes = dict(resource_attrs)
                attributes.update(
                    {a.key: _proto_value(a.value) for a in span.attributes}
                )
                out.append(
                    {
                        "trace_id": span.trace_id.hex(),
                        "span_id": span.span_id.hex(),
                        "name": span.name,
                        "attributes": attributes,
                    }
                )
    return out


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "agent-observability-api", "version": "0.1.0"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ingest")
def ingest(batch: IngestBatch, _auth: None = Depends(require_api_key)) -> dict[str, int]:
    """Accept a simple JSON batch of spans. Minimal validation: every span
    must carry trace_id and span_id."""
    accepted = 0
    for span in batch.spans:
        if not span.get("trace_id") or not span.get("span_id"):
            raise HTTPException(
                status_code=422, detail="Each span needs trace_id and span_id"
            )
        store_span(
            trace_id=str(span["trace_id"]),
            span_id=str(span["span_id"]),
            name=str(span.get("name", "")),
            attributes=span.get("attributes", {})
            if isinstance(span.get("attributes"), dict)
            else {},
            raw=span,
        )
        accepted += 1
    return {"accepted": accepted}


@app.post("/v1/traces")
async def ingest_otlp(
    request: Request, _auth: None = Depends(require_api_key)
) -> dict[str, int]:
    """OTLP trace receiver — the endpoint the SDKs' OTel exporters hit.

    Accepts both OTLP/protobuf (the SDK default, content-type
    application/x-protobuf) and OTLP/JSON.
    """
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    try:
        if "json" in content_type:
            payload = json.loads(body)
            spans = spans_from_otlp(payload)
            if not spans and "resourceSpans" not in payload:
                raise HTTPException(
                    status_code=400, detail="Expected OTLP/JSON with resourceSpans"
                )
        else:
            spans = spans_from_otlp_proto(body)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unparseable OTLP payload: {exc}")
    for span in spans:
        store_span(
            trace_id=span["trace_id"],
            span_id=span["span_id"],
            name=span["name"],
            attributes=span["attributes"],
            raw=span,
        )
    return {"accepted": len(spans)}


@app.get("/v1/traces")
def get_traces(
    limit: int = 50,
    offset: int = 0,
    _auth: None = Depends(require_api_key),
) -> dict[str, Any]:
    # TODO: filtering by service, time range, trace_id; cursor pagination.
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {"spans": list_spans(limit, offset), "limit": limit, "offset": offset}
