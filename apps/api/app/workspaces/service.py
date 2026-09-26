"""Workspace service — projects and API keys, Supabase-backed.

API keys are generated as ``ao_live_<random>``; only the sha256 hash is
stored. The plaintext is returned once at creation and never again.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from fastapi import HTTPException

from ..core.supabase_client import require_supabase


def _new_key() -> tuple[str, str]:
    plaintext = f"ao_live_{secrets.token_urlsafe(32)}"
    digest = hashlib.sha256(plaintext.encode()).hexdigest()
    return plaintext, digest


def create_workspace(user: dict[str, Any], name: str) -> dict[str, Any]:
    client = require_supabase()
    try:
        ws = (
            client.table("workspaces")
            .insert({"owner_id": user["id"], "name": name})
            .execute()
            .data[0]
        )
        plaintext, digest = _new_key()
        key_row = (
            client.table("api_keys")
            .insert(
                {
                    "workspace_id": ws["id"],
                    "key_hash": digest,
                    "name": "default",
                }
            )
            .execute()
            .data[0]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workspace creation failed: {exc}")
    return {
        "id": ws["id"],
        "name": ws["name"],
        "created_at": ws["created_at"],
        "api_key": {"id": key_row["id"], "key": plaintext},
    }


def list_workspaces(user: dict[str, Any]) -> list[dict[str, Any]]:
    client = require_supabase()
    res = (
        client.table("workspaces")
        .select("id,name,created_at")
        .eq("owner_id", user["id"])
        .order("created_at")
        .execute()
    )
    return res.data or []


def create_api_key(user: dict[str, Any], workspace_id: str, name: str) -> dict[str, Any]:
    client = require_supabase()
    owned = (
        client.table("workspaces")
        .select("id")
        .eq("id", workspace_id)
        .eq("owner_id", user["id"])
        .limit(1)
        .execute()
    )
    if not owned.data:
        raise HTTPException(status_code=404, detail="Workspace not found")
    plaintext, digest = _new_key()
    row = (
        client.table("api_keys")
        .insert({"workspace_id": workspace_id, "key_hash": digest, "name": name})
        .execute()
        .data[0]
    )
    return {
        "id": row["id"],
        "name": row["name"],
        "key": plaintext,
        "created_at": row["created_at"],
    }


def revoke_api_key(user: dict[str, Any], workspace_id: str, key_id: str) -> dict[str, bool]:
    client = require_supabase()
    owned = (
        client.table("workspaces")
        .select("id")
        .eq("id", workspace_id)
        .eq("owner_id", user["id"])
        .limit(1)
        .execute()
    )
    if not owned.data:
        raise HTTPException(status_code=404, detail="Workspace not found")
    client.table("api_keys").update({"revoked": True}).eq("id", key_id).eq(
        "workspace_id", workspace_id
    ).execute()
    return {"revoked": True}
