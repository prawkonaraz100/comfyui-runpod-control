#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTION="${1:-}"

case "$ACTION" in
  status)
    exec bash "$ROOT/scripts/status.sh"
    ;;
  verify)
    exec bash "$ROOT/scripts/verify.sh"
    ;;
  provision)
    exec bash "$ROOT/scripts/provision-wan22-animate.sh"
    ;;
  restart_comfyui)
    exec bash "$ROOT/scripts/restart-comfyui.sh"
    ;;
  *)
    echo "Refusing unknown action: $ACTION" >&2
    echo "Allowed: status, verify, provision, restart_comfyui" >&2
    exit 64
    ;;
esac
