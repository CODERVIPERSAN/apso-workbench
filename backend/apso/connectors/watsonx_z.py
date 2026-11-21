"""Mock watsonx Code Assistant for Z — COBOL/JCL intelligence."""

from __future__ import annotations

import re
from typing import Any

from apso.knowledge.bridge import get_bridge


class WatsonxZConnector:
    def __init__(self) -> None:
        self.bridge = get_bridge()

    def explain_cobol(self, name: str) -> dict[str, Any]:
        prog = self.bridge.get_cobol(name)
        if not prog:
            return {"name": name, "found": False, "explanation": None}
        source = prog.get("source") or ""
        paras = re.findall(r"^\s{0,7}([A-Z0-9-]+)\.\s*$", source, re.MULTILINE)
        flags = []
        if "PK-CHUNK" in source or "PKCHUNK" in source.upper() or "PK_CHUNK" in source:
            flags.append("Uses PK Chunking extract path controlled by WS-PK-CHUNKING-FLAG")
        if "EXEC CICS" in source:
            flags.append("CICS command-level program")
        explanation = (
            f"Program {prog.get('program')} in {prog.get('library')} performs "
            f"{len(paras) or 'main'} paragraph(s). "
            + (" ".join(flags) if flags else "Standard batch/online COBOL.")
        )
        return {
            "name": name,
            "found": True,
            "program": prog.get("program"),
            "paragraphs": paras,
            "dependencies": prog.get("dependencies") or [],
            "explanation": explanation,
            "flags": flags,
        }

    def cfg_summary(self, name: str) -> dict[str, Any]:
        prog = self.bridge.get_cobol(name)
        if not prog:
            return {"name": name, "found": False}
        source = prog.get("source") or ""
        nodes = re.findall(r"^\s{0,7}([A-Z0-9-]+)\.\s*$", source, re.MULTILINE)
        edges: list[dict[str, str]] = []
        performs = re.findall(r"PERFORM\s+([A-Z0-9-]+)", source)
        for target in performs:
            edges.append({"from": nodes[0] if nodes else "MAIN", "to": target, "type": "PERFORM"})
        calls = re.findall(r"CALL\s+'([^']+)'", source)
        for target in calls:
            edges.append({"from": nodes[0] if nodes else "MAIN", "to": target, "type": "CALL"})
        return {
            "name": name,
            "found": True,
            "nodes": nodes or ["MAIN"],
            "edges": edges,
            "summary": f"{len(nodes)} paragraphs, {len(edges)} control-flow edges",
        }

    def optimize_advice(self, name: str) -> dict[str, Any]:
        explained = self.explain_cobol(name)
        advice: list[str] = []
        if not explained.get("found"):
            return {"name": name, "found": False, "advice": []}
        flags = explained.get("flags") or []
        if any("PK Chunking" in f for f in flags):
            advice.append(
                "For ABEND during PK Chunking, disable chunking (PKCHUNK=N) and run full extract "
                "per SOP-BATCH-PKCHUNK-001, then reassess chunk size after data cleanup."
            )
            advice.append("Validate unique chunk keys before re-enabling PK Chunking.")
        if any("CICS" in f for f in flags):
            advice.append("Review LSR pool and DB2 thread waits for online latency.")
        if not advice:
            advice.append("No high-priority optimization signals detected.")
        return {"name": name, "found": True, "advice": advice}

    def transform_preview(self, name: str, transformation: str = "disable_pk_chunking") -> dict[str, Any]:
        prog = self.bridge.get_cobol(name)
        if not prog:
            return {"name": name, "found": False}
        source = prog.get("source") or ""
        preview = source
        notes: list[str] = []
        if transformation == "disable_pk_chunking":
            preview = source.replace(
                "01  WS-PK-CHUNKING-FLAG    PIC X(01) VALUE 'Y'.",
                "01  WS-PK-CHUNKING-FLAG    PIC X(01) VALUE 'N'.",
            )
            notes.append("Preview only — sets WS-PK-CHUNKING-FLAG default to N")
            notes.append("Prefer JCL SYSIN PKCHUNK=N for operational bypass without recompile")
        return {
            "name": name,
            "found": True,
            "transformation": transformation,
            "preview": preview,
            "notes": notes,
            "applied": False,
        }
