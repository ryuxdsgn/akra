# Akra in Claude Code

Claude Code is Anthropic's agent that works in a folder on your computer. It can write scripts, make the voice, render the video, and upload after you approve.

**First do** [local-setup.md](local-setup.md). Come back when `python3 tools/doctor.py` says Ready.

## 1. Install and open

1. Install Claude Code. See Anthropic's Claude Code docs for the current way to install it on your system, and sign in. Check the plan requirements there.
2. In your terminal, go into the repo folder and start it:

```bash
cd akra
claude
```

The first time, it asks whether you trust the folder. Say yes only if you got the repo from the real source.

## 2. How Claude Code finds the skill

The repo has a link `.claude/skills/akra` that points to `skills/akra`. When you open the repo folder, Claude Code sees the `akra` skill. You do not install anything. Call it by typing `/akra`. You can also just describe what you want in plain words. Claude Code also reads the working rules in `AGENTS.md`.

## The first session

Open the app in the repo folder. Copy these prompts one at a time. Type `/akra` first, or just describe the task.

**1. Create a channel.**

```text
/akra create a channel. Ask me your questions one at a time. My language is English.
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
/akra fill the idea bank for my channel with 30 ideas. Give each one its own angle.
```

**4. First episode.**

```text
/akra make the next episode for my channel. Work through it one step at a time and wait for me at each approval.
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
2. Say: `/akra make the next episode for my channel.`
3. Read the script and listen to the voice.
4. Watch the render. Approve or ask for fixes.
5. Check the package. Say yes to the upload.
6. Once a week: `/akra run the weekly review.`

About 10-15 minutes of your time per video.

## Safety

- **Never paste keys, tokens or passwords into the chat.** Put keys in `.env`, and `client_secret.json` in the repo folder.
- **Nothing uploads without your approval for that episode.** Do not allow uploads through a browser. Use the upload script.
- Your channel files stay on your computer and are not committed to git.
- Do not install large AI models on a computer with 8 GB RAM.

## If something goes wrong

- Say: `Run python3 tools/doctor.py and fix what fails.`
- Skill not found: check you started `claude` inside the repo folder.
- Other setup problems: [local-setup.md](local-setup.md).
