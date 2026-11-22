import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT))
from library.freeze import freeze, library_root_for  # noqa: E402
import qa_render  # noqa: E402
import validate_episode  # noqa: E402


def make_repo(tmp):
    repo = Path(tmp)
    (repo / "library" / "previews").mkdir(parents=True)
    (repo / "library" / "a.json").write_text("{}")
    (repo / "library" / "catalog.json").write_text("{}")
    (repo / "library" / "previews" / "x.png").write_text("x")
    (repo / "skills" / "akra").mkdir(parents=True)
    proj = repo / "render" / "ep-001"
    proj.mkdir(parents=True)
    return repo, proj


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.proj = make_repo(self.tmp.name)

    def used(self, **kw):
        (self.proj / ".lib_used.json").write_text(json.dumps(dict({"style": "toon", "items": {}, "custom": []}, **kw)))

    def test_freeze_copies_library_once(self):
        self.used()
        self.assertTrue(freeze(self.proj))
        frozen = self.proj / "_lib_frozen" / "library"
        self.assertTrue((frozen / "a.json").is_file())
        self.assertFalse((frozen / "previews").exists())
        self.assertFalse((frozen / "catalog.json").exists())
        self.assertFalse(freeze(self.proj))

    def test_freeze_refresh_overwrites(self):
        self.used()
        freeze(self.proj)
        (self.repo / "library" / "a.json").write_text('{"v": 2}')
        self.assertFalse(freeze(self.proj))
        self.assertEqual((self.proj / "_lib_frozen" / "library" / "a.json").read_text(), "{}")
        self.assertTrue(freeze(self.proj, refresh=True))
        self.assertEqual((self.proj / "_lib_frozen" / "library" / "a.json").read_text(), '{"v": 2}')

    def test_freeze_ignores_projects_without_lib_used(self):
        self.assertFalse(freeze(self.proj))
        self.assertFalse((self.proj / "_lib_frozen").exists())

    def test_build_prefers_frozen_copy(self):
        self.assertEqual(library_root_for(self.proj), self.repo.resolve())
        self.used()
        freeze(self.proj)
        self.assertEqual(library_root_for(self.proj), self.proj / "_lib_frozen")

    def test_qa_fails_on_draft_item(self):
        self.used(items={"a": "draft", "b": "vetted"}, custom=["pose-x"])
        res = qa_render.library_checks(self.proj)
        fails = [r for r in res if not r[1]]
        self.assertEqual(len(fails), 1)
        self.assertIn("draft item(s) a used in final render", fails[0][0])
        notes = [r for r in res if r[1]]
        self.assertIn("custom look/pose pose-x - candidate for the library", notes[0][0])
        self.assertIn("vet the item", fails[0][0])
        self.assertIn("freeze", fails[0][0])
        self.assertIn("--refresh", fails[0][0])
        self.assertIn("REVIEW.md", fails[0][0])
        self.assertFalse((self.proj / "_lib_frozen").exists())   # a draft is never locked into the freeze

    def test_qa_freezes_only_clean_passing_episodes(self):
        self.used(items={"b": "vetted"})
        self.assertEqual(qa_render.library_checks(self.proj, do_freeze=False), [])
        self.assertFalse((self.proj / "_lib_frozen").exists())   # other QA checks failed: no freeze yet
        self.assertEqual(qa_render.library_checks(self.proj), [])
        self.assertTrue((self.proj / "_lib_frozen").is_dir())

    def test_qa_clean_without_lib_used(self):
        self.assertEqual(qa_render.library_checks(self.proj), [])

    def test_qa_without_lib_used_skips_repo_lookup(self):
        from unittest import mock
        with mock.patch.object(qa_render, "find_repo_root_for_qa", side_effect=RuntimeError("no repo")):
            self.assertEqual(qa_render.library_checks(self.proj), [])

    def test_validator_warns_on_direct_rig_import(self):
        from helpers import make_valid, make_channel
        ep = make_valid()
        ep["id"] = "ep-001"
        ep["channel"] = "flat-demo"
        epdir = self.repo / "channels" / "flat-demo" / "episodes"
        epdir.mkdir(parents=True)
        (epdir.parent / "channel.json").write_text(json.dumps(make_channel(id="flat-demo", render_layout="flat")))
        epj = epdir / "ep-001.json"
        epj.write_text(json.dumps(ep))
        (self.proj / "build.py").write_text("from character import Character\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = validate_episode._cmd_validate(epj)
        out = buf.getvalue()
        self.assertEqual(rc, 0, out)
        self.assertIn("render project calls the rig directly; use library.lib.Library", out)
        self.assertEqual(validate_episode._library_warnings(epj),
                         ["render project calls the rig directly; use library.lib.Library"])
        self.used()
        self.assertEqual(validate_episode._library_warnings(epj), [])

    def _hw_episode(self):
        from helpers import make_valid, make_channel
        ep = make_valid()
        ep["id"] = "ep-001"
        ep["channel"] = "flat-demo"
        epdir = self.repo / "channels" / "flat-demo" / "episodes"
        epdir.mkdir(parents=True)
        (epdir.parent / "channel.json").write_text(json.dumps(make_channel(id="flat-demo", render_layout="flat")))
        epj = epdir / "ep-001.json"
        epj.write_text(json.dumps(ep))
        return epj

    def test_validator_ignores_bare_shim_import(self):
        epj = self._hw_episode()
        (self.proj / "build.py").write_text(
            "import character  # noqa: F401  (shim: puts the repo or _lib_frozen on sys.path; keep BEFORE library)\n"
            "from library.lib import Library\n# character.py is a shim\nL = Library('.', 'flat-demo')\n"
            "svg = L.character('x', 'c1', 1, 2)\n")
        self.assertEqual(validate_episode._library_warnings(epj), [])
        (self.proj / "build.py").write_text("import character\nsvg = character.look(skin='#fff')\n")
        self.assertEqual(validate_episode._library_warnings(epj),
                         ["render project calls the rig directly; use library.lib.Library"])

    def test_validator_checks_channel_folder_layout_for_flat_layout(self):
        epj = self._hw_episode()
        shutil.rmtree(self.proj)
        nested = self.repo / "render" / "flat-demo" / "ep-001"
        nested.mkdir(parents=True)
        (nested / "build.py").write_text("import character\ncharacter.character('c1', 1, 2)\n")
        self.assertEqual(validate_episode._library_warnings(epj),
                         ["render project calls the rig directly; use library.lib.Library"])

    def test_frozen_items_survive_live_edits(self):
        import subprocess
        shutil.rmtree(self.repo / "library")
        shutil.copytree(ROOT / "library", self.repo / "library", ignore=shutil.ignore_patterns("previews", "__pycache__"))
        shutil.copy(ROOT / "render" / "_template" / "character.py", self.proj / "character.py")
        item = {"id": "t-char", "name": "frozen-name", "kind": "character", "tags": ["a"], "status": "vetted",
                "origin": "builtin", "created": "2026-01-01", "created_by": "t", "preview": "p.png",
                "examples": ["ep-001"], "style": "toon", "face": "toon", "base_look": {"skin": "#ffffff"},
                "variants": {"skin": {"type": "color"}}, "scale_hint": 1.0}
        (self.repo / "library" / "characters").mkdir(exist_ok=True)
        path = self.repo / "library" / "characters" / "t-char.json"
        path.write_text(json.dumps(item))
        (self.repo / "channels" / "flat-demo").mkdir(parents=True)
        (self.repo / "channels" / "flat-demo" / "library.json").write_text(json.dumps({"style": "toon", "visual_mode": "x", "items": []}))
        self.used()
        freeze(self.proj)
        path.write_text(json.dumps(dict(item, name="live-name")))
        code = ("import character\nfrom library.lib import Library\n"
                "print(Library('.', 'flat-demo').items['t-char']['name'])")
        r = subprocess.run([sys.executable, "-c", code], cwd=self.proj, capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "frozen-name")

    def test_live_import_rejected_when_frozen(self):
        from library.catalog import LibraryError
        from library.lib import Library
        self.used()
        (self.proj / "_lib_frozen" / "library").mkdir(parents=True)
        with self.assertRaises(LibraryError):
            Library(self.proj, "flat-demo")

    def test_shim_imports_frozen_library(self):
        import subprocess
        shutil.rmtree(self.repo / "library")
        shutil.copytree(ROOT / "library", self.repo / "library", ignore=shutil.ignore_patterns("previews", "__pycache__"))
        shutil.copy(ROOT / "render" / "_template" / "character.py", self.proj / "character.py")
        self.used()
        freeze(self.proj)
        r = subprocess.run([sys.executable, "-c", "import character, library; print(library.__file__)"],
                           cwd=self.proj, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("_lib_frozen", r.stdout)
        self.assertIn(str((self.proj / "_lib_frozen").resolve()), str(Path(r.stdout.strip()).resolve()))


if __name__ == "__main__":
    unittest.main()
