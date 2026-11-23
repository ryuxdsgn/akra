import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import ROOT, SKILL_DIR

sys.path.insert(0, str(ROOT / "tools"))
from build_dist import CHATGPT_LIMIT, build  # noqa: E402


class TestBuildDist(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "dist"
        self.paths = build(SKILL_DIR, self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_paths_for_every_platform(self):
        self.assertEqual(set(self.paths), {"claude-ai", "chatgpt", "gemini"})

    def test_zip_has_skill_md_at_root_folder(self):
        with zipfile.ZipFile(self.paths["claude-ai"]) as z:
            names = z.namelist()
        self.assertIn("akra/SKILL.md", names)
        self.assertIn("akra/scripts/validate_episode.py", names)
        self.assertIn("akra/references/rules.md", names)
        self.assertFalse(any("__pycache__" in n for n in names))

    def test_chatgpt_instructions_within_limit(self):
        text = (self.paths["chatgpt"] / "instructions.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text), CHATGPT_LIMIT)
        self.assertEqual(CHATGPT_LIMIT, 8000)

    def test_chatgpt_instructions_onboard_new_users(self):
        text = (self.paths["chatgpt"] / "instructions.md").read_text(encoding="utf-8")
        self.assertIn("Codex", text)                 # full pipeline lives outside ChatGPT
        self.assertIn("API key", text)               # never ask for keys
        self.assertIn("channel.json", text)          # profile is pasted back each session

    def test_chatgpt_setup_sheet(self):
        sheet = (self.paths["chatgpt"] / "gpt-setup.md").read_text(encoding="utf-8")
        for needle in ("Name", "Description", "Conversation starters", "Code Interpreter", "instructions.md"):
            self.assertIn(needle, sheet)

    def test_chatgpt_instructions_no_frontmatter(self):
        text = (self.paths["chatgpt"] / "instructions.md").read_text(encoding="utf-8")
        self.assertFalse(text.startswith("---"))
        self.assertNotIn("name: akra", text)
        self.assertIn("Mode router", text)

    def test_knowledge_contains_all_references(self):
        knowledge = self.paths["chatgpt"] / "knowledge"
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for ref in (SKILL_DIR / "references").glob("*.md"):
            routed = f"references/{ref.name}" in skill
            self.assertEqual((knowledge / ref.name).is_file(), routed, ref.name)
        for tpl in (p for p in (SKILL_DIR / "templates").iterdir() if p.is_file()):   # niches/ kits stay repo-only
            self.assertTrue((knowledge / tpl.name).is_file(), tpl.name)
        self.assertTrue((knowledge / "validate_episode.py").is_file())

    def test_gemini_has_no_script(self):
        gem = self.paths["gemini"]
        self.assertFalse((gem / "knowledge" / "validate_episode.py").exists())
        self.assertTrue((gem / "knowledge" / "rules.md").is_file())
        self.assertIn("rules.md", (gem / "instructions.md").read_text(encoding="utf-8"))

    def test_policy_reference_in_chat_bundles(self):
        self.assertTrue((self.paths["chatgpt"] / "knowledge" / "youtube-policy.md").is_file())
        gem = self.paths["gemini"] / "knowledge"
        self.assertFalse((gem / "youtube-policy.md").exists())
        rules = (gem / "rules.md").read_text(encoding="utf-8")
        self.assertIn("# Validation checklist", rules)
        self.assertIn("YT-UP-1", rules)
        self.assertIn("youtube-policy.md", (self.paths["gemini"] / "instructions.md").read_text(encoding="utf-8"))

    def test_rebuild_replaces_old_output(self):
        stale = self.paths["chatgpt"] / "knowledge" / "stale.md"
        stale.write_text("old")
        build(SKILL_DIR, self.out)
        self.assertFalse(stale.exists())


class TestBuildLimit(unittest.TestCase):
    def test_over_limit_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "akra"
            shutil.copytree(SKILL_DIR, src)
            (src / "SKILL.md").write_text("---\nname: akra\ndescription: x\n---\n" + "a" * 9000)
            with self.assertRaises(ValueError) as ctx:
                build(src, Path(tmp) / "dist")
            self.assertIn("chatgpt instructions", str(ctx.exception))
            self.assertIn("8000", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


class TestBuildSafety(unittest.TestCase):
    def test_out_keeps_unrelated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "victim"
            out.mkdir()
            (out / "keep.txt").write_text("precious")
            build(SKILL_DIR, out)
            build(SKILL_DIR, out)
            self.assertEqual((out / "keep.txt").read_text(), "precious")

    def test_out_containing_src_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "skills" / "akra"
            shutil.copytree(SKILL_DIR, src)
            with self.assertRaises(ValueError):
                build(src, Path(tmp))
            with self.assertRaises(ValueError):
                build(src, src)
            self.assertTrue((src / "SKILL.md").is_file())

    def test_gemini_within_file_limit(self):
        from build_dist import GEMINI_MAX_FILES
        with tempfile.TemporaryDirectory() as tmp:
            paths = build(SKILL_DIR, Path(tmp) / "dist")
            files = [p for p in (paths["gemini"] / "knowledge").iterdir() if p.is_file()]
            self.assertLessEqual(len(files), GEMINI_MAX_FILES)
            self.assertEqual(GEMINI_MAX_FILES, 10)
            merged = (paths["gemini"] / "knowledge" / "templates.md").read_text(encoding="utf-8")
            self.assertIn("channel.example.json", merged)
            self.assertIn("review-log.csv", merged)
