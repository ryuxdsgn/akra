"""The library engine on its own: no rig, no library art, user-made items only (what the public tree ships)."""
import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from helpers import NO_RIG, ROOT

sys.path.insert(0, str(ROOT))
import library.lib as libmod  # noqa: E402
from library.catalog import build_catalog  # noqa: E402
from library.lib import Library, RigNotIncluded  # noqa: E402
from library.schema import validate_item  # noqa: E402

ENGINE = ("__init__.py", "catalog.py", "cli.py", "freeze.py", "lib.py", "preview.py", "schema.py")
COMMON = {"tags": ["mine"], "status": "draft", "origin": "generated", "token_cost": 0, "created": "2026-11-22",
          "created_by": "me", "examples": []}
CHAR = dict(COMMON, id="my_host", kind="character", name="My host", style="hw", face="hw",
            preview="previews/characters/my_host.png", base_look={"skin": "#F0C8A0"},
            variants={"skin": {"type": "color"}}, scale_hint=1.0)
ENV = dict(COMMON, id="my_room", kind="env", name="My room", style="hw", preview="previews/envs/my_room.png",
           module="my_room.py", function="build", variants=["default", "night"], backdrop="#202830",
           safe_area=[60, 820, 1020, 1170], palette=["#202830"])
ENV_PY = "def build(rnd, fl, variant='default'):\n    return '<rect id=\"far-' + variant + '\"/>', ''\n"


def no_rig():
    """Hide library.rig and its modules, as in a tree without library/rig/."""
    hidden = {k: None for k in list(sys.modules) if k == "library.rig" or k.startswith("library.rig.")}
    hidden.update({"library.rig": None, "library.rig.hw": None, "library.rig.toon": None,
                   "library.rig.costumes": None, "library.rig.mocap": None})
    return mock.patch.dict(sys.modules, hidden)


def engine_tree(tmp):
    """A repo holding only the engine, a user item set in channels/_library/ and a channel that selects them."""
    repo = Path(tmp)
    (repo / "skills" / "akra").mkdir(parents=True)
    (repo / "library").mkdir()
    for f in ENGINE:
        shutil.copy(ROOT / "library" / f, repo / "library" / f)
    local = repo / "channels" / "_library"
    (local / "characters").mkdir(parents=True)
    (local / "envs").mkdir()
    (local / "characters" / "my_host.json").write_text(json.dumps(CHAR))
    (local / "envs" / "my_room.json").write_text(json.dumps(ENV))
    (local / "envs" / "my_room.py").write_text(ENV_PY)
    (repo / "channels" / "mine").mkdir()
    (repo / "channels" / "mine" / "library.json").write_text(
        json.dumps({"style": "hw", "visual_mode": "diagram", "items": ["my_host", "my_room"]}))
    proj = repo / "render" / "mine" / "ep-001"
    proj.mkdir(parents=True)
    return repo, proj


class EngineWithoutRig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.proj = engine_tree(self.tmp.name)

    def test_user_items_validate(self):
        self.assertEqual(validate_item(CHAR), [])
        self.assertEqual(validate_item(ENV), [])

    def test_empty_catalog_builds(self):
        cat = build_catalog(self.repo)
        self.assertEqual(cat, {"items": []})
        self.assertEqual(json.loads((self.repo / "library" / "catalog.json").read_text()), {"items": []})

    def test_env_works_without_rig(self):
        with no_rig():
            lib = Library(self.proj, "mine")
            fn, backdrop = lib.env("my_room", "night")
            far, mid = fn(None, [])
        self.assertIn("far-night", far)
        self.assertEqual(backdrop, "#202830")
        rec = json.loads((self.proj / ".lib_used.json").read_text())
        self.assertEqual(rec["items"], {"my_room": "draft"})

    def test_character_without_rig_raises_clear_error(self):
        with no_rig():
            lib = Library(self.proj, "mine")
            for call in (lambda: lib.character("my_host", "c1", 540, 1500), lambda: lib.look("my_host"),
                         lambda: lib.pose("point"), lambda: lib.custom_look()):
                with self.assertRaises(RigNotIncluded) as c:
                    call()
                self.assertIn(NO_RIG, str(c.exception))
                self.assertIn("references/library.md", str(c.exception))

    def test_costume_without_rig_is_a_schema_error(self):
        with no_rig():
            errs = validate_item(dict(CHAR, costume="anything"))
        self.assertTrue(any("not included" in e for e in errs), errs)

    def test_own_rig_module_is_used(self):
        rig = types.SimpleNamespace(
            POSES={"point": {}},
            look=lambda **kw: dict(kw),
            character=lambda cid, x, y, s=1.0, look=None, facing="right": f'<g id="{cid}" data-skin="{look["skin"]}"/>')
        with mock.patch.object(libmod, "load_rig", return_value=rig):
            lib = Library(self.proj, "mine")
            svg = lib.character("my_host", "c1", 540, 1500, skin="#112233")
            self.assertEqual(lib.pose("point"), "point")
        self.assertEqual(svg, '<g id="c1" data-skin="#112233"/>')

    def test_preview_of_character_needs_rig(self):
        from library.preview import render_preview
        with no_rig(), self.assertRaises(RigNotIncluded):
            render_preview(CHAR, self.repo / "out.png", root=self.repo, base=self.repo / "channels" / "_library")


class ShimsWithoutRig(unittest.TestCase):
    """render/_template/character.py and mocap.py in a tree without library/rig/ (run in a fresh interpreter)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.proj = engine_tree(self.tmp.name)
        for f in ("character.py", "mocap.py"):
            shutil.copy(ROOT / "render" / "_template" / f, self.proj / f)

    def py(self, code=None, script=None):
        args = [sys.executable, "-B"] + (["-c", code] if code else [script])
        return subprocess.run(args, cwd=self.proj, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})

    def test_import_still_sets_up_the_library(self):
        r = self.py("import character, mocap\nfrom library.lib import Library\nprint(Library('.', 'mine').style)")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "hw")

    def test_helper_use_raises_clear_error(self):
        for code in ("import character\ncharacter.character('c1', 540, 1500)",
                     "from character import look", "import mocap\nmocap.load"):
            r = self.py(code)
            self.assertNotEqual(r.returncode, 0, code)
            self.assertIn("RigNotIncluded", r.stderr, code)
            self.assertIn(NO_RIG, r.stderr, code)

    def test_mocap_script_exits_with_message(self):
        r = self.py(script="mocap.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn(NO_RIG, r.stderr)


if __name__ == "__main__":
    unittest.main()
