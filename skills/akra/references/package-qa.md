# Mode `package`: upload package + QA

## Metadata
- **Title:** in the channel language, **≤ 60 characters** (`en`) or **≤ 70 characters** (`id`), containing the main keyword. Do not lie about or exaggerate the video's content.
- **Description:** 1–3 sentences that add context, one source line ("Source: ..."), the credit line (`Music: ...` / `Musik: ...`, voice, footage), the disclaimer on a `sensitive_topic` channel, and hashtags at the end.
- **Hashtags:** 3–5, each `#word` without spaces. Always include `#shorts`, plus 2–4 niche hashtags.

## Audio
- **Voiceover:** already made in the `build` mode (Kokoro or another commercially licensed TTS). Make sure the description carries the voice credit if the license asks for or recommends it (e.g. `Voice: Kokoro-82M (hexgrad, Apache-2.0)`).
- **Music** (`music_source`):
  - `youtube_audio_library`: from the YouTube Audio Library (safe for monetization)
  - `licensed`: commercially licensed and the proof is kept
  - `none`: no music
  - Do not use popular or trending music without a license, because it triggers Content ID claims.

## Captions, voiceover and music
Already burned into the video in the `build` mode (word-by-word captions from the voiceover timing, music under the voice). Here just double-check that `music_source` matches the music actually used, and the license proof is kept if `licensed`.

## Before continuing
- The episode status must be `edited`: the 1080×1920 MP4 is rendered and **the user has watched and approved it**.
- If there are revisions, go back to the `build` mode.

## Compliance
- **`ai_disclosure`** (YouTube's rule "Disclosing use of GenAI content", support.google.com/youtube/answer/14328491, checked 2026-11-21): must be `true` if the video makes a real person appear to say or do something, alters footage of a real event/place, creates a realistic scene that never happened, or features AI music as a focus. Animation and clearly unrealistic diagrams with a generic TTS voice (not an imitation of a specific person, e.g. Kokoro) → `false`. A voice cloned from another person (e.g. the ElevenLabs Voice Library) or realistic-looking footage/gameplay → `true` (YouTube's exception is only for cloning your own voice). The label does not reduce reach or monetization; if unsure → `true`. In YouTube Studio answer **"Yes"** to **"Altered or synthetic content"** if `true`.
- **`originality_checklist`:** all four items must really be done, not just ticked:
  - `original_script`: the script was written for this video, not copied
  - `custom_voice_direction`: pauses and emphasis are directed
  - `manual_edit`: scenes, diagrams and rhythm are built specifically for this episode (not a template with only the text swapped), and the user has watched and approved the render
  - `added_value`: there is a point of view, context or insight that is not just reading out facts

## Upload time
Schedule publishing in the channel's `posting_slots`, which are local times in the channel's `timezone` (an IANA name such as `America/New_York` or `UTC`). Pick slots from your audience's local habits: a common starting point is early morning and early evening (17:00–19:00) in the audience's own time zone. If the audience lives in another zone than you, write the slots in the audience's zone and set `timezone` to it.

**Filling `scheduled_at`:** collect all `scheduled_at` of this channel's episodes, then pick the **earliest empty slot** from `posting_slots` in `timezone` (number per day = `videos_per_day`) that is still at least 2 hours from now. Do not stack two videos in the same slot, and do not skip empty slots.

The schedule is sent through the API (`--schedule`, see below); if you must do it manually, use the **Schedule** feature in YouTube Studio. Adjust the slots after looking at "When your viewers are on YouTube" in Analytics.

## Other platforms (if `platforms` in the Channel Profile contains `facebook` / `tiktok`)
The same MP4 (1080×1920, 30–60 s) is used on all platforms. Because TikTok and Facebook buttons are bigger than YouTube's, important text stays in the combined safe area: **x 90–900, y 160–1330** (the caption at y 1185 is already safe).
Make a per-platform package in the Episode Package (`platform_copy`), from the same content:
- **Facebook Reels:** caption of 1–2 sentences + 3–5 hashtags; for older audiences a direct call to action ("Try it with me!"). No `#shorts`.
- **TikTok:** caption ≤ 150 characters, 3–5 hashtags (e.g. `#homeworkout #seniorhealth #fyp`), no `#shorts`. Turn on the **AI-generated** label if `ai_disclosure` is true.
- **Upload:** manual first (Meta Business Suite / Creator Studio for Facebook, the TikTok app or web), at the same slot times. Always ask the user first, same as YouTube. The APIs (Meta Graph `video_reels`, TikTok Content Posting API) are only used once the channel is running, because they need app review.
- Note the link per platform in the Episode Package (`facebook_url`, `tiktok_url`) so the `review` mode can compare.

## Validation and upload
**Policy gate:** YT-META-1, YT-AD-1, YT-TAG-1, YT-KIDS-1, YT-SYN-2, YT-CRED-1, then YT-UP-1 (pre-upload) in youtube-policy.md. Fill `policy_check` {checked_on, items: {id: "pass"}} only for items that are really true. The validator ends with `Monetization: OK` or `Monetization: at risk: <ids>`; tell the user that line.

1. Complete the Episode Package, then run the validator (see SKILL.md) or the checklist in rules.md until it passes.
2. **The "made for kids" question:** answer **honestly** according to who the video's target audience is. This is a legal obligation (COPPA), not a style choice. Set `made_for_kids` in the Episode Package; the upload script sends it as `selfDeclaredMadeForKids` (made for kids turns comments and personalized ads off). If unsure, read YouTube's guide on "made for kids".
3. **Upload through the YouTube Data API (default).** Always ask the user first ("May I upload ep-NNN now, scheduled <date time> <timezone>?") and wait for a yes for that episode.
   - One-time setup (done by the user, guided): Google Cloud project → enable **YouTube Data API v3** → OAuth consent screen (External, add yourself as a test user, scope `youtube.upload`) → OAuth client ID of type **Desktop app** → save the JSON as `client_secret.json` at the project root. Then `uv venv --python 3.12 .venv-youtube` and `uv pip install --python .venv-youtube/bin/python google-api-python-client google-auth-oauthlib`.
   - Login: the user runs `! .venv-youtube/bin/python skills/akra/scripts/youtube_upload.py auth` (a browser opens). The token is saved in `.youtube-token.json`. For a channel on another Brand Account: fill `youtube_account` in the Channel Profile and log in with `auth --channel channels/<id>` (token `.youtube-<account>-token.json`, so another channel's login is not overwritten). App in Testing mode: the token expires after about **7 days**, then log in again.
   - Check first: `.venv-youtube/bin/python skills/akra/scripts/youtube_upload.py upload channels/<id>/episodes/<ep>.json --schedule --dry-run` (shows title, description, tags, category, schedule, file size). The script runs the validator first and refuses while it fails, listing the policy items that are not `"pass"`.
   - Upload: the same command without `--dry-run`. The video goes in as private with `publishAt` = `scheduled_at`; the script writes `youtube_url` and `youtube_video_id` to the Episode Package.
   - **Replacing an already uploaded video** (revision after upload): YouTube cannot replace the file. Ask the user's approval to delete the old one. Then the order is:
     1. Render and QA again.
     2. Update `render` in the Episode Package, then validate.
     3. Upload the new one with `--schedule --force` (same slot). Note the old id in `replaced_video_id`.
     4. Check the new video exists in Studio, only then delete the old one (Studio → Video details → ⋮ → Delete, tick the confirmation). The script token only has the `youtube.upload` scope, so it cannot delete.
     5. Make sure the Shorts list only contains the new version.
   - An API project that has not passed YouTube's audit can lock videos as private. If the script warns, or Studio shows the video as "Private" without a schedule, ask the user to click **Schedule** in YouTube Studio at the same slot.
   - `client_secret*.json` and `.youtube-token.json` are in `.gitignore`: never commit, print, or ask for them to be pasted in chat.
   - **Do not** upload through browser automation (expensive and there is a file size limit).
4. **Facebook Page + Instagram Reels through the Meta Graph API (optional, per channel).** The user's approval per episode is still required; one "yes upload" applies to the platforms the user names.
   - One-time setup per channel: the user creates a Facebook Page (+ a professional Instagram account linked to the Page, if posting to IG) and an app at developers.facebook.com (the steps are printed by `setup`; permissions `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `business_management`, `instagram_basic`, `instagram_content_publish` via **Customize → Add**, without this login fails with "Invalid Scopes"). Then the user runs in their own Terminal: `.venv-youtube/bin/python skills/akra/scripts/meta_upload.py setup --channel channels/<id>`. The script asks for `META_APP_ID` and `META_APP_SECRET` (the secret is hidden, saved to `.env`), opens the login in the browser, asks you to pick a Page, asks for the platforms (Facebook, Instagram, or both), writes `facebook_page.id`, `instagram.handle` and `meta.platforms` to `channel.json`, and if Instagram is chosen installs the launchd `due` job. Do not ask for keys in chat. If the keys are already in `.env`, the agent may run `setup --channel channels/<id> --platforms fb|ig|fb,ig [--page <id>]` itself.
   - Re-login (token only): `meta_upload.py auth --channel channels/<id>` → a non-expiring Page token in `.meta-<id>-token.json` (gitignored). The script refuses if the linked IG is not `instagram.handle`.
   - Upload: `meta_upload.py upload <episode.json> --schedule [--only fb|ig] [--dry-run]` posts to the channel's `meta.platforms` (without that field: both); `--only` for a one-episode exception. A Facebook Reel is scheduled by Facebook at `scheduled_at`. The Instagram API cannot schedule: the episode is marked `instagram_pending`, then `meta_upload.py due` (launchd `~/Library/LaunchAgents/com.akra.meta-due.plist`, every 10 minutes, log `~/Library/Logs/akra-meta-due.log`) posts after the publishing time. The Mac must be on; if it sleeps, posting is delayed until the Mac wakes. Caption = description + hashtags, no `#shorts`. Links are written to `facebook_url` / `instagram_url`.
5. **Manual fallback in YouTube Studio:** Create → Upload, pick the MP4, paste the title and description, fill the AI disclosure and "made for kids", then Schedule.
6. Ask the user to confirm the schedule shows in YouTube Studio, then change the status to `published` and mark the idea as used in `ideas.md`.
