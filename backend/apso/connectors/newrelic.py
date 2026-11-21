"""New Relic GraphQL / NRQL connector (stub → real when NR_API_KEY set)."""

from __future__ import annotations

import os
from typing import Any

from apso.store import store

API_KEY = os.getenv("NR_API_KEY", "")
ACCOUNT = os.getenv("NR_ACCOUNT_ID", "")


def live() -> bool:
    return bool(API_KEY)


def search_logs(query: str, limit: int = 50) -> list[dict[str, Any]]:
    q = query.lower()
    hits = [row for row in store.nr_logs if q in row.get("message", "").lower() or q in row.get("app", "").lower()]
    if not hits and query:
        # broad fallback: return recent errors
        hits = [row for row in store.nr_logs if row.get("level") in ("ERROR", "WARN")]
    return hits[:limit]


def get_app_errors(app: str) -> dict[str, Any]:
    rows = [r for r in store.nr_logs if r.get("app") == app and r.get("level") == "ERROR"]
    return {"app": app, "error_count": len(rows), "samples": rows[:10]}
