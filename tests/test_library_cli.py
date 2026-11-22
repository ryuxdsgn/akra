import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from helpers import ROOT

sys.path.insert(0, str(ROOT))
from library import cli  # noqa: E402

COMMON = {"origin": "builtin", "created": "2026-01-01", "created_by": "tester", "status": "draft", "examples": []}


def _char(iid, style, name):
    return dict(COMMON, id=iid, kind="character", name=name, tags=["test"], style=style, face=style,
                preview=f"previews/characters/{iid}.png", base_look={"skin": "#F0C8A0"},
                variants={"skin": {"type": "color"}}, scale_hint=1.0)


# Synthetic items only (the public tree ships no library items): two characters, one env with a shared helper, one pose set.
ITEMS = {
    "characters/toon_a.json": _char("toon_a", "toon", "Toon A"),
    "characters/hw_a.json": _char("hw_a", "hw", "Host A"),
    "envs/room_a.json": dict(COMMON, id="room_a", kind="env", name="Room A", tags=["room"], style="hw",
                             preview="previews/envs/room_a.png", module="room_a.py", function="build",
                             variants=["default", "night"], backdrop="#242C36", safe_area=[60, 820, 1020, 1170],
                             palette=["#242C36"]),
    "poses/toon.acting.json": dict(COMMON, id="toon/acting", kind="pose", name="Toon acting", tags=["acting"],
                                   style="toon", status="vetted", preview="previews/poses/toon.acting.png",
                                   params_file="poses/toon/acting.json", needs=[]),
}
ENV_MODULE = (
    "import importlib.util as _u\nimport pathlib as _p\n\n"
    "_s = _u.spec_from_file_location(\"_t_env_common\", _p.Path(__file__).with_name(\"_common.py\"))\n"
    "_c = _u.module_from_spec(_s)\n_s.loader.exec_module(_c)\n\n\n"
    "def build(rnd, fl, variant=\"default\"):\n"
    "    return f'<rect width=\"{_c.W}\" height=\"{_c.H}\" fill=\"#242C36\"/>', \"\"\n"
)


def make_repo(tmp):
    repo = Path(tmp)
    (repo / "skills" / "akra").mkdir(parents=True)
    for rel, item in ITEMS.items():
        f = repo / "library" / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(item, indent=2) + "\n")
    (repo / "library" / "envs" / "room_a.py").write_text(ENV_MODULE)
    (repo / "library" / "envs" / "_common.py").write_text("W, H = 1080, 1920\n")
    return repo


def run(argv, repo):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(argv, root=repo)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name)

    def test_list_filters(self):
        code, out, _ = run(["list"], self.repo)
        self.assertEqual(code, 0)
        rows = [r.split() for r in out.strip().splitlines()]
        self.assertEqual({r[0] for r in rows}, {"toon_a", "hw_a", "room_a", "toon/acting"})
        self.assertIn(["toon_a", "character", "toon", "draft", "builtin"], rows)
        _, out, _ = run(["list", "--kind", "character"], self.repo)
        self.assertEqual({r.split()[0] for r in out.strip().splitlines()}, {"toon_a", "hw_a"})
        _, out, _ = run(["list", "--style", "hw"], self.repo)
        self.assertEqual({r.split()[0] for r in out.strip().splitlines()}, {"hw_a", "room_a"})
        _, out, _ = run(["list", "--status", "draft"], self.repo)
        self.assertEqual({r.split()[0] for r in out.strip().splitlines()}, {"toon_a", "hw_a", "room_a"})
        _, out, _ = run(["list", "--status", "vetted"], self.repo)
        self.assertEqual({r.split()[0] for r in out.strip().splitlines()}, {"toon/acting"})

    def test_vet_refuses_without_fresh_preview(self):
        item_file = self.repo / "library" / "characters" / "hw_a.json"
        code, _, err = run(["vet", "hw_a"], self.repo)
        self.assertNotEqual(code, 0)
        self.assertIn("preview", err)
        png = self.repo / "library" / "previews" / "characters" / "hw_a.png"
        png.parent.mkdir(parents=True)
        png.write_bytes(b"png")
        old = item_file.stat().st_mtime - 100
        os.utime(png, (old, old))
        code, _, err = run(["vet", "hw_a"], self.repo)
        self.assertNotEqual(code, 0)
        self.assertEqual(json.loads(item_file.read_text())["status"], "draft")
        new = item_file.stat().st_mtime + 100
        os.utime(png, (new, new))
        code, _, _ = run(["vet", "hw_a"], self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(item_file.read_text())["status"], "vetted")

    def test_promote_strips_channel_fields_and_requires_yes(self):
        item = dict(ITEMS["characters/toon_a.json"])
        item.update(id="pak_rt", name="Pak RT", origin="generated", token_cost=3, status="vetted",
                    examples=["deep-earth/ep-009"], real_name="Sam Example", notes="based on the neighbour",
                    preview="previews/characters/pak_rt.png")
        local = self.repo / "channels" / "_library" / "characters"
        local.mkdir(parents=True)
        (local / "pak_rt.json").write_text(json.dumps(item))
        code, _, err = run(["promote", "pak_rt"], self.repo)
        self.assertNotEqual(code, 0)
        self.assertTrue((local / "pak_rt.json").exists())
        code, out, _ = run(["promote", "pak_rt", "--yes"], self.repo)
        self.assertEqual(code, 0, out)
        self.assertIn("real_name", out)
        self.assertIn("notes", out)
        self.assertFalse((local / "pak_rt.json").exists())
        moved = json.loads((self.repo / "library" / "characters" / "pak_rt.json").read_text())
        self.assertEqual(moved["origin"], "builtin")
        self.assertEqual(moved["examples"], [])
        self.assertNotIn("real_name", moved)
        self.assertNotIn("notes", moved)

    def _local(self, sub):
        d = self.repo / "channels" / "_library" / sub
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_promote_pose_moves_params_file(self):
        item = dict(ITEMS["poses/toon.acting.json"])
        item.update(id="toon/extra", origin="generated", token_cost=1, params_file="poses/toon/extra.json",
                    preview="previews/poses/toon.extra.png")
        (self._local("poses") / "toon.extra.json").write_text(json.dumps(item))
        params = self._local("poses/toon") / "extra.json"
        params.write_text(json.dumps({"wave2": {}}))
        code, out, err = run(["promote", "toon/extra", "--yes"], self.repo)
        self.assertEqual(code, 0, out + err)
        self.assertTrue((self.repo / "library" / "poses" / "toon" / "extra.json").is_file())
        self.assertFalse(params.exists())

    def test_promote_env_copies_missing_helper_and_refuses_overwrite(self):
        lib_envs = self.repo / "library" / "envs"
        item = json.loads((lib_envs / "room_a.json").read_text())
        item.update(id="room2", origin="generated", token_cost=2, status="vetted", module="room2.py",
                    preview="previews/envs/room2.png")
        local = self._local("envs")
        (local / "room2.json").write_text(json.dumps(item))
        src = (lib_envs / "room_a.py").read_text().replace('with_name("_common.py")', 'with_name("_extra.py")')
        (local / "room2.py").write_text(src)
        (local / "_extra.py").write_text((lib_envs / "_common.py").read_text())
        code, out, err = run(["promote", "room2", "--yes"], self.repo)
        self.assertEqual(code, 0, out + err)
        self.assertTrue((lib_envs / "room2.py").is_file())
        self.assertTrue((lib_envs / "_extra.py").is_file())
        self.assertTrue((local / "_extra.py").is_file())      # helper copied: other local envs may use it
        # a local item whose module file would overwrite a builtin one is refused, nothing moves
        (local / "room3.json").write_text(json.dumps(dict(item, id="room3", module="room_a.py",
                                                             preview="previews/envs/room3.png")))
        (local / "room_a.py").write_text("# local")
        code, _, err = run(["promote", "room3", "--yes"], self.repo)
        self.assertNotEqual(code, 0)
        self.assertIn("already exists", err)
        self.assertTrue((local / "room3.json").exists())
        self.assertNotEqual((lib_envs / "room_a.py").read_text(), "# local")

    def test_vet_twice_and_catalog_updated(self):
        item_file = self.repo / "library" / "characters" / "hw_a.json"
        png = self.repo / "library" / "previews" / "characters" / "hw_a.png"
        png.parent.mkdir(parents=True)
        png.write_bytes(b"png")
        new = item_file.stat().st_mtime + 100
        os.utime(png, (new, new))
        self.assertEqual(run(["vet", "hw_a"], self.repo)[0], 0)
        self.assertEqual(run(["vet", "hw_a"], self.repo)[0], 0)
        cat = json.loads((self.repo / "library" / "catalog.json").read_text())
        rows = cat["items"] if isinstance(cat, dict) and "items" in cat else cat
        hw_a = [r for r in (rows if isinstance(rows, list) else rows.values()) if r.get("id") == "hw_a"][0]
        self.assertEqual(hw_a["status"], "vetted")

    def test_promote_refuses_draft(self):
        item = dict(ITEMS["characters/toon_a.json"])
        item.update(id="pak_rw", origin="generated", token_cost=1, status="draft",
                    preview="previews/characters/pak_rw.png")
        (self._local("characters") / "pak_rw.json").write_text(json.dumps(item))
        code, _, err = run(["promote", "pak_rw", "--yes"], self.repo)
        self.assertNotEqual(code, 0)
        self.assertIn("vet it", err)

    def test_freeze_command_delegates(self):
        proj = self.repo / "render" / "ep-001"
        proj.mkdir(parents=True)
        with mock.patch.object(cli, "freeze", return_value=True) as m:
            code, out, _ = run(["freeze", str(proj), "--refresh"], self.repo)
        self.assertEqual(code, 0)
        m.assert_called_once_with(proj, refresh=True)


if __name__ == "__main__":
    unittest.main()
