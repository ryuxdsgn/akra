#!/usr/bin/env python3
"""Scan a tree for private identity strings (deny patterns, home paths).

Usage: identity_scan.py <root> [--deny FILE] [--skip PATH ...] [--all-dirs]
Text and binary files are both searched (case-insensitive bytes match). A deny hit is reported as
"deny pattern N" (N counts the non-comment lines), so the output never repeats a private string. Symlinks are not
followed: their target string is scanned, and a link that points outside the tree is a hit. `--all-dirs` also scans
__pycache__, node_modules and the like (the export does). Exit 1 when anything is found. Stdlib only.
"""
import argparse
import os
import re
import sys

HOME_RE = re.compile(rb"/(?:Users|home)/[A-Za-z0-9_.-]+/", re.I)
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".superpowers"}


def load_patterns(path):
    pats = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                pats.append(s)
    return pats


def _hits_in(data, low):
    """Deny patterns (reported by number, never by content) and home paths found in `data` (bytes)."""
    out = []
    ld = data.lower()
    for i, pl in enumerate(low, 1):
        if pl in ld:
            out.append(f"deny pattern {i}")
    for m in sorted(set(HOME_RE.findall(data))):
        out.append(m.decode("utf-8", "replace"))
    return out


def scan(root, patterns, skip=(), skip_dirs=SKIP_DIRS):
    root = os.path.abspath(root)
    skips = [s.strip("/").replace(os.sep, "/") for s in skip]
    low = [p.encode("utf-8").lower() for p in patterns]
    hits = []
    for dp, dns, fns in os.walk(root):
        rel_dir = os.path.relpath(dp, root).replace(os.sep, "/")
        entries = sorted(fns) + sorted(d for d in dns if os.path.islink(os.path.join(dp, d)))
        dns[:] = sorted(d for d in dns if d not in skip_dirs and not os.path.islink(os.path.join(dp, d)))
        for fn in entries:
            if fn in skip_dirs:
                continue
            rel = fn if rel_dir == "." else rel_dir + "/" + fn
            if any(rel == s or rel.startswith(s + "/") for s in skips):
                continue
            path = os.path.join(dp, fn)
            if os.path.islink(path):
                target = os.readlink(path)
                hits += [(rel, h) for h in _hits_in(os.fsencode(target), low)]
                resolved = os.path.normpath(os.path.join(dp, target))
                if os.path.isabs(target) or not (resolved + os.sep).startswith(root + os.sep):
                    hits.append((rel, "symlink outside the tree"))
                continue
            try:
                with open(path, "rb") as f:
                    data = f.read()
            except OSError:
                continue
            hits += [(rel, h) for h in _hits_in(data, low)]
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--deny")
    ap.add_argument("--skip", action="append", default=[])
    ap.add_argument("--all-dirs", action="store_true", help="also scan __pycache__, node_modules, .venv, .git")
    a = ap.parse_args(argv)
    pats = load_patterns(a.deny) if a.deny else []
    hits = scan(a.root, pats, a.skip, () if a.all_dirs else SKIP_DIRS)
    for rel, p in hits:
        print(f"{rel}: {p}")
    print(f"{len(hits)} hit(s)", file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
