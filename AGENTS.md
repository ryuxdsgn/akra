# akra: agent working rules (Codex, Antigravity, Claude Code and other agents)

This repo makes faceless YouTube Shorts with the **akra** skill (`skills/akra/SKILL.md`; Codex and Antigravity read it from `.agents/skills/akra`, Claude Code from `.claude/skills/akra`). Read that skill first for any video task, then read only the `references/` file of the mode in use.

**Local user notes:** if `AGENTS.local.md` exists in the repo root, read it too. It holds the channels, schedule and habits of the user of this machine (not committed). Its content overrides the defaults in this file, except "Fixed rules".

**New machine or something errors:** run `python3 tools/doctor.py`; the install guide is in `docs/setup.md`.

## Communication
- Reply to the user in the language the user writes in (default: **English**; `AGENTS.local.md` may set another).
- Video content follows the channel language (`language` in `channel.json`; without it, simple international English).
- Do not write the user's email or personal data to outside services.
- Do not ask the user to paste API keys or tokens into the chat. Point to `.env` (ElevenLabs) and `client_secret.json` + `youtube_upload.py auth` (YouTube).

## Channel
Channel data lives in `channels/<id>/` (local, not committed). Read the active channel's `channel.json` and `style-bible.md` before working: language (`language`), voice (`voice`) and posting slots (`posting_slots` in `timezone`). No channel yet: run the `channel` mode in the skill.

Schedule a new episode in the earliest empty slot that is at least 2 hours from now. Check `scheduled_at` of all that channel's episodes and do not double-book.

## Fixed rules (mandatory)
1. **Never upload without the user's approval for that episode.** Upload through `skills/akra/scripts/youtube_upload.py upload <episode.json> --schedule` (venv `.venv-youtube`; per-channel token `.youtube-<account>-token.json`). Do not upload through the browser.
2. **Git:** commit only if asked. `channels/`, `render/ep-*`, `render/*/ep-*`, `_archive/`, `.env`, `client_secret*.json`, `.youtube-*token.json`, `AGENTS.local.md` must not be committed (do not `git add -f`). The repo only contains the skill, templates, tools, tests and docs.
3. **Voice license:** what decides is the license of the voice **model**, not the app. Do not use a non-commercial model (e.g. OmniVoice, VoiceStudio's built-in engine: its weights are CC-BY-NC) in any app. An app like VoiceStudio may be used only with an engine whose license allows commercial use; record the license in `channel.json` → `voice.license`, `license_url`, `license_checked`. Voice cloning only with the voice owner's permission. Voice and music credits are always written in the description.
4. **Music:** calm ambient from the YouTube Audio Library (example: "Pulsar" by The Grey Room / Density & Time), loudnorm −14 LUFS, volume 0.1, credit in the description.
5. **Facts and health:** every factual claim has a source. For health or fitness channels: no "cures" claims, a doctor disclaimer is required, and follow the movement limits in that channel's `style-bible.md`.
6. Do not install a large local AI model without the user's permission (many users have 8 GB RAM laptops).
7. **Work on videos serially.** Only one episode is built or rendered at a time: TTS, snapshot, render and QA. If asked for more than one video (a batch or revisions of several episodes), finish one episode completely (render, `qa_render.py` PASS, validation `OK`), then start the next. Do not run several agents or build/render processes at once, so RAM does not run out. Writing scripts for several episodes at once is still fine, because it is light.

## Build flow (HyperFrames 0.9.40, Node 22+)
- Episode project: `render/<channel-id>/<ep-id>/`, copied from `render/_template/`. (`render/<ep-id>/` without a channel folder is the legacy layout, `"render_layout": "flat"` in `channel.json`.) Reusable items you registered come from `library/` through `Library` (optional, see `skills/akra/references/library.md`).
- After each scene change: `npx --yes hyperframes@0.9.40 check`, then `snapshot --at ...`, and look at the frames before rendering.
- Render: `npx --yes hyperframes@0.9.40 render`, then `python3 skills/akra/scripts/qa_render.py <project> --channel <id>` must PASS (loudness −15.5..−12.5 LUFS, loop SSIM ≥ 0.95, duration, format, no silent gaps).
- Package validation: `python3 skills/akra/scripts/validate_episode.py validate channels/<id>/episodes/<ep>.json` must be `OK`.
- Repo tests: `python3 -m unittest discover -s tests`.
- Many ffmpeg builds lack `drawtext`/libass: use PNG labels from Pillow. Do not rely on numpy in the system Python.

## Characters
Characters are drawn as SVG in the scenes, or come from items you registered with `library.lib.Library` (see `skills/akra/references/library.md`; if `skills/akra/references/` holds a `rig*.md` file, it covers the rig of this installation). `character.py` and `mocap.py` in the template are only shims for an optional rig in `library/rig/`. A character's mouth only moves while that character speaks. Each channel's style and brand assets are in `style-bible.md` and `channels/<id>/brand/`.
