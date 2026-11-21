"""Ticket resolution and closure — ServiceNow write behind HITL."""

from __future__ import annotations

from typing import Any

from apso.connectors import servicenow
from apso.governance.controls import controls
from apso.models import StageResult, ToolCall
from apso.store import store


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    number = incident.get("number")
    rca = (state.get("evidence") or {}).get("rca") or {}
    notes = (
        rca.get("cause")
        or "Resolved via APSO: disabled PK Chunking and re-ran job per SOP-BATCH-014."
    )

    tools: list[ToolCall] = []
    # Re-assess quality for closure notes clarity
    t_q = ToolCall(name="assess_ticket_quality", args={"number": number})
    from apso.agents.data_quality import clean_ticket_fields

    t_q.result = clean_ticket_fields(incident)
    tools.append(t_q)

    t1 = ToolCall(name="find_similar_incidents", args={"number": number})
    t1.result = servicenow.find_similar_incidents(number)
    tools.append(t1)

    t2 = ToolCall(name="find_related_problem", args={"number": number})
    t2.result = servicenow.find_related_problem(number)
    tools.append(t2)

    t3 = ToolCall(name="resolve_ticket", args={"number": number, "confirmed": False})
    preview = servicenow.resolve_ticket(number, notes, confirmed=False)
    t3.result = preview
    tools.append(t3)

    hitl = controls.request_hitl(
        action="resolve_ticket",
        target=number,
        preview={"close_notes": notes, **(preview.get("preview") or {})},
    )

    # Optional problem record draft (no write)
    problem_draft = {
        "short_description": f"Recurring risk: {incident.get('short_description')}",
        "linked_incident": number,
        "status": "draft",
    }

    resolve_preview = {
        "confirmed": False,
        "message": f"Ready to resolve {number}. Review resolution details in the panel.",
        "hitl": "HITL required — no ServiceNow write until you Apply.",
        "close_notes": notes,
        "problem_draft": problem_draft,
    }

    similar_txt = (
        "No similar historical incidents found above the similarity threshold. Base recommendation on live ticket data only."
        if not t1.result
        else f"Similar incidents: {len(t1.result)}"
    )
    pr_txt = f"No related Problem record found for {number}." if not t2.result else str(t2.result)

    summary = (
        f"{notes}\n\n"
        f"**Similar incidents & Problem Record**\n{similar_txt}\n{pr_txt}\n\n"
        f"**Resolve preview (confirmed=false)**\n"
        f"{resolve_preview['message']}\n{resolve_preview['hitl']}"
    )

    # stash for UI
    store.hitl[hitl.id] = hitl

    return StageResult(
        stage="close",
        agent="closure",
        summary=summary,
        confidence=0.88,
        tools_used=tools,
        evidence={"resolve_preview": resolve_preview, "problem_draft": problem_draft},
        hitl_required=True,
        hitl_id=hitl.id,
    )
