"""Supabase client — the SaaS database.

Holds users (via Supabase Auth), workspaces, API keys, subscriptions and
usage events. This is NOT the metrics database (spans live in SQLite for now,
TODO: ClickHouse).

If SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are missing, get_client()
returns None and the dependent routes answer 503 with a clear message.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from .config import settings


_client: Any = None
_tried_init = False


def get_client() -> Any | None:
    global _client, _tried_init
    if _tried_init:
        return _client
    _tried_init = True
    if not settings.supabase_configured:
        return None
    try:
        from supabase import create_client

        _client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
    except Exception:
        _client = None
    return _client


def require_supabase() -> Any:
    """Return the client or raise an honest 503."""
    client = get_client()
    if client is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase is not configured. Set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY, then apply supabase/migrations/001_init.sql "
                "in your Supabase project."
            ),
        )
    return client
