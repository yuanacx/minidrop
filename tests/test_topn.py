#!/usr/bin/env python3
"""Unit tests for TopN parser."""
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from topn import parse_collapsed, write_topn_json


class TestTopN(unittest.TestCase):
    def test_parse_collapsed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.txt"
            p.write_text("main;foo 10\nmain;bar 5\n", encoding="utf-8")
            top = parse_collapsed(p, limit=5)
            self.assertTrue(len(top) >= 2)
            names = {t["function"] for t in top}
            self.assertIn("foo", names)

    def test_write_json(self):
        with tempfile.TemporaryDirectory() as td:
            c = Path(td) / "c.txt"
            out = Path(td) / "top.json"
            c.write_text("a;b 3\n", encoding="utf-8")
            write_topn_json(c, out)
            data = json.loads(out.read_text())
            self.assertIsInstance(data, list)


if __name__ == "__main__":
    unittest.main()
