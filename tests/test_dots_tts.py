"""Pure helpers of dots_tts.py (no model needed)."""
import importlib.util
import unittest

import helpers  # noqa: F401  (puts skills/akra/scripts on sys.path)
from dots_tts import angka, cache_key, max_seconds, pieces_of, script_lines, speak_text, split_at_pauses, time_words


class TestAngka(unittest.TestCase):
    def test_numbers(self):
        cases = {0: "nol", 7: "tujuh", 10: "sepuluh", 11: "sebelas", 15: "lima belas", 20: "dua puluh",
                 25: "dua puluh lima", 100: "seratus", 101: "seratus satu", 250: "dua ratus lima puluh",
                 1000: "seribu", 1500: "seribu lima ratus", 2026: "dua ribu dua puluh enam"}
        for n, want in cases.items():
            self.assertEqual(angka(n), want, n)


class TestSpeakText(unittest.TestCase):
    def test_indonesian_numbers_and_hints(self):
        self.assertEqual(speak_text("Putar 10x, tunggu 5 menit (lima)", "ID"), "Putar sepuluh kali, tunggu lima menit")
        self.assertEqual(speak_text("Naik 20%", "ID"), "Naik dua puluh persen")

    def test_other_language_keeps_digits(self):
        self.assertEqual(speak_text("Do 10 reps", "EN"), "Do 10 reps")


class TestTiming(unittest.TestCase):
    def test_blank_line_is_a_beat(self):
        self.assertEqual(script_lines("Merah kuning.\n\nHijau."), [["Merah kuning.", 0.45], ["Hijau.", 0.0]])

    def test_uses_whisper_when_counts_match_else_shares_out(self):
        lines = [["Hello everyone.", 0.0], ["The light turns green.", 0.0]]
        spans = [(0.0, 1.0), (1.4, 3.4)]
        heard = [{"text": "Hello", "start": 0.1, "end": 0.4}, {"text": "everyone", "start": 0.45, "end": 0.9},
                 {"text": "The", "start": 1.5, "end": 1.9}]        # whisper lost words in line 2
        words, fallback = time_words(lines, spans, heard)
        self.assertEqual([w[0] for w in words], ["Hello", "everyone.", "The", "light", "turns", "green."])
        self.assertEqual(words[0][1:], [0.1, 0.4])
        self.assertEqual(fallback, 1)
        self.assertAlmostEqual(words[2][1], 1.4)
        self.assertLessEqual(words[-1][2], 3.4)


class TestRunawayGuard(unittest.TestCase):
    def test_one_word_line_limit(self):
        self.assertLess(max_seconds("Hijau."), 2.0)          # a babbled 4 s "Hijau." is rejected
        self.assertGreater(max_seconds("Hijau."), 0.8)       # a normal 0.7 s "Hijau." passes
        self.assertGreater(max_seconds("Siapkan payung yang kuat, tanpa lubang, tanpa gagang patah."), 5.0)
        self.assertEqual(max_seconds("Merah. | Kuning. | Hijau."), max_seconds("Merah. Kuning. Hijau."))

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy lives in .venv-dots")
    def test_pieces_split_at_the_pauses(self):
        import numpy as np
        sr = 1000
        tone = lambda s: np.sin(np.arange(int(s * sr)) * 0.3).astype("float32")
        quiet = lambda s: np.zeros(int(s * sr), dtype="float32")
        seg = np.concatenate([tone(0.4), quiet(0.3), tone(0.5), quiet(0.1), tone(0.1), quiet(0.25), tone(0.4)])
        self.assertEqual(pieces_of("Merah. | Kuning. | Hijau."), ["Merah.", "Kuning.", "Hijau."])
        cut = split_at_pauses(seg, sr, 3)
        self.assertEqual(len(cut), 3)
        self.assertAlmostEqual(len(cut[0]) / sr, 0.55, delta=0.05)          # cut inside the 0.3 s pause
        self.assertEqual(sum(len(c) for c in cut), len(seg))
        self.assertIsNone(split_at_pauses(tone(1.0), sr, 2))

    def test_cache_key_changes_with_any_part(self):
        k = cache_key("Hijau.", b"voice", 7, 1.0)
        self.assertEqual(k, cache_key("Hijau.", b"voice", 7, 1.0))
        self.assertNotEqual(k, cache_key("Hijau.", b"voice", 8, 1.0))
        self.assertNotEqual(k, cache_key("Hijau.", b"other", 7, 1.0))


if __name__ == "__main__":
    unittest.main()
