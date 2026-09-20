from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "faceless-video-director" / "SKILL.md"
REFERENCE = (
    ROOT
    / ".agents"
    / "skills"
    / "faceless-video-director"
    / "references"
    / "script-writer-source.md"
)


class FacelessVideoDirectorSkillTests(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        self.assertTrue(SKILL.is_file())
        self.assertTrue(REFERENCE.is_file())

    def test_skill_has_required_frontmatter(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name:\s+faceless-video-director$")
        self.assertRegex(frontmatter, r"(?m)^description:\s+.+$")

    def test_skill_locks_canonical_references(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        required_phrases = [
            "canonical character reference",
            "canonical style reference",
            "Never use the previous generated scene as the only character reference",
            "Scene-level repair",
            "Continuity QA",
            "Do not introduce OpenAI API calls",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, text)

    def test_skill_preserves_script_writer_source(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("# Faceless Script Writer", text)
        self.assertIn("## Hook Engine", text)
        self.assertIn("## Structure Blueprints", text)
        self.assertIn("## Retention Rules", text)
        self.assertIn("## Output Format", text)
        self.assertIn("## Limitations", text)


if __name__ == "__main__":
    unittest.main()
