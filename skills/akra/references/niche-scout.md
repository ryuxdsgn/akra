# Mode `niche`: Niche Scout

Goal: pick **one** niche per channel based on a clear score, then test it for 30 days.

## Starting candidates
Ready-made starting points for 7 niches (example Channel Profile, filled style bible, starter ideas): `templates/niches/README.md`. Fill-in sheet: `templates/niche-brief.md` (candidate request with demand evidence, binge loop and topic capacity per niche, score table, decision, 30-day test).

Evaluate these candidates, then add 1–2 suggestions from the user. Exclude niches already used by another channel.
1. Science & space facts
2. History mysteries
3. Psychology facts
4. Animal facts
5. "How things work"
6. AI tools tips

## Scoring criteria (1–5)
| Criterion | Weight | Question |
|---|---|---|
| RPM potential | ×2 | Will advertisers pay a lot for this niche's viewers? |
| Competition | ×1 | How crowded is it? 5 = there is still a gap |
| Evergreen | ×2 | Will the video still be relevant in 1–2 years? |
| Visual feasibility in HyperFrames | ×2 | Can it be drawn as code (diagrams, real objects, rig characters) without real people or brands? |
| Originality room | ×2 | Can we have a distinct point of view, not just a recycle? |
| Policy risk | ×−2 | 5 = very risky (see flags) |

Total score = sum of (score × weight). Show the full table, not only the winner. Say that RPM values are estimates.

## Risk flags (mark with ⚠️ and explain)
Policy gate: YT-CH-1, YT-CH-2 and YT-CH-3 in youtube-policy.md.
- **Medical/health:** health claims can violate the medical misinformation policy.
- **Financial/investment advice:** needs a disclaimer and risks demonetization.
- **Children:** "made for kids" content turns comments off and lowers revenue.
- **Real people/celebrities:** AI visuals of real people risk policy and copyright violations.
- **News/current events:** not evergreen and prone to factual errors.

## 30-day test plan
- 1 video/day for 30 days, with the same style and voice.
- Review every week (mode `review`).
- **Continue** (change the channel status to `active`) if at least one is met:
  - median views per video rise from week 1 to week 4
  - there are ≥ 3 videos whose views are ≥ 3× the median
  - "stayed to watch" (the opposite of swipe-away) averages ≥ 60%
- **Change the angle or niche** if after 30 days median views are flat and retention is low. Try changing the hook style first; changing the niche is the last option.

These thresholds are a starting point, not a YouTube rule. Adjust once there is real data.

## Output
1. Score table for all candidates.
2. Recommendation of 1 niche + a 3-sentence reason.
3. 3 example video titles for that niche.
4. 30-day test plan with a start date, matching the channel's posting slots and the user's time/token budget (see Capacity in channel-setup.md).
