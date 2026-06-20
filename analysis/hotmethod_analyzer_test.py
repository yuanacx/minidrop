#!/usr/bin/env python3
"""Unit tests for hotmethod_analyzer (mock MinIO + subprocess)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hotmethod_analyzer as ha  # noqa: E402


class TestHotmethodAnalyzer(unittest.TestCase):
    @mock.patch.object(ha, "match_suggestions", return_value=[])
    @mock.patch.object(ha, "perf_to_flamegraph")
    def test_analyze_perf(self, mock_p2f, _mock_sug):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            svg = work / "flamegraph.svg"
            svg.write_text("<svg/>", encoding="utf-8")
            collapsed = work / "collapsed.txt"
            collapsed.write_text("main;foo 10\n", encoding="utf-8")
            mock_p2f.return_value = (svg, collapsed)
            perf = work / "perf.data"
            perf.write_bytes(b"mock")
            out_dir = work / "out"
            result = ha.analyze_perf(perf, out_dir)
            self.assertTrue(Path(result["svg"]).exists())
            self.assertTrue((out_dir / "top.json").exists())

    @mock.patch.object(ha, "upload_file")
    @mock.patch.object(ha, "download_object")
    @mock.patch.object(ha, "analyze_perf")
    def test_main_with_cos_key(self, mock_analyze, mock_dl, _mock_ul):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            svg = out / "t1" / "flamegraph.svg"
            svg.parent.mkdir(parents=True)
            svg.write_text("<svg/>", encoding="utf-8")
            mock_analyze.return_value = {
                "svg": str(svg),
                "topn": [{"function": "foo", "samples": 1}],
                "suggestions": [],
            }
            mock_dl.side_effect = lambda _b, _k, dest: dest.write_bytes(b"x")
            argv = [
                "hotmethod_analyzer.py",
                "--task-id", "t1",
                "--cos-key", "t1/perf.data",
                "--output-dir", str(out),
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = ha.main()
            self.assertEqual(rc, 0)

    def test_main_missing_input(self):
        with mock.patch.object(sys, "argv", ["hotmethod_analyzer.py", "--task-id", "x"]):
            rc = ha.main()
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
