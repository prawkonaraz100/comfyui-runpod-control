#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/prawkonaraz100/comfyui-runpod-control"
RUNNER_DIR="${RUNNER_DIR:-/workspace/actions-runner}"
TOKEN="${1:-${RUNNER_REGISTRATION_TOKEN:-}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$TOKEN" ]]; then
  echo "Usage: bash scripts/bootstrap-runner.sh <GITHUB_RUNNER_REGISTRATION_TOKEN>"
  echo "Generate the short-lived token at:"
  echo "  GitHub repo -> Settings -> Actions -> Runners -> New self-hosted runner -> Linux x64"
  exit 2
fi

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

if [[ ! -x ./config.sh ]]; then
  echo "Discovering latest GitHub Actions runner release..."
  VERSION="$(python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('https://api.github.com/repos/actions/runner/releases/latest') as r:
    tag=json.load(r)['tag_name']
print(tag.lstrip('v'))
PY
)"
  ARCHIVE="actions-runner-linux-x64-${VERSION}.tar.gz"
  curl -fL --retry 5 -o "$ARCHIVE"     "https://github.com/actions/runner/releases/download/v${VERSION}/${ARCHIVE}"
  tar xzf "$ARCHIVE"
fi

if [[ -f .runner ]]; then
  echo "Runner is already configured in $RUNNER_DIR"
else
  export RUNNER_ALLOW_RUNASROOT=1
  ./config.sh --unattended --replace     --url "$REPO_URL"     --token "$TOKEN"     --name "runpod-a40-$(hostname)"     --labels "runpod,a40,comfyui"     --work "_work"
fi

# Make the runner return automatically after a Pod stop/start cycle.
bash "$SCRIPT_DIR/install-runner-autostart.sh"

exec bash "$SCRIPT_DIR/start-runner.sh"
