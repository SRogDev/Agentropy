"""Ingest service: normalize incoming spans and store them.

Two accepted formats:
- POST /v1/ingest — our simple JSON batch ({"spans": [...]}).
- POST /v1/traces — OTLP receiver: protobuf (SDK default, content-type
  application/x-protobuf) or OTLP/JSON.

Span durations (start/end timestamps) and error status are captured when the
payload carries them, so latency and error-rate stats are real.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)

from ..core.metrics_store import store_span


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


def _duration_ms(start_ns: Any, end_ns: Any) -> float | None:
    try:
        start = int(start_ns)
        end = int(end_ns)
    except (TypeError, ValueError):
        return None
    if start <= 0 or end <= start:
        return None
    return (end - start) / 1e6


def _is_error_json(status: dict[str, Any] | None) -> bool:
    if not status:
        return False
    code = status.get("code")
    return code == 2 or str(code).upper() == "STATUS_CODE_ERROR"


def spans_from_otlp(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten an OTLP/JSON ExportTraceServiceRequest into span records."""
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
                        "duration_ms": _duration_ms(
                            span.get("startTimeUnixNano"),
                            span.get("endTimeUnixNano"),
                        ),
                        "is_error": _is_error_json(span.get("status")),
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
                        "duration_ms": _duration_ms(
                            span.start_time_unix_nano, span.end_time_unix_nano
                        ),
                        "is_error": span.status.code
                        == span.status.StatusCode.STATUS_CODE_ERROR,
                    }
                )
    return out


def ingest_batch(spans: list[dict[str, Any]]) -> int:
    """Store spans from the simple JSON format. Minimal validation."""
    accepted = 0
    for span in spans:
        if not span.get("trace_id") or not span.get("span_id"):
            raise HTTPException(
                status_code=422, detail="Each span needs trace_id and span_id"
            )
        attrs = span.get("attributes", {})
        store_span(
            trace_id=str(span["trace_id"]),
            span_id=str(span["span_id"]),
            name=str(span.get("name", "")),
            attributes=attrs if isinstance(attrs, dict) else {},
            raw=span,
            duration_ms=span.get("duration_ms"),
            is_error=bool(span.get("is_error", False)),
        )
        accepted += 1
    return accepted


def ingest_otlp_body(body: bytes, content_type: str) -> int:
    """Parse an OTLP body (protobuf or JSON) and store the spans."""
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
            duration_ms=span.get("duration_ms"),
            is_error=span.get("is_error", False),
        )
    return len(spans)
