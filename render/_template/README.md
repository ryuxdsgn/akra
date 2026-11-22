# akra episode template (HyperFrames)

Extracted from a first explainer episode. Copy this folder for every new episode.

| File | What it is | Edit per episode? |
|---|---|---|
| `channelcfg.py` | Which channel the folder belongs to (`render/<channel-id>/ep-*` = that channel; `render/ep-*` only for the one channel with `"render_layout": "flat"`) and its `brand` / `language` from `channels/<id>/channel.json` | No |
| `hf.py` | Shared builder: brand colours, layout, SVG helpers (`text`, `label`, `show`, `hide`, `pulse`, `spring`, `arrow_down`), scene wrapper, word-by-word captions, voiceover + SFX tracks, root `index.html` | No. Fix it here and copy it to the episode folders |
| `build.py` | Scene functions `sNN(p, d, shot)`, `SCENES`, `SFX` cues | Yes |
| `depth.py` | Cinematic depth (style v3): 4 blurred layers, bloom, light beams, hero key/rim light, grade, vignette, grain, and `bake()` for static layers to PNG | No. Shared like `hf.py` |
| `scenekit.py` | Shared episode boilerplate: `load`/`timer`/`abs_t` (episode + word timings), GSAP helpers (`pop`, `fade`, `shake`, `push`, `move`, `bob`, `show_now`), text (`t`, `BRAND`, `banner`, `pill`), `bake_envs` (baked backgrounds) and `finish` (top band, caption band, grade, grain) | No. Shared like `hf.py`; episode props go in `envNN.py` |
| `character.py`, `mocap.py` | Shims that put the repo `library/` (or the episode's `_lib_frozen/`) on `sys.path` and load an optional character rig from `library/rig/`. No rig ships: without one, any rig helper raises a clear error, and you draw characters in the scene functions (see `skills/akra/references/library.md`) | No |
| `assets/sfx/` | Reusable sounds (`click`, `whoosh`) + `CREDITS.md` | Add sounds when you need them |
| `package.json` | Pinned `hyperframes@0.9.40` scripts | No |

## New episode

```bash
cp -r render/_template render/<channel-id>/ep-002         # folder name = episode id
cd render/<channel-id>/ep-002
python3 build.py && npm run check             # works straight away: every shot is a storyboard card
```

`build.py` reads `channels/<channel>/episodes/<folder name>.json`; the channel comes from the folder layout (`channelcfg.py`). Run inside `_template` itself, it builds `skills/akra/templates/episode.example.json` as a demo.

## Voiceover and timing

```bash
# assets/voiceover.mp3 from ElevenLabs (channel voice)
ffmpeg -v error -y -i assets/voiceover.mp3 -af loudnorm=I=-15:TP=-1.5:LRA=11 -ar 48000 assets/voiceover_norm.wav
npx --yes hyperframes@0.9.40 transcribe assets/voiceover.mp3 --engine whisper --model small.en -l en
mv transcript.json assets/transcript.json
```

- Retime `shots[]` to the word timings, then set `vo_duration` and validate the episode.
- Captions use the script text matched to the timings by word **position**. If the word counts differ, `build.py` stops; fix the transcript and run it again.
- Until the transcript and voiceover exist, captions use estimated timings and the build is silent. That is enough for an animatic.

## Drawing scenes

- Write one `sNN(p, d, shot)` for each shot, in time order. Each returns `(svg, js)`, and timeline times are **local** to the scene.
  - Prefix every id with `p`.
  - Shots with no function yet stay storyboard cards.
- Use **one diagram that grows**: shared drawing functions and fixed coordinates, so the same object stays in place from scene to scene.
- Labels appear on a part as the voice names it.
- The last frame should equal the first, so the Short loops cleanly.
- Ground the viewer first: show the everyday object, then zoom into the mechanism. For example, a front view of the object, then a callout into its cutaway.
- Text stays inside the 168–1330 px band. The diagram area is `ART_TOP`–`ART_BOTTOM`, and captions sit at `CAP_TOP` on one line of at most 20 characters.
- Cinematic depth: see the docstring at the top of `depth.py`. Bake static layers (`depth.bake`) and keep only the hero, diagrams and small parallax live; put the channel brand inside the scene because the background covers the whole frame.
- Characters (optional): draw people as cartoon SVG in the scene functions, not silhouettes. One look per person per episode, one pose per story beat triggered on a narration word, unique ids (never reuse a pill id). See `skills/akra/references/build.md` (Characters).
- Real objects: draw the hero as the real thing (3/4 view, close camera, material, small details) and put the explanation on top. Helpers in `depth.py`: `material`, `sheen`, `texture`, `data_overlay`, `soft_steam`, `perspective`, `plate` (banner/badge with shadow clipped to its rounded shape). Before render, crop every scene at ~2x and look for unintended overlaps (see build.md QA).

## QA and render

1. `python3 build.py && npm run check`. It must pass with 0 errors. The only expected warning is `composition_file_too_large` on `captions.html`.
2. Run `npx --yes hyperframes@0.9.40 snapshot --at <hook>,<each seam>,<end>` and **look** at the frames.
3. Render with `npm run render`, then run `python3 ../../skills/akra/scripts/qa_render.py . --strip <seconds>`. It checks loudness (~-14 LUFS, peak <= -0.9 dB), loop SSIM, duration, format and silence gaps, copies the MP4 to `channels/<id>/episodes/<ep>-assets/<ep>.mp4`, and writes the metrics block at the top of `REVIEW.md`. Look at the motion strip.
4. Under the metrics block in `REVIEW.md`, write the creative calls, fixes, the weakest shot, and credits.
