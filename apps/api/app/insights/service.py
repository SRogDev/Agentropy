"""Insight pipeline orchestration."""

from __future__ import annotations

from typing import Any

from ..core import metrics_store
from .graph import build_graph

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_insight_pipeline() -> list[dict[str, Any]]:
    """Run the full LangGraph pipeline and return the persisted insights."""
    result = _get_graph().invoke({})
    ids = result.get("persisted_ids", [])
    insights = result.get("insights", [])
    out = []
    for insight, insight_id in zip(insights, ids):
        row = dict(insight)
        row["id"] = insight_id
        out.append(row)
    return out


def list_latest(limit: int, offset: int) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    return {
        "insights": metrics_store.list_insights(limit, offset),
        "limit": limit,
        "offset": offset,
    }
