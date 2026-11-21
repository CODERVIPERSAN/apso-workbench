"""LLM connector — Ollama by default (llama3.2), OpenAI-compatible override."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

BASE = os.getenv("MODEL_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"))
API_KEY = os.getenv("MODEL_API_KEY", "ollama")
MODEL = os.getenv("MODEL_NAME", os.getenv("PAIGE_LLM_MODEL", "llama3.2:latest"))


def live() -> bool:
    try:
        r = httpx.get(f"{BASE.rstrip('/')}/models", timeout=2.0)
        return r.status_code < 500
    except Exception:  # noqa: BLE001
        return False


def chat(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.2,
    tool_choice: str | None = "auto",
) -> dict[str, Any]:
    """OpenAI-compatible chat.completions. Returns raw message dict."""
    payload: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
    try:
        r = httpx.post(
            f"{BASE.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=payload,
            timeout=120.0,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]
    except Exception as exc:  # noqa: BLE001
        return {"role": "assistant", "content": f"[llm unavailable: {exc}]", "tool_calls": None}


def _offline(system: str, user: str) -> str:
    blob = f"{system}\n{user}".lower()
    if "pk chunk" in blob or "payroll01" in blob or "inc5668817" in blob:
        return (
            "PAYROLL01 failed during the EXTRACT step because PK Chunking timed out. "
            "The usual fix is to turn PK Chunking off and rerun the job. "
            "I will need your OK before we change the ticket or rerun anything."
        )
    if "json array" in blob or "agent names" in blob:
        return json.dumps(
            [
                "paige",
                "data_quality",
                "triage",
                "impact",
                "log_analysis",
                "change_analyzer",
                "mainframe",
                "code_analyzer",
                "resolution",
                "self_healing",
                "health_check",
                "closure",
            ]
        )
    if "cobol" in blob or "jcl" in blob:
        return "The program turns on the PK Chunking path when that flag is set to Y."
    return "I finished looking. Review what we found, then say OK if you want us to apply a change."


def complete(system: str, user: str, **_: Any) -> str:
    if os.getenv("APSO_LLM", "1") == "0":
        return _offline(system, user)
    msg = chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        tools=None,
    )
    return (msg.get("content") or "").strip()


def tool_schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


def parse_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    raw = message.get("tool_calls") or []
    out = []
    for tc in raw:
        fn = tc.get("function") or {}
        args = fn.get("arguments") or "{}"
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_raw": args}
        out.append({"id": tc.get("id", ""), "name": fn.get("name", ""), "args": args})
    return out
