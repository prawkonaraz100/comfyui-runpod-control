#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"

COMFYUI_DIR="$(find_comfyui)" || die "ComfyUI not found"
DEST="$COMFYUI_DIR/custom_nodes/RunPodGitHubRunnerAutoStart"
mkdir -p "$DEST"
cp -f "$ROOT/runner_autostart/__init__.py" "$DEST/__init__.py"

log "Installed GitHub runner auto-start hook:"
log "  $DEST/__init__.py"
log "It will start /workspace/actions-runner/run.sh whenever ComfyUI starts, if the runner is configured."
