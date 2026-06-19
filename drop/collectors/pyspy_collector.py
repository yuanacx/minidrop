"""py-spy user-space collector."""
from __future__ import annotations

import subprocess
from pathlib import Path


def run_pyspy(pid: int, duration: int, out_dir: Path) -> Path:
    out = out_dir / "profile.svg"
    cmd = [
        "py-spy", "record",
        "-o", str(out),
        "-d", str(duration),
        "-p", str(pid),
    ]
    subprocess.run(cmd, check=True, timeout=duration + 30)
    return out
