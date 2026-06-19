"""Continuous profiling: periodic perf samples to MinIO."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from collectors.perf_collector import run_perf
from storage_minio import upload_file

LOG = logging.getLogger("cp_worker")
INTERVAL = int(os.environ.get("CP_INTERVAL_SEC", "60"))
SAMPLE_SEC = int(os.environ.get("CP_SAMPLE_SEC", "10"))
CP_PID = int(os.environ.get("CP_TARGET_PID", "1"))


def continuous_profiling_loop():
    while True:
        try:
            ts = int(time.time())
            out_dir = Path("/tmp/minidrop/cp") / str(ts)
            out_dir.mkdir(parents=True, exist_ok=True)
            perf_path = run_perf(CP_PID, SAMPLE_SEC, 49, out_dir)
            upload_file(f"cp/{ts}", perf_path, "perf.data")
            LOG.info("cp sample uploaded ts=%s", ts)
        except Exception as e:
            LOG.warning("cp failed: %s", e)
        time.sleep(INTERVAL)
