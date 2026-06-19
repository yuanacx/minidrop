#!/usr/bin/env bash
# E2E test scenarios (run on Linux with stack up)
set -e
API=${API:-http://localhost:8191/api/v1}

echo "=== E2E-1 normal path ==="
T=$(curl -sf -X POST "$API/tasks" -H 'Content-Type: application/json' \
  -d '{"target_ip":"127.0.0.1","pid":1,"duration_sec":5,"hz":49,"collector":"perf"}' | jq -r '.data.tid')
echo "tid=$T"
for i in $(seq 1 30); do
  ST=$(curl -sf "$API/tasks/$T" | jq -r '.data.task.status')
  echo "status=$ST"
  [ "$ST" = "DONE" ] && break
  sleep 2
done

echo "=== E2E-2 bad pid ==="
curl -sf -X POST "$API/tasks" -H 'Content-Type: application/json' \
  -d '{"target_ip":"127.0.0.1","pid":999999,"duration_sec":2,"collector":"perf"}' | jq .

echo "=== E2E-3 agent offline (wrong ip) ==="
curl -sf -X POST "$API/tasks" -H 'Content-Type: application/json' \
  -d '{"target_ip":"10.255.255.1","pid":1,"duration_sec":2,"collector":"perf"}' | jq .

echo "E2E script finished"
