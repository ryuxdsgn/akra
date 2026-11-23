# Style bible: <Your Channel Name> (game tips for <Game Title>)

Example style bible for the "game tips" starter kit. Every value is a suggestion: change colors, fonts, the overlays and the rituals to make the channel your own. Sections that do not apply: write `not used`, do not delete them.

## 0. Summary
- Audience: players 16–35 of <Game Title>, from new to mid-level, watching on a phone between sessions
- Channel promise: each video gives one tested tip for <Game Title> that saves time, resources or frustration
- Style in one sentence: short clips of your own gameplay (or a drawn diagram) under bold lime step chips, arrows and mini-maps on a deep navy frame

## 1. Visual identity
- Visual mode: own gameplay clips with diagram overlays, or fully drawn diagrams · Library style: not used
- Drawing style: flat vector overlays, 4 px rounded strokes, no gradients, chips and cards with 24 px corner radius; generic drawn icons for items (never ripped game art)
- Palette by role:

| Role | Color | Used for |
|---|---|---|
| Background | `#101828` | frame around clips, diagram backdrop |
| Panel | `#1E2A44` | comparison cards, mini-map base |
| Accent | `#C6F432` | step chips, route line, the key number |
| Secondary | `#38BDF8` | player position, "you are here", neutral labels |
| Warning | `#F43F5E` | mistakes, "don't", spoiler warning |
| Avoid | colors that match the game's own UI | overlays must read as ours, not as the game's HUD |

- Typography: banner Space Grotesk Bold, uppercase · caption Inter Bold 64 px · numbers Space Grotesk Bold · minimum text size 30 px
- Logo, watermark, brand line: small channel name bottom-left at y 1290, 50% opacity; no publisher or game logo unless the video policy allows it
- Recurring motifs: numbered lime step chips (1, 2, 3) that pop in on the word; a dotted route line that draws itself on the mini-map

## 2. Cast
`not used`: the tip is the hero. No host character, no face cam, no drawn copies of the game's characters.

## 3. Expressions and emotion
- Emotional range: confident, helpful, a little playful ("you'll never miss this again") · Not allowed: rage bait, mocking other players, fake "game-breaking" hype

| Story beat | Expression / reaction | Example |
|---|---|---|
| Hook | intrigue | clip freezes, a lime circle marks the thing most players miss |
| Explanation | calm, clear | step chips appear one by one with the narration |
| Twist / surprising number | punch | the number pops large on a comparison card |
| Success / understanding | satisfied | the result shown side by side: before vs after |
| Closing | calm | back to the first frame, the marked spot now labeled |

- Eyes: not used

## 4. Poses and gestures
- Pose set: not used (no characters) · Signature gesture: the lime circle that "points" at a spot in the clip
- Gesture meaning: circle = look here, arrow = go this way, cross = don't do this
- One overlay action per beat, triggered by a word in the narration.
- Niche movement limits: not used

## 5. Environments and props
| Env | Used for | Time and light |
|---|---|---|
| Gameplay clip in a navy frame | evidence of the tip (own footage only) | as recorded; no color grading that hides the game's look |
| Drawn mini-map | routes, locations | flat, top-down, north up |
| Comparison board | builds, items, choices | flat panels on navy |

- Depth: 2 layers (clip or diagram, overlays on top)
- Main object: the clip fills the frame width at 16:9 inside the 9:16 frame, or is cropped to 9:16 around the action; overlays never cover the part being explained
- Recurring props: step chips, route line, "you are here" pin, version tag "v x.y" top-right
- Forbidden props: trailers, cinematics, press-kit art, other creators' footage, publisher logos beyond the policy, leaked or datamined content

## 6. Motion and camera
- Motion engine: anime.js (`animekit.py`) · Main object: own gameplay clip or SVG diagram
- Tempo: change focus every 2–3 seconds; zoom into the clip on the detail being explained
- Easing: `expo.out` for zooms, `back.out` for chips popping in, linear for the route line drawing
- Transitions: cut or quick wipe · Maximum still frame: 3 seconds
- Loop: the last frame matches the first (same clip frame, same circle).

## 7. Audio
- Narration: Kokoro `am_fenrir`, speed 0.95 · model license Apache-2.0 · tone: a teammate giving a quick tip in the lobby
- Game audio: muted or under −30 dB under the narration (it is not the content); no copyrighted soundtrack as a focus
- Music: calm ambient from the YouTube Audio Library, loudnorm −14 LUFS, volume 0.1, credit in the description
- Signature sound effects: a short "tick" on each step chip

## 8. Composition and on-screen text
- Text safe area: x 90–900, y 160–1330
- Default position: clip or diagram center, step chips to the left, caption y 1185, version tag top-right
- Captions: per word, active word in accent lime, at most 3 words shown
- Banner / pill: at most 3 words, lime pill with navy text; spoiler warning as a rose pill

## 9. Fixed format
- Opening (1–2 seconds): a frozen frame with a lime circle on the thing most players miss (story episodes: "SPOILER" rose pill first)
- Closing: the before/after result side by side, then the version tag "tested in v x.y"
- Target duration: 30–45 seconds · Structure: hook → open loop → the usual way → the tip in numbered steps → proof (clip or numbers) → loop back

## 10. Facts, safety and monetization
- Every factual claim is sourced in `sources`: official patch notes, the publisher's official guide or wiki, in-game text, or "in-game test, tested in version x.y".
- Publisher video policy: <URL> · checked on <YYYY-MM-DD> · monetized videos allowed: <yes/no> · logo use allowed: <yes/no>. Do not monetize until this line is filled.
- Gameplay: only your own; each clip short and transformed by narration and overlays; credit "<Game Title> by <Publisher>, gameplay recorded by <Your Channel Name>" in the description (shot type `stock`).
- Audience: not for children (made for kids = No).
- `ai_disclosure`: true when realistic gameplay footage is used; false for fully drawn episodes
- Required disclaimer: "Not affiliated with or endorsed by <Publisher>." in every description; "Spoiler warning" on story content
- Forbidden: leaks and datamined content, piracy, cheats or mods that break the terms of service, exploits that harm other players, re-uploaded trailers or other creators' footage

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
- <YYYY-MM-DD> · started from the akra "game tips" starter kit
