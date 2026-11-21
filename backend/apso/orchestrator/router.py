"""4-layer intent routing cascade (ASW pattern) — regex first."""

from __future__ import annotations

import re
from typing import Any

GREETING = re.compile(
    r"^\s*(hi|hello|hey|yo|sup|thanks|thank you|good (morning|afternoon|evening)|how are you)[!?.\s]*$",
    re.I,
)

INVESTIGATE = re.compile(
    r"\b(investigate|investigation|analyze|analysis|triage|look into|diagnose|run (the )?swarm|"
    r"full (multi-?agent )?lifecycle|open (the )?case)\b",
    re.I,
)

# DQ / ticket cleanup (includes common typo "lean" → clean)
CLEAN = re.compile(
    r"\b(clean|lean|scrub|normalize|assess (ticket )?quality|ticket quality|"
    r"dq|data quality|completeness|conformity|uniqueness|"
    r"anything missing|what('?s| is) missing|missing (on|in) (it|the ticket)|"
    r"is (the )?ticket complete|filled in)\b",
    re.I,
)

# Follow-ups that should stick to the active ticket in session
FOLLOW_UP = re.compile(
    r"\b(what should i do next|what('?s| is) next|next step|same (ticket|job|one)|"
    r"that ticket|this ticket|about it|on it|for it|remind me|what (did|have) we|"
    r"what (were|are) we talking|continue|and then)\b",
    re.I,
)

# Intent → specialist agent for single-agent dispatch (no full swarm)
INTENT_AGENT: dict[str, str] = {
    "DQ": "data_quality",
    "SERVICENOW": "paige",
    "MAINFRAME": "mainframe",
    "CODE": "code_analyzer",
    "LOGS": "log_analysis",
    "RCA": "impact",
    "REMEDIATE": "resolution",
    "VALIDATE": "health_check",
    "CLOSE": "closure",
}

RULES: list[tuple[re.Pattern[str], str]] = [
    (CLEAN, "DQ"),
    (re.compile(r"\b(INC\d+)\b", re.I), "SERVICENOW"),
    (re.compile(r"\b(incident|snow|servicenow|ticket|hitl|resolve ticket)\b", re.I), "SERVICENOW"),
    (re.compile(r"\b(job|jcl|abend|mainframe|esp|savrs|spool)\b", re.I), "MAINFRAME"),
    (re.compile(r"\b(cobol|copybook|program-id|watsonx|code analyzer|payext)\b", re.I), "CODE"),
    (re.compile(r"\b(log|newrelic|nrql|error rate|trace)\b", re.I), "LOGS"),
    (re.compile(r"\b(rca|root cause|correlate|impact)\b", re.I), "RCA"),
    (re.compile(r"\b(remediat|fix|heal|playbook|rerun)\b", re.I), "REMEDIATE"),
    (re.compile(r"\b(verify|validate|health check)\b", re.I), "VALIDATE"),
    (re.compile(r"\b(resolve|close|closure)\b", re.I), "CLOSE"),
    (re.compile(r"\b(agent|swarm|orchestrator|kill-?switch|status)\b", re.I), "STATUS"),
]


def is_greeting(message: str) -> bool:
    return bool(GREETING.match((message or "").strip()))


def wants_investigation(message: str) -> bool:
    text = message or ""
    if extract_incident(text) and INVESTIGATE.search(text):
        return True
    if INVESTIGATE.search(text):
        return True
    # bare INC id → treat as investigate that ticket
    if re.fullmatch(r"\s*INC\d+\s*", text, re.I):
        return True
    return False


def classify_intent(message: str, prior: str | None = None) -> dict[str, Any]:
    text = (message or "").strip()
    if is_greeting(text):
        return {"intent": "GREETING", "layer": 0, "priority": "P5", "sticky": False}
    if wants_investigation(text):
        return {"intent": "INVESTIGATE", "layer": 1, "priority": "P2", "sticky": False}
    # Prefer DQ when clean/quality/missing verbs present (even if INC id also matches)
    if CLEAN.search(text):
        return {"intent": "DQ", "layer": 1, "priority": "P3", "sticky": False}
    for pat, intent in RULES:
        if pat.search(text):
            return {"intent": intent, "layer": 1, "priority": "P3", "sticky": False}
    if FOLLOW_UP.search(text) and prior:
        return {"intent": prior, "layer": 3, "priority": "P3", "sticky": True}
    if FOLLOW_UP.search(text):
        return {"intent": "FOLLOW_UP", "layer": 3, "priority": "P3", "sticky": True}
    if prior:
        return {"intent": prior, "layer": 3, "priority": "P3", "sticky": True}
    return {"intent": "GENERAL", "layer": 4, "priority": "P3", "sticky": False}


def agent_for_intent(intent: str) -> str | None:
    if intent == "FOLLOW_UP":
        return "resolution"
    return INTENT_AGENT.get(intent)


def extract_incident(message: str) -> str | None:
    m = re.search(r"\b(INC\d+)\b", message or "", re.I)
    return m.group(1).upper() if m else None
