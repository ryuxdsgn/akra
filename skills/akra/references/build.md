# Mode `build`: voiceover → HyperFrames → render

## Model per step (read first)
Use the cheapest model that is still enough for each step. Most tokens go into `build` (reading code, iterating, snapshots), so that step does **not** use the most expensive model.

| Step | Model tier | Claude Code | Reason |
|---|---|---|---|
| `niche`, `ideas`, `script`, `shots`, title and description in `package` | strong | Opus | script quality, hook and facts decide the views |
| `build` (TTS, HyperFrames code, snapshot, render, QA) and `review` | medium | Sonnet | many mechanical steps; can look at snapshot images |
| mechanical commands (`validate`, `capacity`, `youtube_upload.py`, `youtube_stats.py pull`) | no subagent | — | one command, run it directly |

**In Claude Code:** the main session (the user picks the model, ideally Opus) writes the script, storyboard and package. For `build`, send **one subagent per episode** with `model: sonnet` named explicitly (without it the subagent inherits the expensive session model). The subagent brief only needs paths, do not paste file contents:
- Episode Package (`channels/<id>/episodes/<ep>.json`), the channel's `style-bible.md`, `references/build.md`, the project folder `render/<channel-id>/<ep-id>/`.
- Definition of done: `qa_render.py` PASS and validation `OK`; return the MP4 path, the QA result and the list of unresolved problems (not the full log).
- The subagent does not upload and does not dispatch other subagents.

`build` subagents stay serial: wait for one to finish before sending the next. The main session then looks at the contact sheet or snapshots before handing the video to the user.

**Other agents** (Codex, Antigravity): if you can pick a model per task, follow the tiers in the table; if not, run everything on one model.

**Measure:** after an episode is done, check the session's token cost per model in your agent's usage report. Target: under $3 per video.

Claude builds the video. The user only makes the voiceover (when the TTS needs a user account) and watches the final result to approve it. No CapCut.

Before starting, **load the `hyperframes` skill** (and `hyperframes-cli`, `media-use` if needed). That skill holds the render rules; this file only holds the channel rules.

## 1. Voiceover
- Use the TTS version of the text from the `script` mode (`channels/<id>/episodes/<ep>-assets/tts.txt`) and the channel's fixed voice (Channel Profile → `voice`).
- **License first:** the voice is used on a monetized channel, so the TTS model or service must allow commercial use. Keep the license proof (model card / terms page, with the check date) in `channels/<id>/licenses/` and fill `voice.license`, `voice.license_url`, `voice.license_checked` in the Channel Profile. The ElevenLabs free plan is **not** commercially licensed.
- **Kokoro-82M (default, local, free, Apache-2.0):**
  - One-time setup from the project root: `uv venv --python 3.12 .venv-kokoro` then `uv pip install --python .venv-kokoro/bin/python "kokoro>=0.9.4" soundfile`. If a spaCy error appears, install the `en_core_web_sm` model into that venv. Needs `ffmpeg`.
  - `.venv-kokoro/bin/python skills/akra/scripts/kokoro_tts.py channels/<id>/episodes/<ep>.json --out render/<channel-id>/<ep-id>/assets --text-file <tts.txt> --voice am_fenrir --speed 0.95`
  - The result is `voiceover.mp3` + `transcript.json` with **per-word timing from Kokoro**, so whisper is not needed. Several `--voice` values at once produce one take per voice to compare.
  - The script checks that the words in the TTS text match the script exactly (so captions fit), trims Kokoro's built-in pauses, then adds varied pauses between lines (longer after long sentences, `?` or `:`). Emotion tags at the start of a line (`[tense]`, `[awe]`, …, see script.md) set the pace and pause of that line. Listen first: if a line sounds flat at an important moment, add or change a tag, do not raise `--speed` for the whole video.
  - Light (fine for an 8 GB Mac). Big models like Chatterbox need 16 GB+ RAM.
  - Play the result for the user (`open render/<channel-id>/<ep-id>/assets/voiceover.mp3`) and ask for approval before the build.
- **ElevenLabs (fallback, paid plan only for monetized channels):**
  - Key in `.env` at the project root (`ELEVENLABS_API_KEY=...`, already in `.gitignore`). The user fills it in; never ask for the key to be pasted in chat.
  - `python3 scripts/elevenlabs_tts.py voices` / `models`, then `python3 scripts/elevenlabs_tts.py tts channels/<id>/episodes/<ep>.json --out render/<channel-id>/<ep-id>/assets --text-file <tts.txt> --takes 2`. Every take uses the user's character quota.
- **dots.tts (local, free, Apache-2.0) for non-English channels (e.g. `language: id`):**
  - Setup and commands are in the docstring of `scripts/dots_tts.py` (`.venv-dots/`, int4 weights in `.models/dots-tts-mlx/`, both in `.gitignore`).
  - `.venv-dots/bin/python skills/akra/scripts/dots_tts.py channels/<id>/episodes/<ep>.json --out render/<id>/<ep-id>/assets --ref channels/<id>/voice_ref.wav --ref-text-file channels/<id>/voice_ref.txt --text-file <tts.txt>`
  - About 1.5 minutes per line on an M1 8 GB (peak ~6 GB per line, which is why it runs per line). Close heavy apps first.
  - Word timing comes from whisper (`hyperframes transcribe`, channel language); lines whose word count does not match use an estimate and are reported, so check those captions.
- **ElevenLabs cast (channel with several characters):** one voice per character. `python3 skills/akra/scripts/elevenlabs_tts.py cast <ep.json> --out render/<channel>/<ep>/assets --text-file channels/<id>/episodes/<ep>-assets/tts.txt --speed 1.06`; lines start with `NARRATOR:`/`<CHARACTER NAME>:` (names from `voice.cast`; untagged lines go to the first cast entry), `[pause N]` for N seconds of silence (e.g. between counted reps). The transcript has a `speaker` field for per-character lip-sync. Very short lines in an Indonesian channel can sound like Malay: regenerate them with `--lang id --lang-lines <line numbers, starting at 0>`; other lines stay from the cache.
- **Other TTS / manual:** save the MP3 as `render/<channel-id>/<ep-id>/assets/voiceover.mp3`, then transcribe it to get **per-word timing** (see the `media-use` skill) and save it as `assets/transcript.json`.
- Adjust `t_start`/`t_end` in `shots[]` to the real word timing, fill `vo_duration` with the MP3 duration (ffprobe), then validate again.
- Captions use the script text, not the whisper text; match words to timing by **position** (whisper can mishear, e.g. "used" → "use").

## 2. HyperFrames project
- One project per episode in `render/<channel-id>/<ep-id>/` (`render/<ep-id>/` without a channel folder is the legacy layout, `"render_layout": "flat"` in `channel.json`), copied from the template `render/_template/` (`cp -r render/_template <folder>`). Read `render/_template/README.md`. Brand (colors, font, brand text, language) is read from `brand`/`language` in the Channel Profile through `channelcfg.py`.
- Template files:
  - `hf.py` = the shared part (brand, layout, captions, audio, index). Do not change it per episode.
  - `build.py` = scenes `sNN(p, d, shot)`, `SCENES`, `SFX`. Shots not drawn yet show as storyboard cards, so the project can be built and previewed right away.
  - `scenekit.py` = shared helpers, do not copy them again per episode:
    - episode data: `load`, `timer` (`at(shot, "word")`), `abs_t` for SFX;
    - timeline: `pop`, `fade`, `shake`, `push`, `move`, `bob`, `show_now`;
    - text: `t`, `BRAND`, `banner`, `pill`;
    - background: `bake_envs` (backgrounds baked to PNG) and `finish` (top band, caption band, grade, grain).

    `build.py` should only hold the scenes of that episode. Put the episode's props and environments in `envNN.py`.
  - Start from the template's `build.py`: every shot is a storyboard card until you give it a scene function.
- `build.py` reads the Episode Package (`shots[]`) and `assets/transcript.json`, then produces `index.html`.
- **Reusable items (optional):** environments and other items you registered with the library engine come from `Library` (`L = Library(HERE, channelcfg.locate(HERE)[1])`; see `references/library.md`). Everything else is drawn in the episode's scene functions.
- Each `diagram` scene = one animation block (HTML/SVG + GSAP) following the shot description and the style bible.
- **Lighting for cartoon channels** (optional; only if `channel.json` has `"lighting"` and this installation has `references/lighting.md`): soft room + light on the characters, see that file.
- **Cinematic depth** (if the style bible asks for it): use `depth.py` from the template.
  - `depth.layers()` builds far/mid/near layers with blur, bloom and light spots.
  - `depth.hero_light()` + `depth.cast_shadow()` give a warm key light, cyan rim light, bottom shadow and a cast shadow on the main object.
  - `depth.grade()` adds color grade, vignette and grain.
  - **Bake static layers** with `depth.bake()`: the background (far + mid) becomes one PNG, the near layer becomes a separate transparent PNG in front of the main object. SVG blur is recomputed every frame, so only the main object, the diagram and small parallax are left live. PNGs are stored in `assets/bg/` and only re-rendered when the picture changes (needs Google Chrome).
  - The background covers the whole frame, so the channel brand is drawn inside the scene.
- **Real objects** (if the style bible asks for it). Helpers are in `depth.py`:
  - `material(p, eid, "steel"|"chrome"|"ceramic"|"plastic"|"glass"|"wood"|"rubber")` → material gradient. Fill it with the object's shape, then `hero_light()` on top.
  - `sheen(p, eid, d, box)` → a gloss strip GSAP can slide (`#{p}-{eid}-hl`) so the object feels like it turns or moves.
  - `texture(p, eid, d)` → fine noise for metal, paper, food. Static, so better baked.
  - `data_overlay(p, eid, d, bands)` → a thermal, pressure or flow layer clipped to the object's shape; each band (`-b0`, `-b1`, …) is switched on one at a time.
  - `soft_steam(p, eid, x, y)` → blurred steam; `perspective(points)` → far edge for a 3/4 look.
  - `plate(p, eid, x, y, w, h, fill, rot)` → rounded banner/badge plate; shadow and bevel are clipped to its shape (put the text on top).
  - Object drawing order: cast shadow → shape + material → texture → `hero_light` → small details → gloss → overlay → arrows and labels.
- **Characters (optional, if a scene contains people).** No character rig ships with akra. Draw people as SVG in the scene functions (or in `envNN.py` helpers), or register your own items and rig with the library engine (`references/library.md`). Either way:
  - One fixed look per character (hair, clothes, accessories) in all of the episode's scenes, defined once and reused.
  - One clear pose or gesture per story beat, triggered on a narration word (`at(shot, "word")`); deliberate stillness beats constant motion.
  - The mouth moves only while that character speaks on screen; the narrator never moves a character's mouth.
  - **IDs must be unique:** a character's id must not equal a pill/banner id (e.g. pill `{p}-dw` + character `{p}-wr`), because `fade()` on the pill would also hide the character.
  - A character does not replace the object being explained: they point at, hold or react to it.
  - If `references/` holds a `rig*.md` file, follow it for the rig API.
- `stock` shots (if any) are added as media clips from `assets/`, with the source credit in the description.

## 3. Required layers (same in every episode)
Policy gate: YT-COPY-1, YT-COPY-2, YT-SYN-1, YT-SHORT-1 in youtube-policy.md.
- **Word-by-word captions:** from `assets/transcript.json`, at most 3–4 words shown at once, the word being spoken lights up in the accent colour. Position bottom-center, outside the YouTube button area (right side and bottom 20%).
- **Voiceover** as the main audio track.
- **Music** from `music_source` (YouTube Audio Library or licensed): save it as `assets/music.mp3`, `hf.py` adds it automatically (volume 0.1, about −20 dB below the voice). Keep the license proof if `licensed`.
- 2–4 soft sound effects at key moments (optional).
- Footer with the active channel's brand text (`brand.text`) and the brand background from the style bible.

## 4. QA before render
1. `npm run check` must pass without errors.
2. `npx hyperframes snapshot` at several points (opening, each scene change, closing), then **look at the images**: text is readable and not cut off, captions do not collide with labels, the diagram is accurate.
   - With cinematic depth, also check: the main object is the **sharpest** thing in the frame; the main object stays in the diagram area (y 250–1170) and is not covered by captions; banners/labels do not sink into the bokeh; frame edges are not dark or transparent because of blur.
   - With real objects, also check: cover the label, is the object still recognized right away? Does the overlay still show the object underneath? No plain boxes for everyday objects. Small details do not collide with labels, timers or captions.
   - **Vector cleanliness (no accidental overlaps).** Crop details of each scene (zoom ~2×) and check:
     - Shadows, highlights and bevel strips do not leave the rounded corners of their shape: clip to the same shape (`depth.plate()` for banners/badges), a cast shadow = the same shape shifted, not a rectangle.
     - Text does not cut through the lines/circles of its container (e.g. writing inside a meter: enlarge the circle or move the text).
     - Badges, icons (radiation symbol, X) and pills do not touch or cover the edge of the main object/label; keep a gap ≥ 20 px or place them clearly inside.
     - Banners/pills do not hit the channel brand (y≈228) above them; tilted banner: compute its top end (y − h/2 − w/2·sin rot).
     - Two objects side by side (lens + alarm, etc.) do not overlap each other, including glow and at the largest animation scale.
     - Sound waves/rings may be behind a banner, but the banner does not cover the object being explained.
     Fix one, then look for the same pattern in all scenes (the same helper is used in many places).
   - **Characters:** snapshot right after each pose change and in the middle of the scene, then check: joints stay connected (shoulder, elbow, neck, hip) without gaps; the hand reaches its target (chin on `think`, object on `point`); eyelids fully close on a blink and only one mouth shows; the face is not covered by a pill/banner/caption; the pose silhouette reads at phone size; the character does not disappear mid-scene (sign of an id clash).
3. Watch it muted: can it still be understood through the diagram and captions?

## 5. Render
- **Serial:** only one episode is built, snapshotted or rendered at a time (Mac 8 GB RAM). For several episodes, finish one (render + QA PASS + validation `OK`) before starting the next.
- Render MP4 **1080×1920**, 30 fps, to `render/<channel-id>/<ep-id>/renders/`.
- QA after render, one command: `python3 skills/akra/scripts/qa_render.py render/<channel-id>/<ep-id> --strip <seconds of a moving scene>`.
  - This script checks loudness (-15.5..-12.5 LUFS, peak ≤ -0.9 dB), loop SSIM (≥ 0.95), duration against `vo_duration`, format 1080×1920 30 fps + audio, and no silence > 1.2 seconds.
  - Then it copies the MP4 to `channels/<channel-id>/episodes/<ep-id>-assets/<ep-id>.mp4`.
  - The metrics block at the top of `REVIEW.md` is written or updated; the notes below it stay safe.
  - Exit 1 on any FAIL: fix, then render again.
  - The 6-frame strip (`renders/strip_<t>s.png`) must be **looked at** to check motion smoothness.
- Write below the `REVIEW.md` metrics block: creative decisions, fixes made during QA, the weakest shot and credits.
- Change the episode status to `edited`.
- **The user watches and approves** before moving on to `package`. Revisions go back to step 2.
