"""Camera grammar helpers (scenekit) and the whole-frame QA add-on (qa_addon_frames)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "render", "_template"))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "akra", "scripts"))
import scenekit as sk  # noqa: E402
try:
    import qa_addon_frames as qf  # noqa: E402  (a local QA add-on; not every distribution ships it)
except ImportError:
    qf = None


class Helpers(unittest.TestCase):
    def test_cam_nests_outer_and_inner(self):
        self.assertEqual(sk.cam("s1", "<rect/>"), '<g id="s1-cam"><g id="s1-camk"><rect/></g></g>')

    def test_creep_scale_follows_rate(self):
        js = sk.creep("s1", 2.0, rate=0.2)
        s1 = float(re.findall(r"scale:([\d.]+)", js)[1])
        self.assertAlmostEqual(s1, 1.002 ** 60, places=3)
        self.assertIn('ease:"none"', js)

    def test_kick_decays_and_flips(self):
        js = sk.kick("s1", 1.0, amp=10, frames=4)
        xs = [float(x) for x in re.findall(r"\{x:(-?[\d.]+),y", js)]
        self.assertEqual(xs[-1], 0.0)
        self.assertTrue(all(a * b < 0 for a, b in zip(xs[:-2], xs[1:-1])))       # sign flips every frame
        self.assertTrue(all(abs(a) > abs(b) for a, b in zip(xs[:-1], xs[1:])))    # and decays
        self.assertIn('"#s1-camk"', js)

    def test_lead_is_two_frames_early_and_never_negative(self):
        self.assertAlmostEqual(sk.lead(1.0), 1.0 - 2 / 30, places=3)
        self.assertEqual(sk.lead(0.02), 0.0)

    def test_glide_and_roll_use_smootherstep(self):
        self.assertIn(sk.SMOOTHERSTEP, sk.glide("s1", "cam", 0.5, 0.8, x=100))
        self.assertIn("rotation:4.5", sk.roll("s1", 1.0))


@unittest.skipUnless(qf and shutil.which("ffmpeg"), "qa_addon_frames or ffmpeg missing")
class FramesAddon(unittest.TestCase):
    def test_finds_freeze_white_and_pop_but_not_motion(self):
        with tempfile.TemporaryDirectory() as d:
            mp4 = os.path.join(d, "t.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y",
                            "-f", "lavfi", "-i", "testsrc2=s=216x384:r=30:d=1",
                            "-f", "lavfi", "-i", "color=c=gray:s=216x384:r=30:d=1",
                            "-f", "lavfi", "-i", "testsrc2=s=216x384:r=30:d=1",
                            "-filter_complex", "[0][1][2]concat=n=3,drawbox=enable='eq(n,75)':x=0:y=0:w=216:h=384:color=white:t=fill",
                            mp4], check=True)
            r = qf.scan(mp4)
            self.assertEqual(len(r["frozen"]), 1)
            a, b = r["frozen"][0]
            self.assertTrue(1.0 <= a <= 1.3 and 1.8 <= b <= 2.05, r["frozen"])
            self.assertEqual(r["white"], [2.5])
            self.assertEqual(r["pop"], [2.5])
            self.assertEqual(r["black"], [])


if __name__ == "__main__":
    unittest.main()
