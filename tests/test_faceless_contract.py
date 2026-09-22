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
PROPOSAL_FIXTURE = ROOT / "faceless" / "projects" / "demo"
STYLE_FRAME_FIXTURE = ROOT / "faceless" / "projects" / "style-frame-demo"


class FacelessContractTests(unittest.TestCase):
    def run_validator(self, project_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(project_dir)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def copy_fixture(self, source: Path = PROPOSAL_FIXTURE) -> Path:
        temp_root = Path(tempfile.mkdtemp(prefix="faceless-contract-"))
        self.addCleanup(shutil.rmtree, temp_root, True)
        target = temp_root / source.name
        shutil.copytree(source, target)
        return target

    def test_proposal_project_is_valid(self) -> None:
        result = self.run_validator(PROPOSAL_FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stage=proposal", result.stdout)

    def test_style_frame_stage_is_valid_without_scenes_or_continuity(self) -> None:
        result = self.run_validator(STYLE_FRAME_FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stage=style_frame", result.stdout)
        self.assertIn("scenes=0", result.stdout)

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

    def test_proposal_stage_requires_at_least_one_scene(self) -> None:
        project_dir = self.copy_fixture()
        scenes_path = project_dir / "scenes.json"
        scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
        scenes["scenes"] = []
        scenes_path.write_text(json.dumps(scenes, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("from proposal stage onward", result.stderr)

    def test_style_frame_request_must_match_channel_aspect_ratio(self) -> None:
        project_dir = self.copy_fixture(STYLE_FRAME_FIXTURE)
        request_path = project_dir / "style-frame-request.json"
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["aspect_ratio"] = "16:9"
        request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("aspect_ratio", result.stderr)

    def test_proposal_stage_requires_continuity_manifest(self) -> None:
        project_dir = self.copy_fixture()
        (project_dir / "continuity.json").unlink()

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("continuity.json", result.stderr)

    def test_approved_style_lock_must_match_channel_style_frame(self) -> None:
        project_dir = self.copy_fixture()
        continuity_path = project_dir / "continuity.json"
        continuity = json.loads(continuity_path.read_text(encoding="utf-8"))
        continuity["style_lock"]["canonical_reference"] = "assets/style/other-style.png"
        continuity_path.write_text(
            json.dumps(continuity, indent=2) + "\n", encoding="utf-8"
        )

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must match channel.visual_identity.style_frame.path", result.stderr)

    def test_scene_character_reference_must_match_canonical_lock(self) -> None:
        project_dir = self.copy_fixture()
        scenes_path = project_dir / "scenes.json"
        scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
        scenes["scenes"][0]["references"]["character"] = "assets/characters/other.png"
        scenes_path.write_text(json.dumps(scenes, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical character reference", result.stderr)

    def test_scene_requires_explicit_lock_lists(self) -> None:
        project_dir = self.copy_fixture()
        scenes_path = project_dir / "scenes.json"
        scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
        scenes["scenes"][0].pop("forbidden_changes")
        scenes_path.write_text(json.dumps(scenes, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator(project_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden_changes", result.stderr)


if __name__ == "__main__":
    unittest.main()
