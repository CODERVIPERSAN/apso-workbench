# APSO — External APIs (provided) vs Built Modules

## You provide (connector stubs ready)

| System | Env vars | Connector |
|--------|----------|-----------|
| ServiceNow | `SNOW_BASE_URL`, `SNOW_USER`, `SNOW_PASS` | `connectors/servicenow.py` |
| New Relic | `NR_API_KEY`, `NR_ACCOUNT_ID` | `connectors/newrelic.py` |
| Mainframe | `MF_HOST`, `MF_USER`, `MF_PASS` | `connectors/mainframe.py` |
| Model | `MODEL_BASE_URL`, `MODEL_API_KEY`, `MODEL_NAME` | `connectors/model.py` |

Until env vars are set, connectors run against `data/seed.json` (demo mode).

## APSO builds (agentic modules)

1. Incident management  
2. Data-quality management (built here — not Informatica product)  
3. Mainframe operations (agent over MF API)  
4. COBOL/JCL code intelligence (agent over model + MF source)  
5. Log analysis (agent over New Relic API)  
6. Root-cause analysis  
7. AI remediation  
8. Testing and validation  
9. Ticket resolution and closure  

## Architecture cloned

ASW App Support Workbench pattern from production reference:
- Registry-driven agents (`registry/agents.yaml`)
- Gateway wrap (circuit breaker, fail-soft)
- SSE chat / investigation stream
- HITL gates before SNOW write / JCL submit
- Paige-style intake urgency classification
- 5-stage lifecycle: intake → diagnose → resolve → verify → close

## Open-source references (not vendored)

- Zowe CLI / SDK — mainframe API patterns  
- IBM Z Open Editor — COBOL/JCL language ideas  
- ServiceNow Table API + MCP Server Console  
- OpenMetadata / OpenDQV — DQ rule patterns for our DQ agent  
