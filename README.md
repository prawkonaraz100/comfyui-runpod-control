# ComfyUI RunPod Control

GitHub-based control plane for a RunPod-hosted ComfyUI installation.

This repository is intentionally **public** and contains **no credentials**.

## Target

- RunPod 48 GB-class GPU (currently RTX 6000 Ada 48 GB)
- Current official RunPod ComfyUI template
- ComfyUI on port 8188
- Wan2.2 Animate / **MIX** character replacement
- Static-camera source video as the initial use case

## What this repository controls

Two GitHub Actions workflows are provided:

### GPU control

Runs on the **self-hosted GitHub Actions runner inside the RunPod Pod**.

Allowed commands:

- `status`
- `verify`
- `provision`
- `restart_comfyui`

Commands can be started manually in the GitHub Actions UI or by changing `control/command.json`.

### RunPod power

Runs on a normal GitHub-hosted runner and talks to the official RunPod REST API.

Allowed commands:

- `status`
- `start`
- `stop`
- `restart`

Commands can be started manually or by changing `control/power.json`.

This requires these GitHub Actions repository secrets:

- `RUNPOD_API_KEY`
- `RUNPOD_POD_ID`

Do not commit their values.

---

## One-time setup on the existing RunPod Pod

Open the RunPod Jupyter/terminal and run:

```bash
cd /workspace
git clone https://github.com/prawkonaraz100/comfyui-runpod-control.git
cd comfyui-runpod-control
```

Then open:

**GitHub repository → Settings → Actions → Runners → New self-hosted runner → Linux → x64**

Copy only the short-lived **registration token** shown by GitHub and run:

```bash
cd /workspace/comfyui-runpod-control
bash scripts/bootstrap-runner.sh YOUR_SHORT_LIVED_REGISTRATION_TOKEN
```

The bootstrapper:

1. installs the current GitHub Actions runner under `/workspace/actions-runner`,
2. registers it only for this repository,
3. applies labels `runpod,comfyui,gpu48`,
4. starts it,
5. installs a tiny ComfyUI custom-node hook that automatically starts the runner whenever ComfyUI starts after a Pod stop/start cycle.

The registration token is not written to this repository.

---

## Wan2.2 Animate provisioning

After the self-hosted runner appears as **Idle** on GitHub, use:

**Actions → GPU control → Run workflow → provision**

or edit `control/command.json` to:

```json
{
  "action": "provision",
  "nonce": 1
}
```

The provisioner installs/updates:

- ComfyUI-Manager
- ComfyUI-KJNodes
- comfyui_controlnet_aux

and downloads the official Wan2.2 Animate workflow plus the FP8 model set documented by ComfyUI:

- `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors`
- `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors`
- `umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `clip_vision_h.safetensors`
- `wan_2.1_vae.safetensors`
- `video_wan2_2_14B_animate.json`

Sources are declared in `config/wan22-animate.env`.

The current official RunPod ComfyUI layout at
`/workspace/runpod-slim/ComfyUI` is detected automatically.

After provisioning, run `restart_comfyui`.

---

## Control from GitHub commits

The self-hosted workflow intentionally listens only to changes in:

```text
control/command.json
```

Example:

```json
{
  "action": "verify",
  "nonce": 2
}
```

Changing `nonce` forces a new push event.

RunPod power control uses:

```text
control/power.json
```

Example:

```json
{
  "action": "stop",
  "nonce": 3
}
```

This design allows an authorized GitHub writer to operate the Pod without exposing a general remote shell.

---

## Security model

- No workflow runs on `pull_request` or `pull_request_target`.
- Forks and outside pull requests never execute on the self-hosted runner.
- The self-hosted workflow executes only a fixed allowlist in `scripts/control.sh`.
- No arbitrary command text from JSON is passed to a shell.
- The runner is dedicated to this repository.
- RunPod API credentials belong only in GitHub Actions Secrets.
- Never commit Jupyter tokens, SSH keys, RunPod API keys, runner registration tokens, or Hugging Face credentials.
- Treat any Jupyter URL containing `?token=...` as a credential.

See `SECURITY.md`.

## Notes

The official RunPod ComfyUI template currently uses:

```text
/workspace/runpod-slim/ComfyUI
```

and exposes ComfyUI on port `8188`.

The workflow is configured for Wan2.2 Animate **MIX**, where the person in the source video is replaced by the character from the reference image while retaining the source performance and scene.
