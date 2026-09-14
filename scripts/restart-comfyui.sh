#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
COMFYUI_DIR="$(find_comfyui)" || die "ComfyUI not found"
PYTHON="$(find_python "$COMFYUI_DIR")" || die "Python not found"

log "Stopping existing ComfyUI main.py processes"
pkill -TERM -f "$COMFYUI_DIR/main.py" 2>/dev/null || true
for _ in {1..20}; do
  pgrep -f "$COMFYUI_DIR/main.py" >/dev/null 2>&1 || break
  sleep 1
done
pkill -KILL -f "$COMFYUI_DIR/main.py" 2>/dev/null || true

mkdir -p /workspace/logs
log "Starting ComfyUI on 0.0.0.0:8188"
cd "$COMFYUI_DIR"
nohup "$PYTHON" main.py --listen 0.0.0.0 --port 8188   > /workspace/logs/comfyui.log 2>&1 &
echo $! > /workspace/logs/comfyui.pid

for _ in {1..60}; do
  if curl -fsS --max-time 3 http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
    log "ComfyUI is healthy"
    exit 0
  fi
  sleep 2
done

tail -n 120 /workspace/logs/comfyui.log || true
die "ComfyUI did not become healthy within 120 seconds"
