#!/usr/bin/env python3
"""Tests for rule-based advisor."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from advisor import load_rules, match_suggestions  # noqa: E402


class TestAdvisor(unittest.TestCase):
    def test_match_suggestions(self):
        with tempfile.TemporaryDirectory() as td:
            rules = Path(td) / "rules.yaml"
            rules.write_text(
                "- regex: 'malloc'\n  advice: 'check heap'\n",
                encoding="utf-8",
            )
            topn = [{"function": "malloc", "samples": 10}]
            out = match_suggestions(topn, rules)
            self.assertEqual(len(out), 1)
            self.assertIn("heap", out[0]["advice"])

    def test_load_rules_empty(self):
        with tempfile.TemporaryDirectory() as td:
            rules = Path(td) / "rules.yaml"
            rules.write_text("[]", encoding="utf-8")
            self.assertEqual(load_rules(rules), [])


if __name__ == "__main__":
    unittest.main()
