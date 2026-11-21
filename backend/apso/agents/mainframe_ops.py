"""Mainframe operations agent — spool/JCL/ESP via mainframe connector."""

from __future__ import annotations

from typing import Any

from apso.connectors import mainframe
from apso.models import StageResult, ToolCall


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    job = incident.get("ci") or ""
    tools: list[ToolCall] = []

    t1 = ToolCall(name="savrs_job_spool", args={"job": job})
    spool = mainframe.job_spool(job)
    t1.result = spool
    tools.append(t1)

    t2 = ToolCall(name="read_jcl", args={"job": job})
    jcl = mainframe.read_jcl(job)
    t2.result = {"has_jcl": "jcl" in jcl, "error": jcl.get("error")}
    tools.append(t2)

    t3 = ToolCall(name="esp_job_history", args={"job": job})
    hist = mainframe.esp_history(job)
    t3.result = hist
    tools.append(t3)

    abend = spool.get("abend")
    msg = spool.get("message") or spool.get("error") or "no spool"
    summary = f"Mainframe job {job}: status={spool.get('last_status')} step={spool.get('step')} abend={abend}. {msg}"
    return StageResult(
        stage="diagnose",
        agent="mainframe",
        summary=summary,
        confidence=0.85 if "error" not in spool else 0.3,
        tools_used=tools,
        evidence={"spool": spool, "jcl": jcl, "history": hist},
    )
