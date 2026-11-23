"""anime.js (v4) animation in akra scenes, rendered by HyperFrames like any other scene.

Use it for what anime.js does well on the scene's SVG: staggers over many parts, SVG line drawing, morphing,
keyframes. The scene function returns (svg, js, html): the html is the module script below.

    import animekit

    def s04(p, d, shot):
        html, js = animekit.scene(p, d, f'''
            const tl = createTimeline({{ autoplay: false }});
            tl.add("#{p}-teeth rect", {{ opacity: [0, 1], y: [20, 0], delay: stagger(60), duration: 500 }}, 300);
            tl.add(svg.createDrawable("#{p}-path"), {{ draw: ["0 0", "0 1"], duration: 1200 }}, 800);
            return tl;                                   // or one animation, or an array of them
        ''')
        return svg_markup, js, html

To drive something anime.js cannot reach directly (a character rig, a canvas), animate a plain object and redraw
from it after every seek: return { anims: tl, after: (t) => redraw(state) } (seek mutes anime.js callbacks, so
do the drawing in `after`, not in onUpdate).

How it renders: anime.js never plays on its own (autoplay: false). The scene's GSAP timeline tweens a clock from 0
to the scene length and seeks every returned animation to that time, so frames can render in any order. Times in
anime.js are milliseconds from the scene start. Rules: create everything with autoplay: false, use
`utils.random` only through `rand` (seeded, see below) or anime's createSeededRandom, no loops without an end
(finite `loop` counts only), and never animate the same property of one element from both GSAP and anime.js.

In your code you get the anime.js v4 exports (animate, createTimeline, stagger, utils, svg, eases,
createSeededRandom) and rand() (seeded 0..1).
"""
import json

ANIME_VERSION = "4.4.1"            # pinned
ANIME_URL = f"https://cdn.jsdelivr.net/npm/animejs@{ANIME_VERSION}/+esm"

_MODULE = """<script type="module">
import { animate, createTimeline, stagger, utils, svg, eases, createSeededRandom } from "%(url)s";
const host = window.__akraAnime[%(key)s];
try {
const rand = createSeededRandom(%(seed)d);
const made = (() => {          // not async: anime.js animations are thenables, await would wait for the end
%(body)s
})();
const spec = made && made.anims ? made : { anims: made };
const list = (Array.isArray(spec.anims) ? spec.anims : [spec.anims]).filter(Boolean);
const after = typeof spec.after === "function" ? spec.after : null;
if (!list.length || list.some((a) => typeof a.seek !== "function"))
  throw new Error("animekit scene %(key_raw)s: return an anime.js animation, timeline, or an array of them");
host.render = (t) => { for (const a of list) a.seek(t * 1000, true); if (after) after(t); };
host.render(host.clock.t);
host.ready();
} catch (err) { host.fail(err); throw err; }
</script>"""


def scene(p, dur, body, seed=1):
    """anime.js layer for scene `p` lasting `dur` s. `body` is JS that creates animations with autoplay: false and
    RETURNS them. Returns (html, js): put js in the scene's timeline code, return html as the third value."""
    key = f"{p}-anime"
    module = _MODULE % {"url": ANIME_URL, "key": json.dumps(key), "key_raw": key, "seed": int(seed), "body": body}
    js = (f'(function(){{const c={{t:0}},h={{clock:c,render:null}};'
          f'window.__akraAnime=window.__akraAnime||{{}};window.__akraAnime[{json.dumps(key)}]=h;'
          f'window.__hf=window.__hf||{{}};window.__hf.buildReady=window.__hf.buildReady||{{}};'
          f'window.__hf.buildReady[{json.dumps(key)}]=new Promise(function(r,j){{h.ready=r;h.fail=j;}});'
          f'tl.to(c,{{t:{dur:.2f},duration:{dur:.2f},ease:"none",onUpdate:function(){{if(h.render)h.render(c.t);}}}},0);}})();')
    return module, js
