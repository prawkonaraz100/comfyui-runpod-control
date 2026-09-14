#!/usr/bin/env bash
set -Eeuo pipefail
RUNNER_DIR="${RUNNER_DIR:-/workspace/actions-runner}"
cd "$RUNNER_DIR"

if pgrep -f "$RUNNER_DIR/bin/Runner.Listener" >/dev/null 2>&1 || pgrep -f 'Runner.Listener.*comfyui-runpod-control' >/dev/null 2>&1; then
  echo "GitHub runner already appears to be running."
  pgrep -af 'Runner.Listener' || true
  exit 0
fi

mkdir -p /workspace/logs
export RUNNER_ALLOW_RUNASROOT=1
nohup ./run.sh > /workspace/logs/github-runner.log 2>&1 &
echo $! > /workspace/logs/github-runner.pid
echo "Started GitHub runner PID $!"
sleep 3
tail -n 30 /workspace/logs/github-runner.log || true
