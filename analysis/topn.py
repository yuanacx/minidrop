#!/usr/bin/env python3
"""Parse collapsed stack lines into TopN JSON."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import List, Dict


def parse_collapsed(path: Path, limit: int = 20) -> List[Dict]:
    counts: Counter = Counter()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        stack, _samples = parts
        for frame in stack.split(";"):
            if frame:
                counts[frame] += 1
    top = counts.most_common(limit)
    return [{"function": fn, "samples": n} for fn, n in top]


def write_topn_json(collapsed: Path, out: Path) -> List[Dict]:
    data = parse_collapsed(collapsed)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
