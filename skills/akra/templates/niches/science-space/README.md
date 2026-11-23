# Starter kit: Science and space facts

A generic starting point for a channel that makes the very big, the very small and the invisible easy to see: planet sizes, what happens inside a star, why the sky looks the way it does. Copy the folder's files into `channels/<your-id>/`, then change the names, colors, voice and posting slots to your own. Nothing here is a finished channel: write your own angle, ideas and scripts.

## Files
| File | Copy to | Change at least |
|---|---|---|
| `channel.json` | `channels/<id>/channel.json` | `id`, `name`, `language`, `voice`, `posting_slots`, `timezone`, `started_on`, `style_approved_on` |
| `style-bible.md` | `channels/<id>/style-bible.md` | palette, typography, the guide probe (or `not used`), opening and closing ritual |
| `ideas.md` | `channels/<id>/ideas.md` | check every source yourself, then add your own ideas until there are 30 |

## The niche in short
- **Curiosity it satisfies:** "I've looked at the sky my whole life; why does it work like that?"
- **Binge loop:** one question, one picture that makes it obvious; scale videos make viewers want the next comparison.
- **Topic capacity:** very large (planets and moons, stars, light, weather, the human scale of space, everyday physics); estimate 400+.
- **Demand signals to check:** search suggestions for "why is the <thing>" and "how big is <planet>"; outlier space Shorts from small channels (`scripts/youtube_research.py outliers`). Record what you find in `research/patterns.md`.
- **Why it suits akra:** scale, orbits and invisible processes are drawn better than filmed; one shared ruler and a cutaway do the explaining.

## Series formats
- **"To scale":** two things side by side on one ruler, then the camera pulls back to show the real gap.
- **"Invisible made visible":** a process you cannot see (scattering, tides, air pressure) drawn as particles and arrows.
- **"Weird worlds":** one strange fact about a planet or moon, compared with Earth.
- **"Sky questions":** everyday weather and sky (blue sky, twinkling stars, seasons) answered in one picture.

## Hook formulas (write your own words)
- "<familiar thing> is <surprising size/time> compared with <other thing>."
- "On <planet>, <everyday thing> works backwards."
- "You can't see <process>, but it happens every <time>."
- "The <light/sky/weather> you see right now is <surprising fact>."

## Scene patterns that fit
Scale comparison · Reveal / cutaway · Before → after · Myth vs fact (see `templates/shot-plan.md`).

## Sources that fit
NASA mission and science pages (including NASA Space Place for plain-language basics), ESA science pages, NOAA and national weather services for weather, university astronomy and physics department explainers, peer-reviewed journals for newer results, encyclopedias (Britannica) for definitions.

## Risks
- **Accuracy:** numbers change with new measurements; round with "about" and use the value on the source page, never a number from memory.
- **Scale honesty:** when sizes and distances cannot share one frame, show a "not to scale" tag; never mix the two silently.
- **Agencies and brands:** draw generic spacecraft; no NASA or ESA logos, mission patches or anything that suggests the channel is official. Do not use agency photos; everything is code-drawn.
- **Speculation:** label ideas that are not settled ("scientists think", "one model says") and do not present them as fact; no doom or fake-danger hooks (asteroid panic, "the Sun will explode tomorrow").
- **Real people:** astronauts and scientists are not drawn as likenesses; use a generic suited figure if a human is needed.
