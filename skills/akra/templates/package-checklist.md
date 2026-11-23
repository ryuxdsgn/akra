# Package checklist: <episode id> · <channel>

A fill-in sheet for the `package` mode (`references/package-qa.md`). Fill it after the user has watched and approved the render. The values go into the Episode Package; the validator must print `OK` before any upload.

## 0. Ready to package?
- [ ] `qa_render.py` PASS on the final MP4 · file: <render path, contains the episode id>
- [ ] Visual review done (`templates/visual-review.md`), every item OK
- [ ] The user watched and approved this render on <YYYY-MM-DD> → `status: "edited"`, `approved_on`

## 1. Title (channel language)
- Candidates (≤ 60 characters for `en`, ≤ 70 for `id`; main keyword included; no exaggeration):
  1. <…> (<n> chars)
  2. <…> (<n> chars)
  3. <…> (<n> chars)
- **Chosen:** <…> · the video really answers it: [ ]

## 2. Description
```
<1–3 sentences of context that add something the video does not say>

Source: <title or site> (<URL>)
<Disclaimer, on a sensitive-topic channel: the channel's fixed wording, e.g. a doctor disclaimer>
Voice: <name, model, license>
Music: "<track>" by <artist>, <library or license>
<Footage: <source and license>, if any>

#shorts #<niche> #<niche> #<channel tag>
```
- [ ] Every factual claim in the video has a source here or in `sources`
- [ ] Voice and music credits match what is actually in the render (`music_source`)

## 3. Hashtags
3–5, each `#word`; always `#shorts` on YouTube, plus 2–4 niche tags: <…>

## 4. Pinned comment (optional)
<one question that invites a real answer, or a short follow-up tip; no "subscribe" begging>

## 5. Other platforms (`platform_copy`, if the channel posts there)
| Platform | Caption | Hashtags (no `#shorts`) | Notes |
|---|---|---|---|
| Facebook Reels | <1–2 sentences + a direct call to action> | <3–5> | cover frame `cover_at`: <seconds, a clear moment of the action> |
| Instagram Reels | <same as Facebook or shorter> | <3–5> | posted by the `due` job after the slot |
| TikTok | <≤ 150 characters> | <3–5> | AI-generated label if `ai_disclosure` is true |

## 6. Compliance
- **`ai_disclosure`:** <true/false> because <one reason>
  - true: a real person appears to say or do something, real footage is altered, a realistic scene that never happened, a cloned voice of someone else, realistic gameplay or footage
  - false: animation or clearly unrealistic diagrams with a generic TTS voice
  - unsure → true
- **`made_for_kids`:** <true/false>; answer honestly for the target audience (legal obligation)
- **`originality_checklist`** (each one really done, not just ticked):
  - [ ] `original_script`: written for this video
  - [ ] `custom_voice_direction`: pauses, emphasis and emotion tags directed
  - [ ] `manual_edit`: scenes built for this episode, render approved by the user
  - [ ] `added_value`: a point of view or insight beyond reading facts
- **`policy_check`:** fill `items` only with ids that are really true (see `references/youtube-policy.md`); `checked_on`: <YYYY-MM-DD>

## 7. Schedule
- Taken slots of this channel (`scheduled_at` of all episodes): <…>
- **Earliest empty slot ≥ 2 hours from now:** <YYYY-MM-DDTHH:MM:SS+zone> (`posting_slots` in `timezone`)

## 8. Validate and upload
```bash
python3 skills/akra/scripts/validate_episode.py validate channels/<id>/episodes/<ep>.json   # must print OK
.venv-youtube/bin/python skills/akra/scripts/youtube_upload.py upload channels/<id>/episodes/<ep>.json --schedule --dry-run
```
- [ ] Validator `OK` and `Monetization: OK` (tell the user that line)
- [ ] **The user said yes to uploading this episode** at this slot (ask every time)
- [ ] YouTube upload without `--dry-run` → `youtube_url`: <…>
- [ ] Facebook / Instagram (if used): `meta_upload.py upload <ep.json> --schedule` → `facebook_url`: <…> · Instagram: queued
- [ ] The user sees the schedule in YouTube Studio → `status: "published"`; idea ticked in `ideas.md`
