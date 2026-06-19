#!/usr/bin/env python3
"""Rule-based suggestions from TopN function names."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict

import yaml


def load_rules(path: Path) -> List[Dict]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw or []


def match_suggestions(topn: List[Dict], rules_path: Path) -> List[Dict]:
    rules = load_rules(rules_path)
    out: List[Dict] = []
    for item in topn:
        fn = item.get("function", "")
        for rule in rules:
            if re.search(rule["regex"], fn, re.I):
                out.append({"function": fn, "advice": rule["advice"]})
                break
    return out
