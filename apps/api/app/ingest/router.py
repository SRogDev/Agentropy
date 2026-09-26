"""Ingest routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..auth.dependencies import require_api_key
from .schemas import IngestBatch
from .service import ingest_batch, ingest_otlp_body

router = APIRouter()


@router.post("/v1/ingest")
def ingest(batch: IngestBatch, _auth: None = Depends(require_api_key)) -> dict[str, int]:
    return {"accepted": ingest_batch(batch.spans)}


@router.post("/v1/traces")
async def ingest_otlp(
    request: Request, _auth: None = Depends(require_api_key)
) -> dict[str, int]:
    """OTLP trace receiver — the endpoint the SDKs' OTel exporters hit."""
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    return {"accepted": ingest_otlp_body(body, content_type)}
