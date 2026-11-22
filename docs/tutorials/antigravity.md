# Akra in Antigravity

Antigravity is Google's agent app. It works in a folder on your computer. It can write scripts, make the voice, render the video, and upload after you approve.

**First do** [local-setup.md](local-setup.md). Come back when `python3 tools/doctor.py` says Ready.

## 1. Install and open

1. Install Antigravity. See Google's Antigravity docs for the current download and sign-in steps.
2. Open the repo folder (the `akra` folder) as your workspace. Use the app's menu to open a folder.
3. Open the agent panel (or the agent command line).

## 2. How Antigravity finds the skill

Antigravity looks for skills in `.agents/skills/` inside your workspace. The repo has `.agents/skills/akra`, a link to `skills/akra`. Antigravity shows the agent every skill's name and description, and the agent reads the full skill when your task fits. You can also name the skill in your message, or type `/akra` in the app (Google's docs say the app and the CLI offer skills as slash commands). Google's docs do not mention `AGENTS.md`. The repo's own rules are in `AGENTS.md`, so at the start of each session say: `Read AGENTS.md and follow it.` If something differs in your version, see the app's docs.

## The first session

Open the app in the repo folder. Copy these prompts one at a time. Say "use the akra skill" (or type `/akra`).

**1. Create a channel.**

```text
Use the akra skill to create a channel. Ask me your questions one at a time. My language is English.
```

The agent asks about niche, tone, visual style, voice and posting times. It saves them in `channels/<id>/`.

**2. Approve the style frames.** Before your first episode, the agent must pass the "style gate":

```text
Render 2-3 sample style frames for my channel and show them to me. I will tell you what to change.
```

Look at the pictures. Ask for changes until you like them. Then say:

```text
I approve the style. Record the approval date.
```

Without this approval, the checks stop every episode.

**3. Ideas.**

```text
Use the akra skill to fill the idea bank for my channel with 30 ideas. Give each one its own angle.
```

**4. First episode.**

```text
Use the akra skill to make the next episode for my channel. Work through it one step at a time and wait for me at each approval.
```

## The full episode flow

For each video, the agent works in this order. You decide at the steps marked **you**.

1. **Script.** A short script with a hook and a source for every fact. **You** read it and fix anything untrue.
2. **Storyboard.** The scenes, one by one.
3. **Voice.** The agent makes the voiceover with Kokoro or ElevenLabs. **You** listen.
4. **Build.** It writes the animated scenes and captions, checks frames, and renders the MP4.
5. **QA.** An automatic check (loudness, loop, length, format). It must say PASS.
6. **Watch and approve.** **You** watch the whole video. Say what to fix, or say it is approved.
7. **Package.** Title, description, hashtags, sources, credits, and the monetization check ([youtube-policy.md](../../skills/akra/references/youtube-policy.md)). The check must say `Monetization: OK`.
8. **Upload.** The agent asks: "May I upload this episode now, scheduled for this time?" **You** say yes or no. It uploads as a scheduled video only after your yes.

Akra builds one episode at a time, start to finish. This keeps your computer from running out of memory.

Monetization reminders: your own angle, a source for every fact, AI disclosure when it applies, an honest "made for kids" answer, and you watch before upload.

## Your daily routine

1. Open the app in the repo folder.
2. Say: `Use the akra skill to make the next episode for my channel.`
3. Read the script and listen to the voice.
4. Watch the render. Approve or ask for fixes.
5. Check the package. Say yes to the upload.
6. Once a week: `Use the akra skill to run the weekly review.`

About 10-15 minutes of your time per video.

## Safety

- **Never paste keys, tokens or passwords into the chat.** Put keys in `.env`, and `client_secret.json` in the repo folder.
- **Nothing uploads without your approval for that episode.** Do not allow uploads through a browser. Use the upload script.
- Your channel files stay on your computer and are not committed to git.
- Do not install large AI models on a computer with 8 GB RAM.

## If something goes wrong

- Say: `Read AGENTS.md. Then run python3 tools/doctor.py and fix what fails.`
- Skill not seen: check that the workspace is the repo folder itself, not a folder above it.
- Other setup problems: [local-setup.md](local-setup.md).
