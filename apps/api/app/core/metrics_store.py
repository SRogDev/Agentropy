"""Metrics store — SQLite stub for spans and insights.

TODO: replace with ClickHouse for production trace storage. The functions
below are the seam: keep their signatures, swap the implementation.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import sqlite3

from .config import settings


def _connect() -> sqlite3.Connection:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                span_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                attributes TEXT NOT NULL DEFAULT '{}',
                raw TEXT NOT NULL DEFAULT '{}',
                duration_ms REAL,
                is_error INTEGER NOT NULL DEFAULT 0,
                received_at REAL NOT NULL
            )
            """
        )
        # Migrations for DBs created by earlier skeleton versions.
        _ensure_column(conn, "spans", "duration_ms", "REAL")
        _ensure_column(conn, "spans", "is_error", "INTEGER NOT NULL DEFAULT 0")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spans_received ON spans(received_at DESC)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,              -- prediction | warning | proposal
                severity TEXT NOT NULL,          -- info | low | medium | high
                title TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                suggested_action TEXT NOT NULL DEFAULT '',
                data TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_insights_created ON insights(created_at DESC)"
        )


# ---------------------------------------------------------------------------
# Spans
# ---------------------------------------------------------------------------


def store_span(
    trace_id: str,
    span_id: str,
    name: str,
    attributes: dict[str, Any],
    raw: dict[str, Any],
    duration_ms: float | None = None,
    is_error: bool = False,
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO spans (trace_id, span_id, name, attributes, raw,"
            " duration_ms, is_error, received_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                trace_id,
                span_id,
                name,
                json.dumps(attributes),
                json.dumps(raw),
                duration_ms,
                1 if is_error else 0,
                time.time(),
            ),
        )


def list_spans(limit: int, offset: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT trace_id, span_id, name, attributes, duration_ms, is_error,"
            " received_at FROM spans"
            " ORDER BY received_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [
        {
            "trace_id": r["trace_id"],
            "span_id": r["span_id"],
            "name": r["name"],
            "attributes": json.loads(r["attributes"]),
            "duration_ms": r["duration_ms"],
            "is_error": bool(r["is_error"]),
            "received_at": r["received_at"],
        }
        for r in rows
    ]


def recent_spans(limit: int = 2000) -> list[dict[str, Any]]:
    """Newest-first spans for the insight engine."""
    return list_spans(limit, 0)


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------


def store_insight(insight: dict[str, Any]) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO insights (type, severity, title, detail,"
            " suggested_action, data, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                insight["type"],
                insight["severity"],
                insight["title"],
                insight.get("detail", ""),
                insight.get("suggested_action", ""),
                json.dumps(insight.get("data", {})),
                time.time(),
            ),
        )
        return cur.lastrowid


def list_insights(limit: int, offset: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, type, severity, title, detail, suggested_action, data,"
            " created_at FROM insights"
            " ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "type": r["type"],
            "severity": r["severity"],
            "title": r["title"],
            "detail": r["detail"],
            "suggested_action": r["suggested_action"],
            "data": json.loads(r["data"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]
