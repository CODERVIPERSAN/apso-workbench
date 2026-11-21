"""APSO Cognitive Bridge — retrieve / contribute."""

from __future__ import annotations

from typing import Any

from apso.store import store


def search(query: str) -> dict[str, Any]:
    q = query.lower()
    sops = [s for s in store.sops if q in s["title"].lower() or q in s["body"].lower() or q in s["id"].lower()]
    playbooks = [p for p in store.playbooks if q in p["title"].lower() or q in p["id"].lower()]
    incidents = [
        i.model_dump()
        for i in store.incidents.values()
        if q in i.number.lower() or q in i.short_description.lower()
    ]
    return {"sops": sops, "playbooks": playbooks, "incidents": incidents[:10]}


def contribute(outcome: dict[str, Any]) -> None:
    """Lightweight learning hook — append SOP note from outcomes."""
    if outcome.get("sop_update"):
        store.sops.append(outcome["sop_update"])
