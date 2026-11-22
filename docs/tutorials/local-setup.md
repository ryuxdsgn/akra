# Set up your computer (for Claude Code, Antigravity and Codex)

Rendering a video needs real programs on your computer. This page lists them and shows how to install them. Do it once. Then pick your app: [Claude Code](claude-code.md), [Antigravity](antigravity.md) or [Codex](codex.md).

A "terminal" is the text window where you type commands. On macOS open **Terminal**. On Linux open your terminal app. On Windows see the Windows section below.

## What you need

| Need | Why | Required? |
|---|---|---|
| macOS, Linux, or Windows with WSL2 | The scripts are Linux-style. Windows is not tested by the authors. | Yes |
| 8 GB RAM or more | Akra renders one video at a time to fit | Yes |
| 6 GB or more free disk | Tools, the Kokoro voice (with PyTorch) and render files | Yes |
| Node.js 22 or newer | Runs HyperFrames 0.9.40 (the video renderer) through `npx` | Yes |
| Google Chrome | The render engine draws each frame in it | Yes |
| ffmpeg (with the `loudnorm` filter) | Joins picture and sound, and fixes loudness | Yes |
| Python 3.10 or newer | Runs the Akra scripts | Yes |
| git | Downloads and updates the repo | Yes |
| uv | Creates the small Python environments for voice and YouTube | Only for Kokoro or YouTube |
| A voice: Kokoro or ElevenLabs | Makes the voiceover | Yes, pick one |
| YouTube login files | Lets the upload script post for you | Optional |
| Meta (Facebook and Instagram) keys | Lets you post Reels from the script | Optional |

**Voice choices**

- **Kokoro:** free, runs on your computer, Apache-2.0 license (commercial use allowed). The `kokoro` package pulls in PyTorch: about 1.5 GB on a Mac (measured: a 1.2 GB environment plus the ~330 MB model), often 2–3 GB or more on Linux or Windows. Best for English.
- **ElevenLabs:** paid, runs online. You put an API key in the `.env` file. Check that your plan allows commercial use.

## Install steps

### macOS

1. Install [Homebrew](https://brew.sh) if you do not have it.
2. In Terminal:

```bash
brew install node git ffmpeg uv
brew install --cask google-chrome
```

3. Check Python: `python3 --version`. It must say 3.10 or higher. If not, run `brew install python`.

### Linux (Debian or Ubuntu)

1. Install the basics:

```bash
sudo apt update
sudo apt install git ffmpeg python3 python3-venv curl
```

2. Install Node.js 22 or newer from [nodejs.org](https://nodejs.org) (the apt version is often too old). Check with `node --version`.
3. Install Google Chrome from [google.com/chrome](https://www.google.com/chrome/).
4. Install uv: see [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/).

### Windows (WSL2)

1. Install WSL2 with Ubuntu. See Microsoft's page "Install WSL".
2. Open the Ubuntu terminal. Do **everything** below inside Ubuntu, not in PowerShell.
3. Follow the Linux steps above, inside Ubuntu.
4. Put the repo inside the Ubuntu home folder (`~/akra`), not under `/mnt/c`. It is much faster.
5. Chrome must be installed inside Ubuntu too. If rendering cannot find Chrome, see the HyperFrames docs.

## Get the repo and run setup

1. Download the repo (use the real address of this repo):

```bash
git clone https://github.com/ryuxdsgn/akra.git
cd akra
```

2. Run setup. Choose what you want:

```bash
tools/setup.sh --kokoro      # free local voice
# tools/setup.sh --youtube   # add this for YouTube upload
# tools/setup.sh --all       # everything
```

Setup makes a `.env` file for your keys. It never prints or sends them.

3. Check your computer:

```bash
python3 tools/doctor.py
```

Read the list. `OK` is good. `WARN` is an optional feature that is not set up. `FAIL` must be fixed. Fix the FAILs, run it again, and repeat until the last line says **Ready**.

## Troubleshooting `doctor.py`

| You see | What it means | Fix |
|---|---|---|
| `FAIL python ... needs 3.10+` | Python is too old | Install a newer Python and use `python3` |
| `FAIL node ... Node.js not found` or `needs 22+` | Node is missing or old | Install Node.js 22 or newer, open a new terminal, check `node --version` |
| `FAIL npx not found` | Npx comes with Node | Reinstall Node.js |
| `FAIL ffmpeg not found` | ffmpeg is missing | `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` |
| `FAIL ffmpeg without the loudnorm filter` | A stripped-down ffmpeg | Install a full build of ffmpeg |
| `WARN git not found` | Git is missing | Install git |
| `WARN uv not found` | uv is needed for voice and YouTube setup | Install uv, then run setup again |
| `WARN kokoro ... missing` | Local voice is not installed | `tools/setup.sh --kokoro` |
| `WARN elevenlabs ... not set` | No ElevenLabs key | Fine if you use Kokoro. Otherwise put the key in `.env` yourself |
| `WARN youtube ... missing` | Upload is not set up | Optional. See below |
| `WARN channels ... no channel yet` | You have not made a channel | Normal on day one. Your app will create one |
| `WARN meta ... missing` | Facebook or Instagram is not set up | Optional. See below |

Other problems:

- **Voice error about spaCy:** install the `en_core_web_sm` model into `.venv-kokoro`. See [setup.md](../setup.md).
- **Render is slow or the computer freezes:** close other apps. Never render two videos at once.
- **ffmpeg has no `drawtext`:** that is fine. Akra makes text labels as images.

More detail: [setup.md](../setup.md).

## Your keys (optional)

**Never paste a key or password into the chat with your agent.** Put keys in files on your computer.

### ElevenLabs

Open `.env` in a text editor and fill in `ELEVENLABS_API_KEY=` with your key. Save. That is all.

### YouTube upload

1. Run `tools/setup.sh --youtube` if you have not.
2. Go to [console.cloud.google.com](https://console.cloud.google.com/) and create a project.
3. Enable **YouTube Data API v3** (and **YouTube Analytics API** for weekly stats).
4. Set up the **OAuth consent screen**: type External, and add your own Google account as a test user.
5. Create an **OAuth client ID** of type **Desktop app**. Download the JSON file.
6. Save it as `client_secret.json` in the repo folder (next to `README.md`).
7. Log in once per channel. A browser window opens:

```bash
.venv-youtube/bin/python skills/akra/scripts/youtube_upload.py auth --channel channels/<your-channel-id>
```

Notes:

- While your consent screen is in Testing mode, the login lasts about 7 days. Repeat step 7 when it expires.
- A new Google API project may be forced to keep API uploads **private** until it passes a YouTube audit. Check YouTube's current rules. If it happens, schedule the video by hand in YouTube Studio.
- Nothing uploads without your approval. See your app's tutorial.

### Facebook and Instagram (optional)

Needs `tools/setup.sh --youtube`. Run `.venv-youtube/bin/python skills/akra/scripts/meta_upload.py setup --channel channels/<your-channel-id>`. It prints the steps and asks for keys in the terminal, not in chat. Full steps: [setup.md](../setup.md). TikTok has no automatic upload: you post the MP4 yourself.

## What stays private

These are never committed to git: `channels/`, finished videos, `.env`, `client_secret*.json` and the token files. Back up `channels/` yourself.

## Next

- [Claude Code](claude-code.md)
- [Antigravity](antigravity.md)
- [Codex](codex.md)
