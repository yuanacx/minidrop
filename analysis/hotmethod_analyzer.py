#!/usr/bin/env python3
"""
Mini-Drop analysis entrypoint.
perf.data -> flamegraph.svg + top.json + suggestions.md
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from advisor import match_suggestions
from storage import download_object, upload_file
from topn import write_topn_json

LOG = logging.getLogger("hotmethod_analyzer")
FLAMEGRAPH_DIR = Path(os.environ.get("FLAMEGRAPH_DIR", "/opt/FlameGraph"))


def run_cmd(cmd: list, cwd: Path | None = None) -> None:
    LOG.info("run: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)


def perf_to_flamegraph(perf_data: Path, work: Path) -> tuple[Path, Path]:
    script_txt = work / "perf.script.txt"
    collapsed = work / "collapsed.txt"
    svg = work / "flamegraph.svg"
    stackcollapse = FLAMEGRAPH_DIR / "stackcollapse-perf.pl"
    flamegraph = FLAMEGRAPH_DIR / "flamegraph.pl"
    if not stackcollapse.exists():
        stackcollapse = Path(__file__).parent / "vendor" / "stackcollapse-perf.pl"
    if not flamegraph.exists():
        flamegraph = Path(__file__).parent / "vendor" / "flamegraph.pl"
    with script_txt.open("w", encoding="utf-8") as f:
        subprocess.run(
            ["perf", "script", "-i", str(perf_data), "--header", "--no-inline"],
            stdout=f,
            check=True,
        )
    with collapsed.open("w", encoding="utf-8") as f:
        subprocess.run(
            ["perl", str(stackcollapse), str(script_txt)],
            stdout=f,
            check=True,
        )
    with svg.open("w", encoding="utf-8") as f:
        subprocess.run(
            ["perl", str(flamegraph), str(collapsed)],
            stdout=f,
            check=True,
        )
    return svg, collapsed


def analyze_perf(perf_data: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        svg, collapsed = perf_to_flamegraph(perf_data, work)
        topn_path = out_dir / "top.json"
        topn = write_topn_json(collapsed, topn_path)
        rules = Path(__file__).parent / "rules.yaml"
        suggestions = match_suggestions(topn, rules)
        sug_path = out_dir / "suggestions.md"
        lines = ["# 规则建议\n"]
        for s in suggestions:
            lines.append(f"- **{s['function']}**：{s['advice']}\n")
        sug_path.write_text("".join(lines), encoding="utf-8")
        final_svg = out_dir / "flamegraph.svg"
        final_svg.write_bytes(svg.read_bytes())
    return {
        "svg": str(final_svg),
        "topn": topn,
        "suggestions": suggestions,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Mini-Drop hotmethod analyzer")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--cos-key", default="", help="MinIO object key for perf.data")
    parser.add_argument("--local-perf", default="", help="Local perf.data path (dev)")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--output-dir", default="./output")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) / args.task_id
    bucket = os.environ.get("MINIO_BUCKET", "drop")

    try:
        if args.local_perf:
            perf_path = Path(args.local_perf)
        elif args.cos_key:
            perf_path = out_dir / "perf.data"
            download_object(bucket, args.cos_key, perf_path)
        else:
            print(json.dumps({"error": "need --local-perf or --cos-key"}), file=sys.stderr)
            return 2

        result = analyze_perf(perf_path, out_dir)
        if not args.no_save and args.cos_key:
            upload_file(bucket, f"{args.task_id}/flamegraph.svg", Path(result["svg"]), "image/svg+xml")
            upload_file(bucket, f"{args.task_id}/top.json", out_dir / "top.json", "application/json")
        print(json.dumps({"ok": True, "task_id": args.task_id, **result}, ensure_ascii=False))
        return 0
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
