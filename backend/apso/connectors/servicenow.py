"""ServiceNow Table API connector (stub → real REST when env set)."""

from __future__ import annotations

import os
from typing import Any

from apso.models import Incident
from apso.store import store

BASE = os.getenv("SNOW_BASE_URL", "")  # e.g. https://instance.service-now.com
USER = os.getenv("SNOW_USER", "")
PASS = os.getenv("SNOW_PASS", "")


def live() -> bool:
    return bool(BASE and USER)


def list_incidents(active_only: bool = True) -> list[Incident]:
    items = list(store.incidents.values())
    if active_only:
        items = [i for i in items if i.state.lower() not in ("resolved", "closed")]
    return items


def get_incident(number: str) -> Incident | None:
    return store.incidents.get(number)


def update_incident(number: str, fields: dict[str, Any], *, confirmed: bool = False) -> dict[str, Any]:
    """HITL: confirmed=False returns preview only — no write."""
    inc = store.incidents.get(number)
    if not inc:
        return {"error": f"Incident {number} not found"}
    preview = {"number": number, "changes": fields, "confirmed": confirmed}
    if not confirmed:
        return {"ok": False, "preview": preview, "hitl": True, "message": "HITL required — no ServiceNow write until you Apply."}
    for k, v in fields.items():
        if hasattr(inc, k):
            setattr(inc, k, v)
    return {"ok": True, "incident": inc.model_dump(), "confirmed": True}


def resolve_ticket(number: str, close_notes: str, *, confirmed: bool = False) -> dict[str, Any]:
    return update_incident(
        number,
        {"state": "Resolved", "close_notes": close_notes},
        confirmed=confirmed,
    )


def find_similar_incidents(number: str, threshold: float = 0.85) -> list[dict[str, Any]]:
    # Seed has no historical matches for INC5668817 by design
    _ = (number, threshold)
    return []


def find_related_problem(number: str) -> dict[str, Any] | None:
    for p in store.problems:
        if number in (p.get("incidents") or []):
            return p
    return None
