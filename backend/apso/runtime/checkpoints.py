"""Cursor-like checkpoints — snapshot before risky Apply (HITL writes)."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from apso.store import store


class CheckpointStore:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def create(self, *, reason: str, incident_number: str | None = None, payload: dict[str, Any] | None = None) -> str:
        cid = f"ckpt-{uuid4().hex[:10]}"
        snap = {
            "id": cid,
            "reason": reason,
            "incident_number": incident_number,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
            "incidents": {k: v.model_dump() for k, v in store.incidents.items()},
            "jobs": copy.deepcopy(store.jobs),
        }
        self._items[cid] = snap
        return cid

    def get(self, checkpoint_id: str) -> dict[str, Any] | None:
        return self._items.get(checkpoint_id)

    def restore(self, checkpoint_id: str) -> dict[str, Any]:
        snap = self._items.get(checkpoint_id)
        if not snap:
            return {"ok": False, "error": "checkpoint not found"}
        from apso.models import Incident

        store.incidents = {k: Incident(**v) for k, v in snap["incidents"].items()}
        store.jobs = copy.deepcopy(snap["jobs"])
        return {"ok": True, "restored": checkpoint_id, "reason": snap["reason"]}

    def list(self) -> list[dict[str, Any]]:
        return [
            {"id": v["id"], "reason": v["reason"], "incident_number": v.get("incident_number"), "created_at": v["created_at"]}
            for v in self._items.values()
        ]


checkpoints = CheckpointStore()
