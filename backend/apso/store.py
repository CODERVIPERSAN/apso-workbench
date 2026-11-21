"""In-memory cognitive bridge + seed loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apso.models import HITLRequest, Incident, InvestigationState

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "seed.json"


class Store:
    def __init__(self) -> None:
        self.incidents: dict[str, Incident] = {}
        self.problems: list[dict[str, Any]] = []
        self.jobs: dict[str, Any] = {}
        self.jcl: dict[str, str] = {}
        self.cobol: dict[str, str] = {}
        self.sops: list[dict[str, Any]] = []
        self.dq_rules: list[dict[str, Any]] = []
        self.nr_logs: list[dict[str, Any]] = []
        self.playbooks: list[dict[str, Any]] = []
        self.investigations: dict[str, InvestigationState] = {}
        self.hitl: dict[str, HITLRequest] = {}
        self.runs_today: int = 17
        self.kill_switch: bool = False  # must stay off for agents to run
        self.load()


    def load(self) -> None:
        raw = json.loads(DATA.read_text())
        for row in raw["incidents"]:
            inc = Incident(**row)
            self.incidents[inc.number] = inc
        self.problems = list(raw.get("problems") or [])
        self.jobs = dict(raw.get("jobs") or {})
        self.jcl = dict(raw.get("jcl") or {})
        self.cobol = dict(raw.get("cobol") or {})
        self.sops = list(raw.get("sops") or [])
        self.dq_rules = list(raw.get("dq_rules") or [])
        self.nr_logs = list(raw.get("nr_logs") or [])
        self.playbooks = list(raw.get("playbooks") or [])


store = Store()
