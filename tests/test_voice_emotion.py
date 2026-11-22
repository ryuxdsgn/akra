"""Emotion map in TTS text: Kokoro line tags (pace + pause) and ElevenLabs audio tags (no network)."""
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

from helpers import ROOT

sys.path.insert(0, str(ROOT / "skills" / "akra" / "scripts"))
import elevenlabs_tts as el  # noqa: E402
import kokoro_tts as ko  # noqa: E402

CAST = {"NARRATOR": {}, "HOST": {}}


class KokoroEmotion(unittest.TestCase):
    def test_split_tag_at_line_start_only(self):
        self.assertEqual(ko.split_emotion("[tense] The pressure rises."), ("tense", "The pressure rises."))
        self.assertEqual(ko.split_emotion("The pressure rises."), (None, "The pressure rises."))
        self.assertEqual(ko.split_emotion("[really](+2) fast"), (None, "[really](+2) fast"))   # stress markup

    def test_params_known_compound_unknown(self):
        self.assertEqual(ko.emotion_params(None), (1.0, 0.0))
        self.assertEqual(ko.emotion_params("tense"), ko.EMOTIONS["tense"])
        self.assertEqual(ko.emotion_params("tense, quiet"), ko.EMOTIONS["tense"])
        self.assertEqual(ko.emotion_params("kagum"), ko.EMOTIONS["awe"])
        with redirect_stdout(StringIO()) as out:
            self.assertEqual(ko.emotion_params("grumpy"), (1.0, 0.0))
        self.assertIn("unknown emotion", out.getvalue())

    def test_emotions_shape_the_read(self):
        speed, pause = ko.EMOTIONS["awe"]
        self.assertLess(speed, 1.0)
        self.assertGreater(pause, 0.0)
        self.assertGreater(ko.EMOTIONS["excited"][0], 1.0)
        for m, p in ko.EMOTIONS.values():
            self.assertTrue(0.85 <= m <= 1.15 and 0.0 <= p <= 0.5)

    def test_tags_never_count_as_words(self):
        text = ko.prepare("[TENSE] The valve SNAPS shut.\n\n[awe] And then, silence.")
        self.assertEqual(ko.plain(text).split(), ["The", "valve", "snaps", "shut.", "And", "then,", "silence."])
        self.assertIn("[tense]", text)                 # caps tag lowered, not turned into stress markup
        self.assertIn("[snaps](+2)", text)


class FakePipe:
    def __init__(self):
        self.calls = []

    def __call__(self, text, voice, speed, split_pattern):
        self.calls.append((text, speed))
        return []


class KokoroSynthSpeed(unittest.TestCase):
    def test_line_speed_follows_tag(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy only in .venv-kokoro")
        pipe = FakePipe()
        try:
            ko.synth(pipe, "[excited] Go!\nPlain line.", "am_fenrir", 0.95)
        except ValueError:
            pass                                       # no audio from the fake pipe
        self.assertEqual(pipe.calls[0], ("Go!", 0.95 * ko.EMOTIONS["excited"][0]))
        self.assertEqual(pipe.calls[1], ("Plain line.", 0.95))


class ElevenTags(unittest.TestCase):
    def test_strip_tags(self):
        self.assertEqual(el.strip_tags("[teasing, warm] Just one? [laughs] Go."), "Just one? Go.")

    def test_supports_tags(self):
        self.assertTrue(el.supports_tags("eleven_v4"))
        self.assertTrue(el.supports_tags("eleven_v3"))
        self.assertFalse(el.supports_tags("eleven_multilingual_v2"))
        self.assertFalse(el.supports_tags(None))

    def test_alignment_skips_tags(self):
        text = "[whispers] It runs. [laughs softly] Yes."
        al = {"characters": list(text),
              "character_start_times_seconds": [i * 0.1 for i in range(len(text))],
              "character_end_times_seconds": [i * 0.1 + 0.05 for i in range(len(text))]}
        self.assertEqual([w["text"] for w in el.words_from_alignment(al)], ["It", "runs.", "Yes."])

    def test_cast_line_keeps_tag_for_api(self):
        out = el.cast_lines("HOST: [teasing] Just one?", CAST)
        self.assertEqual(out, [["HOST", "[teasing] Just one?", 0.0]])

    def test_gap_ignores_trailing_tag(self):
        self.assertEqual(el.line_gap("Go! [laughs]", "HOST", "HOST"), el.line_gap("Go!", "HOST", "HOST"))

    def test_pause_is_still_a_pause(self):
        out = el.cast_lines("Hello.\n[pause 1.5]\nAgain.", CAST)
        self.assertEqual(out, [["NARRATOR", "Hello.", 1.5], ["NARRATOR", "Again.", 0.0]])


if __name__ == "__main__":
    unittest.main()
