#!/usr/bin/env python3
"""Episode build for akra (HyperFrames). Copy of render/_template/ - see README.md.

Reads channels/<CHANNEL>/episodes/<folder name>.json + assets/transcript.json and writes
index.html, compositions/sNN.html (one per shot) and compositions/captions.html.

Shots without a scene function render as storyboard cards (animatic), so the project
builds and previews from the first minute. Replace them one by one with drawings.
Shared helpers (timing, pop/fade/push, banner/pill, baked backgrounds, finish) live in
scenekit.py: keep this file to the episode's own drawings. Props + environments for the
episode go in envNN.py next to it.

Re-run after editing the episode, the transcript or this file:  python3 build.py
"""
import os
import sys

import channelcfg
import character  # noqa: F401  (shim: puts the repo or _lib_frozen on sys.path; keep BEFORE library)
import depth  # noqa: F401  (depth.defs(p), depth.bokeh, ... for drawn scenes)
import hf
import scenekit as sk
from library.lib import Library  # noqa: F401
from scenekit import ACCENT, GRAPH, INK, PRIMARY, banner, fade, pill, pop, push  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
EP_ID = os.path.basename(HERE)                   # render/<channel-id>/ep-002/ -> ep-002
if EP_ID == "_template":                         # the template itself builds the example episode
    EP_PATH = os.path.join(HERE, "..", "..", "skills", "akra", "templates", "episode.example.json")
    SHOTS, WORDS = [], []
else:
    EP_PATH = sk.ep_path(HERE)
    EP, SHOTS, WORDS = sk.load(HERE)
at = sk.timer(WORDS)                             # at(shot, "word") -> seconds into that shot

# ---- library (optional: your own registered items; see skills/akra/references/library.md) ----
# L = Library(HERE, channelcfg.locate(HERE)[1])
# BK = sk.bake_envs(HERE, {"my_room": L.env("my_room")})                          # (fn, backdrop) for bake_envs
# with a character rig in library/rig/:
# hero = L.character("my_host", "pa", 540, 1500, s=1.2)      # character (svg); look variations are checked against the item ranges
# js += L.rig.pose("pa", L.pose("point"), at(shot, "word"))   # pose name is checked for the channel style


# ---- environments (baked once to assets/bg/*.png) ------------------------------------------
# def _lab(rnd, fl):                             # far/mid layers; append glows to fl
#     far = f'<rect width="1080" height="1920" fill="#2A2E2A"/>'
#     return far, ""
# BK = sk.bake_envs(HERE, {"lab": (_lab, "#2A2E2A")})
BK = {}


# ---- scenes ------------------------------------------------------------------------------
# One function per shot, in time order: fn(p, d, shot) -> (svg, js)
#   p    : scene id prefix ("s01"); prefix every element id with it
#   d    : scene duration (s); timeline times are LOCAL to the scene
#   shot : the shot dict from the Episode Package (narration, prompt, ...)
# Pattern: svg = BK["lab"] + depth.defs(p) + '<g id="{p}-cam">' + hero + '</g>' + sk.finish(p, BK) + overlays + sk.BRAND
#          js  = push(p, "cam", d) + pop(p, "ban", at(shot, "word"))
# Hook banner visible on frame 0 (sk.show_now) and again for the last >= 2 s, so the Short loops.

def s01(p, d, shot):
    """Example scene: a part in the primary colour that the voice names on the hook."""
    svg = (f'<rect id="{p}-part" x="340" y="560" width="400" height="400" rx="40" fill="{PRIMARY}"/>'
           + banner(p, "ban", 540, 1095, 420, 112, "THE PART", 62) + sk.BRAND)
    js = sk.show_now(p, "ban") + pop(p, "part", 0.4, 0.4, 0.6)
    return svg, js


SCENES = [s01]          # shots after the last listed function use storyboard cards

# ---- sound effects: (file in assets/sfx without .wav, absolute start s, volume) ------------
# Each on a visible action; peak ~1 frame after the picture. sk.abs_t(SHOTS, WORDS, k, "word")
# gives the absolute time of a word in shot k. Credit CC BY sounds in assets/sfx/CREDITS.md.
SFX = [
    ("whoosh", 0.05, 0.4),
]


if __name__ == "__main__":
    if not os.path.exists(EP_PATH):
        sys.exit(f"episode not found: {EP_PATH}")
    hf.build(HERE, EP_PATH, SCENES, SFX, sk.BRAND_TEXT)
