# Weekly review: <channel> · <week, e.g. 2026-W05> · <YYYY-MM-DD>

A fill-in sheet for the `review` mode (`references/review.md`). One sheet per channel per week. Numbers come from `scripts/youtube_stats.py pull channels/<id>` (saved to `review-log.csv`); "stayed to watch" is copied by hand from YouTube Studio. Videos younger than about 3 days are "too new": list them, do not judge them.

## 0. This week in one line
<e.g. "7 videos, hooks with a number held best, the middle of the exercise videos drags">

## 1. Numbers
| Episode | Published | Hook type | Views | Stayed to watch % | hold@3s % | avg % | end % | Subs | Note |
|---|---|---|---|---|---|---|---|---|---|
| <ep-…> | <date> | <story / contradiction / number / you / question / statement> | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |

Channel medians this week: views <…> · avg % <…> · hold@3s <…> · stayed to watch <…>
Previous week's medians: views <…> · avg % <…> · hold@3s <…> · stayed to watch <…>

## 2. How to read them
| Signal | Threshold (a starting point, adjust with your data) | What it points at |
|---|---|---|
| hold@3s low | below ~70% | the hook or the first frame |
| Stayed to watch low | below ~60% | the first frame and the opening words do not match what the viewer expected |
| avg % high, end % low | end % far under avg % | the middle slows down; check the shots around the drop |
| end % above ~100% | — | viewers rewatch: the loop works, keep it |
| Views high, avg % low | — | the title or topic pulls, the video does not deliver; check the promise |
| One video ≥ 3× the median | — | a pattern to repeat: note hook, topic and opening |

Rank by **avg %**, not by views: early Shorts views are noisy. With fewer than ~5 videos in a group, call a pattern a guess.

## 3. Winners and losers
- **Top 3 by avg %:** <ep, why it worked (hook, topic, opening frame, pacing)>
- **Bottom 3 by avg %:** <ep, where it lost people (second, shot, line)>
- **Outliers (≥ 3× median views):** <ep or "none">

## 4. Patterns
| Group | Videos | Median avg % | Median hold@3s | Read |
|---|---|---|---|---|
| Hook: <type> | <n> | | | <keep / drop / guess> |
| Topic: <sub-topic> | <n> | | | |
| Format: <series> | <n> | | | |

Niche comparison (`scripts/youtube_research.py outliers channels/<id>`, then `research/patterns.md`): <patterns outliers use that this channel has not tried>

## 5. Next week's changes (exactly 3, each testable)
1. **Hook:** <one change, e.g. "open with the number on screen in the first frame">
2. **Pacing:** <one change, e.g. "cut the normal-state beat to 4 s">
3. **Topic:** <one change, e.g. "two more videos like ep-…">

Idea bank: <ideas moved up> · <new ideas added (7–10)>

## 6. Monetization progress (re-check YouTube's current requirements)
- Subscribers: <X> / 1,000
- Valid Shorts views, last 90 days: <Y> / 10,000,000 (or long-form watch hours <…> / 4,000)
- At this rate: <estimated date or "not yet predictable">

## 7. Continue, change or stop (30-day test, from week 4)
- [ ] Median views rose from week 1 to now
- [ ] ≥ 3 videos at ≥ 3× the median
- [ ] Stayed to watch averages ≥ 60%

| Result | Decision |
|---|---|
| At least one is met | **Continue**: status `active`, keep the format, apply the 3 changes |
| None is met, but hold@3s or avg % improved | **Change the angle**: new hook style or series format for 2 more weeks |
| None is met and nothing improved after changing the angle | **Change the niche** (last option): back to `templates/niche-brief.md`; status `paused` |

Decision this week: <continue / change the angle / change the niche / too early (before week 4)>

## 8. Housekeeping
- [ ] Policy refresh (YT-REV-1): source pages re-opened, changes noted
- [ ] `review-log.csv` updated; `hook_type` corrected in episode files where the guess was wrong
- [ ] Capacity still fits (videos per day vs time and budget)
