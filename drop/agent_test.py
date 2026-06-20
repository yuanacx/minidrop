#!/usr/bin/env python3
"""Unit tests for drop agent heartbeat and task execution."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent  # noqa: E402


class TestAgentHelpers(unittest.TestCase):
    def test_hostname(self):
        name = agent.hostname()
        self.assertIsInstance(name, str)
        self.assertTrue(len(name) > 0)

    @mock.patch("agent.socket.socket")
    def test_ip_addr(self, mock_socket):
        sock = mock.MagicMock()
        sock.getsockname.return_value = ("172.18.1.2", 0)
        mock_socket.return_value = sock
        self.assertEqual(agent.ip_addr(), "172.18.1.2")


class TestNotifyResult(unittest.TestCase):
    @mock.patch("agent.requests.post")
    def test_notify_success(self, mock_post):
        agent.notify_result("tid1", cos_key="tid1/perf.data")
        self.assertGreaterEqual(mock_post.call_count, 2)
        urls = [c.args[0] for c in mock_post.call_args_list]
        self.assertTrue(any("/hotmethod/notify_result" in u for u in urls))
        self.assertTrue(any("/internal/task_result" in u for u in urls))


class TestExecuteTask(unittest.TestCase):
    @mock.patch("agent.notify_result")
    @mock.patch("agent.upload_file", return_value="t1/perf.data")
    @mock.patch("agent.run_perf")
    def test_execute_perf(self, mock_perf, mock_upload, mock_notify):
        mock_perf.return_value = Path("/tmp/minidrop/t1/perf.data")
        desc = {
            "task_id": "t1",
            "collector": "perf",
            "sample_argv": {"pid": 99, "duration_sec": 2, "hz": 99},
        }
        agent.execute_task(desc)
        mock_perf.assert_called_once()
        mock_notify.assert_called_once()
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0], "t1")
        self.assertEqual(kwargs.get("cos_key"), "t1/perf.data")


class TestHeartbeatLoop(unittest.TestCase):
    @mock.patch("agent.time.sleep", side_effect=InterruptedError("stop"))
    @mock.patch("agent.requests.post")
    def test_heartbeat_pulls_task(self, mock_post, _mock_sleep):
        mock_post.return_value.json.return_value = {
            "status": "SERVING",
            "pending": True,
            "task_desc": {"task_id": "hb1", "collector": "perf", "sample_argv": {"pid": 1}},
        }
        mock_post.return_value.raise_for_status = mock.Mock()
        with mock.patch("agent.threading.Thread") as mock_thread:
            with self.assertRaises(InterruptedError):
                agent.heartbeat_loop()
            mock_thread.assert_called_once()


if __name__ == "__main__":
    unittest.main()
