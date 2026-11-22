import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "skills", "akra", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import meta_upload as mu  # noqa: E402
import doctor  # noqa: E402
import validate_episode as ve  # noqa: E402

PAGES = [{"id": "111", "name": "Page A", "access_token": "tA", "ig_user_id": "9", "ig_username": "akun_a"},
         {"id": "222", "name": "Page B", "access_token": "tB", "ig_user_id": None, "ig_username": None}]


def make_root():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "skills", "akra", "scripts"))
    os.makedirs(os.path.join(d, "channels", "demo", "episodes"))
    return d


class ParsePlatforms(unittest.TestCase):
    def test_codes_names_and_menu(self):
        self.assertEqual(mu.parse_platforms("fb"), ["facebook"])
        self.assertEqual(mu.parse_platforms("ig"), ["instagram"])
        self.assertEqual(mu.parse_platforms("ig, fb"), ["facebook", "instagram"])
        self.assertEqual(mu.parse_platforms("instagram"), ["instagram"])
        self.assertEqual(mu.parse_platforms("3"), ["facebook", "instagram"])
        self.assertEqual(mu.parse_platforms("1"), ["facebook"])

    def test_unknown_raises(self):
        for bad in ("", "tiktok", "4", "fb,x"):
            with self.assertRaises(ValueError):
                mu.parse_platforms(bad)


class ChannelPlatforms(unittest.TestCase):
    def test_default_both_for_older_channels(self):
        self.assertEqual(mu.channel_platforms({}), ["facebook", "instagram"])

    def test_channel_choice_and_only_override(self):
        ch = {"meta": {"platforms": ["facebook"]}}
        self.assertEqual(mu.channel_platforms(ch), ["facebook"])
        self.assertEqual(mu.channel_platforms(ch, "ig"), ["instagram"])


class PickPage(unittest.TestCase):
    def test_by_id_single_and_menu(self):
        self.assertEqual(mu.pick_page(PAGES, "222")["name"], "Page B")
        self.assertEqual(mu.pick_page(PAGES[:1])["id"], "111")
        answers = iter(["9", "x", "2"])
        self.assertEqual(mu.pick_page(PAGES, None, lambda _: next(answers))["id"], "222")

    def test_errors(self):
        with self.assertRaises(SystemExit):
            mu.pick_page([], None)
        with self.assertRaises(SystemExit):
            mu.pick_page(PAGES, "333")
        with self.assertRaises(SystemExit) as e:
            mu.pick_page(PAGES, None, None)          # several pages, not interactive
        self.assertIn("--page", str(e.exception.code))


class EnvFile(unittest.TestCase):
    def test_set_replaces_and_is_private(self):
        d = make_root()
        with open(os.path.join(d, ".env"), "w") as f:
            f.write("ELEVENLABS_API_KEY=x\nMETA_APP_ID=old\n")
        mu.set_env("META_APP_ID", "123", d)
        mu.set_env("META_APP_SECRET", "s3", d)
        text = open(os.path.join(d, ".env")).read()
        self.assertEqual(text, "ELEVENLABS_API_KEY=x\nMETA_APP_ID=123\nMETA_APP_SECRET=s3\n")
        self.assertEqual(os.stat(os.path.join(d, ".env")).st_mode & 0o777, 0o600)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(mu.has_env("META_APP_SECRET", d))
            self.assertFalse(mu.has_env("META_NOPE", d))


class ApplyChannel(unittest.TestCase):
    def test_writes_page_ig_and_platforms(self):
        ch = {"id": "demo", "facebook_page": {"url": "u"}}
        mu.apply_channel(ch, PAGES[0], ["facebook", "instagram"])
        self.assertEqual(ch["facebook_page"], {"url": "u", "id": "111"})
        self.assertEqual(ch["instagram"]["handle"], "akun_a")
        self.assertEqual(ch["meta"], {"platforms": ["facebook", "instagram"]})
        self.assertEqual(ve._check_channel_extras(ch), [])

    def test_facebook_only_leaves_instagram(self):
        ch = {"id": "demo"}
        mu.apply_channel(ch, PAGES[1], ["facebook"])
        self.assertNotIn("instagram", ch)
        self.assertEqual(ch["meta"]["platforms"], ["facebook"])


class InstallDue(unittest.TestCase):
    def test_writes_plist_and_bootstraps_once(self):
        d, home, calls = make_root(), tempfile.mkdtemp(), []

        def run(cmd, **kw):
            calls.append(cmd[:2])
            return SimpleNamespace(returncode=0)
        self.assertEqual(mu.install_due(d, home, run, "darwin"), "installed")
        path = os.path.join(home, "Library", "LaunchAgents", "com.akra.meta-due.plist")
        text = open(path).read()
        self.assertIn("<string>due</string>", text)
        self.assertIn(os.path.join(d, "skills", "akra", "scripts", "meta_upload.py"), text)
        self.assertIn("<integer>600</integer>", text)
        self.assertEqual(calls, [["launchctl", "bootout"], ["launchctl", "bootstrap"]])
        self.assertEqual(mu.install_due(d, home, run, "darwin"), "unchanged")
        self.assertEqual(len(calls), 2)

    def test_bootstrap_failure_exits(self):
        d, home = make_root(), tempfile.mkdtemp()
        with self.assertRaises(SystemExit):
            mu.install_due(d, home, lambda cmd, **kw: SimpleNamespace(returncode=5), "darwin")

    def test_linux_prints_cron(self):
        self.assertEqual(mu.install_due(make_root(), tempfile.mkdtemp(), None, "linux"), "cron")


class Setup(unittest.TestCase):
    def run_setup(self, platforms, page=PAGES[0], extra=None):
        d = make_root()
        ch = {"id": "demo", "name": "Demo", **(extra or {})}
        with open(os.path.join(d, "channels", "demo", "channel.json"), "w") as f:
            json.dump(ch, f)
        with open(os.path.join(d, ".env"), "w") as f:
            f.write("META_APP_ID=1\nMETA_APP_SECRET=2\n")
        a = SimpleNamespace(channel=os.path.join(d, "channels", "demo"), platforms=platforms, page=None, no_due=False)
        cwd = os.getcwd()
        os.chdir(d)
        try:
            with mock.patch.object(mu, "oauth_pages", return_value=[page]), \
                 mock.patch.object(mu, "install_due", return_value="installed") as due, \
                 mock.patch("sys.stdin.isatty", return_value=False), mock.patch.dict(os.environ, {}, clear=True):
                mu.setup(a)
        finally:
            os.chdir(cwd)
        out = json.load(open(os.path.join(d, "channels", "demo", "channel.json")))
        return d, out, due

    def test_both_platforms_installs_due(self):
        d, ch, due = self.run_setup("fb,ig")
        self.assertEqual(ch["meta"]["platforms"], ["facebook", "instagram"])
        self.assertEqual(ch["instagram"]["handle"], "akun_a")
        self.assertTrue(os.path.isfile(os.path.join(d, ".meta-demo-token.json")))
        due.assert_called_once()

    def test_facebook_only_skips_due(self):
        _, ch, due = self.run_setup("fb", PAGES[1])
        self.assertEqual(ch["meta"]["platforms"], ["facebook"])
        due.assert_not_called()

    def test_instagram_needs_linked_account(self):
        with self.assertRaises(SystemExit) as e:
            self.run_setup("ig", PAGES[1])
        self.assertIn("Instagram", str(e.exception.code))

    def test_instagram_handle_mismatch_stops(self):
        with self.assertRaises(SystemExit):
            self.run_setup("fb,ig", PAGES[0], {"instagram": {"handle": "lain"}})

    def test_missing_keys_non_interactive_stops(self):
        d = make_root()
        with open(os.path.join(d, "channels", "demo", "channel.json"), "w") as f:
            json.dump({"id": "demo", "name": "Demo"}, f)
        a = SimpleNamespace(channel=os.path.join(d, "channels", "demo"), platforms="fb", page=None, no_due=False)
        cwd = os.getcwd()
        os.chdir(d)
        try:
            with mock.patch("sys.stdin.isatty", return_value=False), mock.patch.dict(os.environ, {}, clear=True), \
                 self.assertRaises(SystemExit) as e:
                mu.setup(a)
        finally:
            os.chdir(cwd)
        self.assertIn(".env", str(e.exception.code))


class Validator(unittest.TestCase):
    def test_meta_rules(self):
        ok = {"facebook_page": {"id": "1"}, "instagram": {"handle": "a"}, "meta": {"platforms": ["instagram"]}}
        self.assertEqual(ve._check_channel_extras(ok), [])
        for bad in ({"meta": {"platforms": []}, "facebook_page": {"id": "1"}},
                    {"meta": {"platforms": ["tiktok"]}, "facebook_page": {"id": "1"}},
                    {"meta": {"platforms": ["facebook"]}},
                    {"meta": {"platforms": ["instagram"]}, "facebook_page": {"id": "1"}}):
            self.assertEqual(len(ve._check_channel_extras(bad)), 1, bad)


class Doctor(unittest.TestCase):
    def test_meta_rows(self):
        d, home = make_root(), tempfile.mkdtemp()
        for cid, ch in (("plain", {"id": "plain"}),
                        ("fbonly", {"id": "fbonly", "facebook_page": {"id": "1"}, "meta": {"platforms": ["facebook"]}}),
                        ("both", {"id": "both", "facebook_page": {"id": "2"}, "meta": {"platforms": ["facebook", "instagram"]}})):
            os.makedirs(os.path.join(d, "channels", cid), exist_ok=True)
            json.dump(ch, open(os.path.join(d, "channels", cid, "channel.json"), "w"))
        open(os.path.join(d, ".env"), "w").write("META_APP_ID=1\nMETA_APP_SECRET=2\n")
        open(os.path.join(d, ".meta-fbonly-token.json"), "w").write("{}")
        open(os.path.join(d, ".meta-both-token.json"), "w").write("{}")
        rows = doctor.meta_checks(d, ["both", "fbonly", "plain"], home)
        self.assertEqual([r.status for r in rows], ["warn", "ok"])
        self.assertIn("Instagram automatic job", rows[0].detail)
        self.assertNotIn("1", "".join(r.detail for r in rows).replace("instagram", ""))


if __name__ == "__main__":
    unittest.main()
