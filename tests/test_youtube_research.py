import argparse
import unittest

import helpers  # noqa: F401  (puts skills/akra/scripts on sys.path)
import youtube_research as yr


def args(**kw):
    base = dict(query=None, days=None, min_ratio=None, min_views=None)
    base.update(kw)
    return argparse.Namespace(**base)


def vid(i, ch, views, dur=40):
    return {"id": i, "title": f"t{i}", "channel": ch, "channel_id": ch, "views": views,
            "duration_s": dur, "age_days": 5, "query": "q", "subs": 1000}


class TestResearch(unittest.TestCase):
    def test_settings_from_channel_and_flags(self):
        ch = {"niche": "how things work", "language": "id",
              "research": {"queries": ["cara kerja"], "days": 30, "exclude_channels": ["UCx"]},
              "youtube_channel_id": "UCme"}
        cfg = yr.settings(ch, args())
        self.assertEqual(cfg["queries"], ["cara kerja"])
        self.assertEqual((cfg["days"], cfg["min_ratio"], cfg["region"]), (30, 3.0, "ID"))
        self.assertEqual(cfg["exclude"], {"UCx", "UCme"})
        cfg = yr.settings(ch, args(query=["lain"], days=7, min_ratio=5))
        self.assertEqual((cfg["queries"], cfg["days"], cfg["min_ratio"]), (["lain"], 7, 5))

    def test_settings_falls_back_to_niche_then_fails(self):
        self.assertEqual(yr.settings({"niche": "space"}, args())["queries"], ["space"])
        self.assertIsNone(yr.settings({"niche": "space"}, args())["region"])
        with self.assertRaises(SystemExit):
            yr.settings({}, args())

    def test_baseline_excludes_candidate_and_needs_three(self):
        self.assertEqual(yr.baseline([("a", 1000), ("b", 100), ("c", 200), ("d", 300)], "a"), 200)
        self.assertIsNone(yr.baseline([("a", 1000), ("b", 100), ("c", 200)], "a"))

    def test_score_small_channel_hit_counts_big_channel_normal_does_not(self):
        videos = [vid("s1", "small", 50_000), vid("b1", "big", 900_000), vid("long", "small", 90_000, dur=600)]
        baselines = {"small": [("s1", 50_000), ("x", 1_000), ("y", 2_000), ("z", 3_000)],
                     "big": [("b1", 900_000), ("p", 800_000), ("q", 1_000_000), ("r", 700_000)]}
        rows = yr.score(videos, baselines, 3)
        self.assertEqual([r["id"] for r in rows], ["s1"])        # big channel's ordinary video and the long video drop out
        self.assertEqual((rows[0]["baseline"], rows[0]["ratio"]), (2000, 25.0))

    def test_score_min_views_floor(self):
        baselines = {"tiny": [("t1", 5_000), ("a", 10), ("b", 10), ("c", 10)]}
        self.assertEqual(yr.score([vid("t1", "tiny", 5_000)], baselines, 3, (), 20_000), [])
        self.assertEqual(len(yr.score([vid("t1", "tiny", 5_000)], baselines, 3)), 1)
        self.assertEqual(yr.settings({"niche": "x"}, args())["min_views"], 20_000)
        self.assertEqual(yr.settings({"niche": "x"}, args(min_views=0))["min_views"], 0)

    def test_score_skips_excluded_channel(self):
        baselines = {"me": [("m1", 9_000), ("a", 10), ("b", 10), ("c", 10)]}
        self.assertEqual(yr.score([vid("m1", "me", 9_000)], baselines, 3, {"me"}), [])

    def test_render_md(self):
        cfg = {"queries": ["q"], "days": 60, "min_ratio": 3, "min_views": 20000, "region": None}
        row = dict(vid("abc", "Chan|nel", 12345), baseline=100, ratio=123.4, title="A | B")
        md = yr.render_md([row], cfg, "2026-01-15")
        self.assertIn("https://youtube.com/shorts/abc", md)
        self.assertIn("A / B", md)
        self.assertIn("12,345", md)
        self.assertIn("never copy", md)
        self.assertIn("No outliers", yr.render_md([], cfg, "2026-01-15"))

    def test_iso_duration(self):
        self.assertEqual(yr.iso_duration("PT1M5S"), 65)
        self.assertEqual(yr.iso_duration("bad"), 0)


if __name__ == "__main__":
    unittest.main()


class TestResearchDocs(unittest.TestCase):
    def test_ideas_and_script_use_research(self):
        from helpers import SKILL_DIR
        ideas = (SKILL_DIR / "references" / "idea-bank.md").read_text(encoding="utf-8")
        self.assertIn("youtube_research.py outliers", ideas)
        self.assertIn("patterns.md", ideas)
        self.assertIn("beda", ideas)
        self.assertIn("patterns.md", (SKILL_DIR / "references" / "script.md").read_text(encoding="utf-8"))
        self.assertIn("youtube_research.py", (SKILL_DIR / "references" / "review.md").read_text(encoding="utf-8"))
        self.assertTrue((SKILL_DIR / "templates" / "patterns.md").is_file())
