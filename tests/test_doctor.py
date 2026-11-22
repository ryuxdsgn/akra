import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import doctor  # noqa: E402


def fake_env(tools, outputs):
    """which() finds names in `tools`; run() returns outputs[name] (or raises if missing)."""
    def which(name):
        return f"/usr/bin/{name}" if name in tools else None

    def run(cmd):
        key = os.path.basename(cmd[0])
        if key not in outputs:
            raise OSError(key)
        return outputs[key]
    return which, run


GOOD = {
    "node": "v24.13.0\n",
    "ffmpeg": " ... A->A loudnorm  EBU R128 loudness normalization\n",
}


class ParseVersion(unittest.TestCase):
    def test_node_style(self):
        self.assertEqual(doctor.major_version("v24.13.0"), 24)

    def test_garbage(self):
        self.assertIsNone(doctor.major_version("not a version"))


class Checks(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def results(self, tools, outputs):
        which, run = fake_env(tools, outputs)
        return {r.name: r for r in doctor.run_checks(self.root, which=which, run=run)}

    def test_all_required_present_passes(self):
        res = self.results({"node", "npx", "ffmpeg", "git", "uv"}, GOOD)
        self.assertFalse(doctor.has_failures(res.values()))
        self.assertEqual(res["node"].status, "ok")
        self.assertEqual(res["ffmpeg"].status, "ok")

    def test_chrome_missing_is_a_warning(self):
        which, run = fake_env({"node", "npx", "ffmpeg", "git"}, GOOD)
        res = {r.name: r for r in doctor.run_checks(self.root, which=which, run=run, exists=lambda p: False,
                                                    environ={})}
        self.assertEqual(res["chrome"].status, "warn")
        self.assertIn("Chrome", res["chrome"].detail)
        self.assertFalse(doctor.has_failures(res.values()))

    def test_chrome_found(self):
        which, _ = fake_env({"chromium"}, {})
        self.assertEqual(doctor.find_chrome(which, lambda p: False, {}), "/usr/bin/chromium")
        self.assertEqual(doctor.find_chrome(lambda n: None, lambda p: p == "/opt/c", {"CHROME": "/opt/c"}), "/opt/c")
        self.assertEqual(doctor.find_chrome(lambda n: None, lambda p: p == doctor.CHROME_APPS[0], {}),
                         doctor.CHROME_APPS[0])
        self.assertIsNone(doctor.find_chrome(lambda n: None, lambda p: False, {}))

    def test_old_node_fails(self):
        res = self.results({"node", "npx", "ffmpeg", "git"}, dict(GOOD, node="v20.11.0\n"))
        self.assertEqual(res["node"].status, "fail")
        self.assertIn("22", res["node"].detail)
        self.assertTrue(doctor.has_failures(res.values()))

    def test_missing_ffmpeg_fails(self):
        res = self.results({"node", "npx", "git"}, GOOD)
        self.assertEqual(res["ffmpeg"].status, "fail")

    def test_ffmpeg_without_loudnorm_fails(self):
        res = self.results({"node", "npx", "ffmpeg", "git"}, dict(GOOD, ffmpeg="no filters here\n"))
        self.assertEqual(res["ffmpeg"].status, "fail")
        self.assertIn("loudnorm", res["ffmpeg"].detail)

    def test_optional_items_only_warn(self):
        res = self.results({"node", "npx", "ffmpeg", "git"}, GOOD)  # no uv, no venvs, no keys
        for name in ("uv", "kokoro", "youtube", "elevenlabs", "channels"):
            self.assertEqual(res[name].status, "warn", name)
        self.assertFalse(doctor.has_failures(res.values()))

    def test_elevenlabs_key_detected_but_never_shown(self):
        with open(os.path.join(self.root, ".env"), "w") as f:
            f.write("# comment\nELEVENLABS_API_KEY=sk_secret_value_123\n")
        res = self.results({"node", "npx", "ffmpeg", "git"}, GOOD)
        self.assertEqual(res["elevenlabs"].status, "ok")
        self.assertNotIn("sk_secret_value_123", res["elevenlabs"].detail)

    def test_empty_elevenlabs_key_warns(self):
        with open(os.path.join(self.root, ".env"), "w") as f:
            f.write("ELEVENLABS_API_KEY=\n")
        res = self.results({"node", "npx", "ffmpeg", "git"}, GOOD)
        self.assertEqual(res["elevenlabs"].status, "warn")

    def test_youtube_needs_venv_and_client_secret(self):
        os.makedirs(os.path.join(self.root, ".venv-youtube", "bin"))
        open(os.path.join(self.root, ".venv-youtube", "bin", "python"), "w").close()
        res = self.results({"node", "npx", "ffmpeg", "git"}, GOOD)
        self.assertEqual(res["youtube"].status, "warn")
        self.assertIn("client_secret.json", res["youtube"].detail)
        open(os.path.join(self.root, "client_secret.json"), "w").close()
        res = self.results({"node", "npx", "ffmpeg", "git"}, GOOD)
        self.assertEqual(res["youtube"].status, "ok")

    def test_channels_counted(self):
        os.makedirs(os.path.join(self.root, "channels", "my-channel"))
        open(os.path.join(self.root, "channels", "my-channel", "channel.json"), "w").close()
        res = self.results({"node", "npx", "ffmpeg", "git"}, GOOD)
        self.assertEqual(res["channels"].status, "ok")
        self.assertIn("my-channel", res["channels"].detail)


if __name__ == "__main__":
    unittest.main()
