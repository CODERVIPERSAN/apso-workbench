"""Paige-style intake: urgent vs less urgent + incident context assembly."""

from __future__ import annotations

from typing import Any

from apso.models import Incident


def classify_urgency(incident: Incident) -> str:
    """Mirror Paige triage: high vs low for orchestrator parallelization."""
    if incident.priority in ("1", "2"):
        return "high"
    text = f"{incident.short_description} {incident.description}".lower()
    if any(k in text for k in ("abend", "outage", "p1", "critical", "down")):
        return "high"
    return "low"


def assemble_context(incident: Incident) -> dict[str, Any]:
    """Precomputed working set (Paige Incident Context pattern) — not a summary."""
    return {
        "incident": incident.model_dump(),
        "urgency": classify_urgency(incident),
        "entities": {
            "ci": incident.ci,
            "assignment_group": incident.assignment_group,
            "value_stream": incident.value_stream,
            "job_name": incident.ci if incident.ci.isupper() and len(incident.ci) <= 8 or "_" not in incident.ci else incident.ci,
        },
        "signals": {
            "from_servicenow": True,
            "from_pagerduty": incident.caller.startswith("nr.") or "alert" in incident.caller,
        },
    }
