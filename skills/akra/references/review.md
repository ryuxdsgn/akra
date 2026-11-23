# Mode `review`: weekly review per channel

Always for **one channel**. If the user has several channels, review them one by one, then write a short comparison summary at the end.

Fill-in sheet for the whole review (numbers, how to read them, winners, patterns, 3 changes, monetization, continue/change/stop): `templates/weekly-review.md`.

## Input: pull automatically from the YouTube Analytics API
```
.venv-youtube/bin/python scripts/youtube_stats.py pull channels/<id>
```
- This script prints a table per video: views, **avg %** (average percent watched), **hold@3s** (percent of viewers still watching at second 3, from the retention curve), **end%** (percent who stay to the end), average watch time, likes and subs. Then a summary per **hook type** (`hook_type` in the episode JSON; if empty, guessed from the hook text: story / contradiction / number / you / question / statement) and YPP progress.
- One row per video per week is saved (upsert) to `channels/<id>/review-log.csv`. Use `--no-write` just to look, or `--json` for raw numbers.
- YouTube data lags by about 2–3 days. Newer videos are marked "too new"; do not draw conclusions from them yet.
- **One-time setup:** enable "YouTube Analytics API" in Google Cloud Console (the same project as upload), then the user runs `! .venv-youtube/bin/python skills/akra/scripts/youtube_stats.py auth` (browser login, read-only scope, separate token `.youtube-analytics-token.json`). Testing-mode tokens expire after about 7 days, so run `auth` again when asked.
- **Not available in the API:** "stayed to watch / swiped away" for Shorts exists only in YouTube Studio. Ask the user to copy it if needed, then fill the `stayed_to_watch_pct` column.
- Without API access (other chats), ask the user to copy the same numbers from Studio → Analytics → Content → Shorts.

## Analysis
1. **Winners and losers:** top 3 and bottom 3 by **avg %** (not views; early Shorts views are very random), then views.
2. **Hook:** hold@3s below ~70% means the hook or first frame is weak. Compare per `hook_type` and look for patterns in the winning hook text. Fill `hook_type` in the episode JSON if the script's guess is wrong.
3. **Middle and end:** high avg % but low end% means the middle of the video slows down. Check the shots around the drop point, because the script does not read the per-second curve. end% above ~100% means viewers rewatch, and the loop works.
4. **Topic:** which sub-topics (aviation, home, history, and so on) have a high avg %.
5. **Compare with the niche:** run `scripts/youtube_research.py outliers channels/<id>` (see idea-bank.md, External reference research), then update `research/patterns.md`: which patterns outliers use that this channel has not tried, and this channel's own proven patterns.
6. **Next week's actions:** 3 concrete changes (hook, pacing, topic), then reorder the idea bank: ideas similar to the winners move up, and add 7–10 new ideas.
7. At least ~5 videos per group before concluding a pattern; below that call it a guess.

## Monetization progress (re-check the requirements on YouTube)
The YouTube Partner Program requirements commonly used for Shorts ad revenue:
- **1,000 subscribers**, **and**
- **10 million valid Shorts views in the last 90 days** (or 4,000 long-form watch hours in 12 months)

Show progress as: subscribers X / 1,000, 90-day views Y / 10 million, and the estimated date of reaching it at the current rate. **Always remind that these requirements need to be re-checked**, because YouTube can change them.

## Beyond Shorts ads
Shorts ad revenue per 1,000 views is relatively small. Suggest, depending on the channel's stage:
- **Long-form compilations** (8–12 minutes from the best 10–15 Shorts, with connecting narration). RPM is usually much higher.
- **Affiliate:** products relevant to the niche (books, tools, courses), placed in the description or a pinned comment.
- After monetization is active: Super Thanks and memberships.

## 30-day test decision
At week 4, apply the continue/change criteria in niche-scout.md, then recommend changing the channel status (`testing` → `active` or `paused`).

## Policy refresh (weekly)
YT-REV-1 in youtube-policy.md: open every source URL, and if a page changed after its check date, update the rule and date and tell the user.

## Recommended routine
- **Daily (60–90 minutes):** one video goes through the stages script → upload. If scripts were made in a batch, 45–60 minutes is enough: voiceover, build, QA, upload.
- **Weekly (Sunday, 1–2 hours):** this review (including outlier research), then a **batch of 7 scripts and shot lists** for next week.
- **Monthly:** evaluate capacity (`capacity`: videos/day vs posting slots, working minutes, token budget) before adding videos per day or opening a new channel.
