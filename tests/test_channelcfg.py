"""render/_template/channelcfg.py: channel from folder layout + brand from channel.json."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "render" / "_template"))
import channelcfg  # noqa: E402


class TestChannelCfg(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add_channel(self, cid, **prof):
        d = self.root / "channels" / cid
        d.mkdir(parents=True)
        (d / "channel.json").write_text(json.dumps({"id": cid, **prof}))

    def test_flat_layout_uses_the_channel_that_declares_it(self):
        self.add_channel("other")
        self.add_channel("my-first", render_layout="flat")
        root, ch = channelcfg.locate(self.root / "render" / "ep-007")
        self.assertEqual((Path(root), ch), (self.root, "my-first"))

    def test_flat_layout_without_declaration_is_an_error(self):
        self.add_channel("other")
        with self.assertRaises(channelcfg.LayoutError) as cm:
            channelcfg.locate(self.root / "render" / "ep-007")
        self.assertIn("render/<channel-id>/ep-007", str(cm.exception))

    def test_flat_layout_declared_twice_is_an_error(self):
        self.add_channel("a", render_layout="flat")
        self.add_channel("b", render_layout="flat")
        with self.assertRaises(channelcfg.LayoutError) as cm:
            channelcfg.locate(self.root / "render" / "ep-007")
        self.assertIn("a, b", str(cm.exception))

    def test_template_folder_has_no_channel(self):
        root, ch = channelcfg.locate(self.root / "render" / "_template")
        self.assertEqual((Path(root), ch), (self.root, None))
        cfg = channelcfg.settings(self.root / "render" / "_template")
        self.assertEqual((cfg["channel"], cfg["brand_text"]), (None, ""))

    def test_nested_channel_layout(self):
        root, ch = channelcfg.locate(self.root / "render" / "deep-earth" / "ep-001")
        self.assertEqual((Path(root), ch), (self.root, "deep-earth"))

    def test_defaults_without_profile(self):
        cfg = channelcfg.settings(self.root / "render" / "my-channel" / "ep-001")
        self.assertEqual(cfg["brand_text"], "MY-CHANNEL")
        self.assertEqual(cfg["colors"]["bg"], channelcfg.DEFAULT_COLORS["bg"])
        self.assertEqual((cfg["font"], cfg["language"], cfg["cap_max_chars"]), ("Montserrat", "en", 20))

    def test_brand_from_profile(self):
        ch_dir = self.root / "channels" / "deep-earth"
        ch_dir.mkdir(parents=True)
        (ch_dir / "channel.json").write_text(json.dumps({
            "name": "Deep Earth", "language": "id",
            "brand": {"font": "Nunito", "colors": {"bg": "#FFF3D6"}}}))
        cfg = channelcfg.settings(self.root / "render" / "deep-earth" / "ep-001")
        self.assertEqual(cfg["brand_text"], "DEEP EARTH")
        self.assertEqual(cfg["colors"]["bg"], "#FFF3D6")
        self.assertEqual(cfg["colors"]["ink"], channelcfg.DEFAULT_COLORS["ink"])      # unset colours keep the default
        self.assertEqual((cfg["font"], cfg["language"], cfg["cap_max_chars"]), ("Nunito", "id", 18))


if __name__ == "__main__":
    unittest.main()
