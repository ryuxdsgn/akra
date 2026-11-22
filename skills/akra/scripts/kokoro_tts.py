#!/usr/bin/env python3
"""Local Kokoro-82M voiceover for akra episodes (Apache-2.0 weights: commercial use allowed).

Setup once (from the project root):
  uv venv --python 3.12 .venv-kokoro
  uv pip install --python .venv-kokoro/bin/python "kokoro>=0.9.4" soundfile

  .venv-kokoro/bin/python kokoro_tts.py <episode.json> --out render/<channel-id>/ep-007/assets \
      --text-file tts.txt --voice am_michael [--voice am_fenrir ...] [--speed 1.0]

Per voice it writes voiceover_<voice>.mp3 + transcript_<voice>.json (word timings from Kokoro itself,
same format as `hyperframes transcribe`). With one voice it also copies them to voiceover.mp3 /
transcript.json. Listen, then copy the chosen one over voiceover.mp3 / transcript.json.

Text: --text-file (TTS version: one phrase per line = breath; blank line = dramatic beat, +0.45 s) or else the episode `script`.
(pronunciation hints) are dropped and CAPS emphasis is lowered (Kokoro would spell it out).
Emotion map: a line may start with one emotion tag, e.g. "[tense] The pressure keeps rising." Kokoro has no
emotion control, so the tag sets that line's pace and the pause after it (EMOTIONS below; tag applies to that
line only). Tags are never spoken and never count as script words. Unknown tags are read neutrally (warning).
The words must match the episode script one-to-one so captions line up.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SR = 24000
BEAT = 0.45          # extra pause after a line followed by a blank line

# emotion -> (speed multiplier, extra pause after the line in s). English and Indonesian names.
EMOTIONS = {
    "neutral": (1.0, 0.0), "curious": (0.97, 0.15), "tense": (0.93, 0.25), "serious": (0.95, 0.2),
    "surprised": (1.06, 0.3), "excited": (1.08, 0.1), "awe": (0.9, 0.4), "warm": (0.95, 0.2),
    "calm": (0.92, 0.25), "playful": (1.04, 0.1), "relieved": (0.93, 0.3), "urgent": (1.1, 0.05),
}
EMOTIONS.update({"netral": EMOTIONS["neutral"], "penasaran": EMOTIONS["curious"], "tegang": EMOTIONS["tense"],
                 "serius": EMOTIONS["serious"], "kaget": EMOTIONS["surprised"], "semangat": EMOTIONS["excited"],
                 "kagum": EMOTIONS["awe"], "hangat": EMOTIONS["warm"], "tenang": EMOTIONS["calm"],
                 "jahil": EMOTIONS["playful"], "lega": EMOTIONS["relieved"], "mendesak": EMOTIONS["urgent"]})
_EMO = re.compile(r"^\s*\[([a-zA-Z][a-zA-Z ,_-]*)\](?!\()\s*")


def split_emotion(line):
    """'[tense] text' -> ('tense', 'text'); no tag -> (None, line). '[word](+2)' stress markup is not a tag."""
    m = _EMO.match(line)
    return (m.group(1).strip().lower(), line[m.end():]) if m else (None, line)


def emotion_params(tag):
    """(speed multiplier, extra pause) for a tag; the first word of a compound tag ('tense, quiet') counts."""
    if tag is None:
        return EMOTIONS["neutral"]
    key = re.split(r"[ ,]", tag)[0]
    if key not in EMOTIONS:
        print(f"! unknown emotion [{tag}] read as neutral (known: {', '.join(sorted(EMOTIONS))})")
        return EMOTIONS["neutral"]
    return EMOTIONS[key]


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


ACRONYMS = {"QR", "LED", "GPS", "USB", "TV", "DNA", "NASA", "ATM", "PIN", "NFC", "RFID", "CPU", "AI", "UK", "USA", "US", "CO2"}


def prepare(text):
    text = re.sub(r"(?m)^(\s*)\[([A-Za-z][A-Za-z ,_-]*)\](?!\()",                # emotion tags: lowercase,
                  lambda m: f"{m.group(1)}[{m.group(2).lower()}]", text)        # so CAPS emphasis skips them
    text = re.sub(r"(?<!\])\s*\([^)]*\)", "", text)                        # pronunciation hints
    # CAPS emphasis -> Kokoro/misaki stress markup (Kokoro would spell plain caps letter by letter)
    # Real acronyms stay in caps so Kokoro spells them (Q-R, L-E-D); every other CAPS word is emphasis.
    text = re.sub(r"\b([A-Z]{2,}(?:'[A-Z]+)?)\b",
                  lambda m: m.group(1) if m.group(1) in ACRONYMS else f"[{m.group(1).lower()}](+2)", text)
    return text


def plain(text):
    text = "\n".join(split_emotion(ln)[1] for ln in text.split("\n"))     # drop emotion tags
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)                    # drop [word](+2) markup


def synth(pipe, text, voice, speed):
    import numpy as np
    audio, words, offset = [], [], 0.0
    # One line at a time so we know where the blank lines are: a blank line = a dramatic beat (+BEAT s).
    # ("..." inside a line barely pauses in Kokoro; use a new line or a blank line for a real pause.)
    lines, extra, mult = [], [], []
    for ln in text.split("\n"):
        if ln.strip():
            tag, say = split_emotion(ln.strip())
            m, pause = emotion_params(tag)
            lines.append(say.strip())
            extra.append(pause)
            mult.append(m)
        elif extra:
            extra[-1] += BEAT
    results = [(r, extra[i]) for i, ln in enumerate(lines)
               for r in pipe(ln, voice=voice, speed=speed * mult[i], split_pattern=r"\n+")]
    for r, beat in results:
        a = r.audio.cpu().numpy() if hasattr(r.audio, "cpu") else np.asarray(r.audio)
        # Kokoro pads every line with ~0.25 s of silence on each side: trim it (keep 40 ms),
        # otherwise every sentence break is the same ~0.6 s and the read ticks like a metronome.
        loud = np.flatnonzero(np.abs(a) > 0.02 * np.abs(a).max())
        lead = max(0, loud[0] - int(0.04 * SR)) if len(loud) else 0
        a = a[lead:(loud[-1] + int(0.04 * SR)) if len(loud) else len(a)]
        for t in r.tokens or []:
            if t.start_ts is None or not re.search(r"[A-Za-z0-9]", t.text):
                continue
            s, e = t.start_ts - lead / SR, (t.end_ts or t.start_ts) - lead / SR
            words.append([t.text, offset + max(0.0, s), offset + min(len(a) / SR, e)])
        # breath between lines: longer after a long sentence or a colon/question, shorter after a short one
        n = len(r.graphemes.split())
        g = 0.16 + min(0.22, 0.018 * n) + (0.1 if r.graphemes.rstrip()[-1:] in "?:" else 0.0) + beat
        gap = np.zeros(int(g * SR), dtype=a.dtype)
        audio += [a, gap]
        offset += (len(a) + len(gap)) / SR
    return np.concatenate(audio[:-1]), words


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode")
    ap.add_argument("--out", required=True)
    ap.add_argument("--text-file")
    ap.add_argument("--voice", action="append", required=True)
    ap.add_argument("--speed", type=float, default=1.0)
    a = ap.parse_args()

    ep = json.load(open(a.episode))
    text = prepare(open(a.text_file, encoding="utf-8").read() if a.text_file else ep["script"])
    script_words = [norm(w) for w in ep["script"].split() if re.search(r"[A-Za-z0-9]", w)]
    text_words = [norm(w) for w in plain(text).split() if re.search(r"[A-Za-z0-9]", w)]
    if script_words != text_words:
        for k, (x, y) in enumerate(zip(script_words, text_words)):
            if x != y:
                sys.exit(f"text differs from the episode script at word {k}: script '{x}' vs text '{y}'")
        sys.exit(f"text has {len(text_words)} words, script has {len(script_words)}")

    import soundfile as sf
    from kokoro import KPipeline
    os.makedirs(a.out, exist_ok=True)
    pipe = KPipeline(lang_code="a" if all(v[0] == "a" for v in a.voice) else "b", repo_id="hexgrad/Kokoro-82M")
    for voice in a.voice:
        audio, words = synth(pipe, text, voice, a.speed)
        # Kokoro tokens can split or merge words ("doesn't" -> "does" "n't"); map onto the script words.
        merged, cur = [], None
        for w, s, e in words:
            cur = [cur[0] + w, cur[1], e] if cur else [w, s, e]
            target = script_words[len(merged)] if len(merged) < len(script_words) else None
            if target is None or norm(cur[0]) == target or not target.startswith(norm(cur[0])):
                merged.append(cur)
                cur = None
        if cur:
            merged.append(cur)
        if len(merged) != len(script_words):
            print(f"! {voice}: {len(merged)} timed words vs {len(script_words)} script words; "
                  "use `npx hyperframes transcribe` for this take")
        wav = os.path.join(a.out, f"voiceover_{voice}.wav")
        mp3 = wav[:-4] + ".mp3"
        sf.write(wav, audio, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ar", "44100", "-b:a", "128k", mp3], check=True)
        os.remove(wav)
        out = [{"text": w, "start": round(s, 3), "end": round(e, 3), "id": f"w{i}"} for i, (w, s, e) in enumerate(merged)]
        json.dump(out, open(os.path.join(a.out, f"transcript_{voice}.json"), "w"), indent=2)
        print(f"{voice}: {mp3}  {len(audio) / SR:.2f}s  {len(merged)} words")
    if len(a.voice) == 1:
        v = a.voice[0]
        for src, dst in ((f"voiceover_{v}.mp3", "voiceover.mp3"), (f"transcript_{v}.json", "transcript.json")):
            open(os.path.join(a.out, dst), "wb").write(open(os.path.join(a.out, src), "rb").read())


if __name__ == "__main__":
    main()
