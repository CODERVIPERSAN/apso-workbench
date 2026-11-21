"""Mock Informatica-like Data Quality connector."""

from __future__ import annotations

from typing import Any

from apso.knowledge.bridge import get_bridge
from apso.models import utcnow


DIMENSIONS = ("completeness", "accuracy", "consistency", "uniqueness", "timeliness", "validity")


class InformaticaDQConnector:
    def __init__(self) -> None:
        self.bridge = get_bridge()

    def list_rules(self, dataset: str | None = None) -> list[dict[str, Any]]:
        rules = list(self.bridge.dq_rules)
        if dataset:
            rules = [r for r in rules if r.get("dataset") == dataset]
        return rules

    def profile(self, dataset: str) -> dict[str, Any]:
        rules = self.list_rules(dataset)
        failing = [r for r in rules if r.get("status") == "FAIL"]
        return {
            "dataset": dataset,
            "profiled_at": utcnow().isoformat(),
            "rule_count": len(rules),
            "failing_count": len(failing),
            "failing_rules": failing,
            "sample_rows_scanned": 1_250_000 if "CUST" in dataset.upper() else 100_000,
            "notes": (
                "PK chunk key uniqueness failed for CUST_EXTRACT_STAGING"
                if dataset == "CUST_EXTRACT_STAGING"
                else "Profile complete"
            ),
        }

    def score(self, dataset: str | None = None) -> dict[str, Any]:
        rules = self.list_rules(dataset) if dataset else list(self.bridge.dq_rules)
        by_dim: dict[str, list[float]] = {d: [] for d in DIMENSIONS}
        for rule in rules:
            dim = rule.get("dimension")
            if dim in by_dim:
                by_dim[dim].append(float(rule.get("current_score") or 0.0))

        dimensions: dict[str, float] = {}
        for dim, scores in by_dim.items():
            if scores:
                dimensions[dim] = round(sum(scores) / len(scores), 3)
            else:
                dimensions[dim] = 1.0 if not dataset else 0.0

        overall = (
            round(sum(dimensions.values()) / len(dimensions), 3) if dimensions else 0.0
        )
        return {
            "dataset": dataset or "ALL",
            "overall": overall,
            "dimensions": dimensions,
            "scored_at": utcnow().isoformat(),
            "failing_rules": [r["rule_id"] for r in rules if r.get("status") == "FAIL"],
        }
