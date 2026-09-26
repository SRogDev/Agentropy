"""Trace query service."""

from __future__ import annotations

from ..core.metrics_store import list_spans


def query_spans(limit: int, offset: int) -> dict:
    # TODO: filtering by service, time range, trace_id; cursor pagination.
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {"spans": list_spans(limit, offset), "limit": limit, "offset": offset}
