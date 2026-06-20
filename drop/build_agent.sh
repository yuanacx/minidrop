#!/usr/bin/env bash
# Build standalone drop_agent binary (run on Linux for ECS deployment).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q pyinstaller -r requirements.txt
python3 -m PyInstaller --clean --noconfirm drop_agent.spec
ls -lh dist/drop_agent
echo "SUCCESS: dist/drop_agent"
