# Niche starter kits

Seven generic starting points for a new channel. Each kit is a folder with an example Channel Profile, a filled 12-section style bible, 10 starter ideas and a short guide to the niche (curiosity, binge loop, topic capacity, series formats, hook formulas, sources, risks). Every value is a suggestion you are expected to change.

| Kit | Niche | Sensitive topic | Fits akra because |
|---|---|---|---|
| `how-things-work/` | how everyday things work | none | real objects with a see-through cutaway |
| `science-space/` | science and space facts | none | scale comparisons and invisible processes drawn as diagrams |
| `history-origins/` | origins of everyday objects, customs and words | none | timelines, maps and cartoon period characters |
| `home-exercise/` | gentle home exercise for beginners and older adults | health | coach + doer characters, rep counters, safety lines |
| `game-tips/` | tips for one game | none (gameplay footage rules apply) | own narration with drawn overlays on your own gameplay |
| `animal-nature/` | animal and nature facts | none (decide made-for-kids honestly) | cartoon animals, cutaways, scale against home objects |
| `everyday-psychology/` | everyday psychology and habits | none by default; health if you cover mental health | everyperson character, wrong-then-right gags, myth vs fact |

## How to start a channel from a kit
1. Pick a kit with `templates/niche-brief.md` (score it against your own candidates first).
2. Copy `channel.json`, `style-bible.md` and `ideas.md` into `channels/<your-id>/`.
3. Change at least: `id`, `name`, `language`, `voice` (and its license fields), `posting_slots`, `timezone`, dates, palette, cast and rituals.
4. Check every source in `ideas.md` yourself and rewrite the hooks in your own words; add ideas until there are 30.
5. Run `python3 skills/akra/scripts/validate_episode.py validate-channel channels/<your-id>/channel.json` until it prints `OK`.
6. Render 2–3 style frames and approve the style bible before the first episode (`references/channel-setup.md`).

## Do not
- Publish the kit as it is: many channels starting from the same kit with the same look would read as repetitive content. Make the look, cast and angle your own.
- Keep a placeholder (`<…>`) or an example date in a live channel.
