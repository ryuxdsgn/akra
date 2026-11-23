"""YouTube policy gate and style-bible gate (references/youtube-policy.md)."""
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from helpers import SKILL_DIR, make_channel, make_policy_check, make_valid

import validate_episode as ve
from validate_episode import (POLICY_IDS, PRE_UPLOAD_IDS, is_legacy, policy_gate, previous_episodes,
                              validate, validate_channel, warnings)

POLICY_MD = SKILL_DIR / "references" / "youtube-policy.md"


def has(errors, text):
    return any(text in e for e in errors)


def edited(**kw):
    """An `edited` package with a full policy_check (ready for upload)."""
    ep = make_valid()
    ep["status"] = "edited"
    ep["policy_check"] = make_policy_check()
    ep.update(kw)
    return ep


def approved_channel(**kw):
    return make_channel(style_approved_on="2026-11-20", **kw)


class TestNewFields(unittest.TestCase):
    def test_valid_fixture_passes(self):
        self.assertEqual(validate(make_valid()), [])
        self.assertEqual(validate(edited(), profile=approved_channel()), [])

    def test_made_for_kids_required_bool(self):
        for bad in (None, "no", 0):
            ep = make_valid()
            if bad is None:
                del ep["made_for_kids"]
            else:
                ep["made_for_kids"] = bad
            self.assertTrue(has(validate(ep), "made_for_kids"), bad)
        ep = make_valid()
        ep["made_for_kids"] = True
        self.assertEqual(validate(ep), [])

    def test_synthetic_content_required_bool(self):
        ep = make_valid()
        del ep["synthetic_content"]
        self.assertTrue(has(validate(ep), "synthetic_content"))
        ep["synthetic_content"] = "yes"
        self.assertTrue(has(validate(ep), "synthetic_content"))

    def test_synthetic_needs_ai_disclosure(self):
        ep = make_valid()
        ep.update(synthetic_content=True, ai_disclosure=False)
        self.assertTrue(has(validate(ep), "YT-SYN-2"))
        ep["ai_disclosure"] = True
        self.assertEqual(validate(ep), [])

    def test_variation_shape(self):
        for bad in (None, "x", {"story": "a", "setting": "b"}, {"story": "a", "setting": " ", "props": "c"}):
            ep = make_valid()
            if bad is None:
                del ep["variation"]
            else:
                ep["variation"] = bad
            self.assertTrue(has(validate(ep), "variation"), bad)

    def test_sources(self):
        ep = make_valid()
        del ep["sources"]
        self.assertTrue(has(validate(ep), "sources"))
        ep["sources"] = ["NASA, some page"]                        # legacy string form
        self.assertTrue(has(validate(ep), "sources[0]"))
        ep["sources"] = [{"claim": "x", "url": "nasa.gov"}]          # no scheme
        self.assertTrue(has(validate(ep), "sources[0]"))
        ep["sources"] = []
        self.assertTrue(has(validate(ep), "no_factual_claims"))
        ep["no_factual_claims"] = True
        self.assertEqual(validate(ep), [])

    def test_music_credit(self):
        ep = make_valid()
        ep["description"] = "Scientists found water deep under the Pacific."
        self.assertTrue(has(validate(ep), "YT-CRED-1"))
        ep["music_source"] = "none"
        self.assertEqual(validate(ep), [])
        ep["music_source"] = "licensed"
        ep["music_credit"] = "Track X by Artist Y (licensed)"
        self.assertTrue(has(validate(ep), "music_credit"))
        ep["description"] += " Track X by Artist Y (licensed)"
        self.assertEqual(validate(ep), [])

    def test_music_credit_language_label(self):
        ep = make_valid()
        ep["description"] = "Air tersimpan di dalam mineral.\nMusik: \"Pulsar\" (YouTube Audio Library)."
        self.assertEqual(ve._check_music_credit(ep, "id"), [])
        self.assertTrue(ve._check_music_credit(ep, "en"))           # en wants "Music:"


class TestPolicyCheck(unittest.TestCase):
    def test_required_from_edited(self):
        ep = edited()
        del ep["policy_check"]
        errs = validate(ep, profile=approved_channel())
        self.assertTrue(has(errs, "policy_check: missing"))
        self.assertTrue(has(errs, "YT-UP-1"))

    def test_not_required_while_scripted(self):
        ep = make_valid()
        self.assertNotIn("policy_check", ep)
        self.assertEqual(validate(ep), [])
        ep["policy_check"] = {"checked_on": "2026-11-22", "items": {"YT-AUTH-1": "pass"}}   # partial is fine
        self.assertEqual(validate(ep), [])

    def test_upload_always_requires_it(self):
        errs = validate(make_valid(), for_upload=True)
        self.assertTrue(has(errs, "policy_check: missing"))

    def test_item_not_pass(self):
        ep = edited(policy_check=make_policy_check(YT_TAG_1="fail"))
        errs = validate(ep, profile=approved_channel())
        self.assertTrue(has(errs, "not pass: YT-TAG-1"))
        self.assertEqual(ve.missing_policy_items(ep), ["YT-TAG-1"])

    def test_bad_date_and_unknown_id(self):
        pc = make_policy_check()
        pc["checked_on"] = "22-11-2026"
        pc["items"]["YT-NOPE-9"] = "pass"
        errs = validate(edited(policy_check=pc), profile=approved_channel())
        self.assertTrue(has(errs, "checked_on"))
        self.assertTrue(has(errs, "YT-NOPE-9"))

    def test_shape(self):
        errs = validate(edited(policy_check=["YT-AUTH-1"]), profile=approved_channel())
        self.assertTrue(has(errs, "policy_check: must be"))


class TestPolicyIdsMatchReference(unittest.TestCase):
    def setUp(self):
        self.text = POLICY_MD.read_text(encoding="utf-8")

    def test_every_defined_id_known(self):
        defined = re.findall(r"^- \*\*(YT-[A-Z]+-\d+)\*\*", self.text, re.M)
        self.assertEqual(len(defined), len(set(defined)))
        self.assertEqual(tuple(defined), POLICY_IDS)

    def test_pre_upload_line_matches_validator(self):
        line = re.search(r"^Pre-upload ids: (.+)$", self.text, re.M).group(1)
        self.assertEqual(tuple(i.strip() for i in line.split(",")), PRE_UPLOAD_IDS)

    def test_pre_upload_ids_are_the_episode_steps(self):
        steps = re.split(r"^## ", self.text, flags=re.M)
        ep_ids = []
        for sec in steps:
            if sec.split("\n", 1)[0].startswith(("ideas", "build", "package", "pre-upload")):
                ep_ids += re.findall(r"^- \*\*(YT-[A-Z]+-\d+)\*\*", sec, re.M)
        self.assertEqual(tuple(ep_ids), PRE_UPLOAD_IDS)

    def test_impact_tags_match_validator(self):
        tags = dict(re.findall(r"^- \*\*(YT-[A-Z]+-\d+)\*\* \[([^\]]+)\]", self.text, re.M))
        self.assertEqual(tags, ve.IMPACT)
        self.assertLessEqual(set(tags.values()), {ve.BLOCKS, ve.LIMITS, ve.STRIKE, "process"})
        self.assertIn("eligible for monetization", self.text)

    def test_every_item_has_source_and_date(self):
        for line in self.text.splitlines():
            if line.startswith("- **YT-"):
                self.assertRegex(line, r"https://support\.google\.com/youtube/answer/\d+", line[:20])
                self.assertIn("(checked 2026-11-22)", line, line[:20])


class TestMonetizationLine(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(ve.monetization_line(edited(), []), "Monetization: OK")

    def test_legacy_published_is_not_checked(self):
        ep = {k: v for k, v in edited().items() if k != "policy_check"}
        ep["status"] = "published"
        self.assertEqual(ve.monetization_line(ep, ["x (YT-AUTH-1)"]),
                         "Monetization: not checked (made before the policy gate)")

    def test_pending_before_package(self):
        self.assertIn("pending", ve.monetization_line(make_valid(), []))

    def test_at_risk_lists_ids_with_impact(self):
        ep = edited(policy_check=make_policy_check(YT_AD_1="fail"))
        line = ve.monetization_line(ep, ["variation: same story as ep-001 (YT-AUTH-2)"])
        self.assertEqual(line, "Monetization: at risk: YT-AUTH-2 [blocks monetization], YT-AD-1 [limits ads]")

    def test_items_of_later_steps_are_pending(self):
        pc = make_policy_check()
        for i in ("YT-COPY-1", "YT-TAG-1", "YT-CRED-1", "YT-UP-1"):
            del pc["items"][i]
        ep = dict(make_valid(), status="scripted", policy_check=pc)
        self.assertEqual(ve.monetization_line(ep, []),
                         "Monetization: OK so far (pending: YT-COPY-1 at build; YT-TAG-1, YT-CRED-1 at package; "
                         "YT-UP-1 at pre-upload)")
        ep["status"] = "visuals"                       # build reached: its open item is now at risk
        self.assertEqual(ve.monetization_line(ep, []),
                         "Monetization: at risk: YT-COPY-1 [strike/removal risk] "
                         "(pending: YT-TAG-1, YT-CRED-1 at package; YT-UP-1 at pre-upload)")

    def test_reached_step_failure_is_at_risk(self):
        pc = make_policy_check(YT_FACT_1="fail")
        del pc["items"]["YT-META-1"]
        ep = dict(make_valid(), status="scripted", policy_check=pc)
        self.assertEqual(ve.monetization_line(ep, []),
                         "Monetization: at risk: YT-FACT-1 [strike/removal risk] (pending: YT-META-1 at package)")

    def test_step_reached_by_status(self):
        ep = dict(make_valid(), status="idea")
        self.assertFalse(ve.step_reached(ep, "YT-AUTH-1"))
        self.assertTrue(ve.step_reached(dict(ep, status="scripted"), "YT-AUTH-1"))
        self.assertFalse(ve.step_reached(dict(ep, status="scripted"), "YT-COPY-1"))
        self.assertTrue(ve.step_reached(dict(ep, status="edited"), "YT-UP-1"))
        self.assertTrue(ve.step_reached(dict(ep, status="idea"), "YT-CH-1"))        # channel items: always
        self.assertEqual(set(ve.STEP_OF), set(ve.PRE_UPLOAD_IDS))

    def test_cli_prints_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            eps = Path(tmp) / "channels" / "deep-earth" / "episodes"
            eps.mkdir(parents=True)
            (eps.parent / "channel.json").write_text(json.dumps(approved_channel()))
            (eps / "ep-001.json").write_text(json.dumps(edited()))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = ve.main(["validate", str(eps / "ep-001.json")])
            self.assertEqual(code, 0, out.getvalue())
            self.assertTrue(out.getvalue().rstrip().endswith("Monetization: OK"))
            bad = edited(policy_check=make_policy_check(YT_TAG_1="fail"))
            (eps / "ep-001.json").write_text(json.dumps(bad))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = ve.main(["validate", str(eps / "ep-001.json")])
            self.assertEqual(code, 1)
            self.assertIn("Monetization: at risk: YT-TAG-1 [strike/removal risk]", out.getvalue())


class TestVariation(unittest.TestCase):
    def prev(self, n, **var):
        ep = make_valid()
        ep["id"] = f"ep-{n:03d}"
        ep["variation"] = {"story": f"story {n}", "setting": f"setting {n}", "props": f"props {n}", **var}
        return ep

    def test_same_story_is_error(self):
        ep = make_valid()
        ep["id"] = "ep-010"
        p = self.prev(9, story=ep["variation"]["story"].upper())     # case/space-insensitive
        self.assertTrue(has(validate(ep, previous=[p]), "same story as ep-009"))

    def test_same_setting_and_props_is_error(self):
        ep = make_valid()
        ep["id"] = "ep-010"
        p = self.prev(9, setting=ep["variation"]["setting"], props=ep["variation"]["props"])
        self.assertTrue(has(validate(ep, previous=[p]), "same setting and props as ep-009"))

    def test_same_setting_only_is_fine(self):
        ep = make_valid()
        ep["id"] = "ep-010"
        p = self.prev(9, setting=ep["variation"]["setting"])
        self.assertEqual(validate(ep, previous=[p]), [])

    def test_window_is_last_three_by_id(self):
        ep = make_valid()
        ep["id"] = "ep-010"
        same = self.prev(6, story=ep["variation"]["story"])
        others = [same, self.prev(7), self.prev(8), self.prev(9), self.prev(11, story=ep["variation"]["story"])]
        window = previous_episodes(ep, others)
        self.assertEqual([o["id"] for o in window], ["ep-007", "ep-008", "ep-009"])
        self.assertEqual(validate(ep, previous=window), [])
        other_channel = self.prev(9, story=ep["variation"]["story"])
        other_channel["channel"] = "elsewhere"
        self.assertEqual(previous_episodes(ep, [other_channel]), [])

    def test_cli_reads_sibling_episodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            eps = Path(tmp) / "channels" / "deep-earth" / "episodes"
            eps.mkdir(parents=True)
            (eps.parent / "channel.json").write_text(json.dumps(approved_channel()))
            a, b = make_valid(), make_valid()
            a["id"], b["id"] = "ep-001", "ep-002"
            a["topic"] = "How a pin-tumbler door lock opens"  # a different subject; only the variation repeats
            (eps / "ep-001.json").write_text(json.dumps(a))
            (eps / "ep-002.json").write_text(json.dumps(b))
            errors, _, _ = ve.validate_file(eps / "ep-002.json")
            self.assertTrue(has(errors, "same story as ep-001"))
            errors, _, _ = ve.validate_file(eps / "ep-001.json")
            self.assertEqual(errors, [])


class TestHealthChannel(unittest.TestCase):
    def health(self, **kw):
        return approved_channel(sensitive_topic="health", **kw)

    def ep(self):
        ep = make_valid()
        ep["description"] += "\nNot medical advice: ask your doctor before you start."
        return ep

    def test_clean_episode_passes(self):
        self.assertEqual(validate(self.ep(), profile=self.health()), [])

    def test_requires_disclaimer(self):
        ep = make_valid()
        self.assertTrue(has(validate(ep, profile=self.health()), "disclaimer"))
        self.assertEqual(validate(ep, profile=approved_channel()), [])   # not a health channel

    def test_custom_disclaimer(self):
        prof = self.health(disclaimer="Info umum saja, bukan nasihat medis.")
        self.assertTrue(has(validate(self.ep(), profile=prof), "disclaimer"))
        ep = make_valid()
        ep["description"] += "\nInfo umum saja, bukan nasihat medis."
        self.assertEqual(validate(ep, profile=prof), [])

    def test_rejects_cure_words(self):
        for field in ("title", "description"):
            ep = self.ep()
            ep[field] += " This cures back pain"
            self.assertTrue(has(validate(ep, profile=self.health()), f"{field}: forbidden"), field)

    def test_cure_word_boundaries(self):
        ep = self.ep()
        ep["description"] += " Keep your data secure."
        self.assertEqual(validate(ep, profile=self.health()), [])

    def test_indonesian_word_and_script(self):
        ep = self.ep()
        ep["script"] = ep["script"][:-1] + " menyembuhkan."
        errs = ve._check_sensitive(ep, self.health(language="id"), "id")
        self.assertTrue(has(errs, "script: forbidden"))
        self.assertTrue(has(errs, "menyembuhkan"))

    def test_configurable_words(self):
        ep = self.ep()
        ep["title"] = "A miracle stretch"
        self.assertTrue(has(validate(ep, profile=self.health(forbidden_words=["miracle"])), "title: forbidden"))
        self.assertEqual(validate(ep, profile=self.health()), [])

    def test_finance_rules(self):
        prof = approved_channel(sensitive_topic="finance")
        ep = make_valid()
        ep["title"] = "Guaranteed returns in a week"
        errs = validate(ep, profile=prof)
        self.assertTrue(has(errs, "title: forbidden"))
        self.assertTrue(has(errs, "finance disclaimer"))

    def test_expert_persona_rejected(self):
        for persona in ("Dr. Sehat, your AI doctor", "Dokter Rina", "certified financial advisor"):
            self.assertTrue(has(validate_channel(self.health(persona=persona)), "YT-CH-2"), persona)
        self.assertEqual(validate_channel(self.health(persona="friendly neighbour who exercises")), [])
        self.assertEqual(validate_channel(make_channel(persona="Dr. Robot the inventor")), [])   # not sensitive

    def test_channel_field_types(self):
        self.assertTrue(has(validate_channel(make_channel(sensitive_topic="crypto")), "sensitive_topic"))
        self.assertEqual(validate_channel(make_channel(sensitive_topic=None)), [])
        self.assertTrue(has(validate_channel(make_channel(forbidden_words="cure")), "forbidden_words"))
        self.assertTrue(has(validate_channel(make_channel(made_for_kids="no")), "made_for_kids"))


class TestStyleGate(unittest.TestCase):
    def test_required_beyond_scripted(self):
        ep = make_valid()
        ep["status"] = "visuals"
        errs = validate(ep, profile=make_channel())
        self.assertTrue(has(errs, "style gate"))
        self.assertEqual(validate(ep, profile=approved_channel()), [])

    def test_not_required_while_scripted(self):
        self.assertEqual(validate(make_valid(), profile=make_channel()), [])

    def test_bad_date(self):
        self.assertTrue(has(validate_channel(make_channel(style_approved_on="soon")), "style_approved_on"))
        ep = make_valid()
        ep["status"] = "visuals"
        self.assertTrue(has(validate(ep, profile=make_channel(style_approved_on="soon")), "style gate"))

    def test_qa_render_names_gate(self):
        import qa_render
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "channels" / "ch"
            d.mkdir(parents=True)
            (d / "channel.json").write_text(json.dumps({"id": "ch"}))
            self.assertEqual(qa_render.style_gate(tmp, "ch"), (False, "style_approved_on missing"))
            (d / "channel.json").write_text(json.dumps({"id": "ch", "style_approved_on": "2026-11-20"}))
            self.assertEqual(qa_render.style_gate(tmp, "ch"), (True, "2026-11-20"))
            self.assertIsNone(qa_render.style_gate(tmp, "other")[0])


class TestLegacy(unittest.TestCase):
    def old(self, **kw):
        ep = make_valid()
        for k in ("made_for_kids", "synthetic_content", "variation", "sources"):
            del ep[k]
        ep.update(kw)
        return ep

    def test_published_gives_warnings_only(self):
        ep = self.old(status="published")
        self.assertTrue(is_legacy(ep))
        self.assertEqual(validate(ep, profile=make_channel()), [])
        notes = warnings(ep, profile=make_channel())
        self.assertTrue(has(notes, "legacy package, policy gate: made_for_kids"))
        self.assertTrue(has(notes, "style gate"))

    def test_dated_before_epoch_without_policy_check(self):
        ep = self.old(status="edited", scheduled_at="2026-11-21T18:00:00-05:00")
        self.assertTrue(is_legacy(ep))
        self.assertEqual(validate(ep), [])
        ep = self.old(status="edited", created_on="2026-11-21")
        self.assertTrue(is_legacy(ep))

    def test_epoch_day_and_later_are_strict(self):
        for when in ("2026-11-22", "2026-12-01"):
            ep = self.old(status="edited", created_on=when)
            self.assertFalse(is_legacy(ep), when)
            self.assertTrue(has(validate(ep), "made_for_kids"), when)

    def test_undated_is_strict(self):
        self.assertFalse(is_legacy(self.old()))
        self.assertTrue(validate(self.old()))

    def test_policy_check_opts_out_of_legacy(self):
        ep = self.old(status="edited", created_on="2026-11-01", policy_check=make_policy_check())
        self.assertFalse(is_legacy(ep))
        self.assertTrue(has(validate(ep), "made_for_kids"))

    def test_upload_ignores_legacy(self):
        errs, _ = policy_gate(self.old(status="published"), for_upload=True)
        self.assertTrue(has(errs, "made_for_kids"))

    def test_base_rules_still_errors_when_legacy(self):
        ep = self.old(status="published", hashtags=["#a"])
        self.assertTrue(has(validate(ep), "hashtags"))


class TestUploadRefusal(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SKILL_DIR / "scripts"))
        import youtube_upload
        self.yu = youtube_upload
        self.tmp = tempfile.TemporaryDirectory()
        self.eps = Path(self.tmp.name) / "channels" / "deep-earth" / "episodes"
        (self.eps / "ep-001-assets").mkdir(parents=True)
        (self.eps / "ep-001-assets" / "ep-001.mp4").write_bytes(b"x")
        (self.eps.parent / "channel.json").write_text(json.dumps(approved_channel()))

    def tearDown(self):
        self.tmp.cleanup()

    def run_upload(self, ep):
        path = self.eps / "ep-001.json"
        path.write_text(json.dumps(ep))
        args = SimpleNamespace(episode=str(path), file=None, privacy="private", schedule=False,
                               dry_run=True, force=False)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                self.yu.upload(args)
                code = 0
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue()

    def test_refuses_and_lists_missing_items(self):
        ep = edited(policy_check=make_policy_check(YT_UP_1="todo", YT_TAG_1="fail"))
        code, out = self.run_upload(ep)
        self.assertNotIn(code, (0, None))
        self.assertIn("refusing to upload", out)
        self.assertIn("YT-TAG-1, YT-UP-1", out)
        self.assertIn("Monetization: at risk:", out)

    def test_refuses_legacy_published_package(self):
        ep = make_valid()
        del ep["made_for_kids"]
        ep["status"] = "published"
        code, out = self.run_upload(ep)
        self.assertNotIn(code, (0, None))
        self.assertIn("made_for_kids", out)

    def test_passes_gate_and_sends_audience(self):
        ep = edited(made_for_kids=True, synthetic_content=True, ai_disclosure=True)
        code, out = self.run_upload(ep)
        self.assertIn(code, (0, None), out)
        self.assertIn('"selfDeclaredMadeForKids": true', out)
        self.assertIn('"containsSyntheticMedia": true', out)


if __name__ == "__main__":
    unittest.main()
