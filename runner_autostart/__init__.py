from __future__ import annotations

import os
import pathlib
import subprocess

RUNNER_DIR = pathlib.Path(os.environ.get("RUNNER_DIR", "/workspace/actions-runner"))
LOG_DIR = pathlib.Path("/workspace/logs")
LOG_FILE = LOG_DIR / "github-runner.log"


def _runner_is_configured() -> bool:
    return (RUNNER_DIR / ".runner").exists() and (RUNNER_DIR / "run.sh").exists()


def _runner_is_running() -> bool:
    try:
        result = subprocess.run(
            ["pgrep", "-f", "Runner.Listener"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _start_runner() -> None:
    if not _runner_is_configured() or _runner_is_running():
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["RUNNER_ALLOW_RUNASROOT"] = "1"

    with LOG_FILE.open("ab", buffering=0) as log:
        subprocess.Popen(
            ["bash", "run.sh"],
            cwd=str(RUNNER_DIR),
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )


try:
    _start_runner()
except Exception as exc:
    print(f"[RunPodGitHubRunnerAutoStart] runner start skipped: {exc}")


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
