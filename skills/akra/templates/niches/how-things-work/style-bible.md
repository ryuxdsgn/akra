# Style bible: <Your Channel Name> (how everyday things work)

Example style bible for the "how everyday things work" starter kit. Every value is a suggestion: change colors, fonts, the host and the rituals to make the channel your own. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: adults 18–45 who like knowing how things work, watching on a phone in short breaks
- Channel promise: each video opens one everyday object and shows the one mechanism that makes it work
- Style in one sentence: real objects drawn in 2.5D/3D on a dark warm background, the shell turns see-through and cyan arrows show the mechanism

## 1. Visual identity
- Visual mode: real objects with diagram overlays · Library style: not used
- Drawing style: clean vector, no outlines on objects, 2 soft shadow tones, medium detail (3–5 parts that make the object recognizable), 3/4 view by default
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#1B1A1F` | backdrop, far layer |
| Main object | natural material colors | the object being explained (steel, plastic, glass) |
| Accent | `#3FD0E0` | flow arrows, labels, the moving part |
| Positive / safe | `#7BD389` | the right way, check marks |
| Warning | `#FF6B4A` | heat, danger, "do not" only |
| Avoid | pure `#FFFFFF` backgrounds | they flatten the cutaway |

- Typography: banner Inter Black, uppercase · caption Inter Bold 64 px · minimum text size 30 px
- Logo, watermark, brand line: small channel name bottom-left at y 1290, 50% opacity
- Recurring motifs: a thin cyan scan line that sweeps once when the shell turns see-through

## 2. Cast
`not used` by default: the object is the hero. Optional host:

| Library id | Name | Role in the story | Fixed traits | Voice |
|---|---|---|---|---|
| `host` | <name> | points at parts, reacts to the reveal | round glasses, rolled-up sleeves, tool apron, short hair | narrator |

- The host never covers the object; stands at the left edge, at most 30% of the frame width.
- The mouth only moves when the host speaks a quoted line, not with the narrator.

## 3. Expressions and emotion
- Emotional range: curious, surprised, satisfied ("oh, that's why") · Not allowed: mocking the viewer, fake shock

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | curious | the object turns slowly, one part glints |
| Explanation | calm, focused | camera follows the moving part |
| Twist / surprising number | surprised | number pops large beside the part |
| Success / understanding | satisfied | the whole mechanism runs once at full speed |
| Closing | calm | back to the closed object, same angle as the first frame |

- Eyes (if a host is used): look at the part being explained.

## 4. Poses and gestures
- Pose set: drawn in scenes (host optional) · Signature gesture: `point` at the hidden part on its name
- Gesture meaning: `point` = introduce a part, `think` = the question, `thumbs_up` = understood
- One clear pose per beat, triggered by a word in the narration.
- Niche movement limits: not used

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Workbench | default | warm lamp from upper left |
| Kitchen counter / bathroom shelf | object in its real place for the hook | soft daylight |

- Depth: 3 layers (far blurred room, mid workbench, sharp object)
- Main object: 3/4 view, 60–80% of the frame width, materials clear (brushed steel, matte plastic, glass)
- Recurring props: a small ruler for scale, a screwdriver resting on the bench
- Forbidden props: real brands and logos, trademarked product shapes

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: Three.js 3D (`three3d.py`) or SVG 2.5D
- Tempo: change focus every 2–4 seconds; slow orbit or dolly while explaining
- Easing: `expo.out` for camera, `back.out` for labels popping in
- Transitions: cut or push-in · Maximum still frame: 3 seconds
- Loop: the last frame matches the first (closed object, same angle).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a friend explaining over coffee
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a soft "click" when the shell turns see-through

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: object center, labels to the left of the parts, caption y 1185
- Captions: per word, active word in accent cyan, at most 3 words shown
- Banner / pill: at most 3 words, white pill with dark text

## 9. Fixed format
- Opening (1–2 seconds): the object in its real place, one part glints
- Closing: the mechanism runs once at full speed, then the shell closes
- Target duration: 35–50 seconds · Structure: hook → open loop → normal use → cutaway → the one mechanism → twist → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources`.
- Audience: not for children (made for kids = No).
- `ai_disclosure`: false (animation + generic TTS)
- Required disclaimer: "Do not open powered or pressurized devices yourself." on episodes about mains, gas or pressure
- Forbidden: brand names and logos, unsafe DIY instructions

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
- <YYYY-MM-DD> · started from the akra "how everyday things work" starter kit
