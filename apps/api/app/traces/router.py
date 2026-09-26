"""Trace query routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth.dependencies import require_api_key
from .schemas import TracesOut
from .service import query_spans

router = APIRouter()


@router.get("/v1/traces", response_model=TracesOut)
def get_traces(
    limit: int = 50,
    offset: int = 0,
    _auth: None = Depends(require_api_key),
) -> dict:
    return query_spans(limit, offset)
