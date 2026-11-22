"""Regression tests for the minors deferred from the final review."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import ROOT, SKILL_DIR, make_channel, make_valid

from validate_episode import capacity, main, validate, validate_channel

sys.path.insert(0, str(ROOT / "tools"))
import build_dist  # noqa: E402


def run(fn, argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(argv)
    return code, out.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add_channel(self, cid, **overrides):
        (self.root / cid / "episodes").mkdir(parents=True)
        path = self.root / cid / "channel.json"
        path.write_text(json.dumps(make_channel(id=cid, **overrides)))
        return path


class TestChannelProfileErrors(Tmp):
    # 6: a broken channel.json must not be reported as "no profile found"
    def test_broken_profile_reports_invalid_json(self):
        self.add_channel("deep-earth").write_text("{oops")
        ep = self.root / "deep-earth" / "episodes" / "ep-1.json"
        ep.write_text(json.dumps(make_valid()))
        code, out = run(main, ["validate", str(ep)])
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", out)
        self.assertNotIn("no profile found", out)


class TestCapacityReporting(Tmp):
    # 7: invalid profiles are reported, not silently skipped
    def test_invalid_profile_is_listed_as_skipped(self):
        self.add_channel("good")
        self.add_channel("bad", status="live")
        cap = capacity(self.root)
        self.assertEqual(cap["channels"], ["good"])
        self.assertEqual(len(cap["skipped"]), 1)
        self.assertIn("bad", cap["skipped"][0])
        code, out = run(main, ["capacity", str(self.root)])
        self.assertIn("skipped", out)
        self.assertIn("bad", out)

    # Flow removed: capacity counts videos against posting slots, not Flow credits
    def test_videos_vs_posting_slots(self):
        self.add_channel("a", videos_per_day=2, posting_slots=["01:00", "06:00"])
        self.add_channel("b", videos_per_day=3, posting_slots=["12:00"])
        cap = capacity(self.root)
        self.assertEqual(cap["videos_per_day"], 5)
        self.assertEqual(cap["slots_per_day"], 3)
        self.assertEqual(cap["minutes_per_day"], 5 * 75)
        self.assertEqual(cap["per_channel"]["a"], {"videos_per_day": 2, "slots": 2})
        self.assertEqual(cap["over_slots"], ["b"])
        self.assertNotIn("credits_per_day", cap)

    def test_capacity_counts_legacy_wib_slots(self):
        path = self.add_channel("w", videos_per_day=1, posting_slots_wib=["06:00", "18:00"])
        ch = json.loads(path.read_text())
        del ch["posting_slots"], ch["timezone"]
        path.write_text(json.dumps(ch))
        cap = capacity(self.root)
        self.assertEqual(cap["per_channel"]["w"], {"videos_per_day": 1, "slots": 2})

    def test_capacity_cli_marks_over_and_fits(self):
        self.add_channel("a", videos_per_day=1)
        self.add_channel("b", videos_per_day=2)
        code, out = run(main, ["capacity", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("a: 1 video(s)/day, 1 slot(s): fits", out)
        self.assertIn("b: 2 video(s)/day, 1 slot(s): OVER", out)
        self.assertNotIn("credit", out.lower())

    def test_monthly_credits_option_removed(self):
        with self.assertRaises(SystemExit):
            run(main, ["capacity", str(self.root), "--monthly-credits", "1000"])

    def test_legacy_credits_per_video_is_only_a_warning(self):
        for legacy in (-1, True, "100", 0, 120):
            self.assertEqual(validate_channel(make_channel(credits_per_video=legacy)), [], legacy)
        path = self.add_channel("a", credits_per_video=120)
        code, out = run(main, ["validate-channel", str(path)])
        self.assertEqual(code, 0)
        self.assertIn("warning: credits_per_video: legacy Flow field", out)
        self.assertIn("OK", out)
        cap = capacity(self.root)
        self.assertEqual(cap["channels"], ["a"])


class TestRulesDrift(unittest.TestCase):
    # 12: validator matches rules.md
    def test_started_on_needs_dashes(self):
        errors = validate_channel(make_channel(started_on="20261109"))
        self.assertTrue(any(e.startswith("started_on") for e in errors))

    def test_hashtag_rejects_punctuation(self):
        ep = make_valid()
        ep["hashtags"] = ["#shorts", "#space!", "#ocean"]
        self.assertTrue(any(e.startswith("hashtags") for e in validate(ep)))
        ep["hashtags"] = ["#shorts", "#space_facts", "#océan"]
        self.assertEqual(validate(ep), [])

    def test_shot_length_2_to_8_seconds(self):
        for ends in ((9, 16, 24, 32, 40), (1.5, 8, 16, 24, 32, 40)):
            ep = make_valid()
            ep["shots"][:] = []
            start = 0
            for end in ends:
                ep["shots"].append({"t_start": start, "t_end": end, "type": "diagram", "prompt": "x"})
                start = end
            self.assertTrue(any("2-8" in e for e in validate(ep)), ends)

    def test_rules_md_documents_new_rules(self):
        rules = (SKILL_DIR / "references" / "rules.md").read_text(encoding="utf-8")
        for needle in ("2–8 seconds", "Posting slots", "`veo` / `flow_image`", "letters, digits or `_`"):
            self.assertIn(needle, rules)


class TestEncoding(Tmp):
    # 16: BOM accepted, non-UTF-8 named in the error
    def test_utf8_bom_episode_is_accepted(self):
        self.add_channel("deep-earth")
        ep = self.root / "deep-earth" / "episodes" / "ep-1.json"
        ep.write_bytes(b"\xef\xbb\xbf" + json.dumps(make_valid()).encode())
        code, out = run(main, ["validate", str(ep)])
        self.assertEqual(code, 0, out)

    def test_non_utf8_error_names_the_file(self):
        ep = self.root / "latin.json"
        ep.write_bytes('{"title": "caf\xe9"}'.encode("latin-1"))
        code, out = run(main, ["validate", str(ep)])
        self.assertEqual(code, 2)
        self.assertIn("latin.json", out)
        self.assertIn("UTF-8", out)


class TestBuildDistMinors(Tmp):
    def copy_skill(self):
        src = self.root / "src" / "akra"
        shutil.copytree(SKILL_DIR, src)
        return src

    # 8: symlinked subfolders are packaged
    def test_symlinked_folder_is_zipped(self):
        src = self.copy_skill()
        extra = self.root / "extra"
        extra.mkdir()
        (extra / "note.md").write_text("hi")
        os.symlink(extra, src / "extra")
        paths = build_dist.build(src, self.root / "dist")
        names = zipfile.ZipFile(paths["claude-ai"]).namelist()
        self.assertIn("akra/extra/note.md", names)

    # 9: --src . still names the zip after the folder
    def test_src_dot_names_zip_after_folder(self):
        src = self.copy_skill()
        cwd = os.getcwd()
        os.chdir(src)
        try:
            paths = build_dist.build(Path("."), self.root / "dist")
        finally:
            os.chdir(cwd)
        self.assertEqual(paths["claude-ai"].name, "akra.zip")

    # 10: file-system errors end in a message, not a traceback
    def test_oserror_is_reported(self):
        blocker = self.root / "dist"
        blocker.write_text("i am a file")
        code, out = run(build_dist.main, ["--out", str(blocker)])
        self.assertEqual(code, 1)
        self.assertIn("error:", out)

    # 11: CRLF frontmatter is stripped
    def test_crlf_frontmatter_stripped(self):
        text = "---\r\nname: x\r\ndescription: y\r\n---\r\n\r\n# Body\r\n"
        self.assertEqual(build_dist._strip_frontmatter(text), "# Body\r\n")


if __name__ == "__main__":
    unittest.main()
