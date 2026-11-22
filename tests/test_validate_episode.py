import unittest

from helpers import make_script, make_shots, make_valid

from validate_episode import count_words, est_seconds, validate, warnings


def has_error(errors, field):
    return any(e.startswith(field) for e in errors)


class TestCore(unittest.TestCase):
    def test_valid_episode_has_no_errors(self):
        self.assertEqual(validate(make_valid()), [])

    def test_count_words_tokens(self):
        self.assertEqual(count_words("Don't miss this 3D well-known fact."), 6)

    def test_est_seconds(self):
        self.assertEqual(est_seconds(150), 60.0)

    def test_script_too_short(self):
        ep = make_valid()
        ep["script"] = make_script(74)
        self.assertTrue(has_error(validate(ep), "script"))

    def test_script_too_long(self):
        ep = make_valid()
        ep["script"] = make_script(151)
        self.assertTrue(has_error(validate(ep), "script"))

    def test_script_bounds_inclusive(self):
        for n in (75, 150):
            ep = make_valid()
            ep["script"] = make_script(n)
            self.assertFalse(has_error(validate(ep), "script"), n)

    def test_hook_too_long(self):
        ep = make_valid()
        ep["hook"] = "one two three four five six seven eight nine ten eleven"
        ep["script"] = ep["hook"] + ". " + ep["script"]
        self.assertTrue(has_error(validate(ep), "hook"))

    def test_hook_not_opening(self):
        ep = make_valid()
        ep["hook"] = "Something completely different."
        self.assertTrue(has_error(validate(ep), "hook"))

    def test_hook_match_ignores_case_and_trailing_punctuation(self):
        ep = make_valid()
        ep["hook"] = "THIS OCEAN HIDES A SECOND OCEAN!"
        self.assertFalse(has_error(validate(ep), "hook"))

    def test_hook_must_match_whole_words(self):
        ep = make_valid()
        ep["hook"] = "This ocean hides a second oce"
        self.assertTrue(has_error(validate(ep), "hook"))

    def test_missing_field_reported_not_crash(self):
        ep = make_valid()
        del ep["shots"]
        self.assertIn("shots: missing", validate(ep))

    def test_missing_channel_reported(self):
        ep = make_valid()
        del ep["channel"]
        self.assertIn("channel: missing", validate(ep))

    def test_wrong_type_reported(self):
        ep = make_valid()
        ep["shots"] = "x"
        self.assertTrue(has_error(validate(ep), "shots"))

    def test_script_wrong_type_reported(self):
        ep = make_valid()
        ep["script"] = 42
        self.assertTrue(has_error(validate(ep), "script"))

    def test_bad_status(self):
        ep = make_valid()
        ep["status"] = "done"
        self.assertTrue(has_error(validate(ep), "status"))

    def test_non_dict_episode(self):
        self.assertTrue(validate([]))


class TestShots(unittest.TestCase):
    def _errors(self, shots):
        ep = make_valid()
        ep["shots"] = shots
        return validate(ep)

    def test_shots_must_start_at_zero(self):
        shots = make_shots()
        shots[0]["t_start"] = 1
        self.assertTrue(has_error(self._errors(shots), "shots: must start at 0"))

    def test_shot_gap(self):
        shots = make_shots()
        shots[2]["t_start"] = 17
        self.assertTrue(has_error(self._errors(shots), "shots: gap"))

    def test_shot_overlap(self):
        shots = make_shots()
        shots[2]["t_start"] = 15
        self.assertTrue(has_error(self._errors(shots), "shots: overlap"))

    def test_unsorted_shots_are_accepted(self):
        shots = make_shots()
        shots.reverse()
        self.assertEqual(self._errors(shots), [])

    def test_zero_length_shot(self):
        shots = make_shots(ends=(8, 8, 16, 24, 32, 40))
        self.assertTrue(has_error(self._errors(shots), "shots"))

    def test_shots_cover_duration(self):
        # script of 100 words lasts 40s; shots end at 32s
        shots = make_shots(ends=(8, 16, 24, 32))
        self.assertTrue(has_error(self._errors(shots), "shots: cover"))

    def test_stock_shots_ok(self):
        self.assertEqual(self._errors(make_shots(shot_type="stock")), [])

    def test_legacy_flow_shot_rejected_in_new_package(self):
        for legacy in ("veo", "flow_image"):
            shots = make_shots()
            shots[0]["type"] = legacy
            errors = self._errors(shots)
            self.assertTrue(has_error(errors, "shots[0]: " + legacy), (legacy, errors))
            self.assertTrue(any("legacy Google Flow" in e for e in errors), errors)

    def test_bad_shot_type(self):
        shots = make_shots()
        shots[1]["type"] = "photo"
        self.assertTrue(has_error(self._errors(shots), "shots[1]"))

    def test_empty_prompt(self):
        shots = make_shots()
        shots[1]["prompt"] = "  "
        self.assertTrue(has_error(self._errors(shots), "shots[1]"))

    def test_empty_shot_list(self):
        self.assertTrue(has_error(self._errors([]), "shots"))

    def test_shot_not_object_or_bad_times(self):
        self.assertTrue(has_error(self._errors(["x"]), "shots[0]"))
        shots = make_shots()
        shots[0]["t_end"] = "8"
        self.assertTrue(has_error(self._errors(shots), "shots[0]"))


class TestLegacyFlowPackages(unittest.TestCase):
    """Google Flow / Veo is gone; already-published packages must keep validating."""

    def test_legacy_credit_estimate_is_not_an_error(self):
        ep = make_valid()
        ep["credit_estimate"] = 120
        self.assertEqual(validate(ep), [])
        self.assertIn("credit_estimate: legacy Flow field, ignored", warnings(ep))

    def test_published_veo_shot_is_only_a_warning(self):
        ep = make_valid()
        ep["status"] = "published"
        ep["shots"][0]["type"] = "veo"
        ep["shots"][1]["type"] = "flow_image"
        self.assertEqual(validate(ep), [])
        notes = warnings(ep)
        self.assertIn("shots[0]: legacy veo shot; Flow no longer used", notes)
        self.assertIn("shots[1]: legacy flow_image shot; Flow no longer used", notes)

    def test_clean_package_has_no_warnings(self):
        self.assertEqual(warnings(make_valid()), [])

    def test_unknown_type_still_rejected_when_published(self):
        ep = make_valid()
        ep["status"] = "published"
        ep["shots"][0]["type"] = "photo"
        self.assertTrue(any("type must be one of" in e for e in validate(ep)))


if __name__ == "__main__":
    unittest.main()


class TestNonFiniteTimes(unittest.TestCase):
    def test_nan_and_infinity_rejected(self):
        for bad in (float("nan"), float("inf")):
            ep = make_valid()
            ep["shots"][1]["t_start"] = bad
            self.assertTrue(has_error(validate(ep), "shots[1]"), bad)
            ep = make_valid()
            ep["shots"][-1]["t_end"] = bad
            self.assertTrue(has_error(validate(ep), "shots[4]"), bad)
