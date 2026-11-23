# Starter kit: Gentle home exercise

A generic starting point for a channel that shows one gentle home exercise per video for beginners and older adults: chair exercises, walking, balance and stretching. Copy the folder's files into `channels/<your-id>/`, then change the names, colors, cast, voice and posting slots to your own. Nothing here is a finished channel: write your own angle, ideas and scripts.

This is a **health** channel (`sensitive_topic: "health"`). The validator checks every episode for the disclaimer and the forbidden claim words, and the persona must not claim a credential (doctor, nurse, physiotherapist and so on).

## Files
| File | Copy to | Change at least |
|---|---|---|
| `channel.json` | `channels/<id>/channel.json` | `id`, `name`, `language`, `voice`, `posting_slots`, `timezone`, `started_on`, `style_approved_on`, `disclaimer` (keep its meaning) |
| `style-bible.md` | `channels/<id>/style-bible.md` | palette, typography, the two characters, opening and closing ritual, movement limits (only stricter) |
| `ideas.md` | `channels/<id>/ideas.md` | check every source yourself, then add your own ideas until there are 30 |

## The niche in short
- **Curiosity it satisfies:** "I want to move more, but I'm stiff, unsure or not young; what can I safely do at home?"
- **Binge loop:** one move per video, done together in real time; viewers save the videos and come back to repeat them.
- **Topic capacity:** large (seated strength, standing balance, walking, stretching, breathing, everyday moves like getting up from the floor); estimate 200+.
- **Demand signals to check:** search suggestions for "chair exercises for <group>" and "exercises for <body part> at home"; outlier Shorts from small channels (`scripts/youtube_research.py outliers`). Record what you find in `research/patterns.md`.
- **Why it suits akra:** a cartoon character shows the move cleanly from the best angle, with arrows on the joint that moves; no gym, no filming, no real body on camera.

## Series formats
- **"Chair club":** one move done seated or holding the chair back, 5 slow reps counted on screen.
- **"Steady feet":** one balance move next to a wall or chair, with the support always in reach.
- **"Do it during":** a move that fits an everyday moment (waiting for the kettle, the TV ad break).
- **"Why it helps":** the plain reason behind a guideline (how much to move, the talk test, breathing out on the effort).

## Hook formulas (write your own words)
- "You can do this one without leaving your chair."
- "Standing up from a chair is already a <muscle> workout."
- "Hold the chair. Now try this for <short time>."
- "The easiest way to start moving after a long sit."

## Safety lines
Say one safety line in every video, and the one that fits the move's main risk. Generic wording below; check it against the source and keep it general (no personal advice).

| Condition or situation | Generic safety line | Source type |
|---|---|---|
| Dizziness, chest pain, unusual breathlessness | "Stop, sit down and rest. If it doesn't pass, get medical help." | national health service exercise safety page; heart foundation |
| High blood pressure | "Breathe out as you push. Don't hold your breath." | heart foundation guidance on strength exercise |
| Diabetes | "Keep a snack nearby. If you use insulin, check your sugar first." | national diabetes association exercise page |
| Joint pain or arthritis | "Move in a small range. It should never hurt." | arthritis foundation or national health service page |
| Balance problems or fall risk | "Hold a chair or wall the whole time." | national health service or CDC falls prevention page |
| After surgery, during or after pregnancy | "Ask your doctor first before you try this." | national health service; national obstetrics body |
| New to exercise or a long break | "Start with fewer reps. Add more over the weeks." | WHO physical activity guidelines |

## Scene patterns that fit
Demonstration with a rep counter · Right way vs common mistake · Before → after (stiff → moving) · Myth vs fact (see `templates/shot-plan.md`).

## Sources that fit
WHO physical activity guidelines, NHS exercise and "strength and balance" pages, CDC physical activity pages, national health services of other countries, heart foundations, arthritis and diabetes associations, falls-prevention programmes run by health authorities. Not: influencer posts, supplement sellers, single small studies.

## Risks
- **Medical misinformation (YT-MED-1):** no "cures", "heals", "reverses" or weight-loss promises; frame every benefit as general ("helps keep your legs strong"), sourced.
- **Persona (YT-CH-2):** never present the narrator or coach as a doctor, physiotherapist or trainer.
- **Physical safety:** low-impact moves only, support always in reach, slow tempo, a safety line every time; see the movement limits in `style-bible.md`.
- **Audience:** older viewers watch on small screens; big text, slow captions, no fast cuts.
- **Repetition:** vary the move, the room and the everyday moment, not only the body part name.
