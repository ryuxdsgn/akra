"""Language-aware scripts and the optional multi-platform channel fields."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import SKILL_DIR, make_channel, make_valid

from validate_episode import LANGUAGES, est_seconds, main, validate, validate_channel

sys.path.insert(0, str(SKILL_DIR / "scripts"))
import youtube_upload  # noqa: E402


def has_error(errors, field):
    return any(e.startswith(field) for e in errors)


def id_script(n):
    hook = "Pernah lihat pelangi ganda?"
    body = ("cahaya matahari memantul dua kali di dalam tetes hujan yang jatuh " * 30).split()
    return hook, " ".join(hook.split() + body[: n - len(hook.split())]) + "."


class TestLanguageRules(unittest.TestCase):
    def test_default_language_is_english(self):
        self.assertEqual(validate(make_valid()), [])
        self.assertEqual(est_seconds(150), 60)

    def test_indonesian_uses_slower_speech_rate(self):
        wpm = LANGUAGES["id"]["wpm"]
        self.assertLess(wpm, LANGUAGES["en"]["wpm"])
        self.assertAlmostEqual(est_seconds(wpm, wpm), 60)

    def test_indonesian_word_bounds(self):
        rules = LANGUAGES["id"]
        for n, bad in ((rules["min_words"] - 1, True), (rules["min_words"], False),
                       (rules["max_words"], False), (rules["max_words"] + 1, True)):
            ep = make_valid()
            ep["hook"], ep["script"] = id_script(n)
            self.assertEqual(has_error(validate(ep, language="id"), "script"), bad, n)

    def test_episode_language_field_used_when_no_argument(self):
        ep = make_valid()
        ep["hook"], ep["script"] = id_script(LANGUAGES["id"]["max_words"])
        ep["language"] = "id"
        self.assertFalse(has_error(validate(ep), "script"))

    def test_unknown_language_reported(self):
        self.assertTrue(has_error(validate(make_valid(), language="xx"), "language"))

    def test_indonesian_title_limit_is_wider(self):
        ep = make_valid()
        ep["title"] = "x" * (LANGUAGES["en"]["max_title"] + 5)
        self.assertTrue(has_error(validate(ep), "title"))
        ep["hook"], ep["script"] = id_script(80)
        self.assertFalse(has_error(validate(ep, language="id"), "title"))


class TestChannelOptionalFields(unittest.TestCase):
    def test_new_fields_valid(self):
        ch = make_channel(language="id", platforms=["youtube", "facebook", "tiktok"],
                          youtube_category_id="17", youtube_account="deep-earth",
                          brand={"text": "DEEP EARTH", "font": "Baloo 2",
                                 "colors": {"bg": "#FFF3D6", "accent": "#FF7A59"}})
        self.assertEqual(validate_channel(ch), [])

    def test_bad_language(self):
        self.assertTrue(has_error(validate_channel(make_channel(language="indonesian")), "language"))

    def test_bad_platforms(self):
        self.assertTrue(has_error(validate_channel(make_channel(platforms=["myspace"])), "platforms"))
        self.assertTrue(has_error(validate_channel(make_channel(platforms=[])), "platforms"))

    def test_bad_category_and_account(self):
        self.assertTrue(has_error(validate_channel(make_channel(youtube_category_id=17)), "youtube_category_id"))
        self.assertTrue(has_error(validate_channel(make_channel(youtube_account="Bad Name")), "youtube_account"))

    def test_bad_brand(self):
        self.assertTrue(has_error(validate_channel(make_channel(brand="red")), "brand"))
        self.assertTrue(has_error(validate_channel(make_channel(brand={"colors": {"bg": "red"}})), "brand"))


class TestCliUsesChannelLanguage(unittest.TestCase):
    def test_validate_reads_language_from_profile(self):
        with tempfile.TemporaryDirectory() as d:
            ch_dir = Path(d) / "deep-earth"
            (ch_dir / "episodes").mkdir(parents=True)
            (ch_dir / "channel.json").write_text(json.dumps(make_channel(language="id")))
            ep = make_valid()
            ep["hook"], ep["script"] = id_script(70)    # <75 = too short in English, fine in Indonesian (~34 s)
            ep_path = ch_dir / "episodes" / "ep-001.json"
            ep_path.write_text(json.dumps(ep))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["validate", str(ep_path)]), 0)


class TestUploadUsesChannel(unittest.TestCase):
    def test_body_defaults_match_old_behaviour(self):
        body = youtube_upload.body_for(make_valid(), "private", False)
        self.assertEqual(body["snippet"]["categoryId"], "28")
        self.assertEqual(body["snippet"]["defaultLanguage"], "en")

    def test_body_uses_channel_language_and_category(self):
        ch = make_channel(language="id", youtube_category_id="17")
        body = youtube_upload.body_for(make_valid(), "private", False, ch)
        self.assertEqual(body["snippet"]["categoryId"], "17")
        self.assertEqual(body["snippet"]["defaultLanguage"], "id")
        self.assertEqual(body["snippet"]["defaultAudioLanguage"], "id")

    def test_token_name_per_account(self):
        self.assertEqual(youtube_upload.token_name({}), ".youtube-token.json")
        self.assertEqual(youtube_upload.token_name({"youtube_account": "deep-earth"}),
                         ".youtube-deep-earth-token.json")
        self.assertEqual(youtube_upload.token_name({"youtube_account": "deep-earth"}, "analytics"),
                         ".youtube-deep-earth-analytics-token.json")
        self.assertEqual(youtube_upload.token_name({}, "analytics"), ".youtube-analytics-token.json")

    def test_channel_for_episode(self):
        with tempfile.TemporaryDirectory() as d:
            ch_dir = Path(d) / "deep-earth"
            (ch_dir / "episodes").mkdir(parents=True)
            (ch_dir / "channel.json").write_text(json.dumps(make_channel(language="id")))
            ep_path = ch_dir / "episodes" / "ep-001.json"
            self.assertEqual(youtube_upload.channel_for(str(ep_path))["language"], "id")
            self.assertEqual(youtube_upload.channel_for(str(Path(d) / "nowhere" / "x.json")), {})


if __name__ == "__main__":
    unittest.main()
