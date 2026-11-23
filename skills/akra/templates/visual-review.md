# Visual review: <episode id> · render <file name>

Run this after `qa_render.py` passes and **before** the user sees the video. The automatic gates (loudness, loop, duration, flicker, pose QA) do not see most of the defects below; a person (or the main agent session) has to look at frames. Note each item as OK or the fix made; re-render and repeat until all are OK.

## How to look
Use the final MP4, not snapshots (snapshots can differ from the render). Replace `<V>` with the MP4 path and `<S>` with a scratch folder.

```bash
# overview: one frame every 2.5 s, 12 per sheet
ffmpeg -v error -i <V> -vf "fps=1/2.5,scale=360:-1,tile=6x2" -frames:v 2 <S>/sheet%d.png
# motion: every frame (30 fps) of one walk or exercise cycle, cropped to the legs
ffmpeg -v error -ss <t> -t 1.3 -i <V> -vf "fps=30,crop=<w>:<h>:<x>:<y>,scale=150:-1,tile=13x3" -frames:v 1 <S>/legs.png
# faces: 0.1 s steps over a talking or moving stretch, cropped to the heads
ffmpeg -v error -ss <t> -t 2.4 -i <V> -vf "fps=10,crop=<w>:<h>:<x>:<y>,scale=225:-1,tile=6x4" -frames:v 1 <S>/faces.png
# cuts: every frame from 0.2 s before to 0.6 s after each scene change
ffmpeg -v error -ss <cut-0.2> -t 0.8 -i <V> -vf "fps=30,scale=270:-1,tile=6x4" -frames:v 1 <S>/cut.png
```

## Story and layout
- [ ] The story reads without sound: place, time, what the character wants, what changes
- [ ] Nothing important sits in the Shorts UI zones (right-hand buttons, bottom caption and title area)
- [ ] Captions follow the voice word by word and never cover a face or the action
- [ ] On-screen text that must be read is large enough on a phone (≥ 30 px bold at 1080×1920)
- [ ] No empty boxes: a card, meter or timer appears together with its content
- [ ] Time skips are clearly visible (the clock or timer grows, a "+N MIN" chip, then settles)
- [ ] Opening and closing frames match closely, so the loop is smooth

## Characters
- [ ] **Eyes:** open and steady; blinks are sparse and happen on real expression changes, never every few frames
- [ ] **Mouth:** moves only while that character speaks
- [ ] **Size:** characters, pets and props keep consistent sizes across scenes and against each other
- [ ] **Spacing:** two characters never stand nose to nose or overlap bodies; a clear gap at all times
- [ ] **Joints and limbs:** arms and legs connected, hands on what they hold (rail, backrest, knee), no limb through a prop, a pet or another body
- [ ] **Feet:** flat on the floor or step, no floating and no sinking; a planted foot does not slide
- [ ] **Walking:** a visible stride (one foot ahead, one behind), the swing foot lifts, arms swing opposite; the far leg stays readable (darker) where the legs cross
- [ ] **Turning around:** an instant flip with both feet planted; no frame where the body looks squashed or thin
- [ ] **Sitting and standing:** the body moves through the action (lean, push, rise); no pop from seated to standing
- [ ] **Exercise form** matches the source and the channel's movement limits

## Props and cuts
- [ ] Every prop is in place for the whole video; nothing pops in or out at a cut (check each cut frame by frame)
- [ ] Recurring props keep the same position and size after a cut
- [ ] Seats, beds and steps have plausible heights for the characters (seated feet rest on the floor)
- [ ] Props do not merge into one cluttered shape; keep a clear gap between them

## Visual cues (arrows, marks, chips, meters)
- [ ] Each motion arrow starts on the body part it describes and points the way it moves
- [ ] Each check or cross mark sits beside the limb it judges and is visible only while that limb is in that pose
- [ ] Chips line up in the info column; no chip covers a face
- [ ] The meter fills exactly on the spoken counts

## Result
| Item | Found at (s) | Fix | Re-checked |
|---|---|---|---|
| <…> | <…> | <…> | <OK / still open> |

Hand the video to the user only when every item is OK or the user has accepted the open ones.
