"""ASW-style agent gateway — circuit breaker, timeout, fail-soft."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from apso.governance.controls import controls
from apso.models import StageResult


def wrap_node(name: str, fn: Callable[[dict[str, Any]], StageResult]) -> Callable[[dict[str, Any]], StageResult]:
    def wrapped(state: dict[str, Any]) -> StageResult:
        ok, reason = controls.can_execute(name)
        if not ok:
            return StageResult(
                stage=state.get("stage", "unknown"),
                agent=name,
                summary=f"Gateway blocked {name}: {reason}",
                confidence=0.0,
            )
        start = time.time()
        try:
            result = fn(state)
            controls.breaker.success(name)
            return result
        except Exception as exc:  # noqa: BLE001
            controls.breaker.failure(name)
            return StageResult(
                stage=state.get("stage", "unknown"),
                agent=name,
                summary=f"I encountered an issue while processing through {name}: {exc}",
                confidence=0.0,
                evidence={"error": str(exc), "latency_ms": int((time.time() - start) * 1000)},
            )

    return wrapped
