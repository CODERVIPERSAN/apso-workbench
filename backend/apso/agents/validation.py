"""Testing and validation — health check after remediation."""

from __future__ import annotations

from typing import Any

from apso.connectors import mainframe, newrelic
from apso.models import StageResult, ToolCall


def health_check(job: str, app: str | None = None) -> dict[str, Any]:
    spool = mainframe.job_spool(job) if job else {}
    errors = newrelic.get_app_errors(app or "payroll-batch")
    ok = spool.get("last_status") in ("CC 0000", "COMPLETED") or spool.get("abend") is None and "error" not in spool
    # If still ABEND, not healthy
    if spool.get("abend"):
        ok = False
    return {
        "healthy": ok,
        "job_status": spool.get("last_status"),
        "abend": spool.get("abend"),
        "app_errors": errors.get("error_count", 0),
    }


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    job = incident.get("ci") or ""
    t = ToolCall(name="health_check", args={"job": job})
    result = health_check(job)
    t.result = result
    summary = (
        "Verify OK — job healthy."
        if result["healthy"]
        else f"Verify pending — job status={result.get('job_status')} abend={result.get('abend')}. Apply remediation first."
    )
    return StageResult(
        stage="verify",
        agent="validation",
        summary=summary,
        confidence=0.7 if result["healthy"] else 0.55,
        tools_used=[t],
        evidence={"health": result},
    )
