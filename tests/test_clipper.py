"""Clipper mode: time parsing, gameplay coverage of the split layout, cleanup of raw downloads."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "akra", "scripts"))
import clip_fetch  # noqa: E402
import clip_split  # noqa: E402

try:
    import PIL  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False
HAVE_FONT = any(Path(f).expanduser().exists() for f in clip_split.FONT_CANDIDATES)


class Times(unittest.TestCase):
    def test_parse_and_format(self):
        self.assertEqual(clip_fetch.parse_t("6:40"), 400.0)
        self.assertEqual(clip_fetch.parse_t("1:02:03"), 3723.0)
        self.assertEqual(clip_fetch.parse_t(12.5), 12.5)
        self.assertEqual(clip_fetch.hms(400), "6:40.0")

    def test_hype_words(self):
        self.assertTrue(clip_fetch.HYPE.search("anjir gila"))
        self.assertTrue(clip_fetch.HYPE.search("no way bro"))
        self.assertFalse(clip_fetch.HYPE.search("pesawat"))


@unittest.skipUnless(HAVE_PIL and HAVE_FONT, "Pillow or a heavy font missing")
class Coverage(unittest.TestCase):
    def test_gameplay_stays_clear(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = {"channel": "x", "dur": 6.0, "hook": "A VERY LONG HOOK THAT NEEDS TO SHRINK TO FIT THE FRAME",
                   "credit": "Clip: Someone", "face": [0, 0, 400, 260], "game": [0, 0, 636, 720],
                   "sources": {"a": "source/a.mp4"},
                   "shots": [["a", 0, 2.0, ""], ["a", 5, 4.0, "SECOND LABEL"]],
                   "words": [{"text": "hello", "start": 0.2, "end": 0.6}, {"text": "world!", "start": 2.5, "end": 3.0}]}
            Path(d, "clip.json").write_text(json.dumps(cfg))
            worst, _ = clip_split.Clip(d).coverage()
            self.assertLessEqual(worst, 0.08)


class Clean(unittest.TestCase):
    def test_dry_run_keeps_then_yes_deletes(self):
        with tempfile.TemporaryDirectory() as d:
            for sub in ("raw", "source", "renders"):
                Path(d, sub).mkdir()
                Path(d, sub, "f.bin").write_bytes(b"x" * 10)
            Path(d, "clip.json").write_text("{}")
            with redirect_stdout(io.StringIO()):
                clip_split.clean(d, yes=False)
            self.assertTrue(Path(d, "raw").exists())
            with redirect_stdout(io.StringIO()):
                clip_split.clean(d, yes=True)
            self.assertFalse(Path(d, "raw").exists())
            self.assertFalse(Path(d, "source").exists())
            self.assertTrue(Path(d, "renders", "f.bin").exists())
            self.assertTrue(Path(d, "clip.json").exists())


if __name__ == "__main__":
    unittest.main()
