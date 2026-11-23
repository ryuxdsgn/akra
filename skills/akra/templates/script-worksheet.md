# Script worksheet: <episode id> · <idea id> · <channel>

A fill-in sheet for the `script` mode (`references/script.md`). Fill it top to bottom; the results go into the Episode Package (`hook`, `script`, `story_logic`, `variation`, `sources`) and into `channels/<id>/episodes/<ep>-assets/tts.txt`. Delete the guidance lines once filled.

## 0. Is the subject new?
- [ ] Listed this channel's episodes (`topic`, `title`): no episode covers this subject yet
- [ ] Idea ticked in `ideas.md` with this episode id
- Last 3 episodes' variation (story / setting / props): <ep-a: …> · <ep-b: …> · <ep-c: …>

## 1. Story brief (4 lines)
- **Moment:** <one concrete everyday event the viewer knows>
- **Detail:** <1–3 sensory details: a sound, a smell, an object on screen>
- **Emotion:** <one feeling to take home: relief, awe, "oh, that's why">
- **Meaning:** <one sentence the viewer keeps>

## 2. Hook candidates (6–8, different mechanisms)
Score 0–2 per column. **Honest = 0 or Pull = 0 → out.**

| # | Candidate (≤ 10 words) | Mechanism | Gap | Specific | Honest | Fit | Voice | Pull | Total |
|---|---|---|---|---|---|---|---|---|---|
| 1 | <…> | curiosity gap | | | | | | | |
| 2 | <…> | contrarian | | | | | | | |
| 3 | <…> | stakes | | | | | | | |
| 4 | <…> | specific number | | | | | | | |
| 5 | <…> | scene | | | | | | | |
| 6 | <…> | question | | | | | | | |
| 7 | <…> | "your …" | | | | | | | |

**Chosen:** #<n>, because <one reason>. First frame shows: <picture + banner that say the same thing>.

## 3. Beats (one line each)
| Beat | Time | What happens on screen | Line(s) |
|---|---|---|---|
| Hook | 0–3 s | <…> | <the hook, exactly> |
| Quick payoff + open loop | 3–10 s | <…> | <…> |
| Normal state | | <…> | <…> |
| Turning point | | <the moment happens> | <…> |
| Twist / added value | | <pays off the open loop> | <…> |
| Safety line (health channels) | | <…> | <the channel's required wording> |
| Closing | | <loop back to the hook **or** a light CTA, not both> | <…> |

## 4. Story logic (ask "why?" at every line)
- [ ] **Place and time:** every line fits where and when the scene is
- [ ] **Props:** each prop has a reason to be there and is in place for the whole video (never pops in or out at a cut)
- [ ] **Motivation:** each character has a reason for what they do and say
- [ ] **Cause and effect:** each line follows from the one before; the ending pays off the opening
- [ ] **Staging:** characters never need to stand face to face up close or overlap; if two people share a small space, one can coach from a seat
- [ ] **Without sound:** banners and captions alone still tell the story

`story_logic` for the package (one line per beat):
1. <…>
2. <…>
3. <…>

## 5. Final script
<one paragraph; the hook is the first sentence exactly as written>

- Words: <n> (en 75–150, sweet spot 100–130 · id 62–125, sweet spot 80–105)
- Estimated seconds: <n> (video must stay ≤ 60 s)

## 6. TTS text (`tts.txt`)
Same words as the script; only punctuation, line breaks, pauses and tags may change.

Emotion flow in one line: <e.g. curious → tense → relieved → warm>

Single voice:
```
[curious] <line>
<line>

[tense] <line>
```

Cast (several voices, ElevenLabs cast mode):
```
HOST: [teasing] <line>
GUEST: [whiny] <line>
NARRATOR: <line>
[pause 0.6]
NARRATOR: <line>
```

## 7. Facts and sources (the user checks these in 2 minutes)
| Claim as spoken | Source (title, URL) | Checked on |
|---|---|---|
| <…> | <…> | <YYYY-MM-DD> |

Health or fitness channel:
- [ ] No "cures" claims; safety line spoken; doctor disclaimer in the description
- [ ] Movements stay within the limits in the channel's `style-bible.md`

## 8. Variation (different from the last 3 episodes)
- story: <…>
- setting: <…>
- props: <…>
