# akra

A workflow for making faceless YouTube Shorts (long-form is planned) as code-drawn videos, packaged as an agent skill. Your agent writes animated diagrams and word-by-word captions as HTML and renders them with [HyperFrames](https://www.npmjs.com/package/hyperframes). Nothing is AI-generated video: every frame comes from code you can read and edit.

akra ships the workflow, not art: the skill and its references, the render template, QA and validation scripts, the upload tools, and an optional engine for registering your own reusable scene items. Characters, backgrounds and other drawings are made per channel, by you and your agent.

akra covers the whole job, from picking a niche to the weekly review. Your agent does the writing, building and checking. You keep the decisions: the topic, the angle, the final watch, and the upload.

## Where it runs

| Platform | What you get | How |
|---|---|---|
| Claude Code | Full flow: script, build, render, QA, upload | Open this folder, call `/akra` |
| Codex, Antigravity | Full flow | Open this folder, call `$akra` (skill read from `.agents/skills/akra`) |
| Claude.ai | Planning and writing, validation through code execution | Upload `dist/claude-ai/akra.zip` as a skill |
| ChatGPT | Writing only (no render) | Custom GPT, see `dist/chatgpt/gpt-setup.md` |
| Gemini | Writing only (no render) | Gem, see `dist/gemini/` |

Build the bundles with `python3 tools/build_dist.py`.

## Tutorials

Step-by-step guides for beginners, in plain English: [docs/tutorials/](docs/tutorials/README.md).

| Group | Apps | Plan and write | Render video |
|---|---|---|---|
| Chat apps | [ChatGPT](docs/tutorials/chatgpt.md), [Gemini](docs/tutorials/gemini.md), [Claude.ai](docs/tutorials/claude-ai.md) | Yes | No |
| Agent apps on your computer | [Claude Code](docs/tutorials/claude-code.md), [Antigravity](docs/tutorials/antigravity.md), [Codex](docs/tutorials/codex.md) | Yes | Yes (see [local setup](docs/tutorials/local-setup.md)) |

## How it works

You talk to the agent; it routes to a mode and reads only that mode's reference file.

| Mode | What it does |
|---|---|
| `channel` | Set up a channel: niche, language, concept, visual style, voice, posting slots |
| `niche` | Score and pick a niche |
| `ideas` | Fill an idea bank from trend research |
| `script` | 75-150 word script with a hook and a TTS version |
| `shots` | 9:16 scene storyboard |
| `build` | Voiceover, HyperFrames project, captions, music, snapshots, MP4 render, automatic QA |
| `package` | Title, description, hashtags, source list, credits, validation |
| `review` | Weekly numbers and a continue/change decision |
| `library` | Optional: register your own reusable items (engine in `library/`, empty catalog) |

Typical loop per video: `script` -> `shots` -> voiceover -> `build` -> **you watch and approve** -> `package` -> upload (only after you say yes).

## Requirements

- Python 3.10+ (standard library only for the core tools; Pillow for labels and previews)
- Node.js 22+ and ffmpeg (HyperFrames renders through them)
- One of the agents above
- Optional: Kokoro for local voiceover, an ElevenLabs key, YouTube/Meta API credentials

Full install steps: [docs/setup.md](docs/setup.md). To see what your machine is missing:

```bash
python3 tools/doctor.py
```

## Quick start

```bash
git clone <this repo> && cd akra
tools/setup.sh
python3 tools/doctor.py
```

Then open your agent in the folder and say:

```
/akra channel        # Codex: $akra channel
```

Answer the questions, then ask for `ideas`, `script`, `shots` and `build`, one episode at a time. Channel data lives in `channels/<id>/` and stays on your machine (it is git-ignored).

## Responsible use

akra makes production fast. It does not make a video worth publishing; that part is yours.

- **Original scripts with a real angle.** Do not republish someone else's script or a bare list of facts. Add your own explanation, example or point of view.
- **Every factual claim has a source.** `package` asks for the sources; link them in the description.
- **No medical or financial "expert" personas.** No invented doctors, traders or credentials. For health or sport topics: no "cure" claims, a doctor disclaimer, and stay inside safe movements.
- **Read YouTube's policy on inauthentic content** (mass-produced, repetitive, or low-effort videos): https://support.google.com/youtube/answer/1311392. Channels made of templated, near-identical videos can lose monetization. Vary your topics and add real value.
- **Disclose AI.** Turn on YouTube's altered or synthetic content label when it applies, and say in the description that the voice is synthetic.
- **Voice and music licenses.** Use voice models whose license allows commercial use (check the model, not the app that runs it). Never clone a voice without its owner's consent. Credit the voice and the music in the description.
- **A human approves every upload.** The agent never uploads on its own: you review the render and the package first, and the upload script is only run after you say yes.

## Tests

```bash
python3 -m unittest discover -s tests
```

## License

MIT, see [LICENSE](LICENSE). Bundled and optional third-party assets (sound effects, HyperFrames, GSAP, Kokoro, fonts) are listed in [THIRD_PARTY.md](THIRD_PARTY.md).
