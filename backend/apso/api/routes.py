from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from apso.agents import MODULES
from apso.connectors import mainframe, model, newrelic, servicenow
from apso.governance.controls import controls
from apso.knowledge.bridge import search
from apso.models import ChatRequest, InvestigateRequest
from apso.orchestrator.lifecycle import run_investigation
from apso.orchestrator.router import classify_intent, extract_incident
from apso.registry_loader import load_agents
from apso.store import store

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "kill_switch": store.kill_switch,
        "connectors": {
            "servicenow": servicenow.live(),
            "newrelic": newrelic.live(),
            "mainframe": mainframe.live(),
            "model": model.live(),
        },
    }


@router.get("/agents")
def agents() -> list[dict[str, Any]]:
    return load_agents()


@router.get("/status")
def status() -> dict[str, Any]:
    agents_list = load_agents()
    active = sum(1 for a in agents_list if a.get("status") == "ACTIVE")
    total = len(agents_list)
    open_inc = len([i for i in store.incidents.values() if i.state.lower() not in ("resolved", "closed")])
    pending = len([h for h in store.hitl.values() if h.status == "pending"])
    return {
        "incidents": open_inc,
        "agents_active": active,
        "agents_total": total,
        "runs_today": store.runs_today,
        "pending": pending,
        "connected_systems": 8,
        "running_tasks": 2 if pending else 0,
        "environment": "Prod Environment",
        "mainframe": "Mainframe",
        "all_systems": "All Systems Operational" if not store.kill_switch else "Kill-switch ENGAGED",
    }


@router.get("/incidents")
def incidents() -> list[dict[str, Any]]:
    return [i.model_dump() for i in store.incidents.values()]


@router.get("/incidents/{number}")
def incident(number: str) -> dict[str, Any]:
    inc = servicenow.get_incident(number.upper())
    if not inc:
        raise HTTPException(404, "Incident not found")
    return inc.model_dump()


@router.post("/investigations")
async def start_investigation(body: InvestigateRequest) -> dict[str, Any]:
    inv = await asyncio.to_thread(
        run_investigation, body.incident_number.upper(), auto=body.auto
    )
    return inv.model_dump(mode="json")


@router.get("/investigations/{inv_id}")
def get_investigation(inv_id: str) -> dict[str, Any]:
    inv = store.investigations.get(inv_id)
    if not inv:
        raise HTTPException(404, "Not found")
    return inv.model_dump(mode="json")


@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    async def gen():
        from apso.connectors import model
        from apso.orchestrator.agent_runtime import orchestrator_plan
        from apso.orchestrator.router import is_greeting, wants_investigation
        from apso.store import store as _store

        from apso.orchestrator.agent_runtime import SPEAK_PLAIN, run_agent
        from apso.runtime.modes import mode_policy
        from apso.runtime.sessions import sessions

        sid = sessions.ensure(body.session_id)
        prior = sessions.as_prompt_block(sid)
        sessions.append(sid, "user", body.message)
        sticky_inc = sessions.active_incident(sid)
        sticky_intent = sessions.last_intent(sid)
        yield _sse({"type": "session", "session_id": sid})

        def remember(reply: str) -> None:
            sessions.append(sid, "assistant", reply)

        def resolve_number(msg: str) -> str:
            return extract_incident(msg) or sticky_inc or "INC5668817"

        mode = mode_policy.normalize(body.mode)
        intent = classify_intent(body.message, prior=sticky_intent)
        if intent["intent"] not in {"GREETING", "GENERAL", "STATUS"}:
            sessions.set_intent(sid, intent["intent"])
        status_plain = {
            "ask": "Answering with read-only checks",
            "plan": "Building a step-by-step plan",
            "agent": "Ready to dig into the ticket",
        }.get(mode, "Ready")
        yield _sse({"type": "status", "message": status_plain})
        yield _sse({"type": "agent_start", "agent": "orchestrator", "role": "Here to help with your ticket"})

        # Greetings always stay chat-only
        if intent["intent"] == "GREETING" or is_greeting(body.message):
            user_blob = f"{prior}\n\nEngineer: {body.message}" if prior else body.message
            reply = model.complete(
                "You help support engineers with tickets. Reply in 1-2 short friendly sentences. "
                "No jargon. Remember earlier turns in this chat. Do not invent ticket numbers. "
                "Do not start an investigation.",
                user_blob,
            )
            remember(reply)
            yield _sse({"type": "agent_done", "agent": "orchestrator", "summary": reply})
            yield _sse({"type": "done"})
            return

        # --- Cursor Ask mode: single agent + READ-ONLY tools (no swarm, no writes) ---
        if mode == "ask":
            number = resolve_number(body.message)
            inc = servicenow.get_incident(number) if number else None
            ctx = {
                "incident": (inc.model_dump() if inc else {"number": number}),
                "mode": "ask",
                "chat_history": prior,
            }
            queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
            loop = asyncio.get_running_loop()
            last_reply: list[str] = []

            def emit_ask(e: dict[str, Any]) -> None:
                if e.get("type") == "agent_done" and e.get("summary"):
                    last_reply.append(str(e["summary"]))
                loop.call_soon_threadsafe(queue.put_nowait, e)

            def _ask_worker() -> None:
                try:
                    run_agent(
                        "ask",
                        task=(
                            "Look things up with read-only tools, then answer in plain support language. "
                            + body.message
                        ),
                        context=ctx,
                        emit=emit_ask,
                        mode="ask",
                        tool_override=mode_policy.ask_toolset(),
                    )
                except Exception as exc:  # noqa: BLE001
                    emit_ask({"type": "error", "text": str(exc)})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            task = asyncio.create_task(asyncio.to_thread(_ask_worker))
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _sse(event)
                await asyncio.sleep(0)
            await task
            if last_reply:
                remember(last_reply[-1])
            yield _sse({"type": "done"})
            return

        # --- Cursor Plan mode: orchestrator plan only ---
        if mode == "plan":
            number = resolve_number(body.message)
            inc = servicenow.get_incident(number)
            plan = orchestrator_plan((inc.model_dump() if inc else {"number": number}), emit=None)
            friendly = {
                "paige": "first look at the ticket",
                "data_quality": "check the ticket is filled in",
                "triage": "figure out what failed",
                "impact": "how urgent / who is hit",
                "log_analysis": "check the logs",
                "change_analyzer": "what changed recently",
                "mainframe": "batch job history",
                "code_analyzer": "explain the failing program",
                "resolution": "suggest a fix",
                "self_healing": "prepare a fix for your OK",
                "health_check": "confirm things look healthy",
                "closure": "prep close notes",
            }
            steps = "\n".join(
                f"{i+1}. {friendly.get(a, a.replace('_', ' '))}" for i, a in enumerate(plan)
            )
            text = (
                f"Here is a simple plan for {number} ({len(plan)} steps):\n{steps}\n\n"
                f"When you are ready, say Investigate {number} and we will walk through it."
            )
            remember(text)
            yield _sse({"type": "plan", "agents": plan})
            yield _sse({"type": "agent_message", "agent": "orchestrator", "text": text})
            yield _sse({"type": "agent_done", "agent": "orchestrator", "summary": text})
            yield _sse({"type": "done"})
            return

        # --- Cursor Agent mode: multi-agent swarm when requested ---
        if mode_policy.allows_swarm(mode) and (
            wants_investigation(body.message) or intent["intent"] == "INVESTIGATE"
        ):
            number = resolve_number(body.message) if extract_incident(body.message) or sticky_inc else None
            if not number:
                yield _sse(
                    {
                        "type": "agent_done",
                        "agent": "orchestrator",
                        "summary": "Which ticket should I look into? For example: Investigate INC5668817",
                    }
                )
                open_incs = [
                    i.number
                    for i in _store.incidents.values()
                    if i.state.lower() not in ("resolved", "closed")
                ]
                if open_incs:
                    yield _sse({"type": "text", "text": "Open tickets right now: " + ", ".join(open_incs)})
                yield _sse({"type": "done"})
                return

            queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
            loop = asyncio.get_running_loop()
            last_reply: list[str] = []

            def emit(e: dict[str, Any]) -> None:
                if e.get("type") == "agent_done" and e.get("summary"):
                    last_reply.append(str(e["summary"]))
                loop.call_soon_threadsafe(queue.put_nowait, e)

            async def worker() -> None:
                try:
                    await asyncio.to_thread(run_investigation, number, auto=body.auto, emit=emit)
                except Exception as exc:  # noqa: BLE001
                    emit({"type": "error", "text": str(exc)})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            task = asyncio.create_task(worker())
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _sse(event)
                await asyncio.sleep(0)
            await task
            if last_reply:
                remember(" ".join(last_reply[-3:]))
            else:
                remember(f"Looked into {number}.")
            yield _sse({"type": "done"})
            return

        # Agent mode, no full swarm — dispatch one specialist with tools
        from apso.orchestrator.router import agent_for_intent

        specialist = agent_for_intent(intent["intent"])
        # Follow-ups without a specialist → keep helping on sticky ticket
        if not specialist and (sticky_inc or intent["intent"] == "FOLLOW_UP"):
            specialist = "data_quality" if intent["intent"] == "DQ" else "resolution"
        number = resolve_number(body.message)
        inc = servicenow.get_incident(number)
        ctx = {
            "incident": (inc.model_dump() if inc else {"number": number}),
            "mode": mode,
            "user_message": body.message,
            "chat_history": prior,
        }

        if specialist:
            queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
            loop = asyncio.get_running_loop()
            last_reply: list[str] = []

            def emit_one(e: dict[str, Any]) -> None:
                if e.get("type") == "agent_done" and e.get("summary"):
                    last_reply.append(str(e["summary"]))
                loop.call_soon_threadsafe(queue.put_nowait, e)

            if specialist == "data_quality":
                task_text = (
                    f"Active ticket is {number} (from this chat — do not invent another INC). "
                    "Call get_incident then assess_ticket_quality. "
                    "Answer whether anything is missing in plain words, then one next tip. "
                    f"Engineer said: {body.message}"
                )
            else:
                task_text = (
                    f"Active ticket is {number} (from this chat — do not invent another INC). "
                    "Use tools on THIS ticket. Answer in plain support language. "
                    f"Engineer said: {body.message}"
                )

            def _one_worker() -> None:
                try:
                    run_agent(
                        specialist,
                        task=task_text,
                        context=ctx,
                        emit=emit_one,
                        mode=mode,
                    )
                except Exception as exc:  # noqa: BLE001
                    emit_one({"type": "error", "text": str(exc)})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            task = asyncio.create_task(asyncio.to_thread(_one_worker))
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _sse(event)
                await asyncio.sleep(0)
            await task
            if last_reply:
                remember(last_reply[-1])
            yield _sse({"type": "done"})
            return

        # True general chat — still ops-context, never refuse workbench tickets
        active = sticky_inc or "INC5668817"
        system = (
            "You help support engineers with tickets, batch jobs, and logs. "
            f"{SPEAK_PLAIN} "
            f"Active ticket in this chat is {active}. Never invent other INC numbers. "
            "Use earlier turns. For a full look, ask them to say Investigate plus the ticket number."
        )
        user_blob = f"{prior}\n\nEngineer: {body.message}" if prior else body.message
        answer = model.complete(system, user_blob)
        remember(answer)
        yield _sse({"type": "agent_done", "agent": "orchestrator", "summary": answer})
        yield _sse({"type": "done"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/hitl")
def list_hitl() -> list[dict[str, Any]]:
    return [h.model_dump(mode="json") for h in store.hitl.values()]


@router.post("/hitl/{hitl_id}/approve")
def approve_hitl(hitl_id: str) -> dict[str, Any]:
    if hitl_id not in store.hitl:
        raise HTTPException(404, "HITL not found")
    req = controls.resolve_hitl(hitl_id, True)
    # Execute gated write
    result: dict[str, Any] = {"hitl": req.model_dump(mode="json")}
    if req.action == "resolve_ticket":
        notes = req.preview.get("close_notes", "Resolved via APSO HITL Apply")
        result["write"] = servicenow.resolve_ticket(req.target, notes, confirmed=True)
    elif req.action == "submit_jcl":
        result["write"] = mainframe.submit_jcl(req.target, confirmed=True)
    return result


@router.post("/hitl/{hitl_id}/reject")
def reject_hitl(hitl_id: str) -> dict[str, Any]:
    from apso.runtime.checkpoints import checkpoints

    if hitl_id not in store.hitl:
        raise HTTPException(404, "HITL not found")
    req = controls.resolve_hitl(hitl_id, False)
    restored = None
    ckpt = (req.preview or {}).get("checkpoint_id")
    if ckpt:
        restored = checkpoints.restore(ckpt)
    return {"hitl": req.model_dump(mode="json"), "checkpoint_restore": restored}


@router.get("/checkpoints")
def list_checkpoints() -> list[dict[str, Any]]:
    from apso.runtime.checkpoints import checkpoints

    return checkpoints.list()


@router.post("/checkpoints/{checkpoint_id}/restore")
def restore_checkpoint(checkpoint_id: str) -> dict[str, Any]:
    from apso.runtime.checkpoints import checkpoints

    out = checkpoints.restore(checkpoint_id)
    if not out.get("ok"):
        raise HTTPException(404, out.get("error", "not found"))
    return out


@router.get("/modes")
def list_modes() -> dict[str, Any]:
    from apso.runtime.modes import mode_policy

    return {
        "modes": {
            "ask": mode_policy.describe("ask"),
            "plan": mode_policy.describe("plan"),
            "agent": mode_policy.describe("agent"),
        },
        "ask_tools": mode_policy.ask_toolset(),
    }


@router.post("/governance/kill-switch")
def kill_switch(on: bool = True) -> dict[str, Any]:
    return controls.engage_kill_switch(on)


@router.get("/knowledge/search")
def knowledge_search(q: str) -> dict[str, Any]:
    return search(q)


@router.get("/modules/{name}/demo")
def module_demo(name: str) -> dict[str, Any]:
    mod = MODULES.get(name)
    if not mod:
        raise HTTPException(404, f"Unknown module. Choose from: {list(MODULES)}")
    inc = servicenow.get_incident("INC5668817")
    state = {"incident": inc.model_dump() if inc else {}, "evidence": {}}
    # For RCA, pre-fill some evidence
    if name == "root_cause_analysis":
        from apso.agents import log_analysis as la
        from apso.agents import mainframe_ops as mf

        state["evidence"].update(mf.run(state).evidence)
        state["evidence"].update(la.run(state).evidence)
    result = mod.run(state)
    return result.model_dump(mode="json")


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"
