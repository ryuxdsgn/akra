#!/usr/bin/env python3
"""ElevenLabs voiceover for akra episodes (standard library only).

The API key is read from the ELEVENLABS_API_KEY environment variable or from a `.env` file
(ELEVENLABS_API_KEY=...) in the current folder or any parent folder. Never commit `.env`.

  python3 elevenlabs_tts.py voices                       # list your voices: name + voice_id
  python3 elevenlabs_tts.py models                       # list models: model_id + name
  python3 elevenlabs_tts.py tts <episode.json> --out render/<channel-id>/ep-006/assets \
      --voice-id <id> --model <model_id> [--text-file tts.txt] [--takes 2]

`tts` uses the with-timestamps endpoint and writes, per take k:
  voiceover_take<k>.mp3 + transcript_take<k>.json   (word timings, same format as `hyperframes transcribe`)
and copies take 1 to voiceover.mp3 + transcript.json. Listen to the takes, then copy the best one over
voiceover.mp3 / transcript.json. Each take costs ElevenLabs characters from your plan.

Text: --text-file (the TTS version: ... pauses, CAPS emphasis) or else the episode `script`.
The words must match the episode script one-to-one (punctuation and case may differ) so captions line up.
voice_id / model_id default to channel.json -> voice.voice_id / voice.model_id when present.

Cast mode (several voices, e.g. characters who talk): channel.json -> voice.cast = {"NARRATOR": {"voice_id": ...},
"HOST": {...}, ...} and a --text-file whose lines start with a speaker tag ("HOST: Quick tip first!"; a line
without a tag, or tagged "NARRATOR:", is the first cast entry). One request per line (cached in <out>/.eleven-cache, so re-runs cost
nothing for unchanged lines), lines joined with short gaps; a blank line adds a beat, "[pause 1.5]" adds
1.5 s of silence. Every transcript word gets a "speaker" field, so build.py can lip-sync only that character.
  python3 elevenlabs_tts.py cast <episode.json> --out render/<channel>/ep-001/assets --text-file tts.txt [--seed 1]
Emotion (audio tags, Eleven v3/v4 only): put tags in square brackets in the text, e.g.
"HOST: [teasing, warm] Just one? Start small!" or "[whispers] It is still running." Tags are sent to
ElevenLabs but never count as script words and never reach the transcript/captions. On other models the
tags are stripped (with a warning). "[pause N]" stays a pause, not a tag.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.elevenlabs.io/v1"


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if key:
        return key
    d = os.getcwd()
    while True:
        p = os.path.join(d, ".env")
        if os.path.isfile(p):
            for line in open(p, encoding="utf-8"):
                m = re.match(r"\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*['\"]?([^'\"\s#]+)", line)
                if m:
                    return m.group(1)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    sys.exit("ELEVENLABS_API_KEY not set (environment or .env)")


def call(method, path, body=None, query=""):
    req = urllib.request.Request(f"{API}{path}{query}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read().decode(errors='replace')[:500]}")


TAG_MODELS = ("eleven_v3", "eleven_v4")
_AUDIO_TAG = re.compile(r"\[[^\]]*\]")


def strip_tags(text):
    """Text without [audio tags] (for word checks and for models without tag support)."""
    return re.sub(r"[ \t]{2,}", " ", _AUDIO_TAG.sub(" ", text)).strip()


def supports_tags(model):
    return bool(model) and model.startswith(TAG_MODELS)


def words_from_alignment(al):
    """Character alignment -> [{text, start, end, id}] split on whitespace; [audio tags] are skipped."""
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, t0, t1, depth = [], "", None, None, 0
    for c, a, b in zip(chars, st, en):
        if c == "[":
            depth += 1
        if depth:
            if c == "]":
                depth -= 1
            c = " "
        if c.isspace():
            if cur:
                words.append((cur, t0, t1))
            cur, t0 = "", None
            continue
        if t0 is None:
            t0 = a
        cur += c
        t1 = b
    if cur:
        words.append((cur, t0, t1))
    words = [w for w in words if re.search(r"[A-Za-z0-9]", w[0])]   # drop standalone "..." etc.
    return [{"text": w, "start": round(a, 3), "end": round(b, 3), "id": f"w{k}"} for k, (w, a, b) in enumerate(words)]


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def channel_voice(ep_path, ep):
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(ep_path))), "channel.json")
    if os.path.isfile(p):
        return json.load(open(p)).get("voice", {})
    return {}


def tts(a):
    ep = json.load(open(a.episode))
    voice = channel_voice(a.episode, ep)
    voice_id = a.voice_id or voice.get("voice_id")
    model = a.model or voice.get("model_id")
    if not voice_id or not model:
        sys.exit("need --voice-id and --model (or voice.voice_id / voice.model_id in channel.json)")
    text = open(a.text_file, encoding="utf-8").read() if a.text_file else ep["script"]
    text = re.sub(r"\s*\([^)]*\)", "", text) if a.strip_hints else text   # drop pronunciation hints
    if _AUDIO_TAG.search(text) and not supports_tags(model):
        print(f"! {model} has no audio tags: tags removed")
        text = strip_tags(text)
    script_words = [norm(w) for w in ep["script"].split() if re.search(r"[A-Za-z0-9]", w)]
    text_words = [norm(w) for w in strip_tags(text).split() if re.search(r"[A-Za-z0-9]", w)]
    if script_words != text_words:
        for k, (x, y) in enumerate(zip(script_words, text_words)):
            if x != y:
                sys.exit(f"text differs from the episode script at word {k}: script '{x}' vs text '{y}'")
        sys.exit(f"text has {len(text_words)} words, script has {len(script_words)}")
    os.makedirs(a.out, exist_ok=True)
    body = {"text": text, "model_id": model,
            "voice_settings": {"stability": a.stability, "similarity_boost": a.similarity}}
    for k in range(1, a.takes + 1):
        r = call("POST", f"/text-to-speech/{voice_id}/with-timestamps", body, "?output_format=mp3_44100_128")
        mp3 = os.path.join(a.out, f"voiceover_take{k}.mp3")
        open(mp3, "wb").write(base64.b64decode(r["audio_base64"]))
        words = words_from_alignment(r.get("alignment") or r["normalized_alignment"])
        if len(words) != len(script_words):
            print(f"! take {k}: {len(words)} timed words vs {len(script_words)} script words (check before using)")
        json.dump(words, open(os.path.join(a.out, f"transcript_take{k}.json"), "w"), indent=2)
        print(f"take {k}: {mp3}  {words[-1]['end']:.2f}s  {len(words)} words")
    for src, dst in (("voiceover_take1.mp3", "voiceover.mp3"), ("transcript_take1.json", "transcript.json")):
        open(os.path.join(a.out, dst), "wb").write(open(os.path.join(a.out, src), "rb").read())
    print("take 1 copied to voiceover.mp3 + transcript.json")


SR = 44100
BEAT = 0.45
_TAG = re.compile(r"^\s*([A-Z][A-Z_]{1,20})\s*:\s*(.+)$")
# A line that is only "[pause 1.5]" is 1.5 s of silence. Any one-word tag followed by seconds counts, so the
# pause word can be written in the channel's language.
_PAUSE = re.compile(r"^\s*\[[^\W\d_]+\s+(\d+(?:\.\d+)?)\]\s*$")
DEFAULT_SPEAKER = "NARRATOR"   # tag that always means the default speaker (the first cast entry)


def _speaker(tag, cast):
    """Cast name for a line tag: the name itself, the default speaker for DEFAULT_SPEAKER, or a cast name that
    differs from the tag by one letter (a spelling variant); None when nothing matches."""
    if tag in cast:
        return tag
    if tag == DEFAULT_SPEAKER:
        return next(iter(cast))
    near = [c for c in cast if len(tag) > 4 and _one_letter_apart(tag, c)]
    return near[0] if len(near) == 1 else None


def _one_letter_apart(a, b):
    if abs(len(a) - len(b)) != 1:
        return False
    short, long_ = sorted((a, b), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def cast_lines(text, cast):
    """[(speaker, text, pause_after_s)] from a tagged text file; untagged lines go to the first cast entry."""
    first = next(iter(cast))
    out = []
    for ln in text.split("\n"):
        m = _PAUSE.match(ln)
        if m:
            if out:
                out[-1][2] += float(m.group(1))
            continue
        if not ln.strip():
            if out:
                out[-1][2] += BEAT
            continue
        m = _TAG.match(ln)
        spk = _speaker(m.group(1), cast) if m else None
        if m and spk is None and m.group(1).isupper() and len(m.group(1)) > 2:
            sys.exit(f"unknown speaker {m.group(1)} (cast: {', '.join(cast)})")
        spk, say = (spk, m.group(2)) if spk else (first, ln.strip())
        out.append([spk, say.strip(), 0.0])
    return out


def line_gap(say, spk, nxt):
    """Gap after a line: longer at a speaker change (a breath between characters)."""
    say = strip_tags(say)
    g = 0.14 + (0.08 if say[-1:] in "?!" else 0.0)
    return g + (0.1 if nxt and nxt != spk else 0.0)


def _pcm(mp3_bytes):
    return subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                          input=mp3_bytes, capture_output=True, check=True).stdout


def cast_tts(a):
    ep = json.load(open(a.episode))
    voice = channel_voice(a.episode, ep)
    cast, model = voice.get("cast") or {}, a.model or voice.get("model_id")
    if not cast or not model:
        sys.exit("need voice.cast and voice.model_id in channel.json")
    lines = cast_lines(open(a.text_file, encoding="utf-8").read(), cast)
    if any(_AUDIO_TAG.search(say) for _, say, _ in lines) and not supports_tags(model):
        print(f"! {model} has no audio tags: tags removed")
        lines = [[spk, strip_tags(say), p] for spk, say, p in lines]
    script_words = [norm(w) for w in ep["script"].split() if re.search(r"[A-Za-z0-9]", w)]
    text_words = [norm(w) for _, say, _ in lines for w in strip_tags(say).split() if re.search(r"[A-Za-z0-9]", w)]
    if script_words != text_words:
        k = next((i for i, (x, y) in enumerate(zip(script_words, text_words)) if x != y), min(len(script_words), len(text_words)))
        sys.exit(f"text differs from the episode script at word {k} ({len(text_words)} vs {len(script_words)} words)")
    cache = os.path.join(a.out, ".eleven-cache")
    os.makedirs(cache, exist_ok=True)
    pcm, words, t, used = b"", [], 0.0, 0
    for i, (spk, say, pause) in enumerate(lines):
        v = cast[spk]
        settings = {"stability": v.get("stability", a.stability), "similarity_boost": v.get("similarity", a.similarity)}
        if "style" in v:
            settings["style"] = v["style"]
        if v.get("speed", a.speed) != 1.0:
            settings["speed"] = v.get("speed", a.speed)
        body = {"text": say, "model_id": model, "voice_settings": settings, "seed": a.seed + i,
                "previous_text": lines[i - 1][1] if i and lines[i - 1][0] == spk else None,
                "next_text": lines[i + 1][1] if i + 1 < len(lines) and lines[i + 1][0] == spk else None}
        if a.lang and (a.lang_lines is None or i in a.lang_lines):
            body["language_code"] = a.lang          # very short lines ("Two, open up.", "Relax.") can drift to a neighbouring language
        body = {k: x for k, x in body.items() if x is not None}
        key = hashlib.sha1(json.dumps([v["voice_id"], body], sort_keys=True).encode()).hexdigest()[:16]
        hit = os.path.join(cache, key + ".json")
        if os.path.exists(hit):
            r = json.load(open(hit))
        else:
            r = call("POST", f"/text-to-speech/{v['voice_id']}/with-timestamps", body, "?output_format=mp3_44100_128")
            json.dump(r, open(hit, "w"))
            used += len(say)          # audio tags are billed as characters too
        seg = _pcm(base64.b64decode(r["audio_base64"]))
        lw = words_from_alignment(r.get("alignment") or r["normalized_alignment"])
        head = max(0.0, lw[0]["start"] - 0.05) if lw else 0.0
        tail = min(len(seg) / 2 / SR, (lw[-1]["end"] + 0.15) if lw else len(seg) / 2 / SR)
        seg = seg[int(head * SR) * 2:int(tail * SR) * 2]
        for w in lw:
            words.append({"text": w["text"], "start": round(t + w["start"] - head, 3), "end": round(t + w["end"] - head, 3),
                          "speaker": spk})
        nxt = lines[i + 1][0] if i + 1 < len(lines) else None
        gap = line_gap(say, spk, nxt) + pause if nxt else 0.0
        pcm += seg + b"\0\0" * int(gap * SR)
        t += len(seg) / 2 / SR + gap
        print(f"[{i + 1}/{len(lines)}] {spk}: {say}", flush=True)
    for k, w in enumerate(words):
        w["id"] = f"w{k}"
    os.makedirs(a.out, exist_ok=True)
    mp3 = os.path.join(a.out, f"voiceover_{a.take}.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-i", "pipe:0", "-b:a", "128k", mp3],
                   input=pcm, check=True)
    tr = os.path.join(a.out, f"transcript_{a.take}.json")
    json.dump(words, open(tr, "w"), indent=2, ensure_ascii=False)
    for src, dst in ((mp3, "voiceover.mp3"), (tr, "transcript.json")):
        open(os.path.join(a.out, dst), "wb").write(open(src, "rb").read())
    if len(words) != len(script_words):
        print(f"! {len(words)} timed words vs {len(script_words)} script words (check before using)")
    print(f"take {a.take}: {mp3}  {t:.2f}s  {len(words)} words  ({used} characters billed this run)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("voices")
    sub.add_parser("models")
    t = sub.add_parser("tts")
    t.add_argument("episode")
    t.add_argument("--out", required=True)
    t.add_argument("--voice-id")
    t.add_argument("--model")
    t.add_argument("--text-file")
    t.add_argument("--takes", type=int, default=2)
    t.add_argument("--stability", type=float, default=0.5)
    t.add_argument("--similarity", type=float, default=0.75)
    t.add_argument("--keep-hints", dest="strip_hints", action="store_false", help="keep (pronunciation hints) in the text")
    c = sub.add_parser("cast")
    c.add_argument("episode")
    c.add_argument("--out", required=True)
    c.add_argument("--text-file", required=True)
    c.add_argument("--model")
    c.add_argument("--seed", type=int, default=1)
    c.add_argument("--take", default="cast")
    c.add_argument("--stability", type=float, default=0.5)
    c.add_argument("--similarity", type=float, default=0.75)
    c.add_argument("--speed", type=float, default=1.0, help="speaking rate 0.7-1.2 (a cast entry's own speed wins)")
    c.add_argument("--lang", help="ISO 639-1 language_code to force (e.g. id), so short lines do not drift to a neighbour language")
    c.add_argument("--lang-lines", type=lambda x: {int(k) for k in x.split(",")},
                   help="only these 0-based line numbers get --lang (others keep their cached take)")
    a = ap.parse_args()
    if a.cmd == "cast":
        return cast_tts(a)
    if a.cmd == "voices":
        for v in call("GET", "/voices")["voices"]:
            print(f"{v['voice_id']}  {v['name']}  [{v.get('category', '')}]")
    elif a.cmd == "models":
        for m in call("GET", "/models"):
            print(f"{m['model_id']}  {m.get('name', '')}  tts={m.get('can_do_text_to_speech')}")
    else:
        tts(a)


if __name__ == "__main__":
    main()
