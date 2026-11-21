"""Cursor-style functional modes — Ask / Agent / Plan (behavior, not UI).

Ask   = instructions + read-only tools + model (no writes, no swarm lifecycle)
Plan  = orchestrator produces agent plan only (no tool side effects beyond reads)
Agent = full multi-agent lifecycle + HITL checkpoints before writes
"""

from __future__ import annotations

from typing import Any

# Tools that mutate or stage external writes (even preview → HITL path)
WRITE_TOOLS = frozenset(
    {
        "resolve_ticket_preview",
        "submit_jcl_preview",
        "resolve_ticket",
        "submit_jcl",
        "update_ticket_fields",
        "run_playbook",
    }
)

READ_TOOLS = frozenset(
    {
        "get_incident",
        "assess_ticket_quality",
        "find_similar_incidents",
        "find_related_problem",
        "search_nr_logs",
        "get_nr_app_errors",
        "savrs_job_spool",
        "read_jcl",
        "read_cobol",
        "esp_job_history",
        "search_knowledge",
        "list_dq_rules",
        "health_check_job",
    }
)

# Cursor Ask ≈ single agent with broad read tools
ASK_AGENT_TOOLS = sorted(READ_TOOLS)


class ModePolicy:
    """Enforce Cursor-like mode semantics in the runtime."""

    def normalize(self, mode: str | None) -> str:
        m = (mode or "agent").lower().strip()
        return m if m in {"ask", "agent", "plan"} else "agent"

    def filter_tools(self, mode: str, tools: list[str]) -> list[str]:
        mode = self.normalize(mode)
        if mode == "ask":
            return [t for t in tools if t in READ_TOOLS]
        if mode == "plan":
            # Plan may only use ultra-light reads for context
            return [t for t in tools if t in {"get_incident", "search_knowledge"}]
        return list(tools)

    def allows_swarm(self, mode: str) -> bool:
        return self.normalize(mode) == "agent"

    def allows_write_preview(self, mode: str) -> bool:
        return self.normalize(mode) == "agent"

    def ask_toolset(self) -> list[str]:
        return list(ASK_AGENT_TOOLS)

    def describe(self, mode: str) -> dict[str, Any]:
        mode = self.normalize(mode)
        return {
            "mode": mode,
            "swarm": self.allows_swarm(mode),
            "write_preview": self.allows_write_preview(mode),
            "tool_policy": "read_only" if mode in {"ask", "plan"} else "read_write_hitl",
        }


mode_policy = ModePolicy()
