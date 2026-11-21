"""External API connectors — plug real credentials when provided.

Owned APIs (stubs until wired):
  - ServiceNow
  - New Relic
  - Mainframe (SAVRS/ESP/FTP)
  - Model (LLM serving)
"""

from apso.connectors import mainframe, model, newrelic, servicenow

__all__ = ["servicenow", "newrelic", "mainframe", "model"]
