#!/usr/bin/env python3
"""Post-render QA for an akra episode: one command instead of six.

  python3 qa_render.py render/<channel-id>/ep-015                 # newest renders/*.mp4
  python3 qa_render.py render/<channel-id>/ep-015 --mp4 renders/x.mp4 --no-copy

Checks (exit 1 if any FAIL):
  - loudness   integrated -15.5 .. -12.5 LUFS (target ~ -14), true peak <= -0.9 dBFS   (ffmpeg ebur128)
  - loop       SSIM first frame vs last frame >= 0.95 (Shorts replay seamlessly)         (ffmpeg ssim)
  - duration   15-60 s, and within 0.6 s of the episode's vo_duration
  - format     1080x1920, ~30 fps, has an audio stream                                  (ffprobe)
  - silence    no gap of silence longer than 1.2 s after the first second                (ffmpeg silencedetect)
  - style gate the channel's style_approved_on is set (user approved 2-3 sample style frames)
Then copies the MP4 to channels/<channel>/episodes/<ep>-assets/<ep>.mp4 and writes/updates the metrics
block at the top of <ep_dir>/REVIEW.md (your notes below the block are kept).
Looking at the frames is still your job: the snapshots before render, and a strip of the finished MP4
(`--strip 12.5` saves 6 frames from 12.5 s at 6 fps to the scratch/output folder for a motion check).
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LUFS = (-15.5, -12.5)
PEAK_MAX = -0.9
SSIM_MIN = 0.95
BEGIN, END = "<!-- qa_render:begin -->", "<!-- qa_render:end -->"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(mp4):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
             "-of", "json", mp4])
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    return dict(duration=float(j["format"]["duration"]), width=v.get("width"), height=v.get("height"),
                fps=round(float(num) / float(den or 1), 2), audio=any(s["codec_type"] == "audio" for s in j["streams"]))


def loudness(mp4):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    pk = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else None), (float(pk.group(1)) if pk and pk.group(1) != "-inf" else None)


def loop_ssim(mp4, tmp):
    a, b = os.path.join(tmp, "first.png"), os.path.join(tmp, "last.png")
    run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-frames:v", "1", a])
    run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.05", "-i", mp4, "-frames:v", "1", b])
    m = re.search(r"All:([\d.]+)", run(["ffmpeg", "-i", a, "-i", b, "-lavfi", "ssim", "-f", "null", "-"]).stderr)
    return float(m.group(1)) if m else None


def silences(mp4, min_len=1.2):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp4, "-af", f"silencedetect=n=-45dB:d={min_len}", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return [(s, e) for s, e in zip(starts, ends + [None] * (len(starts) - len(ends))) if s > 1.0]


def strip(mp4, at, out):
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", mp4, "-vf", "fps=6,scale=270:-1,tile=6x1", "-frames:v", "1", out])
    return out


def locate(ep_dir):
    """(project root, channel id or None) from the folder layout. render/<channel-id>/<ep-id> is normal;
    render/<ep-id> belongs to the one channel whose channel.json has "render_layout": "flat"
    (same rule as render/_template/channelcfg.py). None: pass --channel."""
    ep_dir = os.path.abspath(ep_dir)
    parent = os.path.dirname(ep_dir)
    if os.path.basename(parent) != "render":
        return os.path.dirname(os.path.dirname(parent)), os.path.basename(parent)
    root = os.path.dirname(parent)
    flat = []
    for path in sorted(glob.glob(os.path.join(root, "channels", "*", "channel.json"))):
        try:
            if json.load(open(path, encoding="utf-8")).get("render_layout") == "flat":
                flat.append(os.path.basename(os.path.dirname(path)))
        except (OSError, ValueError):
            pass
    return root, (flat[0] if len(flat) == 1 else None)


def style_gate(root, channel):
    """(ok, value) for the style-bible gate: channels/<id>/channel.json needs style_approved_on (YYYY-MM-DD),
    the date the user approved 2-3 sample style frames. ok None = no readable profile (not checked here)."""
    path = os.path.join(root, "channels", channel, "channel.json")
    try:
        prof = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None, "no channel.json"
    when = prof.get("style_approved_on") if isinstance(prof, dict) else None
    if isinstance(when, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        return True, when
    return False, "style_approved_on missing"


def find_repo_root_for_qa():
    for d in Path(__file__).resolve().parents:
        if (d / "library").is_dir() and (d / "skills" / "akra").is_dir():
            return d
    raise RuntimeError("repo root (library/ + skills/akra/) not found above " + __file__)


def library_checks(ep_dir, do_freeze=True):
    """Check .lib_used.json, then freeze the library into the episode (only when no draft item was used and
    do_freeze is set, i.e. the other QA checks passed). Returns (name, ok, value) tuples."""
    ep = Path(ep_dir)
    used_path = ep / ".lib_used.json"
    if not used_path.is_file():
        return []
    try:
        used = json.loads(used_path.read_text())
    except (ValueError, OSError):
        return [("library", False, ".lib_used.json unreadable")]
    out = []
    drafts = sorted(i for i, st in used.get("items", {}).items() if st == "draft")
    if drafts:
        out.append((f"library: draft item(s) {', '.join(drafts)} used in final render - vet the item "
                    f"(after user approval: library/cli.py vet <id>) and rebuild; if already frozen, run "
                    f"`python3 library/cli.py freeze {ep} --refresh` and note it in REVIEW.md", False, ", ".join(drafts)))
    custom = used.get("custom") or []
    if custom:
        names = ", ".join(str(c) for c in custom)
        out.append((f"library: custom look/pose {names} - candidate for the library", True, names))
    if do_freeze and not drafts:
        root = str(find_repo_root_for_qa())
        if root not in sys.path:
            sys.path.insert(0, root)
        from library.freeze import freeze
        freeze(ep)
    return out


ADDON_DIR = Path(__file__).resolve().parent


def addon_checks(ep_dir, channel):
    """Optional QA add-ons: modules named qa_addon_*.py next to this script. Each has
    qa_checks(ep_dir, channel) -> [(name, ok, value, expect, note)]; a row with a note is printed as a note only.
    None installed: no rows. An add-on that breaks fails its own row instead of stopping the QA."""
    import importlib
    rows = []
    for path in sorted(ADDON_DIR.glob("qa_addon_*.py")):
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))
        try:
            rows += list(importlib.import_module(path.stem).qa_checks(ep_dir, channel))
        except Exception as e:  # keep QA usable if an add-on itself breaks
            rows.append((path.stem, False, f"add-on error: {e}", "add-on runs", None))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ep_dir", help="render/<channel-id>/<ep-id> (or render/<ep-id> for a channel with render_layout flat)")
    ap.add_argument("--mp4", help="render to check (default: newest renders/*.mp4)")
    ap.add_argument("--channel", help="default: from the folder layout (see locate())")
    ap.add_argument("--no-copy", action="store_true", help="do not copy into channels/.../<ep>-assets/")
    ap.add_argument("--strip", type=float, action="append", default=[], help="save a 6-frame motion strip from this time (s)")
    a = ap.parse_args()

    ep_dir = os.path.abspath(a.ep_dir)
    ep_id = os.path.basename(ep_dir)
    root, found = locate(ep_dir)
    a.channel = a.channel or found
    if not a.channel:
        sys.exit(f"{ep_dir}: channel unknown. Use render/<channel-id>/{ep_id}, pass --channel <id>, or set "
                 "\"render_layout\": \"flat\" in exactly one channels/<id>/channel.json")
    mp4 = os.path.abspath(a.mp4) if a.mp4 else max(glob.glob(os.path.join(ep_dir, "renders", "*.mp4")), key=os.path.getmtime, default=None)
    if not mp4 or not os.path.exists(mp4):
        sys.exit(f"no render found in {ep_dir}/renders")
    ep_json = os.path.join(root, "channels", a.channel, "episodes", f"{ep_id}.json")
    vo = json.load(open(ep_json)).get("vo_duration") if os.path.exists(ep_json) else None

    checks = []

    def check(name, ok, value, want):
        checks.append((name, "PASS" if ok else "FAIL", value, want))

    info = probe(mp4)
    with tempfile.TemporaryDirectory() as tmp:
        lufs, peak = loudness(mp4)
        ssim = loop_ssim(mp4, tmp)
    gaps = silences(mp4)

    check("loudness", lufs is not None and LUFS[0] <= lufs <= LUFS[1], f"{lufs} LUFS", f"{LUFS[0]}..{LUFS[1]} (target -14)")
    check("true peak", peak is not None and peak <= PEAK_MAX, f"{peak} dBFS", f"<= {PEAK_MAX}")
    check("loop SSIM", ssim is not None and ssim >= SSIM_MIN, f"{ssim:.3f}" if ssim else "n/a", f">= {SSIM_MIN}")
    d = info["duration"]
    check("duration", 15 <= d <= 60 and (vo is None or abs(d - vo) <= 0.6), f"{d:.2f} s" + (f" (vo {vo})" if vo else ""), "15-60 s, ~vo_duration")
    check("format", info["width"] == 1080 and info["height"] == 1920 and 29 <= info["fps"] <= 31 and info["audio"],
          f'{info["width"]}x{info["height"]} {info["fps"]} fps audio={info["audio"]}', "1080x1920 30 fps + audio")
    check("silence", not gaps, ", ".join(f"{s:.1f}-{e:.1f}s" if e else f"{s:.1f}s-end" for s, e in gaps) or "none", "no gap > 1.2 s")

    notes = []
    for name, ok, value, expect, note in addon_checks(ep_dir, a.channel):
        if note:
            notes.append(note)
        else:
            check(name, ok, value, expect)

    sg_ok, sg_val = style_gate(root, a.channel)
    if sg_ok is None:
        notes.append(f"style gate: not checked ({sg_val})")
    else:
        check("style gate", sg_ok, sg_val, "style_approved_on set (references/channel-setup.md)")

    for name, ok, value in library_checks(ep_dir, do_freeze=all(c[1] == "PASS" for c in checks)):
        if ok:
            notes.append(name)
        else:
            short, _, hint = name.partition(" - ")
            check(short, False, value, "no draft items")
            if hint:
                notes.append("FIX: " + hint)

    w = max(len(c[0]) for c in checks)
    print(f"{ep_id}: {os.path.relpath(mp4, root)}")
    for name, st, val, want in checks:
        print(f"  {st}  {name:{w}}  {val:34}  want {want}")

    for n in notes:
        print(f"  NOTE  {n}")

    copied = None
    if not a.no_copy:
        dst_dir = os.path.join(root, "channels", a.channel, "episodes", f"{ep_id}-assets")
        os.makedirs(dst_dir, exist_ok=True)
        copied = os.path.join(dst_dir, f"{ep_id}.mp4")
        shutil.copy2(mp4, copied)
        print(f"  copied -> {os.path.relpath(copied, root)}")

    for at in a.strip:
        out = strip(mp4, at, os.path.join(ep_dir, "renders", f"strip_{at:g}s.png"))
        print(f"  motion strip -> {os.path.relpath(out, root)}")

    # metrics block at the top of REVIEW.md (notes below it are kept)
    rv = os.path.join(ep_dir, "REVIEW.md")
    block = (f"{BEGIN}\nRender: {os.path.relpath(mp4, ep_dir)} · {d:.1f} s · {lufs} LUFS · peak {peak} dB · loop SSIM "
             f"{ssim:.3f} · {info['width']}x{info['height']} {info['fps']} fps\n"
             + "".join(f"- {st} {name}: {val}\n" for name, st, val, _ in checks) + END)
    old = open(rv).read() if os.path.exists(rv) else f"# {ep_id} review\n\n"
    if BEGIN in old and END in old:
        new = old[:old.index(BEGIN)] + block + old[old.index(END) + len(END):]
    else:
        lines = old.split("\n", 1)
        new = lines[0] + "\n" + block + "\n" + (lines[1] if len(lines) > 1 else "")
    open(rv, "w").write(new)
    print(f"  REVIEW.md metrics updated")

    failed = [c for c in checks if c[1] == "FAIL"]
    print("QA " + ("FAILED: " + ", ".join(c[0] for c in failed) if failed else "passed"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
