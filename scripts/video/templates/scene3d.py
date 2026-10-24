"""The 3D animation template (3d.html): a narrated video whose backgrounds are 3D scenes drawn
with three.js, lit and colored from the brand's own accent. build.py imports SCENE3D_TEMPLATES.

The engine is a library of shots, each a pure function of time, so render.js can seek any frame
exactly: shapes, hero (a phone with the user's screenshot), cards, chart, coin, rings, and globe;
the mascot and its places (mascot.py), or the user's own rigged character in its place
(character.py); and the product's own screens (demo.py), which draw() hands
the frame between without a cut.
"""
from drawn import NARRATED_CSS, TIMELINE_JS, drawn_body
from character import CHARACTER_DOC, CHARACTER_JS
from demo import DEMO_CSS, DEMO_DOC, DEMO_JS
from mascot import MASCOT_DOC, MASCOT_JS

THREE_VERSION = "0.186.1"  # pinned to the version in scripts/video/package.json

# the shots, as listed in the template's comment
SHOT_DOC = f"""  Shots (data-shot), each running from its --in until the next shot starts:
    shapes  glossy shapes floating in the brand's colors. Any line; a good hook.
    hero    a phone turning toward the camera. data-src="assets/screen.png" puts
            the user's real screenshot on its screen; without one it shows a
            generic interface. Event: --land.
    cards   cards flying in and stacking, one per item: data-items="Research,
            Write,Post" (short labels; emoji work). Events: --card-1, --card-2...
    chart   bars growing: data-values="12,30,85", the user's real numbers only.
            Without data-values it draws a plain rising icon, not data.
            Event: --top, when the last bar tops out.
    coin    a coin or badge spinning in and landing: data-src="assets/logo.png"
            puts the logo on its face, otherwise a star. Event: --land.
    rings   flying through a tunnel of rings. Energy, a transition, a hook.
    globe   a dotted globe with arcs between places, for reach and "anywhere".
            Events: --arc-1, --arc-2...
{MASCOT_DOC}
{CHARACTER_DOC}
{DEMO_DOC}
  data-sfx on a shot cues a sound on one of its events, e.g. data-sfx="ding:land"
  (the events are set when the page loads, so render.js finds them)."""

ENGINE_JS = r"""
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

// ---- frame, colors, helpers
const ART = document.querySelector('canvas.art');
const W = ART.width, H = ART.height; // 1080x1920, or 1920x1080 for a landscape video
const WIDE = W > H;
const LIFT = Math.round(190 * H / 1920); // the subject sits this far above the frame's middle, clear of the captions
const css = getComputedStyle(document.documentElement);
const cssColor = (name, fallback) => new THREE.Color(css.getPropertyValue(name).trim() || fallback);
const SRGB = THREE.SRGBColorSpace;
const accent = cssColor('--accent', '#e07a55');
const hsl = accent.getHSL({}, SRGB);
const PAL = {
  accent,
  second: new THREE.Color().setHSL((hsl.h + 0.55) % 1, Math.min(0.65, hsl.s), 0.56, SRGB),
  third: new THREE.Color().setHSL((hsl.h + 0.09) % 1, Math.min(0.85, hsl.s + 0.1), 0.7, SRGB),
  pearl: new THREE.Color('#f2f0ec'),
  ink: new THREE.Color('#17171d'),
  bg: cssColor('--bg', '#0f0f13'),
};
const hex = (c) => `#${c.getHexString()}`;
const clamp = (x) => Math.min(1, Math.max(0, x));
const lerp = (a, b, k) => a + (b - a) * k;
const out3 = (x) => 1 - (1 - clamp(x)) ** 3;
const inOut = (x) => { x = clamp(x); return x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2; };
const back = (x) => { x = clamp(x); return 1 + 2.6 * (x - 1) ** 3 + 1.6 * (x - 1) ** 2; };
function rng(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) >>> 0;
    let t = seed;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const loadImage = (src) => new Promise((resolve, reject) => {
  const img = new Image();
  img.onload = () => resolve(img);
  img.onerror = () => reject(new Error(`image didn't load: ${src}`));
  img.src = src;
});
const canvas2d = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; };
// a browser opened on the file (not render.js) can refuse to read a local image into WebGL
const readable = (g) => { try { g.getImageData(0, 0, 1, 1); return true; } catch { return false; } };
const texture = (c) => { const t = new THREE.CanvasTexture(c); t.colorSpace = SRGB; t.anisotropy = 4; return t; };
const FONT = getComputedStyle(document.body).fontFamily;

// ---- renderer: one WebGL canvas, lit by a studio environment for soft reflections
const renderer = new THREE.WebGLRenderer({ canvas: document.querySelector('canvas.art'), antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.toneMapping = THREE.NeutralToneMapping; // keeps the brand colors true; ACES washes them out
renderer.outputColorSpace = SRGB;
const env = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;

const glossy = (c, rough = 0.28) => new THREE.MeshPhysicalMaterial({ color: c, roughness: rough, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.12 });
const metal = (c, rough = 0.24) => new THREE.MeshStandardMaterial({ color: c, roughness: rough, metalness: 0.85 });
const glow = (c, k = 0.6) => new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: k, roughness: 0.35, metalness: 0.2 });

// A soft radial backdrop: the brand's background, lifted toward the accent in the middle.
function backdrop(tint) {
  const [c, g] = canvas2d(270, 480);
  const mid = PAL.bg.clone().lerp(PAL.accent, tint);
  const grad = g.createRadialGradient(135, 190, 8, 135, 220, 340);
  grad.addColorStop(0, hex(mid));
  grad.addColorStop(1, hex(PAL.bg.clone().multiplyScalar(0.5)));
  g.fillStyle = grad;
  g.fillRect(0, 0, 270, 480);
  return { tex: texture(c), mid };
}

// A soft shadow on an invisible floor, under whatever stands on it.
let shadowTex;
function contactShadow(width, y, opacity = 0.5) {
  if (!shadowTex) {
    const [c, g] = canvas2d(128, 128);
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, 'rgba(0,0,0,1)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grad;
    g.fillRect(0, 0, 128, 128);
    shadowTex = new THREE.CanvasTexture(c);
  }
  const m = new THREE.Mesh(new THREE.PlaneGeometry(width, width * 0.5), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, opacity, depthWrite: false }));
  m.rotation.x = -Math.PI / 2;
  m.position.y = y;
  return m;
}

// A flat rounded rectangle, centered.
function roundedPlane(w, h, r) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2 + r, -h / 2);
  s.lineTo(w / 2 - r, -h / 2); s.absarc(w / 2 - r, -h / 2 + r, r, -Math.PI / 2, 0);
  s.lineTo(w / 2, h / 2 - r); s.absarc(w / 2 - r, h / 2 - r, r, 0, Math.PI / 2);
  s.lineTo(-w / 2 + r, h / 2); s.absarc(-w / 2 + r, h / 2 - r, r, Math.PI / 2, Math.PI);
  s.lineTo(-w / 2, -h / 2 + r); s.absarc(-w / 2 + r, -h / 2 + r, r, Math.PI, Math.PI * 1.5);
  return new THREE.ShapeGeometry(s, 12);
}

// A scene with the backdrop, the environment, a key light, and an accent rim light; and a
// camera whose view is shifted so the origin lands LIFT pixels above the middle of the frame.
function stage({ fov = 30, tint = 0.2, fog } = {}) {
  const scene = new THREE.Scene();
  const bd = backdrop(tint);
  scene.background = bd.tex;
  scene.environment = env;
  if (fog) scene.fog = new THREE.Fog(bd.mid, fog[0], fog[1]);
  const key = new THREE.DirectionalLight(0xffffff, 1.5);
  key.position.set(3, 5, 6);
  const rim = new THREE.DirectionalLight(PAL.accent, 2.4);
  rim.position.set(-4, 2, -5);
  scene.add(key, rim);
  const camera = new THREE.PerspectiveCamera(fov, W / H, 0.1, 200);
  camera.setViewOffset(W, H, 0, LIFT, W, H);
  return { scene, camera };
}
const aim = (camera, x, y, z, at = [0, 0, 0]) => { camera.position.set(x, y, z); camera.lookAt(...at); };

// An entrance: 0 to 1 over `d` seconds after `delay`, or 1 at once for the shot on the cover.
const entrance = (shot, lt, delay = 0, d = 0.7, ease = back) => (shot.first ? 1 : ease((lt - delay) / d));

// ---- the shots
const SHOTS = {};

// Glossy shapes floating in the brand's colors.
SHOTS.shapes = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.22 });
  const geo = {
    box: new RoundedBoxGeometry(1, 1, 1, 4, 0.18), torus: new THREE.TorusGeometry(0.6, 0.24, 32, 96),
    sphere: new THREE.SphereGeometry(0.62, 48, 32), ico: new THREE.IcosahedronGeometry(0.66, 0),
    capsule: new THREE.CapsuleGeometry(0.34, 0.6, 8, 32), cone: new THREE.ConeGeometry(0.55, 1, 48),
    knot: new THREE.TorusKnotGeometry(0.45, 0.15, 160, 20), octa: new THREE.OctahedronGeometry(0.62, 0),
  };
  const layout = [
    ['box', PAL.accent, -0.7, 0.95, 0.2, 0.42], ['torus', PAL.pearl, 0.8, 0.72, -0.5, 0.42],
    ['sphere', PAL.second, -0.08, 0.05, 0.8, 0.46], ['ico', PAL.third, 0.72, -0.55, 0.3, 0.34],
    ['capsule', PAL.pearl, -0.86, -0.48, -0.6, 0.36], ['cone', PAL.second, 0.15, 1.32, -1.0, 0.32],
    ['knot', PAL.accent, -0.38, -1.05, 0.5, 0.3], ['octa', PAL.accent, 0.98, 1.38, -0.4, 0.24],
  ];
  const r = rng(7);
  const items = layout.map(([kind, color, x, y, z, s], i) => {
    const m = new THREE.Mesh(geo[kind], kind === 'ico' || kind === 'octa' ? metal(color, 0.3) : glossy(color));
    m.position.set(x, y, z);
    scene.add(m);
    return { m, x, y, z, s, phase: r() * 6.28, spin: [(r() - 0.5) * 1.2, (r() - 0.5) * 1.4], delay: 0.05 * i };
  });
  return {
    scene, camera,
    update(lt) {
      for (const it of items) {
        it.m.scale.setScalar(it.s * entrance(shot, lt, it.delay, 0.6));
        it.m.position.y = it.y + 0.09 * Math.sin(lt * 1.1 + it.phase);
        it.m.rotation.set(it.phase + lt * it.spin[0], it.phase * 0.7 + lt * it.spin[1], 0);
      }
      const k = inOut(lt / shot.dur);
      aim(camera, 0.35 * Math.sin(lt * 0.35), 0.1, lerp(9.6, 8.6, k));
    },
  };
};

// A phone turning toward the camera, with the user's screenshot (data-src) on its screen.
SHOTS.hero = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.18 });
  const [w, h, radius] = [0.9, 1.9, 0.12];
  const [c, g] = canvas2d(600, 1300);
  g.beginPath();
  g.roundRect(0, 0, 600, 1300, 64);
  g.clip();
  let drawn = false;
  if (el.dataset.src) {
    const img = await loadImage(el.dataset.src);
    const k = Math.max(600 / img.width, 1300 / img.height); // cover the screen, cropping the overflow
    g.drawImage(img, (600 - img.width * k) / 2, 0, img.width * k, img.height * k);
    drawn = readable(g);
  }
  if (!drawn) { // a generic interface: header, cards, a button; no text, nothing to mistake for a real product
    const grad = g.createLinearGradient(0, 0, 0, 1300);
    grad.addColorStop(0, hex(PAL.bg.clone().lerp(PAL.accent, 0.18)));
    grad.addColorStop(1, hex(PAL.bg));
    g.fillStyle = grad;
    g.fillRect(0, 0, 600, 1300);
    g.fillStyle = hex(PAL.accent);
    g.beginPath(); g.roundRect(40, 110, 520, 220, 36); g.fill();
    g.fillStyle = 'rgba(255,255,255,.55)';
    g.beginPath(); g.roundRect(80, 160, 260, 30, 15); g.roundRect(80, 215, 180, 26, 13); g.fill();
    [PAL.second, PAL.third, PAL.pearl].forEach((col, i) => {
      const y = 380 + i * 200;
      g.fillStyle = 'rgba(255,255,255,.07)';
      g.beginPath(); g.roundRect(40, y, 520, 170, 30); g.fill();
      g.fillStyle = hex(col);
      g.beginPath(); g.arc(115, y + 85, 42, 0, 6.29); g.fill();
      g.fillStyle = 'rgba(255,255,255,.4)';
      g.beginPath(); g.roundRect(185, y + 52, 290, 24, 12); g.roundRect(185, y + 96, 200, 20, 10); g.fill();
    });
    g.fillStyle = hex(PAL.accent);
    g.beginPath(); g.roundRect(40, 1060, 520, 120, 60); g.fill();
  }
  const phone = new THREE.Group();
  phone.add(new THREE.Mesh(new RoundedBoxGeometry(w, h, 0.11, 6, radius), metal(PAL.accent, 0.3)));
  const bezel = new THREE.Mesh(roundedPlane(w - 0.04, h - 0.04, radius - 0.02), new THREE.MeshStandardMaterial({ color: 0x050507, roughness: 0.2 }));
  bezel.position.z = 0.0555;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.1, h - 0.1), new THREE.MeshBasicMaterial({ map: texture(c), transparent: true, toneMapped: false }));
  screen.position.z = 0.056;
  phone.add(bezel, screen);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.05, 0.024, 16, 160), glow(PAL.accent, 0.8));
  ring.position.z = -0.9;
  const orbs = [PAL.second, PAL.third, PAL.pearl].map((col, i) => {
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.1 + 0.03 * i, 32, 16), glossy(col));
    scene.add(m);
    return m;
  });
  scene.add(phone, ring, contactShadow(2.0, -h / 2 - 0.18, 0.55));
  const LAND = 0.9;
  return {
    scene, camera, events: { land: shot.first ? 0 : LAND },
    update(lt) {
      const k = entrance(shot, lt, 0, LAND, out3);
      phone.position.y = lerp(-3.4, 0, k) + 0.035 * Math.sin(lt * 1.4);
      phone.rotation.set(-0.06 + 0.03 * Math.sin(lt * 0.9), lerp(-0.55, 0.32, inOut(lt / shot.dur)) - (1 - k) * Math.PI, 0);
      ring.rotation.set(0.25 * Math.sin(lt * 0.5), 0.35 * Math.cos(lt * 0.4), lt * 0.3);
      ring.scale.setScalar(entrance(shot, lt, 0.2, 0.8));
      orbs.forEach((m, i) => {
        const a = lt * (0.6 + 0.15 * i) + i * 2.1;
        m.position.set(0.85 * Math.cos(a), 0.75 - 0.75 * i + 0.12 * Math.sin(a * 1.3), 0.5 * Math.sin(a) - 0.2);
        m.scale.setScalar(entrance(shot, lt, 0.4 + 0.1 * i, 0.5));
      });
      aim(camera, 0, 0.15, lerp(9, 8, inOut(lt / shot.dur)));
    },
  };
};

// Cards flying in and stacking, one per item of data-items.
SHOTS.cards = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.16 });
  const labels = (el.dataset.items || ',,').split(',').map((s) => s.trim()).slice(0, 5);
  await document.fonts.load(`800 110px ${FONT}`);
  const colors = [PAL.accent, PAL.second, PAL.third];
  const group = new THREE.Group();
  const step = labels.length > 3 ? 0.6 : 0.68;
  const cards = labels.map((label, i) => {
    const [c, g] = canvas2d(1024, 318);
    g.fillStyle = hex(PAL.pearl);
    g.beginPath(); g.roundRect(0, 0, 1024, 318, 44); g.fill();
    g.fillStyle = hex(colors[i % 3]);
    g.beginPath(); g.arc(160, 159, 88, 0, 6.29); g.fill();
    g.strokeStyle = '#fff'; g.lineWidth = 22; g.lineCap = 'round'; g.lineJoin = 'round';
    g.beginPath(); g.moveTo(118, 162); g.lineTo(148, 194); g.lineTo(206, 128); g.stroke();
    if (label) {
      let size = 110;
      g.font = `800 ${size}px ${FONT}`;
      while (g.measureText(label).width > 700 && size > 50) g.font = `800 ${(size -= 6)}px ${FONT}`;
      g.fillStyle = hex(PAL.ink);
      g.textBaseline = 'middle';
      g.fillText(label, 290, 165);
    } else {
      g.fillStyle = 'rgba(23,23,29,.18)';
      g.beginPath(); g.roundRect(290, 112, 520, 40, 20); g.roundRect(290, 178, 360, 32, 16); g.fill();
    }
    const card = new THREE.Group();
    card.add(new THREE.Mesh(new RoundedBoxGeometry(1.7, 0.527, 0.06, 4, 0.08), glossy(PAL.pearl, 0.35)));
    const face = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.527), new THREE.MeshBasicMaterial({ map: texture(c), transparent: true, toneMapped: false }));
    face.position.z = 0.031;
    card.add(face);
    group.add(card);
    return { card, y: ((labels.length - 1) / 2 - i) * step, x: i % 2 ? 0.07 : -0.07, delay: 0.15 + i * 0.32 };
  });
  group.scale.setScalar(Math.min(1, 2.0 / (0.527 + (labels.length - 1) * step)));
  scene.add(group, contactShadow(2.2, -1.2, 0.35));
  return {
    scene, camera,
    events: Object.fromEntries(cards.map((cd, i) => [`card-${i + 1}`, shot.first ? 0 : cd.delay + 0.2])),
    update(lt) {
      cards.forEach((cd, i) => {
        const k = entrance(shot, lt, cd.delay, 0.6);
        cd.card.position.set(lerp(3.2, cd.x, k), cd.y + 0.03 * Math.sin(lt * 1.3 + i), lerp(-2.5, 0, k));
        cd.card.rotation.set(0.05 * Math.sin(lt + i), lerp(-1.3, 0, k) + 0.14 * Math.sin(lt * 0.8 + i * 1.7), (i % 2 ? -1 : 1) * 0.03);
      });
      aim(camera, 0.5 * Math.sin(lt * 0.4), 0.25, lerp(8.6, 8.1, inOut(lt / shot.dur)));
    },
  };
};

// Bars growing to data-values: the user's real numbers, or a plain rising icon without them.
SHOTS.chart = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.16 });
  const given = (el.dataset.values || '').split(',').map(Number).filter((v) => Number.isFinite(v) && v >= 0).slice(0, 8);
  const values = given.length ? given : [2, 3, 5, 8];
  const max = Math.max(...values) || 1;
  const [bw, gap] = [0.34, 0.13];
  const span = values.length * bw + (values.length - 1) * gap;
  const base = new THREE.Mesh(new RoundedBoxGeometry(span + 0.5, 0.12, 0.95, 4, 0.05), glossy(PAL.ink, 0.4));
  base.position.y = -1.0;
  scene.add(base, contactShadow(span + 1.6, -1.07, 0.45));
  const top = values.indexOf(max);
  const bars = values.map((v, i) => {
    const m = new THREE.Mesh(new RoundedBoxGeometry(bw, 1, bw, 4, 0.06), i === top ? glossy(PAL.accent) : glossy(PAL.pearl, 0.35));
    m.position.x = -span / 2 + bw / 2 + i * (bw + gap);
    scene.add(m);
    return { m, h: Math.max(0.05, 1.7 * v / max), delay: (shot.first ? 0 : 0.2) + i * 0.18 };
  });
  const GROW = 0.8;
  return {
    scene, camera, events: { top: bars[bars.length - 1].delay + GROW },
    update(lt) {
      for (const b of bars) {
        const k = out3((lt - b.delay) / GROW);
        const h = Math.max(0.001, b.h * (shot.first ? lerp(0.35, 1, k) : k));
        b.m.scale.y = h;
        b.m.position.y = -0.94 + h / 2;
      }
      const a = lerp(-0.5, 0.3, inOut(lt / shot.dur));
      aim(camera, 8.6 * Math.sin(a), 1.4, 8.6 * Math.cos(a), [0, 0.1, 0]);
    },
  };
};

// A coin or badge spinning in and landing, with the logo (data-src) or a star on its face.
SHOTS.coin = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.24 });
  const [c, g] = canvas2d(1024, 1024);
  const grad = g.createRadialGradient(440, 400, 40, 512, 512, 520);
  grad.addColorStop(0, '#ffffff');
  grad.addColorStop(1, hex(PAL.pearl.clone().lerp(PAL.accent, 0.25)));
  g.fillStyle = grad;
  g.fillRect(0, 0, 1024, 1024);
  g.strokeStyle = hex(PAL.accent);
  g.lineWidth = 26;
  g.beginPath(); g.arc(512, 512, 430, 0, 6.29); g.stroke();
  let drawn = false;
  if (el.dataset.src) {
    const img = await loadImage(el.dataset.src);
    const k = Math.min(560 / img.width, 560 / img.height);
    g.drawImage(img, 512 - img.width * k / 2, 512 - img.height * k / 2, img.width * k, img.height * k);
    drawn = readable(g);
    if (!drawn) { g.fillStyle = grad; g.fillRect(0, 0, 1024, 1024); }
  }
  if (!drawn) {
    g.fillStyle = hex(PAL.accent);
    g.beginPath();
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 5;
      const r = i % 2 ? 130 : 300;
      g.lineTo(512 + r * Math.cos(a), 530 + r * Math.sin(a));
    }
    g.fill();
  }
  const face = new THREE.MeshStandardMaterial({ map: texture(c), metalness: 0.3, roughness: 0.35 });
  const rim = metal(PAL.accent, 0.22);
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.13, 96), [rim, face, face]);
  disc.rotation.set(Math.PI / 2, Math.PI / 2, 0); // a face toward the camera, upright
  const bevel = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.055, 16, 96), rim);
  const coin = new THREE.Group();
  coin.add(disc, bevel);
  const r = rng(3);
  const sparks = Array.from({ length: 14 }, (_, i) => {
    const m = new THREE.Mesh(new THREE.OctahedronGeometry(0.07, 0), glow(i % 2 ? PAL.pearl : PAL.accent, 1));
    scene.add(m);
    const a = (i / 14) * 6.28 + r() * 0.3;
    return { m, dir: [Math.cos(a), Math.sin(a)], speed: 1.6 + r() * 1.2 };
  });
  const wave = new THREE.Mesh(new THREE.TorusGeometry(1, 0.02, 8, 128), new THREE.MeshBasicMaterial({ color: PAL.accent, transparent: true, toneMapped: false }));
  scene.add(coin, wave, contactShadow(1.7, -1.15, 0.4));
  const LAND = shot.first ? 0 : 1.0;
  return {
    scene, camera, events: { land: LAND },
    update(lt) {
      const k = out3(lt / Math.max(LAND, 0.001));
      coin.position.y = (shot.first ? 0 : lerp(2.8, 0, k)) + 0.05 * Math.sin(lt * 1.5);
      coin.rotation.y = (shot.first ? 0 : (1 - k) * 4 * Math.PI) + 0.28 * Math.sin(Math.max(0, lt - LAND) * 1.2);
      coin.rotation.x = 0.06 * Math.sin(lt * 0.9);
      const after = lt - LAND;
      for (const s of sparks) {
        const d = after > 0 ? out3(after / 0.8) * s.speed : 0;
        s.m.position.set(s.dir[0] * (0.75 + d * 0.8), s.dir[1] * (0.75 + d * 0.8), 0.2);
        s.m.scale.setScalar(after > 0 && after < 0.8 ? 1 - after / 0.8 : 0.0001);
        s.m.rotation.set(lt * 3, lt * 2, 0);
      }
      wave.scale.setScalar(after > 0 ? lerp(0.8, 1.9, out3(after / 0.7)) : 0.0001);
      wave.material.opacity = after > 0 ? Math.max(0, 0.85 * (1 - after / 0.7)) : 0;
      aim(camera, 0, 0.1, lerp(8, 7.5, inOut(lt / shot.dur)));
    },
  };
};

// Flying through a tunnel of rings.
SHOTS.rings = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.3, fog: [3, 24] });
  const colors = [PAL.accent, PAL.pearl, PAL.second];
  const rings = Array.from({ length: 16 }, (_, i) => {
    const m = new THREE.Mesh(new THREE.TorusGeometry(1.25, i % 3 === 1 ? 0.045 : 0.075, 16, 120), glow(colors[i % 3], i % 3 === 1 ? 0.3 : 0.65));
    m.position.z = -i * 2.4;
    scene.add(m);
    return m;
  });
  const r = rng(11);
  const pts = new Float32Array(500 * 3);
  for (let i = 0; i < 500; i++) {
    const a = r() * 6.28;
    const d = 1.9 + r() * 2.5;
    pts.set([Math.cos(a) * d, Math.sin(a) * d, 6 - r() * 44], i * 3);
  }
  const dust = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(pts, 3)),
    new THREE.PointsMaterial({ color: PAL.pearl, size: 0.035 }));
  scene.add(dust);
  return {
    scene, camera,
    update(lt) {
      rings.forEach((m, i) => { m.rotation.z = i * 0.5 + lt * 0.5 * (i % 2 ? 1 : -1); });
      const z = lerp(6, -6 - 5 * shot.dur, inOut(lt / shot.dur) * 0.75 + (lt / shot.dur) * 0.25);
      camera.position.set(0.25 * Math.sin(lt * 0.8), 0.15 * Math.cos(lt * 0.7), z);
      camera.lookAt(0, 0, z - 10);
      camera.rotateZ(0.12 * Math.sin(lt * 0.6));
    },
  };
};

// A dotted globe, its land made-up blobs (not a map), with arcs rising between places.
SHOTS.globe = async (el, shot) => {
  const { scene, camera } = stage({ tint: 0.2 });
  const R = 0.85;
  const world = new THREE.Group();
  world.add(new THREE.Mesh(new THREE.SphereGeometry(R * 0.985, 64, 48), new THREE.MeshStandardMaterial({ color: PAL.bg.clone().lerp(PAL.accent, 0.08), roughness: 0.85, metalness: 0 })));
  const land = (p) => Math.sin(3.1 * p.x + 1.7) * Math.sin(2.3 * p.y + 0.4) * Math.sin(2.9 * p.z + 2.2) + 0.45 * Math.sin(5.3 * p.x + 4.1 * p.z) > 0.02;
  const dots = [];
  const N = 2000;
  const sea = PAL.bg.clone().lerp(PAL.pearl, 0.28);
  const pts = [];
  for (let i = 0; i < N; i++) {
    const y = 1 - (2 * (i + 0.5)) / N;
    const rr = Math.sqrt(1 - y * y);
    const a = i * 2.39996;
    const p = new THREE.Vector3(Math.cos(a) * rr, y, Math.sin(a) * rr);
    pts.push(p);
    if (land(p)) dots.push(p);
  }
  const dotMesh = new THREE.InstancedMesh(new THREE.SphereGeometry(0.013, 6, 4), new THREE.MeshBasicMaterial({ toneMapped: false }), pts.length);
  const mtx = new THREE.Matrix4();
  pts.forEach((p, i) => {
    const onLand = land(p);
    dotMesh.setMatrixAt(i, mtx.makeScale(onLand ? 1 : 0.6, onLand ? 1 : 0.6, onLand ? 1 : 0.6).setPosition(p.x * R, p.y * R, p.z * R));
    dotMesh.setColorAt(i, onLand ? PAL.pearl : sea);
  });
  world.add(dotMesh);
  const r = rng(5);
  const arcs = [];
  for (let tries = 0; arcs.length < 6 && tries < 400; tries++) {
    const a = dots[Math.floor(r() * dots.length)];
    const b = dots[Math.floor(r() * dots.length)];
    const ang = a.angleTo(b);
    if (ang < 0.6 || ang > 1.7 || a.z < -0.2 || b.z < -0.2) continue;
    const mid = a.clone().add(b).normalize().multiplyScalar(R * (1 + 0.3 * ang));
    const geo = new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(a.clone().multiplyScalar(R), mid, b.clone().multiplyScalar(R)), 64, 0.012, 6);
    const tube = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: PAL.accent, toneMapped: false }));
    const pin = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 8), new THREE.MeshBasicMaterial({ color: PAL.accent, toneMapped: false }));
    pin.position.copy(b).multiplyScalar(R);
    world.add(tube, pin);
    arcs.push({ geo, pin, delay: (shot.first ? 0 : 0.3) + arcs.length * 0.35 });
  }
  const [hc, hg] = canvas2d(256, 256);
  const halo = hg.createRadialGradient(128, 128, 60, 128, 128, 128);
  halo.addColorStop(0, hex(PAL.accent));
  halo.addColorStop(1, 'rgba(0,0,0,0)');
  hg.fillStyle = halo;
  hg.fillRect(0, 0, 256, 256);
  const aura = new THREE.Mesh(new THREE.PlaneGeometry(2.9, 2.9), new THREE.MeshBasicMaterial({ map: texture(hc), transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false }));
  aura.position.z = -1.3;
  scene.add(aura, world);
  const DRAW = 0.8;
  return {
    scene, camera,
    events: Object.fromEntries(arcs.map((a, i) => [`arc-${i + 1}`, a.delay + DRAW])),
    update(lt) {
      world.scale.setScalar(entrance(shot, lt, 0, 0.8));
      world.rotation.set(0.35, -0.5 + 0.3 * lt, 0);
      for (const a of arcs) {
        const k = out3((lt - a.delay) / DRAW);
        a.geo.setDrawRange(0, Math.floor((a.geo.index.count / 6) * k) * 6);
        a.pin.scale.setScalar(k >= 1 ? 1 + 0.25 * Math.sin((lt - a.delay - DRAW) * 6) : 0.0001);
      }
      aim(camera, 0, 0.1, lerp(8.2, 7.4, inOut(lt / shot.dur)));
    },
  };
};

""" + MASCOT_JS + CHARACTER_JS + DEMO_JS + r"""
// A screen shot (demo.py) hands the frame on without a cut: over HANDOVER seconds it pushes on
// through and fades while the next shot arrives. A desk pushing into a screen needs no handover:
// the screen already fills the frame when the desk ends.
const HANDOVER = 0.45;
const draw = (view, lt, shot) => {
  for (const s of timeline) if (s.view && s.view.screen) s.view.screen.hide();
  document.body.dataset.tone = view.tone || 'dark'; // a light set gets a lighter scrim behind the captions
  const prev = timeline[timeline.indexOf(shot) - 1];
  const k = lt / HANDOVER;
  const handing = !!prev && !!prev.view && k < 1 && !!(view.screen || prev.view.screen) && !(prev.view.into && view.screen);
  if (view.screen) {
    if (handing && prev.view.screen) prev.view.show(prev.dur + lt, { leave: k });
    else if (handing) { prev.view.update(prev.dur + lt); renderer.render(prev.view.scene, prev.view.camera); }
    view.show(lt, handing ? { arrive: k } : {});
    return;
  }
  view.update(lt);
  renderer.render(view.scene, view.camera);
  if (handing) prev.view.show(prev.dur + lt, { leave: k });
};
"""

LINES = [
    (0.2, "Marketing is a hundred small jobs a week."),
    (3.4, "This plugin does them in one place."),
    (6.4, "It even renders your videos, right on your machine."),
    (10.0, "Then sends them to TikTok, Reels, and Shorts when you approve."),
    (14.0, "Free and open source. Link in bio."),
]

SCENE3D_TEMPLATES = {}
SCENE3D_TEMPLATES["3d.html"] = dict(
    bgs=[],
    g1="#000", g2="#000",
    doc=f"""  Template: 3D animation, narrated (references/video-types.md: explainer,
  ad, launch, brand profile, educational). 17 seconds: a voiceover over 3D
  scenes drawn with three.js in the brand's colors, word-by-word captions
  synced to the voice, and the hook on screen from the very first frame.

  The brand's mascot presents: a robot in the brand's colors that walks, waves,
  lip-syncs to the voice, and holds up the user's own screen, in a light studio
  or at a desk at night (the mascot, desk, and title shots below).

  Usually made by scripts/video/compose.js with "style: 3d" in the script's
  frontmatter: it voices the script, gives each line a shot ([shot: hero] on
  a line picks one), times everything to the voice, and writes this page.
  By hand: each line is a scene holding
    <div class="say auto" data-voice="assets/voice-2.wav" style="--voice:3.4s">The line.</div>
  and each shot is an empty <div class="shot" data-shot="..." style="--in:3.4s">,
  usually one per line. Without a voice clip, the captions here run at a
  steady reading pace, as a preview.

{SHOT_DOC}

  How it draws: the page defines window.renderFrame(t), which render.js calls
  with the time of every frame, so the 3D is frame-exact like the CSS. three.js
  {THREE_VERSION} comes from scripts/video/node_modules (npm install), or from
  jsDelivr when the page is opened in a browser. Colors come from --accent and
  --bg, so brand.js restyles the 3D too. Screenshots and logos must be the
  user's real ones; the shots never show people (the mascot is the brand's
  robot, never a stand-in for a customer or a team member).""",
    body_attrs='class="fyp" data-duration="17" data-drop="3.4" data-music="tech" data-bpm="112" data-key="C" data-mode="major" data-energy="2" data-motif="1 5 3 5 | 6 5 3 2"',
    css=NARRATED_CSS + """  .art-scrim { position: absolute; inset: 0; pointer-events: none;
               background: linear-gradient(to bottom, rgba(0,0,0,.28), rgba(0,0,0,0) 22%, rgba(0,0,0,0) 56%, rgba(0,0,0,.5) 78%, rgba(0,0,0,.3)); }
  body[data-tone="light"] .art-scrim { opacity: .4; }
""" + DEMO_CSS,
    head_extra=f"""<script type="importmap">{{"imports": {{"three": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/"}}}}</script>
<script type="module">{ENGINE_JS}{TIMELINE_JS}</script>
""",
    body=drawn_body(
        '<canvas class="art" width="1080" height="1920" data-lint="off"></canvas>',
        [(0, "mascot", ' data-do="wave"'),
         (3.4, "desk", ' data-sfx="whoosh:enter"'),
         (6.4, "mascot", ' data-do="present" data-prop="screen"'),
         (10.0, "title", ' data-text="Posted" data-sfx="pop:letter-1 pop:done"'),
         (14.0, "mascot", ' data-do="cheer" data-sfx="pop:land"')],
        LINES, "your whole week of marketing, done", "free on GitHub · link in bio"),
)
