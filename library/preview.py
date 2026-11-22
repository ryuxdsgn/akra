"""Preview rendering for library items: every preview is a 1080x1920 frame rasterised by headless Chrome,
labelled with Pillow (ffmpeg has no drawtext) and saved downscaled to 540x960.

character: 3x2 grid of the acting poses neutral/point/present/think/surprise/happy.
pose set:  each pose drawn on three characters of the style (big sets: 1 character per cell, cycling the three).
env:       up to three variants side by side with safe_area as a dashed rectangle.

Poses are applied statically: the rig's own set_pose() GSAP JS is run in the page against the inlined gsap build,
so the still is exactly what `set_pose` produces in a render (frame 0)."""
import importlib.util
import json
import math
import os
import random
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from library.catalog import LibraryError, load_items
from library.lib import _costume, load_rig

W, H = 1080, 1920
OUT_W = 540
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"
GSAP_CACHE = Path.home() / ".cache" / "akra-library" / "gsap-3.15.0.min.js"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
CHAR_POSES = ("neutral", "point", "present", "think", "surprise", "happy")
BG = "#CFCAC2"
# Characters drawn first on pose-set sheets, per style: library/preview.json -> {"preferred": {"<style>": [ids]}}
# when the installation has one; otherwise any character of the style.
PREFERRED_FILE = Path(__file__).resolve().parent / "preview.json"


def _preferred(path=PREFERRED_FILE):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    pref = data.get("preferred") if isinstance(data, dict) else None
    return {k: tuple(v) for k, v in pref.items() if isinstance(v, list)} if isinstance(pref, dict) else {}


PREFERRED = _preferred()


def _gsap_source():
    if not GSAP_CACHE.is_file():
        GSAP_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(GSAP_URL, timeout=30) as r:
            GSAP_CACHE.write_bytes(r.read())
    return GSAP_CACHE.read_text(encoding="utf-8")


def _chrome_png(svg_body, js, png):
    """Rasterise <svg>(body) after running js (GSAP sets) in one headless Chrome process."""
    page = ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
            'svg{display:block}</style></head><body>'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg_body}</svg>'
            f'<script>{_gsap_source()}</script><script>{js}</script></body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "p.html"
        f.write_text(page, encoding="utf-8")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        f"--window-size={W},{H}", f"--screenshot={png}", "file://" + str(f)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)


def _finish(raw_png, labels, out):
    """Draw labels (x, y, text, size, anchor) at full size, then downscale to OUT_W and save."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(raw_png).convert("RGB")
    d = ImageDraw.Draw(im)
    for x, y, text, size, anchor in labels:
        font = ImageFont.truetype(FONT, size)
        d.text((x + 2, y + 2), text, font=font, fill=(255, 255, 255), anchor=anchor)
        d.text((x, y), text, font=font, fill=(24, 24, 28), anchor=anchor)
    im = im.resize((OUT_W, OUT_W * H // W), Image.LANCZOS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)
    return out


def _dress(rig, item, cid, x, y, s):
    L = rig.look(**item["base_look"])
    svg = rig.character(cid, x, y, s=s, look=L)
    if item.get("costume"):
        svg = _costume(rig, svg, cid, L, item["costume"])
    return svg, L


def _wants_chair(pose_name):
    return pose_name.startswith(("sit", "chair"))


def _pick_characters(items, style, n=3):
    chars = [i for i in items.values() if i["kind"] == "character" and i["style"] == style
             and i.get("public")]
    chars.sort(key=lambda i: (i["status"] != "vetted", bool(i.get("costume")), i["id"]))
    pref = [items[p] for p in PREFERRED.get(style, ()) if p in items and items[p]["style"] == style]
    out = pref[:n]  # a tree without the preferred items falls back to any character of the style
    for c in chars:
        if len(out) >= n:
            break
        if c not in out:
            out.append(c)
    if not out:
        out = [i for i in items.values() if i["kind"] == "character" and i["style"] == style][:n]
    if not out:
        raise LibraryError(f"no characters of style {style!r} to draw poses on")
    return out


def _character_sheet(item, rig):
    svg, js, labels = f'<rect width="{W}" height="{H}" fill="{BG}"/>', "", [(W // 2, 70, item["id"], 56, "mm")]
    cw, ch, top = W // 3, (H - 150) // 2, 150
    for i, name in enumerate(CHAR_POSES):
        col, row = i % 3, i // 3
        # characters face right and the point/present/happy arm reaches ~180 px past the body:
        # shift each column left and draw a little smaller so the right column's hand stays in frame
        cx, y0 = col * cw + cw // 2 - 60, top + row * ch
        cid = f"c{i}"
        body, L = _dress(rig, item, cid, cx, y0 + ch - 90, 1.0)
        svg += body
        js += rig.set_pose(cid, name, L)
        labels.append((cx + 60, y0 + ch - 40, name, 34, "mm"))
    return svg, js, labels


def _pose_sheet(item, rig, items, base):
    params_file = base / item["params_file"]
    params = json.loads(params_file.read_text(encoding="utf-8"))
    for n, p in params.items():
        p = dict(p)
        if "face" in p:
            p["face"] = tuple(p["face"])
        rig.POSES[n] = p
    names = list(params)
    chars = _pick_characters(items, item["style"])
    triple = len(names) <= 9
    cols = 3 if triple else 4 if len(names) <= 16 else 5
    rows = math.ceil(len(names) / cols)
    cw, ch, top = W // cols, (H - 150) // rows, 150
    s = min(0.8, (ch - 80) / 540) if not triple else min(0.55, (ch - 80) / 540)
    svg, js = f'<rect width="{W}" height="{H}" fill="{BG}"/>', ""
    labels = [(W // 2, 70, item["id"], 56, "mm")]
    for i, name in enumerate(names):
        col, row = i % cols, i // cols
        x0, y0 = col * cw, top + row * ch
        feet = y0 + ch - 50
        who = chars if triple else [chars[i % len(chars)]]
        for k, citem in enumerate(who):
            cx = x0 + cw * (k + 0.5) / len(who)
            cid = f"p{i}k{k}"
            body, L = _dress(rig, citem, cid, cx, feet, s)
            if _wants_chair(name) and hasattr(rig, "chair"):
                svg += rig.chair(cid, cx, feet, s, look=L)
            svg += body
            js += rig.set_pose(cid, name, L)
        labels.append((x0 + cw // 2, y0 + ch - 20, name, 26 if cols > 3 else 30, "mm"))
    return svg, js, labels


def _env_sheet(item, base):
    p = base / "envs" / item["module"]
    if not p.is_file():
        raise LibraryError(f"{item['id']}: module {item['module']!r} not found")
    spec = importlib.util.spec_from_file_location(f"_prev_env_{item['id']}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, item["function"])
    pw, ph, y0 = W // 3, H // 3, 640
    svg = f'<rect width="{W}" height="{H}" fill="#2A2A2E"/>'
    labels = [(W // 2, 70, item["id"], 56, "mm")]
    sx0, sy0, sx1, sy1 = item["safe_area"]
    for i, v in enumerate(item["variants"][:3]):
        fl = []
        far, mid = fn(random.Random(len(item["id"])), fl, v)
        backdrop = item.get("backdrops", {}).get(v, item["backdrop"])
        inner = (f'<rect width="{W}" height="{H}" fill="{backdrop}"/>{far}{mid}{"".join(fl)}'
                 f'<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" fill="none" stroke="#FF2D95" '
                 f'stroke-width="7" stroke-dasharray="26 16"/>')
        svg += (f'<svg x="{i * pw}" y="{y0}" width="{pw}" height="{ph}" viewBox="0 0 {W} {H}" overflow="hidden">'
                f'{inner}</svg>')
        labels.append((i * pw + pw // 2, y0 + ph + 40, v, 34, "mm"))
    return svg, "", labels


def render_preview(item, out, root=None, base=None):
    """Render the preview of one item to `out` (PNG, 540x960). `root` is the repo root; `base` is the library
    folder the item lives in (library/ by default, channels/_library/ for local items): pose params files and env
    modules are resolved against it."""
    root = Path(root) if root else Path(__file__).resolve().parent.parent
    base = Path(base) if base else root / "library"
    if item["kind"] == "env":
        svg, js, labels = _env_sheet(item, base)          # environments need no character rig
    elif item["kind"] == "character":
        rig = load_rig(item["style"])                     # RigNotIncluded (a LibraryError) without library/rig/
        svg, js, labels = _character_sheet(item, rig)
    elif item["kind"] == "pose":
        rig = load_rig(item["style"])
        local = root / "channels" / "_library"
        items = load_items(root / "library", local if local.is_dir() else None)
        svg, js, labels = _pose_sheet(item, rig, items, base)
    else:
        raise LibraryError(f"unknown kind {item['kind']!r}")
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.png"
        _chrome_png(svg, js, raw)
        return _finish(raw, labels, out)
