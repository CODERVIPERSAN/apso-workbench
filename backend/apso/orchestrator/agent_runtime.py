"""Multi-agent runtime — each agent is an LLM with tools (ASW tool-loop)."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from apso.connectors import mainframe, model, newrelic, servicenow
from apso.connectors.model import chat, parse_tool_calls, tool_schema
from apso.governance.controls import controls
from apso.knowledge.bridge import search
from apso.models import StageResult, ToolCall
from apso.store import store

Emit = Callable[[dict[str, Any]], None]


# ---- shared tool implementations (API connectors) ----

def _pick(args: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for k in keys:
        if args.get(k) not in (None, ""):
            return args[k]
    return default


def invoke_tool(name: str, args: dict[str, Any] | None, context: dict[str, Any]) -> Any:
    """Never raise — always fill defaults from case context."""
    from apso.agents.data_quality import clean_ticket_fields

    a = {**_default_args(name, context), **(args or {})}
    # normalize common LLM aliases
    if "number" not in a or not a.get("number"):
        a["number"] = _pick(a, "number", "incident_number", "incident", "id", default=_case_number(context))
    if "job_name" not in a or not a.get("job_name"):
        a["job_name"] = _pick(a, "job_name", "job", "ci", default=_case_job(context))
    if "program" not in a or not a.get("program"):
        a["program"] = _pick(a, "program", "program_name", "member", default="PAYEXT")
    if "query" not in a or not a.get("query"):
        a["query"] = _pick(a, "query", "q", "search", default=_case_job(context))

    try:
        if name == "get_incident":
            inc = servicenow.get_incident(str(a["number"]))
            return inc.model_dump() if inc else {"error": "not found"}
        if name == "assess_ticket_quality":
            inc = servicenow.get_incident(str(a["number"]))
            return clean_ticket_fields(inc.model_dump() if inc else {"number": a["number"]})
        if name == "find_similar_incidents":
            return servicenow.find_similar_incidents(str(a["number"]))
        if name == "find_related_problem":
            return servicenow.find_related_problem(str(a["number"])) or {"found": False}
        if name == "resolve_ticket_preview":
            return servicenow.resolve_ticket(
                str(a["number"]),
                str(a.get("close_notes") or "Resolved via APSO (HITL pending)."),
                confirmed=False,
            )
        if name == "search_nr_logs":
            return newrelic.search_logs(str(a["query"]))
        if name == "get_nr_app_errors":
            return newrelic.get_app_errors(str(a.get("app") or "payroll-batch"))
        if name == "savrs_job_spool":
            return mainframe.job_spool(str(a["job_name"]))
        if name == "read_jcl":
            return mainframe.read_jcl(str(a["job_name"]))
        if name == "read_cobol":
            return mainframe.read_source(str(a["program"]))
        if name == "esp_job_history":
            return mainframe.esp_history(str(a["job_name"]))
        if name == "submit_jcl_preview":
            return mainframe.submit_jcl(str(a["job_name"]), confirmed=False)
        if name == "search_knowledge":
            return search(str(a["query"]))
        if name == "list_dq_rules":
            ds = str(a.get("dataset") or "")
            return [r for r in store.dq_rules if not ds or r.get("dataset") == ds]
        if name == "health_check_job":
            return {
                "spool": mainframe.job_spool(str(a["job_name"])),
                "errors": newrelic.get_app_errors("payroll-batch"),
            }
        return {"error": f"unknown tool {name}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "tool": name, "args": a}


def _case_number(context: dict[str, Any]) -> str:
    inc = context.get("incident") or {}
    return str(inc.get("number") or "INC5668817")


def _case_job(context: dict[str, Any]) -> str:
    inc = context.get("incident") or {}
    return str(inc.get("ci") or "PAYROLL01")


# How every agent talks to support engineers (user-facing replies)
SPEAK_PLAIN = (
    "You are talking to a support engineer in chat. Use everyday words they already know: "
    "ticket, job, error, logs, priority, assignment group, what failed, what to try next.\n"
    "Do NOT use jargon like: quality score, HITL, swarm, orchestrator, blast radius, "
    "value stream, conformity, completeness score, tool policy, checkpoint, lifecycle, "
    "read_write_hitl, or raw 0–1 scores.\n"
    "Say 'needs your OK before we change anything' instead of HITL. "
    "2–5 short sentences. No markdown headings. No field-by-field dumps."
)

AGENT_SPECS: dict[str, dict[str, Any]] = {
    "orchestrator": {
        "role": "Coordinates the team and keeps the case moving.",
        "tools": ["get_incident", "search_knowledge"],
    },
    "paige": {
        "role": "First look — is this urgent, and what is the ticket about?",
        "tools": ["get_incident", "assess_ticket_quality"],
    },
    "data_quality": {
        "role": "Checks whether the ticket is filled in properly.",
        "tools": ["get_incident", "assess_ticket_quality", "list_dq_rules"],
    },
    "triage": {
        "role": "Figures out what broke — job name, symptoms, where to look.",
        "tools": ["get_incident", "search_knowledge"],
    },
    "impact": {
        "role": "How bad is it — who is affected and how urgent.",
        "tools": ["get_incident", "search_nr_logs"],
    },
    "log_analysis": {
        "role": "Reads application and system logs for errors.",
        "tools": ["search_nr_logs", "get_nr_app_errors"],
    },
    "change_analyzer": {
        "role": "Checks what changed recently on this job or system.",
        "tools": ["search_knowledge", "esp_job_history"],
    },
    "code_analyzer": {
        "role": "Explains the failing batch program in plain words.",
        "tools": ["read_jcl", "read_cobol", "savrs_job_spool"],
    },
    "mainframe": {
        "role": "Looks at the batch job run history and output.",
        "tools": ["savrs_job_spool", "read_jcl", "esp_job_history"],
    },
    "resolution": {
        "role": "Suggests a practical fix from the runbook.",
        "tools": ["search_knowledge", "get_incident", "submit_jcl_preview"],
    },
    "self_healing": {
        "role": "Prepares a fix you can approve before anything runs.",
        "tools": ["submit_jcl_preview", "search_knowledge"],
    },
    "health_check": {
        "role": "Checks things look healthy after a fix.",
        "tools": ["health_check_job", "search_nr_logs"],
    },
    "closure": {
        "role": "Prepares clear close notes — needs your OK before the ticket is resolved.",
        "tools": [
            "assess_ticket_quality",
            "find_similar_incidents",
            "find_related_problem",
            "resolve_ticket_preview",
        ],
    },
}


def _schemas_for(tool_names: list[str]) -> list[dict[str, Any]]:
    props = {
        "get_incident": tool_schema("get_incident", "Fetch ServiceNow incident", {"number": {"type": "string"}}, ["number"]),
        "assess_ticket_quality": tool_schema("assess_ticket_quality", "Score ticket field quality", {"number": {"type": "string"}}, ["number"]),
        "find_similar_incidents": tool_schema("find_similar_incidents", "Find similar historical incidents", {"number": {"type": "string"}}, ["number"]),
        "find_related_problem": tool_schema("find_related_problem", "Find related problem record", {"number": {"type": "string"}}, ["number"]),
        "resolve_ticket_preview": tool_schema(
            "resolve_ticket_preview",
            "Preview resolve (HITL — does not write)",
            {"number": {"type": "string"}, "close_notes": {"type": "string"}},
            ["number"],
        ),
        "search_nr_logs": tool_schema("search_nr_logs", "Search New Relic logs", {"query": {"type": "string"}}, ["query"]),
        "get_nr_app_errors": tool_schema("get_nr_app_errors", "App error summary", {"app": {"type": "string"}}, []),
        "savrs_job_spool": tool_schema("savrs_job_spool", "Mainframe job spool", {"job_name": {"type": "string"}}, ["job_name"]),
        "read_jcl": tool_schema("read_jcl", "Read JCL", {"job_name": {"type": "string"}}, ["job_name"]),
        "read_cobol": tool_schema("read_cobol", "Read COBOL source", {"program": {"type": "string"}}, ["program"]),
        "esp_job_history": tool_schema("esp_job_history", "ESP scheduler history", {"job_name": {"type": "string"}}, ["job_name"]),
        "submit_jcl_preview": tool_schema("submit_jcl_preview", "Preview JCL submit (HITL)", {"job_name": {"type": "string"}}, ["job_name"]),
        "search_knowledge": tool_schema("search_knowledge", "Search SOPs/playbooks", {"query": {"type": "string"}}, ["query"]),
        "list_dq_rules": tool_schema("list_dq_rules", "List DQ rules", {"dataset": {"type": "string"}}, []),
        "health_check_job": tool_schema("health_check_job", "Post-fix health check", {"job_name": {"type": "string"}}, ["job_name"]),
    }
    return [props[n] for n in tool_names if n in props]


def run_agent(
    agent_name: str,
    *,
    task: str,
    context: dict[str, Any],
    emit: Emit | None = None,
    max_iters: int = 5,
    mode: str = "agent",
    tool_override: list[str] | None = None,
) -> StageResult:
    """LLM tool-calling loop for one specialist agent (Cursor triad: instructions+tools+model)."""
    import os

    from apso.runtime.modes import mode_policy

    spec = AGENT_SPECS.get(agent_name) or {
        "role": f"{agent_name} agent",
        "tools": tool_override or [],
    }
    ok, reason = controls.can_execute(agent_name if agent_name in AGENT_SPECS else "orchestrator")
    if not ok:
        return StageResult(stage=agent_name, agent=agent_name, summary=f"Blocked: {reason}", confidence=0.0)

    def _emit(e: dict[str, Any]) -> None:
        if emit:
            emit(e)

    allowed_tools = mode_policy.filter_tools(mode, tool_override or list(spec["tools"]))
    _emit({"type": "agent_start", "agent": agent_name, "role": spec["role"], "mode": mode_policy.normalize(mode)})
    tools = _schemas_for(allowed_tools)
    used: list[ToolCall] = []
    evidence: dict[str, Any] = {}

    # Fast path for tests: tools + one LLM summary (or no LLM if APSO_LLM=0)
    if os.getenv("APSO_LLM", "1") == "0":
        for name in allowed_tools[:3]:
            args = _default_args(name, context)
            result = invoke_tool(name, args, context)
            used.append(ToolCall(name=name, args=args, result=result))
            evidence[name] = result
            _emit({"type": "tool_done", "agent": agent_name, "tool": name, "result": result})
        summary = f"Looked at the ticket and related details ({len(used)} checks)."
        _emit({"type": "agent_done", "agent": agent_name, "summary": summary})
        return StageResult(
            stage=agent_name,
            agent=agent_name,
            summary=summary,
            confidence=0.7,
            tools_used=used,
            evidence=evidence,
        )

    system = (
        f"You help with IT support tickets. Your job: {spec['role']}\n"
        f"{SPEAK_PLAIN}\n"
        "This workbench is authorized — use tools for tickets, jobs, and logs. Never refuse incident numbers.\n"
        "Never say you already fixed ServiceNow or reran a job — that needs the engineer's OK first.\n"
        "Use earlier chat turns when the engineer refers to them (this ticket, what we said, next steps).\n"
        f"Case context:\n{json.dumps({k: v for k, v in context.items() if k != 'chat_history'}, default=str)[:4000]}"
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    prior = (context.get("chat_history") or "").strip()
    if prior:
        messages.append({"role": "user", "content": prior})
        messages.append(
            {
                "role": "assistant",
                "content": "Got it — I remember what we covered. Continuing from that.",
            }
        )
    messages.append({"role": "user", "content": task})

    for i in range(max_iters):
        _emit({"type": "agent_thinking", "agent": agent_name, "iteration": i + 1})
        msg = chat(messages, tools=tools if tools else None)
        tool_calls = parse_tool_calls(msg)
        content = (msg.get("content") or "").strip()
        # Final reply is agent_done only (avoids duplicate chat bubbles)

        if not tool_calls:
            if i == 0 and tools:
                # Hybrid fallback: run primary tools, then ask LLM to synthesize
                messages.append({"role": "assistant", "content": content or "(planning tools)"})
                for name in allowed_tools[:3]:
                    args = _default_args(name, context)
                    _emit({"type": "tool_start", "agent": agent_name, "tool": name, "args": args})
                    result = invoke_tool(name, args, context)
                    used.append(ToolCall(name=name, args=args, result=result))
                    evidence[name] = result
                    _emit({"type": "tool_done", "agent": agent_name, "tool": name, "result": result})
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Tool {name} result:\n{json.dumps(result, default=str)[:4000]}",
                        }
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"{SPEAK_PLAIN}\n"
                            "Using the tool results, tell the engineer what you found and what to do next."
                        ),
                    }
                )
                continue
            summary = content or "I checked what I could — ask if you want me to dig further."
            conf = controls.score_confidence(evidence)
            _emit({"type": "agent_done", "agent": agent_name, "summary": summary})
            return StageResult(
                stage=agent_name,
                agent=agent_name,
                summary=summary,
                confidence=conf,
                tools_used=used,
                evidence=evidence,
            )

        # append assistant tool_calls message
        messages.append(msg)
        for tc in tool_calls:
            name = tc["name"]
            args = tc["args"] if isinstance(tc["args"], dict) else {}
            _emit({"type": "tool_start", "agent": agent_name, "tool": name, "args": args})
            if name not in allowed_tools:
                result = {
                    "error": f"Tool '{name}' blocked in mode={mode_policy.normalize(mode)}",
                    "allowed": allowed_tools,
                }
            else:
                result = invoke_tool(name, args, context)
            used.append(ToolCall(name=name, args=args, result=result))
            evidence[name] = result
            _emit({"type": "tool_done", "agent": agent_name, "tool": name, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id") or name,
                    "content": json.dumps(result, default=str)[:6000],
                }
            )

    # force summary
    messages.append(
        {
            "role": "user",
            "content": f"{SPEAK_PLAIN}\nWrap up what you found for the support engineer.",
        }
    )
    final = chat(messages, tools=None)
    summary = (final.get("content") or "").strip() or "I finished checking — ask if you need more detail."
    _emit({"type": "agent_done", "agent": agent_name, "summary": summary})
    return StageResult(
        stage=agent_name,
        agent=agent_name,
        summary=summary,
        confidence=controls.score_confidence(evidence),
        tools_used=used,
        evidence=evidence,
    )


def _default_args(tool_name: str, context: dict[str, Any]) -> dict[str, Any]:
    inc = context.get("incident") or {}
    number = inc.get("number") or "INC5668817"
    job = inc.get("ci") or "PAYROLL01"
    mapping = {
        "get_incident": {"number": number},
        "assess_ticket_quality": {"number": number},
        "find_similar_incidents": {"number": number},
        "find_related_problem": {"number": number},
        "resolve_ticket_preview": {
            "number": number,
            "close_notes": "Resolved via APSO multi-agent investigation (HITL pending).",
        },
        "search_nr_logs": {"query": job},
        "get_nr_app_errors": {"app": "payroll-batch"},
        "savrs_job_spool": {"job_name": job},
        "read_jcl": {"job_name": job},
        "read_cobol": {"program": "PAYEXT"},
        "esp_job_history": {"job_name": job},
        "submit_jcl_preview": {"job_name": job},
        "search_knowledge": {"query": inc.get("short_description") or job},
        "list_dq_rules": {"dataset": ""},
        "health_check_job": {"job_name": job},
    }
    return mapping.get(tool_name, {})


def orchestrator_plan(incident: dict[str, Any], emit: Emit | None = None) -> list[str]:
    """LLM (or fallback) chooses agent sequence for this case."""
    import os

    default = [
        "paige",
        "data_quality",
        "triage",
        "impact",
        "log_analysis",
        "change_analyzer",
        "mainframe",
        "code_analyzer",
        "resolution",
        "self_healing",
        "health_check",
        "closure",
    ]
    if emit:
        emit({"type": "agent_start", "agent": "orchestrator", "role": AGENT_SPECS["orchestrator"]["role"]})
        emit({"type": "agent_thinking", "agent": "orchestrator", "iteration": 1})
    if os.getenv("APSO_LLM", "1") == "0":
        if emit:
            emit({"type": "agent_message", "agent": "orchestrator", "text": f"Offline plan: {default}"})
            emit({"type": "plan", "agents": default})
        return default
    prompt = (
        "Return ONLY a JSON array of agent names to run in order for this incident. "
        f"Allowed: {default}. Incident: {json.dumps(incident, default=str)[:1500]}"
    )
    text = model.complete(AGENT_SPECS["orchestrator"]["role"], prompt)
    if emit:
        emit({"type": "agent_message", "agent": "orchestrator", "text": text})
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            plan = json.loads(text[start : end + 1])
            plan = [p for p in plan if p in AGENT_SPECS and p != "orchestrator"]
            if plan:
                if emit:
                    emit({"type": "plan", "agents": plan})
                return plan
    except json.JSONDecodeError:
        pass
    if emit:
        emit({"type": "plan", "agents": default})
    return default
