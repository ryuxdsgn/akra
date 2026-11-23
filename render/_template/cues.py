"""Visual cues: the information drawn over a cartoon scene, placed from rig joints and checked before render.

Names (use these words in scripts, shot lists and reviews):
  motion arrow  curved arrow with a white halo showing which way a body part moves, anchored at a joint
  mark          check (correct) or cross (wrong) disc, sitting next to the body part it judges, with a pointer
  chip          white pill with a coloured outline: exercise name, sets x reps, a safety line
  meter         row of rep icons that fill on the counts
The calendar, brand badge and captions are not cues; they have fixed places of their own.

Layout:
  INFO column   chips and the meter stack in one left-aligned column under the brand (lanes, top to bottom), so the
                information always appears in the same place and never sits on a face.
  arrows/marks  live next to the body: arrow_at() starts near a joint and sweeps the way it moves; mark_at() sits
                beside the middle of a limb segment (two joints) with a pointer to it.

Every cue is registered on a Board with its box and time window. Board.check() reports cues that cover a face,
leave the safe area, touch the caption band, overlap another cue on screen at the same time, sit too far from
their joint, or are too small to read. Board.assert_clean() stops the build on any of them.

    board = cues.Board(faces=[...], caption=(y0, y1))
    svg += board.arrow_at("s06-ap", eid_start, ankle, toward=(-1, 0.6), t0=1.2, t1=2.0)
    ...
    board.assert_clean()
"""
import math

import scenekit as sk

W, H = 1080, 1920
SAFE = (40, 150, 1000, 1640)          # x0, y0, x1, y1: Shorts UI covers the right edge and the bottom
INFO_X = 75                           # left edge of the info column
LANES = {"meter": 430, 1: 600, 2: 700, 3: 800}   # lane centre y; a lane holds one chip (or the meter)
ARROW_MIN = 120                       # px, shortest readable motion arrow (start to tip)
MARK_MAX_GAP = 150                    # px, farthest a mark may sit from the limb it judges
INKD, MINT, ORANGE, SOFT_RED = "#3B2A20", sk.ORANGE, sk.BRASS, "#E25D4F"
WHITE = "#FFFFFF"


def _f(v):
    return f"{v:.0f}"


def chip_width(text, size):
    return len(text) * size * 0.62 + 80


def overlaps(a, b, pad=0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def circle_box(cx, cy, r):
    return (cx - r, cy - r, cx + r, cy + r)


def box_hits_circle(b, cx, cy, r):
    nx, ny = min(max(cx, b[0]), b[2]), min(max(cy, b[1]), b[3])
    return (nx - cx) ** 2 + (ny - cy) ** 2 < r * r


def seg_dist(p, a, b):
    ax, ay, bx, by = *a, *b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


# ---- drawings (hidden until animated in) --------------------------------------------------------------------------
def chip_svg(eid, x, y, text, size=40, color=ORANGE, hidden=True, align="left"):
    """White pill, coloured outline, dark text. x is the left edge (align=left) or the centre (align=middle)."""
    w = chip_width(text, size)
    x0 = x if align == "left" else x - w / 2
    h = size * 1.9
    o = ' opacity="0"' if hidden else ""
    return (f'<g id="{eid}" class="ak"{o}><rect x="{_f(x0)}" y="{_f(y - h / 2 + 8)}" width="{_f(w)}" height="{_f(h)}" rx="{_f(h / 2)}" '
            f'fill="#000" opacity="0.16"/><rect x="{_f(x0)}" y="{_f(y - h / 2)}" width="{_f(w)}" height="{_f(h)}" rx="{_f(h / 2)}" '
            f'fill="{WHITE}" stroke="{color}" stroke-width="6"/>' + sk.t(x0 + w / 2, y + size * 0.36, text, size, INKD, 800)
            + '</g>'), (x0, y - h / 2, x0 + w, y + h / 2)


def arrow_svg(eid, p0, c, p1, width=12):
    """Curved motion arrow: white halo, mint body (#eid-l0 halo, #eid-l body, drawn on), head at p1."""
    tx, ty = p1[0] - c[0], p1[1] - c[1]
    ln = math.hypot(tx, ty) or 1
    tx, ty = tx / ln, ty / ln
    nx, ny = -ty, tx
    hl, hw = width * 2.4, width * 1.9
    base = (p1[0] - tx * hl, p1[1] - ty * hl)
    d = f"M {_f(p0[0])} {_f(p0[1])} Q {_f(c[0])} {_f(c[1])} {_f(base[0])} {_f(base[1])}"
    head = (f"M {_f(p1[0] + tx * 6)} {_f(p1[1] + ty * 6)} L {_f(base[0] + nx * hw)} {_f(base[1] + ny * hw)} "
            f"L {_f(base[0] - nx * hw)} {_f(base[1] - ny * hw)} Z")
    return (f'<g id="{eid}" opacity="0"><path id="{eid}-l0" d="{d}" fill="none" stroke="{WHITE}" stroke-width="{width * 2}" '
            f'stroke-linecap="round"/><path d="{head}" fill="{WHITE}" stroke="{WHITE}" stroke-width="{width * 0.9:.0f}" stroke-linejoin="round"/>'
            f'<path id="{eid}-l" d="{d}" fill="none" stroke="{MINT}" stroke-width="{width}" stroke-linecap="round"/>'
            f'<path d="{head}" fill="{MINT}" stroke="{MINT}" stroke-width="2" stroke-linejoin="round"/></g>')


def mark_svg(eid, x, y, ok, r, tip, hidden=True):
    """Check/cross disc at (x, y) with a pointer toward `tip` (the limb it judges)."""
    col = MINT if ok else SOFT_RED
    a = math.atan2(tip[1] - y, tip[0] - x)
    px, py = x + math.cos(a) * (r + 22), y + math.sin(a) * (r + 22)
    s1 = (x + math.cos(a + 0.5) * (r - 4), y + math.sin(a + 0.5) * (r - 4))
    s2 = (x + math.cos(a - 0.5) * (r - 4), y + math.sin(a - 0.5) * (r - 4))
    ptr = f'<path d="M {_f(s1[0])} {_f(s1[1])} L {_f(px)} {_f(py)} L {_f(s2[0])} {_f(s2[1])} Z" fill="{WHITE}" stroke="{col}" stroke-width="6" stroke-linejoin="round"/>'
    sym = (f'<path d="M {_f(x - r * 0.45)} {_f(y + 2)} L {_f(x - r * 0.1)} {_f(y + r * 0.36)} L {_f(x + r * 0.5)} {_f(y - r * 0.36)}" '
           f'fill="none" stroke="{col}" stroke-width="{r * 0.24:.0f}" stroke-linecap="round" stroke-linejoin="round"/>' if ok else
           f'<path d="M {_f(x - r * 0.38)} {_f(y - r * 0.38)} L {_f(x + r * 0.38)} {_f(y + r * 0.38)} M {_f(x + r * 0.38)} {_f(y - r * 0.38)} '
           f'L {_f(x - r * 0.38)} {_f(y + r * 0.38)}" stroke="{col}" stroke-width="{r * 0.24:.0f}" stroke-linecap="round"/>')
    o = ' opacity="0"' if hidden else ""
    return (f'<g id="{eid}" class="ak"{o}><circle cx="{_f(x)}" cy="{_f(y + 6)}" r="{r}" fill="#000" opacity="0.18"/>{ptr}'
            f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{r}" fill="{WHITE}" stroke="{col}" stroke-width="6"/>{sym}</g>')


# ---- board: placement + checks --------------------------------------------------------------------------------------
class Board:
    """Registers cues (box + on-screen time) and checks the layout. faces: [(cx, cy, r)] head circles; caption:
    (y0, y1) band of the caption line."""

    def __init__(self, faces=(), caption=None, safe=SAFE, scene=""):
        self.faces, self.caption, self.safe, self.scene = list(faces), caption, safe, scene
        self.items = []          # (kind, eid, box, t0, t1, extra)

    def _add(self, kind, eid, box, t0, t1, **extra):
        self.items.append((kind, eid, box, t0, t1, extra))

    def chip(self, eid, text, lane, t0, t1, size=40, color=ORANGE, hidden=True):
        y = LANES[lane]
        svg, box = chip_svg(eid, INFO_X, y, text, size, color, hidden)
        self._add("chip", eid, box, t0, t1)
        return svg

    def meter_box(self, eid, width, height, t0, t1):
        """The meter draws itself; register its box (left edge INFO_X, centred on the meter lane)."""
        y = LANES["meter"]
        box = (INFO_X, y - height / 2, INFO_X + width, y + height / 2)
        self._add("meter", eid, box, t0, t1)
        return box

    def arrow_at(self, eid, joint, toward, t0, t1, length=170, bend=0.35, lift=(0, -40), width=12):
        """Motion arrow starting near `joint` (offset by `lift`, off the limb), sweeping `length` px along `toward`
        (a direction vector), bowed by `bend` to the left of travel."""
        ln = math.hypot(*toward) or 1
        ux, uy = toward[0] / ln, toward[1] / ln
        p0 = (joint[0] + lift[0], joint[1] + lift[1])
        p1 = (p0[0] + ux * length, p0[1] + uy * length)
        c = ((p0[0] + p1[0]) / 2 + uy * length * bend, (p0[1] + p1[1]) / 2 - ux * length * bend)
        xs, ys = (p0[0], c[0], p1[0]), (p0[1], c[1], p1[1])
        pad = width * 2
        box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        self._add("arrow", eid, box, t0, t1, anchor=joint, length=math.hypot(p1[0] - p0[0], p1[1] - p0[1]))
        return arrow_svg(eid, p0, c, p1, width)

    def mark_at(self, eid, a, b, ok, t0, t1, r=40, side=-1, gap=95, hidden=True):
        """Mark beside the middle of limb segment a-b, `gap` px off it on `side` (-1 = above for a level limb)."""
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        if ny * side < 0:
            nx, ny = -nx, -ny
        x, y = mx + nx * gap, my + ny * gap
        box = circle_box(x, y, r + 8)
        self._add("mark", eid, box, t0, t1, seg=(a, b), center=(x, y))
        return mark_svg(eid, x, y, ok, r, (mx, my), hidden)

    def check(self):
        out, sx0, sy0, sx1, sy1 = [], *self.safe
        tag = f"{self.scene}: " if self.scene else ""
        for kind, eid, b, t0, t1, ex in self.items:
            if b[0] < sx0 or b[1] < sy0 or b[2] > sx1 or b[3] > sy1:
                out.append(f"{tag}{kind} {eid} leaves the safe area {self.safe}: box {tuple(round(v) for v in b)}")
            for cx, cy, r in self.faces:
                if box_hits_circle(b, cx, cy, r):
                    out.append(f"{tag}{kind} {eid} covers a face at ({cx:.0f}, {cy:.0f})")
            if self.caption and b[3] > self.caption[0] and b[1] < self.caption[1]:
                out.append(f"{tag}{kind} {eid} touches the caption band {self.caption}")
            if kind == "arrow" and ex["length"] < ARROW_MIN:
                out.append(f"{tag}arrow {eid} is too short to read ({ex['length']:.0f} px < {ARROW_MIN})")
            if kind == "mark" and seg_dist(ex["center"], *ex["seg"]) > MARK_MAX_GAP:
                out.append(f"{tag}mark {eid} floats {seg_dist(ex['center'], *ex['seg']):.0f} px from its limb (max {MARK_MAX_GAP})")
        for i, (k1, e1, b1, s1, f1, x1) in enumerate(self.items):
            for k2, e2, b2, s2, f2, x2 in self.items[i + 1:]:
                if s1 < f2 and s2 < f1 and overlaps(b1, b2, 6) and not ({k1, k2} == {"mark"} and x1.get("center") == x2.get("center")):
                    out.append(f"{tag}{k1} {e1} and {k2} {e2} overlap on screen at the same time")
        return out

    def assert_clean(self):
        bad = self.check()
        if bad:
            raise SystemExit("cue layout:\n  " + "\n  ".join(bad))
        return True


def face_circles(J_list, scale, r=118):
    """Head circles from rig joints (r34kit.joints output): one per character, radius r * scale."""
    return [(j["head"][0], j["head"][1], r * scale) for j in J_list]
