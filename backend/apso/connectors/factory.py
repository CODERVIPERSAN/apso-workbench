from __future__ import annotations

from apso.connectors.mainframe import MainframeConnector
from apso.connectors.servicenow import ServiceNowConnector
from apso.connectors.watsonx_z import WatsonxZConnector

_snow: ServiceNowConnector | None = None
_mf: MainframeConnector | None = None
_wx: WatsonxZConnector | None = None


def get_servicenow() -> ServiceNowConnector:
    global _snow
    if _snow is None:
        _snow = ServiceNowConnector()
    return _snow


def get_mainframe() -> MainframeConnector:
    global _mf
    if _mf is None:
        _mf = MainframeConnector()
    return _mf


def get_watsonx() -> WatsonxZConnector:
    global _wx
    if _wx is None:
        _wx = WatsonxZConnector()
    return _wx
