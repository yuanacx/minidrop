#!/usr/bin/env bash
set -e
cd /opt/minidrop
apt-get install -y jq >/dev/null 2>&1 || true

echo "=== DB tid column ==="
docker compose exec -T postgres psql -U postgres -d drop -c "\d tasks" | head -20

echo "=== create task ==="
RESP=$(curl -sf -X POST http://127.0.0.1:8191/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"target_ip":"127.0.0.1","pid":1,"duration_sec":5,"hz":49,"collector":"perf"}')
echo "$RESP"
TID=$(echo "$RESP" | jq -r '.data.tid')
echo "TID=$TID"

echo "=== poll task ==="
for i in $(seq 1 20); do
  echo "--- poll $i ---"
  curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq '.data.task | {tid,status,status_reason,cos_key,analysis_status}'
  ST=$(curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq -r '.data.task.status')
  [ "$ST" = "DONE" ] && break
  [ "$ST" = "FAILED" ] && break
  sleep 3
done

echo "=== list tasks ==="
curl -sf http://127.0.0.1:8191/api/v1/tasks | jq .

echo "=== minio data ==="
docker compose exec -T minio sh -c "ls -laR /data/ 2>/dev/null | head -40"

echo "=== drop_agent tail ==="
docker compose logs drop_agent --tail 15
