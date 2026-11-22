"""library/preview.py: preferred preview characters come from an optional library/preview.json."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT))
from library import preview  # noqa: E402


def char(cid, style="hw", **kw):
    return dict({"id": cid, "kind": "character", "style": style, "status": "vetted", "public": True}, **kw)


class PreferredFile(unittest.TestCase):
    def test_missing_or_bad_file_means_no_preference(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(preview._preferred(Path(t) / "preview.json"), {})
            (Path(t) / "preview.json").write_text("not json")
            self.assertEqual(preview._preferred(Path(t) / "preview.json"), {})

    def test_file_lists_ids_per_style(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "preview.json"
            f.write_text(json.dumps({"preferred": {"hw": ["b", "a"]}}))
            self.assertEqual(preview._preferred(f), {"hw": ("b", "a")})

    def test_pick_order(self):
        items = {i: char(i) for i in ("a", "b", "c")}
        old = preview.PREFERRED
        try:
            preview.PREFERRED = {}
            self.assertEqual([c["id"] for c in preview._pick_characters(items, "hw", 2)], ["a", "b"])
            preview.PREFERRED = {"hw": ("c", "missing")}
            self.assertEqual([c["id"] for c in preview._pick_characters(items, "hw", 2)], ["c", "a"])
        finally:
            preview.PREFERRED = old


if __name__ == "__main__":
    unittest.main()
