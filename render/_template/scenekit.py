"""scenekit - the per-episode boilerplate an akra build.py would otherwise copy, in one shared module.

    import scenekit as sk
    EP, SHOTS, WORDS = sk.load(HERE)                 # episode JSON, shots sorted by time, transcript words
    at = sk.timer(WORDS)                             # at(shot, "word", nth=1) -> local seconds in that shot
    BK = sk.bake_envs(HERE, {"lab": (_lab, "#2A2E2A")})   # baked PNG backgrounds + grain
    svg = BK["lab"] + depth.defs(p) + ... + sk.finish(p, BK, capband=True) + sk.banner(p, "ban", ...) + sk.BRAND
    js  = sk.pop(p, "ban", at(shot, "word")) + sk.push(p, "cam", d)
    SFX = [("click", sk.abs_t(SHOTS, WORDS, 3, "word"), 0.3)]

Timeline helpers return GSAP strings for the scene's `tl`; times are LOCAL to the scene.
Text helpers: t (svg text), BRAND (channel line at y228), banner (tilted keyword plate, hidden until pop),
pill (outlined label, width from the text). Layout rules they follow: build.md (text >= 28 px, brand y228,
caption band 1110-1330 kept clear, keep pills off faces).
"""
import json
import os
import random
import re

import channelcfg
import depth

W, H = 1080, 1920
# Brand comes from channels/<id>/channel.json -> brand (channelcfg.py).
CFG = channelcfg.settings(os.path.dirname(os.path.abspath(__file__)))
_C = CFG["colors"]
GRAPH = _C["bg"]; INK = _C["ink"]; MUT = _C["muted"]; DIM = _C["dim"]
PRIMARY = _C["primary"]; BRL = _C["primary_light"]; ACCENT = _C["accent"]; ORANGE = _C["highlight"]
BRASS, CYAN = PRIMARY, ACCENT      # older names of the same two colours
FONT = CFG["font"]
CHANNEL = CFG["channel"]
BRAND_TEXT = CFG["brand_text"]
ROOT = CFG["root"]


# ---- episode data ------------------------------------------------------------------------------------
def ep_path(here, channel=None):
    """channels/<channel>/episodes/<folder name>.json; channel and root follow the folder layout (channelcfg)."""
    root, found = channelcfg.locate(here)
    return os.path.join(root, "channels", channel or found, "episodes", f"{os.path.basename(os.path.abspath(here))}.json")


def load(here, channel=None):
    """(episode dict, shots sorted by t_start, transcript words that contain a letter/digit)."""
    ep = json.load(open(ep_path(here, channel)))
    shots = sorted(ep["shots"], key=lambda s: s["t_start"])
    tr = os.path.join(here, "assets", "transcript.json")
    words = [w for w in json.load(open(tr)) if re.search(r"[A-Za-z0-9]", w["text"])] if os.path.exists(tr) else []
    return ep, shots, words


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def timer(words):
    """at(shot, word, nth=1): seconds from the shot start to the nth time `word` is spoken inside the shot.
    Words are matched lowercase alphanumeric ("don't" -> "dont", "ninety-two" -> "ninetytwo")."""
    def at(shot, word, nth=1):
        n = 0
        for w in words:
            if shot["t_start"] - 0.05 <= w["start"] < shot["t_end"] and norm(w["text"]) == word:
                n += 1
                if n == nth:
                    return round(w["start"] - shot["t_start"], 2)
        raise KeyError(f"{word!r} (#{nth}) not spoken in shot {shot['narration']!r}")
    return at


def abs_t(shots, words, k, word, nth=1):
    """Absolute time of a word in shot k (for SFX cues)."""
    return round(shots[k]["t_start"] + timer(words)(shots[k], word, nth), 2)


# ---- timeline helpers (GSAP strings for `tl`) --------------------------------------------------------
def pop(p, eid, at_, d=0.35, s0=1.6):
    """Spring a hidden element in (opacity 0 -> 1, scale s0 -> 1)."""
    return (f'tl.fromTo("#{p}-{eid}",{{opacity:0,scale:{s0},transformOrigin:"50% 50%"}},'
            f'{{opacity:1,scale:1,duration:{d},ease:"back.out(2.2)"}},{at_:.2f});')


def fade(p, eid, at_, d=0.3, to=1):
    return f'tl.to("#{p}-{eid}",{{opacity:{to},duration:{d}}},{at_:.2f});'


def shake(p, eid, at_, amp=12, n=3):
    return (f'tl.fromTo("#{p}-{eid}",{{x:0}},{{x:{amp},duration:0.05,yoyo:true,repeat:{n * 2 - 1},ease:"none",'
            f'immediateRender:false}},{at_:.2f});')


def push(p, eid, d, s0=1.0, s1=1.04, ox=540, oy=760, at_=0):
    """Slow camera push (scale) around an SVG point; use on a wrapper group like {p}-cam."""
    lazy = ",immediateRender:false" if at_ else ""
    return (f'tl.fromTo("#{p}-{eid}",{{scale:{s0},svgOrigin:"{ox} {oy}"}},'
            f'{{scale:{s1},svgOrigin:"{ox} {oy}",duration:{d:.2f},ease:"sine.inOut"{lazy}}},{at_:.2f});')


def move(p, eid, at_, d, x=None, y=None, ease="sine.inOut"):
    """Tween to an absolute x/y offset. Put the transform on an inner group, never on the tweened element."""
    kv = ",".join(f"{k}:{v}" for k, v in (("x", x), ("y", y)) if v is not None)
    return f'tl.to("#{p}-{eid}",{{{kv},duration:{d:.2f},ease:"{ease}"}},{at_:.2f});'


def bob(p, eid, d, amp=8, period=2.4, at_=0):
    """Gentle float (yoyo) that ends on a whole cycle inside the scene. No repeat:-1 (render contract)."""
    n = max(1, int((d - at_) / (period / 2)))
    return f'tl.to("#{p}-{eid}",{{y:"+={amp}",duration:{period / 2},yoyo:true,repeat:{n - 1},ease:"sine.inOut"}},{at_:.2f});'


def show_now(p, eid):
    """Visible from the scene's frame 0 (hook banner on frame 0 of the video)."""
    return f'gsap.set("#{p}-{eid}",{{opacity:1}});'


# ---- text --------------------------------------------------------------------------------------------
def t(x, y, s, size=40, color=INK, w=800, anchor="middle", extra=""):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{w}" font-family="{FONT}" '
            f'text-anchor="{anchor}" {extra}>{s}</text>')


BRAND = t(540, 228, BRAND_TEXT, 28, DIM, 800, extra='letter-spacing="8"')


def banner(p, eid, x, y, w, h, s, size, fill=PRIMARY, color=GRAPH, rot=-4):
    """Tilted keyword plate, hidden until pop(). Keep it <= ~4 words and on screen >= 0.5 s + 0.3 s/word."""
    r = h * 0.2
    box = f'x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="{r:.0f}"'
    return (f'<g id="{p}-{eid}" opacity="0"><g transform="rotate({rot} {x} {y})">'
            f'<defs><clipPath id="{p}-{eid}-bc"><rect {box}/></clipPath></defs>'
            f'<rect x="{x - w / 2}" y="{y - h / 2 + 9}" width="{w}" height="{h}" rx="{r:.0f}" fill="#000" opacity="0.35"/>'
            f'<rect {box} fill="{fill}"/>'
            f'<g clip-path="url(#{p}-{eid}-bc)"><rect x="{x - w / 2}" y="{y + h / 2 - 12}" width="{w}" height="12" fill="#000" opacity="0.16"/>'
            f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="6" fill="#FFFFFF" opacity="0.18"/></g>'
            + t(x, y + size * 0.36, s, size, color, 900) + '</g></g>')


def pill(eid, x, y, s, size=40, color=ACCENT, fill=GRAPH, hidden=True):
    """Outlined label; width follows the text (0.7 em per character + padding). eid is the FULL id."""
    w = len(s) * size * 0.7 + 70
    o = ' opacity="0"' if hidden else ""
    return (f'<g id="{eid}"{o}><rect x="{x - w / 2:.0f}" y="{y - size * 0.95:.0f}" width="{w:.0f}" height="{size * 1.9:.0f}" '
            f'rx="{size * 0.95:.0f}" fill="{fill}" stroke="{color}" stroke-width="4"/>' + t(x, y + size * 0.36, s, size, color, 800) + '</g>')


# ---- backgrounds + finishing -------------------------------------------------------------------------
GRAIN = ('<defs><filter id="gr"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/>'
         '<feColorMatrix type="saturate" values="0"/></filter></defs>'
         f'<rect width="{W}" height="{H}" filter="url(#gr)"/>')


def bake_envs(here, envs, seed=0):
    """envs = {name: (fn(rnd, far_lights) -> (far_svg, mid_svg), backdrop_hex)}. Each is baked once to
    assets/bg/<name>-bg.png through depth.layers (blurred far/mid + lights); returns {name: <image>, "grain": <image>}.
    fn appends glow shapes (depth.bokeh, lit windows) to far_lights; ids inside fn use a 2-letter prefix."""
    out = {}
    for name, (fn, back) in envs.items():
        fl = []
        far, mid = fn(random.Random(len(name) + seed), fl)
        out[name] = depth.bake(here, f"{name}-bg", depth.layers(name[:2], far=far, far_lights="".join(fl), mid=mid,
                                                                graded=False, backdrop=back))
    out["grain"] = depth.bake(here, "grain", GRAIN)
    return out


def finish(p, bk, capband=False, top_op=0.92):
    """Top darkening band (keeps BRAND readable), optional caption band (busy backgrounds), grade, grain."""
    out = ""
    if capband:
        out += (f'<defs><linearGradient id="{p}-capb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070A" stop-opacity="0"/>'
                f'<stop offset="0.5" stop-color="#05070A" stop-opacity="0.55"/><stop offset="1" stop-color="#05070A" stop-opacity="0"/></linearGradient></defs>'
                f'<rect y="1110" width="{W}" height="220" fill="url(#{p}-capb)"/>')
    out += (f'<defs><linearGradient id="{p}-topb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#04060B" stop-opacity="{top_op}"/>'
            f'<stop offset="0.55" stop-color="#04060B" stop-opacity="{top_op * 0.75:.2f}"/><stop offset="1" stop-color="#04060B" stop-opacity="0"/></linearGradient></defs>'
            f'<rect width="{W}" height="330" fill="url(#{p}-topb)"/>')
    out += depth.grade(p, grain=False)
    if "grain" in bk:
        out += bk["grain"].replace("<image ", '<image opacity="0.06" style="mix-blend-mode:overlay" ')
    return out
