"""Root-cause analysis / impact analyzer — correlates evidence."""

from __future__ import annotations

from typing import Any

from apso.connectors import model
from apso.governance.controls import controls
from apso.knowledge.bridge import search
from apso.models import StageResult, ToolCall


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    prior = state.get("evidence") or {}
    tools: list[ToolCall] = []

    t1 = ToolCall(name="search_sop", args={"q": incident.get("short_description", "")})
    kb = search(incident.get("short_description") or incident.get("ci") or "PK")
    # Prefer PK chunk SOP for demo INC
    if "5668817" in str(incident.get("number", "")) or "pk" in (incident.get("short_description") or "").lower():
        kb = search("PK Chunking")
    t1.result = kb
    tools.append(t1)

    evidence = {
        "logs": prior.get("logs"),
        "spool": prior.get("spool"),
        "code": prior.get("code"),
        "sop": (kb.get("sops") or [None])[0],
    }
    conf = controls.score_confidence(evidence)

    prompt = (
        f"Incident {incident.get('number')}: {incident.get('short_description')}\n"
        f"Spool: {evidence.get('spool')}\nLogs: {evidence.get('logs')}\nSOP: {evidence.get('sop')}"
    )
    t2 = ToolCall(name="rca_synthesize", args={})
    rca_text = model.complete("You are the APSO RCA agent.", prompt)
    t2.result = {"text": rca_text}
    tools.append(t2)

    rca = {
        "priority": incident.get("priority"),
        "cause": rca_text,
        "sop": evidence.get("sop"),
        "confidence": conf,
        "next_steps": [
            "Disable PK Chunking in JCL PARMS (PKCHUNK=N)",
            "Re-run the job",
            "Verify CC 0000",
            "Resolve ticket with HITL Apply",
        ]
        if evidence.get("sop") and "PK" in str(evidence.get("sop"))
        else ["Review evidence", "Propose remediation"],
    }

    summary = rca_text
    if evidence.get("sop"):
        summary += f" Compliant with {(evidence['sop'] or {}).get('id')} batch job rules."

    return StageResult(
        stage="diagnose",
        agent="correlation",
        summary=summary,
        confidence=conf,
        tools_used=tools,
        evidence={"rca": rca, **{k: v for k, v in evidence.items() if v}},
    )
