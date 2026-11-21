from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"


class Stage(str, Enum):
    INTAKE = "intake"
    DIAGNOSE = "diagnose"
    RESOLVE = "resolve"
    VERIFY = "verify"
    CLOSE = "close"


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    duration_ms: int = 0


class StageResult(BaseModel):
    stage: str
    agent: str
    summary: str
    confidence: float = 0.0
    tools_used: list[ToolCall] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    hitl_required: bool = False
    hitl_id: str | None = None


class HITLRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"hitl-{uuid4().hex[:8]}")
    action: str
    target: str
    preview: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending | approved | rejected
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None


class Incident(BaseModel):
    number: str
    sys_id: str
    short_description: str
    description: str = ""
    priority: str = "3"
    state: str = "New"
    assignment_group: str = ""
    ci: str = ""
    value_stream: str = ""
    opened_at: str = ""
    caller: str = ""
    work_notes: str = ""
    close_notes: str = ""
    quality_score: float | None = None


class InvestigationState(BaseModel):
    id: str = Field(default_factory=lambda: f"inv-{uuid4().hex[:8]}")
    incident_number: str
    stage: Stage = Stage.INTAKE
    urgency: str = "low"  # from Paige: high | low
    messages: list[str] = Field(default_factory=list)
    stage_results: list[StageResult] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    rca: dict[str, Any] | None = None
    resolve_preview: dict[str, Any] | None = None
    hitl: HITLRequest | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    auto: bool = True
    # Cursor-style modes: ask (chat) | agent (swarm) | plan (orchestrator plan only)
    mode: str = "agent"


class InvestigateRequest(BaseModel):
    incident_number: str
    auto: bool = True
