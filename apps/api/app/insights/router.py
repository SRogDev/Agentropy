"""Insight routes.

POST /v1/insights/run executes the LangGraph pipeline on demand.
TODO: also run on a schedule (cron/worker) so insights are fresh without
a manual trigger.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth.dependencies import require_api_key
from .schemas import InsightOut, InsightsListOut
from .service import list_latest, run_insight_pipeline

router = APIRouter()


@router.post("/v1/insights/run", response_model=list[InsightOut])
def run_insights(_auth: None = Depends(require_api_key)) -> list[dict]:
    return run_insight_pipeline()


@router.get("/v1/insights", response_model=InsightsListOut)
def get_insights(
    limit: int = 50,
    offset: int = 0,
    _auth: None = Depends(require_api_key),
) -> dict:
    return list_latest(limit, offset)
