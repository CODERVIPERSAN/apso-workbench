"""Incident management agent — uses ServiceNow connector API."""

from __future__ import annotations

from typing import Any

from apso.connectors import servicenow
from apso.models import StageResult, ToolCall


def run(state: dict[str, Any]) -> StageResult:
    number = (state.get("incident") or {}).get("number") or state.get("incident_number")
    tools: list[ToolCall] = []

    t1 = ToolCall(name="get_live_incident", args={"number": number})
    inc = servicenow.get_incident(number)
    t1.result = inc.model_dump() if inc else {"error": "not found"}
    tools.append(t1)

    t2 = ToolCall(name="find_similar_incidents", args={"number": number})
    similar = servicenow.find_similar_incidents(number)
    t2.result = similar
    tools.append(t2)

    t3 = ToolCall(name="find_related_problem", args={"number": number})
    problem = servicenow.find_related_problem(number)
    t3.result = problem
    tools.append(t3)

    if similar:
        sim_txt = f"Found {len(similar)} similar incidents."
    else:
        sim_txt = "No similar historical incidents found above the similarity threshold. Base recommendation on live ticket data only."
    pr_txt = (
        f"Related problem: {problem.get('number')}"
        if problem
        else f"No related Problem record found for {number}."
    )

    return StageResult(
        stage="diagnose",
        agent="servicenow",
        summary=f"{sim_txt} {pr_txt}",
        confidence=0.75,
        tools_used=tools,
        evidence={"similar": similar, "problem": problem, "incident": t1.result},
    )
