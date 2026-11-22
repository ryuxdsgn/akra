import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import HAVE_ART, HAVE_RIG, ROOT

sys.path.insert(0, str(ROOT))
from library.catalog import LibraryError, build_catalog, load_items  # noqa: E402
from library.schema import validate_item  # noqa: E402

COMMON = {
    "name": "Test", "tags": ["a"], "style": "hw", "status": "draft", "origin": "builtin",
    "created": "2026-01-01", "created_by": "tester", "preview": "previews/x.png", "examples": ["ep-001"],
}


def character(**kw):
    d = dict(COMMON, id="hw-test", kind="character", base_look={"skin": "#fff"},
             variants={"skin": {"type": "color"}, "hat": {"enum": ["a", "b"]}, "h": {"min": 1, "max": 2}},
             face="hw", scale_hint=1.0)
    d.update(kw)
    return d


def env(**kw):
    d = dict(COMMON, id="room", kind="env", module="room.py", function="build",
             variants=["default"], backdrop="#112233", safe_area=[0, 0, 1080, 1920], palette=["#112233"])
    d.update(kw)
    return d


def write(path, item):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(item))


class SchemaTests(unittest.TestCase):
    def test_valid_character_passes(self):
        self.assertEqual(validate_item(character()), [])

    def test_valid_env_and_pose_set_pass(self):
        self.assertEqual(validate_item(env()), [])
        ps = dict(COMMON, id="hw/acting", kind="pose", params_file="poses/hw/acting.json", needs=["chair"])
        self.assertEqual(validate_item(ps), [])

    def test_missing_field_reported(self):
        c = character()
        del c["tags"]
        errs = validate_item(c)
        self.assertTrue(any("tags" in e for e in errs), errs)

    def test_generated_item_needs_token_cost(self):
        errs = validate_item(character(origin="generated"))
        self.assertTrue(any("token_cost" in e for e in errs), errs)
        self.assertEqual(validate_item(character(origin="generated", token_cost=5)), [])

    def test_face_must_match_style(self):
        errs = validate_item(character(style="hw", face="toon"))
        self.assertTrue(any("face" in e for e in errs), errs)

    def test_env_safe_area_inside_frame(self):
        errs = validate_item(env(safe_area=[0, 0, 1200, 1920]))
        self.assertTrue(any("safe_area" in e for e in errs), errs)

    def test_costume_rules(self):
        if not HAVE_RIG:
            errs = validate_item(character(costume="period_costume"))
            self.assertTrue(any("not included" in e for e in errs), errs)
            return
        from library.rig.costumes import COSTUMES
        known = sorted(COSTUMES)[0]
        self.assertEqual(validate_item(character(costume=known)), [])
        self.assertTrue(any("costume" in e for e in validate_item(character(costume="nope"))))
        errs = validate_item(character(costume=known, style="toon", face="toon"))
        self.assertTrue(any("costume" in e for e in errs), errs)

    def test_bad_kind_status_origin_rejected(self):
        for field, val in (("kind", "pose_set"), ("status", "ready"), ("origin", "hand")):
            errs = validate_item(character(**{field: val}))
            self.assertTrue(any(field in e for e in errs), (field, errs))

    def test_created_must_be_iso_string(self):
        self.assertTrue(any("created" in e for e in validate_item(character(created="2026-13-40"))))
        self.assertTrue(any("created" in e for e in validate_item(character(created=20261120))))

    def test_bool_and_nullable_color_variant_specs(self):
        ok = {"g": {"type": "bool"}, "tie": {"type": "color", "nullable": True}}
        self.assertEqual(validate_item(character(variants=ok)), [])
        for bad in ({"type": "bool", "nullable": True}, {"type": "color", "nullable": False},
                    {"type": "color", "nullable": "yes"}, {"type": "int"}):
            self.assertTrue(validate_item(character(variants={"x": bad})), bad)

    def test_env_variants_need_default(self):
        self.assertTrue(any("variants" in e for e in validate_item(env(variants=["night"]))))


class CatalogTests(unittest.TestCase):
    def test_local_item_cannot_shadow_builtin_id(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            write(t / "library/characters/hw-test.json", character())
            write(t / "channels/_library/characters/hw-test.json", character())
            with self.assertRaises(LibraryError) as cm:
                load_items(t / "library", t / "channels/_library")
            self.assertIn("hw-test", str(cm.exception))

    def test_id_must_match_filename(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            write(t / "library/characters/other.json", character())
            with self.assertRaises(LibraryError):
                load_items(t / "library", None)

    def test_invalid_item_raises(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            bad = character()
            del bad["name"]
            write(t / "library/characters/hw-test.json", bad)
            with self.assertRaises(LibraryError):
                load_items(t / "library", None)

    def test_pose_param_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            write(t / "library/poses/hw/acting.json", {"nod": {"a": 1}})
            ps = dict(COMMON, id="hw/acting", kind="pose", params_file="poses/hw/acting.json", needs=[])
            write(t / "library/poses/hw.acting.json", ps)
            items = load_items(t / "library", None)
            self.assertEqual(list(items), ["hw/acting"])

    def test_catalog_json_is_builtin_only_and_sorted(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            write(t / "library/characters/hw-zed.json", character(id="hw-zed"))
            write(t / "library/envs/room.json", env())
            write(t / "channels/_library/characters/hw-local.json", character(id="hw-local"))
            cat = build_catalog(t, t / "channels/_library")
            on_disk = json.loads((t / "library/catalog.json").read_text())
            self.assertEqual(on_disk, cat)
            self.assertEqual([i["id"] for i in on_disk["items"]], ["hw-zed", "room"])

    @unittest.skipUnless(HAVE_ART and HAVE_RIG, "library art and rig not included")
    def test_public_only_tree_builds_catalog_and_loads(self):
        """A tree holding only the items marked public (what the public export ships) still builds, loads and lists."""
        import random
        import shutil
        from library.lib import Library
        src = ROOT / "library"
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "skills" / "akra").mkdir(parents=True)
            public = {}
            for sub in ("characters", "envs", "poses"):
                for f in sorted((src / sub).glob("*.json")):
                    item = json.loads(f.read_text())
                    if not item.get("public"):
                        continue
                    public[item["id"]] = item
                    (t / "library" / sub).mkdir(parents=True, exist_ok=True)
                    shutil.copy(f, t / "library" / sub / f.name)
                    if item["kind"] == "env":
                        shutil.copy(src / "envs" / item["module"], t / "library" / "envs" / item["module"])
                    if item["kind"] == "pose":
                        dst = t / "library" / item["params_file"]
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(src / item["params_file"], dst)
            shutil.copy(src / "envs" / "_common.py", t / "library" / "envs" / "_common.py")
            shutil.copytree(src / "rig", t / "library" / "rig")
            for f in ("__init__.py", "lib.py", "catalog.py", "schema.py"):
                shutil.copy(src / f, t / "library" / f)
            cat = build_catalog(t)
            ids = {i["id"] for i in cat["items"]}
            self.assertEqual(ids, set(public))
            self.assertTrue(all(i["public"] for i in cat["items"]))
            self.assertEqual(set(load_items(t / "library")), ids)
            for name in ("toon", "hw"):
                channel = f"demo-{name}"
                char = min(i for i, it in public.items() if it["kind"] == "character" and it["style"] == name)
                env = min(i for i, it in public.items() if it["kind"] == "env" and it["style"] == name)
                proj = t / "render" / name / "ep-001"
                proj.mkdir(parents=True)
                (t / "channels" / channel).mkdir(parents=True)
                (t / "channels" / channel / "library.json").write_text(
                    json.dumps({"style": name, "visual_mode": "x", "items": []}))
                lib = Library(proj, channel)
                self.assertIn("<g", lib.character(char, "c1", 540, 1200))
                fn, backdrop = lib.env(env)
                far, mid = fn(random.Random(1), [])
                self.assertTrue(far)


if __name__ == "__main__":
    unittest.main()
