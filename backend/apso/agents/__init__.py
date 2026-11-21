from apso.agents import (
    closure,
    code_intelligence,
    data_quality,
    impact,
    log_analysis,
    mainframe_ops,
    remediation,
    ticket_ops,
    validation,
)

MODULES = {
    "incident_management": ticket_ops,
    "data_quality_management": data_quality,
    "mainframe_operations": mainframe_ops,
    "cobol_jcl_code_intelligence": code_intelligence,
    "log_analysis": log_analysis,
    "root_cause_analysis": impact,
    "ai_remediation": remediation,
    "testing_and_validation": validation,
    "ticket_resolution_and_closure": closure,
}

__all__ = ["MODULES"]
