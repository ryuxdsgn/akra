# Akra in Claude.ai (Project + skill)

You will add the Akra skill (a folder of instructions Claude can read) to Claude.ai, and use it inside a Project (a workspace that keeps your chats and files together). Claude.ai can plan and write, and it can run the checker script with its code tool. **It cannot render video or upload.** To turn scripts into videos, use Group 2 (see the [chooser](README.md)).

## What you need

- A Claude.ai account.
- A plan that supports Projects and custom skills, and code execution turned on. Plan rules change, so check current plan requirements in the app's help pages.
- About 10 minutes.

## 1. Get the bundle

You need one file: `dist/claude-ai/akra.zip`. Two ways to get it:

- **Download:** if the project page offers a release zip, download it.
- **Build it yourself:** you need [Python](https://www.python.org/downloads/) 3.10 or newer. In a terminal, from the repo folder, run:

```bash
python3 tools/build_dist.py
```

`akra.zip` holds one folder, `akra/`, with `SKILL.md`, `references/`, `scripts/` and `templates/`. Do not unzip it for upload.

## 2. Add the skill

1. In Claude.ai, open **Settings** and find the **Skills** section (it may be under Capabilities).
2. Choose to upload a skill, and select `akra.zip`.
3. Switch the skill **on**.
4. Make sure code execution is on, so Claude can run `validate_episode.py`.

The menu names change over time. If you cannot find them, see the app's docs on custom skills.

## 3. Create a Project

1. Click **Projects**, then **Create project**. Name it, for example, `My Shorts channel`.
2. In the project instructions, paste:

```text
Use the akra skill for everything in this project. Write to me in English. Never ask me for passwords or keys. Keep my channel.json in the project knowledge.
```

Later, you will add `channel.json` and `style-bible.md` to the **project knowledge**. Then every chat in the project knows your channel.

## 4. First use

Open a new chat inside the project. Copy each prompt in order.

**Step 1: create a channel.**

```text
Use akra to create a new channel for me. Ask me your questions one at a time. My language is English.
```

At the end Claude gives you `channel.json` and `style-bible.md`. Save them as files and add both to the project knowledge.

**Step 2: ideas.**

```text
Fill the idea bank with 30 ideas for my channel. Give each idea a one-line angle that makes it different from other videos.
```

**Step 3: script.**

```text
Write the script for idea number 3. Include a hook, a TTS version for the voiceover, and a source for every factual claim.
```

**Step 4: storyboard.**

```text
Write the 9:16 scene storyboard for this script.
```

**Step 5: upload package and monetization check.**

```text
Prepare the upload package: title, description, hashtags, sources, credits. Then run the monetization check and run validate_episode.py. Tell me every item that fails.
```

Fix every failure and ask again until the check says `OK`.

## 5. Your daily routine

1. Open the project and start a new chat.
2. Ask for the next idea, then the script and the storyboard.
3. Read the script. Change anything that is not true or not yours.
4. Ask for the upload package and the checker run.
5. Once a week, paste your YouTube numbers and ask for the `review` mode.

## 6. YouTube monetization reminders

Full list: [youtube-policy.md](../../skills/akra/references/youtube-policy.md).

- **Original angle.** Every video needs its own point of view.
- **Sources.** Every fact needs a link.
- **AI disclosure.** Turn on YouTube's altered or synthetic content label when it applies, and say in the description that the voice is synthetic.
- **Made for kids.** Answer honestly. It is a legal question.
- **Watch before upload.** You watch every finished video before it goes public.

## 7. Limits

- It cannot make a voiceover, render video, or upload to YouTube.
- Files it writes stay in the chat. Download what you want to keep.
- To turn scripts into videos, use Group 2: [local-setup.md](local-setup.md).
