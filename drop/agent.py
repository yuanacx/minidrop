#!/usr/bin/env python3
"""Mini-Drop agent: heartbeat, task execution, collectors."""
from __future__ import annotations

import logging
import os
import socket
import threading
import time
from pathlib import Path

import requests

from collectors.bpftrace_collector import run_bpftrace
from collectors.cp_worker import continuous_profiling_loop
from collectors.perf_collector import run_perf
from collectors.pyspy_collector import run_pyspy
from storage_minio import upload_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("drop_agent")

SERVER = os.environ.get("DROP_SERVER", "http://127.0.0.1:50051")
APISERVER = os.environ.get("APISERVER", "http://127.0.0.1:8191")
AGENT_ID = os.environ.get("AGENT_ID", "agent-1")
HEARTBEAT_SEC = float(os.environ.get("HEARTBEAT_SEC", "5"))


def hostname() -> str:
    return socket.gethostname()


def ip_addr() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def notify_result(task_id: str, cos_key: str = "", error: str = "", artifact_type: str = "perf.data"):
    requests.post(
        f"{SERVER}/hotmethod/notify_result",
        json={
            "task_id": task_id,
            "error_message": error,
            "cos_key": cos_key,
            "artifact_type": artifact_type,
        },
        timeout=10,
    )
    try:
        requests.post(
            f"{APISERVER}/api/v1/internal/task_result",
            json={"tid": task_id, "cos_key": cos_key, "error": error},
            timeout=10,
        )
    except Exception as e:
        LOG.warning("apiserver notify failed: %s", e)


def execute_task(desc: dict) -> None:
    task_id = desc["task_id"]
    collector = desc.get("collector", "perf")
    argv = desc.get("sample_argv", {})
    pid = int(argv.get("pid", 1))
    duration = int(argv.get("duration_sec", 10))
    hz = int(argv.get("hz", 99))
    out_dir = Path("/tmp/minidrop") / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if collector == "perf":
            perf_path = run_perf(pid, duration, hz, out_dir)
            key = upload_file(task_id, perf_path, "perf.data")
            notify_result(task_id, cos_key=key, artifact_type="perf.data")
        elif collector == "pyspy":
            svg = run_pyspy(pid, duration, out_dir)
            key = upload_file(task_id, svg, "pyspy.svg")
            notify_result(task_id, cos_key=key, artifact_type="pyspy.svg")
        elif collector == "bpftrace":
            js = run_bpftrace(duration, out_dir)
            key = upload_file(task_id, js, "bpftrace.json")
            notify_result(task_id, cos_key=key, artifact_type="bpftrace.json")
        else:
            notify_result(task_id, error=f"unknown collector {collector}")
    except Exception as e:
        LOG.exception("task failed")
        notify_result(task_id, error=str(e))


def heartbeat_loop():
    while True:
        try:
            resp = requests.post(
                f"{SERVER}/healthcheck/do",
                json={
                    "hostname": hostname(),
                    "ip_addr": ip_addr(),
                    "agent_id": AGENT_ID,
                    "agent_version": "0.1.0",
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("pending") and data.get("task_desc"):
                desc = data["task_desc"]
                threading.Thread(target=execute_task, args=(desc,), daemon=True).start()
        except Exception as e:
            LOG.warning("heartbeat failed: %s", e)
        time.sleep(HEARTBEAT_SEC)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Mini-Drop drop_agent (heartbeat + collectors)")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    args = parser.parse_args()
    if args.version:
        print("drop_agent 0.1.0")
        sys.exit(0)

    threading.Thread(target=continuous_profiling_loop, daemon=True).start()
    heartbeat_loop()
