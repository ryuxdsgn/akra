#!/usr/bin/env python3
"""Clipper mode builder: a streamer's moment -> 1080x1920 vertical clip with a split layout.

Layout (top to bottom): facecam panel (captions sit on the streamer's chest, so they never cover the
game) / accent seam with the title box / gameplay panel (clean: only the title box edge and a thin
progress bar touch it). Streamer audio is kept and follows the cuts. All text is drawn with Pillow,
so ffmpeg needs no drawtext or libass.

usage:
  python3 clip_split.py build   <clip-dir> [--preview T ...]   # reads <clip-dir>/clip.json
  python3 clip_split.py cover   <clip-dir>                     # % of the gameplay panel covered by overlays
  python3 clip_split.py clean   <clip-dir> --yes               # delete raw downloads after upload

clip.json (paths relative to the clip dir unless noted):
{
  "channel": "<channel-id>",                 # brand files resolve under channels/<id>/
  "dur": 29.0, "lufs": -14,
  "hook": "TEXT", "credit": "Clip: <creator> (YouTube)",
  "face": [x, y, w, h],                      # facecam box in source px
  "game": [x, y, w, h] | "center",           # gameplay crop in source px; "center" = auto 0.885:1 crop
  "sources": {"a": "source/a.mp4"},          # sources with video + the streamer's audio
  "shots": [["a", src_start, dur, "LABEL"]], # LABEL shows on the seam ("" = none); shot 0 shows the hook
  "words": [{"text": "...", "start": 0.0, "end": 0.4}],  # OUTPUT time; only clean, correct words
  "watermark": {"file": "brand/watermark.png", "w": 240},  # optional, under channels/<id>/
  "accent": ["#FF4FA3", "#FFC23A"],          # seam and progress bar gradient
  "font": "/path/to/Black.ttf"               # optional; default: first heavy font found
}
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30
FACE_H = 700                 # facecam panel height
SEAM = 10                    # accent bar height
GAME_Y = FACE_H              # gameplay panel top
GAME_H = H - GAME_Y
CAP_Y = 565                  # caption top (on the streamer's chest, inside the face panel)
YELLOW, WHITE, BLACK = (255, 210, 63, 255), (255, 255, 255, 255), (0, 0, 0, 255)
FONT_CANDIDATES = [
    "~/Library/Fonts/NunitoSans-Black.ttf", "~/Library/Fonts/OpenSauceOne-Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf", "/Library/Fonts/Arial Black.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/ariblk.ttf",
]
RAW_DIRS = ("raw", "source", "jobs")


def repo_root(start):
    for p in [start, *start.parents]:
        if (p / "channels").is_dir():
            return p
    return start


def hex_rgba(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


class Clip:
    def __init__(self, d):
        from PIL import Image, ImageFont
        self.Image = Image
        self.ImageFont = ImageFont
        self.dir = Path(d).resolve()
        self.c = json.loads((self.dir / "clip.json").read_text())
        c = self.c
        self.dur = c["dur"]
        font = c.get("font") or next((str(Path(f).expanduser()) for f in FONT_CANDIDATES
                                      if Path(f).expanduser().exists()), None)
        if not font:
            sys.exit("no heavy font found: set \"font\" in clip.json")
        self.font_path = font
        self.f_hook, self.f_label, self.f_cap, self.f_credit = (ImageFont.truetype(font, s) for s in (74, 58, 78, 28))
        self.shots, t = [], 0.0
        for key, s0, dd, label in c["shots"]:
            self.shots.append((t, t + dd, key, s0, label)); t += dd
        self.groups = self._groups(c.get("words", []))
        self.accent = [hex_rgba(x) for x in c.get("accent", ["#FF4FA3", "#FFC23A"])]
        self.wm = None
        if c.get("watermark"):
            root = repo_root(self.dir)
            im = Image.open(root / "channels" / c["channel"] / c["watermark"]["file"]).convert("RGBA")
            w = c["watermark"].get("w", 240)
            self.wm = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        self._bar = self._gradient(W, SEAM)
        self._shade = self._face_shade()

    # ---------- drawing ----------
    @staticmethod
    def _groups(words):
        out, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) == 3 or w["text"][-1] in ".,?!":
                out.append(cur); cur = []
        return out + ([cur] if cur else [])

    def _gradient(self, w, h):
        im = self.Image.new("RGBA", (w, h))
        a, b = self.accent
        for x in range(w):
            k = x / max(w - 1, 1)
            col = tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(4))
            for y in range(h):
                im.putpixel((x, y), col)
        return im

    def _face_shade(self):
        """Dark fade over the lower face panel so captions stay readable."""
        im = self.Image.new("RGBA", (W, FACE_H), (0, 0, 0, 0))
        top = CAP_Y - 90
        for y in range(top, FACE_H):
            k = (y - top) / (FACE_H - top)
            im.paste((0, 0, 0, int(170 * k)), (0, y, W, y + 1))
        return im

    def _box(self, img, cy, text, f, scale):
        from PIL import ImageDraw
        m = ImageDraw.Draw(self.Image.new("RGBA", (1, 1)))
        b = m.textbbox((0, 0), text, font=f)
        pad = 24
        bw, bh = b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2
        LW = max(W, bw + 40)
        layer = self.Image.new("RGBA", (LW, bh + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x0 = (LW - bw) / 2
        d.rounded_rectangle((x0 + 6, 26, x0 + bw + 6, 26 + bh), radius=20, fill=(0, 0, 0, 150))  # drop shadow
        d.rounded_rectangle((x0, 20, x0 + bw, 20 + bh), radius=20, fill=YELLOW, outline=BLACK, width=5)
        d.text((x0 + pad - b[0], 20 + pad - b[1]), text, font=f, fill=BLACK)
        if bw > W - 40:
            scale *= (W - 40) / bw
        if scale != 1.0 or LW != W:
            layer = layer.resize((max(1, int(LW * scale)), max(1, int(layer.height * scale))), self.Image.LANCZOS)
        img.alpha_composite(layer, (int((W - layer.width) / 2), int(cy - layer.height / 2)))

    @staticmethod
    def _pop(t, t0, d=0.18):
        x = min(max((t - t0) / d, 0), 1)
        return 0.6 + 0.4 * (1 - (1 - x) ** 3)

    def overlay(self, t):
        from PIL import ImageDraw
        img = self.Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        img.alpha_composite(self._shade, (0, 0))
        img.alpha_composite(self._bar, (0, FACE_H - SEAM // 2))
        if self.wm:
            img.alpha_composite(self.wm, (28, 30))
        cr = self.c["credit"]
        cw = d.textlength(cr, font=self.f_credit)
        d.text((W - 28 - cw, 42), cr, font=self.f_credit, fill=(255, 255, 255, 230), stroke_width=3, stroke_fill=BLACK)
        sh = next((s for s in self.shots if s[0] <= t < s[1]), self.shots[-1])
        if t < self.shots[0][1]:
            self._box(img, FACE_H, self.c["hook"], self.f_hook, self._pop(t, 0))
        elif sh[4]:
            self._box(img, FACE_H, sh[4], self.f_label, self._pop(t, sh[0]))
        g = [x for x in self.groups if x[0]["start"] - 0.05 <= t <= x[-1]["end"] + 0.6]
        if g:
            g = g[-1]
            words = [w["text"].strip(".,?!").upper() for w in g]
            f = self.f_cap
            sp = d.textlength(" ", font=f)
            total = sum(d.textlength(x, font=f) for x in words) + sp * (len(words) - 1)
            if total > W - 120:
                f = self.ImageFont.truetype(self.font_path, int(78 * (W - 120) / total))
                sp = d.textlength(" ", font=f)
                total = sum(d.textlength(x, font=f) for x in words) + sp * (len(words) - 1)
            act = max(i for i, w in enumerate(g) if w["start"] - 0.05 <= t or i == 0)
            x = (W - total) / 2
            for i, wd in enumerate(words):
                d.text((x, CAP_Y), wd, font=f, fill=YELLOW if i == act else WHITE, stroke_width=9, stroke_fill=BLACK)
                x += d.textlength(wd, font=f) + sp
        pw = int(W * min(t / self.dur, 1))
        if pw:
            img.alpha_composite(self._gradient_cached(pw), (0, H - 8))
        return img

    def _gradient_cached(self, pw):
        if not hasattr(self, "_pbar"):
            full = self.Image.new("RGBA", (W, 8))
            full.paste(self._bar.resize((W, 8)), (0, 0))
            self._pbar = full
        return self._pbar.crop((0, 0, pw, 8))

    # ---------- video ----------
    def game_box(self, src_w=None, src_h=None):
        g = self.c["game"]
        if g != "center":
            return g
        if src_w is None:
            src_w, src_h = self._probe(next(iter(self.c["sources"].values())))
        gw = round(src_h * W / GAME_H) // 2 * 2
        return [(src_w - gw) // 2, 0, gw, src_h]

    def _probe(self, rel):
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height", "-of", "csv=p=0", str(self.dir / rel)],
                             capture_output=True, text=True, check=True).stdout.strip().split(",")
        return int(out[0]), int(out[1])

    def panel_chain(self, i, label=True):
        fx, fy, fw, fh = self.c["face"]
        gx, gy, gw, gh = self.game_box()
        tail = f"[st{i}];" if label else ""
        return (f"[{i}:v]split[f{i}][g{i}];"
                f"[f{i}]crop={fw}:{fh}:{fx}:{fy},scale={W}:{FACE_H}:flags=lanczos,setsar=1[fp{i}];"
                f"[g{i}]crop={gw}:{gh}:{gx}:{gy},scale={W}:{GAME_H}:flags=lanczos,setsar=1[gp{i}];"
                f"[fp{i}][gp{i}]vstack{tail}")

    def render(self):
        out = self.dir / "renders" / f"{self.dir.name}.mp4"
        out.parent.mkdir(exist_ok=True)
        cmd = ["ffmpeg", "-v", "error", "-y"]
        for a, b, key, s0, _ in self.shots:
            cmd += ["-ss", f"{s0:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", str(self.dir / self.c["sources"][key])]
        n = len(self.shots)
        cmd += ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        fc = ""
        for i, (a, b, *_) in enumerate(self.shots):
            d = b - a
            fc += self.panel_chain(i)
            fc += (f"[st{i}]trim=duration={d:.3f},setpts=PTS-STARTPTS,fps={FPS}[v{i}];"
                   f"[{i}:a]atrim=duration={d:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,"
                   f"afade=t=out:st={d - 0.04:.3f}:d=0.04[a{i}];")
        fc += "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[base][aud];"
        fc += f"[{n}:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,format=yuv420p[vout];"
        fc += f"[aud]loudnorm=I={self.c.get('lufs', -14)}:TP=-1.5:LRA=11,atrim=duration={self.dur}[aout]"
        cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium",
                "-crf", "18", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{self.dur}",
                "-movflags", "+faststart", str(out)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(int(self.dur * FPS)):
            p.stdin.write(self.overlay(i / FPS).tobytes())
        p.stdin.close()
        rc = p.wait()
        print(out)
        return rc

    def preview(self, t):
        a, b, key, s0, _ = next(s for s in self.shots if s[0] <= t < s[1])
        out = self.dir / "renders" / f"preview_{t:05.2f}.png"
        out.parent.mkdir(exist_ok=True)
        raw = out.with_suffix(".base.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s0 + t - a:.3f}", "-i", str(self.dir / self.c["sources"][key]),
                        "-frames:v", "1", "-filter_complex", self.panel_chain(0, label=False), str(raw)], check=True)
        img = self.Image.open(raw).convert("RGBA")
        img.alpha_composite(self.overlay(t))
        img.convert("RGB").save(out)
        raw.unlink()
        print(out)

    def coverage(self):
        """Worst-case share of the gameplay panel covered by overlay pixels (alpha > 0) across the clip."""
        worst, at = 0.0, 0.0
        for k in range(int(self.dur * 4)):
            t = k / 4
            hist = self.overlay(t).crop((0, GAME_Y + SEAM, W, H)).getchannel("A").histogram()
            share = 1 - hist[0] / (W * (H - GAME_Y - SEAM))
            if share > worst:
                worst, at = share, t
        return worst, at


def clean(d, yes):
    d = Path(d).resolve()
    targets = [d / x for x in RAW_DIRS if (d / x).exists()]
    total = sum(f.stat().st_size for t in targets for f in t.rglob("*") if f.is_file())
    if not targets:
        print("nothing to clean"); return 0
    for t in targets:
        print(f"  {t.relative_to(d)}/")
    print(f"raw files: {total / 1e6:.1f} MB")
    if not yes:
        print("dry run: add --yes to delete (only after the clip is uploaded)"); return 0
    for t in targets:
        shutil.rmtree(t)
    print("deleted")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "cover", "clean"])
    ap.add_argument("dir")
    ap.add_argument("--preview", type=float, nargs="*")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if a.cmd == "clean":
        sys.exit(clean(a.dir, a.yes))
    c = Clip(a.dir)
    if a.cmd == "cover":
        worst, at = c.coverage()
        print(f"gameplay covered: {worst * 100:.1f}% worst case (t={at:.2f}s)")
        sys.exit(0 if worst <= 0.08 else 1)
    if a.preview:
        for t in a.preview:
            c.preview(t)
    else:
        sys.exit(c.render())


if __name__ == "__main__":
    main()
