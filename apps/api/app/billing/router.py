"""Billing routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from ..auth.dependencies import get_current_user
from .schemas import CheckoutIn, CheckoutOut
from .service import create_checkout, handle_webhook

router = APIRouter()


@router.post("/v1/billing/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutIn, user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    return create_checkout(payload.tier, user)


@router.post("/v1/billing/webhook")
async def webhook(request: Request) -> dict[str, str]:
    # No auth dependency here — authenticity comes from the Polar signature.
    return await handle_webhook(request)
