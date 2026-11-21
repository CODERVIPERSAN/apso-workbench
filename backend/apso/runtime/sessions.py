"""Per-session chat memory so the LLM can remember prior turns."""

from __future__ import annotations

import re
import threading
import uuid
from typing import Any

_INC = re.compile(r"\b(INC\d+)\b", re.I)


class SessionMemory:
    def __init__(self, *, max_turns: int = 24) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, list[dict[str, str]]] = {}
        self._active_incident: dict[str, str] = {}
        self._last_intent: dict[str, str] = {}
        self.max_turns = max_turns

    def ensure(self, session_id: str | None) -> str:
        sid = (session_id or "").strip() or str(uuid.uuid4())
        with self._lock:
            self._sessions.setdefault(sid, [])
        return sid

    def append(self, session_id: str, role: str, content: str) -> None:
        text = (content or "").strip()
        if not text:
            return
        with self._lock:
            hist = self._sessions.setdefault(session_id, [])
            hist.append({"role": role, "content": text[:4000]})
            if len(hist) > self.max_turns:
                self._sessions[session_id] = hist[-self.max_turns :]
            m = _INC.search(text)
            if m:
                self._active_incident[session_id] = m.group(1).upper()

    def set_intent(self, session_id: str, intent: str) -> None:
        if intent and intent not in {"GREETING", "GENERAL", "STATUS"}:
            with self._lock:
                self._last_intent[session_id] = intent

    def last_intent(self, session_id: str) -> str | None:
        with self._lock:
            return self._last_intent.get(session_id)

    def active_incident(self, session_id: str) -> str | None:
        with self._lock:
            if session_id in self._active_incident:
                return self._active_incident[session_id]
            # scan history newest-first
            for m in reversed(self._sessions.get(session_id) or []):
                hit = _INC.search(m["content"])
                if hit:
                    num = hit.group(1).upper()
                    self._active_incident[session_id] = num
                    return num
        return None

    def history(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            return list(self._sessions.get(session_id) or [])

    def as_prompt_block(self, session_id: str, *, limit: int = 12) -> str:
        hist = self.history(session_id)[-limit:]
        if not hist:
            return ""
        lines = []
        for m in hist:
            who = "Engineer" if m["role"] == "user" else "APSO"
            lines.append(f"{who}: {m['content']}")
        sticky = self.active_incident(session_id)
        head = "Earlier in this chat:\n" + "\n".join(lines)
        if sticky:
            head = f"Active ticket in this chat: {sticky}\n" + head
        return head


sessions = SessionMemory()
