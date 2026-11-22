import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from helpers import HAVE_RIG, ROOT

sys.path.insert(0, str(ROOT))
from library.catalog import LibraryError  # noqa: E402
from library.lib import Library, find_repo_root  # noqa: E402

needs_rig = unittest.skipUnless(HAVE_RIG, "character rig not included")
COMMON = {"name": "T", "tags": ["a"], "status": "draft", "origin": "builtin", "created": "2026-01-01",
          "created_by": "tester", "preview": "p.png", "examples": ["ep-001"]}
VARIANTS = {"skin": {"type": "color"}, "hat": {"enum": ["a", "b"]}, "h": {"min": 1, "max": 2}}


def char(cid, style):
    return dict(COMMON, id=cid, kind="character", style=style, face=style, base_look={"skin": "#ffffff"},
                variants=VARIANTS, scale_hint=1.0)


class LoaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        shutil.copytree(ROOT / "library", self.repo / "library")
        (self.repo / "skills" / "akra").mkdir(parents=True)
        for sub in ("characters", "envs"):
            (self.repo / "library" / sub).mkdir(exist_ok=True)
        self._write("characters", "t-hw", char("t-hw", "hw"))
        self._write("characters", "t-toon", char("t-toon", "toon"))
        env = dict(COMMON, id="t-env", kind="env", style="hw", module="t_env.py", function="build",
                   variants=["default", "night"], backdrop="#112233", safe_area=[0, 0, 1080, 1920], palette=["#112233"])
        self._write("envs", "t-env", env)
        (self.repo / "library" / "envs" / "t_env.py").write_text(
            "def build(rnd, fl, variant='default'):\n    return '<g>far-' + variant + '</g>', '<g>mid</g>'\n")
        self._cfg("demo-hw", "hw")
        self._cfg("demo-toon", "toon")
        self.proj = self.repo / "render" / "ep-001"
        self.proj.mkdir(parents=True)

    def _write(self, sub, name, item):
        (self.repo / "library" / sub / f"{name}.json").write_text(json.dumps(item))

    def _cfg(self, channel, style, items=()):
        d = self.repo / "channels" / channel
        d.mkdir(parents=True, exist_ok=True)
        (d / "library.json").write_text(json.dumps({"style": style, "visual_mode": "x", "items": list(items)}))

    def lib(self, channel="demo-hw"):
        return Library(self.proj, channel)

    def test_style_lock_rejects_other_style(self):
        with self.assertRaises(LibraryError) as c:
            self.lib().character("t-toon", "c1", 100, 500)
        self.assertIn("style", str(c.exception))

    def test_variant_out_of_range_rejected(self):
        with self.assertRaises(LibraryError):
            self.lib().look("t-hw", h=5)
        with self.assertRaises(LibraryError):
            self.lib().look("t-hw", skin="red")
        with self.assertRaises(LibraryError):
            self.lib().look("t-hw", nope=1)

    def test_enum_variant_rejected(self):
        with self.assertRaises(LibraryError):
            self.lib().look("t-hw", hat="z")

    @needs_rig
    def test_bool_and_nullable_color_variants(self):
        item = char("t-hw", "hw")
        item["variants"] = dict(VARIANTS, g={"type": "bool"}, tie={"type": "color", "nullable": True})
        self._write("characters", "t-hw", item)
        lib = self.lib()
        lib.look("t-hw", g=True)
        lib.look("t-hw", g=False)
        lib.look("t-hw", tie=None)
        lib.look("t-hw", tie="#112233")
        for kw in ({"g": 1}, {"g": 0}, {"g": None}, {"g": "true"}, {"skin": None}, {"tie": "red"}):
            with self.assertRaises(LibraryError, msg=str(kw)):
                lib.look("t-hw", **kw)

    @needs_rig
    def test_valid_variants_build(self):
        svg = self.lib().character("t-hw", "c1", 100, 500, skin="#aabbcc", h=1.5)
        self.assertIsInstance(svg, str)

    @needs_rig
    def test_pose_is_resolved_per_style(self):
        hw, toon = self.lib().rig.POSES["point"], self.lib("demo-toon").rig.POSES["point"]
        self.assertNotEqual(hw, toon)
        for style, got in (("hw", hw), ("toon", toon)):
            ref = {}
            for f in sorted((ROOT / "library" / "poses" / style).glob("*.json")):
                ref.update(json.loads(f.read_text()))
            want = dict(ref["point"])
            if "face" in want:
                want["face"] = tuple(want["face"])
            self.assertEqual(got, want)
        with self.assertRaises(LibraryError):
            self.lib().pose("no-such-pose")
        self.assertEqual(self.lib().pose("point"), "point")

    def test_unselected_item_rejected(self):
        self._cfg("demo-hw", "hw", ["t-env"])
        with self.assertRaises(LibraryError):
            self.lib().character("t-hw", "c1", 100, 500)
        self.lib().env("t-env")

    @needs_rig
    def test_usage_record_written(self):
        lib = self.lib()
        lib.character("t-hw", "c1", 100, 500)
        lib.custom_pose("zz-test", armB=1)
        rec = json.loads((self.proj / ".lib_used.json").read_text())
        self.assertEqual(rec["style"], "hw")
        self.assertEqual(rec["items"]["t-hw"], "draft")
        self.assertIn("zz-test", rec["custom"])
        self.assertIn("zz-test", lib.rig.POSES)
        lib.rig.POSES.pop("zz-test")

    @needs_rig
    def test_usage_record_pruned_per_process(self):
        import library.lib as libmod
        self._write("characters", "t-hw2", dict(char("t-hw2", "hw"), status="vetted"))
        self.lib().character("t-hw", "c1", 100, 500)        # build 1 uses a draft
        self.lib().character("t-hw2", "c2", 100, 500)       # same process: merges
        rec = json.loads((self.proj / ".lib_used.json").read_text())
        self.assertEqual(rec["items"], {"t-hw": "draft", "t-hw2": "vetted"})
        libmod._WRITTEN.clear()                              # simulate a new build process
        self.lib().character("t-hw2", "c2", 100, 500)
        rec = json.loads((self.proj / ".lib_used.json").read_text())
        self.assertEqual(rec["items"], {"t-hw2": "vetted"})

    @needs_rig
    def test_usage_record_keeps_other_scripts(self):
        import library.lib as libmod
        self._write("characters", "t-hw2", dict(char("t-hw2", "hw"), status="vetted"))
        with mock.patch.object(sys, "argv", ["build.py"]):
            self.lib().character("t-hw", "c1", 100, 500)    # build.py uses a draft
        libmod._WRITTEN.clear()                              # cover.py runs in its own process
        with mock.patch.object(sys, "argv", ["cover.py"]):
            self.lib().character("t-hw2", "c2", 100, 500)
        rec = json.loads((self.proj / ".lib_used.json").read_text())
        self.assertEqual(rec["items"], {"t-hw": "draft", "t-hw2": "vetted"})   # draft not hidden by cover.py
        self.assertEqual(set(rec["by_script"]), {"build.py", "cover.py"})

    def test_missing_config_for_unknown_channel(self):
        with self.assertRaises(LibraryError) as c:
            self.lib("other")
        self.assertIn("library.json", str(c.exception))

    def test_repo_root_found_from_nested_channel_project(self):
        nested = self.repo / "render" / "demo-toon" / "ep-009"
        nested.mkdir(parents=True)
        self.assertEqual(find_repo_root(nested), self.repo.resolve())

    def test_env_returns_bakeable_callable(self):
        fn, backdrop = self.lib().env("t-env", "night")
        far, mid = fn(None, 0)
        self.assertIsInstance(far, str)
        self.assertIsInstance(mid, str)
        self.assertIn("night", far)
        self.assertEqual(backdrop, "#112233")
        with self.assertRaises(LibraryError):
            self.lib().env("t-env", "dawn")


if __name__ == "__main__":
    unittest.main()
