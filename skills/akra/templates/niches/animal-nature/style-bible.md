# Style bible: <Your Channel Name> (animal and nature facts)

Example style bible for the "animal and nature facts" starter kit. Every value is a suggestion: change colors, fonts, the guide and the rituals to make the channel your own. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: curious viewers 13+ (teens and adults) who like strange facts about living things, watching on a phone in short breaks
- Channel promise: each video shows one animal or plant and the body part or behaviour that explains something surprising about it
- Style in one sentence: flat cartoon animals with accurate anatomy on a deep forest-green background, cutaways, scale comparisons and habitat maps in sunflower yellow

## 1. Visual identity
- Visual mode: characters (animals) with diagram overlays · Library style: not used (drawn in scenes)
- Drawing style: no outline, flat fill + 2 shadow tones, medium detail (the 3–5 features a biologist would recognize: number of legs, eye position, beak or tooth shape), side view by default
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#16352F` | deep forest green, far layer |
| Main object | natural animal and plant colors | the living thing being explained |
| Accent | `#F2B134` | labels, scale bars, map pins, the part that matters |
| Positive / safe | `#8FD18A` | "fact" stamp, the right way to watch wildlife |
| Warning | `#E46A5E` | "myth" stamp, "keep your distance" only |
| Avoid | red splashes and dark red | read as blood; no gore |

- Typography: banner Fredoka SemiBold · caption Fredoka SemiBold 64 px · minimum text size 32 px
- Logo, watermark, brand line: small channel name bottom-left at y 1290, 50% opacity
- Recurring motifs: a field-notebook page with a dotted grid behind diagrams; a yellow magnifier circle for cutaways; a hand silhouette for scale

## 2. Cast
`not used` by default: the animal is the hero. Optional guide:

| Library id | Name | Role in the story | Fixed traits | Voice |
|---|---|---|---|---|
| `guide` | <name> | holds the field notebook, points at parts, reacts to the twist | wide-brim hat, binoculars on a strap, khaki vest with pockets, rolled sleeves | narrator |

- The guide never touches or holds wild animals; stands at the left edge, at most 25% of the frame width.
- Animals are drawn as animals (no clothes, no human mouths that talk); their mouths only move for real behaviour (eating, calling).
- The mouth of the guide only moves when the guide speaks a quoted line, not with the narrator.

## 3. Expressions and emotion
- Emotional range: wonder, playful surprise, respect for the animal · Not allowed: mocking animals, gore, fear for shock, fake human feelings

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | wonder | the animal does the surprising thing once |
| Explanation | calm, focused | magnifier cutaway on the body part |
| Twist / surprising fact | playful surprise | scale bar jumps beside a hand or a bus |
| Success / understanding | satisfied | the behaviour replays, now with labels |
| Closing | calm | the animal back in its habitat, same frame as the first |

- Eyes (guide): on the body part being explained; animals keep natural eye behaviour (owls do not blink like cartoons).

## 4. Poses and gestures
- Pose set: drawn in scenes · Signature gesture: the guide taps the notebook page on the closing fact
- Gesture meaning: `point` = name a part, `notebook_tap` = the key fact, `binoculars_up` = watch from a distance
- One clear pose per beat, triggered by a word in the narration; deliberate stillness is better than constant motion.
- Anatomy: animal joints and gaits follow the real animal (count legs, check how knees bend in birds and insects).
- Niche movement limits: not used

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Habitat backdrop | default (forest, savanna, reef, pond, desert as fits) | natural daylight, or moonlight for night animals |
| Field-notebook page | cutaways, life cycles, myth vs fact | flat, warm paper on the green background |
| Habitat map | where the animal lives | flat map, range in accent yellow |

- Depth: 3 layers (far habitat blurred, mid plants, sharp animal)
- Main object: side or 3/4 view, 50–75% of the frame width; cutaways inside a magnifier circle
- Recurring props: a hand silhouette and a coin or mug for scale, the field notebook, a small compass on maps
- Forbidden props: real brands and logos, zoo or aquarium logos, cages or tanks shown as a pet-keeping tip, weapons and traps

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: SVG 2.5D
- Tempo: change focus every 2–4 seconds; gentle drift on habitat shots, still camera on cutaways
- Easing: `sine.inOut` for animal motion, `back.out` for labels and stamps
- Transitions: cut or magnifier zoom · Maximum still frame: 3 seconds
- Loop: the last frame matches the first (the animal in its habitat, same pose).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a naturalist friend whispering on a walk
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a soft page flip when the field notebook opens

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: animal center, labels beside the parts, scale bar under the animal, caption y 1185
- Captions: per word, active word in accent yellow, at most 3 words shown
- Banner / pill: at most 3 words, yellow pill with dark green text; "MYTH" and "FACT" stamps in their role colors

## 9. Fixed format
- Opening (1–2 seconds): the animal does the surprising thing once, no explanation yet
- Closing: the guide's notebook tap on the key fact, then back to the opening frame
- Target duration: 35–50 seconds · Structure: hook → open loop → normal life → cutaway or scale → the one explanation → twist → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources` (natural history museums, National Geographic Society, zoo and aquarium education pages, university biology departments, IUCN).
- Audience: not for children (made for kids = No): the channel targets curious viewers 13+; change it if the content is aimed at children (see README, Risks).
- `ai_disclosure`: false (animation + generic TTS)
- Required disclaimer: "Watch wild animals from a distance." on episodes about wild or dangerous animals; "For a sick pet, ask a vet." on episodes about pets
- Forbidden: gore and wounds, tips for catching, feeding or keeping wild animals, pet medical advice, false anthropomorphism, unsourced numbers

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
- <YYYY-MM-DD> · started from the akra "animal and nature facts" starter kit
