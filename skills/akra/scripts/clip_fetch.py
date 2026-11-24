#!/usr/bin/env python3
"""Clipper mode source tools: fetch only what you need from a streamer's VOD, then find moments.

Saves bandwidth and disk: download the audio first (~1 MB per minute), find the moments from it,
then download only the video sections you will use.

usage:
  python3 clip_fetch.py info    <url>                         # title, channel, duration, heatmap peaks
  python3 clip_fetch.py audio   <url> <clip-dir>              # -> <clip-dir>/raw/audio.m4a
  python3 clip_fetch.py moments <clip-dir> [--top 8] [--lang id] [--no-whisper]
  python3 clip_fetch.py section <url> <clip-dir> START END [--height 1080]
                                                             # -> <clip-dir>/source/<START>.mp4 with the VOD audio
Needs yt-dlp and ffmpeg. faster-whisper (small model, about 0.5 GB) is optional for transcripts;
never load medium or large on an 8 GB machine. No numpy.
"""
import argparse, json, math, re, shutil, subprocess, sys
from pathlib import Path

HYPE = re.compile(
    r"\b(no way|oh my god|omg|wait|bro|let'?s go|holy|insane|crazy|wtf|dude|run|"      # en
    r"anjir|anjay|gila|buset|waduh|astaga|wkwk\w*|cuy|bang|kabur|lari|mampus|aduh|hah|loh|lho)\b", re.I)


def ytdlp():
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        sys.exit("yt-dlp not found: pip install yt-dlp")


def hms(s):
    s = parse_t(s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:04.1f}" if s >= 3600 else f"{int(s // 60)}:{s % 60:04.1f}"


def parse_t(v):
    if isinstance(v, (int, float)):
        return float(v)
    parts = [float(p) for p in str(v).split(":")]
    return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))


def info(url):
    j = json.loads(subprocess.run(ytdlp() + ["-j", "--no-warnings", url], capture_output=True, text=True, check=True).stdout)
    keep = {k: j.get(k) for k in ("id", "title", "channel", "uploader_id", "webpage_url", "duration", "view_count",
                                   "upload_date", "was_live", "license")}
    hm = sorted(j.get("heatmap") or [], key=lambda x: -x["value"])[:8]
    keep["heatmap_top"] = [{"start": round(x["start_time"]), "end": round(x["end_time"]), "value": round(x["value"], 2)}
                           for x in hm]
    return keep


def audio(url, d):
    d = Path(d); (d / "raw").mkdir(parents=True, exist_ok=True)
    meta = info(url)
    (d / "raw" / "info.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    subprocess.run(ytdlp() + ["-f", "140/bestaudio[ext=m4a]/bestaudio", "-o", str(d / "raw" / "audio.%(ext)s"),
                              "--no-warnings", url], check=True)
    print(d / "raw" / "audio.m4a")


def loudness(path):
    """Momentary loudness per second from ffmpeg ebur128 (no numpy)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=metadata=1,"
                        "ametadata=print:key=lavfi.r128.M", "-f", "null", "-"], capture_output=True, text=True)
    per, t = {}, None
    for line in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1)); continue
        m = re.search(r"lavfi\.r128\.M=(-?[\d.]+|-inf)", line)
        if m and t is not None:
            v = float(m.group(1)) if m.group(1) != "-inf" else -70.0
            per.setdefault(int(t), []).append(v)
    n = max(per) + 1 if per else 0
    return [max(per.get(i, [-70.0])) for i in range(n)]


def transcribe(path, lang, d):
    out = d / "raw" / "transcript.json"
    if out.exists():
        return json.loads(out.read_text())
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper not installed: moments use loudness and heatmap only")
        return []
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(path), language=lang, word_timestamps=True, vad_filter=True)
    words = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for s in segs for w in (s.words or [])]
    out.write_text(json.dumps(words, ensure_ascii=False))
    return words


def moments(d, top, lang, use_whisper, min_len=15, max_len=35):
    d = Path(d)
    a = d / "raw" / "audio.m4a"
    meta = json.loads((d / "raw" / "info.json").read_text()) if (d / "raw" / "info.json").exists() else {}
    loud = loudness(a)
    n = len(loud)
    if not n:
        sys.exit("could not read loudness")
    mean = sum(loud) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in loud) / n) or 1
    score = [max(0.0, (x - mean) / sd) for x in loud]
    for h in meta.get("heatmap_top", []):
        for s in range(h["start"], min(h["end"] + 1, n)):
            score[s] += 3 * h["value"]
    words = transcribe(a, lang, d) if use_whisper else []
    for w in words:
        if HYPE.search(w["w"]) and int(w["s"]) < n:
            score[int(w["s"])] += 1.5
    # best non-overlapping windows
    win = 20
    sums = [sum(score[i:i + win]) for i in range(max(1, n - win))]
    picks, used = [], set()
    for i in sorted(range(len(sums)), key=lambda k: -sums[k]):
        if len(picks) >= top:
            break
        s0, s1 = max(0, i - 5), min(n, i + win + 5)
        if any(x in used for x in range(s0, s1)):
            continue
        used.update(range(s0, s1))
        picks.append((s0, min(s1, s0 + max_len)))
    lines = [f"# Moments: {meta.get('title', a.name)}", f"source: {meta.get('webpage_url', a)}  creator: {meta.get('channel', '?')}",
             f"signals: loudness{', heatmap' if meta.get('heatmap_top') else ''}{', transcript' if words else ''}", ""]
    for k, (s0, s1) in enumerate(sorted(picks), 1):
        said = " ".join(w["w"] for w in words if s0 <= w["s"] < s1)
        peak = max(range(s0, s1), key=lambda i: score[i])
        lines += [f"## {k}. {hms(s0)}-{hms(s1)} ({s1 - s0}s)  peak {hms(peak)}", f"> {said or '(no transcript)'}", ""]
    out = d / "moments.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(out)


def section(url, d, start, end, height):
    d = Path(d); (d / "source").mkdir(parents=True, exist_ok=True)
    s0, s1 = parse_t(start), parse_t(end)
    tag = f"{int(s0 // 60):02d}{int(s0 % 60):02d}"
    vid = d / "raw" / f"video_{tag}.mp4"
    (d / "raw").mkdir(exist_ok=True)
    subprocess.run(ytdlp() + ["-f", f"bv*[height<={height}][vcodec^=avc1]/bv*[height<={height}]", "--download-sections",
                              f"*{s0}-{s1}", "-o", str(vid), "--no-warnings", url], check=True)
    out = d / "source" / f"{tag}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vid), "-ss", f"{s0}", "-t", f"{s1 - s0}",
                    "-i", str(d / "raw" / "audio.m4a"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)], check=True)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("info"); p.add_argument("url")
    p = sp.add_parser("audio"); p.add_argument("url"); p.add_argument("dir")
    p = sp.add_parser("moments"); p.add_argument("dir"); p.add_argument("--top", type=int, default=8)
    p.add_argument("--lang", default=None); p.add_argument("--no-whisper", action="store_true")
    p = sp.add_parser("section"); p.add_argument("url"); p.add_argument("dir"); p.add_argument("start"); p.add_argument("end")
    p.add_argument("--height", type=int, default=1080)
    a = ap.parse_args()
    if a.cmd == "info":
        print(json.dumps(info(a.url), indent=1, ensure_ascii=False))
    elif a.cmd == "audio":
        audio(a.url, a.dir)
    elif a.cmd == "moments":
        moments(a.dir, a.top, a.lang, not a.no_whisper)
    else:
        section(a.url, a.dir, a.start, a.end, a.height)


if __name__ == "__main__":
    main()
