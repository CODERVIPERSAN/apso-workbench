import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apso.governance.controls import controls
from apso.orchestrator.lifecycle import run_investigation
from apso.orchestrator.router import classify_intent, extract_incident
from apso.store import store


def test_router_inc():
    from apso.orchestrator.router import agent_for_intent, is_greeting, wants_investigation

    assert extract_incident("look at INC5668817 please") == "INC5668817"
    assert classify_intent("show spool for abend")["intent"] == "MAINFRAME"
    assert classify_intent("hi")["intent"] == "GREETING"
    assert is_greeting("hello")
    assert not wants_investigation("hi")
    assert wants_investigation("Investigate INC5668817")
    # clean / typo lean → DQ specialist, not bare LLM refusal path
    assert classify_intent("clean the INC5668817")["intent"] == "DQ"
    assert classify_intent("lean the inc5668817")["intent"] == "DQ"
    assert classify_intent("is anything missing on it?")["intent"] == "DQ"
    assert classify_intent("what should I do next?", prior="DQ")["intent"] == "DQ"
    assert agent_for_intent("DQ") == "data_quality"



def test_lifecycle_inc5668817(monkeypatch):
    monkeypatch.setenv("APSO_LLM", "0")
    controls.engage_kill_switch(False)
    store.incidents["INC5668817"].state = "In Progress"
    inv = run_investigation("INC5668817", auto=True)
    assert inv.completed
    assert len(inv.stage_results) >= 5
    assert inv.resolve_preview is not None
    assert inv.resolve_preview.get("confirmed") is False
    assert any(sr.hitl_required for sr in inv.stage_results)
