"""qa_render.py: which channel an episode folder belongs to (no built-in default channel)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "skills" / "akra" / "scripts"))
import qa_render  # noqa: E402


class TestQaRenderLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add_channel(self, cid, **prof):
        d = self.root / "channels" / cid
        d.mkdir(parents=True)
        (d / "channel.json").write_text(json.dumps({"id": cid, **prof}))

    def test_nested(self):
        root, ch = qa_render.locate(str(self.root / "render" / "my-ch" / "ep-003"))
        self.assertEqual((Path(root), ch), (self.root, "my-ch"))

    def test_flat_declared(self):
        self.add_channel("legacy", render_layout="flat")
        root, ch = qa_render.locate(str(self.root / "render" / "ep-003"))
        self.assertEqual((Path(root), ch), (self.root, "legacy"))

    def test_flat_undeclared_has_no_channel(self):
        root, ch = qa_render.locate(str(self.root / "render" / "ep-003"))
        self.assertEqual((Path(root), ch), (self.root, None))




class TestQaAddons(unittest.TestCase):
    PATCHES = {"probe": lambda m: {"duration": 30, "width": 1080, "height": 1920, "fps": 30, "audio": True},
               "loudness": lambda m: (-14.0, -2.0), "loop_ssim": lambda m, t: 0.99, "silences": lambda m: [],
               "library_checks": lambda ep, do_freeze=False: []}

    def run_qa(self, addon_dir):
        import contextlib
        import io
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp) / "render" / "ch" / "ep-001"
            (ep / "renders").mkdir(parents=True)
            (ep / "renders" / "a.mp4").write_bytes(b"x")
            out = io.StringIO()
            code = 0
            with mock.patch.multiple(qa_render, ADDON_DIR=Path(addon_dir), **self.PATCHES), \
                 mock.patch.object(sys, "argv", ["qa_render.py", str(ep), "--channel", "ch", "--no-copy"]), \
                 contextlib.redirect_stdout(out):
                try:
                    qa_render.main()
                except SystemExit as e:
                    code = e.code or 0
        return code, out.getvalue()

    def test_no_addons_no_extra_rows(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self.run_qa(d)
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)

    def test_addon_rows_and_notes(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "qa_addon_zzdemo.py").write_text(
                "def qa_checks(ep_dir, channel):\n"
                "    return [('demo', False, 'bad', 'good', None), ('demo2', True, '', '', 'demo2: skipped (x)')]\n")
            try:
                code, out = self.run_qa(d)
            finally:
                sys.modules.pop("qa_addon_zzdemo", None)
        self.assertNotEqual(code, 0)
        self.assertIn("demo", out)
        self.assertIn("demo2: skipped (x)", out)

    def test_broken_addon_fails_its_row_only(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "qa_addon_zzbroken.py").write_text("def qa_checks(ep_dir, channel):\n    raise RuntimeError('boom')\n")
            try:
                code, out = self.run_qa(d)
            finally:
                sys.modules.pop("qa_addon_zzbroken", None)
        self.assertNotEqual(code, 0)
        self.assertIn("add-on error: boom", out)


if __name__ == "__main__":
    unittest.main()
