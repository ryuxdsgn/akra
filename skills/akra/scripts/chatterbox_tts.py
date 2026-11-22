#!/usr/bin/env python3
"""Local Chatterbox voiceover for akra episodes (MIT weights: commercial use allowed; output carries
Resemble AI's inaudible Perth watermark). More expressive than Kokoro via --exaggeration.

Setup once (from the project root):
  uv venv --python 3.11 .venv-chatterbox
  uv pip install --python .venv-chatterbox/bin/python chatterbox-tts

  .venv-chatterbox/bin/python chatterbox_tts.py <episode.json> --out render/<channel-id>/ep-007/assets \
      --text-file tts.txt --ref voice_ref.wav --exaggeration 0.7 [--exaggeration 0.9] [--cfg 0.3] [--seed 1]

--ref is a clean 10-20 s clip of the channel voice (a licensed TTS voice or your own; never clone a
person without consent). Each line of the text file is generated separately (Chatterbox is steadier on
short chunks) and joined with short pauses that vary with sentence length.
Writes voiceover_ex<value>.mp3 per exaggeration value. Chatterbox gives no word timings: run
`npx hyperframes transcribe` on the chosen take, then check the words against the script.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def prepare(text):
    text = re.sub(r"\s*\([^)]*\)", "", text)                               # pronunciation hints
    text = re.sub(r"\b([A-Z]{2,})\b", lambda m: m.group(1).lower(), text)  # CAPS emphasis
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def trim(a, sr):
    import numpy as np
    loud = np.flatnonzero(np.abs(a) > 0.02 * np.abs(a).max())
    if not len(loud):
        return a
    return a[max(0, loud[0] - int(0.04 * sr)):loud[-1] + int(0.06 * sr)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode")
    ap.add_argument("--out", required=True)
    ap.add_argument("--text-file")
    ap.add_argument("--ref", required=True)
    ap.add_argument("--exaggeration", type=float, action="append", required=True)
    ap.add_argument("--cfg", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    ep = json.load(open(a.episode))
    lines = prepare(open(a.text_file, encoding="utf-8").read() if a.text_file else ep["script"])
    norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))
    sw = [norm(w) for w in ep["script"].split() if re.search(r"[A-Za-z0-9]", w)]
    tw = [norm(w) for w in " ".join(lines).split() if re.search(r"[A-Za-z0-9]", w)]
    if sw != tw:
        sys.exit("text words differ from the episode script")

    import numpy as np
    import soundfile as sf
    import torch
    from chatterbox.tts import ChatterboxTTS
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    _load = torch.load
    torch.load = lambda *x, **k: _load(*x, **{**k, "map_location": torch.device(device)})
    model = ChatterboxTTS.from_pretrained(device=device)
    os.makedirs(a.out, exist_ok=True)
    for ex in a.exaggeration:
        torch.manual_seed(a.seed)
        parts = []
        for ln in lines:
            wav = model.generate(ln, audio_prompt_path=a.ref, exaggeration=ex, cfg_weight=a.cfg)
            seg = trim(wav.squeeze(0).cpu().numpy(), model.sr)
            n = len(ln.split())
            g = 0.16 + min(0.22, 0.018 * n) + (0.1 if ln[-1:] in "?:" else 0.0)
            parts += [seg, np.zeros(int(g * model.sr), dtype=seg.dtype)]
        audio = np.concatenate(parts[:-1])
        wav_path = os.path.join(a.out, f"voiceover_ex{ex:g}.wav")
        sf.write(wav_path, audio, model.sr)
        mp3 = wav_path[:-4] + ".mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-ar", "44100", "-b:a", "128k", mp3], check=True)
        os.remove(wav_path)
        print(f"exaggeration {ex:g}: {mp3}  {len(audio) / model.sr:.2f}s")


if __name__ == "__main__":
    main()
