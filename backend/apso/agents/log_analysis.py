"""Log analysis — New Relic connector + local correlation."""

from __future__ import annotations

from typing import Any

from apso.connectors import newrelic
from apso.models import StageResult, ToolCall


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    query = incident.get("ci") or incident.get("short_description") or ""
    t = ToolCall(name="search_nr_logs", args={"query": query})
    logs = newrelic.search_logs(query)
    t.result = logs
    errors = [l for l in logs if l.get("level") == "ERROR"]
    summary = (
        f"Log analysis: {len(logs)} events, {len(errors)} errors. "
        + (errors[0]["message"] if errors else "No ERROR-level hits.")
    )
    return StageResult(
        stage="diagnose",
        agent="log_analysis",
        summary=summary,
        confidence=0.8 if errors else 0.5,
        tools_used=[t],
        evidence={"logs": logs},
    )
