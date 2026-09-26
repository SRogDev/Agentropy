"""Centralized environment configuration.

Every integration degrades honestly: if the env vars for an optional
integration (Supabase, Polar, LLM) are missing, the dependent routes return
HTTP 503 with a clear message instead of faking behavior.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass
class Settings:
    # Ingest auth (dev default only — never ship this).
    api_key: str = field(default_factory=lambda: _env("API_KEY", "dev-key"))

    # Metrics store (SQLite stub; TODO: ClickHouse).
    db_path: str = field(
        default_factory=lambda: _env(
            "DB_PATH",
            str(Path(__file__).resolve().parent.parent.parent / "data" / "spans.db"),
        )
    )

    # Supabase — the SaaS database (users, workspaces, keys, subscriptions).
    supabase_url: str = field(default_factory=lambda: _env("SUPABASE_URL"))
    supabase_service_role_key: str = field(
        default_factory=lambda: _env("SUPABASE_SERVICE_ROLE_KEY")
    )
    supabase_jwt_secret: str = field(
        default_factory=lambda: _env("SUPABASE_JWT_SECRET")
    )

    # Polar — billing.
    polar_access_token: str = field(default_factory=lambda: _env("POLAR_ACCESS_TOKEN"))
    polar_webhook_secret: str = field(
        default_factory=lambda: _env("POLAR_WEBHOOK_SECRET")
    )
    polar_starter_product_id: str = field(
        default_factory=lambda: _env("POLAR_STARTER_PRODUCT_ID")
    )
    polar_pro_product_id: str = field(
        default_factory=lambda: _env("POLAR_PRO_PRODUCT_ID")
    )
    polar_server: str = field(
        default_factory=lambda: _env("POLAR_SERVER", "https://api.polar.sh")
    )
    polar_success_url: str = field(
        default_factory=lambda: _env("POLAR_SUCCESS_URL", "http://localhost:3000/dashboard")
    )

    # Optional LLM refinement for insight wording (rules are the default).
    # Via OpenRouter — a mid-tier model is plenty for polishing prose.
    openrouter_api_key: str = field(default_factory=lambda: _env("OPENROUTER_API_KEY"))
    openrouter_model: str = field(
        default_factory=lambda: _env("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    )

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def supabase_auth_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_jwt_secret)

    @property
    def polar_configured(self) -> bool:
        return bool(
            self.polar_access_token
            and self.polar_starter_product_id
            and self.polar_pro_product_id
        )


settings = Settings()
