# Shot plan: <episode id> · <channel>

A fill-in sheet for the `shots` mode (`references/shot-plan.md`). Fill it after the script is approved (its `story_logic` lines are the input). Rows go into `shots[]` of the Episode Package; the scene description column becomes `prompt`. Timecodes are adjusted to the real word timing after the voiceover.

## 0. Setup for the whole episode
- **Place and time:** <e.g. small living room, morning daylight> (one place unless the story moves)
- **Cast and fixed looks:** <character: hair, clothes, accessories> (same in every scene)
- **Props on set from the first frame:** <every prop the story uses, with its spot> (nothing appears only when needed)
- **Main object / hero:** <what the camera returns to>
- **Info column and safe areas:** text stays inside x 90–900, y 160–1330 (1080×1920); captions at the bottom
- **Different from the last 3 episodes:** setting <…> · props <…> · story <…>

## 1. Shots
Each shot 2–8 seconds (the validator's range; 2–6 is the target rhythm). Inside a shot longer than 3 seconds, plan a change of focus. No gaps between shots; the first starts at 0.

| # | t_start–t_end | Narration (exact words) | Type | What we see (place, hero, action) | Cast: pose on "word", gaze | Cues and text (arrow, mark, chip, meter, label ≤ 3 words) | Camera | Props state at the end |
|---|---|---|---|---|---|---|---|---|
| 1 | 0–<t> | <hook> | diagram | <the object or its paradox right away, no title card> | <…> | <banner that says the hook> | <…> | <…> |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |
| 6 | | | | | | | | |
| 7 | | | | | | | | |
| 8 | | | | | | | | |
| 9 | | | | | | | | |
| 10 | | | | | | | | |

Scene description (`prompt`) format, one short English paragraph per shot:
`[place]: [hero object], [what moves + direction], [cues and when they appear], [camera focus]`
With a character, add: `Cast: <name> <position>, <pose> on "<word>", gaze <target>.`

## 2. Continuity check (one line per prop or state that carries across cuts)
| Prop or state | Set in shot | Changes in shot (action shown) | Still true at the end |
|---|---|---|---|
| <chair at left wall> | 1 | — | yes |
| <character sitting> | 2 | 5 (stands up, rise is shown) | standing |

- [ ] Nothing pops in or out at a cut
- [ ] Every state change (sit → stand, pick up → put down, day → night) is shown, not cut around
- [ ] Two characters never share the same spot or stand nose to nose
- [ ] The last shot can loop back into the first (same framing or a matching object)

## 3. Scene patterns (pick, then adapt; do not reuse a whole episode's sequence)
| Pattern | Use for | Beats | Cues |
|---|---|---|---|
| **Reveal / cutaway** | how a thing works inside | whole object → shell turns see-through → the moving part works → zoom to it | label on the part, flow arrows |
| **Before → after** | a fix, a habit, a change | wrong state → the change → right state, same framing | cross mark, then check mark |
| **Wrong then right (gag)** | a common mistake | the character does it wrong → small comic result → does it right | cross on the wrong limb or step, check on the right one |
| **Coach + doer** | instructions with two characters | coach seated or to the side, doer in the middle; the coach points, the doer performs | chip with the move name, meter for counts |
| **Rep counter** | exercises, steps, sets | the action repeats on the spoken counts | meter fills exactly on each count |
| **Time skip** | "after 10 minutes", daily habits | the clock or timer grows, the hands move, it settles back | chip "+N MIN" |
| **Step list** | a procedure | one step per shot, the same framing, a number in the corner | numbered chip |
| **Scale comparison** | sizes, amounts, distances | the familiar object first, then the new one beside it | label with the number |
| **Map / route** | places, journeys, flows | the map draws on, a route traces, a pin pops | arrow along the route, place labels |
| **Timeline** | history, stages | the line draws left to right, events pop at their dates | date labels |
| **Myth vs fact** | a common belief | the belief shown → stamped "myth" → the fact shown | cross, then check |

## 4. Before building
- [ ] Every shot matches a `story_logic` line
- [ ] Every factual picture (direction of flow, order of steps, form of a movement) matches the source in the script
- [ ] On-screen text is in the channel language and readable on a phone (≥ 30 px bold)
- [ ] Health or fitness: movements stay within the limits in `style-bible.md`, and the safety line has its own shot or chip
