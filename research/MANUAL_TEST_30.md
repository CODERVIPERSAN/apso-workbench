# APSO Manual Test — 30 Prompts

Base URL: `http://127.0.0.1:8000`
API smoke: **10/10** passed
Chat prompts: **30/30** passed (no SSE errors, events>0)

## API smoke

- ✅ `health` — {"ok": true, "status": 200, "keys": ["status", "kill_switch", "connectors"]}
- ✅ `status` — {"ok": true, "status": 200, "keys": ["incidents", "agents_active", "agents_total", "runs_today", "pending", "connected_systems", "running_tasks", "environment"]}
- ✅ `agents` — {"ok": true, "status": 200, "keys": "list"}
- ✅ `incidents` — {"ok": true, "status": 200, "keys": "list"}
- ✅ `knowledge` — {"ok": true, "status": 200, "keys": ["sops", "playbooks", "incidents"]}
- ✅ `module_dq` — {"ok": true, "status": 200, "keys": ["stage", "agent", "summary", "confidence", "tools_used", "evidence", "hitl_required", "hitl_id"]}
- ✅ `module_mf` — {"ok": true, "status": 200, "keys": ["stage", "agent", "summary", "confidence", "tools_used", "evidence", "hitl_required", "hitl_id"]}
- ✅ `module_log` — {"ok": true, "status": 200, "keys": ["stage", "agent", "summary", "confidence", "tools_used", "evidence", "hitl_required", "hitl_id"]}
- ✅ `module_code` — {"ok": true, "status": 200, "keys": ["stage", "agent", "summary", "confidence", "tools_used", "evidence", "hitl_required", "hitl_id"]}
- ✅ `module_rca` — {"ok": true, "status": 200, "keys": ["stage", "agent", "summary", "confidence", "tools_used", "evidence", "hitl_required", "hitl_id"]}

## Prompt results

### 01. Investigate INC5668817
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.01s

### 02. Show open P1 and P2 incidents
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 03. What is the status of INC5668801?
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 04. Assess ticket quality for INC5668817
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 05. Find similar incidents to INC5668817
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 06. Resolve INC5668817 with HITL preview only
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.01s

### 07. Paige triage INC5668817 — is it urgent?
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 08. Sort this incident urgent vs less urgent: CICS TOR1 high CPU
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 09. Run data quality checks on CUSTOMER_MASTER
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 10. Score completeness and uniqueness dimensions
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 11. Clean ticket fields for INC5668790
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 12. Get SAVRS spool for job PAYROLL01
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 13. Read JCL for PAYROLL01
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 14. Show ESP history for PAYROLL01
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 15. Why did PAYROLL01 abend S322?
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 16. Explain COBOL program PAYEXT
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 17. Analyze JCL PKCHUNK settings for payroll extract
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 18. Give optimize advice for PAYEXT
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 19. Search New Relic logs for PK Chunking timeout
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 20. Show payroll-batch application errors
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 21. Correlate logs with mainframe ABEND for INC5668817
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 22. Perform root cause analysis on INC5668817
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.01s

### 23. Suggest remediation using SOP-BATCH-014
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 24. Disable PK Chunking and prepare JCL rerun (HITL)
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 25. Run health check after PAYROLL01 fix
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 26. Close INC5668817 and draft problem record
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 27. Search knowledge for PK Chunking failure recovery
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.01s

### 28. Show agent swarm status and kill-switch state
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.01s

### 29. Orchestrator: run full multi-agent lifecycle on INC5668817
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

### 30. What tools will the log_analysis and code_analyzer agents use?
- result: **PASS**
- events: 80 · agents: change_analyzer, closure, code_analyzer, data_quality, health_check, impact, log_analysis, mainframe, orchestrator, paige, resolution, self_healing, triage · tools: assess_ticket_quality, esp_job_history, find_related_problem, find_similar_incidents, get_incident, get_nr_app_errors, health_check_job, list_dq_rules, read_cobol, read_jcl, savrs_job_spool, search_knowledge, search_nr_logs, submit_jcl_preview
- elapsed: 0.0s

## UI manual checks (browser)

Executed against `http://127.0.0.1:8000/?ui=manual30`:

| # | UI action | Result |
|---|-----------|--------|
| 1 | Load Agent Swarm page | PASS — orchestrator + 12 agent cards |
| 2 | Run multi-agent investigation | PASS — 13 cards DONE, 65+ message bubbles, HITL bar |
| 3 | Handoff chain populated | PASS — 24 handoff rows (assign + return) |
| 4 | Prompt: Search New Relic logs for PK Chunking timeout | PASS — swarm re-ran, HITL visible |
| 5 | Prompt: Explain COBOL program PAYEXT | PASS — done=13, hitl=true |
| 6 | Prompt: Get SAVRS spool for job PAYROLL01 | PASS |
| 7 | Prompt: Run data quality checks on CUSTOMER_MASTER | PASS |
| 8 | Prompt: Close INC5668817 and draft problem record | PASS |
| 9 | Prompt: Suggest remediation using SOP-BATCH-014 | PASS — bubbles grew to 455 |
| 10 | Lifecycle Map nav | PASS — stages Intake→Close with agent tags |
| 11 | HITL Apply write | PASS — apply response in message bus |
| 12 | Kill-switch off / Model indicator | PASS — footer Kill-switch: off |

**UI verdict:** Agent swarm, message bus, handoff chain, lifecycle map, and HITL gate all behaved as a multi-agent workbench for the exercised prompts.

**Note:** Backend 30-prompt sweep used `APSO_LLM=0` (deterministic tool path) so all 30 complete quickly. Live Ollama path is available when server is started without that flag.
