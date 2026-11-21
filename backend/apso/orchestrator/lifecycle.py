"""Orchestrator-centric multi-agent lifecycle (APSO architecture)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from apso.connectors import servicenow
from apso.governance.controls import controls
from apso.models import InvestigationState, Stage
from apso.orchestrator.agent_runtime import orchestrator_plan, run_agent
from apso.paige_bridge.intake import assemble_context, classify_urgency
from apso.store import store

EventCb = Callable[[dict[str, Any]], None]

STAGE_OF = {
    "paige": "intake",
    "data_quality": "intake",
    "triage": "diagnose",
    "impact": "diagnose",
    "log_analysis": "diagnose",
    "change_analyzer": "diagnose",
    "mainframe": "diagnose",
    "code_analyzer": "diagnose",
    "resolution": "resolve",
    "self_healing": "resolve",
    "health_check": "verify",
    "closure": "close",
}


def run_investigation(
    incident_number: str,
    *,
    auto: bool = True,
    emit: EventCb | None = None,
) -> InvestigationState:
    def _emit(payload: dict[str, Any]) -> None:
        if emit:
            emit(payload)

    inc = servicenow.get_incident(incident_number)
    if not inc:
        raise ValueError(f"Unknown incident {incident_number}")

    ctx = assemble_context(inc)
    inv = InvestigationState(
        incident_number=incident_number,
        urgency=classify_urgency(inc),
        stage=Stage.INTAKE,
    )
    store.investigations[inv.id] = inv
    store.runs_today += 1

    _emit(
        {
            "type": "architecture",
            "lifecycle": ["intake", "diagnose", "resolve", "verify", "close"],
            "active_stage": "intake",
            "message": "Orchestrator-centric lifecycle started",
        }
    )
    _emit({"type": "status", "stage": "intake", "message": f"Paige intake — urgency={inv.urgency}"})

    case_context: dict[str, Any] = {
        "incident": inc.model_dump(),
        "paige_context": ctx,
        "evidence_digest": {},
    }

    plan = orchestrator_plan(inc.model_dump(), emit=_emit)
    _emit(
        {
            "type": "text",
            "text": f"I will walk through {len(plan)} checks on this ticket.",
        }
    )

    for agent_name in plan:
        if store.kill_switch:
            _emit({"type": "error", "text": "Safety stop is on — paused the investigation."})
            break

        stage = STAGE_OF.get(agent_name, "diagnose")
        _emit({"type": "architecture", "active_stage": stage, "active_agent": agent_name})

        task = (
            f"Look into ticket {incident_number}. "
            f"What it says: {inc.short_description}. "
            f"Job/system: {inc.ci}. "
            "Use your tools, then tell the support engineer what you found in plain words."
        )
        if agent_name == "closure":
            task += " Draft close notes for review — do not say the ticket is already closed."
        if agent_name in ("resolution", "self_healing"):
            task += " If it fits the runbook, suggest turning off PK Chunking and rerunning the job."

        result = run_agent(agent_name, task=task, context=case_context, emit=_emit)
        result.stage = stage
        inv.stage_results.append(result)
        inv.tools_used.extend([t.name for t in result.tools_used])
        inv.messages.append(f"[{agent_name}] {result.summary}")
        case_context["evidence_digest"][agent_name] = {
            "summary": result.summary,
            "tools": [t.name for t in result.tools_used],
        }
        # flatten useful evidence
        for k, v in result.evidence.items():
            case_context["evidence_digest"][k] = v

        if agent_name in ("resolution", "self_healing", "closure"):
            # Cursor-like checkpoint before risky Apply
            from apso.runtime.checkpoints import checkpoints

            action = "resolve_ticket" if agent_name == "closure" else "submit_jcl"
            target = incident_number if action == "resolve_ticket" else inc.ci
            ckpt = checkpoints.create(
                reason=f"pre-{action}",
                incident_number=incident_number,
                payload={"agent": agent_name, "summary": result.summary[:500]},
            )
            preview = {
                "agent": agent_name,
                "summary": result.summary,
                "close_notes": result.summary[:500],
                "confirmed": False,
                "checkpoint_id": ckpt,
            }
            hitl = controls.request_hitl(action, target, preview)
            result.hitl_required = True
            result.hitl_id = hitl.id
            inv.hitl = hitl
            if agent_name == "closure":
                inv.resolve_preview = {
                    "confirmed": False,
                    "message": f"Ready to close {incident_number}. Please review the notes first.",
                    "hitl": "Needs your OK — nothing is written to ServiceNow until you Apply.",
                    "close_notes": result.summary[:800],
                    "checkpoint_id": ckpt,
                }
            _emit(
                {
                    "type": "hitl_gate",
                    "hitl_id": hitl.id,
                    "checkpoint_id": ckpt,
                    "action": action,
                    "agent": agent_name,
                    "preview": preview,
                    "message": "Needs your OK before we change anything outside this workbench.",
                }
            )
            if not auto:
                break

        # investigation loop signal back to orchestrator after diagnose cluster
        if agent_name == "code_analyzer":
            _emit(
                {
                    "type": "investigation_loop",
                    "message": "Diagnosis done — next we will look at how to fix it.",
                }
            )

    inv.completed = True
    inv.stage = Stage.CLOSE
    _emit({"type": "architecture", "active_stage": "close", "active_agent": None})
    _emit({"type": "done", "investigation_id": inv.id, "tools_used": inv.tools_used, "plan": plan})
    return inv


def stream_investigation(incident_number: str, auto: bool = True) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []

    def emit(e: dict[str, Any]) -> None:
        queue.append(e)

    inv = run_investigation(incident_number, auto=auto, emit=emit)
    queue.append({"type": "investigation", "data": inv.model_dump(mode="json")})
    return queue
