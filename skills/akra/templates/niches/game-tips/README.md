# Starter kit: Game tips

A generic starting point for a channel that explains one game you play: mechanics the game never spells out, hidden features, beginner mistakes and efficient routes. Pick your game, replace `<Game Title>` everywhere, then copy the folder's files into `channels/<your-id>/` and change the names, colors, voice and posting slots to your own. Nothing here is a finished channel: write your own angle, ideas and scripts.

## Files
| File | Copy to | Change at least |
|---|---|---|
| `channel.json` | `channels/<id>/channel.json` | `id`, `name`, `niche` (your game), `language`, `voice`, `posting_slots`, `timezone`, `research.queries`, `started_on`, `style_approved_on` |
| `style-bible.md` | `channels/<id>/style-bible.md` | palette, typography, the publisher's video policy URL, opening and closing ritual |
| `ideas.md` | `channels/<id>/ideas.md` | test every tip in the current game version yourself, then add your own ideas until there are 30 |

## The niche in short
- **Curiosity it satisfies:** "I play this game; what am I missing that better players already know?"
- **Binge loop:** one tip per video, numbered within a series; viewers save the tips and come back for the next one before their next session.
- **Topic capacity:** depends on the game. A deep game with regular updates gives 150+ tips (systems, items, map, modes, each patch); a small game may run out after 30. Check before you commit.
- **Demand signals to check:** search suggestions for "<Game Title> tips", "<Game Title> how to", "<Game Title> beginner mistakes"; outlier tip Shorts from small channels (`scripts/youtube_research.py outliers`). Record what you find in `research/patterns.md`.
- **Why it suits akra:** the tip is explained by the channel's own narration and code-drawn overlays (step chips, arrows, mini-maps, comparison cards); gameplay is only short evidence underneath, or the whole idea is drawn as a diagram.

## Series formats
- **"The game never tells you":** one mechanic or stat the tutorial skips, shown with a drawn diagram.
- **"Stop doing this":** a common beginner mistake vs the better way, as a split comparison card.
- **"Fastest route":** a mini-map with numbered stops for a resource, quest or unlock.
- **Patch check:** what one official patch note actually changes in play, tested by you.

## Hook formulas (write your own words)
- "This stat in <Game Title> matters more than <obvious stat>."
- "You've been <common action> wrong since the tutorial."
- "<Number> minutes to <goal> if you go this way."
- "The last patch quietly changed <system>."

## Scene patterns that fit
Mini-map route · Before → after · Comparison card · Step-by-step chips · Myth vs fact (see `templates/shot-plan.md`). Scene type `diagram` by default; `stock` only for your own gameplay clips (see below).

## Sources that fit
Official patch notes, the official game guide or wiki run by the publisher, the in-game help or codex text, and your own in-game test. Every tested tip states the version: "tested in version x.y". Fan wikis are a lead to check in game, not a source.

## Risks
- **Publisher video policy:** before monetizing, find the publisher's video/streaming policy (often called "video policy", "content creator policy" or "fan content policy"), check that monetized videos are allowed, and record the URL and date in the style bible (section 10). If the policy forbids monetization, use fully drawn diagrams only, or pick another game.
- **Footage:** only your own gameplay. Never re-upload trailers, cinematics, press kits or other creators' footage.
- **Reused content:** clips are short (a few seconds each) and always transformed by your narration and overlays. A video that is mostly raw gameplay with little commentary risks the reused-content rule and demonetization.
- **Terms of service:** no leaks, datamined unreleased content, piracy, mods or cheats that break the terms of service, and no exploits that harm other players (duping, griefing, online glitches). Single-player tricks the game allows are fine.
- **Spoilers:** story content gets a spoiler warning in the first second and in the title.
- **`ai_disclosure`:** `true` for episodes that use realistic gameplay footage (package-qa.md treats realistic-looking gameplay as needing the label), `false` for fully drawn episodes.
- **Logos and brands:** no publisher or game logos beyond what the policy allows; draw generic icons for items and UI.
- **Version drift:** tips go stale after patches. Put the version in the description and recheck old tips after major updates.
- **Not for kids by default:** game tips usually target teens and adults; answer "made for kids" honestly per episode, and if the game itself is rated for adults, never aim the channel at children.
