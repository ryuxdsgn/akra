"""HyperFrames diagram pipeline: `diagram` shots and the `build` mode."""
import json
import unittest

from helpers import SKILL_DIR, make_valid

from validate_episode import validate


def all_diagram(ep: dict) -> dict:
    for shot in ep["shots"]:
        shot["type"] = "diagram"
        shot["prompt"] = "Ballpoint pen ball rolls on paper; cyan arrows show ink flowing onto the ball"
    return ep


class TestDiagramShots(unittest.TestCase):
    def test_all_diagram_episode_is_valid(self):
        self.assertEqual(validate(all_diagram(make_valid())), [])

    def test_diagram_shot_needs_scene_description(self):
        ep = all_diagram(make_valid())
        ep["shots"][0]["prompt"] = " "
        self.assertIn("shots[0]: prompt is empty", validate(ep))

    def test_veo_no_longer_a_new_shot_type(self):
        ep = all_diagram(make_valid())
        ep["shots"][0]["type"] = "veo"
        self.assertTrue(any("legacy Google Flow" in e for e in validate(ep)))

    def test_unknown_type_still_rejected(self):
        ep = make_valid()
        ep["shots"][0]["type"] = "capcut"
        self.assertTrue(any("type must be one of" in e for e in validate(ep)))


class TestBuildMode(unittest.TestCase):
    def setUp(self):
        self.skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_router_has_build_mode(self):
        self.assertIn("`build`", self.skill_md)
        self.assertIn("references/build.md", self.skill_md)
        self.assertTrue((SKILL_DIR / "references" / "build.md").is_file())

    def test_build_reference_covers_pipeline(self):
        text = (SKILL_DIR / "references" / "build.md").read_text(encoding="utf-8")
        for token in ("HyperFrames", "npm run check", "snapshot", "1080", "1920",
                      "caption", "voiceover", "music"):
            self.assertIn(token.lower(), text.lower(), token)

    def test_capcut_is_no_longer_the_default_editor(self):
        self.assertNotIn("**CapCut**", self.skill_md)

    def test_example_episode_uses_diagrams(self):
        ep = json.loads((SKILL_DIR / "templates" / "episode.example.json").read_text())
        self.assertTrue(any(s["type"] == "diagram" for s in ep["shots"]))
        self.assertEqual(validate(ep), [])




class TestVoiceoverDuration(unittest.TestCase):
    def test_real_vo_duration_overrides_word_estimate(self):
        ep = all_diagram(make_valid())  # 100 words ~ 40 s estimate, shots end at 40
        ep["shots"][-1]["t_end"] = 36.0
        self.assertTrue(any("cover only" in e for e in validate(ep)))
        ep["vo_duration"] = 36.5
        self.assertEqual(validate(ep), [])

    def test_vo_duration_must_be_positive_number(self):
        ep = all_diagram(make_valid())
        ep["vo_duration"] = "47s"
        self.assertTrue(any("vo_duration" in e for e in validate(ep)))


if __name__ == "__main__":
    unittest.main()
