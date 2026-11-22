# Mode `shots`: HyperFrames scene storyboard

**AI video is weak at explaining concepts** (abstract AI clips leave viewers confused). All visuals are built as code and rendered with HyperFrames (see references/build.md): animated diagrams, real objects and simple drawn characters. No generative AI video or images.

## Splitting into scenes
- **9:16** format, 1080×1920.
- One scene per narration sentence or phrase; each scene lasts **2–6 seconds** (a fast rhythm protects retention). Inside a scene longer than 3 seconds, plan a change of focus (zoom, pan, pop-in) so no frame stays still for more than 3 seconds.
- Timecodes `t_start`/`t_end` in seconds, covering the whole narration **without gaps**. The first scene starts at 0. After the voiceover is done, timecodes are adjusted to the real word timing.
- Scene types:
  - `diagram` (**default**): a HyperFrames scene. The `prompt` field holds the scene description: the object, what moves, which arrows/labels appear, and their order.
  - `stock`: licensed, credited footage (e.g. gameplay), only if the channel's style bible allows it. The source credit goes in the description.

## Writing a `diagram` scene description
Write in English (scene descriptions are internal; on-screen text still uses the channel language), one short paragraph:

`[object from the style bible], [what moves + direction], [arrows/labels that appear and when], [camera focus: zoom to which part]`

If the style bible asks for an environment, also name the **place** at the start of the description (e.g. `Night city street, lamp-lit sidewalk: ...`).

If the style bible uses **cinematic depth** (4 layers + depth of field), the description must state these three things in one opening sentence:
- **Layers:** the content of the far / mid / near layers (near may be "none").
- **Focus:** the sharpest object (always the main object).
- **Light:** the visible light source + the key light direction and rim light color.

If the style bible asks for **real objects**, also add:
- **Material:** the main object's material + 2–3 small details that make it recognizable (e.g. `brushed steel shell, perforated door mesh, rubber feet`).
- **Overlay:** if the scene explains something invisible (heat, current, pressure), write it as a layer on top of the object (`thermal overlay on the pan`), do not replace the object with an abstract shape.

If the scene contains **people** (historical figures, inventors, "you" the viewer), draw them as a **cartoon character** (SVG drawn in the scene, or a library item if the channel has a rig), not a silhouette:
- **Cast:** character name + a fixed look (hair, clothes, accessories) that stays the same in all of the episode's scenes, e.g. `Host: parted dark hair, round glasses, white lab coat, navy tie`. Children use child proportions (big head).
- **Acting:** one pose per beat (e.g. `neutral`, `point`, `think`, `surprise`, `happy`), triggered by a **word** in the narration (`point on "first"`). Emotion comes from the approved story, not guessed from the transcript.
- **Gaze:** where the eyes look (the object being explained).
- The mouth does **not** move with the narrator; lip-sync is only for quotes spoken by that character themselves.
- A character does not replace the real object: they point at/hold/react to the object, and the object remains the visual hero.

Format: `Layers: far <...>, mid <...>, near <...>. Focus: <hero>. Material: <material + details>. Light: <source>, warm key from <direction>, cyan rim from <direction>. Then: <action as usual>`
With a character, add after `Focus`: `Cast: <character> <position>, <pose> on "<word>", gaze <target>.`

Example:
> Ballpoint pen tip rolls across paper; at 1s the barrel turns translucent to reveal the ink tube; cyan arrows show ink flowing down onto the ball; label "ball socket" fades in; slow zoom to the tip.

Example with cinematic depth:
> Layers: far rainy night street with lit shop windows and bokeh, mid car dashboard with glowing screen, near blurred A-pillars. Focus: windshield wiper. Light: street lamps through the windshield, warm key from upper left, cyan rim from the screen on the right. Then: the wiper arm sweeps once and the rain sensor glows; cyan label "rain sensor" pops in above.

Example with a character:
> Layers: far workshop wall with a tool rack, mid blueprint of a windmill, near none. Focus: blueprint. Cast: Host (lab coat, round glasses) left of the board, think on "wonder", point at the blades on "first", gaze the blueprint. Light: ceiling lamp, warm key from upper right. Then: pill "TURNS WIND INTO WORK" pops under the windmill.

Rules:
- Real objects first, diagrams later: plain boxes, blobs or icons are only allowed for things that are truly invisible (molecules, waves). Everyday objects are always drawn as the object itself.
- One visual idea per scene. If you need two ideas, split into two scenes.
- Labels are allowed and encouraged, but at most 3 words and they must not cover the caption below.
- Follow the palette and shapes in the active channel's `style-bible.md` so all episodes look like one series.
- Accuracy matters more than beauty: the direction of force, flow and order of motion must match the source in the script.
- The opening scene (0–2 seconds) must show the object or its paradox right away. Do not open with a title.

## Policy gate
YT-AUTH-2 (setting and props differ from the last 3 episodes), YT-COPY-2 and YT-SYN-1 in youtube-policy.md.

## Output
Table `# | t_start–t_end | narration | type | scene description`. Save to `shots[]` in the Episode Package. Continue to the `build` mode.
