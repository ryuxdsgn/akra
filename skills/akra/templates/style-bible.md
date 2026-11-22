# Style bible: <channel name>

One file per channel. The agent reads it before writing a script, storyboard or build, so **write only the rules that apply now**, short and specific. When a rule changes, update its section and add one line to "Decision history" at the very bottom. Sections that do not apply to this channel: write `not used`, do not delete them.

If the channel uses the asset library (`channels/<id>/library.json`), write characters, poses and environments as **library ids** so the agent uses `L.character(...)`, `L.pose(...)`, `L.env(...)` directly.

## 0. Summary
- Audience: <who, age, situation while watching>
- Channel promise: <one sentence: what the viewer gets from each video>
- Style in one sentence: <e.g. "warm sticker-style cartoon in a living room" / "real 2.5D objects with diagrams on top">

## 1. Visual identity
- Visual mode: <diagram / real objects / characters / mixed> · Library style: <`hw` / `toon` / not used>
- Drawing style: <outline (color, thickness), flat color fill + number of shadows, level of detail, default perspective>
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#______` | walls, sky, large areas |
| Main object | `#______` | the object being explained |
| Accent | `#______` | key words, flow, highlights |
| Positive / safe | `#______` | check marks, the right way |
| Warning | `#______` | only for "careful/stop" |
| Avoid | `#______` | <reason> |

- Typography: title/banner <font, weight> · caption <font, size px> · minimum text size <px>
- Logo, watermark, brand line: <file in `channels/<id>/brand/`, position in the frame>
- Recurring motifs: <e.g. thin diagonal lines, thin grid, circular spotlight>

## 2. Cast
Write `not used` if the channel has no characters. One row per fixed character; the look does not change between episodes.

| Library id | Name | Role in the story | Fixed traits (silhouette, hair, clothes, accessories, colors) | Voice |
|---|---|---|---|---|
| `<id>` | <name> | <e.g. lazy viewer / coach / inventor> | <3–5 traits that make them recognizable from afar> | <voice> |

- Proportions and body style: <e.g. head 1.25×, heavy body `girth` 1.22>
- Guest characters (historical, viewer): <rule, e.g. look from the library + costume, one look per episode>
- The mouth only moves when that character speaks, it does not follow the narrator.

## 3. Expressions and emotion
- The channel's emotional range: <e.g. warm, playful, awe> · Not allowed: <e.g. mocking, pain as a joke, exaggerated fear>

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | <e.g. startled, curious> | <character + moment> |
| Explanation | <calm, focused on the object> | |
| Twist / surprising number | <shocked, "!?"> | |
| Success / understanding | <happy, relieved> | |
| Closing | <the channel's signature expression> | |

- Eyes: <e.g. looking at the object being explained; subtle blink and breathing in all scenes with characters>

## 4. Poses and gestures
- Pose set: <library set id, or `drawn in scenes`> · Signature gestures: <pose name + when it is used>
- Gesture meaning: <e.g. `point` = introduce a part, `think` = a question, `thumbs_up` = success>
- One clear pose per beat, triggered by a word in the narration; deliberate stillness is better than constant motion.
- Anatomy: joints bend in one direction only, the hand reaches the target it points at.
- Niche movement limits: <e.g. only low-risk movements, no jumping / not used>

## 5. Environments and props
| Library env id | Used for | Time and light |
|---|---|---|
| `<id>` | <which scene> | <e.g. bright morning from the window> |

- Depth: <e.g. 3–4 layers (far strongly blurred, mid lightly blurred, sharp object, dark near) / flat background>
- Main object: <e.g. real object in 3/4 view, filling 60–80% of the frame width, clear material, diagram as a layer on top>
- Recurring props: <channel-specific items, e.g. bolster, whistle, habit calendar>
- Forbidden props: real brands and logos, <others>

## 6. Motion and camera
- Tempo: <e.g. change focus every 2–4 seconds / static camera for older viewers>
- Easing and motion style: <e.g. pop-in `back.out`, small squash, shake on the twist>
- Transitions: <cut / push-in / zoom> · Maximum still frame: <seconds>
- Loop: the last frame connects to the first frame (QA checks SSIM ≥ 0.95).

## 7. Audio
- Narration: <provider / voice / settings> · model license: <commercial, source> · tone: <e.g. an engineer friend telling a story over coffee>
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description.
- Signature sound effects: <e.g. a whistle at the start, a "ding" on each rep / not used>

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330 (safe for YouTube, TikTok and Facebook)
- Default position: character <left/right>, main object <center>, caption <y px>, brand line <y px>
- Captions: per word, active word colored <accent>, at most <3–4> words shown, <color per speaker if any>
- Banner / pill: at most <3–4> words, <shape and color>; cut text, show with acting, icons and arrows.

## 9. Fixed format
- Opening (1–2 seconds): <signature ritual or visual hook>
- Closing: <ritual, signature gesture, closing sentence>
- Target duration: <seconds> · Structure: <e.g. hook → problem → mechanism → twist → closing>

## 10. Facts, safety and monetization
- Every factual claim is sourced; sources are noted in the Episode Package (`sources`).
- Audience: not for children (made for kids = No), except <reason>.
- `ai_disclosure`: <true/false + reason; see references/package-qa.md, e.g. animation + generic TTS → false, a voice cloned from someone else → true>
- Required disclaimer: <e.g. "not a substitute for a doctor's advice" for health / not used>
- Forbidden: <e.g. "cures" claims, real people without permission, copyrighted assets>

## Sensitive topic
- `sensitive_topic`: <`health` / `finance` / not used> · persona: <honest description, no doctor or financial-adviser credentials (YT-CH-2)>
- Disclaimer text for every description: <exact text, also in `disclaimer` in channel.json / not used>
- Extra forbidden claim words: <list, also in `forbidden_words` / not used>
- Disclosure plan: <which content would be realistic synthetic media and needs the label (YT-CH-4) / none>

## Approval
Style-bible gate (references/channel-setup.md): 2–3 sample style frames rendered from this file, approved by the user before the first episode.
- Sample frames: <PNG paths>
- Approved by the user on: <YYYY-MM-DD> (same date as `style_approved_on` in channel.json)

## 11. References
- Reference frame: <PNG path or the episode that best represents the current style>
- Reference episodes: <ep-id for each scene type>

## Decision history
One line per decision, newest on top. The content is already reflected in the sections above.
- <YYYY-MM-DD> · <short decision> · from <ep-id>
