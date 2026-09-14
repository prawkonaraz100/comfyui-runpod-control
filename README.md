# ComfyUI RunPod Control

Secure GitHub-based control plane for a RunPod-hosted ComfyUI installation.

This repository is intentionally **public** and contains **no credentials**.

## Security model

- No workflows run on `pull_request`.
- GPU jobs are manual (`workflow_dispatch`) or owner-controlled pushes only.
- The RunPod self-hosted runner must be dedicated to this repository.
- Never place RunPod API keys, Hugging Face tokens, Jupyter tokens, SSH keys, or other credentials in the repository.
- Use GitHub Actions Secrets for credentials.

## Target

- RunPod A40 48 GB
- ComfyUI on port 8188
- Wan2.2 Animate / MIX character replacement workflow
- Static-camera source video as the initial use case

The bootstrap scripts and workflows are added in subsequent commits.
