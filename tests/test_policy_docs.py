"""Workflow docs and templates point to the YouTube policy gate and the style-bible gate."""
import json
import unittest

from helpers import SKILL_DIR


class TestDocsPointToGate(unittest.TestCase):
    def test_each_step_reference_points_to_policy(self):
        for name in ("channel-setup.md", "idea-bank.md", "script.md", "shot-plan.md", "build.md",
                     "package-qa.md", "review.md", "niche-scout.md", "rules.md"):
            text = (SKILL_DIR / "references" / name).read_text(encoding="utf-8")
            self.assertIn("youtube-policy.md", text, name)

    def test_skill_md_points_once(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(skill.count("references/youtube-policy.md"), 1)

    def test_channel_setup_style_gate(self):
        text = (SKILL_DIR / "references" / "channel-setup.md").read_text(encoding="utf-8")
        self.assertIn("style_approved_on", text)
        self.assertRegex(text, r"2.3 sample style frames")

    def test_templates_carry_new_fields(self):
        ep = json.loads((SKILL_DIR / "templates" / "episode.example.json").read_text())
        for key in ("made_for_kids", "synthetic_content", "variation", "sources", "policy_check"):
            self.assertIn(key, ep)
        ch = json.loads((SKILL_DIR / "templates" / "channel.example.json").read_text())
        for key in ("style_approved_on", "sensitive_topic", "made_for_kids"):
            self.assertIn(key, ch)
        bible = (SKILL_DIR / "templates" / "style-bible.md").read_text(encoding="utf-8")
        self.assertIn("## Approval", bible)
        self.assertIn("## Sensitive topic", bible)


if __name__ == "__main__":
    unittest.main()
