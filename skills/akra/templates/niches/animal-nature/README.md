# Starter kit: Animal and nature facts

A generic starting point for a channel that explains how animals and plants work: their bodies, behaviour and life cycles. Copy the folder's files into `channels/<your-id>/`, then change the names, colors, voice and posting slots to your own. Nothing here is a finished channel: write your own angle, ideas and scripts.

## Files
| File | Copy to | Change at least |
|---|---|---|
| `channel.json` | `channels/<id>/channel.json` | `id`, `name`, `language`, `voice`, `posting_slots`, `timezone`, `started_on`, `style_approved_on`, `made_for_kids` (decide it, see Risks) |
| `style-bible.md` | `channels/<id>/style-bible.md` | palette, typography, the guide (or `not used`), opening and closing ritual |
| `ideas.md` | `channels/<id>/ideas.md` | check every source yourself, then add your own ideas until there are 30 |

## The niche in short
- **Curiosity it satisfies:** "Why does that animal (or plant) do that, and how does its body pull it off?"
- **Binge loop:** one living thing, one surprising body part or behaviour per video; viewers collect strange facts and share them.
- **Topic capacity:** very large (mammals, birds, insects, sea life, reptiles, plants, fungi, habitats); estimate 500+.
- **Demand signals to check:** search suggestions for "why do <animal> <behaviour>" and "how does a <animal> <ability>"; outlier animal-fact Shorts from small channels (`scripts/youtube_research.py outliers`). Record what you find in `research/patterns.md`.
- **Why it suits akra:** a cartoon animal with accurate anatomy cues can be opened up, scaled next to a hand or a mug and placed on a habitat map; things that are hard or impossible to film (inside a chrysalis, inside an eye) are easy to draw.

## Series formats
- **"Inside the animal":** a cutaway of one body part and what it does.
- **"Myth or fact":** a common belief, the stamp, the real explanation.
- **"Life cycle":** one living thing from start to adult in 40 seconds.
- **"Plant tricks":** how a plant moves water, catches food or follows light.

## Hook formulas (write your own words)
- "A <animal> can <ability>. Here's the body part that does it."
- "<animal> aren't <common belief>. It's their <food/body part>."
- "Put your hand next to a <animal>'s <part>."
- "This plant <surprising action> without a single muscle."

## Scene patterns that fit
Reveal / cutaway · Scale comparison (hand, coin, mug, door, bus) · Habitat map · Myth vs fact · Life-cycle sequence (see `templates/shot-plan.md`).

## Sources that fit
National Geographic Society education pages, museums of natural history (education and collection pages), zoos and aquariums with education pages, university biology and veterinary departments, the IUCN Red List for status and range, botanic gardens for plants, encyclopedias (Britannica). Not: viral fact lists without a source.

## Risks
- **Made for kids (YT-KIDS-1):** cute animals attract children. Decide honestly by who you make it for, not by revenue: if the script, pace and look are aimed at children, set `made_for_kids: true`. This kit defaults to `false` because it targets curious viewers 13+ (vocabulary, pace, anatomy detail and no toy-like characters); keep the style that way, or change the field.
- **No gore:** predation and death are shown as a cut, a silhouette or a before/after, never blood or wounds (also keeps ads).
- **Dangerous handling:** never suggest touching, catching, feeding or keeping wild animals; say "watch from a distance" where it applies.
- **No pet medical advice:** explain how a body works; for a sick pet the only line is "ask a vet".
- **Accuracy:** no false anthropomorphism ("it feels sad"); scale, numbers and range must match the source; mark disputed claims as such or skip them.
- **Repetition:** vary the animal group and the habitat, not only the species name.
