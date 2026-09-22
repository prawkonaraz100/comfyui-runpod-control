from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "faceless_register_reference.py"
FIXTURE = ROOT / "faceless" / "projects" / "prawkonaraz-after-exam"

ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZK1sAAAAASUVORK5CYII="
)


class FacelessReferenceRegistrationTests(unittest.TestCase):
    def copy_fixture(self) -> Path:
        temp_root = Path(tempfile.mkdtemp(prefix="faceless-reference-"))
        self.addCleanup(shutil.rmtree, temp_root, True)
        target = temp_root / "project"
        shutil.copytree(FIXTURE, target)
        return target

    def source_png(self, project_dir: Path, name: str = "source.png") -> Path:
        path = project_dir.parent / name
        path.write_bytes(ONE_PIXEL_PNG)
        return path

    def run_script(
        self,
        project_dir: Path,
        source: Path,
        kind: str,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(project_dir),
                "--source",
                str(source),
                "--kind",
                kind,
                *extra,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_style_frame_can_be_registered_and_approved(self) -> None:
        project_dir = self.copy_fixture()
        source = self.source_png(project_dir)

        result = self.run_script(
            project_dir, source, "style-frame", "--approve"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        channel = json.loads((project_dir / "channel.json").read_text(encoding="utf-8"))
        project = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
        continuity = json.loads(
            (project_dir / "continuity.json").read_text(encoding="utf-8")
        )
        request = json.loads(
            (project_dir / "style-frame-request.json").read_text(encoding="utf-8")
        )

        expected = "assets/style/style-frame-v1.png"
        self.assertEqual(channel["visual_identity"]["style_frame"]["status"], "approved")
        self.assertEqual(channel["visual_identity"]["style_frame"]["path"], expected)
        self.assertTrue(project["approvals"]["style_frame"])
        self.assertEqual(continuity["style_lock"]["status"], "approved")
        self.assertEqual(continuity["style_lock"]["canonical_reference"], expected)
        self.assertEqual(request["status"], "approved")
        self.assertEqual(request["output_path"], expected)
        self.assertTrue((project_dir / expected).is_file())

    def test_character_sheet_never_approves_character_lock(self) -> None:
        project_dir = self.copy_fixture()
        source = self.source_png(project_dir)

        result = self.run_script(
            project_dir, source, "character-sheet", "--approve"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot approve", result.stderr)

    def test_character_requires_approved_style_before_character_approval(self) -> None:
        project_dir = self.copy_fixture()
        source = self.source_png(project_dir)

        result = self.run_script(project_dir, source, "character", "--approve")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("style frame is approved", result.stderr)

    def test_character_can_be_approved_after_style_approval(self) -> None:
        project_dir = self.copy_fixture()
        source = self.source_png(project_dir)

        style_result = self.run_script(
            project_dir, source, "style-frame", "--approve"
        )
        self.assertEqual(style_result.returncode, 0, style_result.stderr)

        character_result = self.run_script(
            project_dir, source, "character", "--approve"
        )
        self.assertEqual(character_result.returncode, 0, character_result.stderr)

        continuity = json.loads(
            (project_dir / "continuity.json").read_text(encoding="utf-8")
        )
        self.assertEqual(continuity["character_lock"]["status"], "approved")
        self.assertEqual(
            continuity["character_lock"]["canonical_reference"],
            "assets/characters/driver-01.png",
        )

    def test_existing_reference_is_not_replaced_without_flag(self) -> None:
        project_dir = self.copy_fixture()
        source = self.source_png(project_dir)

        first = self.run_script(project_dir, source, "style-frame")
        self.assertEqual(first.returncode, 0, first.stderr)

        second = self.run_script(project_dir, source, "style-frame")
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("--replace", second.stderr)


if __name__ == "__main__":
    unittest.main()
