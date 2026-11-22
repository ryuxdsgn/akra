# Validation checklist (manual version)

Use this checklist if the `validate_episode.py` script cannot be run. Check every item and write ✅ or ❌ with the reason. The rules are exactly the same as the script.

## Episode Package
**Required fields:** `id`, `channel`, `niche`, `topic`, `status`, `hook`, `script`, `shots`, `title`, `description`, `hashtags`, `ai_disclosure`, `music_source`, `originality_checklist`. Optional field: `vo_duration` (real voiceover duration in seconds; if present, it is used instead of the 150 words/minute estimate for the shot coverage check). The legacy field `credit_estimate` (Flow era) is ignored.

1. **`status`** is one of: `idea`, `scripted`, `visuals`, `edited`, `published`.
2. **`script`** has **75–150 words** (≈ 30–60 seconds at 150 words/minute). Words like `don't`, `3D`, `well-known` each count as 1 word.
3. **`hook`** has 1–**10** words, and the script starts with that hook word for word (case and punctuation are ignored).
4. **`shots`:**
   - at least 1 shot; every shot has numeric `t_start` and `t_end`, with `t_end` > `t_start`
   - each shot lasts **2–8 seconds** (0.1 second tolerance)
   - `type` is one of `diagram` (HyperFrames scene, default) or `stock` (licensed, credited footage); `prompt` is not empty
   - after sorting: the first shot starts at 0, each shot connects with no gap or overlap (0.1 second tolerance), and the last shot ends at least 1 second before the end of the narration (`vo_duration` if present, otherwise word count ÷ 150 × 60)
   - legacy types `veo` / `flow_image` (Google Flow, no longer used): ❌ for packages not yet `published`; only a warning for `published` packages
5. **`title`** is not empty and ≤ **60** characters.
6. **`description`** is not empty.
7. **`hashtags`** number **3–5**, each in the form `#word`: after `#` only letters, digits or `_` (no spaces or punctuation).
8. **`ai_disclosure`** is `true` or `false` (not text).
9. **`music_source`** is one of `youtube_audio_library`, `licensed`, `none`.
10. **`originality_checklist`** contains `original_script`, `custom_voice_direction`, `manual_edit`, `added_value`, and all four are `true`.
11. **`channel`** equals the `id` in the Channel Profile of this episode's folder, and that profile is valid.

**Policy gate** (ids from youtube-policy.md):
12. **`made_for_kids`** and **`synthetic_content`** are `true` or `false`; if `synthetic_content` is `true`, `ai_disclosure` is `true`.
13. **`variation`** has non-empty `story`, `setting`, `props`. Compare with the channel's last 3 episodes by id: the same `story`, or the same `setting` and `props` together, fails.
14. **`sources`** is a list of {`claim`, `url` (http/https)}, at least 1. An empty list only with `"no_factual_claims": true`.
15. If `music_source` is not `none`: the description has a `Music:` line (`Musik:` for `id`), or the exact `music_credit` text.
16. **`policy_check`** {`checked_on`: YYYY-MM-DD, `items`}: required from status `edited` and for every upload. Every "Pre-upload ids" item in youtube-policy.md is `"pass"`; unknown ids fail. End the report with the validator's `Monetization:` line (`OK`, `OK so far (pending: ...)` or `at risk: <ids>`).
17. **Style gate:** from status `visuals` on, the Channel Profile has `style_approved_on` (YYYY-MM-DD).
18. **`sensitive_topic` channel** (`health` / `finance`): the description carries the disclaimer (the profile's `disclaimer`, else e.g. "not medical advice", "bukan nasihat medis", "not financial advice"); title, description and script have no forbidden word (health: cure, cures, cured, curing, menyembuhkan, disembuhkan; finance: guaranteed profit, guaranteed returns, risk-free, pasti untung, dijamin untung, tanpa risiko; plus the profile's `forbidden_words`).
19. **Legacy:** a `published` package, or one with no `policy_check` dated (`created_on` or `scheduled_at`) before 2026-11-22, gets items 12–18 as warnings, not failures. An upload always needs them.

## Channel Profile
1. Required fields: `id`, `name`, `niche`, `status`, `voice`, `style_bible`, `posting_slots`, `timezone`, `videos_per_day`, `started_on`.
2. `id` only contains lowercase letters, digits and `-` (e.g. `deep-earth`).
3. `name`, `niche` and `style_bible` are not empty.
4. `status` is one of `testing`, `active`, `paused`.
5. `voice` contains `provider` and `voice_name`.
6. `posting_slots` contains at least 1 time in `HH:MM` format (00:00–23:59), local to `timezone` (an IANA name, e.g. `UTC`, `America/New_York`).
7. `videos_per_day` is an integer ≥ 1.
8. `started_on` is in `YYYY-MM-DD` format (with `-`).
9. The legacy field `credits_per_video` (Flow era) is ignored, only a warning is given.
10. Optional: `style_approved_on` is YYYY-MM-DD; `made_for_kids` is `true`/`false`; `sensitive_topic` is `health`, `finance` or `null`; with a `sensitive_topic`, `persona` claims no credential (doctor, dokter, nurse, financial advisor, and so on: YT-CH-2).

## Capacity
Count from channels with status `testing` and `active` (`paused` channels are not counted):
- **Posting slots:** for each channel, `videos_per_day` must not exceed the number of `posting_slots`. If more, mark `OVER`.
- **Working time:** total `videos_per_day` × 75 minutes = estimated daily working time (done serially). Compare with the user's time and token budget.

Also mention invalid profiles (they are not counted).
