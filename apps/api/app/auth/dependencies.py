"""Auth dependencies.

Two mechanisms:

1. ``require_api_key`` — for machine-to-machine ingest/query traffic
   (``X-API-Key`` header). Accepts the ``API_KEY`` env dev key, and — when
   Supabase is configured — hashed per-workspace keys from the ``api_keys``
   table. TODO: scopes, rotation.
2. ``get_current_user`` — for the SaaS dashboard/API surface. Validates a
   Supabase JWT from the ``Authorization: Bearer`` header (HS256 with
   ``SUPABASE_JWT_SECRET``). 503 when Supabase auth is not configured.
"""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Depends, Header, HTTPException

from ..core.config import settings
from ..core.supabase_client import get_client

_SUPABASE_USER_503 = (
    "Supabase auth is not configured. Set SUPABASE_URL and SUPABASE_JWT_SECRET."
)


def _lookup_workspace_key(provided: str) -> bool:
    """Check a sha256-hashed key against the Supabase api_keys table."""
    client = get_client()
    if client is None:
        return False
    digest = hashlib.sha256(provided.encode()).hexdigest()
    try:
        res = (
            client.table("api_keys")
            .select("id")
            .eq("key_hash", digest)
            .eq("revoked", False)
            .limit(1)
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")
    if x_api_key == settings.api_key:
        return
    if _lookup_workspace_key(x_api_key):
        return
    raise HTTPException(status_code=401, detail="Invalid X-API-Key")


def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Validate a Supabase JWT and return the user claims."""
    if not settings.supabase_auth_configured:
        raise HTTPException(status_code=503, detail=_SUPABASE_USER_503)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401, detail="Missing Authorization: Bearer token"
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        import jwt

        claims = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
    return {"id": claims["sub"], "email": claims.get("email")}


# Re-export for routers: `user = Depends(get_current_user)`.
require_user = Depends(get_current_user)
