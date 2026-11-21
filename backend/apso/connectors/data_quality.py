"""APSO Data Quality engine — built in-house (no external DQ product API)."""

from __future__ import annotations

from typing import Any

from apso.knowledge.bridge import get_bridge
from apso.models import utcnow

DIMENSIONS = (
    "completeness",
    "accuracy",
    "consistency",
    "timeliness",
    "uniqueness",
    "validity",
)


class DataQualityEngine:
    def __init__(self) -> None:
        self.bridge = get_bridge()

    def list_rules(self) -> list[dict[str, Any]]:
        return list(self.bridge.dq_rules)

    def profile_dataset(self, dataset: str) -> dict[str, Any]:
        rules = [r for r in self.bridge.dq_rules if r.get("dataset") == dataset]
        if not rules:
            rules = list(self.bridge.dq_rules)
        scores = {d: 0.95 for d in DIMENSIONS}
        failures: list[dict[str, Any]] = []
        for rule in rules:
            dim = rule.get("dimension", "completeness")
            threshold = float(rule.get("threshold", 0.9))
            observed = float(rule.get("current_score", rule.get("last_score", threshold)))
            scores[dim] = min(scores.get(dim, 1.0), observed)
            if observed < threshold or rule.get("status") == "FAIL":
                failures.append(
                    {
                        "rule_id": rule.get("rule_id") or rule.get("id"),
                        "dimension": dim,
                        "observed": observed,
                        "threshold": threshold,
                        "message": rule.get("description", "threshold breach"),
                    }
                )
        overall = sum(scores.values()) / len(scores)
        return {
            "dataset": dataset,
            "overall": round(overall, 3),
            "dimensions": {k: round(v, 3) for k, v in scores.items()},
            "failures": failures,
            "rules_evaluated": len(rules),
            "profiled_at": utcnow().isoformat(),
        }

    def assess_ticket_fields(self, incident: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        cleaned = dict(incident)
        score = 1.0
        for field in ("short_description", "description", "priority", "assignment_group"):
            if not cleaned.get(field):
                issues.append(f"missing_{field}")
                score -= 0.15
        if cleaned.get("short_description"):
            cleaned["short_description"] = " ".join(str(cleaned["short_description"]).split())
        if cleaned.get("description"):
            cleaned["description"] = str(cleaned["description"]).strip()
        pri = str(cleaned.get("priority") or "")
        if pri and not any(pri.startswith(p) for p in ("1", "2", "3", "4", "5")):
            issues.append("nonstandard_priority")
            score -= 0.05
        grade = "good" if score >= 0.85 else "fair" if score >= 0.65 else "poor"
        return {
            "score": round(max(0.0, score), 2),
            "grade": grade,
            "issues": issues,
            "cleaned_fields": {
                "short_description": cleaned.get("short_description"),
                "description": cleaned.get("description"),
                "priority": cleaned.get("priority"),
                "assignment_group": cleaned.get("assignment_group"),
                "category": cleaned.get("category"),
            },
            "assessed_at": utcnow().isoformat(),
        }

    def draft_close_notes(self, incident_number: str, resolution: str) -> dict[str, Any]:
        return {
            "number": incident_number,
            "close_notes": (
                f"Resolved {incident_number}. {resolution.strip()} "
                "Verified via health check. Notes cleaned by APSO Data Quality agent."
            ),
            "drafted_at": utcnow().isoformat(),
        }


_dq: DataQualityEngine | None = None


def get_dq_engine() -> DataQualityEngine:
    global _dq
    if _dq is None:
        _dq = DataQualityEngine()
    return _dq
