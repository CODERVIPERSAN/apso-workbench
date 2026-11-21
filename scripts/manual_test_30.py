#!/usr/bin/env python3
"""Manual regression: 30 crafted prompts against APSO backend (+ optional UI notes)."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"

PROMPTS = [
    # Incident / ServiceNow
    "Investigate INC5668817",
    "Show open P1 and P2 incidents",
    "What is the status of INC5668801?",
    "Assess ticket quality for INC5668817",
    "Find similar incidents to INC5668817",
    "Resolve INC5668817 with HITL preview only",
    # Paige / triage
    "Paige triage INC5668817 — is it urgent?",
    "Sort this incident urgent vs less urgent: CICS TOR1 high CPU",
    # Data quality
    "Run data quality checks on CUSTOMER_MASTER",
    "Score completeness and uniqueness dimensions",
    "Clean ticket fields for INC5668790",
    # Mainframe
    "Get SAVRS spool for job PAYROLL01",
    "Read JCL for PAYROLL01",
    "Show ESP history for PAYROLL01",
    "Why did PAYROLL01 abend S322?",
    # COBOL / code
    "Explain COBOL program PAYEXT",
    "Analyze JCL PKCHUNK settings for payroll extract",
    "Give optimize advice for PAYEXT",
    # Logs / New Relic
    "Search New Relic logs for PK Chunking timeout",
    "Show payroll-batch application errors",
    "Correlate logs with mainframe ABEND for INC5668817",
    # RCA / remediation
    "Perform root cause analysis on INC5668817",
    "Suggest remediation using SOP-BATCH-014",
    "Disable PK Chunking and prepare JCL rerun (HITL)",
    # Validate / close
    "Run health check after PAYROLL01 fix",
    "Close INC5668817 and draft problem record",
    # Knowledge / governance / swarm
    "Search knowledge for PK Chunking failure recovery",
    "Show agent swarm status and kill-switch state",
    "Orchestrator: run full multi-agent lifecycle on INC5668817",
    "What tools will the log_analysis and code_analyzer agents use?",
]


def http_json(method: str, path: str, body: dict | None = None, timeout: float = 120.0):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}


def http_sse_chat(message: str, timeout: float = 180.0) -> dict:
    req = urllib.request.Request(
        BASE + "/api/chat",
        data=json.dumps({"message": message, "auto": True}).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    events = []
    errors = []
    agents = set()
    tools = set()
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        buf = b""
        while True:
            chunk = resp.read(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n\n" in buf:
                part, buf = buf.split(b"\n\n", 1)
                line = part.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                try:
                    ev = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                events.append(ev)
                if ev.get("type") == "error":
                    errors.append(ev.get("text"))
                if ev.get("agent"):
                    agents.add(ev["agent"])
                if ev.get("type") == "tool_done" and ev.get("tool"):
                    tools.add(ev["tool"])
                if ev.get("type") == "done" and "investigation_id" in ev:
                    pass
    return {
        "elapsed_s": round(time.time() - t0, 2),
        "events": len(events),
        "agents": sorted(agents),
        "tools": sorted(tools),
        "errors": errors,
        "ok": not errors and len(events) > 0,
        "last_types": [e.get("type") for e in events[-5:]],
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parents[1] / "research"
    out_dir.mkdir(exist_ok=True)
    report_path = out_dir / "MANUAL_TEST_30.md"

    # Baseline API checks
    checks = []
    for name, fn in [
        ("health", lambda: http_json("GET", "/api/health")),
        ("status", lambda: http_json("GET", "/api/status")),
        ("agents", lambda: http_json("GET", "/api/agents")),
        ("incidents", lambda: http_json("GET", "/api/incidents")),
        ("knowledge", lambda: http_json("GET", "/api/knowledge/search?q=" + urllib.parse.quote("PK Chunking"))),
        ("module_dq", lambda: http_json("GET", "/api/modules/data_quality_management/demo")),
        ("module_mf", lambda: http_json("GET", "/api/modules/mainframe_operations/demo")),
        ("module_log", lambda: http_json("GET", "/api/modules/log_analysis/demo")),
        ("module_code", lambda: http_json("GET", "/api/modules/cobol_jcl_code_intelligence/demo")),
        ("module_rca", lambda: http_json("GET", "/api/modules/root_cause_analysis/demo")),
    ]:
        try:
            status, body = fn()
            checks.append({"name": name, "ok": status == 200, "status": status, "keys": list(body)[:8] if isinstance(body, dict) else type(body).__name__})
        except Exception as exc:  # noqa: BLE001
            checks.append({"name": name, "ok": False, "error": str(exc)})

    # Ensure kill-switch off
    try:
        http_json("POST", "/api/governance/kill-switch?on=false")
    except Exception:
        pass

    results = []
    print(f"Running {len(PROMPTS)} chat prompts against {BASE} …")
    for i, prompt in enumerate(PROMPTS, 1):
        print(f"[{i:02d}/30] {prompt[:70]}", flush=True)
        try:
            r = http_sse_chat(prompt)
            r["prompt"] = prompt
            r["n"] = i
            results.append(r)
            flag = "PASS" if r["ok"] else "FAIL"
            print(f"       {flag} events={r['events']} agents={len(r['agents'])} tools={len(r['tools'])} {r['elapsed_s']}s", flush=True)
            if r["errors"]:
                print(f"       errors={r['errors'][:2]}", flush=True)
        except Exception as exc:  # noqa: BLE001
            results.append({"n": i, "prompt": prompt, "ok": False, "errors": [str(exc)], "events": 0, "agents": [], "tools": [], "elapsed_s": 0})
            print(f"       FAIL {exc}", flush=True)

    passed = sum(1 for r in results if r.get("ok"))
    api_passed = sum(1 for c in checks if c.get("ok"))

    lines = [
        "# APSO Manual Test — 30 Prompts",
        "",
        f"Base URL: `{BASE}`",
        f"API smoke: **{api_passed}/{len(checks)}** passed",
        f"Chat prompts: **{passed}/{len(results)}** passed (no SSE errors, events>0)",
        "",
        "## API smoke",
        "",
    ]
    for c in checks:
        lines.append(f"- {'✅' if c.get('ok') else '❌'} `{c['name']}` — {json.dumps({k: v for k, v in c.items() if k != 'name'})}")

    lines += ["", "## Prompt results", ""]
    for r in results:
        lines.append(f"### {r['n']:02d}. {r['prompt']}")
        lines.append(f"- result: **{'PASS' if r.get('ok') else 'FAIL'}**")
        lines.append(f"- events: {r.get('events')} · agents: {', '.join(r.get('agents') or []) or '—'} · tools: {', '.join(r.get('tools') or []) or '—'}")
        lines.append(f"- elapsed: {r.get('elapsed_s')}s")
        if r.get("errors"):
            lines.append(f"- errors: `{r['errors']}`")
        lines.append("")

    report_path.write_text("\n".join(lines))
    print(f"\nWrote {report_path}")
    print(f"SUMMARY api={api_passed}/{len(checks)} chat={passed}/{len(results)}")
    return 0 if passed == len(results) and api_passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
