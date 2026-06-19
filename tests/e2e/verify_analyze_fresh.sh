#!/usr/bin/env bash
set -e
cd /opt/minidrop

python3 -c "while True: pass" &
HOG_PID=$!
sleep 1
echo "HOG_PID=$HOG_PID"

RESP=$(curl -sf -X POST http://127.0.0.1:8191/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d "{\"target_ip\":\"127.0.0.1\",\"pid\":$HOG_PID,\"duration_sec\":10,\"hz\":99,\"collector\":\"perf\"}")
echo "=== create ==="
echo "$RESP"
TID=$(echo "$RESP" | jq -r '.data.tid')

for i in $(seq 1 25); do
  ST=$(curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq -r '.data.task.status')
  echo "poll $i status=$ST"
  [ "$ST" = "DONE" ] && break
  [ "$ST" = "FAILED" ] && break
  sleep 2
done

kill $HOG_PID 2>/dev/null || true

echo ""
echo "=== Step 1: POST /analyze ==="
curl -sv -X POST "http://127.0.0.1:8191/api/v1/tasks/$TID/analyze" 2>&1
echo ""

echo "=== Step 2: task after analyze ==="
curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq .

echo "=== Step 3: MinIO ==="
docker compose exec -T minio sh -c "ls -la /data/drop/$TID/ 2>&1"
