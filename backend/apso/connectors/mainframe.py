"""Mainframe connector — SAVRS/ESP/FTP style (stub → real when MF_* set)."""

from __future__ import annotations

import os
from typing import Any

from apso.store import store

MF_USER = os.getenv("MF_USER", "")
MF_PASS = os.getenv("MF_PASS", "")
MF_HOST = os.getenv("MF_HOST", "")


def live() -> bool:
    return bool(MF_HOST and MF_USER)


def job_spool(job_name: str) -> dict[str, Any]:
    job = store.jobs.get(job_name)
    if not job:
        return {"error": f"Job {job_name} not found"}
    return {"job": job_name, **job, "spool_excerpt": f"{job.get('step')}: {job.get('message')}"}


def read_jcl(job_name: str) -> dict[str, Any]:
    text = store.jcl.get(job_name)
    if not text:
        return {"error": f"JCL for {job_name} not found"}
    return {"job": job_name, "jcl": text}


def read_source(program: str) -> dict[str, Any]:
    text = store.cobol.get(program)
    if not text:
        return {"error": f"Source {program} not found"}
    return {"program": program, "source": text}


def esp_history(job_name: str) -> dict[str, Any]:
    job = store.jobs.get(job_name, {})
    return {
        "job": job_name,
        "scheduler": job.get("scheduler", "ESP"),
        "runs": [{"at": job.get("last_run"), "status": job.get("last_status"), "abend": job.get("abend")}],
    }


def submit_jcl(job_name: str, jcl: str | None = None, *, confirmed: bool = False) -> dict[str, Any]:
    body = jcl or store.jcl.get(job_name, "")
    preview = {"job": job_name, "jcl_preview": body[:400], "confirmed": confirmed}
    if not confirmed:
        return {"ok": False, "hitl": True, "preview": preview, "message": "HITL required — no JCL submit until you Apply."}
    # Simulate success after approval
    if job_name in store.jobs:
        store.jobs[job_name]["last_status"] = "CC 0000"
        store.jobs[job_name]["abend"] = None
        store.jobs[job_name]["message"] = "Completed after PKCHUNK=N rerun"
    return {"ok": True, "job": job_name, "status": "SUBMITTED", "confirmed": True}
