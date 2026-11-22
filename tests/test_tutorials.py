"""Beginner tutorials exist, and every relative link in them points to a real repo file."""
import re
import unittest

from helpers import ROOT

TUTORIALS = ROOT / "docs" / "tutorials"
NAMES = ("README", "chatgpt", "gemini", "claude-ai", "local-setup", "claude-code", "antigravity", "codex")
LINK = re.compile(r"\]\(([^)\s]+)\)")


class TestTutorials(unittest.TestCase):
    def test_files_exist(self):
        for name in NAMES:
            self.assertTrue((TUTORIALS / f"{name}.md").is_file(), name)

    def test_chooser_links_every_tutorial(self):
        text = (TUTORIALS / "README.md").read_text(encoding="utf-8")
        for name in NAMES[1:]:
            self.assertIn(f"{name}.md", text, name)

    def test_readme_links_tutorials(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/tutorials/README.md", text)

    def test_relative_links_resolve(self):
        for path in [ROOT / "README.md"] + [TUTORIALS / f"{n}.md" for n in NAMES]:
            for target in LINK.findall(path.read_text(encoding="utf-8")):
                if re.match(r"[a-z]+:", target) or target.startswith("#"):
                    continue
                dest = (path.parent / target.split("#")[0]).resolve()
                self.assertTrue(dest.exists(), f"{path.name}: broken link {target}")


if __name__ == "__main__":
    unittest.main()
