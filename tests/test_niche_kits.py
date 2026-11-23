"""Niche starter kits in skills/akra/templates/niches/: complete, valid and generic."""
import json
import re
import unittest

from tests.helpers import SKILL_DIR
from validate_episode import FORBIDDEN_WORDS, validate_channel

NICHES = SKILL_DIR / "templates" / "niches"
FILES = ("README.md", "channel.json", "style-bible.md", "ideas.md")
TEMPLATE_HEADINGS = [l for l in (SKILL_DIR / "templates" / "style-bible.md").read_text().splitlines()
                     if l.startswith("## ")]


def kits():
    return sorted(p for p in NICHES.iterdir() if p.is_dir())


class NicheKitTests(unittest.TestCase):
    def test_seven_kits_listed_in_index(self):
        index = (NICHES / "README.md").read_text()
        self.assertEqual(len(kits()), 7, [k.name for k in kits()])
        for kit in kits():
            self.assertIn(f"`{kit.name}/`", index, kit.name)

    def test_every_kit_has_its_files(self):
        for kit in kits():
            for name in FILES:
                self.assertTrue((kit / name).is_file(), f"{kit.name}/{name}")

    def test_channel_profiles_validate(self):
        for kit in kits():
            profile = json.loads((kit / "channel.json").read_text())
            self.assertEqual(validate_channel(profile), [], kit.name)
            if profile.get("sensitive_topic"):
                self.assertTrue(profile.get("disclaimer"), f"{kit.name}: sensitive topic needs a disclaimer")

    def test_style_bible_keeps_every_section(self):
        for kit in kits():
            text = (kit / "style-bible.md").read_text()
            for heading in TEMPLATE_HEADINGS:
                self.assertIn(heading.split(":")[0], text, f"{kit.name}: missing {heading}")

    def test_ideas_have_ten_short_hooks(self):
        for kit in kits():
            text = (kit / "ideas.md").read_text()
            ideas = re.findall(r"^## \[ \] \d{3} — ", text, re.M)
            self.assertEqual(len(ideas), 10, kit.name)
            for hook in re.findall(r"^- hook: (.+)$", text, re.M):
                self.assertLessEqual(len(hook.split()), 10, f"{kit.name}: {hook}")

    def test_health_kits_avoid_cure_claims(self):
        words = FORBIDDEN_WORDS["health"]["en"]
        for kit in kits():
            profile = json.loads((kit / "channel.json").read_text())
            if profile.get("sensitive_topic") != "health":
                continue
            text = (kit / "ideas.md").read_text().lower()
            for w in words:
                self.assertIsNone(re.search(rf"\b{w}\b", text), f"{kit.name}: '{w}' in ideas")


if __name__ == "__main__":
    unittest.main()
