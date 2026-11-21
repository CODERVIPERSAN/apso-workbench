"""AI remediation — suggest fix; execution HITL-gated."""

from __future__ import annotations

from typing import Any

from apso.connectors import mainframe
from apso.governance.controls import controls
from apso.models import StageResult, ToolCall
from apso.store import store


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    job = incident.get("ci") or ""
    playbook = next((p for p in store.playbooks if "PK" in p["id"] or "PK" in p["title"]), store.playbooks[0] if store.playbooks else None)

    tools: list[ToolCall] = []
    t1 = ToolCall(name="suggest_fix", args={"job": job})
    suggestion = {
        "action": "disable_pk_chunking_and_rerun",
        "playbook": playbook,
        "jcl_change": "PARMS('PKCHUNK=N,...')",
        "rationale": "SOP-BATCH-014 — PK Chunking timeout recovery",
    }
    t1.result = suggestion
    tools.append(t1)

    # Preview submit — never executes without HITL
    t2 = ToolCall(name="submit_jcl", args={"job": job, "confirmed": False})
    preview = mainframe.submit_jcl(job, confirmed=False)
    t2.result = preview
    tools.append(t2)

    hitl = controls.request_hitl(
        action="submit_jcl",
        target=job,
        preview=preview.get("preview") or preview,
    )

    return StageResult(
        stage="resolve",
        agent="remediation",
        summary=(
            f"Suggested remediation: disable PK Chunking and re-run {job}. "
            "HITL required — no mainframe write until you Apply."
        ),
        confidence=0.82,
        tools_used=tools,
        evidence={"remediation": suggestion, "submit_preview": preview},
        hitl_required=True,
        hitl_id=hitl.id,
    )
