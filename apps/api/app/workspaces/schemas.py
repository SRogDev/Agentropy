"""Workspace schemas."""

from __future__ import annotations

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceOut(BaseModel):
    id: str
    name: str
    created_at: str


class ApiKeyCreate(BaseModel):
    name: str = "default"


class ApiKeyOut(BaseModel):
    id: str
    name: str
    key: str  # plaintext — shown ONCE at creation
    created_at: str


class ApiKeyMeta(BaseModel):
    id: str
    name: str
    revoked: bool
    created_at: str
