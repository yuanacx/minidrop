"""perf record collector."""
from __future__ import annotations

import subprocess
from pathlib import Path


def run_perf(pid: int, duration: int, hz: int, out_dir: Path) -> Path:
    out = out_dir / "perf.data"
    cmd = [
        "perf", "record",
        "-F", str(hz),
        "-g",
        "-p", str(pid),
        "-o", str(out),
        "--", "sleep", str(duration),
    ]
    subprocess.run(cmd, check=True, timeout=duration + 30)
    return out
