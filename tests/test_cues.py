import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "render", "_template"))
import cues  # noqa: E402

FACES = [(896, 951, 146), (184, 938, 146)]       # two seated characters' heads at scale 1.24
CAPTION = (1440, 1560)
KNEE, ANKLE = (314, 1242), (449, 1225)          # the left character's extended leg


class FloatingMark(unittest.TestCase):
    def test_old_hand_placed_cross_is_flagged(self):
        b = cues.Board(FACES, CAPTION)
        b.items.append(("mark", "x", cues.circle_box(404, 1052, 44), 0, 2, {"seg": (KNEE, ANKLE), "center": (404, 1052)}))
        self.assertTrue(any("floats" in m for m in b.check()))

    def test_mark_at_sits_next_to_the_limb(self):
        b = cues.Board(FACES, CAPTION)
        svg = b.mark_at("x", KNEE, ANKLE, False, 0, 2)
        self.assertIn('id="x"', svg)
        self.assertEqual(b.check(), [])
        (_, _, box, _, _, ex) = b.items[0]
        self.assertLess(ex["center"][1], min(KNEE[1], ANKLE[1]))        # above a level leg


class Arrows(unittest.TestCase):
    def test_short_arrow_is_flagged(self):
        b = cues.Board(FACES, CAPTION)
        b.arrow_at("a", (648, 1228), (-1, 0.5), 0, 1, length=80)
        self.assertTrue(any("too short" in m for m in b.check()))

    def test_readable_arrow_passes(self):
        b = cues.Board(FACES, CAPTION)
        svg = b.arrow_at("a", (648, 1228), (-1, 0.5), 0, 1)
        self.assertIn('id="a-l"', svg)
        self.assertEqual(b.check(), [])


class Layout(unittest.TestCase):
    def test_chips_share_the_left_column(self):
        b = cues.Board(FACES, CAPTION)
        b.chip("c1", "SEJAUH NYAMAN", 1, 0, 3)
        b.chip("c2", "NYERI? BERHENTI", 2, 0, 3)
        self.assertEqual({it[2][0] for it in b.items}, {cues.INFO_X})
        self.assertEqual(b.check(), [])

    def test_face_caption_safe_and_overlap(self):
        b = cues.Board(FACES, CAPTION)
        b.items.append(("chip", "face", (800, 900, 1000, 980), 0, 1, {}))
        b.items.append(("chip", "cap", (300, 1450, 600, 1500), 0, 1, {}))
        b.items.append(("chip", "edge", (900, 300, 1060, 360), 0, 1, {}))
        b.chip("c1", "A", 1, 0, 2)
        b.chip("c2", "B", 1, 1, 3)                     # same lane, overlapping time
        msgs = " | ".join(b.check())
        for want in ("covers a face", "caption band", "safe area", "overlap on screen"):
            self.assertIn(want, msgs)

    def test_same_lane_at_different_times_is_fine(self):
        b = cues.Board(FACES, CAPTION)
        b.chip("c1", "A", 1, 0, 2)
        b.chip("c2", "B", 1, 2, 3)
        self.assertEqual(b.check(), [])

    def test_assert_clean_stops(self):
        b = cues.Board(FACES, CAPTION)
        b.arrow_at("a", (648, 1228), (-1, 0), 0, 1, length=50)
        with self.assertRaises(SystemExit):
            b.assert_clean()


if __name__ == "__main__":
    unittest.main()
