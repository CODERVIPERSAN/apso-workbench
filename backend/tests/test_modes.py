import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apso.orchestrator.agent_runtime import run_agent
from apso.runtime.checkpoints import checkpoints
from apso.runtime.modes import WRITE_TOOLS, mode_policy
from apso.store import store


def test_ask_filters_write_tools():
    tools = ["get_incident", "submit_jcl_preview", "search_nr_logs"]
    filtered = mode_policy.filter_tools("ask", tools)
    assert "submit_jcl_preview" not in filtered
    assert "get_incident" in filtered
    assert mode_policy.allows_swarm("ask") is False


def test_agent_allows_swarm_and_writes():
    assert mode_policy.allows_swarm("agent") is True
    assert mode_policy.allows_write_preview("agent") is True
    assert "submit_jcl_preview" in mode_policy.filter_tools("agent", list(WRITE_TOOLS | {"get_incident"}))


def test_ask_agent_blocks_write_tool(monkeypatch):
    monkeypatch.setenv("APSO_LLM", "0")
    ctx = {"incident": store.incidents["INC5668817"].model_dump()}
    # Force include a write tool in override — mode filter must strip it
    result = run_agent(
        "ask",
        task="test",
        context=ctx,
        mode="ask",
        tool_override=["get_incident", "submit_jcl_preview"],
    )
    names = [t.name for t in result.tools_used]
    assert "submit_jcl_preview" not in names
    assert "get_incident" in names


def test_checkpoint_create_and_restore():
    store.incidents["INC5668817"].state = "In Progress"
    cid = checkpoints.create(reason="test", incident_number="INC5668817")
    store.incidents["INC5668817"].state = "Resolved"
    out = checkpoints.restore(cid)
    assert out["ok"] is True
    assert store.incidents["INC5668817"].state == "In Progress"
