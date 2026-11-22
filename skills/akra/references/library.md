# Asset library (mode `library`)

The library is optional. It is an engine for reusable items you make yourself: it checks them against a schema, locks them to the channel's style, records which items an episode uses, and freezes them into the episode once it is final. Episodes that draw everything in their scenes do not need it.

- Engine: `library/` (`lib.py` loader, `schema.py`, `catalog.py`, `cli.py`, `freeze.py`, `preview.py`). Built-in items go in `library/characters/`, `library/envs/` and `library/poses/`; `library/catalog.json` lists them.
- Your own items: `channels/_library/` (same folders, local, not committed). An item there may not reuse a built-in id.
- Commands: `python3 library/cli.py <list|build-catalog|preview|vet|freeze|promote>` from the project root.
- If `references/` holds a `rig*.md` file, it describes the rig and built-in items of this installation; read it as well.

## Item kinds and styles
- Kinds: `character`, `pose` (a set of poses per style), `env` (environment: far and mid layers, safe area, variants). Story objects (cup, ladder, rope) are not library items; draw them in the episode file.
- Style slots: `hw` and `toon`, locked per channel (`channels/<id>/library.json` -> `style`). Items of the other style are rejected by the loader.
- Status: `draft` (not approved, must not be used in a final render) or `vetted`. Origin: `builtin` or `generated` (`generated` needs `token_cost`).
- Every item has `id`, `kind`, `name`, `tags`, `style`, `status`, `origin`, `created` (YYYY-MM-DD), `created_by`, `preview` (path of its preview PNG) and `examples` (episode ids). `python3 library/cli.py list` prints what is installed.

## Add your own items
1. **Environment** (works with the engine alone): `channels/_library/envs/<id>.json` plus the module it names.
   ```json
   {"id": "my_room", "kind": "env", "name": "My room", "tags": ["room"], "style": "hw", "status": "draft",
    "origin": "generated", "token_cost": 0, "created": "2026-01-01", "created_by": "me",
    "preview": "previews/envs/my_room.png", "examples": [], "module": "my_room.py", "function": "build",
    "variants": ["default", "night"], "backdrop": "#202830", "safe_area": [60, 820, 1020, 1170], "palette": ["#202830"]}
   ```
   `channels/_library/envs/my_room.py` defines `build(rnd, fl, variant="default") -> (far_svg, mid_svg)` and appends glows to `fl`. `safe_area` is `[x0, y0, x1, y1]` inside 1080×1920, and `variants` must contain `default`.
2. **Character or pose set** (needs a rig). A character item adds `base_look` (dict), `variants` (`{"type": "color"}`, `{"type": "bool"}`, `{"type": "color", "nullable": true}`, `{"enum": [...]}` or `{"min": a, "max": b}`), `face` (equal to `style`) and `scale_hint`. A pose set adds `params_file` (a JSON of pose name -> parameters) and `needs` (`chair`, `rail`, `ik_target`).
   The loader draws them with a rig module `library/rig/<style>.py` that provides `look(**kw)`, `character(cid, x, y_feet, s, look, facing)`, a `POSES` dict and `set_pose`/`pose`. This distribution ships no rig: without one, character and pose calls raise "character rig not included in this distribution". Either draw characters as SVG in the scene functions (references/build.md, Characters) or add your own rig module.
3. Select the items for the channel in `channels/<id>/library.json`: `{"style": "hw", "visual_mode": "diagram", "items": ["my_room"]}`. An empty `items` list allows every item of that style.
4. Check them: `python3 library/cli.py list --status draft`, then `preview <id>` (headless Chrome; an environment sheet shows up to 3 variants with the safe area drawn).

## How an episode uses the library
`build.py` creates `L = Library(HERE, channelcfg.locate(HERE)[1])`, then calls:
- `L.env("my_room", variant="default")`: returns `(env_function, backdrop_color)` for `sk.bake_envs`.
- With a rig: `L.character(<id>, cid, x, y_feet, s=1.0, facing="right", **variations)` (variations are checked against the item's ranges) and `L.pose(<name>)` (a pose name valid for the channel's style).
The loader records use in `.lib_used.json` and warns about `draft` items; `qa_render.py` FAILS if a `draft` item is used in a final render.

Escape hatch for one-off scenes: `L.custom_look(...)` and `L.custom_pose(name, **param)`. Allowed. The loader records them in `.lib_used.json` (`custom`); write them yourself in that episode's `REVIEW.md` as library item candidates.

## Create new
For an item that does not exist yet (e.g. "car workshop at night"):
1. The user describes the item.
2. Before starting, show an **estimate of the token cost** (environments and poses are cheaper than characters) and **wait for the user's confirmation**. The user bears the tokens; in local mode with a subscription, what gets used is the quota. Do not start before there is confirmation.
3. Create the item in library format in `channels/_library/` (status `draft`, `origin: generated`).
4. Make the preview sheet with `preview <id>`.
5. Check quality with the standard in `references/build.md`: not cut by the frame edge, no stray marks, the safe area stays clear; for characters also joints connected, hands reach their target and identity readable. Look at the image yourself before showing it.
6. Show the preview to the user and ask for approval. Rejected = the item stays `draft` and is not used.

## vet
`python3 library/cli.py vet <id>` is only run **after the user approves the preview** (needs explicit approval for that item). The command refuses if the preview does not exist or is older than the item file. The result is `status: vetted`. Never vet on your own.

## Freeze and refresh
- `python3 library/cli.py freeze <episode-project>` copies the library to `<project>/_lib_frozen`. Run automatically by `qa_render.py` at the end of a final render, only if all checks pass and no `draft` item is used (drafts are never frozen). While that folder exists, the build uses the frozen copy, so episode revisions do not change silently.
- `freeze <project> --refresh` takes the latest library. Each time it is used, **note in that episode's `REVIEW.md`** what changed and why.

## promote
`python3 library/cli.py promote <id> --yes` turns a local item into a built-in item (channel-specific data such as real character names and notes are dropped). Needs the user's **approval** for that item; do not run `--yes` without approval. An item may only be promoted if it is already `vetted` (the `promote` command refuses `draft` items). After promote, commit only if the user asks.
