#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"

echo "=== time ==="
date -u
echo
echo "=== gpu ==="
nvidia-smi || true
echo
echo "=== disk ==="
df -h /workspace / 2>/dev/null || df -h
echo
echo "=== memory ==="
free -h || true
echo
echo "=== processes ==="
ps -ef | grep -E '[C]omfyUI|[m]ain.py|[R]unner.Listener|[r]un.sh' || true
echo
echo "=== comfyui ==="
curl -fsS --max-time 5 http://127.0.0.1:8188/system_stats || true
echo
echo
echo "=== runner ==="
pgrep -af 'Runner.Listener|run.sh' || true
