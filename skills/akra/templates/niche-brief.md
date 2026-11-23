# Niche brief: <channel working name> · <YYYY-MM-DD>

A fill-in sheet for the `niche` mode (`references/niche-scout.md`). Part A asks for candidates with evidence, part B checks each one, part C scores them and part D records the decision. The result goes into the Channel Profile (`niche`, `language`, `sensitive_topic`, `research.queries`) and the first lines of `style-bible.md`.

## Inputs
- Channel language and audience country: <e.g. en, worldwide · id, Indonesia>
- Who you want to watch (age, situation while watching): <…>
- Time per video you can spend: <minutes> · videos per day: <n>
- Production you can do cheaply: <code-drawn diagrams and characters (default in akra) · screen recordings of your own screen · licensed or public-domain archive clips · licensed gameplay with credit>
- Voice: <local TTS with a commercial license · paid TTS · your own voice>
- Niches already used by your other channels (excluded): <…>

## A. Candidate request (paste to the agent, or let the agent run it)
Fill the brackets, then send:

> You are my faceless YouTube Shorts strategist. I am launching a brand-new channel in **[language]** for **[audience]**. Suggest **7 faceless niche ideas** that already have proven search demand and suggested-video demand, and that are cheap to produce with **[production I can do cheaply]** and **[voice]**. For each niche, explain:
> 1. the curiosity it satisfies (the question a viewer brings),
> 2. why viewers keep clicking after the first few videos (the binge loop),
> 3. how many topics it can realistically support (a number, with 3 example topics),
> 4. the evidence of demand: search suggestions, outlier videos from small channels, a trend, each with a link or "guess" when there is none,
> 5. the cheapest way to make it look good, and what would make it original rather than recycled,
> 6. policy and monetization risks (health, finance, kids, real people, news, reused footage).
>
> Exclude: **[niches already used]**. Do not invent view counts; mark anything unverified as "guess".

Agent notes:
- **Evidence before claims.** "Proven demand" means something you can show: YouTube search autocomplete, `scripts/youtube_research.py outliers` (videos far above their channel's median), Google Trends, TikTok Creative Center for TikTok. Without any, write `guess`.
- **Cheap is not the same as copied.** Stock or archive clips with only a voiceover over them risk YouTube's reused or repetitive content rule. Every niche needs its own visual layer (diagram, overlay, character, own commentary) and its own angle.
- **Akra draws visuals as code**, so niches that explain mechanisms, steps, comparisons, timelines or places fit best. Niches that live on real faces, real news footage or celebrity clips fit worst.

## B. Candidate cards (one per niche, 7 in total)

### 1. <niche name>
- **Curiosity it satisfies:** <the question a viewer brings, e.g. "how does this everyday thing actually work?">
- **Binge loop:** <why the next video gets clicked: a series format, a collection to complete, a "part 2", one rule per video, ranking or comparison>
- **Topic capacity:** <realistic number> topics · examples: <topic 1> · <topic 2> · <topic 3>
- **Demand evidence:**
  | Signal | What you found | Link | Checked on |
  |---|---|---|---|
  | Search suggestions | <phrases that autocomplete> | <…> | <date> |
  | Outliers (small channels, ≥ 3× median) | <n videos, typical views> | <…> | <date> |
  | Trend | <rising / steady / falling> | <…> | <date> |
- **Cheapest good-looking production:** <e.g. code-drawn object cutaways + TTS> · minutes per video: <estimate>
- **Originality angle:** <what this channel adds that others do not>
- **Risks:** <⚠️ flag + one-line reason, or "none found">

### 2. <niche name>
- **Curiosity it satisfies:** <…>
- **Binge loop:** <…>
- **Topic capacity:** <…>
- **Demand evidence:** <table as above>
- **Cheapest good-looking production:** <…>
- **Originality angle:** <…>
- **Risks:** <…>

<!-- Repeat the card for niches 3 to 7. -->

## C. Score table (weights from `references/niche-scout.md`)
Score 1–5; policy risk counts negative (5 = very risky). RPM is an estimate.

| Niche | RPM ×2 | Competition ×1 | Evergreen ×2 | Visual feasibility ×2 | Originality ×2 | Policy risk ×−2 | Topics | Total |
|---|---|---|---|---|---|---|---|---|
| <1> | | | | | | | | |
| <2> | | | | | | | | |
| <3> | | | | | | | | |
| <4> | | | | | | | | |
| <5> | | | | | | | | |
| <6> | | | | | | | | |
| <7> | | | | | | | | |

A niche with fewer than **100 realistic topics** is a series, not a channel; note it and score evergreen lower.

## D. Decision
- **Chosen niche:** <name>
- **Why (3 sentences):** <…>
- **3 example titles (channel language):** <…> · <…> · <…>
- **Channel promise (one sentence):** <what each video gives the viewer>
- **First series format:** <e.g. "one object, one hidden mechanism", "one condition, one safe move">
- **`research.queries` for outlier research:** <3–5 search phrases>
- **Sensitive topic?** <yes/no; if yes: the required disclaimer wording and limits>

## E. 30-day test
- Start date: <YYYY-MM-DD> · posting slots: <times + time zone> · videos per day: <n>
- Continue when at least one is met: median views rise from week 1 to week 4 · ≥ 3 videos at ≥ 3× the median · "stayed to watch" ≥ 60%
- First change if it stalls: <the hook style>; changing the niche is the last option
- Weekly review dates: <…>
