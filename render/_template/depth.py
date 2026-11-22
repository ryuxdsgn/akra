"""Cinematic depth for akra scenes: 4 layers with depth of field,
bloom, light beams, colour grade, vignette and grain. Shared like hf.py: fix it here, copy to episodes.

Layers, back to front (blur = SVG stdDeviation at 1080x1920):
  far   sky, skyline, street ............ blur 9   (+ bloom of its lights)
  mid   room / dashboard / table ........ blur 2.5 (+ bloom of its lights)
  hero  the object being explained ...... SHARP, lit by hero_light()
  near  pillars, leaves, frame edges .... blur 18, dark
Diagrams, arrows and labels go on top of everything, sharp.

Two ways to use it inside a scene function sNN(p, d, shot):
  live : svg = layers(p, far=..., mid=..., hero=..., near=..., far_lights=..., mid_lights=...)
  baked: bg   = bake(HERE, f"{p}-bg", layers(p, far=..., mid=..., graded=False))   # behind the hero, PNG once
         near = bake(HERE, f"{p}-near", layers(p, near=..., graded=False))          # in front, transparent PNG
         svg  = bg + defs(p) + hero_svg + near + grade(p) + diagram_svg
Bake whatever does not move: SVG blur is recomputed every frame and slows the render. Animate only the
hero, diagrams and small parallax groups live.
"""
import hashlib
import os
import subprocess
import tempfile

W, H = 1080, 1920
BLUR_FAR, BLUR_MID, BLUR_NEAR, BLUR_BLOOM = 9, 2.5, 18, 26
WARM_LIGHT, COOL_LIGHT = "#FFD9A0", "#7FE0F5"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def defs(p):
    """Filters + gradients, ids prefixed with the scene id p."""
    return (f'<defs>'
            f'<filter id="{p}-dofFar" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="{BLUR_FAR}"/></filter>'
            f'<filter id="{p}-dofMid" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="{BLUR_MID}"/></filter>'
            f'<filter id="{p}-dofNear" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{BLUR_NEAR}"/></filter>'
            f'<filter id="{p}-bloom" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{BLUR_BLOOM}"/></filter>'
            f'<filter id="{p}-beam" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="30"/></filter>'
            f'<filter id="{p}-soft"><feGaussianBlur stdDeviation="6"/></filter>'
            f'<filter id="{p}-shadow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="22"/></filter>'
            f'<filter id="{p}-grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/>'
            f'<feColorMatrix type="saturate" values="0"/></filter>'
            f'<linearGradient id="{p}-beamG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{WARM_LIGHT}" stop-opacity="0.5"/>'
            f'<stop offset="1" stop-color="{WARM_LIGHT}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="{p}-grade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2A3A8A" stop-opacity="0.25"/>'
            f'<stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#FF9A50" stop-opacity="0.12"/></linearGradient>'
            f'<radialGradient id="{p}-vig" cx="0.5" cy="0.6" r="0.75"><stop offset="0.55" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity="0.65"/></radialGradient>'
            f'</defs>')


def beam(p, x0, x1, y0, x2, x3, y1, opacity=0.5):
    """Soft light shaft: top edge x0..x1 at y0, bottom edge x2..x3 at y1 (warm, screen-blended)."""
    return (f'<path d="M {x0} {y0} L {x1} {y0} L {x3} {y1} L {x2} {y1} Z" fill="url(#{p}-beamG)" opacity="{opacity}" '
            f'filter="url(#{p}-beam)" style="mix-blend-mode:screen"/>')


def bokeh(cx, cy, r, color, opacity=0.35):
    """Out-of-focus light disc (put in far_lights so it also blooms)."""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{opacity:.2f}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="3" opacity="0.45"/>')


def grade(p, grain=True):
    """Final look: cool top / warm bottom grade, vignette, film grain."""
    g = (f'<rect width="{W}" height="{H}" fill="url(#{p}-grade)" style="mix-blend-mode:soft-light"/>'
         f'<rect width="{W}" height="{H}" fill="url(#{p}-vig)"/>')
    if grain:
        g += f'<rect width="{W}" height="{H}" filter="url(#{p}-grain)" opacity="0.06" style="mix-blend-mode:overlay"/>'
    return g


def layers(p, far="", mid="", hero="", near="", far_lights="", mid_lights="", beams="", graded=True, backdrop="#141B2D"):
    """Compose the 4 depth layers. *_lights = bright shapes (windows, lamps, screens): drawn blurred with
    their layer AND again as bloom. Include defs(p) once per scene: this function does.
    backdrop: solid colour under the far layer so blurred frame edges do not fade to transparent."""
    out = defs(p)
    if far or far_lights:
        out += f'<rect width="{W}" height="{H}" fill="{backdrop}"/>'
        out += f'<g filter="url(#{p}-dofFar)">{far}{far_lights}</g>'
        if far_lights:
            out += f'<g filter="url(#{p}-bloom)" style="mix-blend-mode:screen" opacity="0.9">{far_lights}</g>'
    out += beams
    if mid or mid_lights:
        out += f'<g filter="url(#{p}-dofMid)">{mid}{mid_lights}</g>'
        if mid_lights:
            out += f'<g filter="url(#{p}-bloom)" style="mix-blend-mode:screen" opacity="0.7">{mid_lights}</g>'
    out += hero
    if near:
        out += f'<g filter="url(#{p}-dofNear)">{near}</g>'
    if graded:
        out += grade(p)
    return out


def hero_light(p, eid, d, box, key=(0.25, 0.15), rim=(0.95, 0.75), spec=None):
    """2.5D lighting for the hero shape `d` (SVG path) with bounding box (x, y, w, h):
    warm key light, cool rim light, ambient occlusion at the bottom, optional specular (cx, cy, rx, ry).
    Draw the base fill (radial gradient) first, then this on top. Needs defs(p) in the scene."""
    x, y, w, h = box
    gid = f"{p}-{eid}"
    out = (f'<defs><clipPath id="{gid}-clip"><path d="{d}"/></clipPath>'
           f'<radialGradient id="{gid}-key" cx="{key[0]}" cy="{key[1]}" r="0.55"><stop offset="0" stop-color="{WARM_LIGHT}" stop-opacity="0.55"/>'
           f'<stop offset="1" stop-color="{WARM_LIGHT}" stop-opacity="0"/></radialGradient>'
           f'<radialGradient id="{gid}-rim" cx="{rim[0]}" cy="{rim[1]}" r="0.45"><stop offset="0" stop-color="{COOL_LIGHT}" stop-opacity="0.6"/>'
           f'<stop offset="1" stop-color="{COOL_LIGHT}" stop-opacity="0"/></radialGradient>'
           f'<linearGradient id="{gid}-ao" x1="0" y1="0" x2="0" y2="1"><stop offset="0.6" stop-color="#000" stop-opacity="0"/>'
           f'<stop offset="1" stop-color="#000" stop-opacity="0.35"/></linearGradient></defs>'
           f'<g clip-path="url(#{gid}-clip)">'
           + "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{gid}-{k})"/>' for k in ("key", "rim", "ao"))
           + '</g>')
    if spec:
        cx, cy, rx, ry = spec
        out += f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#FFFFFF" opacity="0.8" filter="url(#{p}-soft)"/>'
    return out


def cast_shadow(p, cx, cy, rx, ry, opacity=0.55):
    """Soft contact shadow under the hero."""
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#000" opacity="{opacity}" filter="url(#{p}-shadow)"/>'


def bake(here, name, svg_body):
    """Render static layers once to assets/bg/<name>.png (transparent where nothing is drawn; cached by content
    hash) and return an <image> tag.
    Re-renders only when the drawing changes. Needs Google Chrome (set CHROME=... elsewhere)."""
    out_dir = os.path.join(here, "assets", "bg")
    os.makedirs(out_dir, exist_ok=True)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg_body}</svg>'
    digest = hashlib.sha1(svg.encode()).hexdigest()[:10]
    png = os.path.join(out_dir, f"{name}.png")
    stamp = png + ".hash"
    if not (os.path.exists(png) and os.path.exists(stamp) and open(stamp).read() == digest):
        with tempfile.TemporaryDirectory() as tmp:
            page = os.path.join(tmp, "bg.html")
            open(page, "w").write('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;'
                                  'background:transparent}svg{display:block}</style></head><body>' + svg + '</body></html>')
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            "--default-background-color=00000000",
                            f"--window-size={W},{H}", f"--screenshot={png}", "file://" + page],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        open(stamp, "w").write(digest)
        print(f"baked assets/bg/{name}.png")
    return f'<image href="assets/bg/{name}.png" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none"/>'


# ---- realism helpers -----------------------------------------------------------------------------------
# Rule of thumb: draw the REAL object first (materials, wear, small parts), lay the explanation on top
# (overlay, arrows, labels). A viewer should name the object in 1 s without any label.

MATERIALS = {
    #  name       stops (offset, colour) across the object, left -> right (or top -> bottom with vertical=True)
    "steel":    [(0, "#5A606C"), (0.18, "#C9CED6"), (0.32, "#7D838F"), (0.7, "#A9AEB8"), (1, "#4A4F5A")],
    "chrome":   [(0, "#2B2F38"), (0.2, "#F4F6FA"), (0.35, "#5C626E"), (0.6, "#DADDE3"), (1, "#30343C")],
    "ceramic":  [(0, "#8A8C96"), (0.35, "#F2EDE4"), (0.8, "#C9C4BA"), (1, "#6E707A")],
    "plastic":  [(0, "#2A2E36"), (0.3, "#4A505C"), (0.55, "#3A3F4A"), (1, "#1E2128")],
    "glass":    [(0, "#9FD8F0"), (0.4, "#E8F7FF"), (0.6, "#7FC4E0"), (1, "#5AA8C8")],
    "wood":     [(0, "#6B4428"), (0.4, "#A06A3E"), (0.7, "#8A5A34"), (1, "#5A3820")],
    "rubber":   [(0, "#141518"), (0.5, "#2A2C31"), (1, "#101114")],
}


def material(p, eid, kind="steel", vertical=False, stops=None):
    """Linear gradient id `{p}-{eid}` for a real material (MATERIALS or custom stops). Returns (defs, url)."""
    st = stops or MATERIALS[kind]
    x2, y2 = ("0", "1") if vertical else ("1", "0")
    g = (f'<defs><linearGradient id="{p}-{eid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
         + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in st) + '</linearGradient></defs>')
    return g, f"url(#{p}-{eid})"


def sheen(p, eid, d, box, width=0.08, opacity=0.5, angle=12):
    """Glossy highlight band clipped to the hero shape `d` (box = x, y, w, h). It starts left of the shape;
    tween `#{p}-{eid}-hl` x (e.g. gsap.to(..., {x: w*1.3})) to sell turning, sliding or a camera move."""
    x, y, w, h = box
    bw = max(8, w * width)
    return (f'<defs><clipPath id="{p}-{eid}-sc"><path d="{d}"/></clipPath></defs>'
            f'<g clip-path="url(#{p}-{eid}-sc)"><rect id="{p}-{eid}-hl" x="{x - bw * 2:.0f}" y="{y - h * 0.2:.0f}" '
            f'width="{bw:.0f}" height="{h * 1.4:.0f}" fill="#FFFFFF" opacity="{opacity}" '
            f'transform="rotate({angle} {x:.0f} {y + h / 2:.0f})" filter="url(#{p}-soft)"/></g>')


def texture(p, eid, d, freq=0.8, opacity=0.12, seed=7):
    """Fine surface noise (brushed metal, paper, food crumb) clipped to `d`. Static: bake it with the hero
    if the hero does not move, otherwise keep it small (the filter is recomputed every frame)."""
    return (f'<defs><filter id="{p}-{eid}-tx"><feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="2" seed="{seed}"/>'
            f'<feColorMatrix type="saturate" values="0"/></filter><clipPath id="{p}-{eid}-tc"><path d="{d}"/></clipPath></defs>'
            f'<g clip-path="url(#{p}-{eid}-tc)"><rect x="0" y="0" width="{W}" height="{H}" filter="url(#{p}-{eid}-tx)" '
            f'opacity="{opacity}" style="mix-blend-mode:overlay"/></g>')


def soft_steam(p, eid, x, y, h=150, color="#F2EDE4"):
    """Blurred, translucent steam wisp rising from (x, y); starts hidden (opacity 0): fade + drift it in GSAP."""
    d = f"M {x} {y} q -34 {-h * 0.25:.0f} 0 {-h * 0.5:.0f} q 34 {-h * 0.25:.0f} 0 {-h * 0.5:.0f}"
    # own filter region in user space: the default one hugs the thin path and cuts the blur off at the sides
    return (f'<defs><filter id="{p}-{eid}-f" filterUnits="userSpaceOnUse" x="{x - 120}" y="{y - h - 80:.0f}" width="240" '
            f'height="{h + 160:.0f}"><feGaussianBlur stdDeviation="6"/></filter></defs>'
            f'<g id="{p}-{eid}" opacity="0" filter="url(#{p}-{eid}-f)"><path d="{d}" fill="none" stroke="{color}" stroke-width="34" '
            f'stroke-linecap="round" opacity="0.35"/><path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="12" '
            f'stroke-linecap="round" opacity="0.5"/></g>')


def data_overlay(p, eid, d, bands, base="#3A6EA8", base_opacity=0.35, band_opacity=0.55):
    """Explain ON the real object: a soft tinted overlay (thermal view, pressure, flow) clipped to the hero
    shape `d`, so the object stays visible underneath. bands = [(svg_shape, colour), ...]; each band gets
    id `{p}-{eid}-b<i>` (opacity 0) so GSAP can light them one by one. Base tint id `{p}-{eid}-base`."""
    out = (f'<defs><clipPath id="{p}-{eid}-oc"><path d="{d}"/></clipPath></defs>'
           f'<g clip-path="url(#{p}-{eid}-oc)" style="mix-blend-mode:screen">'
           f'<path id="{p}-{eid}-base" d="{d}" fill="{base}" opacity="{base_opacity}"/>')
    for i, (shape, colour) in enumerate(bands):
        shape = shape.replace("/>", f' fill="{colour}"/>', 1) if "fill=" not in shape else shape
        out += f'<g id="{p}-{eid}-b{i}" opacity="0" filter="url(#{p}-soft)"><g opacity="{band_opacity}">{shape}</g></g>'
    return out + '</g>'


def perspective(points, vx=540, vy=-600, depth_=0.12):
    """3/4 view helper: pull points (x, y) of the far edge toward a vanishing point (vx, vy).
    Use it for tops of boxes, trays, tables: far = perspective(near_edge_points)."""
    return [(x + (vx - x) * depth_, y + (vy - y) * depth_) for x, y in points]


def plate(p, eid, x, y, w, h, fill, rot=0, radius=0.2, drop=9):
    """Rounded badge/banner plate (centre x, y) with drop shadow and bevel strips. Every strip is clipped to
    the rounded shape, so nothing pokes past the corners (a square shadow strip under a rounded banner
    would show). The drop shadow is the same rounded rect, offset down. Text goes on top by the caller."""
    r = h * radius
    box = f'x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="{r:.0f}"'
    return (f'<g transform="rotate({rot} {x} {y})"><defs><clipPath id="{p}-{eid}-pc"><rect {box}/></clipPath></defs>'
            f'<rect x="{x-w/2:.0f}" y="{y-h/2+drop:.0f}" width="{w}" height="{h}" rx="{r:.0f}" fill="#000" opacity="0.35"/>'
            f'<rect {box} fill="{fill}"/><g clip-path="url(#{p}-{eid}-pc)">'
            f'<rect x="{x-w/2:.0f}" y="{y+h/2-12:.0f}" width="{w}" height="12" fill="#000" opacity="0.16"/>'
            f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="6" fill="#FFFFFF" opacity="0.18"/></g></g>')
