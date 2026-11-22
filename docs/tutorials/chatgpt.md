# Akra in ChatGPT (Custom GPT)

You will make a Custom GPT (your own ChatGPT assistant) that follows the Akra workflow. It plans your channel and writes scripts. **It cannot render video.** To turn scripts into videos, use Group 2 (see the [chooser](README.md)).

## What you need

- A ChatGPT account.
- A plan that lets you create Custom GPTs. Plan rules change, so check current plan requirements on OpenAI's site.
- About 10 minutes.

## 1. Get the bundle

You need the folder `dist/chatgpt/`. Two ways to get it:

- **Download:** if the project page offers a release zip, download it and unzip it.
- **Build it yourself:** you need [Python](https://www.python.org/downloads/) 3.10 or newer. In a terminal, from the repo folder, run:

```bash
python3 tools/build_dist.py
```

The files you will use:

| File | What it is for |
|---|---|
| `dist/chatgpt/gpt-setup.md` | The same steps as below, in short |
| `dist/chatgpt/instructions.md` | Text you paste into the GPT (7,995 of the 8,000 characters allowed) |
| `dist/chatgpt/knowledge/` | 17 files you upload as Knowledge |

## 2. Create the GPT

1. In ChatGPT, open **Explore GPTs**, then **Create**, then the **Configure** tab.
2. **Name:** type a name, for example `Akra - Shorts Writer`.
3. **Description:** `Plan a faceless YouTube Shorts channel and write scripts, storyboards and upload packages.`
4. **Instructions:** open `dist/chatgpt/instructions.md`, copy everything, and paste it in. Do not edit it. It is already at the size limit.
5. **Conversation starters** (optional): add these four.
   - Create a new channel for me
   - Fill the idea bank for my channel
   - Write the next Shorts script
   - Prepare the title, description and hashtags
6. **Knowledge:** upload **every file** inside `dist/chatgpt/knowledge/`. One of them is `validate_episode.py`, a checker script.
7. **Capabilities:** turn on **Code Interpreter** (it runs the checker) and **Web Search** (for research). Image generation is not needed.
8. **Actions:** leave empty. The GPT needs no keys.
9. Click **Save** and choose who can see it. **Only me** is the safe choice.

If the menu names look different, ChatGPT changed its screens. See the app's help pages.

## 3. First use

Open your new GPT. Copy each prompt in order.

**Step 1: create a channel.**

```text
Create a new channel for me. Ask me your questions one at a time. My language is English.
```

Answer the questions: niche, tone, visual style, voice, posting times. At the end, the GPT gives you two files as text: `channel.json` and `style-bible.md`.

**Save them.** Copy each into a text file on your computer. ChatGPT may forget your channel between chats, so paste `channel.json` at the start of every new chat.

**Step 2: ideas.**

```text
Here is my channel.json: [paste it here]. Fill the idea bank with 30 ideas. For each idea give a one-line angle that makes it different from other videos.
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
Prepare the upload package for this episode: title, description, hashtags, sources, credits. Then run the monetization check from youtube-policy and run validate_episode.py. Tell me every item that fails.
```

Fix what fails and ask again until it says `OK`.

## 4. Your daily routine

1. Paste `channel.json`.
2. Ask for the next idea, then the script and the storyboard.
3. Read the script. Change anything that is not true or not yours.
4. Ask for the upload package.
5. Once a week, paste your YouTube numbers and ask for the `review` mode.

## 5. YouTube monetization reminders

Full list: [youtube-policy.md](../../skills/akra/references/youtube-policy.md).

- **Original angle.** Every video needs its own point of view, not a template with new keywords.
- **Sources.** Every fact needs a link.
- **AI disclosure.** Turn on YouTube's altered or synthetic content label when it applies, and say in the description that the voice is synthetic.
- **Made for kids.** Answer honestly. It is a legal question.
- **Watch before upload.** You watch every finished video before it goes public.

## 6. Limits

- It cannot make a voiceover, render video, or upload to YouTube.
- It may forget your channel between chats. Keep your `channel.json` handy.
- To turn scripts into videos, use Group 2: [local-setup.md](local-setup.md).
