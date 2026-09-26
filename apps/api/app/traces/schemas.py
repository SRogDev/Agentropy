"""Trace query schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SpanOut(BaseModel):
    trace_id: str
    span_id: str
    name: str
    attributes: dict[str, Any]
    duration_ms: float | None = None
    is_error: bool = False
    received_at: float


class TracesOut(BaseModel):
    spans: list[SpanOut]
    limit: int
    offset: int
