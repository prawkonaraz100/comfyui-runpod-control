#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${1:-artifacts/gpu-preflight}"
mkdir -p "$OUT_DIR"

write_cmd() {
  local name="$1"
  shift
  {
    echo "$ $*"
    "$@"
  } >"$OUT_DIR/$name.txt" 2>&1 || true
}

write_cmd nvidia-smi nvidia-smi
write_cmd python python3 --version
write_cmd ffmpeg ffmpeg -version
write_cmd disk df -h /workspace
write_cmd memory free -h

{
  echo "== ComfyUI locations =="
  for candidate in     /workspace/runpod-slim/ComfyUI     /workspace/ComfyUI     /workspace/comfyui; do
    if [[ -d "$candidate" ]]; then
      echo "FOUND $candidate"
    else
      echo "MISSING $candidate"
    fi
  done

  echo
  echo "== ComfyUI HTTP =="
  if curl -fsS --max-time 5 http://127.0.0.1:8188/system_stats >/tmp/faceless-system-stats.json 2>/dev/null; then
    echo "READY http://127.0.0.1:8188"
    python3 - <<'PY'
import json
from pathlib import Path
p = Path("/tmp/faceless-system-stats.json")
data = json.loads(p.read_text())
system = data.get("system", {})
devices = data.get("devices", [])
print("os:", system.get("os"))
print("python_version:", system.get("python_version"))
print("embedded_python:", system.get("embedded_python"))
for index, device in enumerate(devices):
    print(f"device[{index}].name:", device.get("name"))
    print(f"device[{index}].type:", device.get("type"))
    print(f"device[{index}].vram_total:", device.get("vram_total"))
    print(f"device[{index}].vram_free:", device.get("vram_free"))
PY
  else
    echo "UNAVAILABLE http://127.0.0.1:8188"
  fi
} >"$OUT_DIR/comfyui.txt" 2>&1

COMFY_ROOT=""
for candidate in   /workspace/runpod-slim/ComfyUI   /workspace/ComfyUI   /workspace/comfyui; do
  if [[ -d "$candidate" ]]; then
    COMFY_ROOT="$candidate"
    break
  fi
done

{
  if [[ -z "$COMFY_ROOT" ]]; then
    echo "ComfyUI root not found"
    exit 0
  fi

  echo "ComfyUI root: $COMFY_ROOT"
  echo
  echo "== Model files (names only) =="
  for subdir in checkpoints diffusion_models unet vae text_encoders clip clip_vision loras; do
    dir="$COMFY_ROOT/models/$subdir"
    echo "-- $subdir --"
    if [[ -d "$dir" ]]; then
      find "$dir" -maxdepth 2 -type f -printf '%f\n' | sort | head -n 200
    else
      echo "(missing)"
    fi
  done

  echo
  echo "== Custom node directories =="
  if [[ -d "$COMFY_ROOT/custom_nodes" ]]; then
    find "$COMFY_ROOT/custom_nodes" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
  else
    echo "(missing)"
  fi
} >"$OUT_DIR/comfyui-inventory.txt" 2>&1

echo "Faceless GPU preflight report written to $OUT_DIR"
