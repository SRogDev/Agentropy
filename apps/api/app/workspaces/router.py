"""Workspace routes (Supabase JWT required)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..auth.dependencies import get_current_user
from .schemas import ApiKeyCreate, WorkspaceCreate
from .service import (
    create_api_key,
    create_workspace,
    list_workspaces,
    revoke_api_key,
)

router = APIRouter()


@router.post("/v1/workspaces")
def post_workspace(
    payload: WorkspaceCreate, user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    return create_workspace(user, payload.name)


@router.get("/v1/workspaces")
def get_workspaces(user: dict[str, Any] = Depends(get_current_user)) -> list[dict]:
    return list_workspaces(user)


@router.post("/v1/workspaces/{workspace_id}/keys")
def post_key(
    workspace_id: str,
    payload: ApiKeyCreate,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return create_api_key(user, workspace_id, payload.name)


@router.delete("/v1/workspaces/{workspace_id}/keys/{key_id}")
def delete_key(
    workspace_id: str,
    key_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, bool]:
    return revoke_api_key(user, workspace_id, key_id)
