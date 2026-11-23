# Style bible: <Your Channel Name> (gentle home exercise)

Example style bible for the "gentle home exercise" starter kit. Every value is a suggestion: change colors, fonts, the cast and the rituals to make the channel your own. Movement limits and safety rules may only become stricter. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: beginners and adults 55+, often less active or a bit stiff, watching on a phone at home and ready to move along
- Channel promise: each video teaches one gentle move you can do safely at home today, with a chair or wall for support
- Style in one sentence: warm flat cartoon in a bright living room, a seated coach and a doer move slowly together, teal arrows show the joint that moves

## 1. Visual identity
- Visual mode: characters with diagram overlays · Library style: `toon` (or not used: drawn in scenes)
- Drawing style: soft dark-brown outline 4 px, flat fill + 1 shadow tone, low detail, side or 3/4 view so the moving joint is clear
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#F4EDE1` | walls, floor, large areas (warm oat) |
| Main object | `#E9A86B` | the chair, the mat, the doer's top |
| Accent | `#2B8C7E` | motion arrows, active caption word, rep counter |
| Positive / safe | `#6BB36B` | the right way, check marks, "support here" |
| Warning | `#D9534F` | "stop" signs and the safety line only |
| Avoid | neon and pure black | tiring for older eyes, harsh on small screens |

- Typography: banner Nunito ExtraBold · caption Nunito Bold 72 px · minimum text size 40 px (older viewers)
- Logo, watermark, brand line: small channel name bottom-left at y 1290, 50% opacity
- Recurring motifs: a round rep counter (1–5) that fills like a clock; a soft teal glow on the working muscle

## 2. Cast
Example cast; replace names and looks with your own.

| Library id | Name | Role in the story | Fixed traits | Voice |
|---|---|---|---|---|
| `coach` | <Coach name> | seated coach, shows the move first, counts reps | sits on a wooden chair, grey short hair, round glasses, teal cardigan, white sneakers | narrator |
| `doer` | <Doer name> | the viewer's stand-in: tries the move, makes the common mistake, then gets it right | slightly round body, orange top, comfy trousers, slippers off, a water bottle nearby | narrator (quoted lines optional) |

- Proportions: head 1.2×, soft rounded bodies, realistic joint positions (no rubber limbs).
- Neither character is called doctor, physio or trainer, on screen or in narration.
- The mouth only moves when that character speaks a quoted line, not with the narrator.

## 3. Expressions and emotion
- Emotional range: warm, encouraging, gently funny, proud · Not allowed: pain as a joke, shaming bodies or age, fake struggle

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | relatable | the doer groans getting up from the sofa |
| Explanation | calm, focused | the coach shows the move slowly, side view |
| Twist / surprising fact | pleasantly surprised | "that's it?" look from the doer |
| Success / understanding | proud | the doer finishes rep 5, small smile |
| Closing | warm | both give the signature thumbs-up from their chairs |

- Eyes: on the moving body part or on the viewer when counting; subtle blink and breathing in every scene.

## 4. Poses and gestures
- Pose set: drawn in scenes (or your library pose set) · Signature gesture: `thumbs_up` from the chair at the close
- Gesture meaning: `point` = the muscle or joint that works, `hand_on_chair` = support reminder, `stop_palm` = the safety line
- One clear pose per beat, triggered by a word in the narration; deliberate stillness is better than constant motion.
- Anatomy: joints bend in one direction only, feet stay planted unless the move says otherwise, the hand really holds the chair.
- Niche movement limits (mandatory):
  - low-impact only: no jumping, hopping, running or sudden twists
  - balance moves always next to a chair back or wall, hand on it or within reach
  - slow tempo: about 2 seconds up, 2 seconds down, at most 5–10 reps shown
  - small comfortable range; never into pain; no deep squats, floor sit-ups or moves lying flat for long
  - breathing out on the effort, never holding the breath
  - no weights heavier than a water bottle

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Living room | default (sturdy chair without wheels, clear floor) | soft morning light from a window |
| Kitchen counter | "do it during" moves holding the counter | warm daylight |
| Hallway wall | balance and wall moves | even indoor light |

- Depth: 3 layers (far room lightly blurred, mid furniture, sharp characters)
- Main object: the characters full-body, 55–70% of the frame height, the moving joint never hidden
- Recurring props: sturdy chair without wheels, water bottle, non-slip mat, a wall clock for the rep counter
- Forbidden props: real brands and logos, rolling chairs, rugs that slide, heavy weights, supplements

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: SVG 2.5D characters
- Tempo: static camera; one slow push-in on the working joint per video; change focus every 3–5 seconds
- Easing: `sine.inOut` for body moves (smooth, never snappy), `back.out` only for the rep counter
- Transitions: soft cut · Maximum still frame: 3 seconds (breathing and blink keep it alive)
- Loop: the last frame matches the first (both characters seated, same pose).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a patient friend moving with you
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a soft wooden "tok" on each counted rep

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: coach left, doer right, rep counter top-right, caption y 1185
- Captions: per word, active word in accent teal, at most 3 words shown, extra contrast (dark text on a light pill)
- Banner / pill: at most 3 words (the move's name), oat pill with dark text; the safety line gets its own red-edged pill

## 9. Fixed format
- Opening (1–2 seconds): the doer's everyday struggle (getting up, reaching, wobbling) and the move's name
- Closing: rep 5 done, the safety line, both thumbs-up from their chairs
- Target duration: 35–50 seconds · Structure: hook → why it matters → coach shows → doer tries (common mistake → fix) → reps together → safety line → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources`, from health authorities (WHO, NHS, CDC, national health services, heart foundations).
- Audience: not for children (made for kids = No).
- `ai_disclosure`: false (animation + generic TTS)
- Required disclaimer: the `disclaimer` text from `channel.json` in every description; a spoken or on-screen safety line in every video
- Forbidden: "cures", "heals" or "reverses" claims, weight-loss or fat-burning promises, personal medical advice, moves outside the movement limits, before/after body pictures

## Sensitive topic
- `sensitive_topic`: `health` · persona: friendly home-exercise companion who moves along with the viewer, with no medical or fitness credentials (YT-CH-2)
- Disclaimer text for every description: "This video is general information, not medical advice. Check with your doctor before starting a new exercise, and stop if you feel pain, dizziness or chest pain." (also in `disclaimer` in `channel.json`)
- Extra forbidden claim words: guaranteed, miracle, melts fat, burns belly fat, heals, detox, anti-aging, no pain no gain (also in `forbidden_words`; the validator adds cure, cures, cured, curing)
- Disclosure plan: none (cartoon animation, no realistic synthetic people)

## Approval
- Sample frames: <render 2–3 style frames and put the PNG paths here>
- Approved by the user on: <YYYY-MM-DD>

## 11. References
- Reference frame: <after the first approved episode>
- Reference episodes: <ep-id per scene type>

## Decision history
- <YYYY-MM-DD> · started from the akra "gentle home exercise" starter kit
