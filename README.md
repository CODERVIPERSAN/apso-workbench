# APSO — App Support Workbench (AI Operations Platform)

Orchestrator-centric **multi-agent** ops workbench (ASW-style).  
You plug **ServiceNow / New Relic / Mainframe / Model** APIs; APSO owns the agents, HITL, and lifecycle.

## Quick start

```bash
cd /home/sandy/apso-workbench
chmod +x scripts/start.sh
./scripts/start.sh
# → http://127.0.0.1:8000
```

Demo: ask `Investigate INC5668817` (PK Chunking / HITL resolve preview).

## Architecture

```
Intake (Paige urgency + Data Quality)
  → Diagnose (SNOW · Logs/NR · Mainframe · COBOL · RCA)
  → Resolve (Remediation playbooks)  [HITL]
  → Verify (Health check)
  → Close (Resolve ticket)           [HITL]
```

Governance: RBAC, circuit breaker, kill-switch, confidence scoring, HITL Apply/Reject.

## Modules

| Module | Path |
|--------|------|
| Incident management | `agents/ticket_ops.py` |
| Data-quality management | `agents/data_quality.py` |
| Mainframe operations | `agents/mainframe_ops.py` |
| COBOL/JCL intelligence | `agents/code_intelligence.py` |
| Log analysis | `agents/log_analysis.py` |
| Root-cause analysis | `agents/impact.py` |
| AI remediation | `agents/remediation.py` |
| Testing & validation | `agents/validation.py` |
| Ticket resolution & closure | `agents/closure.py` |

Independent demos: `GET /api/modules/{name}/demo`

## Wire real APIs

```bash
export SNOW_BASE_URL=... SNOW_USER=... SNOW_PASS=...
export NR_API_KEY=... NR_ACCOUNT_ID=...
export MF_HOST=... MF_USER=... MF_PASS=...
export MODEL_BASE_URL=... MODEL_API_KEY=... MODEL_NAME=...
```

See `research/TARGET_APIS.md`.

## Tests

```bash
cd /home/sandy/apso-workbench
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
```
