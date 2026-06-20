#!/usr/bin/env python3
"""
Mini-Drop control plane (Python simplified drop_server).
HTTP/JSON API aligned with proto/control + proto/healthcheck semantics.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

import uvicorn
import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("drop_server")

APISERVER = os.environ.get("APISERVER", "http://apiserver:8191")
OFFLINE_TIMEOUT_SEC = int(os.environ.get("AGENT_OFFLINE_SEC", "30"))

app = FastAPI(title="Mini-Drop Server")

_lock = threading.Lock()
_tasks: Dict[str, Deque[dict]] = {}
_agents: Dict[str, dict] = {}
_audit: List[dict] = []


class RecordArgv(BaseModel):
    hz: int = 99
    duration_sec: int = 10
    pid: int = 1
    event: str = "cpu-cycles"


class TaskDesc(BaseModel):
    task_id: str
    target_ip: str
    sample_argv: RecordArgv
    collector: str = "perf"
    timeout_sec: int = 60


class CreateTaskRequest(BaseModel):
    target_ip: str
    task_desc: TaskDesc


class HealthCheckRequest(BaseModel):
    hostname: str
    ip_addr: str
    agent_id: str
    agent_version: str = "0.1.0"


class TaskResult(BaseModel):
    task_id: str
    error_message: str = ""
    cos_key: str = ""
    artifact_type: str = "perf.data"


def _persist_audit(event: str, agent_id: str, detail: str = "") -> None:
    try:
        requests.post(
            f"{APISERVER}/api/v1/internal/agent_audit",
            json={"agent_id": agent_id, "event": event, "detail": detail},
            timeout=5,
        )
    except Exception as exc:
        LOG.warning("audit persist failed: %s", exc)


def audit(event: str, agent_id: str, detail: str = "") -> None:
    entry = {
        "event": event,
        "agent_id": agent_id,
        "detail": detail,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _audit.append(entry)
    LOG.info("audit %s agent=%s %s", event, agent_id, detail)
    _persist_audit(event, agent_id, detail)


@app.post("/control/create_task")
def create_task(req: CreateTaskRequest):
    ip = req.target_ip
    desc = req.task_desc.model_dump()
    with _lock:
        _tasks.setdefault(ip, deque()).append(desc)
    LOG.info("queued task %s for %s", desc["task_id"], ip)
    return {"ok": True, "message": "queued"}


@app.post("/healthcheck/do")
def healthcheck(req: HealthCheckRequest):
    now = datetime.now(timezone.utc).isoformat()
    was_offline = req.agent_id in _agents and not _agents[req.agent_id].get("online")
    with _lock:
        _agents[req.agent_id] = {
            "hostname": req.hostname,
            "ip_addr": req.ip_addr,
            "online": True,
            "last_seen": now,
            "last_seen_ts": time.time(),
        }
    if was_offline:
        audit("agent_online", req.agent_id, req.ip_addr)

    task_desc: Optional[dict] = None
    with _lock:
        q = _tasks.get(req.ip_addr)
        if not q and req.ip_addr != "127.0.0.1":
            q = _tasks.get("127.0.0.1")
        if q:
            task_desc = q.popleft()

    return {
        "status": "SERVING",
        "pending": task_desc is not None,
        "task_desc": task_desc,
    }


@app.post("/hotmethod/notify_result")
def notify_result(result: TaskResult):
    LOG.info("result task=%s err=%s key=%s", result.task_id, result.error_message, result.cos_key)
    return {"ok": True}


def _online_agents_for_ip(target_ip: str) -> List[dict]:
    """Match agents by IP; host-network agents may register with NIC IP while UI uses 127.0.0.1."""
    exact = [a for a in _agents.values() if a.get("ip_addr") == target_ip and a.get("online")]
    if exact:
        return exact
    if target_ip == "127.0.0.1":
        return [a for a in _agents.values() if a.get("online")]
    return []


@app.get("/control/stat_agent")
def stat_agent(target_ip: str):
    online_agents = _online_agents_for_ip(target_ip)
    if not online_agents:
        return {"online": False, "last_seen": "", "ip_addr": target_ip}
    a = online_agents[0]
    return {
        "online": True,
        "last_seen": a.get("last_seen", ""),
        "ip_addr": a.get("ip_addr", target_ip),
    }


@app.get("/control/list_agents")
def list_agents():
    with _lock:
        items = [
            {
                "hostname": info.get("hostname", ""),
                "ip": info.get("ip_addr", ""),
                "online": bool(info.get("online")),
                "last_seen": info.get("last_seen", ""),
            }
            for info in _agents.values()
        ]
    return {"items": items}


@app.get("/audit")
def list_audit(limit: int = 50):
    return {"items": _audit[-limit:]}


def offline_watchdog():
    while True:
        time.sleep(OFFLINE_TIMEOUT_SEC)
        cutoff = time.time() - OFFLINE_TIMEOUT_SEC
        with _lock:
            for aid, info in list(_agents.items()):
                last = info.get("last_seen_ts")
                if last is None:
                    continue
                if info.get("online") and last < cutoff:
                    info["online"] = False
                    audit("agent_offline", aid, f"heartbeat timeout {OFFLINE_TIMEOUT_SEC}s")


@app.on_event("startup")
def startup():
    for info in _agents.values():
        info["last_seen_ts"] = time.time()
    threading.Thread(target=offline_watchdog, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "50051"))
    uvicorn.run(app, host="0.0.0.0", port=port)
