# Third-party assets and dependencies

akra itself is MIT-licensed (see `LICENSE`). This file lists what else it bundles, loads or expects you to install. Where a license could not be confirmed from the repo, it says "verify": check the source before you rely on it.

## Bundled in this repository

| Item | Where | Source | License |
|---|---|---|---|
| `whoosh.wav` (trimmed from "Whoosh_Simple_ER_SFX_4.wav") | `render/_template/assets/sfx/` | Freesound, by Alex_hears_things: https://freesound.org/people/Alex_hears_things/sounds/521047/ | CC0 1.0 (no credit required) |
| `click.wav` | `render/_template/assets/sfx/` | generated for akra (noise transient + decaying sine, Python stdlib `wave`) | Generated for akra; MIT (same as repo) |

Add new sounds to `render/_template/assets/sfx/CREDITS.md` and here when you bundle them. Credit every CC BY sound in the video description.

## Loaded at build or render time (not bundled)

| Item | Used for | Source | License |
|---|---|---|---|
| HyperFrames (npm `hyperframes`, pinned to 0.9.40 in `render/_template/package.json`) | HTML-to-video render, preview, check, snapshot | https://www.npmjs.com/package/hyperframes | Apache-2.0 |
| GSAP 3.15.0 | Animation timelines, loaded from a CDN in the generated `index.html` | https://gsap.com, https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js | GSAP standard license (free to use, including commercial, with restrictions on building competing no-code animation tools). verify at https://gsap.com/standard-license/ |
| Montserrat | Default caption and label font in the template; referenced by name, not bundled | https://fonts.google.com/specimen/Montserrat | SIL Open Font License 1.1 |
| Node.js 22+, ffmpeg, Python 3 | Runtime and tooling | https://nodejs.org, https://ffmpeg.org, https://www.python.org | Installed by you under their own licenses (ffmpeg: LGPL or GPL depending on the build) |

## Optional, installed by you (never bundled)

| Item | Used for | Source | License |
|---|---|---|---|
| Kokoro-82M (and the `kokoro` Python package) | Local text-to-speech (`skills/akra/scripts/kokoro_tts.py`) | https://huggingface.co/hexgrad/Kokoro-82M | Apache-2.0. Commercial use is allowed; check the model card before relying on it. |
| ElevenLabs API | Hosted text-to-speech with your own key (`elevenlabs_tts.py`) | https://elevenlabs.io | Commercial use depends on your plan: check their terms, and do not clone a voice without the owner's consent. |
| Other voice models (`dots_tts.py`, `chatterbox_tts.py`) | Optional local TTS | their own model cards | verify per model. Only use models whose license allows commercial use. |
| Pillow | PNG labels and previews | https://python-pillow.org | MIT-CMU (HPND) |
| Google and Meta APIs | YouTube upload and stats, Facebook/Instagram posting, with your own OAuth keys | https://developers.google.com/youtube, https://developers.facebook.com | Their API terms apply to your use. |

## Music

No music is bundled. Use calm ambient tracks you have the right to use. A good free source is the YouTube Audio Library (https://www.youtube.com/audiolibrary); each track states its attribution requirement, and the credit goes in the video description. akra normalizes the track to -14 LUFS and mixes it at volume 0.1 under the voiceover.
