"""Insight schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class InsightOut(BaseModel):
    id: int | None = None
    type: Literal["prediction", "warning", "proposal"]
    severity: Literal["info", "low", "medium", "high"]
    title: str
    detail: str = ""
    suggested_action: str = ""
    data: dict[str, Any] = {}
    created_at: float | None = None


class InsightsListOut(BaseModel):
    insights: list[InsightOut]
    limit: int
    offset: int
