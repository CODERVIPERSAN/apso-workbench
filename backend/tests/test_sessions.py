import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apso.runtime.sessions import SessionMemory


def test_session_remembers_turns():
    mem = SessionMemory(max_turns=10)
    sid = mem.ensure(None)
    assert sid
    mem.append(sid, "user", "clean INC5668817")
    mem.append(sid, "assistant", "Ticket looks complete.")
    block = mem.as_prompt_block(sid)
    assert "INC5668817" in block
    assert "complete" in block
    assert mem.active_incident(sid) == "INC5668817"
    # same session id reused
    assert mem.ensure(sid) == sid


def test_history_capped():
    mem = SessionMemory(max_turns=4)
    sid = mem.ensure("s1")
    for i in range(6):
        mem.append(sid, "user", f"msg{i}")
    hist = mem.history(sid)
    assert len(hist) == 4
    assert hist[0]["content"] == "msg2"
