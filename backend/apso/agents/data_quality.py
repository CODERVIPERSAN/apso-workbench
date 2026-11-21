"""Data-quality management — built in APSO (not Informatica product)."""

from __future__ import annotations

from typing import Any

from apso.models import StageResult, ToolCall
from apso.store import store


REQUIRED_TICKET_FIELDS = [
    "short_description",
    "description",
    "assignment_group",
    "ci",
    "priority",
    "value_stream",
]


def clean_ticket_fields(incident: dict[str, Any]) -> dict[str, Any]:
    missing = [f for f in REQUIRED_TICKET_FIELDS if not incident.get(f)]
    present = len(REQUIRED_TICKET_FIELDS) - len(missing)
    score = round(present / len(REQUIRED_TICKET_FIELDS), 2)
    cleaned = dict(incident)
    if cleaned.get("short_description"):
        cleaned["short_description"] = cleaned["short_description"].strip()
    return {
        "quality_score": score,
        "missing_fields": missing,
        "areas": {
            "identity": bool(incident.get("ci") and incident.get("assignment_group")),
            "narrative": bool(incident.get("short_description") and incident.get("description")),
            "routing": bool(incident.get("value_stream")),
            "priority": bool(incident.get("priority")),
        },
        "cleaned": cleaned,
    }


def profile_dataset(dataset: str) -> dict[str, Any]:
    rules = [r for r in store.dq_rules if r.get("dataset") == dataset]
    dims = {r["dimension"]: r for r in rules}
    overall = 1.0
    for r in rules:
        if r.get("current") is not None:
            overall = min(overall, float(r["current"]) / float(r["threshold"]) if r["threshold"] else 0)
    return {"dataset": dataset, "rules": rules, "dimensions": dims, "score": round(min(overall, 1.0), 3)}


def score_dimensions(dataset: str | None = None) -> dict[str, Any]:
    rules = store.dq_rules if not dataset else [r for r in store.dq_rules if r["dataset"] == dataset]
    by_dim: dict[str, list[float]] = {}
    for r in rules:
        if r.get("current") is None:
            continue
        by_dim.setdefault(r["dimension"], []).append(float(r["current"]))
    return {k: round(sum(v) / len(v), 3) for k, v in by_dim.items()}


def run(state: dict[str, Any]) -> StageResult:
    incident = state.get("incident") or {}
    tool = ToolCall(name="assess_ticket_quality", args={"number": incident.get("number")})
    result = clean_ticket_fields(incident)
    tool.result = result
    # Also attach dataset profile if CI looks like a dataset
    ci = incident.get("ci") or ""
    extra = {}
    if ci and ci in {r["dataset"] for r in store.dq_rules}:
        extra = profile_dataset(ci)
    return StageResult(
        stage="intake",
        agent="data_quality",
        summary=(
            "Ticket looks complete."
            if not result["missing_fields"]
            else f"Ticket is missing: {', '.join(result['missing_fields'])}."
        ),
        confidence=0.9,
        tools_used=[tool],
        evidence={"ticket_quality": result, "dataset_profile": extra},
    )
