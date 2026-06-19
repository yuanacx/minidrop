#!/usr/bin/env bash
set -e
cd /opt/minidrop
TID=99ccee16

echo "=== Step 1: POST /analyze ==="
curl -sv -X POST "http://127.0.0.1:8191/api/v1/tasks/$TID/analyze" 2>&1
echo ""
echo ""

echo "=== Step 2: poll analysis_status ==="
for i in $(seq 1 15); do
  echo "--- poll $i ---"
  curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq '.data.task | {tid,status,cos_key,analysis_status,status_reason}'
  AS=$(curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq -r '.data.task.analysis_status')
  [ "$AS" = "done" ] || [ "$AS" = "DONE" ] && break
  sleep 2
done
echo ""
curl -sf "http://127.0.0.1:8191/api/v1/tasks/$TID" | jq .
echo ""

echo "=== Step 3: MinIO files ==="
docker compose exec -T minio sh -c "ls -la /data/drop/$TID/ 2>&1 || ls -laR /data/drop/ 2>&1 | grep -A5 $TID | head -30"

echo ""
echo "=== apiserver logs (analyze) ==="
docker compose logs apiserver --tail 20
