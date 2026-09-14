# Security

This repository is public, but the attached RunPod GPU is not public infrastructure.

## Rules

1. Never add `pull_request`, `pull_request_target`, `issue_comment`, or fork-driven execution to workflows targeting the self-hosted runner.
2. Never execute arbitrary shell text read from repository files. `scripts/control.sh` uses an explicit allowlist.
3. Keep `RUNPOD_API_KEY`, runner registration tokens, Hugging Face tokens, Jupyter tokens, SSH keys, and similar credentials in secret stores or pass them interactively.
4. The self-hosted runner must be dedicated to this repository.
5. Review any change that expands the trigger surface of `.github/workflows/gpu-control.yml`.
6. Do not expose ComfyUI directly without RunPod's authenticated/proxied access controls.
7. Treat URLs containing Jupyter tokens as credentials.

Public readers can inspect this repository, but they cannot push to `main` or dispatch commands unless granted write access.
