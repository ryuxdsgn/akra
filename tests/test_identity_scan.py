import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import identity_scan  # noqa: E402


class IdentityScanTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def w(self, rel, data, mode="w"):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, mode) as f:
            f.write(data)

    def test_hits_and_skip(self):
        self.w("a.txt", "hello Zorblax here")
        self.w("sub/b.md", "nothing")
        self.w("skipme/c.md", "zorblax")
        self.w("bin.dat", b"zorblax\0\1", "wb")
        hits = identity_scan.scan(self.d, ["nothing-here", "ZORBLAX"], skip=["skipme"])
        self.assertEqual(hits, [("a.txt", "deny pattern 2"), ("bin.dat", "deny pattern 2")])

    def test_binary_and_pycache(self):
        self.w("img.png", b"\x89PNG\0\0zOrBlAx\0", "wb")
        self.w("pkg/__pycache__/m.cpython-312.pyc", b"\0\0/" + b"Users/bob/repo/m.py\0", "wb")
        self.assertEqual(identity_scan.scan(self.d, ["zorblax"]), [("img.png", "deny pattern 1")])
        hits = identity_scan.scan(self.d, ["zorblax"], skip_dirs=())
        self.assertIn(("pkg/__pycache__/m.cpython-312.pyc", "/" + "Users/bob/"), hits)
        self.assertEqual(identity_scan.main([self.d, "--deny", self._deny("zorblax"), "--skip", "deny.txt"]), 1)

    def test_output_never_repeats_a_pattern(self):
        import contextlib
        import io
        self.w("a.txt", "zorblax")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            identity_scan.main([self.d, "--deny", self._deny("zorblax"), "--skip", "deny.txt"])
        self.assertIn("deny pattern 1", buf.getvalue())
        self.assertNotIn("zorblax", buf.getvalue().lower().replace("a.txt", ""))

    def test_symlinks_are_scanned_not_followed(self):
        outside = tempfile.mkdtemp()
        with open(os.path.join(outside, "s.txt"), "w") as f:
            f.write("zorblax")
        os.symlink(os.path.join(outside, "s.txt"), os.path.join(self.d, "abs_link"))
        self.w("inner.txt", "ok")
        os.symlink("inner.txt", os.path.join(self.d, "rel_link"))
        os.symlink("zorblax-dir", os.path.join(self.d, "named_link"))
        hits = identity_scan.scan(self.d, ["zorblax"])
        self.assertIn(("abs_link", "symlink outside the tree"), hits)
        self.assertIn(("named_link", "deny pattern 1"), hits)
        self.assertFalse([h for h in hits if h[0] == "rel_link"])
        self.assertFalse([h for h in hits if h[0] == "abs_link" and h[1] == "deny pattern 1"])

    def _deny(self, *pats):
        p = os.path.join(self.d, "deny.txt")
        with open(p, "w") as f:
            f.write("\n".join(pats) + "\n")
        return p

    def test_home_paths(self):
        self.w("x.py", "p='/"+"Users/bob/stuff' q='/"+"home/amy/x'")
        hits = identity_scan.scan(self.d, [])
        self.assertEqual({h[1] for h in hits}, {"/"+"Users/bob/", "/"+"home/amy/"})

    def test_cli_and_comments(self):
        deny = os.path.join(self.d, "deny.txt")
        with open(deny, "w") as f:
            f.write("# comment zorblax\n\nquuxfoo\n")
        self.w("a.txt", "zorblax only")
        self.assertEqual(identity_scan.main([self.d, "--deny", deny, "--skip", "deny.txt"]), 0)
        self.w("b.txt", "QuuxFoo")
        self.assertEqual(identity_scan.main([self.d, "--deny", deny, "--skip", "deny.txt"]), 1)


if __name__ == "__main__":
    unittest.main()
