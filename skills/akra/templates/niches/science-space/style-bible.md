# Style bible: <Your Channel Name> (science and space facts)

Example style bible for the "science and space facts" starter kit. Every value is a suggestion: change colors, fonts, the guide probe and the rituals to make the channel your own. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: adults 16–45 who like space and "why does that happen" questions, watching on a phone in short breaks
- Channel promise: each video answers one science or space question with one picture that makes it obvious
- Style in one sentence: clean vector and Three.js planets on a deep navy star field, one shared ruler for scale, amber highlights mark what matters

## 1. Visual identity
- Visual mode: diagram with real-looking planets and weather · Library style: not used
- Drawing style: clean vector, no outlines on planets, soft terminator shadow (day/night edge) on every sphere, thin 3 px line work for diagrams, cutaways as clean wedges with flat layer colors
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#0B1026` | deep space, night sky |
| Main object | natural planet colors | the planet, star or cloud being explained |
| Accent | `#FFB547` | highlights, the ruler, labels, the moving particle |
| Positive / safe | `#5EEAD4` | "this is the real answer", check marks |
| Warning | `#FF5470` | heat, radiation, "myth" stamp only |
| Avoid | pure `#000000` | crushes into blocky noise after compression |

- Typography: banner Space Grotesk Bold, uppercase · caption Space Grotesk Bold 64 px · minimum text size 30 px
- Logo, watermark, brand line: small channel name bottom-right at y 1290, 50% opacity
- Recurring motifs: a faint star field with slow parallax; an amber scale ruler that stays on screen and rescales when the camera pulls back

## 2. Cast
`not used` by default: the planet or process is the hero. Optional guide:

| Library id | Name | Role in the story | Fixed traits | Voice |
|---|---|---|---|---|
| `probe` | <name> | small round probe that flies to the subject and points with a light beam | round body, two thin antennae, one amber eye light, small solar panels | not used (narrator only) |

- The probe never covers the subject; at most 15% of the frame width.
- The probe has no mouth; it reacts with its eye light (blink, widen, tilt).

## 3. Expressions and emotion
- Emotional range: wonder, surprise, calm understanding · Not allowed: fear-bait, doom, mocking "you didn't know this?"

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | wonder | a tiny dot in the star field grows into the subject |
| Explanation | calm, focused | particles or arrows move through the process slowly |
| Twist / surprising number | surprise | the ruler snaps out to its full length, number pops large |
| Success / understanding | satisfied | the whole process runs once at full speed |
| Closing | calm wonder | pull back until the subject is a dot again |

- Eyes (if the probe is used): the eye light faces the part being explained.

## 4. Poses and gestures
- Pose set: drawn in scenes (probe optional) · Signature gesture: the probe's light beam lands on the key part on its name
- Gesture meaning: beam = introduce a part, eye tilt = the question, eye widen = the twist
- One clear action per beat, triggered by a word in the narration.
- Niche movement limits: not used

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Deep space | planets, stars, scale | light from the Sun's side (left by default) |
| Sky over a horizon | weather and sky questions | daylight or night, matching the question |
| Cutaway wedge | inside a planet or star | flat layer colors, labels on the right |

- Depth: 3 layers (far star field, mid subject, near particles or labels)
- Main object: sphere or cloud at 50–70% of the frame width; for comparisons both objects stand on the same ruler
- Recurring props: the amber ruler, an Earth icon used as the unit of size
- Forbidden props: agency logos, mission patches, photos, real spacecraft markings

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: Three.js 3D (`three3d.py`) for planets, SVG for diagrams and labels
- Tempo: change focus every 2–4 seconds; slow zoom or pull-back while explaining
- Easing: `expo.inOut` for scale pull-backs, `back.out` for labels popping in
- Transitions: zoom through (a dot becomes the next subject) or cut · Maximum still frame: 3 seconds
- Loop: the last frame matches the first (the subject as a dot in the same star field).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a friend pointing at the night sky
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a soft low "whoosh" on each scale pull-back

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: subject center, labels to the right of the parts, ruler at y 1080, caption y 1185
- Captions: per word, active word in accent amber, at most 3 words shown
- Banner / pill: at most 3 words, navy pill with amber outline and white text; use a "NOT TO SCALE" tag whenever sizes and distances are compressed

## 9. Fixed format
- Opening (1–2 seconds): a single dot in the star field zooms in and becomes the subject
- Closing: the process runs once at full speed, then the camera pulls back until the subject is a dot again
- Target duration: 35–50 seconds · Structure: hook → open loop → what you see → zoom in / cutaway → the one cause → twist (scale or number) → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources`; numbers are taken from the source page and rounded with "about".
- Audience: not for children (made for kids = No).
- `ai_disclosure`: false (animation + generic TTS)
- Required disclaimer: not used
- Forbidden: agency logos and anything that looks official, unsettled ideas presented as fact, doom or fake-danger hooks, likenesses of real astronauts or scientists

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
- <YYYY-MM-DD> · started from the akra "science and space facts" starter kit
