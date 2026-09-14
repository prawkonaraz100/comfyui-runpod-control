#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
source "$ROOT/config/wan22-animate.env"

COMFYUI_DIR="$(find_comfyui)" || die "ComfyUI not found"
REPORT="${REPORT_FILE:-/workspace/comfyui-runpod-control-report.txt}"
mkdir -p "$(dirname "$REPORT")"
: > "$REPORT"

pass() { printf 'PASS  %s\n' "$*" | tee -a "$REPORT"; }
fail() { printf 'FAIL  %s\n' "$*" | tee -a "$REPORT"; FAILURES=$((FAILURES+1)); }
info() { printf 'INFO  %s\n' "$*" | tee -a "$REPORT"; }
FAILURES=0

info "UTC: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
info "ComfyUI: $COMFYUI_DIR"

if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)"
  GPU_MEM="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)"
  info "GPU: $GPU_NAME, ${GPU_MEM} MiB VRAM"
  if (( GPU_MEM >= 45000 )); then
    pass "GPU has at least ~48 GB class VRAM"
  else
    fail "GPU VRAM below expected 48 GB class: ${GPU_MEM} MiB"
  fi
else
  fail "nvidia-smi unavailable"
fi

check_file() {
  local path="$1" label="$2"
  if [[ -s "$path" ]]; then
    pass "$label ($(du -h "$path" | awk '{print $1}'))"
  else
    fail "$label missing: $path"
  fi
}

[[ -d "$COMFYUI_DIR/custom_nodes/ComfyUI-KJNodes" ]] && pass "ComfyUI-KJNodes installed" || fail "ComfyUI-KJNodes missing"
[[ -d "$COMFYUI_DIR/custom_nodes/comfyui_controlnet_aux" ]] && pass "comfyui_controlnet_aux installed" || fail "comfyui_controlnet_aux missing"
[[ -d "$COMFYUI_DIR/custom_nodes/ComfyUI-Manager" ]] && pass "ComfyUI-Manager installed" || fail "ComfyUI-Manager missing"

check_file "$COMFYUI_DIR/models/diffusion_models/$WAN_DIFFUSION_NAME" "Wan2.2 Animate FP8 diffusion model"
check_file "$COMFYUI_DIR/models/loras/$WAN_LORA_NAME" "LightX2V LoRA"
check_file "$COMFYUI_DIR/models/text_encoders/$WAN_TEXT_ENCODER_NAME" "UMT5 text encoder"
check_file "$COMFYUI_DIR/models/clip_vision/$WAN_CLIP_VISION_NAME" "CLIP Vision H"
check_file "$COMFYUI_DIR/models/vae/$WAN_VAE_NAME" "Wan VAE"
check_file "$COMFYUI_DIR/user/default/workflows/$WAN_WORKFLOW_NAME" "Official Wan2.2 Animate workflow"

if curl -fsS --max-time 5 http://127.0.0.1:8188/system_stats >/tmp/comfyui-system-stats.json 2>/dev/null; then
  pass "ComfyUI API healthy on 127.0.0.1:8188"
else
  info "ComfyUI API is not currently responding on 8188 (models/nodes can still be installed while it is stopped)"
fi

if [[ "$FAILURES" -gt 0 ]]; then
  info "Verification failures: $FAILURES"
  exit 1
fi
pass "All required static checks passed"
