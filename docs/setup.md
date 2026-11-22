# Installing Akra on your own computer (Codex or Claude Code)

This guide is for people who want to use Akra with **their own channel, concept and keys**. Akra runs on your
computer: an AI agent (Codex from OpenAI, or Claude Code) reads the skill in this repo, then writes scripts,
makes the voice, renders videos and (if you approve) uploads to YouTube.

Want to write scripts only, without rendering? Use a Custom GPT in ChatGPT (see the README, section "Use it
anywhere"). This guide is for the full flow up to the MP4.

## 1. What you need

| Requirement | Notes |
|---|---|
| macOS or Linux | Windows through WSL2 is untested |
| 8 GB RAM | enough; Akra deliberately renders one video at a time |
| Node.js **22+** | for HyperFrames 0.9.40 (video render). Includes `npx` |
| Python **3.10+** | for the Akra scripts |
| ffmpeg | macOS: `brew install ffmpeg`. Must have the `loudnorm` filter |
| uv | for Python venvs: <https://docs.astral.sh/uv/getting-started/installation/> |
| git | to fetch and update the repo |
| Google Chrome | the render engine draws frames in it; `tools/doctor.py` warns when it is missing (or set `CHROME=<path>`) |
| 6 GB+ free disk | the Kokoro voice alone is about 1.5 GB on a Mac (PyTorch), often 2–3 GB or more on Linux |
| AI agent | **Codex** (a ChatGPT plan that includes Codex, or an OpenAI API key) or **Claude Code** |

## 2. Get the repo and install

```bash
git clone https://github.com/ryuxdsgn/akra.git
cd akra
tools/setup.sh --kokoro            # free local voice (Kokoro-82M, Apache-2.0)
# tools/setup.sh --youtube         # add this if you want automatic YouTube upload
# tools/setup.sh --all             # everything
```

`setup.sh` creates `.env` from `.env.example`, installs the venvs you asked for, then runs the checker:

```bash
python3 tools/doctor.py
```

`FAIL` means a required item is missing (Node, ffmpeg, Python). `WARN` is only an optional feature.

## 3. Run the agent

**Codex**
```bash
npm install -g @openai/codex
codex                              # from the repo folder; log in once
```
Codex reads `AGENTS.md` (working rules) and the skill in `.agents/skills/akra` automatically. Call the skill
with `$akra`, or just ask in plain sentences.

**Claude Code**: run `claude` in the repo folder, then `/akra`.

## 4. Start with your own channel

First-time order (write to the agent in your own language):

1. **"Create a new channel"**: the agent asks for the niche, language, concept, visual style, voice and
   schedule, then saves them in `channels/<id>/channel.json` and `style-bible.md`.
2. **"Fill the idea bank for channel <id>"**: at least 30 ideas.
3. **"Make the next video for channel <id>"**: script → storyboard → voice → render → QA. You watch the
   result before anything is uploaded.

Render projects live in `render/<channel-id>/<ep-id>/`. All channel data stays on your computer.

## 5. Your own keys

Put keys in files, **never paste them into the agent chat**.

### ElevenLabs (optional)
Fill `ELEVENLABS_API_KEY=` in `.env`. Without this key, Akra uses Kokoro (local, free). For monetization,
use a voice whose license allows commercial use, and write the credit in the description.

### YouTube (optional, for automatic upload and stats)
1. Open <https://console.cloud.google.com/>, create a new project.
2. **APIs & Services → Library**: enable **YouTube Data API v3** (and **YouTube Analytics API** for weekly
   stats).
3. **OAuth consent screen**: type *External*, add your Google account as a *test user*.
4. **Credentials → Create credentials → OAuth client ID**, type **Desktop app**. Download the JSON and save
   it as `client_secret.json` in the repo root.
5. Log in once per channel:
   ```bash
   .venv-youtube/bin/python skills/akra/scripts/youtube_upload.py auth --channel channels/<id>
   ```
6. The agent only uploads after you approve that episode, through
   `youtube_upload.py upload <episode.json> --schedule`.

Good to know:
- While the consent screen is still in *Testing* mode, the login expires after about 7 days; repeat step 5.
- According to YouTube's documentation, videos uploaded through the API from a project that has **not been
  audited** (created after 28 July 2020) are locked as **private** until the project passes an audit. Check
  the latest rules at <https://developers.google.com/youtube/v3/docs/videos/insert>. If this hits you, upload
  the MP4 manually in YouTube Studio, or apply for an audit for your project.

### Facebook Reels and Instagram Reels (optional)
Needs `tools/setup.sh --youtube` (the same venv). Once per channel:
1. Prepare a Facebook Page. If you want to post to Instagram, link a professional Instagram account to that Page.
2. Run in Terminal: `.venv-youtube/bin/python skills/akra/scripts/meta_upload.py setup --channel channels/<id>`.
   The script prints the steps for creating a Meta app, then asks for the App ID and App Secret (saved to
   `.env`, not to the chat), opens the Facebook login in the browser, asks you to pick a Page, and asks
   whether to schedule to Facebook, Instagram, or both.
3. If Instagram is chosen, the script installs an automatic job that posts the Instagram Reel at each
   publishing time (the Instagram API cannot schedule). The Mac must be on at the publishing time.

`python3 tools/doctor.py` shows what is still missing per channel.

### TikTok
No automatic upload yet (the TikTok API needs an audited app). The agent prepares the MP4 and caption; you upload it yourself.

## 6. Data and privacy

These are **never** committed to git (already in `.gitignore`, and the agent is forbidden to commit them):
`channels/`, `render/<channel>/<ep>/`, `.env`, `client_secret*.json`, `.youtube-*token.json`,
`.meta-*token.json`. Back up `channels/` yourself, for example to a personal drive.

Your own notes for the agent (channel list, schedule, habits) go in `AGENTS.local.md` in the repo root. The
agent reads this file but it is not committed. It can also set the language the agent talks to you in.

## 7. If something goes wrong

- Run `python3 tools/doctor.py` first.
- spaCy error with Kokoro: install the `en_core_web_sm` model into `.venv-kokoro`.
- ffmpeg without `drawtext` is fine; text labels are made as PNGs.
- Slow render or full RAM: close other apps; do not render two videos at once.
- Updating Akra: `git pull`, then `tools/setup.sh` again if dependencies changed.
