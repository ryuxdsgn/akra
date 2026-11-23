# Mode `channel`: create or add a channel

**Policy gate:** YT-CH-1..4 in youtube-policy.md (channel step).

## 1. Readiness gate (2nd channel onward only)
Before opening a new channel, check and show the user:
- **The previous channel has passed the 30-day test** (see the criteria in niche-scout.md). If not, suggest waiting.
- **Capacity:** run `capacity channels/` (or count manually). Check two things:
  - **Posting slots:** each channel's `videos_per_day` is not more than the number of its `posting_slots` (the validator flags `OVER`).
  - **Time and tokens:** total `videos_per_day` of `testing` + `active` channels × 75 agent working minutes, done serially (one episode to the end). Compare with the user's daily time and session token/cost budget. If it is not enough, reduce `videos_per_day` or postpone the new channel.

If something fails, say so plainly. The final decision stays with the user.

## 2. Pick a niche
Run the Niche Scout (niche-scout.md). **Exclude niches already used by the user's other channels**, including ones that are too similar (e.g. "space facts" and "astronomy facts").

## 3. Channel identity
Write a short brief:
- channel language (`language`: `en` or `id`) and platforms (`platforms`: `youtube`, plus `facebook` / `tiktok` if the target audience is there)
- 5 channel name ideas (in the channel language, easy to spell, not too generic; ask the user to check availability on YouTube, Facebook and TikTok)
- tone (e.g. "calm, curious narrator")
- visual style, cast, expressions, poses, settings, audio and composition → fill every section of `style-bible.md` from templates/style-bible.md (sections that do not apply are written `not used`); then pass the style gate below before the first episode
- audience and policy: `made_for_kids` (YT-CH-3), `sensitive_topic` (`health`, `finance` or `null`) and an honest `persona` that claims no doctor or financial-adviser credentials (YT-CH-2), and the disclosure plan (YT-CH-4). Write them into the style bible's "Sensitive topic" section.
- one fixed TTS voice (provider, voice name, settings). One channel = one voice, do not keep swapping. `en`: Kokoro (default). `id`: local dots.tts (`scripts/dots_tts.py`, Apache-2.0) with your own voice reference clip, or paid ElevenLabs. **Do not** use OmniVoice (VoiceStudio's default engine): its weights are CC-BY-NC, not allowed for monetized channels. VoiceStudio with another engine is fine if the model's license allows commercial use (check in Model Manager and the model card); fill `voice.license`, `license_url` and `license_checked`.
- brand for the render template (`brand`: `text`, `font`, `colors` {bg, ink, muted, dim, primary, primary_light, accent, highlight}); without `brand` the template uses a neutral dark look
- 1–2 posting times (`posting_slots`, `HH:MM`) in the audience's time zone (`timezone`, an IANA name; see package-qa.md)

## 4. Create the Channel Profile
Fill `channels/<channel-id>/channel.json` following templates/channel.example.json (or start from a niche kit in templates/niches/, which also brings a filled style bible and starter ideas):
- `id`: lowercase letters, digits and `-` (e.g. `deep-earth`)
- `status`: start with `testing`; change to `active` after it passes the 30-day test; `paused` if stopped for a while
- `videos_per_day`: start with 1
- `started_on`: today's date, format YYYY-MM-DD

- optional: `language`, `platforms`, `youtube_category_id` (e.g. `"17"` Sports, `"26"` Howto & Style; default `"28"`), `youtube_account` (separate login token for this Brand Account), `brand`, `persona`, `sensitive_topic`, `made_for_kids`, `disclaimer` (exact disclaimer text the description must carry), `forbidden_words` (extra claim words to reject)

Validate with `validate-channel`.

### Style-bible gate (before the first episode)
1. Render **2–3 sample style frames** from the style bible: snapshots of a template scene with the brand colors, the font, the caption band and one sample object or background (`cp -r render/_template render/<channel-id>/style-check`, set the sample, `npx hyperframes snapshot --at ...`).
2. Show the frames to the user and ask for approval. Revise the style bible and render again until they approve.
3. Write the approval date as `style_approved_on` (YYYY-MM-DD) in `channel.json`, and note it in the style bible's "Approval" section.

Without `style_approved_on`, the validator rejects every episode beyond `scripted` and `qa_render.py` fails with `style gate`. If the style changes a lot later, repeat the gate and update the date.

If the channel will reuse library items, also write `channels/<channel-id>/library.json`: `style` (`hw` or `toon`), `visual_mode`, and `items` (ids from `library/catalog.json` or `channels/_library/`). Show the choices to the user and ask for approval before saving (see references/library.md; items that do not exist yet go through the "create new" path).

Each channel's render projects live in `render/<channel-id>/<ep-id>/` (`cp -r render/_template render/<channel-id>/ep-001`); the channel and its brand are read automatically from that path. There is no built-in channel. The legacy layout `render/<ep-id>/` (without a channel folder) may only be used by one channel, which writes `"render_layout": "flat"` in `channel.json`; build and `qa_render.py` then map `render/ep-*` to that channel. New channels always use a channel folder.

## 5. Steps on YouTube (done by the user)
1. **YouTube Studio:** create the channel. For the second channel onward use a **Brand Account** (can sit under the same Google account).
2. **Logo:** make it as a vector from the brand assets (see the Brand assets appendix; 1:1, simple icon). **Banner:** 2560×1440, safe area in the center.
3. **Channel description:** 2–3 sentences in the channel language about what viewers get and how often you upload.
4. **Settings:** country, channel keywords, default language = the channel language.
5. **Other platforms** (if in `platforms`): a Facebook Page (enable Reels / professional mode) and a TikTok account with the same name and logo. For automatic Facebook/Instagram scheduling, offer `meta_upload.py setup --channel channels/<id>` (see package-qa.md, Meta Graph API).
6. Pick the channel voice (see step 3), check that its license allows commercial use, keep the proof in `channels/<id>/licenses/`, and record it in `voice` of the Channel Profile.

## 6. Fill the idea bank
Continue to the `ideas` mode for this new channel (at least 30 ideas).

## Appendix: channel brand assets: avatar, banner, cover, watermark

Made in FigCraft ("vectorcraft"); the source is kept in `channels/<id>/brand/` (e.g. `<channel>-brand.figcraft`, exports in `brand/v2/`). If the channel has characters, draw them from the same source as the videos, so proportions match.

### Sizes
| Asset | Size | Notes |
|---|---|---|
| YouTube avatar | 800×800 | shown round; keep important content inside the circle |
| YouTube banner | 2560×1440 | safe area on all devices **1546×423 in the center**; the title must be inside it, characters left/right are only fully visible on TV/desktop |
| Facebook Page cover | 1640×624 | title in the center |
| Video watermark | round sticker top left (x 80–460, y 170–350) | same as the avatar, small version |

### Technical pitfalls
- **Hair outside the circle:** clip with two nested clipPaths, i.e. (top/left area) ∩ (outside the circle). Do not merge into one evenodd path: the face is drawn twice and a thin line appears across it.
- **FigCraft:**
  - Only keeps one shape per clipPath, so merge into one path first.
  - Filters other than shadow/blur are dropped, for example the toon outline: add a plain ink stroke if needed.
  - `node.set width/height` does not scale the content; use `transform.scale`.
  - Fonts: install the TTF in `~/Library/Fonts`, then run `text.rescanFonts`.
- **Applying on YouTube Studio** (Customization → Profile):
  1. Find the hidden `file-input` with `find`, then fill it with `file_upload` (do not click the button).
  2. Click Done in the crop dialog, then Publish.
  3. Verify on the channel page in a new tab. The banner may take a few seconds to change.
  4. The Studio tab often cannot be closed automatically ("Leave site?" dialog); ask the user to close it.
- Always open the exported PNG (`open`) for the user, and keep the old version under a different name.
