import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import export_public  # noqa: E402


def _write(base, rel, text="x\n"):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.dest = Path(self.tmp.name) / "out"
        r = self.repo
        for f in ("__init__.py", "catalog.py", "schema.py"):
            _write(r, f"library/{f}", (ROOT / "library" / f).read_text())
        base = {"id": "pub_char", "kind": "character", "name": "Pub", "tags": ["t"], "style": "hw", "status": "draft",
                "origin": "builtin", "created": "2026-01-01", "created_by": "tester",
                "preview": "previews/characters/pub_char.png", "examples": [], "base_look": {"skin": "#FFFFFF"},
                "variants": {"skin": {"type": "color"}}, "face": "hw", "scale_hint": 1.0, "public": True}
        priv = dict(base, id="secret_char", preview="previews/characters/secret_char.png")
        priv.pop("public")
        _write(r, "library/characters/pub_char.json", json.dumps(base))
        _write(r, "library/characters/secret_char.json", json.dumps(priv))
        _write(r, "library/previews/characters/secret_char.png", "png")
        _write(r, "library/art/drawing.py", "x\n")
        _write(r, "skills/akra/references/addon-notes.md", "add-on\n")
        _write(r, "skills/akra/references/library.md", "engine\n")
        _write(r, "skills/akra/scripts/addon_tool.py", "x\n")
        _write(r, "tests/test_addon.py", "x\n")
        _write(r, "README.md", "hello\n")
        _write(r, "docs/setup.md", "setup\n")
        _write(r, "docs/notes/plan.md", "private\n")             # docs outside the allowlist
        _write(r, "scratch/idea.md", "private\n")                # top-level folder outside the allowlist
        _write(r, ".public-deny.txt", "SecretWord\n")
        _write(r, ".public-export-exclude.txt", "# local\nlibrary/art\nskills/akra/references/addon-*.md\n"
               "skills/akra/scripts/addon_*.py\ntests/test_addon.py\n")
        _write(r, ".env", "KEY=1\n")
        _write(r, ".env.example", "KEY=\n")
        _write(r, ".youtube-a-token.json", "{}")
        subprocess.run(["git", "init", "-q"], cwd=r, check=True)
        self.commit()

    def commit(self):
        subprocess.run(["git", "add", "-A", "-f"], cwd=self.repo, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-q",
                        "--allow-empty", "-m", "x"], cwd=self.repo, check=True)

    def run_export(self, *extra, deny=True, exclude=True, tests=False):
        args = [str(self.dest), "--repo", str(self.repo)]
        args += ["--deny", str(self.repo / ".public-deny.txt")] if deny else []
        args += ["--exclude", str(self.repo / ".public-export-exclude.txt")] if exclude else []
        args += [] if tests else ["--no-tests"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return export_public.main([*args, *extra])

    def test_private_and_non_public_excluded(self):
        self.assertEqual(self.run_export(), 0)
        d = self.dest
        self.assertTrue((d / "README.md").is_file())
        self.assertTrue((d / "docs/setup.md").is_file())
        self.assertFalse((d / "library/characters/secret_char.json").exists())
        self.assertFalse((d / "library/previews/characters/secret_char.png").exists())
        self.assertTrue((d / "library/characters/pub_char.json").is_file())

    def test_only_allowlisted_paths_ship(self):
        self.assertEqual(self.run_export(), 0)
        self.assertFalse((self.dest / "docs/notes").exists())
        self.assertFalse((self.dest / "scratch").exists())
        self.assertTrue(all(export_public.is_public_path(str(p.relative_to(self.dest)))
                            for p in self.dest.rglob("*") if p.is_file()))

    def test_exclude_file_patterns_drop_files_inside_allowed_dirs(self):
        self.assertEqual(self.run_export(), 0)
        d = self.dest
        for rel in ("library/art", "skills/akra/references/addon-notes.md", "skills/akra/scripts/addon_tool.py",
                    "tests/test_addon.py", ".public-export-exclude.txt"):
            self.assertFalse((d / rel).exists(), rel)
        self.assertTrue((d / "skills/akra/references/library.md").is_file())
        for f in ("__init__.py", "catalog.py", "schema.py"):
            self.assertTrue((d / "library" / f).is_file(), f)

    def test_missing_exclude_file_fails_unless_allowed(self):
        (self.repo / ".public-export-exclude.txt").unlink()
        self.commit()
        self.assertEqual(self.run_export(), 2)
        self.assertFalse(self.dest.exists())
        self.assertEqual(self.run_export(exclude=False), 2)
        self.assertEqual(self.run_export("--allow-no-exclude", exclude=False), 0)
        self.assertTrue((self.dest / "tests/test_addon.py").is_file())     # nothing excluded inside allowed dirs

    def test_catalog_rebuilt_from_public_items(self):
        self.assertEqual(self.run_export(), 0)
        cat = json.loads((self.dest / "library/catalog.json").read_text())
        self.assertEqual([i["id"] for i in cat["items"]], ["pub_char"])

    def test_secrets_and_deny_file_never_copied(self):
        self.run_export()
        for rel in (".public-deny.txt", ".env", ".youtube-a-token.json"):
            self.assertFalse((self.dest / rel).exists(), rel)
        self.assertTrue((self.dest / ".env.example").is_file())

    def test_deny_hit_fails(self):
        _write(self.repo, "skills/akra/notes.md", "contains secretword here\n")
        self.commit()
        self.assertEqual(self.run_export(), 1)

    def test_binary_hit_fails(self):
        (self.repo / "library" / "img.png").write_bytes(b"\x89PNG\0\0SECRETWORD\0")
        self.commit()
        self.assertEqual(self.run_export(), 1)

    def test_missing_deny_file_fails_unless_allowed(self):
        (self.repo / ".public-deny.txt").unlink()
        self.commit()
        self.assertEqual(self.run_export(), 2)
        self.assertFalse(self.dest.exists())
        self.assertEqual(self.run_export(deny=False), 2)
        self.assertEqual(self.run_export("--allow-no-deny", deny=False), 0)
        self.assertTrue((self.dest / "README.md").is_file())

    def test_exports_head_not_working_tree(self):
        _write(self.repo, "README.md", "uncommitted edit\n")
        _write(self.repo, "draft.md", "untracked\n")
        self.assertEqual(self.run_export(), 2)              # dirty tracked file: refused
        self.assertEqual(self.run_export("--allow-dirty"), 0)
        self.assertEqual((self.dest / "README.md").read_text(), "hello\n")
        self.assertFalse((self.dest / "draft.md").exists())

    def test_symlinks_recreated_and_scanned(self):
        os.symlink("library.md", self.repo / "skills/akra/references/LINK.md")
        self.commit()
        self.assertEqual(self.run_export(), 0)
        link = self.dest / "skills/akra/references/LINK.md"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "library.md")
        os.symlink("/etc/hosts", self.repo / "skills/akra/OUT.md")
        self.commit()
        import shutil
        shutil.rmtree(self.dest)
        self.assertEqual(self.run_export(), 1)              # link out of the tree is a scan hit

    def test_tests_run_outside_dest_and_leave_no_bytecode(self):
        _write(self.repo, "tests/test_smoke.py", "import unittest\nimport library.schema\n\n\n"
               "class T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(library.schema)\n")
        self.commit()
        self.assertEqual(self.run_export(tests=True), 0)
        self.assertEqual(list(self.dest.rglob("__pycache__")), [])
        self.assertEqual(list(self.dest.rglob("*.pyc")), [])

    def test_nonempty_dest_refused(self):
        _write(self.dest, "a.txt")
        self.assertEqual(self.run_export(), 2)


if __name__ == "__main__":
    unittest.main()
