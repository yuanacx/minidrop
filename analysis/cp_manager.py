#!/usr/bin/env python3
"""List and analyze Continuous Profiling snapshots in MinIO cp/."""
from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from hotmethod_analyzer import analyze_perf
from storage import client_from_env, download_object, upload_file

LOG = logging.getLogger("cp_manager")


def list_snapshots(window_sec: int = 300) -> list[dict]:
    client = client_from_env()
    bucket = _bucket()
    cutoff = time.time() - window_sec
    timestamps: dict[int, str] = {}
    for obj in client.list_objects(bucket, prefix="cp/", recursive=True):
        parts = obj.object_name.split("/")
        if len(parts) < 3 or parts[-1] != "perf.data":
            continue
        try:
            ts = int(parts[1])
        except ValueError:
            continue
        if ts >= cutoff:
            timestamps[ts] = obj.object_name
    return [
        {
            "ts": ts,
            "time": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "perf_key": timestamps[ts],
        }
        for ts in sorted(timestamps.keys())
    ]


def analyze_snapshot(ts: int) -> dict:
    bucket = _bucket()
    perf_key = f"cp/{ts}/perf.data"
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        perf_path = work / "perf.data"
        download_object(bucket, perf_key, perf_path)
        out_dir = work / "out"
        result = analyze_perf(perf_path, out_dir)
        svg_path = Path(result["svg"])
        svg_key = f"cp/{ts}/flamegraph.svg"
        upload_file(bucket, svg_key, svg_path, "image/svg+xml")
    return {"ts": ts, "svg_key": svg_key, "flamegraph_url": f"/artifacts/cp/{ts}/flamegraph.svg"}


def _bucket() -> str:
    import os

    return os.environ.get("MINIO_BUCKET", "drop")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Mini-Drop CP snapshot manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_p = sub.add_parser("list")
    list_p.add_argument("--window", type=int, default=300)

    analyze_p = sub.add_parser("analyze")
    analyze_p.add_argument("--ts", type=int, required=True)

    args = parser.parse_args()
    try:
        if args.cmd == "list":
            print(json.dumps({"snapshots": list_snapshots(args.window)}, ensure_ascii=False))
        else:
            print(json.dumps(analyze_snapshot(args.ts), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
