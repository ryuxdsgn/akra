#!/usr/bin/env python3
"""Export the public tree of this repo into a fresh directory.

Usage: export_public.py <dest> [--deny FILE] [--allow-no-deny] [--exclude FILE] [--allow-no-exclude]
                        [--allow-dirty] [--no-tests] [--repo ROOT]

Takes the files of the HEAD commit (`git archive HEAD`, so uncommitted edits never leak in) that match PUBLIC_PATHS
(an allowlist: nothing outside it ships), minus the patterns in the local exclude file (.public-export-exclude.txt,
gitignored, one fnmatch pattern per line; a pattern also matches everything below it), minus secrets and library
items that lack `"public": true`. It recreates symlinks as links and rebuilds library/catalog.json (empty when no
items ship). Then it runs the test suite in a throw-away copy of <dest> (no bytecode written), removes any
__pycache__ from <dest>, and scans <dest> LAST for private identity strings: text and binary files, symlink
targets, every folder.
Exit 1 on any scan hit or test failure, 2 on a usage problem (dest not empty, no deny file, no exclude file,
dirty tracked files). Stdlib only.
"""
import argparse
import fnmatch
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import identity_scan  # noqa: E402

# What ships (fnmatch on posix paths; an entry also matches everything below it). Everything else stays home.
PUBLIC_PATHS = [
    ".agents/skills/akra",
    ".claude/skills/akra",
    ".env.example",
    ".gitignore",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "THIRD_PARTY.md",
    "docs/setup.md",
    "docs/tutorials",
    "library",
    "render/_template",
    "skills/akra",
    "tests",
    "tools",
]
EXCLUDE_FILE = ".public-export-exclude.txt"
ALWAYS_SKIP_NAMES = ("client_secret",)
LIBRARY_KINDS = {"characters": "characters", "envs": "envs", "poses": "poses"}
NO_BYTECODE = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def _matches(rel, patterns):
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/") + "/*") for pat in patterns)


def load_excludes(path):
    """Patterns of the exclude file: one per line, blank lines and # comments ignored."""
    with open(path, encoding="utf-8") as f:
        return [s for s in (line.strip() for line in f) if s and not s.startswith("#")]


def is_public_path(rel):
    return _matches(rel, PUBLIC_PATHS)


def is_secret(rel):
    name = rel.rsplit("/", 1)[-1]
    if name in (".public-deny.txt", EXCLUDE_FILE):
        return True
    if name.startswith(".env") and name != ".env.example":
        return True
    return name.startswith(ALWAYS_SKIP_NAMES) or (name.startswith(".") and "token" in name and name.endswith(".json"))


def is_private_path(rel, excludes=()):
    """True when rel does not ship: outside the allowlist, a secret, or matched by an exclude pattern."""
    return not is_public_path(rel) or is_secret(rel) or _matches(rel, excludes)


def library_private_files(read, files):
    """Files of library items without "public": true (json, code with the same stem, preview).

    `read(rel)` returns the committed bytes of a file."""
    out = set()
    for rel in files:
        parts = rel.split("/")
        if len(parts) == 3 and parts[0] == "library" and parts[1] in LIBRARY_KINDS and rel.endswith(".json"):
            try:
                item = json.loads(read(rel))
            except (OSError, ValueError, KeyError):
                continue
            if item.get("public") is True:
                continue
            stem = parts[2][:-5]
            out.add(rel)
            out.add(f"library/{parts[1]}/{stem}.py")
            out.add(f"library/previews/{parts[1]}/{stem}.png")
            if isinstance(item.get("preview"), str):
                out.add("library/" + item["preview"])
    return out & set(files)


def head_tree(root):
    """{path: tarfile member} and a reader for the HEAD commit (`git archive HEAD`)."""
    r = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=root, capture_output=True, check=True)
    tar = tarfile.open(fileobj=io.BytesIO(r.stdout))
    members = {m.name: m for m in tar.getmembers() if m.isfile() or m.issym()}

    def read(rel):
        return tar.extractfile(members[rel]).read()
    return members, read


def dirty_tracked(root):
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
                       capture_output=True, text=True, check=True)
    return [line[3:] for line in r.stdout.splitlines() if line.strip()]


def _run_tests(dest):
    """Run the suite in a throw-away copy of dest, so no __pycache__ or test output lands in the export."""
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        shutil.copytree(dest, tree, symlinks=True)
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"], cwd=tree, env=NO_BYTECODE)
    return r.returncode


def _drop_pycache(dest):
    for d in sorted(Path(dest).rglob("__pycache__"), reverse=True):
        if d.is_dir() and not d.is_symlink():
            shutil.rmtree(d)


def export(root, dest, deny=None, run_tests=True, allow_no_deny=False, allow_dirty=False, exclude=None,
           allow_no_exclude=False):
    root, dest = Path(root), Path(dest)
    if dest.exists() and any(dest.iterdir()):
        print(f"error: {dest} is not empty", file=sys.stderr)
        return 2
    have_deny = bool(deny) and Path(deny).is_file()
    if not have_deny and not allow_no_deny:
        print("error: no deny file (.public-deny.txt); pass --deny FILE, or --allow-no-deny to scan home paths only",
              file=sys.stderr)
        return 2
    have_exclude = bool(exclude) and Path(exclude).is_file()
    if not have_exclude and not allow_no_exclude:
        print(f"error: no exclude file ({EXCLUDE_FILE}); pass --exclude FILE, or --allow-no-exclude to ship "
              "everything on the allowlist", file=sys.stderr)
        return 2
    excludes = load_excludes(exclude) if have_exclude else []
    dirty = dirty_tracked(root)
    if dirty and not allow_dirty:
        print(f"error: {len(dirty)} tracked file(s) have uncommitted changes; commit them first (the export takes HEAD), "
              "or pass --allow-dirty to export HEAD anyway", file=sys.stderr)
        return 2
    if dirty:
        print(f"warning: {len(dirty)} tracked file(s) have uncommitted changes; exporting HEAD without them", file=sys.stderr)

    members, read = head_tree(root)
    files = sorted(members)
    skipped_private = {f for f in files if is_private_path(f, excludes)}
    skipped_lib = library_private_files(read, files) - skipped_private
    keep = [f for f in files if f not in skipped_private and f not in skipped_lib]
    dest.mkdir(parents=True, exist_ok=True)
    total, links = 0, 0
    for rel in keep:
        m, out = members[rel], dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if m.issym():
            os.symlink(m.linkname, out)
            links += 1
            continue
        data = read(rel)
        out.write_bytes(data)
        os.chmod(out, 0o755 if m.mode & 0o111 else 0o644)
        total += len(data)

    if (dest / "library" / "catalog.py").is_file():
        r = subprocess.run([sys.executable, "-B", "-c",
                            "from library.catalog import build_catalog; build_catalog('.')"],
                           cwd=dest, capture_output=True, text=True, env=NO_BYTECODE)
        if r.returncode != 0:
            print("catalog rebuild failed:\n" + r.stderr, file=sys.stderr)
            return 1

    print(f"exported {len(keep)} files ({links} symlinks), {total} bytes from HEAD to {dest}")
    print(f"excluded: {len(skipped_private)} paths (outside the allowlist, secrets or {len(excludes)} exclude "
          f"patterns), {len(skipped_lib)} non-public library files")
    status = 0
    if run_tests and _run_tests(dest) != 0:
        print("tests failed in export", file=sys.stderr)
        status = 1
    _drop_pycache(dest)

    pats = identity_scan.load_patterns(deny) if have_deny else []
    hits = identity_scan.scan(dest, pats, skip_dirs=())
    for rel, p in hits:
        print(f"HIT {rel}: {p}")
    print(f"identity scan (text + binary, all folders): {len(hits)} hit(s)"
          + ("" if pats else " (home paths only, no deny file)"))
    return 1 if hits else status


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--deny", default=None, help="deny pattern file (default: .public-deny.txt in the repo root)")
    ap.add_argument("--allow-no-deny", action="store_true", help="export without a deny file (home-path scan only)")
    ap.add_argument("--exclude", default=None, help=f"exclude pattern file (default: {EXCLUDE_FILE} in the repo root)")
    ap.add_argument("--allow-no-exclude", action="store_true", help="export without an exclude file")
    ap.add_argument("--allow-dirty", action="store_true", help="export HEAD even when tracked files are modified")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--repo", default=str(HERE.parent))
    a = ap.parse_args(argv)
    deny = a.deny or str(Path(a.repo) / ".public-deny.txt")
    exclude = a.exclude or str(Path(a.repo) / EXCLUDE_FILE)
    return export(a.repo, a.dest, deny, not a.no_tests, a.allow_no_deny, a.allow_dirty, exclude, a.allow_no_exclude)


if __name__ == "__main__":
    sys.exit(main())
