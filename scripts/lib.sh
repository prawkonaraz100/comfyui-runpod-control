#!/usr/bin/env bash
set -Eeuo pipefail

log() { printf '[%s] %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"; }
die() { log "ERROR: $*"; exit 1; }

find_comfyui() {
  local candidates=(
    "${COMFYUI_DIR:-}"
    "/workspace/ComfyUI"
    "/workspace/comfyui"
    "/ComfyUI"
    "/opt/ComfyUI"
  )
  local p
  for p in "${candidates[@]}"; do
    [[ -n "$p" && -f "$p/main.py" && -d "$p/models" ]] && { printf '%s\n' "$p"; return 0; }
  done
  return 1
}

find_python() {
  local comfy="$1"
  local candidates=(
    "$comfy/venv/bin/python"
    "/workspace/venv/bin/python"
    "/opt/venv/bin/python"
  )
  local p
  for p in "${candidates[@]}"; do
    [[ -x "$p" ]] && { printf '%s\n' "$p"; return 0; }
  done
  command -v python3 || command -v python || return 1
}

download_file() {
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -s "$dest" ]]; then
    log "Already present: $dest ($(du -h "$dest" | awk '{print $1}'))"
    return 0
  fi

  log "Downloading: $dest"
  if command -v aria2c >/dev/null 2>&1; then
    aria2c --console-log-level=warn --summary-interval=10 -x 8 -s 8 -c       --allow-overwrite=true -d "$(dirname "$dest")" -o "$(basename "$dest")" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget --progress=dot:giga -c -O "$dest" "$url"
  elif command -v curl >/dev/null 2>&1; then
    curl -fL --retry 5 --retry-delay 5 -C - -o "$dest" "$url"
  else
    die "Neither aria2c, wget nor curl is available"
  fi
  [[ -s "$dest" ]] || die "Download produced an empty file: $dest"
}

clone_or_update() {
  local url="$1" dest="$2"
  if [[ -d "$dest/.git" ]]; then
    log "Updating $(basename "$dest")"
    git -C "$dest" fetch --depth 1 origin
    git -C "$dest" reset --hard origin/HEAD || git -C "$dest" pull --ff-only
  else
    log "Cloning $url"
    rm -rf "$dest"
    git clone --depth 1 "$url" "$dest"
  fi
}

install_requirements() {
  local python="$1" dir="$2"
  if [[ -f "$dir/requirements.txt" ]]; then
    log "Installing Python requirements for $(basename "$dir")"
    "$python" -m pip install --disable-pip-version-check -r "$dir/requirements.txt"
  fi
}
