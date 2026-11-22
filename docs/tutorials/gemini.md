# Akra in Gemini (Gem)

You will make a Gem (your own Gemini assistant) that follows the Akra workflow. It plans your channel and writes scripts. **It cannot render video.** To turn scripts into videos, use Group 2 (see the [chooser](README.md)).

## What you need

- A Google account signed in to Gemini.
- Access to Gems. Plans and rules change, and Google has said Gems on personal accounts are changing into "skills" starting November 2026. Check current plan requirements and the current screens in the app's help pages.
- About 10 minutes.

## 1. Get the bundle

You need the folder `dist/gemini/`. Two ways to get it:

- **Download:** if the project page offers a release zip, download it and unzip it.
- **Build it yourself:** you need [Python](https://www.python.org/downloads/) 3.10 or newer. In a terminal, from the repo folder, run:

```bash
python3 tools/build_dist.py
```

The files you will use:

| File | What it is for |
|---|---|
| `dist/gemini/instructions.md` | Text you paste into the Gem |
| `dist/gemini/knowledge/` | 10 files you upload as knowledge (the most a Gem takes in this bundle's design) |

The 10 knowledge files: `build.md`, `channel-setup.md`, `idea-bank.md`, `niche-scout.md`, `package-qa.md`, `review.md`, `rules.md`, `script.md`, `shot-plan.md` and `templates.md`. The YouTube policy text is inside `rules.md`.

## 2. Create the Gem

1. Open Gemini and go to **Gems**, then **New Gem**.
2. **Name:** for example `Akra - Shorts Writer`.
3. **Instructions:** open `dist/gemini/instructions.md`, copy everything, and paste it in.
4. **Knowledge:** under Knowledge, choose **Add files** and upload every file from `dist/gemini/knowledge/`.
5. Click **Save**.

If the Knowledge section does not take all files, check the app's docs for the current file limit (this bundle was built for 10 files). If menus look different from these steps, Google changed its screens. See the app's help pages.

## 3. First use

Open your Gem. Copy each prompt in order.

**Step 1: create a channel.**

```text
Create a new channel for me. Ask me your questions one at a time. My language is English.
```

Answer the questions. At the end the Gem gives you `channel.json` and `style-bible.md` as text. Copy each into a text file on your computer. Paste `channel.json` at the start of every new chat.

**Step 2: ideas.**

```text
Here is my channel.json: [paste it here]. Fill the idea bank with 30 ideas, each with a one-line angle that makes it different from other videos.
```

**Step 3: script.**

```text
Here is my channel.json: [paste it here]. Write a script for idea number 3. Include a hook, a TTS version for the voiceover, and a source for every factual claim.
```

**Step 4: storyboard.**

```text
Write the 9:16 scene storyboard for this script: [paste it here].
```

**Step 5: upload package and monetization check.**

```text
Prepare the upload package for this episode: title, description, hashtags, sources, credits. Then go through the monetization checklist in rules.md item by item and tell me pass or fail for each.
```

A Gem cannot run Python, so it checks by hand with the checklist. Fix every fail and ask again.

## 4. Your daily routine

1. Paste `channel.json`.
2. Ask for the next idea, then the script and the storyboard.
3. Read the script. Change anything that is not true or not yours.
4. Ask for the upload package and the checklist.
5. Once a week, paste your YouTube numbers and ask for the `review` mode.

## 5. YouTube monetization reminders

Full list: [youtube-policy.md](../../skills/akra/references/youtube-policy.md).

- **Original angle.** Every video needs its own point of view.
- **Sources.** Every fact needs a link.
- **AI disclosure.** Turn on YouTube's altered or synthetic content label when it applies, and say in the description that the voice is synthetic.
- **Made for kids.** Answer honestly. It is a legal question.
- **Watch before upload.** You watch every finished video before it goes public.

## 6. Limits

- It cannot run code, make a voiceover, render video, or upload to YouTube.
- It may forget your channel between chats. Keep your `channel.json` handy.
- To turn scripts into videos, use Group 2: [local-setup.md](local-setup.md).
