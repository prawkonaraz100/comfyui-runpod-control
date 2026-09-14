#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
source "$ROOT/config/wan22-animate.env"

COMFYUI_DIR="$(find_comfyui)" || die "Could not locate ComfyUI. Set COMFYUI_DIR explicitly."
PYTHON="$(find_python "$COMFYUI_DIR")" || die "Could not locate Python used by ComfyUI."

log "ComfyUI: $COMFYUI_DIR"
log "Python: $PYTHON"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
fi

FREE_KB="$(df -Pk "$COMFYUI_DIR" | awk 'NR==2 {print $4}')"
FREE_GB=$((FREE_KB / 1024 / 1024))
MIN_FREE_GB="${MIN_FREE_GB:-35}"
log "Free storage on ComfyUI filesystem: ${FREE_GB} GiB"
if (( FREE_GB < MIN_FREE_GB )); then
  die "At least ${MIN_FREE_GB} GiB free is required before the first Wan2.2 Animate download. Increase RunPod storage/volume and retry."
fi

mkdir -p   "$COMFYUI_DIR/custom_nodes"   "$COMFYUI_DIR/models/diffusion_models"   "$COMFYUI_DIR/models/loras"   "$COMFYUI_DIR/models/text_encoders"   "$COMFYUI_DIR/models/clip_vision"   "$COMFYUI_DIR/models/vae"   "$COMFYUI_DIR/user/default/workflows"

clone_or_update "$MANAGER_REPO" "$COMFYUI_DIR/custom_nodes/ComfyUI-Manager"
clone_or_update "$KJNODES_REPO" "$COMFYUI_DIR/custom_nodes/ComfyUI-KJNodes"
clone_or_update "$CONTROLNET_AUX_REPO" "$COMFYUI_DIR/custom_nodes/comfyui_controlnet_aux"

install_requirements "$PYTHON" "$COMFYUI_DIR/custom_nodes/ComfyUI-Manager"
install_requirements "$PYTHON" "$COMFYUI_DIR/custom_nodes/ComfyUI-KJNodes"
install_requirements "$PYTHON" "$COMFYUI_DIR/custom_nodes/comfyui_controlnet_aux"

download_file "$WAN_DIFFUSION_URL" "$COMFYUI_DIR/models/diffusion_models/$WAN_DIFFUSION_NAME"
download_file "$WAN_LORA_URL" "$COMFYUI_DIR/models/loras/$WAN_LORA_NAME"
download_file "$WAN_TEXT_ENCODER_URL" "$COMFYUI_DIR/models/text_encoders/$WAN_TEXT_ENCODER_NAME"
download_file "$WAN_CLIP_VISION_URL" "$COMFYUI_DIR/models/clip_vision/$WAN_CLIP_VISION_NAME"
download_file "$WAN_VAE_URL" "$COMFYUI_DIR/models/vae/$WAN_VAE_NAME"
download_file "$WAN_WORKFLOW_URL" "$COMFYUI_DIR/user/default/workflows/$WAN_WORKFLOW_NAME"

mkdir -p /workspace/workflows 2>/dev/null || true
if [[ -d /workspace/workflows ]]; then
  cp -f "$COMFYUI_DIR/user/default/workflows/$WAN_WORKFLOW_NAME" "/workspace/workflows/$WAN_WORKFLOW_NAME"
fi

log "Provisioning complete. Running verification."
bash "$ROOT/scripts/verify.sh"
