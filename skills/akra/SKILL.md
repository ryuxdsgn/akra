---
name: akra
description: Faceless YouTube Shorts production workflow (30-60s, monetization) for one or more channels, in each channel's language (English for international channels, Indonesian and others via `language` in channel.json), posted to YouTube Shorts and optionally Facebook Reels and TikTok. Routes to channel setup, niche scouting, idea bank, script, diagram storyboard, HyperFrames build (animated diagrams, word-by-word captions, voiceover, music), upload package with QA, and weekly review. Use for "YouTube Shorts", "faceless video", "short video script", "explainer diagram video", "animated character video", "pick a niche", "add a channel", "review my Shorts stats", or "clip a streamer", even when akra is not named.
---

# Akra

A semi-automatic workflow for 30-60 second faceless YouTube Shorts. You write the script and storyboard, then **build the video yourself** as animated diagrams in **HyperFrames** (word-by-word captions, voiceover and music included). The voiceover uses the channel voice (`voice` in the Channel Profile: e.g. local **Kokoro-82M**, Apache-2.0, or paid ElevenLabs). The user watches and approves the render, then you upload and schedule it through the **YouTube Data API** (plus Facebook/Instagram through the Meta Graph API if the channel uses them) once the user agrees. All visuals are built as code in HyperFrames (diagrams, real objects, simple drawn characters); there is no generative AI video.

**Quality principle:** every episode is made specifically (accurate diagram, sourced, one brand), not a template with the keywords swapped. The user always watches before publishing. Never upload without the user's approval for that episode.

## Fixed rules
- **Language:** explain things to the user in the language the user writes in (default: English; a machine-local `AGENTS.local.md` may set another). All video content (script, hook, title, description, hashtags, on-screen text) uses the **channel language** (`language` in the Channel Profile; without that field = simple international **English**). Shot descriptions (`shots[].prompt`) may stay in English (build-only).
- **One active channel:** every mode starts by deciding which channel is being worked on and reading its Channel Profile (`channels/<channel-id>/channel.json`, or a profile the user pastes in chat). If there is no channel yet, run the `channel` mode first.
- **Do not mix channels:** style, voice, ideas and reviews come from the active channel only.
- **Originality is required:** YouTube rejects monetization of repetitive mass-produced content. Every script needs its own angle and added value, not a template with the keywords swapped.
- **Stay monetizable:** pass each mode's gate in references/youtube-policy.md.
- **Facts:** include a source for every factual claim. If unsure, mark it "check first" and do not invent.
- **Numbers that change** (prices, API quotas, YPP requirements): state them as estimates and ask the user to verify.

## Mode router
Decide the mode from the user's request. If it is unclear, ask once. Read **only** the reference for that mode.

| Mode | When | Read |
|---|---|---|
| `channel` | create the first channel, add a channel, check capacity | references/channel-setup.md, then references/niche-scout.md |
| `niche` | pick or evaluate a niche | references/niche-scout.md |
| `ideas` | fill or extend the idea bank | references/idea-bank.md |
| `script` | write the script and hook for one idea | references/script.md |
| `shots` | HyperFrames scene storyboard (diagrams, objects, characters) for a script | references/shot-plan.md |
| `build` | voiceover, HyperFrames project, word-by-word captions, music, snapshot QA, MP4 render | references/build.md |
| `brand` | avatar, YouTube banner, Facebook cover, watermark | references/channel-setup.md (Channel brand assets section) |
| `library` | optional: register, preview or approve your own reusable items | references/library.md |
| `package` | title, description, hashtags, TTS text, captions, checklist, validation | references/package-qa.md + references/rules.md |
| `clipper` | clip a streamer, with permission | references/clipper.md |
| `review` | weekly stats (YouTube Analytics API), monetization progress, continue or change niche | references/review.md |

**Batch mode:** "prepare 7 videos" means `script`, `shots`, `build` and `package` repeated for 7 ideas from the active channel's idea bank, with one Episode Package per idea. **Work serially:** finish one episode completely (render, QA PASS, validation `OK`) before starting the next. Do not build, snapshot or render several episodes at once, even via subagents, because the machine only has 8 GB RAM. Scripts may be written first.

## Model per step
Use the cheapest model that is enough: scripts, storyboards and packages with a strong model (Opus); `build` and `review` with a mid-size model (Sonnet), in Claude Code via one `model: sonnet` subagent per episode, serially. Details: top of references/build.md.

## Data
One folder per channel (in Claude Code, at the project root):
```
channels/<channel-id>/
  channel.json               Channel Profile   (example: templates/channel.example.json)
  style-bible.md             fixed visual style (templates/style-bible.md)
  ideas.md                   idea bank
  episodes/<episode-id>.json Episode Package   (example: templates/episode.example.json)
  review-log.csv             weekly stats (templates/review-log.csv)
```
Without a file system (Claude.ai without a project, ChatGPT, Gemini), show file contents as JSON or Markdown code blocks to save, and ask the user to paste the Channel Profile at the start of the next session.

Episode status moves in order: `idea` -> `scripted` -> `visuals` (storyboard + voiceover ready) -> `edited` (MP4 rendered and approved by the user) -> `published`. Render projects live in `render/<channel-id>/<ep-id>/`. Update it after each stage.

## Validation
Before declaring a package ready to upload:
1. **If you can run Python** (Claude Code, code execution in Claude.ai, Code Interpreter in ChatGPT), run `scripts/validate_episode.py` from this skill folder:
   - `python3 scripts/validate_episode.py validate channels/<id>/episodes/<ep>.json` -> must print `OK`
   - if the file is not inside a `channels/` folder (e.g. uploaded to a chat), add `--channel <channel.json>`
   - `validate-channel <channel.json>`, `log <channels-dir> [--channel ID]`, `capacity <channels-dir>` (videos/day vs posting slots, working minutes)
2. **If you cannot**, check manually one by one with the checklist in references/rules.md and write the result for each item.

Fix every problem and validate again. Do not call a package "ready" before it passes.

## Daily flow (short, to explain to the user)
1. `ideas` from trend research (`scripts/youtube_research.py`) -> 2. `script` + `shots` (Claude) -> 3. voiceover in the channel voice (Claude, the user listens) -> 4. `build` HyperFrames + snapshot, render, `qa_render.py` PASS (Claude) -> 5. watch and approve (user) -> 6. `package` + validation (Claude) -> 7. upload + schedule through the API once the user agrees: YouTube, plus Facebook/Instagram per `meta.platforms` (`scripts/meta_upload.py`; Instagram is posted by a `due` job at the posting time). User time: about 10-15 minutes per video. Once a week run `review` (numbers via `scripts/youtube_stats.py pull`).
