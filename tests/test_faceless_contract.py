from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "faceless_validate.py"
FIXTURE = ROOT / "faceless" / "projects" / "demo"


class FacelessContractTests(unittest.TestCase):
    def run_validator(self, project_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(project_dir)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def copy_fixture(self) -> Path:
        temp_root = Path(tempfile.mkdtemp(prefix="faceless-contract-"))
        self.addCleanup(shutil.rmtree, temp_root, True)
        target = temp_root / "demo"
        shutil.copytree(FIXTURE, target)
        return target

    def test_demo_project_is_valid(self) -> None:
        result = self.run_validator(FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_project_cannot_approve_style_before_channel_style_frame(self) -> None:
        project_dir = self.copy_fixture()

        channel_path = project_dir / "channel.json"
        channel = json.loads(channel_path.read_text(encoding="utf-8"))
        channel["visual_identity"]["style_frame"] = {"status": "pending", "path": None}
        channel_path.write_text(json.dumps(channel, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("style frame", result.stderr)

    def test_scene_order_must_be_contiguous(self) -> None:
        project_dir = self.copy_fixture()

        scenes_path = project_dir / "scenes.json"
        scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
        scenes["scenes"][1]["order"] = 3
        scenes_path.write_text(json.dumps(scenes, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".order must equal 2", result.stderr)


if __name__ == "__main__":
    unittest.main()
