"""COBOL/JCL code intelligence — APSO module; model connector for explain."""

from __future__ import annotations

from typing import Any

from apso.connectors import mainframe, model
from apso.models import StageResult, ToolCall


def explain_cobol(program: str) -> dict[str, Any]:
    src = mainframe.read_source(program)
    if "error" in src:
        return src
    text = model.complete(
        "You explain COBOL for L3 engineers. Be concise.",
        f"Explain this program:\n{src['source']}",
    )
    return {"program": program, "explanation": text, "source_preview": src["source"][:500]}


def explain_jcl(job: str) -> dict[str, Any]:
    jcl = mainframe.read_jcl(job)
    if "error" in jcl:
        return jcl
    text = model.complete(
        "You explain JCL steps for L3 engineers.",
        f"Explain this JCL:\n{jcl['jcl']}",
    )
    return {"job": job, "explanation": text, "jcl_preview": jcl["jcl"][:500]}


def optimize_advice(program: str) -> dict[str, Any]:
    return {
        "program": program,
        "advice": [
            "Consider PKCHUNK=N for oversized extract tables per SOP-BATCH-014",
            "Review REGION and TIME parameters if S322 recurs",
        ],
    }


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    job = incident.get("ci") or "PAYROLL01"
    program = "PAYEXT" if "PAY" in job.upper() else job

    tools: list[ToolCall] = []
    t1 = ToolCall(name="explain_jcl", args={"job": job})
    jcl_ex = explain_jcl(job)
    t1.result = jcl_ex
    tools.append(t1)

    t2 = ToolCall(name="explain_cobol", args={"program": program})
    cob = explain_cobol(program)
    t2.result = cob
    tools.append(t2)

    t3 = ToolCall(name="optimize_advice", args={"program": program})
    opt = optimize_advice(program)
    t3.result = opt
    tools.append(t3)

    summary = cob.get("explanation") or jcl_ex.get("explanation") or "Code intelligence complete."
    return StageResult(
        stage="diagnose",
        agent="code_intelligence",
        summary=summary if isinstance(summary, str) else str(summary),
        confidence=0.8,
        tools_used=tools,
        evidence={"code": {"jcl": jcl_ex, "cobol": cob, "optimize": opt}},
    )
