#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/scripts/lib.sh"

MODE="${1:-render}"
WAN_ENGINE_DIR="${WAN_ENGINE_DIR:-/workspace/wan2.2}"
WAN_MODEL_DIR="${WAN_MODEL_DIR:-/workspace/models/Wan2.2-TI2V-5B}"
WAN_DEPS_DIR="${WAN_DEPS_DIR:-/workspace/wan22-deps}"
WAN_ENGINE_COMMIT="${WAN_ENGINE_COMMIT:-42bf4cfaa384bc21833865abc2f9e6c0e67233dc}"
HF_HOME="${HF_HOME:-/workspace/huggingface}"
export HF_HOME

COMFYUI_DIR="$(find_comfyui || true)"
if [[ -n "$COMFYUI_DIR" ]]; then
  PYTHON="$(find_python "$COMFYUI_DIR")"
else
  PYTHON="$(command -v python3 || command -v python)"
fi
[[ -x "$PYTHON" ]] || die "Python interpreter not found"

export PYTHONPATH="$WAN_DEPS_DIR${PYTHONPATH:+:$PYTHONPATH}"

prepare_engine() {
  log "Preparing pinned Wan2.2 engine at $WAN_ENGINE_COMMIT"
  if [[ ! -d "$WAN_ENGINE_DIR/.git" ]]; then
    rm -rf "$WAN_ENGINE_DIR"
    git clone --filter=blob:none --no-checkout https://github.com/Wan-Video/Wan2.2.git "$WAN_ENGINE_DIR"
  fi
  git -C "$WAN_ENGINE_DIR" fetch --depth 1 origin "$WAN_ENGINE_COMMIT"
  git -C "$WAN_ENGINE_DIR" checkout --detach --force "$WAN_ENGINE_COMMIT"
}

prepare_dependencies() {
  local marker="$WAN_DEPS_DIR/.ready-$WAN_ENGINE_COMMIT"
  if [[ -f "$marker" ]]; then
    log "Wan2.2 dependencies already prepared"
    return
  fi

  log "Preparing isolated Wan2.2 Python dependencies in $WAN_DEPS_DIR"
  rm -rf "$WAN_DEPS_DIR"
  mkdir -p "$WAN_DEPS_DIR"
  local req="/tmp/wan22-requirements.txt"
  grep -Ev '^(torch|torchvision|torchaudio|flash_attn)([<>=]|$)' "$WAN_ENGINE_DIR/requirements.txt" > "$req"

  "$PYTHON" -m pip install --disable-pip-version-check --target "$WAN_DEPS_DIR" -r "$req"
  "$PYTHON" -m pip install --disable-pip-version-check --target "$WAN_DEPS_DIR" --no-build-isolation flash_attn
  touch "$marker"
}

verify_gpu_runtime() {
  nvidia-smi >/dev/null 2>&1 || die "NVIDIA GPU is unavailable on this runner"
  "$PYTHON" - <<'PY'
import torch
print(f"torch={torch.__version__} cuda={torch.version.cuda} available={torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available to PyTorch")
print(torch.cuda.get_device_name(0))
props = torch.cuda.get_device_properties(0)
print(f"VRAM={props.total_memory / 1024**3:.1f} GiB")
PY
}

prepare_model() {
  mkdir -p "$WAN_MODEL_DIR" "$HF_HOME"
  log "Preparing Wan2.2 TI2V-5B model (public Hugging Face weights; resumable)"
  "$PYTHON" - <<'PY'
import os
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id="Wan-AI/Wan2.2-TI2V-5B",
    local_dir=os.environ["WAN_MODEL_DIR"],
)
print(path)
PY
}

render_video() {
  local input="$ROOT_DIR/assets/welcome-input.jpg"
  local output="$ROOT_DIR/artifacts/welcome-wan22.mp4"
  [[ -s "$input" ]] || die "Missing input image: $input"
  mkdir -p "$(dirname "$output")"
  rm -f "$output"

  local prompt
  prompt="Animate this exact friendly flat-vector office illustration as a short welcome shot. Preserve the same three people, their faces, hair, clothing and positions, the room layout, colors, wall poster, speech bubble and mug. Do not redraw, replace or alter any written words; keep all Polish text exactly as it appears in the input image. The three people make small natural welcoming gestures: gentle hand waves, tiny head movements, occasional blinks and subtle breathing. Add only a very slow cinematic push-in and slight depth parallax in the room. Keep the composition stable and professional. No new people, no new objects, no scene change, no camera shake, no morphing, no distorted hands, no extra fingers, no altered text."

  log "Starting Wan2.2 TI2V-5B image-to-video render"
  (
    cd "$WAN_ENGINE_DIR"
    "$PYTHON" generate.py \
      --task ti2v-5B \
      --size '1280*704' \
      --ckpt_dir "$WAN_MODEL_DIR" \
      --offload_model True \
      --convert_model_dtype \
      --t5_cpu \
      --image "$input" \
      --frame_num 81 \
      --sample_steps 30 \
      --base_seed 20260917 \
      --save_file "$output" \
      --prompt "$prompt"
  )

  [[ -s "$output" ]] || die "Render did not produce $output"
  log "Render complete: $output"
}

case "$MODE" in
  prepare)
    verify_gpu_runtime
    prepare_engine
    prepare_dependencies
    prepare_model
    ;;
  render)
    verify_gpu_runtime
    prepare_engine
    prepare_dependencies
    prepare_model
    render_video
    ;;
  *)
    die "Usage: $0 {prepare|render}"
    ;;
esac
