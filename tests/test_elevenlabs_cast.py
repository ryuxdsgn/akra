"""elevenlabs_tts.py cast mode: tagged lines, pauses, gaps (no network)."""
import sys
import unittest

from helpers import ROOT

sys.path.insert(0, str(ROOT / "skills" / "akra" / "scripts"))
import elevenlabs_tts as el  # noqa: E402

CAST = {"NARRATOR": {}, "HOST": {}, "GUEST": {}}


class TestCastLines(unittest.TestCase):
    def test_tags_pauses_and_default_speaker(self):
        out = el.cast_lines("Hello.\nHOST: Let's go!\n\nGUEST: Just one more?\n[pause 1.5]\nBack to the story.", CAST)
        self.assertEqual(out, [["NARRATOR", "Hello.", 0.0], ["HOST", "Let's go!", el.BEAT],
                               ["GUEST", "Just one more?", 1.5], ["NARRATOR", "Back to the story.", 0.0]])

    def test_unknown_speaker_fails(self):
        with self.assertRaises(SystemExit):
            el.cast_lines("STRANGER: Hello.", CAST)

    def test_colon_inside_a_line_is_not_a_tag(self):
        out = el.cast_lines("HOST: The trick: go slow.", CAST)
        self.assertEqual(out, [["HOST", "The trick: go slow.", 0.0]])

    def test_narrator_tag_is_the_default_speaker(self):
        cast = {"VOICE": {}, "HOST": {}}
        self.assertEqual(el.cast_lines("NARRATOR: Hello.\nHOST: Hi.", cast), [["VOICE", "Hello.", 0.0], ["HOST", "Hi.", 0.0]])

    def test_spelling_variant_of_a_cast_name(self):
        cast = {"COMMENTATOR": {}, "HOST": {}}
        self.assertEqual(el.cast_lines("COMENTATOR: Hello.", cast), [["COMMENTATOR", "Hello.", 0.0]])
        self.assertEqual(el.cast_lines("NARRATOR: Hi.", {"NARRATORS": {}, "HOST": {}})[0][0], "NARRATORS")
        with self.assertRaises(SystemExit):
            el.cast_lines("HOTS: Hi.", cast)          # short names need an exact match

    def test_pause_word_in_any_language(self):
        for line in ("[pause 1.5]", "[PAUSE 1.5]", "[pausa 1.5]", "  [Pause 2] "):
            out = el.cast_lines(f"One.\n{line}\nTwo.", CAST)
            self.assertEqual([round(p, 2) for _, _, p in out], [float(line.split()[1].rstrip("] ")), 0.0], line)
        out = el.cast_lines("One.\n[whispers] Two.", CAST)
        self.assertEqual(out[1][1], "[whispers] Two.")              # a tag without seconds is not a pause

    def test_gap_longer_at_speaker_change(self):
        self.assertGreater(el.line_gap("Go.", "HOST", "GUEST"), el.line_gap("Go.", "HOST", "HOST"))


if __name__ == "__main__":
    unittest.main()
