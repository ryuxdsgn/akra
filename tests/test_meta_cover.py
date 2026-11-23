import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "skills", "akra", "scripts"))
import meta_upload as mu  # noqa: E402
import validate_episode as ve  # noqa: E402


class RenderMatches(unittest.TestCase):
    def test_own_render_passes(self):
        ep = {"id": "ep-013"}
        self.assertTrue(mu.render_matches(ep, "render/demo/ep-013/renders/ep-013_2026-11-23_07-33-34.mp4"))
        self.assertTrue(mu.render_matches(ep, "channels/demo/episodes/ep-013-assets/final.mp4"))

    def test_other_episode_render_fails(self):
        ep = {"id": "ep-013"}
        self.assertFalse(mu.render_matches(ep, "render/demo/ep-012/renders/ep-012_2026-11-22_15-43-10.mp4"))
        self.assertFalse(mu.render_matches({"id": "ep-01"}, "render/demo/ep-013/renders/ep-013.mp4"))


class CoverSeconds(unittest.TestCase):
    def test_default_is_share_of_duration(self):
        self.assertEqual(mu.cover_seconds({}, 60.0), 27.0)

    def test_episode_override_and_clamp(self):
        self.assertEqual(mu.cover_seconds({"cover_at": 12.5}, 60.0), 12.5)
        self.assertEqual(mu.cover_seconds({"cover_at": 99}, 60.0), 59.5)
        self.assertEqual(mu.cover_seconds({"cover_at": -3}, 60.0), 0.0)

    def test_unknown_duration(self):
        self.assertEqual(mu.cover_seconds({}, None), 0.0)
        self.assertEqual(mu.cover_seconds({"cover_at": 20}, None), 20.0)


class ValidatorRenderOwner(unittest.TestCase):
    def test_flags_other_episode_render(self):
        self.assertEqual(ve.check_render_owner({"id": "ep-013", "render": "render/demo/ep-013/renders/x.mp4"}), [])
        self.assertTrue(ve.check_render_owner({"id": "ep-013", "render": "render/demo/ep-012/renders/ep-012.mp4"}))
        self.assertEqual(ve.check_render_owner({"id": "ep-013"}), [])


if __name__ == "__main__":
    unittest.main()
