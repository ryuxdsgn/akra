"""render/_template three3d.py + animekit.py: Three.js / anime.js scenes driven by the scene's GSAP clock."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "render" / "_template"))
import animekit  # noqa: E402
import hf  # noqa: E402
import three3d  # noqa: E402

EXAMPLE = ROOT / "skills" / "akra" / "templates" / "episode.example.json"


class TestThree3d(unittest.TestCase):
    def setUp(self):
        self.html, self.js = three3d.scene("s03", 4.0, "const m = new THREE.Mesh(); scene.add(m);\nreturn (t) => {};",
                                           region=(0, 250, 1080, 920), seed=7)

    def test_pinned_three_and_canvas_region(self):
        self.assertIn("https://cdn.jsdelivr.net/npm/three@0.184.0/+esm", self.html)
        self.assertRegex(self.three_version(), r"^\d+\.\d+\.\d+$")
        self.assertIn('<canvas id="s03-3d" width="1080" height="920"', self.html)
        self.assertIn("top:250px", self.html)

    def three_version(self):
        return three3d.THREE_VERSION

    def test_clock_tween_and_build_ready(self):
        self.assertIn('window.__hf.buildReady["s03-3d"]', self.js)
        self.assertIn("h.fail=j", self.js)                       # setup errors reject instead of hanging
        self.assertIn("tl.to(c,{t:4.00,duration:4.00,ease:\"none\"", self.js)
        self.assertIn("compileAsync", self.html)                 # setup waits for the shader compile

    def test_no_clock_driven_code(self):
        for bad in ("requestAnimationFrame", "setAnimationLoop", "Math.random", "performance.now", "Date.now"):
            self.assertNotIn(bad, self.html + self.js, bad)
        self.assertIn("let seed = 7", self.html)


class TestAnimekit(unittest.TestCase):
    def setUp(self):
        self.html, self.js = animekit.scene("s04", 3.0, "return createTimeline({ autoplay: false });", seed=3)

    def test_pinned_anime_and_seek(self):
        self.assertIn("https://cdn.jsdelivr.net/npm/animejs@4.4.1/+esm", self.html)
        self.assertIn("a.seek(t * 1000, true)", self.html)
        self.assertIn('window.__hf.buildReady["s04-anime"]', self.js)
        self.assertIn("createSeededRandom(3)", self.html)

    def test_after_hook_for_redraws(self):
        self.assertIn("made && made.anims", self.html)
        self.assertIn("if (after) after(t)", self.html)

    def test_body_not_awaited(self):
        # anime.js animations are thenables: awaiting the body would wait for an animation that never plays
        self.assertNotIn("await (async", self.html)


class TestHfExtraLayer(unittest.TestCase):
    def test_two_tuple_scene_file_unchanged(self):
        self.assertEqual(hf.scene_file("s01", "<g/>", "", 2.0), hf.scene_file("s01", "<g/>", "", 2.0, ""))
        self.assertNotIn("s01-x", hf.scene_file("s01", "<g/>", "", 2.0))

    def test_build_accepts_three_tuple_scene(self):
        def s01(p, d, shot):
            html, js = three3d.scene(p, d, "return (t) => {};")
            return "<g/>", js, html

        with tempfile.TemporaryDirectory() as tmp:
            hf.build(tmp, str(EXAMPLE), [s01], [], "TEST", xfade=0.2)
            comp = (Path(tmp) / "compositions" / "s01.html").read_text()
            self.assertLess(comp.index('id="s01-x"'), comp.index('id="s01-svg"'))   # 3D layer under the SVG
            self.assertIn('<script type="module">', comp)
            s02 = (Path(tmp) / "compositions" / "s02.html").read_text()
            self.assertNotIn("s02-x", s02)                                         # storyboard scenes untouched
            idx = (Path(tmp) / "index.html").read_text()
            self.assertEqual(len(re.findall(r'data-composition-src="compositions/s\d\d.html"', idx)),
                             len(json.loads(EXAMPLE.read_text())["shots"]))


if __name__ == "__main__":
    unittest.main()
