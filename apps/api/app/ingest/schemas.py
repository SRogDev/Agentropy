"""Ingest request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestBatch(BaseModel):
    """Our simple JSON batch format: {"spans": [{trace_id, span_id, ...}]}."""

    spans: list[dict[str, Any]] = Field(default_factory=list)
