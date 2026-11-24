"""3D worlds with 2D character cards: light presets, ink outlines, lens blur and lit cards for three3d scenes.

Patterns from claude-animated-shorts (MIT): world ink from a normals pass, gather lens blur from depth, a sun
placed from the shot's view direction, character cards that take the scene light. Everything here is JS that goes
in front of a `three3d.scene` body, so the body can use `env`:

    import three3d, env3d

    def s04(p, d, shot):
        body = env3d.prelude("golden", view=(4.7, -8.8)) + '''
            const M = await env.load({ road: "city/road-straight", tree: "arena/tree" });
            for (let i = 0; i < 10; i++) env.put(M.road, 0, 8 - i * 4, { s: 4 });
            const host = await env.card(["assets/char/host_neutral.png", "assets/char/host_point.png"], { h: 1.75, x: 4.8, z: -39.4 });
            return (t) => {
                camera.position.set(1.5, 1.9, -31); camera.lookAt(6, 1.5, -40);
                env.creep(t, 0);                       // every hold creeps (no dead frames)
                host.pose(t >= 2.1 ? 1 : 0); host.face();
                env.blur = 13 * ease(seg(t, 1.0, 2.5)); env.focusOn(host);
            };
        '''
        html, js = three3d.scene(p, d, body, lights=False)
        return "", js, html

What `env` gives the body:
- `env.load({key: "pack/name"})` -> {key: Object3D} from `<base>/<pack>/<name>.glb` (shadows on).
- `env.put(obj, x, z, {s, ry, y, noink})` clones and places a model; `noink: true` for flat ground detail
  (grass tiles, painted stripes) that must not get ink lines.
- `env.ground(color)` big lit ground plane that takes shadows.
- `await env.card(urls, {h, x, z, foot})` a 2D character card (PNG with alpha) standing on the ground: lit by the
  sun and the sky (Lambert, normal bent toward the camera and up), casts a shadow, has a contact shadow, and never
  gets world ink. `.pose(i)` swaps the picture, `.face()` turns it to the camera, `.mesh` is the plane.
- `env.unlit(mesh)` keeps painted signs readable (a side sun turns a lit sign grey).
- `env.creep(t, t0, speed)` keeps pushing the camera in along its view after `t0` (call it after placing the camera).
- `env.blur` (px at 1080 wide, 0 = sharp) and `env.focus` (metres) or `env.focusOn(card)` drive the lens.
- `env.sun`, `env.sunAt(x, z)` move the shadow box to where the action is; `env.LP` is the preset in use.

Presets: "day" (sun from the side, 75 deg az, 48 deg up; blue sky) and "golden" (low sun just off the view
direction, sun disc in the sky, peach horizon, blue-violet shade). The sun is set from `view` (the shot's camera
direction in x/z) and frozen for the shot, so the light reads the same whatever the town layout.
"""
import json

PRESETS = {
    "day": {"az": 75, "el": 48, "sun": 0xFFF1D6, "sunI": 2.7, "sky": 0xD3E6FF, "ground": 0x59628A, "hemiI": 1.05,
            "top": 0x3E7FD2, "hor": 0xB8D0EC, "fogNear": 30, "fogFar": 140, "disc": 0.0},
    "golden": {"az": 6, "el": 7, "sun": 0xFFB36B, "sunI": 3.6, "sky": 0xC9B4E6, "ground": 0x6A64B0, "hemiI": 2.1,
               "top": 0x7A6A9E, "hor": 0xFFC47C, "fogNear": 45, "fogFar": 150, "disc": 1.0},
}
INK = 0x030303                  # world line colour
INK_NEAR, INK_FAR = 5.1, 3.3    # line width in px at 1080 wide: near (6 m) -> far (90 m)

_JS = r"""
const env = {};
{
const LP = %(preset)s;
env.LP = LP;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMappingExposure = 1.05;
camera.fov = %(fov)s; camera.far = 300; camera.updateProjectionMatrix();
camera.layers.enable(1);                                   // layer 1 = NOINK: cards, sky, flat ground detail
scene.fog = new THREE.Fog(LP.hor, LP.fogNear, LP.fogFar);  // fog = horizon colour: far things melt into the sky

// sun from the shot's view direction: az 0 = straight ahead (backlit), 90 = from the right, el = height
const rad = Math.PI / 180, FWD = new THREE.Vector3(%(vx)s, 0, %(vz)s).normalize(), RIGHT = new THREE.Vector3(-FWD.z, 0, FWD.x);
const SUN_DIR = new THREE.Vector3()
  .addScaledVector(FWD, Math.cos(LP.az * rad) * Math.cos(LP.el * rad))
  .addScaledVector(RIGHT, Math.sin(LP.az * rad) * Math.cos(LP.el * rad))
  .add(new THREE.Vector3(0, Math.sin(LP.el * rad), 0)).normalize();
const sun = new THREE.DirectionalLight(LP.sun, LP.sunI);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.06;   // low sun: no acne stripes on flat ground
Object.assign(sun.shadow.camera, { left: -%(box)s, right: %(box)s, top: %(box)s, bottom: -%(box)s, near: 1, far: 160 });
sun.shadow.camera.layers.enable(1);                        // cards cast shadows too
scene.add(sun, sun.target);
env.sun = sun;
env.sunAt = (x, z) => { sun.target.position.set(x, 0, z); sun.position.copy(sun.target.position).addScaledVector(SUN_DIR, 70); };
env.sunAt(0, 0);
scene.add(new THREE.HemisphereLight(LP.sky, LP.ground, LP.hemiI));   // the cool tint lives in the shade only

// sky dome: top -> horizon gradient (+ sun disc at golden hour); never tone mapped, no ink
const sky = new THREE.Mesh(new THREE.SphereGeometry(250, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false, toneMapped: false,
  uniforms: { top: { value: new THREE.Color(LP.top) }, hor: { value: new THREE.Color(LP.hor) },
              sunDir: { value: SUN_DIR }, disc: { value: LP.disc }, discCol: { value: new THREE.Color(0xFFCF9E) } },
  vertexShader: "varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
  fragmentShader: `varying vec3 vDir; uniform vec3 top, hor, sunDir, discCol; uniform float disc;
    void main(){ vec3 c = mix(hor, top, smoothstep(0.0, 0.55, vDir.y));
      float s = max(dot(normalize(vDir), normalize(sunDir)), 0.0);
      c += disc * (discCol * smoothstep(0.9993, 0.9997, s) * 2.0 + discCol * pow(s, 60.0) * 0.35);
      gl_FragColor = vec4(c, 1.0); }`,
}));
sky.layers.set(1); sky.renderOrder = -1; sky.frustumCulled = false;
scene.add(sky);
env.onCamera = () => sky.position.copy(camera.position);

// models
let loader = null;
env.load = async (names) => {
  if (!loader) { const m = await import("%(gltf)s"); loader = new m.GLTFLoader(); }
  const out = {};
  await Promise.all(Object.entries(names).map(async ([k, n]) => {
    const g = await loader.loadAsync(`%(base)s/${n}.glb`);
    g.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    out[k] = g.scene;
  }));
  return out;
};
env.put = (obj, x, z, { s = 1, ry = 0, y = 0, noink = false } = {}) => {
  const o = obj.clone(); o.position.set(x, y, z); o.scale.setScalar(s); o.rotation.y = ry; scene.add(o);
  if (noink) o.traverse((c) => c.layers.set(1));
  return o;
};
env.ground = (color = 0x86BE5C) => {
  const g = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshLambertMaterial({ color }));
  g.rotation.x = -Math.PI / 2; g.position.y = -0.02; g.receiveShadow = true; scene.add(g); return g;
};
env.unlit = (mesh) => { const m = mesh.material; mesh.material = new THREE.MeshBasicMaterial({ map: m.map, color: m.color, transparent: m.transparent, alphaTest: m.alphaTest }); return mesh; };

// 2D character card: lit by the scene, casts a shadow, contact shadow at the feet, no world ink
const blobTex = (() => { const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, "rgba(0,0,0,1)"); r.addColorStop(0.55, "rgba(0,0,0,0.6)"); r.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
env.card = async (urls, { h = 1.75, x = 0, z = 0, foot = 0.5 } = {}) => {
  const tl = new THREE.TextureLoader();
  const tex = await Promise.all([].concat(urls).map((u) => tl.loadAsync(u)));
  for (const t of tex) t.colorSpace = THREE.SRGBColorSpace;
  const w = h * tex[0].image.width / tex[0].image.height;
  const geo = new THREE.PlaneGeometry(w, h); geo.translate(w * (0.5 - foot), h / 2 - 0.03, 0);   // feet at the origin
  const n = geo.attributes.normal, bent = new THREE.Vector3(0, 0.55, 0.84).normalize();
  for (let i = 0; i < n.count; i++) n.setXYZ(i, bent.x, bent.y, bent.z);   // light follows sun height, not card spin
  const mat = new THREE.MeshLambertMaterial({ map: tex[0], alphaTest: 0.5 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = true; mesh.receiveShadow = true;
  mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: tex[0], alphaTest: 0.5 });
  mesh.position.set(x, 0, z); mesh.layers.set(1); scene.add(mesh);
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.75, w * 0.3),
    new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, opacity: 0.5, depthWrite: false, color: 0x1a1230 }));
  blob.rotation.x = -Math.PI / 2; blob.position.set(x, 0.03, z); blob.layers.set(1); blob.renderOrder = 1; scene.add(blob);
  return {
    mesh, blob, focusY: h * 0.83,
    pose(i) { mat.map = tex[Math.min(i, tex.length - 1)]; mesh.customDepthMaterial.map = mat.map; },
    face() { mesh.rotation.y = Math.atan2(camera.position.x - mesh.position.x, camera.position.z - mesh.position.z); },
    moveTo(nx, nz) { mesh.position.set(nx, 0, nz); blob.position.set(nx, 0.03, nz); },
  };
};

// camera: every hold creeps
const fwd = new THREE.Vector3();
env.creep = (t, t0 = 0, speed = 0.35) => { const k = Math.max(0, t - t0); if (k > 0) { camera.getWorldDirection(fwd); camera.position.addScaledVector(fwd, k * speed); } };

// lens
env.blur = 0; env.focus = 10;
env.focusOn = (card) => { env.focus = camera.position.distanceTo(card.mesh.position.clone().setY(card.focusY)); };

// post: world normals -> ink -> lens blur -> tone map
const mkRT = () => { const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType }); rt.depthTexture = new THREE.DepthTexture(W, H); return rt; };
const rtColor = mkRT(), rtNorm = mkRT(), rtInk = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const normMat = new THREE.MeshNormalMaterial(), quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), quadGeo = new THREE.PlaneGeometry(2, 2);
const pass = (frag, uniforms, toneMapped = false) => {
  const m = new THREE.ShaderMaterial({ uniforms, toneMapped, depthTest: false, depthWrite: false,
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }", fragmentShader: frag });
  const sc = new THREE.Scene(); sc.add(new THREE.Mesh(quadGeo, m)); return { m, sc };
};
const px = W / 1080;
const COMMON = `#include <packing>
  varying vec2 vUv; uniform vec2 res; uniform float near, far;
  float vz(sampler2D d, vec2 uv){ return -perspectiveDepthToViewZ(texture2D(d, uv).x, near, far); }`;
const ink = pass(`${COMMON}
  uniform sampler2D tColor, tNorm, tNormDepth, tColorDepth; uniform vec3 inkCol, fogCol; uniform float fogNear, fogFar, px, on;
  void main(){
    vec4 base = texture2D(tColor, vUv);
    float zc = vz(tNormDepth, vUv);
    float w = mix(%(ink_near)s, %(ink_far)s, smoothstep(6.0, 90.0, zc)) * px;
    vec2 o = w * 0.5 / res;
    vec3 nc = texture2D(tNorm, vUv).xyz * 2.0 - 1.0;
    float edge = 0.0;
    vec2 dirs[4]; dirs[0] = vec2(o.x, 0.0); dirs[1] = vec2(0.0, o.y); dirs[2] = vec2(o.x, o.y); dirs[3] = vec2(o.x, -o.y);
    for (int i = 0; i < 4; i++) {
      float za = vz(tNormDepth, vUv + dirs[i]), zb = vz(tNormDepth, vUv - dirs[i]);
      edge = max(edge, smoothstep(0.010, 0.025, abs(za + zb - 2.0 * zc) / zc));          // depth jump (2nd difference)
      vec3 na = texture2D(tNorm, vUv + dirs[i]).xyz * 2.0 - 1.0, nb = texture2D(tNorm, vUv - dirs[i]).xyz * 2.0 - 1.0;
      edge = max(edge, 0.8 * smoothstep(0.16, 0.26, 1.0 - min(dot(nc, na), dot(nc, nb))));   // crease > ~35 deg
    }
    if (vz(tColorDepth, vUv) < zc - 0.05) edge = 0.0;            // a card in front: no world ink over it
    if (texture2D(tNormDepth, vUv).x >= 0.9999) edge = 0.0;      // sky
    float fogF = smoothstep(fogNear, fogFar, zc);
    vec3 line = mix(inkCol, fogCol, 0.3 * fogF);
    gl_FragColor = vec4(mix(base.rgb, line, on * edge * (1.0 - 0.75 * fogF)), 1.0);
  }`, {
  tColor: { value: rtColor.texture }, tColorDepth: { value: rtColor.depthTexture },
  tNorm: { value: rtNorm.texture }, tNormDepth: { value: rtNorm.depthTexture },
  res: { value: new THREE.Vector2(W, H) }, near: { value: 0.1 }, far: { value: 300 }, px: { value: px },
  inkCol: { value: new THREE.Color(%(ink)s) }, fogCol: { value: new THREE.Color(LP.hor) },
  fogNear: { value: LP.fogNear }, fogFar: { value: LP.fogFar }, on: { value: %(ink_on)s },
});
const lens = pass(`${COMMON}
  uniform sampler2D tInk, tDepth; uniform float cInf, focus;
  float coc(vec2 uv){ float z = vz(tDepth, uv); return min(cInf * abs(1.0 - focus / z), cInf * 1.5); }
  void main(){
    float c0 = coc(vUv);
    vec3 acc = texture2D(tInk, vUv).rgb; float wsum = 1.0;
    if (cInf > 0.25) {
      float R = cInf * 1.5;
      for (int i = 1; i < 48; i++) {
        float fi = float(i), r = sqrt(fi / 48.0) * R, a = fi * 2.39996323;
        vec2 uv = vUv + vec2(cos(a), sin(a)) * r / res;
        float wgt = clamp(min(coc(uv), c0 + 1.0) - r + 1.0, 0.0, 1.0);   // gather: sharp things in front stay sharp
        acc += texture2D(tInk, uv).rgb * wgt; wsum += wgt;
      }
    }
    vec3 col = acc / wsum;
    float skyM = step(0.9999, texture2D(tDepth, vUv).x);              // the sky is never tone mapped
    gl_FragColor = vec4(mix(toneMapping(col), col, skyM), 1.0);
    #include <colorspace_fragment>
  }`, {
  tInk: { value: rtInk.texture }, tDepth: { value: rtColor.depthTexture },
  res: { value: new THREE.Vector2(W, H) }, near: { value: 0.1 }, far: { value: 300 }, cInf: { value: 0 }, focus: { value: 10 },
}, true);
scene.userData.draw = () => {
  env.onCamera();
  for (const u of [ink.m.uniforms, lens.m.uniforms]) { u.near.value = camera.near; u.far.value = camera.far; }
  lens.m.uniforms.cInf.value = %(lens_on)s ? env.blur * px : 0;
  lens.m.uniforms.focus.value = env.focus;
  const fog = scene.fog;
  camera.layers.disable(1);                                   // world only, normals
  scene.overrideMaterial = normMat; scene.fog = null;
  renderer.setRenderTarget(rtNorm); renderer.setClearColor(0x8080ff, 1); renderer.clear(); renderer.render(scene, camera);
  scene.overrideMaterial = null; scene.fog = fog;
  camera.layers.enable(1);                                    // world + cards + sky, colour
  renderer.setRenderTarget(rtColor); renderer.render(scene, camera);
  renderer.setRenderTarget(rtInk); renderer.render(ink.sc, quadCam);
  renderer.setRenderTarget(null); renderer.render(lens.sc, quadCam);
};
}
"""


def prelude(preset="day", view=(0.0, -1.0), ink=True, lens=True, fov=50, shadow_box=45, base="assets/models"):
    """JS to put in front of a three3d.scene body (use three3d.scene(..., lights=False)).
    preset: "day" | "golden" or a dict with the same keys as PRESETS. view: the shot's camera direction (x, z)."""
    lp = PRESETS[preset] if isinstance(preset, str) else {**PRESETS["day"], **preset}
    vx, vz = (float(v) for v in view)
    if vx == 0 and vz == 0:
        raise ValueError("view must be a direction, not (0, 0)")
    from three3d import THREE_VERSION
    return _JS % {
        "preset": json.dumps(lp), "vx": vx, "vz": vz, "fov": float(fov), "box": float(shadow_box),
        "base": base.rstrip("/"), "ink": INK, "ink_near": INK_NEAR, "ink_far": INK_FAR,
        "ink_on": "1.0" if ink else "0.0", "lens_on": "true" if lens else "false",
        "gltf": f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/loaders/GLTFLoader.js/+esm",
    }
