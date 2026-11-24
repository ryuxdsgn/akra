# Mode `clipper`: vertical clips of a streamer's moments

Cut a short vertical clip from a streamer's or creator's VOD **with their permission**: a clipping campaign that invites clippers (Content Rewards, Clip, Motion Klip and similar) or written permission saved in `channels/<id>/licenses/`. One clip at a time, from the source to cleanup.

This mode does not make a faceless explainer. The streamer's face, voice and reactions are the content, and your edit (moment choice, hook, captions, layout) is what you add.

## Gate before starting (every item must pass)
- **CLIP-PERM-1** Permission exists for this creator: campaign rules pasted into `channels/<id>/campaigns.md`, or a written license in `licenses/`. A credit alone is not permission. Without permission, stop.
- **CLIP-PERM-2** The campaign rules are read: platforms, minimum length, required credit, tags or hashtags, watermark allowed or not, banned content, how views are counted, which countries pay. Rules that sit behind a login: the user pastes them. Do not sign in, join or accept terms for the user.
- **CLIP-MON-1** Do not count on YouTube ad revenue from clips. Permission from the owner is not enough for monetization ("reused content", YT-REUSE-1 in references/youtube-policy.md), so clip pay comes from the campaign. Post clips on a **separate clip channel or account**, never on a channel that is in or working toward the YouTube Partner Program with original content.
- **CLIP-SAFE-1** Skip campaigns or moments with gambling or betting brands, drugs or vapes, leaks, "play early", piracy, game money glitches or bots, nudity, slurs, or story spoilers in launch week. Say why in one line.
- **CLIP-CRED-1** Credit the creator on screen (`credit` in clip.json) and in the caption, with the format the campaign asks for.

## Steps
Work in `render/<channel-id>/clip-<nnn>/` (ignored by git). Scripts are in `scripts/` of this skill. They need `yt-dlp` and `ffmpeg`; `faster-whisper` (small model only) is optional.

1. **Source.** `python3 scripts/clip_fetch.py info <url>`: title, creator, duration and the "most replayed" heatmap peaks when YouTube has them. Prefer VODs that have a heatmap: it shows where viewers rewatch.
2. **Audio first.** `clip_fetch.py audio <url> <clip-dir>` downloads only the audio (about 1 MB per minute). Tell the user the file and size before any download.
3. **Moments.** `clip_fetch.py moments <clip-dir> --lang <channel language>` scores loudness spikes, heatmap peaks and hype words (English and Indonesian lists; extend `HYPE` for other languages) and writes `moments.md`. Read the transcript lines and pick with the viral checklist below. Recommend the best 3 to the user.
4. **Video sections only.** `clip_fetch.py section <url> <clip-dir> START END --height 1080` downloads just that range (give it about 5 s margin on each side) and joins it with the VOD audio into `source/`. 1080p keeps the facecam sharp after the zoom; 720p is fine for an internal draft. Look at a contact sheet (`ffmpeg -vf fps=1/3,scale=320:-1,tile=5x4`) to find the action, the payoff and the facecam box.
5. **clip.json.** Fields are documented at the top of `scripts/clip_split.py`: `face` box (the streamer's camera in source pixels), `game` (`"center"` auto crop, or a box that leaves out the facecam and HUD), `shots` (source key, start, duration, seam label), `words` (captions in output time, only words you checked against the audio; drop misheard words instead of guessing), `hook`, `credit`, `watermark`, `accent`.
6. **Preview.** `clip_split.py build <clip-dir> --preview 0.5 5 10 ...` writes frames to `renders/`. Look at every shot: face framed, game action visible, text readable.
7. **Gameplay clear.** `clip_split.py cover <clip-dir>` must report at most 8% of the gameplay panel covered at the worst moment (only the title edge and the progress bar should touch it).
8. **Render.** `clip_split.py build <clip-dir>` writes `renders/<dir>.mp4` (1080x1920, 30 fps, streamer audio normalized to -14 LUFS).
9. **Check.** Duration inside the campaign's limits (default 15-60 s, best 15-30 s), loudness -15.5..-12.5 LUFS, no silent gap over 1.2 s, hook visible in the first second, last frame delivers what the hook promised. Loop SSIM and flicker checks of `qa_render.py` do not apply to cut gameplay.
10. **Approval.** Show the user the MP4 path, the caption text (credit + required tags) and the campaign it is for. The user says "yes" before anything is posted or submitted. Upload through the platform's API script if the channel has one (`youtube_upload.py`, with the user's approval for that clip) or the user posts it and submits the link to the campaign.
11. **Cleanup after upload.** Raw downloads are only needed until the clip is live. After the user confirms the clip is uploaded, show what will be deleted: `clip_split.py clean <clip-dir>` (dry run: lists `raw/`, `source/`, `jobs/` and their size). Then, with the user's yes, run it with `--yes`. It keeps `clip.json`, `moments.md` and the final MP4 in `renders/`, so the clip can be reposted but not re-cut.

## Layout (clip_split.py)
```
+--------------------------+  0
| logo            credit   |
|    streamer facecam      |  face panel, 700 px
|  CAPTIONS ON THE CHEST   |  (dark fade under the captions)
|====[  TITLE / LABEL  ]===|  accent seam at 700, title box centered on it
|                          |
|        gameplay          |  gameplay panel, 1220 px, nothing on top of it
|      (center crop)       |
|                          |
|▬▬▬▬▬ progress ▬▬▬▬       |  8 px progress bar
+--------------------------+  1920
```
Captions sit on the streamer's chest instead of over the game, so the action stays visible. If the streamer has no facecam, put `face` on a calm part of the game frame (sky, HUD-free corner) or use a full-frame edit outside this script.

## Viral checklist (per clip)
1. **The reaction is the content.** Pick the moment where the streamer reacts hardest (screams, laughs, panics), not just the biggest game event. Gameplay alone is on thousands of channels.
2. **One complete mini story:** intent, chaos, result. Example: wants to steal a jet, fights the guards, takes off.
3. **Cold open:** the first shot (0-2.5 s) is the peak moment, then the story from the start. The hook names the streamer and the situation ("<Name> tries to steal a military jet"). No "wait for it".
4. **Pay off the hook inside the clip.** A hook question with no answer in the clip is clickbait and loses rewatches.
5. **Loop:** end on a frame that leads back into the first shot.
6. **Tight:** 15-30 s, cut dead air and driving without reactions.
7. **Captions** only where the speech is clear and correct; a wrong caption is worse than none.
8. **Test:** 2-3 hooks for the same moment on different posts, then keep what the numbers say (stayed-to-watch, average % watched).

## Done
The clip is posted with the user's approval, its link is added to the campaign, and the raw files are deleted. Record the clip in `channels/<id>/campaigns.md` (date, campaign, link, views later) so `review` can compare hooks.
