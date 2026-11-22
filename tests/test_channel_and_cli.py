import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from helpers import make_channel, make_valid

from validate_episode import capacity, main, validate, validate_channel


def has_error(errors, field):
    return any(e.startswith(field) for e in errors)


class TestMetadata(unittest.TestCase):
    def _errors(self, **changes):
        ep = make_valid()
        ep.update(changes)
        return validate(ep)

    def test_title_too_long(self):
        self.assertTrue(has_error(self._errors(title="x" * 61), "title"))
        self.assertFalse(has_error(self._errors(title="x" * 60), "title"))

    def test_hashtag_count(self):
        self.assertTrue(has_error(self._errors(hashtags=["#a", "#b"]), "hashtags"))
        self.assertTrue(has_error(self._errors(hashtags=[f"#t{i}" for i in range(6)]), "hashtags"))
        self.assertFalse(has_error(self._errors(hashtags=[f"#t{i}" for i in range(5)]), "hashtags"))

    def test_hashtag_format(self):
        self.assertTrue(has_error(self._errors(hashtags=["#shorts", "#space facts", "#x"]), "hashtags"))
        self.assertTrue(has_error(self._errors(hashtags=["#shorts", "science", "#x"]), "hashtags"))
        self.assertTrue(has_error(self._errors(hashtags=["#shorts", 3, "#x"]), "hashtags"))

    def test_ai_disclosure_must_be_bool(self):
        self.assertTrue(has_error(self._errors(ai_disclosure="yes"), "ai_disclosure"))

    def test_music_source_allowlist(self):
        self.assertTrue(has_error(self._errors(music_source="spotify"), "music_source"))
        for ok in ("youtube_audio_library", "licensed", "none"):
            self.assertFalse(has_error(self._errors(music_source=ok), "music_source"))

    def test_originality_all_true(self):
        ep = make_valid()
        ep["originality_checklist"]["manual_edit"] = False
        self.assertTrue(has_error(validate(ep), "originality_checklist"))
        ep = make_valid()
        del ep["originality_checklist"]["added_value"]
        self.assertTrue(has_error(validate(ep), "originality_checklist"))

    def test_empty_title_or_description(self):
        self.assertTrue(has_error(self._errors(title=" "), "title"))
        self.assertTrue(has_error(self._errors(description=""), "description"))


class TestChannelProfile(unittest.TestCase):
    def test_channel_profile_valid(self):
        self.assertEqual(validate_channel(make_channel()), [])

    def test_channel_render_layout(self):
        self.assertEqual(validate_channel(make_channel(render_layout="flat")), [])
        self.assertTrue(has_error(validate_channel(make_channel(render_layout="nested")), "render_layout"))

    def test_channel_bad_status(self):
        self.assertTrue(has_error(validate_channel(make_channel(status="live")), "status"))

    def test_channel_bad_slot(self):
        self.assertTrue(has_error(validate_channel(make_channel(posting_slots=["25:00"])), "posting_slots"))
        self.assertTrue(has_error(validate_channel(make_channel(posting_slots=[])), "posting_slots"))

    def test_channel_timezone(self):
        for tz in ("UTC", "America/New_York", "Europe/London", "Asia/Jakarta"):
            self.assertEqual(validate_channel(make_channel(timezone=tz)), [], tz)
        for bad in ("Mars/Olympus", "", None, "WIB"):
            self.assertTrue(has_error(validate_channel(make_channel(timezone=bad)), "timezone"), bad)
        ch = make_channel()
        del ch["timezone"]
        self.assertTrue(has_error(validate_channel(ch), "timezone"))

    def test_channel_without_slots(self):
        ch = make_channel()
        del ch["posting_slots"]
        self.assertTrue(has_error(validate_channel(ch), "posting_slots"))

    def test_legacy_posting_slots_wib(self):
        """posting_slots_wib (no timezone) still validates and means Asia/Jakarta."""
        from validate_episode import posting_slots
        ch = make_channel(posting_slots_wib=["05:30", "16:00"])
        del ch["posting_slots"], ch["timezone"]
        self.assertEqual(validate_channel(ch), [])
        self.assertEqual(posting_slots(ch), ("posting_slots_wib", ["05:30", "16:00"], "Asia/Jakarta"))
        self.assertTrue(has_error(validate_channel(dict(ch, posting_slots_wib=["25:00"])), "posting_slots_wib"))
        self.assertTrue(has_error(validate_channel(dict(ch, posting_slots_wib=[])), "posting_slots_wib"))
        self.assertEqual(validate_channel(dict(ch, timezone="Asia/Jakarta")), [])
        self.assertTrue(has_error(validate_channel(dict(ch, timezone="UTC")), "timezone"))
        self.assertTrue(has_error(validate_channel(make_channel(posting_slots_wib=["06:00"])), "posting_slots_wib"))

    def test_channel_videos_per_day_min(self):
        self.assertTrue(has_error(validate_channel(make_channel(videos_per_day=0)), "videos_per_day"))
        self.assertTrue(has_error(validate_channel(make_channel(videos_per_day=True)), "videos_per_day"))

    def test_channel_bad_id_and_date(self):
        self.assertTrue(has_error(validate_channel(make_channel(id="Deep Earth")), "id"))
        self.assertTrue(has_error(validate_channel(make_channel(started_on="9-11-2026")), "started_on"))

    def test_channel_missing_voice_or_style(self):
        self.assertTrue(has_error(validate_channel(make_channel(voice={"provider": "x"})), "voice"))
        self.assertTrue(has_error(validate_channel(make_channel(style_bible="")), "style_bible"))

    def test_channel_missing_field(self):
        ch = make_channel()
        del ch["niche"]
        self.assertIn("niche: missing", validate_channel(ch))

    def test_channel_not_object(self):
        self.assertTrue(validate_channel("x"))


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(argv)
    return code, out.getvalue()


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add_channel(self, cid, **overrides):
        d = self.root / cid / "episodes"
        d.mkdir(parents=True)
        (self.root / cid / "channel.json").write_text(json.dumps(make_channel(id=cid, **overrides)))
        return d

    def add_episode(self, cid, eid, **changes):
        ep = make_valid()
        ep.update(id=eid, channel=cid, **changes)
        path = self.root / cid / "episodes" / f"{eid}.json"
        path.write_text(json.dumps(ep))
        return path

    def test_cli_ok_exit0(self):
        self.add_channel("deep-earth")
        code, out = run(["validate", str(self.add_episode("deep-earth", "ep-1"))])
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_cli_errors_exit1(self):
        self.add_channel("deep-earth")
        code, out = run(["validate", str(self.add_episode("deep-earth", "ep-1", title="x" * 61))])
        self.assertEqual(code, 1)
        self.assertIn("title", out)

    def test_cli_bad_json_exit2(self):
        bad = self.root / "bad.json"
        bad.write_text("{not json")
        code, out = run(["validate", str(bad)])
        self.assertEqual(code, 2)
        self.assertIn("error:", out)
        self.assertNotIn("Traceback", out)

    def test_cli_missing_file_exit2(self):
        code, out = run(["validate", str(self.root / "nope.json")])
        self.assertEqual(code, 2)
        self.assertIn("error:", out)

    def test_cli_validate_missing_channel_profile(self):
        d = self.root / "ghost" / "episodes"
        d.mkdir(parents=True)
        ep = make_valid()
        ep["channel"] = "ghost"
        path = d / "ep-1.json"
        path.write_text(json.dumps(ep))
        code, out = run(["validate", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("channel:", out)

    def test_cli_validate_channel_id_mismatch(self):
        self.add_channel("deep-earth")
        path = self.add_episode("deep-earth", "ep-1")
        data = json.loads(path.read_text())
        data["channel"] = "other"
        path.write_text(json.dumps(data))
        code, out = run(["validate", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("channel:", out)

    def test_cli_validate_with_explicit_channel_flag(self):
        flat = self.root / "flat"
        flat.mkdir()
        (flat / "profile.json").write_text(json.dumps(make_channel()))
        ep = flat / "ep-1.json"
        ep.write_text(json.dumps(make_valid()))
        code, out = run(["validate", str(ep), "--channel", str(flat / "profile.json")])
        self.assertEqual(code, 0, out)

    def test_cli_validate_finds_sibling_channel_json(self):
        flat = self.root / "flat"
        flat.mkdir()
        (flat / "channel.json").write_text(json.dumps(make_channel()))
        ep = flat / "ep-1.json"
        ep.write_text(json.dumps(make_valid()))
        code, out = run(["validate", str(ep)])
        self.assertEqual(code, 0, out)

    def test_cli_validate_channel_command(self):
        self.add_channel("deep-earth")
        self.assertEqual(run(["validate-channel", str(self.root / "deep-earth" / "channel.json")])[0], 0)
        self.add_channel("broken", status="live")
        self.assertEqual(run(["validate-channel", str(self.root / "broken" / "channel.json")])[0], 1)

    def test_cli_log_lists_status(self):
        self.add_channel("deep-earth")
        self.add_episode("deep-earth", "ep-1", status="published", title="Hidden Ocean")
        code, out = run(["log", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("deep-earth", out)
        self.assertIn("published", out)
        self.assertIn("Hidden Ocean", out)

    def test_cli_log_filter_channel(self):
        self.add_channel("a")
        self.add_channel("b")
        self.add_episode("a", "ep-a1", title="Alpha title")
        self.add_episode("b", "ep-b1", title="Beta title")
        code, out = run(["log", str(self.root), "--channel", "a"])
        self.assertEqual(code, 0)
        self.assertIn("Alpha title", out)
        self.assertNotIn("Beta title", out)

    def test_cli_log_skips_broken_episode(self):
        self.add_channel("a")
        (self.root / "a" / "episodes" / "bad.json").write_text("{oops")
        code, out = run(["log", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("bad.json", out)

    def test_capacity_skips_paused(self):
        self.add_channel("a", status="active", videos_per_day=1)
        self.add_channel("b", status="testing", videos_per_day=2)
        self.add_channel("c", status="paused", videos_per_day=3)
        cap = capacity(self.root)
        self.assertEqual(cap["videos_per_day"], 3)
        self.assertEqual(cap["minutes_per_day"], 225)
        self.assertEqual(sorted(cap["channels"]), ["a", "b"])
        code, out = run(["capacity", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("225", out)


if __name__ == "__main__":
    unittest.main()
