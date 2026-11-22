# Mode `script`: the script

## Target
- **Length by channel language** (the validator uses `language` in the Channel Profile):
  | `language` | Words | Reading speed | Sweet spot |
  |---|---|---|---|
  | `en` (default) | 75–150 | 150 words/minute | 100–130 |
  | `id` | 62–125 | 125 words/minute (Indonesian words are longer) | 80–105 |
- **Hook ≤ 10 words** (ideally 6–8 words ≈ 3 seconds), and it is the **first sentence** of the script exactly as written.
- **`en`:** simple international English: short sentences, no local idioms or slang, and numbers spoken clearly ("four hundred miles").
- **`id`:** casual everyday Indonesian (words like "yuk", "nih", "gak" are fine), short sentences, one instruction per sentence, no unnecessary English terms. Numbers may be written as digits (`10x`, `5 menit`); `dots_tts.py` pronounces them as words.
- **Any language:** match pace and vocabulary to your audience.
- Other languages: follow the same idea (short, spoken, everyday wording of that language); add a row for the language to the table if a channel needs it.

## Story: one real moment (adapted from BEATS, social-media-skills `storytelling-and-narrative`, MIT)
An explainer script easily becomes a list of mechanisms. Tie the mechanism to **one real moment the viewer knows**, then explain the mechanism **through** that moment.
- **The moment:** a concrete everyday event (a phone dying at 20%, ice melting faster on a metal tray, a car that will not start on a cold morning). The viewer is the lead ("your kitchen", "your ceiling"); the channel is the guide.
- **Do not invent:** the moment may be hypothetical ("Then the toast burns"), but do not write real events, people, quotes or numbers that have no source.
- **Concrete detail:** 1–3 specific sensory details (burnt smell, thin smoke, a loud "beep"), not generic words. These details also become scene material in the `shots` mode.
- **One emotion:** pick one feeling to take home (relief, awe, "oh, that's why"). Close with one meaning that makes the viewer see themselves.
- **If the topic has no moment** (e.g. an abstract concept), do not force it; use one concrete example worked through from start to end.

## Hook: many candidates, choose by score (adapted from social-media-skills `hook-writer`, MIT)
1. **Mine it from the content, do not stick it on.** Find the strongest material in the script: the most surprising fact, the biggest stakes, the most specific number, the sharpest point of view, or the most relatable moment.
2. **Study the patterns first:** if `channels/<id>/research/patterns.md` exists, read the winning hook and title formulas in this niche and this channel's own winning hooks; at least 2 candidates use that proven mechanism (with your own words and facts, not a copy).
3. **Write 6–8 candidates with different mechanisms:** curiosity gap, contrarian, stakes/danger, specific number, scene, question, "your ..." (relevant to the viewer). Not one idea rewritten.
4. **Score 0–2 per column:**
   | Column | Question |
   |---|---|
   | Gap | Does it open a gap a stranger has to close? |
   | Specific | Is there a concrete object, number or detail? |
   | Honest | Does the video really pay it off? **Gate: 0 = out.** |
   | Fit | ≤ 10 words, and can the first frame show it right away? |
   | Voice | Does it match the channel's tone? |
   | Pull | Read cold, does a person **need** the next sentence? **Gate: 0 = out.** |
5. **Layered hook:** on the first frame, picture + spoken words + text banner say the same thing. It must still work without sound.
6. **Cut:** small-talk openings ("In this video", "Did you know", "Hey guys"), empty teasers ("You won't believe this"), over-promising, and hooks that answer themselves immediately.

## Structure
1. **Hook (0–3 s):** the score winner above. The first sentence of the script exactly as written.
2. **Quick payoff + open loop (3–10 s):** answer part of it so the viewer does not feel cheated, and plant one question that is only answered at the end (e.g. "the radiation is the whole point" → answered by "And the radiation?").
3. **Normal state:** what quietly happens every day (the mechanism at rest).
4. **Turning point:** the real moment happens ("Then the toast burns."), and the mechanism works through that moment. Every 5–8 seconds something new; one sentence per picture.
5. **Twist or added value:** pay off the open loop; the channel's own point of view. This is the part that makes the script original.
6. **Closing:** a loop ending (the last sentence connects to the hook) **or** a light CTA ("Follow for part 2"). Not both.

**Check before finishing:** read the script while imagining the video without sound (banners and captions must carry the story); make sure the content pays off the hook's promise; cross out sentences that do not teach, build tension, or set up the payoff.

## Output
1. **Story brief** (moment, concrete detail, emotion, meaning) in 4 lines.
2. **Hook candidate table** with scores; show the top 3 and recommend one with a short reason.
3. **Final script**, written as one paragraph.
4. **Word count and estimated seconds.**
5. **TTS version** of the same script, saved as `channels/<id>/episodes/<ep>-assets/tts.txt`:
   - the words must be **exactly the same** as the script (the TTS script refuses if different, so captions fit); only punctuation, pauses and capital letters may change
   - one sentence or phrase per line; a new line = a breathing pause (longer after a long sentence, `?` or `:`)
   - **a blank line = a dramatic pause** (+0.45 s): use only 2–3 times, before the turning point and after the peak moment
   - `...` inside a line gives almost no pause in Kokoro; if you need a real pause, move to a new line
   - `dots_tts.py` (`id` channels) makes every line in a separate process: short lines (≤ 12 words) are more stable and save RAM
   - exclamation and question marks change intonation; use them for surprise moments, not in every sentence
   - word stress: capital letters on at most one key word per sentence (Kokoro reads it as emphasis `[word](+2)`, not spelled letter by letter)
   - pronunciation hints in parentheses for hard words, e.g. `ringwoodite (RING-wood-ite)`; the Kokoro script removes them automatically, so they are not read aloud
   - **emotion map:** first write the video's emotional flow in one line (e.g. curious → tense → startled → awe → calm), then put an emotion tag at the start of the lines that carry a change of feeling, e.g. `[tense] The pressure keeps rising.` Tags are not spoken and not counted as words. Do not tag every line: 4–8 tags per Short, one emotion per line, and the same feeling may continue without a tag.
     - **Kokoro** (no emotion control): the tag sets the pace and pause of that line. Known tags: `neutral`, `curious`, `tense`, `serious`, `surprised`, `excited`, `awe`, `warm`, `calm`, `playful`, `relieved`, `urgent` (or the Indonesian `netral`, `penasaran`, `tegang`, `serius`, `kaget`, `semangat`, `kagum`, `hangat`, `tenang`, `jahil`, `lega`, `mendesak`). Other tags are read as neutral.
     - **ElevenLabs v3/v4:** tags are sent as they are as audio tags and may be free-form or combined (`[teasing, warm]`, `[whispers]`, `[sighs]`, `[laughs softly]`), and may also sit mid-line before the phrase that changes feeling. In cast mode put it after the character name: `HOST: [teasing] Just one?` Tags count toward paid characters.
     - Write for the ear: vary sentence length (short for surprise, longer for explaining), a pause before the answer, one stressed key word.
6. **Fact list + sources** for the user to check in 2 minutes.

Save to the Episode Package (`hook`, `script`, `status: "scripted"`).

## Policy gate
YT-AUTH-1, YT-AUTH-2, YT-FACT-1, YT-MED-1, YT-REUSE-1, YT-AD-2 in youtube-policy.md; the opening (akra house rule: the first 7 seconds) also follows YT-AD-1. Save `variation` {story, setting, props} (different from the last 3 episodes) and `sources` [{claim, url}] with the script.

## Don'ts
- Inventing numbers or quotes.
- Making a script that only swaps words from another video (risk of "inauthentic content").
- Clickbait that the video does not answer.
