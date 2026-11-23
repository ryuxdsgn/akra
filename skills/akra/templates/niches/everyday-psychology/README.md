# Starter kit: Everyday psychology

A generic starting point for a channel that explains why people do the small everyday things they do: procrastinating, forgetting, overspending, sleeping badly, and the habits that help. Copy the folder's files into `channels/<your-id>/`, then change the names, colors, voice and posting slots to your own. Nothing here is a finished channel: write your own angle, ideas and scripts.

## Files
| File | Copy to | Change at least |
|---|---|---|
| `channel.json` | `channels/<id>/channel.json` | `id`, `name`, `language`, `voice`, `posting_slots`, `timezone`, `sensitive_topic` (see below), `started_on`, `style_approved_on` |
| `style-bible.md` | `channels/<id>/style-bible.md` | palette, typography, the everyperson character, opening and closing ritual |
| `ideas.md` | `channels/<id>/ideas.md` | check every source yourself, then add your own ideas until there are 30 |

## The niche in short
- **Curiosity it satisfies:** "Why do I keep doing this, and is there a simple fix?"
- **Binge loop:** one everyday behavior per video, shown on a cartoon everyperson the viewer recognizes as themselves; each video ends with one small thing to try.
- **Topic capacity:** several hundred (habits, memory, attention, decisions, shopping, social behavior, sleep, motivation); estimate 250+, fewer if you only keep well-replicated findings.
- **Demand signals to check:** search suggestions for "why do I <behavior>", "psychology of <behavior>", "how to stop <habit>"; outlier explainer Shorts from small channels (`scripts/youtube_research.py outliers`). Record what you find in `research/patterns.md`.
- **Why it suits akra:** behavior is easy to act out with one simple drawn character (wrong way, then right way), and mental processes are invisible, so a drawn diagram shows them better than footage.

## Series formats
- **"Why you do that":** the everyperson does a familiar thing, a simple process diagram shows what is going on.
- **"Wrong way / right way":** the common habit fails as a gag, the evidence-based version works.
- **"Myth or fact":** a popular psychology claim stamped MYTH or FACT, with the source.
- **"Brain hack, tested":** one study-backed technique (memory, focus, planning) shown in three steps.

## Hook formulas (write your own words)
- "You don't <behavior> because you're lazy."
- "Your brain <does surprising thing> every time you <action>."
- "<Popular claim>? Researchers tested it."
- "The <number>-second trick that helps you <goal>."

## Scene patterns that fit
Wrong → right gag · Myth vs fact · Process diagram (input → brain → behavior) · Before → after (see `templates/shot-plan.md`). Scene type `diagram` only; no `stock` footage.

## Sources that fit
Peer-reviewed review articles and meta-analyses, university psychology departments, the American Psychological Association (APA) and other national psychological associations, national health services (NHS, CDC, NIH) for sleep and health-adjacent habits, large multi-lab replication projects for claims that did or did not hold up. One single small study is not enough for a "fact".

## `sensitive_topic` choice
The kit ships with `"sensitive_topic": null`, because the default topics are everyday habits and thinking errors, not health care. If you also cover mental health (anxiety, depression, trauma, ADHD, eating, self-harm) or medical sleep problems (insomnia, sleep apnea), set `"sensitive_topic": "health"` in `channel.json`, add the disclaimer below to every such episode, and fill the "Sensitive topic" section of the style bible:
- "This video is general information, not medical or mental-health advice. If you are struggling, talk to a doctor or a licensed mental-health professional."
Episodes that touch suicide or self-harm also point to a crisis line for the audience's country.

## Risks
- **Not treatment:** no diagnosing ("if you do this, you have <disorder>"), no therapy or cure claims, no advice to stop or change medication. For anxiety or depression topics, point to professional help.
- **Pop-psych myths:** learning styles, left-brain/right-brain personalities, "we only use 10% of our brain" and similar claims are only covered to debunk them, with sources.
- **Replication:** some famous findings did not replicate (for example, large multi-lab tests of "ego depletion" did not find the original effect). When a well-known study failed to replicate, say so in the script instead of presenting it as fact.
- **Overclaiming:** say "on average", "in studies", "for many people"; effects are tendencies, not laws, and the everyperson is not a diagnosis.
- **Stereotypes:** the everyperson is generic; do not attach a behavior to a gender, age group, nationality or condition for a joke.
- **Medical misinformation policy:** sleep and health-adjacent claims follow national health service guidance; when they conflict with a newer study, use the health service.
