import json
import re
import unittest

from helpers import SKILL_DIR

from validate_episode import validate, validate_channel


def frontmatter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


class TestSkillContent(unittest.TestCase):
    def setUp(self):
        self.skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_model_tiers_section(self):
        self.assertIn("## Model per step", self.skill_md)
        sec = (SKILL_DIR / "references" / "build.md").read_text(encoding="utf-8").split("## Model per step", 1)[1].split("\n## ", 1)[0]
        for word in ("Opus", "Sonnet", "model: sonnet", "serial"):
            self.assertIn(word, sec)

    def test_frontmatter_name_and_description(self):
        fm = frontmatter(self.skill_md)
        self.assertEqual(fm.get("name"), "akra")
        self.assertTrue(1 <= len(fm.get("description", "")) <= 1024)

    def test_router_references_exist(self):
        refs = set(re.findall(r"references/[a-z0-9-]+\.md", self.skill_md))
        expected = {f"references/{n}.md" for n in (
            "channel-setup", "niche-scout", "idea-bank", "script",
            "shot-plan", "package-qa", "review", "rules")}
        self.assertTrue(expected <= refs, expected - refs)
        for ref in refs:
            self.assertTrue((SKILL_DIR / ref).is_file(), ref)

    def test_router_lists_every_mode(self):
        for mode in ("channel", "niche", "ideas", "script", "shots", "package", "review"):
            self.assertIn(f"`{mode}`", self.skill_md)

    def test_library_mode_routed(self):
        self.assertIn("references/library.md", self.skill_md)
        self.assertTrue((SKILL_DIR / "references" / "library.md").is_file())

    def test_library_reference_requires_user_approval(self):
        text = (SKILL_DIR / "references" / "library.md").read_text(encoding="utf-8")
        sections = re.split(r"^## ", text, flags=re.M)
        for key in ("vet", "promote"):
            body = [x for x in sections if x.lower().startswith(key)]
            self.assertTrue(body, f"no section for {key}")
            self.assertIn("approval", body[0].lower())

    def test_example_episode_is_valid(self):
        ep = json.loads((SKILL_DIR / "templates" / "episode.example.json").read_text())
        self.assertEqual(validate(ep), [])

    def test_example_channel_is_valid(self):
        ch = json.loads((SKILL_DIR / "templates" / "channel.example.json").read_text())
        ep = json.loads((SKILL_DIR / "templates" / "episode.example.json").read_text())
        self.assertEqual(validate_channel(ch), [])
        self.assertEqual(ep["channel"], ch["id"])

    def test_rules_md_mentions_every_limit(self):
        rules = (SKILL_DIR / "references" / "rules.md").read_text(encoding="utf-8")
        for token in ("75", "150", "10", "60", "diagram", "stock", "ai_disclosure",
                      "music_source", "channel", "originality_checklist"):
            self.assertIn(token, rules)

    def test_style_bible_template_sections(self):
        text = (SKILL_DIR / "templates" / "style-bible.md").read_text(encoding="utf-8")
        for heading in ("## 1. Visual identity", "## 2. Cast", "## 3. Expressions and emotion",
                        "## 4. Poses and gestures", "## 5. Environments and props", "## 7. Audio",
                        "## 8. Composition and on-screen text", "## Decision history"):
            self.assertIn(heading, text)
        self.assertNotIn("Flow", text)

    def test_no_google_flow_outside_legacy_rules(self):
        files = [SKILL_DIR / "SKILL.md"] + sorted((SKILL_DIR / "references").glob("*.md"))
        files += sorted((SKILL_DIR / "templates").glob("*.*"))
        files += sorted((SKILL_DIR / "templates" / "niches").rglob("*.*"))
        for path in files:
            if path.name == "rules.md":   # documents the legacy veo/flow_image handling
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?i)google flow|\bveo\b|flow_image|credit_estimate|credits_per_video",
                                path.name)

    def test_templates_exist(self):
        for name in ("style-bible.md", "review-log.csv"):
            self.assertTrue((SKILL_DIR / "templates" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()


class TestExampleQuality(unittest.TestCase):
    def test_example_shot_narration_matches_script(self):
        from validate_episode import _normalize
        ep = json.loads((SKILL_DIR / "templates" / "episode.example.json").read_text())
        joined = " ".join(s["narration"] for s in sorted(ep["shots"], key=lambda s: s["t_start"]))
        self.assertEqual(_normalize(joined), _normalize(ep["script"]))

    def test_upload_guide_does_not_force_made_for_kids_answer(self):
        text = (SKILL_DIR / "references" / "package-qa.md").read_text(encoding="utf-8")
        self.assertNotIn('pilih "No, it\'s not made for kids"', text)
        self.assertIn("made for kids", text.lower())
