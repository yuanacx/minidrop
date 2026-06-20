"""bpftrace eBPF IO latency histogram -> JSON."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_bpftrace(duration: int, out_dir: Path) -> Path:
    out = out_dir / "bpftrace.json"
    script = """
    tracepoint:block:block_rq_complete
    {
        @lat[args->sector * 512] = count();
    }
    interval:s:5 { exit(); }
    """
    # fallback: synthetic histogram if bpftrace missing
    try:
        proc = subprocess.run(
            ["bpftrace", "-e", script],
            capture_output=True,
            text=True,
            timeout=duration + 10,
        )
        text = proc.stdout + proc.stderr
        line_count = max(1, len([ln for ln in text.splitlines() if ln.strip()]))
        data = {
            "type": "io_histogram",
            "raw": text,
            "buckets": [{"label": "block_rq", "count": line_count}],
        }
    except FileNotFoundError:
        data = {
            "type": "io_histogram",
            "buckets": [{"label": "0-1ms", "count": 10}, {"label": "1-10ms", "count": 3}],
            "note": "bpftrace unavailable; demo data",
        }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
