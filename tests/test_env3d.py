"""env3d: the 3D world prelude for three3d scenes."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "render", "_template"))
import env3d  # noqa: E402
import three3d  # noqa: E402


class Prelude(unittest.TestCase):
    def test_presets_and_api(self):
        js = env3d.prelude("golden", view=(4.7, -8.8))
        for name in ("env.load", "env.put", "env.card", "env.creep", "env.focusOn", "env.unlit", "scene.userData.draw"):
            self.assertIn(name, js)
        self.assertIn('"disc": 1.0', js)
        self.assertIn(f"three@{three3d.THREE_VERSION}/examples/jsm/loaders/GLTFLoader.js", js)

    def test_switches_and_custom_preset(self):
        js = env3d.prelude({"sunI": 2.0}, ink=False, lens=False)
        self.assertIn('"sunI": 2.0', js)
        self.assertIn("on: { value: 0.0 }", js)
        self.assertIn("false ? env.blur", js)

    def test_bad_input(self):
        with self.assertRaises(KeyError):
            env3d.prelude("night")
        with self.assertRaises(ValueError):
            env3d.prelude("day", view=(0, 0))

    def test_three3d_lets_a_scene_draw_itself(self):
        html, _ = three3d.scene("s1", 2.0, "return (t) => {};", lights=False)
        self.assertIn("scene.userData.draw", html)


if __name__ == "__main__":
    unittest.main()
