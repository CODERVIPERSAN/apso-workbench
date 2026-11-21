# Cursor architecture → APSO (original clone of *patterns*, not Cursor source)

> Analyzed local install `/usr/share/cursor` (Electron + VS Code fork) + public Cursor docs/blogs.  
> **No Cursor proprietary JS/asar was copied into this repo.**

## Cursor production shape (public)

| Cursor piece | Role |
|--------------|------|
| Electron + VS Code workbench | Shell: activity bar, side bar, editor, panels |
| Agent panel | Unified Ask / Agent / Plan / Debug modes |
| Instructions + Tools + Model | Agent triad |
| Tool cards in transcript | Search, edit, terminal, browser, … |
| Composer input | Bottom prompt; mode switcher |
| Projects / coordinator | Plan then delegate to sub-agents |
| Checkpoints | Restore before risky applies |
| Shadow workspace | Hidden validation loop (Cursor-specific) |
| MCP | External tool servers |

REA note: `/usr/share/cursor` is an Electron desktop app tree (`resources/app`, extensions like `cursor-agent-host`, `cursor-agent-exec`, `cursor-browser-automation`).

## APSO mapping (your product)

| Cursor pattern | APSO equivalent |
|----------------|-----------------|
| Activity bar | Chat · Agents · Incidents · Knowledge · Governance |
| Agent modes Ask/Agent/Plan | **Ask** (chat only) · **Agent** (swarm investigate) · **Plan** (orchestrator plan, no writes) |
| Tool cards | `get_incident`, `search_nr_logs`, `savrs_job_spool`, `read_jcl`, … |
| Sub-agents / Project | Paige, DQ, Triage, Logs, MF, Code, Resolution, HITL Closure |
| Apply / checkpoint | **HITL Apply** before ServiceNow write / JCL submit |
| Context sidebar | Open incident, urgency, connectors, kill-switch |
| Model picker | Ollama / `MODEL_*` endpoint |
| Composer | Bottom prompt “@INC5668817 Investigate…” |

## What we build (functionality only — not UI clone)

Cursor patterns implemented in **backend runtime**:

1. **Modes** (`apso/runtime/modes.py`): `ask` | `plan` | `agent`
   - Ask → single agent + **read-only** tool allowlist (no swarm, no write tools)
   - Plan → orchestrator plan only
   - Agent → full multi-agent lifecycle + HITL
2. **Instructions + Tools + Model triad** per `run_agent(...)`
3. **Checkpoints** (`apso/runtime/checkpoints.py`) before HITL Apply; restore on Reject
4. **Tool policy enforcement** — write tools blocked in Ask even if model requests them

APIs: `GET /api/modes`, `GET /api/checkpoints`, `POST /api/checkpoints/{id}/restore`, chat `mode` field.

UI is out of scope for this mapping — use any client; pass `{"mode":"ask|plan|agent"}`.
