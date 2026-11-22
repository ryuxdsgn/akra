# Mode `ideas`: Idea Bank

**Policy gate:** YT-AUTH-1, YT-AUTH-2, YT-FACT-1, YT-REUSE-1, YT-AD-2 in youtube-policy.md (keep every episode monetizable).

Stored in `channels/<channel-id>/ideas.md`. One bank per channel.

## Rules
- At least **30 ideas** per channel. Add more when the unused ideas drop below 10.
- Every idea contains:
  - `topic`: one sentence
  - `hook`: opening sentence ≤ 10 words, in the channel language
  - `angle`: what makes it different or surprising
  - `sources`: 1–2 trustworthy sources (journal, NASA, encyclopedia, museum, university site)
  - `visual_feasibility`: high / medium / low (can it be drawn as code in HyperFrames?)
  - `ref` (if any): the outlier in `research/` that inspired this idea, and `beda` (difference): this channel's own angle or added value
- **Check duplicates only within the same channel:** compare with `ideas.md` and `episodes/*.json` of the active channel. Similar topics may exist on another channel.
- Avoid topics that hit the risk flags in niche-scout.md.

## External reference research (before adding ideas)
Besides the channel's own data (`review-log.csv`), study other videos in the same niche that **blew up compared with their creator's channel**.
1. **YouTube outliers** (Claude Code / Codex, needs login `youtube_stats.py auth`):
   `.venv-youtube/bin/python scripts/youtube_research.py outliers channels/<id>` → `channels/<id>/research/<date>-outliers.md`. Queries come from `research.queries` in `channel.json` (without it: `niche`); add `--query "..."` for a new angle. If an outlier file less than 7 days old exists, use it, do not pull again (API quota and tokens).
2. **TikTok and Facebook** have no public search API: use web search (e.g. TikTok Creative Center for rising hashtags and songs in the channel's country) and note the results. Do not scrape.
3. **Update `channels/<id>/research/patterns.md`** (format: templates/patterns.md): rising topics, winning title/hook formulas, duration, story angles, what makes the outlier win according to evidence (not guesses). Combine with the channel's own winners from `review`. Read this file before writing ideas.
4. **Without API or web access** (plain chat): ask the user to paste 5–10 Shorts titles that are trending in their niche.

**Originality is still required:** an outlier is evidence of a pattern, not material to copy. Do not copy titles, scripts, scene order or visuals; every idea taken from an outlier must have a clear `beda` (another fact, another angle, this channel's format). YouTube rejects monetization of recycled content.

## Good idea sources
- Patterns from `research/patterns.md`: rising topics in the niche, done with this channel's angle
- "Why/how" questions people search for often
- This channel's best-performing videos (from review): make variations of their angle, do not copy them
- Facts that contradict common belief ("You've been told X, but...")
- Series: "Part 1/2/3" for topics too long for 60 seconds

## Format
```markdown
## [ ] 012 — Ringwoodite holds an ocean
- hook: This ocean hides a second ocean.
- angle: The mantle may store water on the scale of the oceans (still debated)
- sources: Pearson et al., Nature (2014); Schmandt et al., Science (2014)
- visual: high
```
Change `[ ]` to `[x]` once the idea is used, and write its episode id.
