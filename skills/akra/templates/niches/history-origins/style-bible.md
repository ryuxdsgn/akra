# Style bible: <Your Channel Name> (history and origins)

Example style bible for the "history and origins" starter kit. Every value is a suggestion: change colors, fonts, the host and the rituals to make the channel your own. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: adults 18–55 who like trivia, words and "why do we do that" questions, watching on a phone in short breaks
- Channel promise: each video traces one everyday object, custom or word back to where it came from, and says what is known and what is only a story
- Style in one sentence: warm paper-and-ink cartoon world, objects morph back through time along a timeline, generic period characters act out the origin

## 1. Visual identity
- Visual mode: mixed (objects, timelines, maps, cartoon characters) · Library style: `toon` (optional) / not used
- Drawing style: 3 px dark ink outline, flat color fill + 1 soft shadow, light paper grain texture on large areas, side or 3/4 view, medium detail
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#F1E4C8` | paper, maps, large areas |
| Main object | `#2E2A36` ink lines + muted period colors | the object, character outlines, text on paper |
| Accent | `#C8402F` | year marker, key word, dashed route on maps |
| Positive / safe | `#3D7A5F` | "what the records show", check marks |
| Warning | `#E0A23B` | "one story says" / disputed stamp only |
| Avoid | sepia photo filters, `#8B4513`-style brown everywhere | looks like a fake archive photo and muddies the paper |

- Typography: banner Playfair Display Black · caption Inter Bold 64 px · minimum text size 30 px
- Logo, watermark, brand line: small channel name bottom-left at y 1290, 50% opacity
- Recurring motifs: a timeline ruler along the bottom with a red sliding year marker; dashed red routes on a paper map when something travels between places

## 2. Cast
Fixed host is optional; guest period characters appear in most episodes.

| Library id | Name | Role in the story | Fixed traits | Voice |
|---|---|---|---|---|
| `archivist` | <name> | opens the drawer of history, reacts to the twist | round glasses on a chain, green cardigan, ink-stained fingers, pencil behind the ear | narrator |

- Proportions and body style: head 1.2×, simple rounded bodies, no realistic faces.
- Guest characters (historical): generic cartoon look from the library + period costume (toga, ruff collar, tricorn hat, apron), one look per episode. Never a likeness of a real person: no portrait features, no copies of paintings or photos. A named figure is shown as a generic character with a name label only.
- The mouth only moves when that character speaks a quoted line, not with the narrator.

## 3. Expressions and emotion
- Emotional range: curious, amused, "huh, really?" · Not allowed: mocking past people or cultures, jokes about war, religion or suffering

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | curious | today's object sits on the table, the year marker starts to slide back |
| Explanation | calm, interested | a period character uses the old version of the object |
| Twist / surprising origin | amused surprise | the archivist's glasses slip, the old word appears large |
| Success / understanding | satisfied | the timeline shows every version in a row |
| Closing | warm | the object morphs back to today's version |

- Eyes: look at the object or word being explained; subtle blink and breathing in all scenes with characters.

## 4. Poses and gestures
- Pose set: drawn in scenes or library `toon` set · Signature gesture: the archivist `point`s at the year marker when it stops
- Gesture meaning: `point` = introduce a date or object, `think` = the question, `shrug` = "one story says"
- One clear pose per beat, triggered by a word in the narration.
- Niche movement limits: not used

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Modern table | the hook and the loop back | soft daylight |
| Paper map | when an object or word travels | flat, no light direction |
| Period room (market, kitchen, workshop) | the origin scene | warm candle or window light |

- Depth: 3 layers (far paper texture, mid scene, sharp object or character)
- Main object: 3/4 view, 50–70% of the frame width; each historical version sits on the same spot so the morph reads clearly
- Recurring props: the timeline ruler, a card-catalog drawer, a magnifying glass for close-ups
- Forbidden props: photos or paintings of real people, flags or religious symbols used as decoration, real brands and logos

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: SVG 2.5D
- Tempo: change focus every 2–4 seconds; the year marker slides while the object morphs
- Easing: `expo.inOut` for the year marker, `back.out` for labels and stamps
- Transitions: page turn or morph · Maximum still frame: 3 seconds
- Loop: the last frame matches the first (today's object on the table, same angle).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a friend telling a good story at dinner
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a soft "tape rewind" when the year marker slides back

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: object or character center, archivist at the left edge (at most 30% of the width), timeline at y 1080, caption y 1185
- Captions: per word, active word in accent red, at most 3 words shown
- Banner / pill: at most 3 words, paper card with ink text; the year in large serif numbers; the "ONE STORY SAYS" stamp in amber

## 9. Fixed format
- Opening (1–2 seconds): today's object on the modern table, the year marker begins to slide back
- Closing: the year marker runs forward to today and the object morphs back to its modern version
- Target duration: 35–50 seconds · Structure: hook → open loop → today's object → rewind → origin scene → twist (story vs record) → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources`; disputed origins are called "one story says" and the story's source is given too.
- Audience: not for children (made for kids = No).
- `ai_disclosure`: false (animation + generic TTS, no realistic people)
- Required disclaimer: not used
- Forbidden: likenesses of real people, myths presented as fact, taking sides on war, religion or politics, real brands and logos

## Sensitive topic
- `sensitive_topic`: not used
- Disclosure plan: none

## Approval
- Sample frames: <render 2–3 style frames and put the PNG paths here>
- Approved by the user on: <YYYY-MM-DD>

## 11. References
- Reference frame: <after the first approved episode>
- Reference episodes: <ep-id per scene type>

## Decision history
- <YYYY-MM-DD> · started from the akra "history and origins" starter kit
