# Style bible: <Your Channel Name> (everyday psychology)

Example style bible for the "everyday psychology" starter kit. Every value is a suggestion: change colors, fonts, the character and the rituals to make the channel your own. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: adults 18–40 curious about their own habits, watching on a phone in the evening or on a commute
- Channel promise: each video explains one everyday behavior with real research and ends with one small thing to try
- Style in one sentence: a flat cartoon everyperson acts out the wrong way and the right way on a soft lavender set, with simple brain and process diagrams popping up beside them

## 1. Visual identity
- Visual mode: drawn characters with simple diagrams · Library style: not used (or your own registered everyperson)
- Drawing style: flat vector, 3 px dark ink outline on characters, no outline on backgrounds, 1 soft shadow tone, rounded shapes, low detail
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#EFE9FB` | room wall, diagram backdrop |
| Ink | `#2B2540` | outlines, text, the everyperson's hair |
| Accent | `#FF8A3D` | thought bubbles, process arrows, the key word |
| Evidence-based / right way | `#14B8A6` | FACT stamp, the right-way scene, check marks |
| Myth / wrong way | `#C2255C` | MYTH stamp, the wrong-way scene, crosses |
| Avoid | realistic brain anatomy, gore, clinical blues | it should feel friendly, not like a hospital |

- Typography: banner Fredoka Bold, uppercase · caption Nunito ExtraBold 64 px · minimum text size 30 px
- Logo, watermark, brand line: small channel name bottom-left at y 1290, 50% opacity
- Recurring motifs: a small tangerine thought bubble above the everyperson's head that shows what the brain is "saying"; a rubber-stamp MYTH / FACT that thumps onto the screen

## 2. Cast
| Library id | Name | Role in the story | Fixed traits | Voice |
|---|---|---|---|---|
| `everyperson` | <name> | does the everyday behavior, wrong way then right way | round head, simple dot eyes, messy short hair in ink color, oversized tangerine hoodie, gray trousers, no age or gender cues beyond that | narrator |
| `brain` (optional) | — | a small cartoon brain in the thought bubble that reacts | pink-lavender blob with two dot eyes, no anatomy detail | none |

- The everyperson is generic and relatable: never tied to a gender, age group, nationality or condition for a joke.
- The mouth only moves when the everyperson speaks a quoted line, not with the narrator.

## 3. Expressions and emotion
- Emotional range: relatable, gently funny, kind, "oh, that's me" · Not allowed: shaming the viewer, mocking anyone with a mental-health condition, fear or doom

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | caught in the act | the everyperson freezes mid-habit, looks at the camera |
| Explanation | curious | thought bubble opens, process diagram appears beside it |
| Twist / surprising number | surprised | eyes wide, the MYTH or FACT stamp thumps down |
| Success / understanding | relieved, proud | the right-way version works, small teal check sparkle |
| Closing | calm smile | same pose as the first frame, now doing the right way |

- Eyes: look at the diagram while it is explained, at the camera on the hook.

## 4. Poses and gestures
- Pose set: drawn in scenes · Signature gesture: `facepalm` on the wrong-way gag
- Gesture meaning: `facepalm` = the common mistake, `think` = the question, `point` = the diagram, `thumbs_up` = the right way works
- One clear pose per beat, triggered by a word in the narration.
- Niche movement limits: not used

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Living room / desk | default (work, phone, procrastination) | soft evening lamp |
| Bedroom | sleep topics | dim, blue night window |
| Shop aisle / phone shopping screen | money and shopping biases | bright, flat |
| Diagram space | process and brain diagrams | plain lavender, no room |

- Depth: 2–3 layers (flat room, everyperson, diagram or thought bubble on top)
- Main object: the everyperson, 40–55% of the frame height, centered or left; diagrams on the right
- Recurring props: a phone, a to-do list, a coffee mug, a price tag
- Forbidden props: pills and medication, real brands and logos, real people's faces, realistic brain scans presented as evidence

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: SVG 2D
- Tempo: change focus every 2–4 seconds; gentle push-in on the face for reactions
- Easing: `back.out` for the stamp and the thought bubble, `sine.inOut` for character idle, `expo.out` for camera
- Transitions: cut, or a swipe split from wrong way to right way · Maximum still frame: 3 seconds
- Loop: the last frame matches the first (same pose and room, now the right way).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a warm friend, slightly amused, never preachy
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a soft "thump" when the MYTH / FACT stamp lands

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: everyperson left or center, diagram right, caption y 1185
- Captions: per word, active word in accent tangerine, at most 3 words shown
- Banner / pill: at most 3 words, ink pill with lavender text; MYTH / FACT stamps in their own colors

## 9. Fixed format
- Opening (1–2 seconds): the everyperson caught mid-habit (phone in hand, cart full), looks at the camera, thought bubble pops
- Closing: the right-way version plays once, a teal check appears, then back to the opening pose
- Target duration: 35–50 seconds · Structure: hook → open loop → the familiar behavior → what's going on (diagram) → what research shows → one small thing to try → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources`: peer-reviewed reviews or meta-analyses, university psychology departments, APA, national health services for sleep. Say "on average" or "in studies"; name replication failures where they exist.
- Audience: not for children (made for kids = No).
- `ai_disclosure`: false (animation + generic TTS)
- Required disclaimer: "General information, not medical or mental-health advice." on any episode about sleep problems, stress or mood; mental-health episodes also follow "Sensitive topic" below
- Forbidden: diagnosing, therapy or cure claims, medication advice, pop-psych myths presented as true (learning styles, left/right brain), stereotyping groups

## Sensitive topic
- `sensitive_topic`: not used by default. If the channel covers mental health or medical sleep problems: `health`.
- Disclosure plan: none by default. With `health`: the disclaimer "This video is general information, not medical or mental-health advice. If you are struggling, talk to a doctor or a licensed mental-health professional." on screen at the end and first in the description; suicide or self-harm topics also link a crisis line for the audience's country.

## Approval
- Sample frames: <render 2–3 style frames and put the PNG paths here>
- Approved by the user on: <YYYY-MM-DD>

## 11. References
- Reference frame: <after the first approved episode>
- Reference episodes: <ep-id per scene type>

## Decision history
- <YYYY-MM-DD> · started from the akra "everyday psychology" starter kit
