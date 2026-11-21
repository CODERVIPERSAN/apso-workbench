"""Protection layer: kill-switch, HITL, confidence, circuit breaker, RBAC."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apso.models import HITLRequest
from apso.store import store


class CircuitBreaker:
    def __init__(self, threshold: int = 3, cooldown_s: int = 300) -> None:
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.failures: dict[str, int] = {}
        self.open_until: dict[str, float] = {}

    def allow(self, name: str) -> bool:
        until = self.open_until.get(name, 0)
        now = datetime.now(timezone.utc).timestamp()
        if until and now < until:
            return False
        if until and now >= until:
            self.failures[name] = 0
            self.open_until.pop(name, None)
        return True

    def success(self, name: str) -> None:
        self.failures[name] = 0

    def failure(self, name: str) -> None:
        self.failures[name] = self.failures.get(name, 0) + 1
        if self.failures[name] >= self.threshold:
            self.open_until[name] = datetime.now(timezone.utc).timestamp() + self.cooldown_s


class Controls:
    ROLES = {"L3 Engineer": {"write", "approve", "read"}, "viewer": {"read"}}

    def __init__(self) -> None:
        self.breaker = CircuitBreaker()

    @property
    def kill_switch(self) -> bool:
        return store.kill_switch

    def engage_kill_switch(self, on: bool = True) -> dict[str, Any]:
        store.kill_switch = on
        return {"kill_switch": store.kill_switch}

    def can_execute(self, agent: str, *, role: str = "L3 Engineer") -> tuple[bool, str]:
        if store.kill_switch:
            return False, "Emergency kill-switch engaged"
        perms = self.ROLES.get(role, set())
        if "read" not in perms:
            return False, "RBAC denied"
        if not self.breaker.allow(agent):
            return False, f"Circuit open for {agent}"
        return True, "ok"

    def score_confidence(self, evidence: dict[str, Any]) -> float:
        score = 0.4
        if evidence.get("logs"):
            score += 0.15
        if evidence.get("spool"):
            score += 0.15
        if evidence.get("sop"):
            score += 0.2
        if evidence.get("code"):
            score += 0.1
        return round(min(score, 0.99), 2)

    def request_hitl(self, action: str, target: str, preview: dict[str, Any]) -> HITLRequest:
        req = HITLRequest(action=action, target=target, preview=preview)
        store.hitl[req.id] = req
        return req

    def resolve_hitl(self, hitl_id: str, approve: bool) -> HITLRequest:
        req = store.hitl[hitl_id]
        req.status = "approved" if approve else "rejected"
        req.resolved_at = datetime.now(timezone.utc)
        return req


controls = Controls()
