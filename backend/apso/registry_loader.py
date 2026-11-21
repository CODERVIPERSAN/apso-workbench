from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "registry"


def load_agents() -> list[dict[str, Any]]:
    data = yaml.safe_load((REG / "agents.yaml").read_text())
    return list(data.get("agents") or [])


def load_capabilities() -> list[dict[str, Any]]:
    data = yaml.safe_load((REG / "capabilities.yaml").read_text())
    return list(data.get("capabilities") or [])


def agent_status_map() -> dict[str, str]:
    return {a["name"]: a.get("status", "ACTIVE") for a in load_agents()}
