"""Three.js (3D) scenes for akra episodes, rendered by HyperFrames like any other scene.

A scene function returns (svg, js, html) instead of (svg, js): the extra html holds a WebGL canvas that sits
UNDER the scene's SVG, so labels, arrows and the brand drawn in SVG stay on top of the 3D picture.

    import three3d

    def s03(p, d, shot):
        html, js = three3d.scene(p, d, '''
            const box = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), new THREE.MeshStandardMaterial({ color: 0xC8A15A }));
            scene.add(box);
            camera.position.set(0, 1.5, 7); camera.lookAt(0, 0, 0);
            return (t) => { box.rotation.y = t * 0.8; };      // pure function of local time t (0 = scene start)
        ''')
        svg = hf.label(p, "a", 540, 1100, "Gear box")
        return svg, js + hf.show(p, "a", 1.2), html

How it renders (the HyperFrames contract for 3D): the scene timeline tweens a clock from 0 to the scene length and
draws the frame for that time on every seek; setup (meshes, shader compile, one throwaway frame) is one
`window.__hf.buildReady` promise, so the first frame waits for it. Frames render out of order, so the update you
return must depend on `t` only: no requestAnimationFrame, no timers, no Math.random (use `rand()`, seeded).

In your setup code you get: THREE, scene, camera (PerspectiveCamera 35 deg), renderer, rand() (seeded 0..1),
clamp, lerp, seg(t, a, b) (0..1 progress of t between a and b), ease(x) (smooth in-out), and W/H of the canvas.
A default light rig (warm key, cool rim, soft fill) is added unless lights=False.
"""
import json

THREE_VERSION = "0.184.0"          # pinned; same release the HyperFrames 3D examples use
THREE_URL = f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/+esm"

_MODULE = """<script type="module">
import * as THREE from "%(url)s";
const host = window.__akra3d[%(key)s];
try {
const W = %(w)d, H = %(h)d;
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById(%(cid)s), antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, W / H, 0.1, 200);
camera.position.set(0, 0, 10);
let seed = %(seed)d >>> 0;
const rand = () => { seed = (seed + 0x6D2B79F5) >>> 0; let x = seed; x = Math.imul(x ^ (x >>> 15), x | 1);
  x ^= x + Math.imul(x ^ (x >>> 7), x | 61); return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, k) => a + (b - a) * k;
const seg = (t, a, b) => clamp((t - a) / Math.max(1e-6, b - a));
const ease = (x) => x * x * (3 - 2 * x);
if (%(lights)s) {
  const key = new THREE.DirectionalLight(0xFFE2B8, 2.4); key.position.set(-4, 6, 6); scene.add(key);
  const rim = new THREE.DirectionalLight(0x9FD8FF, 1.6); rim.position.set(5, 3, -5); scene.add(rim);
  scene.add(new THREE.HemisphereLight(0xFFFFFF, 0x30343A, 0.6));
}
const update = await (async () => {
%(body)s
})();
if (typeof update !== "function") throw new Error("three3d scene %(key_raw)s: the setup code must return update(t)");
host.render = (t) => { update(t); renderer.render(scene, camera); };
await renderer.compileAsync(scene, camera);
host.render(0);
renderer.getContext().readPixels(0, 0, 1, 1, renderer.getContext().RGBA, renderer.getContext().UNSIGNED_BYTE, new Uint8Array(4));
host.render(host.clock.t);
host.ready();
} catch (err) { host.fail(err); throw err; }
</script>"""


def scene(p, dur, body, region=(0, 0, 1080, 1920), seed=1, lights=True):
    """3D layer for scene `p` lasting `dur` s. `body` is JS setup code that RETURNS update(t).
    region = (x, y, w, h) of the canvas in the 1080x1920 frame. Returns (html, js): put js in the scene's
    timeline code and return html as the third value of the scene function."""
    x, y, w, h = (int(v) for v in region)
    cid, key = f"{p}-3d", f"{p}-3d"
    canvas = (f'<canvas id="{cid}" width="{w}" height="{h}" '
              f'style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;"></canvas>')
    module = _MODULE % {"url": THREE_URL, "key": json.dumps(key), "key_raw": key, "cid": json.dumps(cid),
                        "w": w, "h": h, "seed": int(seed), "lights": "true" if lights else "false",
                        "body": body}
    js = (f'(function(){{const c={{t:0}},h={{clock:c,render:null}};'
          f'window.__akra3d=window.__akra3d||{{}};window.__akra3d[{json.dumps(key)}]=h;'
          f'window.__hf=window.__hf||{{}};window.__hf.buildReady=window.__hf.buildReady||{{}};'
          f'window.__hf.buildReady[{json.dumps(key)}]=new Promise(function(r,j){{h.ready=r;h.fail=j;}});'
          f'tl.to(c,{{t:{dur:.2f},duration:{dur:.2f},ease:"none",onUpdate:function(){{if(h.render)h.render(c.t);}}}},0);}})();')
    return canvas + "\n" + module, js
