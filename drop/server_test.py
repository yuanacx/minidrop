#!/usr/bin/env python3
"""Unit tests for drop_server agent registry and audit."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))

import server  # noqa: E402


class TestDropServer(unittest.TestCase):
    def setUp(self):
        server._agents.clear()
        server._tasks.clear()
        server._audit.clear()
        self.client = TestClient(server.app)

    @mock.patch("server._persist_audit")
    def test_healthcheck_registers_agent(self, mock_persist):
        resp = self.client.post(
            "/healthcheck/do",
            json={
                "hostname": "host1",
                "ip_addr": "172.18.1.5",
                "agent_id": "agent-1",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "SERVING")
        stat = self.client.get("/control/stat_agent", params={"target_ip": "127.0.0.1"})
        self.assertTrue(stat.json()["online"])
        mock_persist.assert_not_called()

    @mock.patch("server._persist_audit")
    def test_stat_agent_exact_ip(self, _mock_persist):
        self.client.post(
            "/healthcheck/do",
            json={"hostname": "h", "ip_addr": "10.0.0.1", "agent_id": "a1"},
        )
        stat = self.client.get("/control/stat_agent", params={"target_ip": "10.0.0.1"})
        self.assertTrue(stat.json()["online"])

    @mock.patch("server._persist_audit")
    def test_create_task_and_dispatch(self, _mock_persist):
        self.client.post(
            "/control/create_task",
            json={
                "target_ip": "127.0.0.1",
                "task_desc": {
                    "task_id": "t1",
                    "target_ip": "127.0.0.1",
                    "sample_argv": {"pid": 1, "duration_sec": 5, "hz": 99},
                },
            },
        )
        resp = self.client.post(
            "/healthcheck/do",
            json={"hostname": "h", "ip_addr": "172.18.1.5", "agent_id": "a1"},
        )
        data = resp.json()
        self.assertTrue(data["pending"])
        self.assertEqual(data["task_desc"]["task_id"], "t1")

    @mock.patch("server._persist_audit")
    def test_offline_watchdog_marks_offline(self, mock_persist):
        server._agents["a1"] = {
            "hostname": "h",
            "ip_addr": "127.0.0.1",
            "online": True,
            "last_seen": "old",
            "last_seen_ts": time.time() - 60,
        }
        server.OFFLINE_TIMEOUT_SEC = 30
        cutoff = time.time() - server.OFFLINE_TIMEOUT_SEC
        with server._lock:
            for aid, info in list(server._agents.items()):
                last = info.get("last_seen_ts")
                if info.get("online") and last < cutoff:
                    info["online"] = False
                    server.audit("agent_offline", aid, "test")
        stat = self.client.get("/control/stat_agent", params={"target_ip": "127.0.0.1"})
        self.assertFalse(stat.json()["online"])
        events = [c.args[0] for c in mock_persist.call_args_list]
        self.assertIn("agent_offline", events)

    def test_list_agents(self):
        server._agents["a1"] = {
            "hostname": "h",
            "ip_addr": "1.2.3.4",
            "online": True,
            "last_seen": "2026-01-01T00:00:00Z",
        }
        resp = self.client.get("/control/list_agents")
        self.assertEqual(len(resp.json()["items"]), 1)


if __name__ == "__main__":
    unittest.main()
