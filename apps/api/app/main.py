"""Agentropy API — commercial core of the platform.

Screaming architecture: each domain owns its router/service/schemas.
This module only wires routers together.

Domains:
- ingest     — span ingestion (simple JSON batch + OTLP receiver)
- traces     — trace query
- insights   — LangGraph insight engine (predictions + proposals)
- billing    — Polar checkout + webhooks
- workspaces — Supabase-backed projects + API keys
- auth       — X-API-Key (machine) and Supabase JWT (human) dependencies

Honest TODOs (do not ship as-is):
- TODO: replace SQLite metrics store with ClickHouse (see core/metrics_store.py).
- TODO: run the insight pipeline on a schedule, not just on demand.
- TODO: per-workspace scoping for spans/insights once tenancy lands.
- TODO: rate limiting, retention policies, key scopes/rotation.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .billing.router import router as billing_router
from .core.metrics_store import init_db
from .ingest.router import router as ingest_router
from .insights.router import router as insights_router
from .traces.router import router as traces_router
from .workspaces.router import router as workspaces_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Agentropy API", version="0.2.0", lifespan=lifespan)

app.include_router(ingest_router)
app.include_router(traces_router)
app.include_router(insights_router)
app.include_router(billing_router)
app.include_router(workspaces_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "agentropy-api", "version": "0.2.0"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
