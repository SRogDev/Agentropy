"""Billing service — Polar integration.

Tiers: starter $19/mo, pro $49/mo (unlimited seats on both).

Setup required in the Polar dashboard BEFORE this works:
1. Create an organization and two subscription products
   ("Agentropy Starter" $19/mo, "Agentropy Pro" $49/mo).
2. Copy the product IDs into POLAR_STARTER_PRODUCT_ID / POLAR_PRO_PRODUCT_ID.
3. Create an access token -> POLAR_ACCESS_TOKEN.
4. Add a webhook endpoint pointing at POST /v1/billing/webhook and copy its
   signing secret -> POLAR_WEBHOOK_SECRET.

Without these env vars every billing route returns 503 with a clear message.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

import httpx
from fastapi import HTTPException, Request

from ..core.config import settings
from ..core.supabase_client import require_supabase

_TIERS = {"starter": 19, "pro": 49}


def _require_polar() -> None:
    if not settings.polar_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Polar is not configured. Set POLAR_ACCESS_TOKEN, "
                "POLAR_STARTER_PRODUCT_ID and POLAR_PRO_PRODUCT_ID "
                "(create the products in the Polar dashboard first)."
            ),
        )


def create_checkout(tier: str, user: dict[str, Any]) -> dict[str, str]:
    _require_polar()
    product_id = (
        settings.polar_starter_product_id
        if tier == "starter"
        else settings.polar_pro_product_id
    )
    try:
        resp = httpx.post(
            f"{settings.polar_server.rstrip('/')}/v1/checkouts",
            headers={"Authorization": f"Bearer {settings.polar_access_token}"},
            json={
                "products": [product_id],
                "success_url": settings.polar_success_url,
                "customer_email": user.get("email"),
                "metadata": {"user_id": user.get("id"), "tier": tier},
            },
            timeout=20,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Polar checkout failed: {exc}"
        )
    data = resp.json()
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=502, detail="Polar returned no checkout URL")
    return {"checkout_url": url, "tier": tier}


def _verify_webhook_signature(request: Request, body: bytes) -> None:
    """Standard-webhooks (Svix-style) verification used by Polar."""
    if not settings.polar_webhook_secret:
        raise HTTPException(status_code=503, detail="POLAR_WEBHOOK_SECRET not set")
    webhook_id = request.headers.get("webhook-id", "")
    timestamp = request.headers.get("webhook-timestamp", "")
    signature = request.headers.get("webhook-signature", "")
    if not (webhook_id and timestamp and signature):
        raise HTTPException(status_code=401, detail="Missing webhook signature headers")
    signed = f"{webhook_id}.{timestamp}.{body.decode()}".encode()
    expected = base64.b64encode(
        hmac.new(settings.polar_webhook_secret.encode(), signed, hashlib.sha256).digest()
    ).decode()
    provided = [s.split(",", 1)[1] for s in signature.split(" ") if s.startswith("v1,")]
    if not any(hmac.compare_digest(expected, p) for p in provided):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


async def handle_webhook(request: Request) -> dict[str, str]:
    """Validate the Polar signature and upsert the subscription in Supabase."""
    body = await request.body()
    _verify_webhook_signature(request, body)
    import json

    event = json.loads(body)
    event_type = event.get("type", "")
    data = event.get("data", {}) or {}

    # We only care about subscription lifecycle events.
    if not event_type.startswith("subscription."):
        return {"status": "ignored", "event": event_type}

    client = require_supabase()
    metadata = data.get("metadata", {}) or {}
    workspace_id = metadata.get("workspace_id")
    row = {
        "workspace_id": workspace_id,
        "polar_customer_id": data.get("customer_id"),
        "polar_subscription_id": data.get("id"),
        "tier": metadata.get("tier"),
        "status": data.get("status"),
        "current_period_end": data.get("current_period_end"),
    }
    row = {k: v for k, v in row.items() if v is not None}
    try:
        # Upsert on the Polar subscription id (unique).
        client.table("subscriptions").upsert(
            row, on_conflict="polar_subscription_id"
        ).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Subscription sync failed: {exc}")
    return {"status": "ok", "event": event_type}
