import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apso.agents import MODULES
from apso.connectors import servicenow
from apso.governance.controls import controls
from apso.store import store


def _state():
    inc = servicenow.get_incident("INC5668817")
    return {"incident": inc.model_dump(), "evidence": {}}


def test_all_nine_modules_independently():
    state = _state()
    # seed evidence for RCA
    state["evidence"].update(MODULES["mainframe_operations"].run(state).evidence)
    state["evidence"].update(MODULES["log_analysis"].run(state).evidence)
    for name, mod in MODULES.items():
        result = mod.run(state)
        assert result.agent
        assert result.summary
        assert isinstance(result.tools_used, list)
        state["evidence"].update(result.evidence)


def test_hitl_blocks_snow_write():
    preview = servicenow.resolve_ticket("INC5668817", "test", confirmed=False)
    assert preview.get("hitl") is True
    assert store.incidents["INC5668817"].state != "Resolved"


def test_hitl_approve_writes():
    controls.engage_kill_switch(False)
    req = controls.request_hitl("resolve_ticket", "INC5668817", {"close_notes": "ok"})
    controls.resolve_hitl(req.id, True)
    out = servicenow.resolve_ticket("INC5668817", "ok", confirmed=True)
    assert out["ok"] is True
    # reset for other tests
    store.incidents["INC5668817"].state = "In Progress"


def test_kill_switch():
    controls.engage_kill_switch(True)
    ok, reason = controls.can_execute("mainframe")
    assert ok is False
    assert "kill" in reason.lower()
    controls.engage_kill_switch(False)


def test_dq_scores_ticket():
    from apso.agents.data_quality import clean_ticket_fields

    r = clean_ticket_fields(_state()["incident"])
    assert r["quality_score"] >= 0.8
