"""Shared HyperFrames builder for akra episodes.

Episode-specific code (drawings, scene timelines, SFX cues) lives in build.py.
Everything here is the same for every episode: brand, SVG helpers, scene wrapper,
word-by-word captions, voiceover + SFX tracks and the root index.html.
"""
import html
import json
import os
import re
import wave

import channelcfg

W, H = 1080, 1920

# ---- brand (channels/<id>/channel.json -> brand, see channelcfg.py) ------------------
CFG = channelcfg.settings(os.path.dirname(os.path.abspath(__file__)))
_C = CFG["colors"]
GRAPH = _C["bg"]; INK = _C["ink"]; MUT = _C["muted"]; DIM = _C["dim"]
PRIMARY = _C["primary"]; BRL = _C["primary_light"]; ACCENT = _C["accent"]
BRASS, CYAN = PRIMARY, ACCENT      # older names of the same two colours
HOUSING = _C["housing"]; EDGE = _C["edge"]; PLUG = "#343B42"; BORE = "#15181B"
FONT = CFG["font"]
LANG = CFG["language"]

# ---- layout ------------------------------------------------------------------------
# Text safe band 168-1330 px (YouTube UI covers the right edge and the bottom ~20 %).
BRAND_TOP = 200          # channel tag
ART_TOP, ART_BOTTOM = 250, 1170   # diagram area
CAP_TOP = CFG["cap_top"]  # captions: one line, 70 px, max ~20 characters (default 1185)
CAP_MAX_CHARS = CFG["cap_max_chars"]
SPEAKER_COLORS = CFG["speaker_colors"]   # transcript "speaker" -> caption colour (cast voiceovers)


def esc(s):
    return html.escape(s, quote=True)


# ---- SVG helpers -------------------------------------------------------------------

def text(x, y, s, size=38, color=INK, weight=800, anchor="middle", eid=None, spacing=0):
    a = f' id="{eid}"' if eid else ""
    return (f'<text{a} x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}" font-family="{FONT}">{esc(s)}</text>')


def label(p, eid, x, y, s, lx=None, ly=None, color=INK, size=38, anchor="middle"):
    """Hidden label (+ optional accent-colour leader line to lx,ly). Reveal with show()."""
    lead = ""
    if lx is not None:
        lead = f'<line x1="{x}" y1="{y+12}" x2="{lx}" y2="{ly}" stroke="{ACCENT}" stroke-width="4"/>'
    return f'<g id="{p}-{eid}" opacity="0">{lead}{text(x, y, s, size, color, anchor=anchor)}</g>'


def show(p, eid, t, d=0.3):
    return f'tl.fromTo("#{p}-{eid}",{{opacity:0}},{{opacity:1,duration:{d}}},{t:.2f});'


def hide(p, eids, t, d=0.3):
    ids = ",".join(f'"#{p}-{e}"' for e in eids)
    return f'tl.to([{ids}],{{opacity:0,duration:{d}}},{t:.2f});'


def pulse(sel, t, attr="fill", base=PRIMARY, hi=ACCENT, d=0.18):
    """Flash an SVG attribute to the accent colour and back (e.g. 'this part')."""
    return f'tl.fromTo("{sel}",{{{attr}:"{base}"}},{{{attr}:"{hi}",duration:{d},yoyo:true,repeat:1}},{t:.2f});'


def spring(x, y0, y1, eid, coils=7, amp=20):
    pts = []
    for k in range(coils * 2 + 1):
        yy = y0 + (y1 - y0) * k / (coils * 2)
        xx = x if k in (0, coils * 2) else (x - amp if k % 2 else x + amp)
        pts.append(f"{xx:.0f},{yy:.1f}")
    return (f'<g id="{eid}"><polyline points="{" ".join(pts)}" fill="none" stroke="{MUT}" '
            f'stroke-width="5" stroke-linejoin="round"/></g>')


def arrow_down(eid, x, y0, y1, color=INK):
    return (f'<g id="{eid}" opacity="0"><line x1="{x}" y1="{y0}" x2="{x}" y2="{y1-16}" stroke="{color}" stroke-width="7"/>'
            f'<path d="M {x-16} {y1-26} L {x} {y1} L {x+16} {y1-26} Z" fill="{color}"/></g>')


# ---- scene wrapper -------------------------------------------------------------------

def scene_file(sid, svg, js, dur, extra=""):
    """One sub-composition. Timeline times are LOCAL to the scene (0 = scene start).
    extra: optional HTML under the SVG (a three3d canvas + its module script); "" keeps the old output."""
    extra = f'<div id="{sid}-x" style="position:absolute;inset:0;">\n{extra}\n</div>\n' if extra else ""
    return f'''<template>
<style>
#root {{ position:absolute; inset:0; }}
#root svg {{ position:absolute; inset:0; }}
</style>
<div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
{extra}<svg id="{sid}-svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" data-layout-allow-overlap>
{svg}
</svg>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{js}
tl.set({{}}, {{}}, {dur:.2f});
window.__timelines["{sid}"] = tl;
</script>
</template>
'''


def storyboard_scene(p, shot, n):
    """Placeholder for a shot without a drawing yet: shows the storyboard text (animatic)."""
    words = shot.get("prompt", "").split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 34:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    body = "".join(text(540, 640 + i * 52, ln, 36, MUT, 600) for i, ln in enumerate(lines[:10]))
    svg = (f'<g id="{p}-box"><rect x="90" y="420" width="900" height="700" rx="28" fill="{HOUSING}" stroke="{EDGE}" stroke-width="4" stroke-dasharray="18 12"/>'
           + text(540, 540, f"SHOT {n:02d} · {shot.get('type', 'diagram').upper()}", 44, BRL)
           + body + "</g>")
    return svg, f'tl.fromTo("#{p}-box",{{opacity:0}},{{opacity:1,duration:0.3}},0);'


# ---- words -------------------------------------------------------------------------------

def load_words(here, script, shots, total):
    """Word timings from assets/transcript.json (hyperframes transcribe).
    Without a voiceover yet, spread the script words evenly over each shot's narration."""
    path = os.path.join(here, "assets", "transcript.json")
    if os.path.exists(path):
        words = json.load(open(path))
        return [w for w in words if re.search(r"[A-Za-z0-9]", w["text"])]
    print("! no assets/transcript.json: captions use estimated timings (animatic only)")
    out = []
    for s in shots:
        toks = s.get("narration", "").split()
        if not toks:
            continue
        step = (s["t_end"] - s["t_start"]) / len(toks)
        for k, t in enumerate(toks):
            a = s["t_start"] + k * step
            out.append({"text": t, "start": round(a, 2), "end": round(a + step * 0.9, 2)})
    if len(out) != len(script.split()):
        # narration fields do not add up to the script: fall back to the whole script
        toks = script.split(); step = total / len(toks)
        out = [{"text": t, "start": round(k * step, 2), "end": round((k + 0.9) * step, 2)} for k, t in enumerate(toks)]
    return out


# ---- captions -------------------------------------------------------------------------

def caption_groups(words, script):
    """Script text (not whisper text) matched to timings by word POSITION."""
    tokens = script.split()
    assert len(tokens) == len(words), f"script has {len(tokens)} words, transcript {len(words)}: fix the transcript"
    groups, cur = [], []
    for i, (tok, w) in enumerate(zip(tokens, words)):
        cur.append((tok, w["start"], w["end"], w.get("speaker")))
        nxt = words[i + 1] if i + 1 < len(words) else None
        too_long = nxt is not None and len(" ".join(c[0] for c in cur) + " " + tokens[i + 1]) > CAP_MAX_CHARS
        if (nxt is None or tok[-1] in ".,?!" or len(cur) >= 4 or too_long
                or (nxt["start"] - w["end"]) >= 0.15 or nxt.get("speaker") != w.get("speaker")):
            groups.append(cur); cur = []
    return groups


def captions_file(groups, total):
    items, js = [], []
    for gi, g in enumerate(groups):
        start = max(0.15, g[0][1] - 0.05)
        if gi > 0:                                   # never two groups on screen at once
            start = max(start, groups[gi - 1][-1][2])
        end = max(groups[gi + 1][0][1] - 0.05, g[-1][2]) if gi + 1 < len(groups) else min(total - 0.3, g[-1][2] + 0.4)  # last caption clears before the loop frame
        end = min(end, total)
        base = SPEAKER_COLORS.get(g[0][3] or "", INK)
        hot = ACCENT if base == INK else INK        # ink words light up in the accent colour, speaker-coloured words in ink
        spans = " ".join(f'<span id="cw{gi}-{k}" class="w" style="color:{base}">{esc(c[0])}</span>' for k, c in enumerate(g))
        items.append(f'<div id="cg{gi}" class="clip cap" data-start="{start:.2f}" data-duration="{end-start:.2f}">'
                     f'<div id="ci{gi}" class="cap-in">{spans}</div></div>')
        js.append(f'tl.fromTo("#ci{gi}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.12,ease:"power2.out"}},{start:.2f});')
        for k, c in enumerate(g):
            ws, we = c[1], c[2]
            js.append(f'tl.set("#cw{gi}-{k}",{{color:"{hot}"}},{max(ws, start):.2f});')
            js.append(f'tl.set("#cw{gi}-{k}",{{color:"{base}"}},{min(we, end):.2f});')
    return f'''<template>
<style>
#root {{ position:absolute; inset:0; }}
.cap {{ position:absolute; left:0; top:{CAP_TOP}px; width:{W}px; height:140px; }}
.cap-in {{ width:100%; text-align:center; font-family:"{FONT}"; font-weight:800; font-size:70px; line-height:1.15;
  color:{INK}; padding:0 90px; text-shadow:0 4px 0 #0B0D0F, 0 0 18px rgba(0,0,0,0.65); }}
.w {{ color:{INK}; }}
</style>
<div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
{chr(10).join(items)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["captions"] = tl;
</script>
</template>
'''


# ---- audio -----------------------------------------------------------------------------

def wav_len(here, name):
    with wave.open(os.path.join(here, "assets", "sfx", name + ".wav")) as w:
        return w.getnframes() / w.getframerate()


def sfx_tags(here, cues, total):
    """cues: (file name in assets/sfx without .wav, absolute start s, volume 0-1)."""
    return "\n".join(
        f'<audio id="fx{k:02d}" class="clip" src="assets/sfx/{f}.wav" data-start="{t:.2f}" '
        f'data-duration="{min(wav_len(here, f), total - t):.2f}" data-track-index="{4 + k % 3}" data-volume="{v}"></audio>'
        for k, (f, t, v) in enumerate(cues))


def vo_tag(here, total):
    if os.path.exists(os.path.join(here, "assets", "voiceover_norm.wav")):
        return (f'<audio id="vo" class="clip" src="assets/voiceover_norm.wav" data-start="0" '
                f'data-duration="{total}" data-track-index="3" data-volume="1"></audio>')
    print("! no assets/voiceover_norm.wav: building without voiceover")
    return ""


def music_tag(here, total, volume=0.1):
    """Background music: assets/music.mp3 (YouTube Audio Library or licensed), ~-20 dB under the voice."""
    for f in ("music.mp3", "music.wav"):
        if os.path.exists(os.path.join(here, "assets", f)):
            return (f'<audio id="music" class="clip" src="assets/{f}" data-start="0" data-duration="{total}" '
                    f'data-track-index="7" data-volume="{volume}"></audio>')
    print("! no assets/music.mp3: building without music")
    return ""


# ---- root ---------------------------------------------------------------------------------

def index_html(brand, total, hosts, extra_audio):
    return f'''<!doctype html>
<html lang="{LANG}"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width={W}, height={H}"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{GRAPH};font-family:"{FONT}",sans-serif;}}
#bg{{position:absolute;inset:0;background:{GRAPH};
  background-image:linear-gradient({INK}0A 1px,transparent 1px),linear-gradient(90deg,{INK}0A 1px,transparent 1px);background-size:60px 60px;}}
#brand{{position:absolute;left:0;top:{BRAND_TOP}px;width:{W}px;text-align:center;font-weight:800;font-size:28px;letter-spacing:8px;color:{DIM};z-index:1;}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
<div id="bg" class="clip" data-start="0" data-duration="{total}" data-track-index="0" style="z-index:1"></div>
<div id="brand" class="clip" data-start="0" data-duration="{total}" data-track-index="0">{esc(brand)}</div>
{chr(10).join(hosts)}
<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{total}" data-track-index="2" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:3"></div>
{extra_audio}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.set({{}}, {{}}, {total});
window.__timelines["main"] = tl;
</script></body></html>
'''


def build(here, ep_path, scenes, sfx_cues, brand, xfade=0.0):
    """scenes: list of fn(p, d, shot) -> (svg, js) or (svg, js, html), one per shot in time order; None = storyboard
    placeholder. The optional html (e.g. a three3d canvas) is drawn under the scene's SVG.
    xfade > 0: soft cut. Each scene (but the last) holds its final frame `xfade` s longer and the next one fades in on
    top of it, so a cut between two shots with the same framing does not jump. The first scene never fades in (loop)."""
    ep = json.load(open(ep_path))
    shots = sorted(ep["shots"], key=lambda s: s["t_start"])
    total = round(max(ep.get("vo_duration") or 0, shots[-1]["t_end"]) + 0.1, 2)
    scenes = list(scenes) + [None] * (len(shots) - len(scenes))
    assert len(scenes) == len(shots), f"{len(scenes)} scene functions for {len(shots)} shots"

    comp = os.path.join(here, "compositions")
    os.makedirs(comp, exist_ok=True)
    for f in os.listdir(comp):                     # drop scenes left over from an older storyboard
        if re.fullmatch(r"s\d\d\.html", f):
            os.remove(os.path.join(comp, f))
    hosts = []
    for i, (shot, fn) in enumerate(zip(shots, scenes)):
        sid = f"s{i+1:02d}"; t0 = shot["t_start"]; dur = round(shot["t_end"] - t0, 2)
        if i == len(shots) - 1:                    # last scene holds to the very end (no blank tail frame)
            dur = round(total - t0, 2)
        out = fn(sid, dur, shot) if fn else storyboard_scene(sid, shot, i + 1)
        svg, js, extra = (tuple(out) + ("",))[:3]
        hold = dur
        if xfade > 0 and i > 0:
            tgt = f"#{sid}-svg,#{sid}-x" if extra else f"#{sid}-svg"
            js = (f'tl.fromTo("{tgt}",{{opacity:0}},{{opacity:1,duration:{xfade:.2f},ease:"none",immediateRender:true}},0);' + js)
        if xfade > 0 and i < len(shots) - 1:
            hold = round(dur + xfade, 2)
        open(os.path.join(comp, f"{sid}.html"), "w").write(scene_file(sid, svg, js, hold, extra))
        dur = hold
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{t0:.2f}" data-duration="{dur:.2f}" data-track-index="1" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}" style="z-index:2"></div>')

    words = load_words(here, ep["script"], shots, total)
    groups = caption_groups(words, ep["script"])
    open(os.path.join(comp, "captions.html"), "w").write(captions_file(groups, total))
    audio = vo_tag(here, total) + "\n" + music_tag(here, total) + "\n" + sfx_tags(here, sfx_cues, total)
    open(os.path.join(here, "index.html"), "w").write(index_html(brand, total, hosts, audio))
    drawn = sum(1 for f in scenes if f)
    print(f"wrote index.html: {len(shots)} shots ({drawn} drawn, {len(shots)-drawn} storyboard), "
          f"{len(groups)} caption groups, {len(sfx_cues)} sfx, {total}s")
