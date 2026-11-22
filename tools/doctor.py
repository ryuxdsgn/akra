#!/usr/bin/env python3
"""Check that this machine is ready to run akra end to end.

Usage (from the repo root):
  python3 tools/doctor.py [--root <repo folder>]

Required (FAIL stops the build): Python 3.10+, Node.js 22+ with npx (HyperFrames 0.9.40), ffmpeg with the
loudnorm filter. Optional (WARN): Google Chrome (render and previews need it), uv, the Kokoro venv (local voice), the YouTube venv + client_secret.json
(auto upload), an ElevenLabs key in .env, at least one channel, Meta (FB/IG)
keys + login + Instagram due job for channels that use Meta. Key values are never printed.
Exit code 1 when a required check fails. Standard library only.
"""
import os
import re
import shutil
import subprocess
import sys
from collections import namedtuple

Result = namedtuple("Result", "name status detail")  # status: ok | warn | fail

NODE_MIN = 22
PY_MIN = (3, 10)


def major_version(text):
    m = re.search(r"(\d+)\.\d+", text or "")
    return int(m.group(1)) if m else None


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout


def _env_value(root, key):
    path = os.path.join(root, ".env")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


CHROME_APPS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
)
CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")


def find_chrome(which=shutil.which, exists=os.path.isfile, environ=None):
    """Path of a Chrome/Chromium binary: $CHROME, the usual app locations, then PATH; None when absent."""
    env = os.environ if environ is None else environ
    if env.get("CHROME") and exists(env["CHROME"]):
        return env["CHROME"]
    for path in CHROME_APPS:
        if exists(path):
            return path
    for name in CHROME_NAMES:
        found = which(name)
        if found:
            return found
    return None


def run_checks(root, which=shutil.which, run=_run, exists=os.path.isfile, environ=None):
    out = []

    py = sys.version_info[:2]
    out.append(Result("python", "ok" if py >= PY_MIN else "fail",
                      f"Python {py[0]}.{py[1]}" + ("" if py >= PY_MIN else f" (needs {PY_MIN[0]}.{PY_MIN[1]}+)")))

    if not which("node"):
        out.append(Result("node", "fail", f"Node.js not found (needs {NODE_MIN}+)"))
    else:
        try:
            ver = run(["node", "--version"]).strip()
        except (OSError, subprocess.SubprocessError):
            ver = ""
        major = major_version(ver)
        ok = major is not None and major >= NODE_MIN
        out.append(Result("node", "ok" if ok else "fail",
                          f"Node {ver or '?'}" + ("" if ok else f" (needs {NODE_MIN}+ for HyperFrames)")))
    out.append(Result("npx", "ok" if which("npx") else "fail",
                      "npx found" if which("npx") else "npx not found (installed together with Node.js)"))

    if not which("ffmpeg"):
        out.append(Result("ffmpeg", "fail", "ffmpeg not found"))
    else:
        try:
            filters = run(["ffmpeg", "-hide_banner", "-filters"])
        except (OSError, subprocess.SubprocessError):
            filters = ""
        ok = "loudnorm" in filters
        out.append(Result("ffmpeg", "ok" if ok else "fail",
                          "ffmpeg with the loudnorm filter" if ok else "ffmpeg without the loudnorm filter (install a full build)"))

    chrome = find_chrome(which, exists, environ)
    out.append(Result("chrome", "ok" if chrome else "warn",
                      f"Chrome: {chrome}" if chrome
                      else "Google Chrome not found: rendering and previews need it (install it, or set CHROME=<path>)"))

    out.append(Result("git", "ok" if which("git") else "warn",
                      "git found" if which("git") else "git not found (needed to update the repo)"))
    out.append(Result("uv", "ok" if which("uv") else "warn",
                      "uv found" if which("uv") else "uv not found (needed to create the Kokoro/YouTube venvs)"))

    kokoro = os.path.isfile(os.path.join(root, ".venv-kokoro", "bin", "python"))
    out.append(Result("kokoro", "ok" if kokoro else "warn",
                      "Kokoro venv ready (free local voice)" if kokoro
                      else "Kokoro venv missing: run tools/setup.sh --kokoro"))

    key = _env_value(root, "ELEVENLABS_API_KEY")
    out.append(Result("elevenlabs", "ok" if key else "warn",
                      "ELEVENLABS_API_KEY is set in .env" if key
                      else "ELEVENLABS_API_KEY not set in .env (optional, if you do not use Kokoro)"))

    yt_venv = os.path.isfile(os.path.join(root, ".venv-youtube", "bin", "python"))
    secret = os.path.isfile(os.path.join(root, "client_secret.json"))
    if yt_venv and secret:
        out.append(Result("youtube", "ok", "YouTube venv and client_secret.json ready"))
    else:
        missing = [n for n, ok in ((".venv-youtube (tools/setup.sh --youtube)", yt_venv),
                                   ("client_secret.json", secret)) if not ok]
        out.append(Result("youtube", "warn", "automatic upload not ready, missing: " + ", ".join(missing)))

    chan_dir = os.path.join(root, "channels")
    chans = sorted(d for d in (os.listdir(chan_dir) if os.path.isdir(chan_dir) else [])
                   if os.path.isfile(os.path.join(chan_dir, d, "channel.json")))
    out.append(Result("channels", "ok" if chans else "warn",
                      ("channels: " + ", ".join(chans)) if chans
                      else "no channel yet: ask the agent to \"create a new channel\" (channel mode)"))
    out.extend(meta_checks(root, chans))
    return out


def meta_checks(root, chans, home=None):
    """One WARN/OK row per channel that uses Meta (facebook_page or meta in channel.json)."""
    import json
    home = home or os.path.expanduser("~")
    out = []
    keys = bool(_env_value(root, "META_APP_ID") and _env_value(root, "META_APP_SECRET"))
    due = os.path.isfile(os.path.join(home, "Library", "LaunchAgents", "com.akra.meta-due.plist"))
    for cid in chans:
        try:
            ch = json.load(open(os.path.join(root, "channels", cid, "channel.json"), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not (ch.get("facebook_page") or ch.get("meta")):
            continue
        plats = (ch.get("meta") or {}).get("platforms") or ["facebook", "instagram"]
        token = os.path.isfile(os.path.join(root, f".meta-{ch.get('meta_account') or cid}-token.json"))
        missing = [n for n, ok in (("META_APP_ID/META_APP_SECRET in .env", keys), ("login (token)", token),
                                   ("meta.platforms", bool(ch.get("meta"))),
                                   ("Instagram automatic job", due or "instagram" not in plats)) if not ok]
        detail = f"{cid}: {', '.join(plats)}"
        out.append(Result("meta", "warn" if missing else "ok",
                          detail + (" | missing: " + ", ".join(missing) +
                                    f" (run meta_upload.py setup --channel channels/{cid})" if missing else " ready")))
    return out


def has_failures(results):
    return any(r.status == "fail" for r in results)


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if len(sys.argv) == 3 and sys.argv[1] == "--root":
        root = os.path.abspath(sys.argv[2])
    results = run_checks(root)
    mark = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}
    for r in results:
        print(f"[{mark[r.status]}] {r.name:<10} {r.detail}")
    if has_failures(results):
        print("\nSome required items are missing. See docs/setup.md.")
        return 1
    print("\nReady. WARN is only for optional features.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
