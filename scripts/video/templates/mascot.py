"""The 3D mascot for the 3D template (3d.html): a robot that walks, waves, talks with the voice,
points at things, and holds up the user's own phone screen, laptop screen, or sign. scene3d.py
appends MASCOT_JS to its engine, so the mascot shot and the desk shot share its stage, lights,
and helpers.

The robot is built from primitives in the brand's colors and posed with a small rig: each joint
is a group, the arms and legs are solved with two-bone IK from hand and foot targets, and every
action is a pure function of time, so render.js can seek any frame exactly and render frames in
parallel. Its mouth moves with the words of the captions (their --in/--done times, which
render.js sets from the voice), so it lip-syncs to whatever voiceover the page has.
"""

MASCOT_DOC = """    mascot  the brand's robot mascot, alive: it blinks, breathes, lip-syncs to
            the voice, and gestures on the words. data-do picks the action:
              wave (hi; the default first shot), talk (presenting), point (at
              the screen prop), present (ta-da), cheer (jumps, confetti),
              think, shrug, sad (the problem, under a rain cloud), walk (walks
              in), dance (on the music's beat), thumbs, wow.
            data-prop puts something in its hands: phone or laptop (data-src
            = the user's real screenshot), sign (data-text, or data-src for
            their logo), screen (data-src floating beside it, for point and
            present). data-set picks the place: "room" (a living room by
            day), "stage" (an LED wall and light beams), "city" (a rooftop
            at dusk), "park" (sky, hills, trees), "studio" (light and
            seamless), or "night"; without one, shots take the room, stage,
            city, and park in turn. data-bg="assets/photo.jpg" stands it in
            front of the user's own photo instead, softly blurred (title,
            icons, and button take data-set and data-bg too). data-face overrides the
            expression (happy, wow, love, sad, think, wink); data-frame="full",
            "mid" (waist up), or "wide". data-talk="no" keeps its mouth shut
            when the voice isn't the mascot's. Events: --jump and --land
            (cheer), --stop (walk), --point, --open (present), --show (a prop
            held up).
    desk    a cozy desk at night: the mascot types at a monitor showing the
            user's real screenshot (data-src), turns to wave, and the camera
            pushes in and flies into the screen. data-mascot="no" leaves the
            chair empty. Events: --turn, --enter (into the screen).
    title   big 3D letters dropping onto the studio floor one by one:
            data-text (one to three short words), with the mascot beside it
            unless data-mascot="no". Events: --letter-1, --letter-2..., --done.
    icons   app tiles dropping into a grid, one per item, a small mascot
            waving in the last cell: data-items="🔍 Research,📅 Calendar"
            (an emoji, then a short label; up to 8, or 9 with
            data-mascot="no"). For a product's features, a plugin's skills,
            the tools it works with. Events: --tile-1, --tile-2..., --done.
    notes   sticky notes floating in the dark, the camera drifting through
            them: data-items="a launch video,a week of posts" (up to 8,
            handwritten). Ideas, requests, a week's plan; never quotes from
            people who didn't say them. data-set="studio" for a light room.
            Events: --note-1, --note-2...
    button  a big button a cursor clicks, the label changing from data-text
            to data-done ("☆ Star" to "★ Starred", "+ Follow" to
            "Following") under confetti, the mascot pointing up at it then
            cheering. The call to action. Event: --click."""

MASCOT_JS = r"""
// ================= the mascot: the brand's robot, rigged, lip-synced, and holding the user's things =================

const BONES = { thigh: 0.27, shin: 0.25, upper: 0.28, fore: 0.27 };
const ANKLE = 0.115; // the ankle's height with the boot flat on the floor
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
// framings: world heights (feet to antenna) to pixel rows; the low ones leave room for a hook or CTA at the top
const SPAN = { full: [-0.02, 2.3, 430, 1330], low: [-0.02, 2.3, 620, 1390], mid: [0.55, 2.3, 400, 1290], midLow: [0.55, 2.3, 560, 1400], wide: [-0.02, 2.3, 520, 1300] };
const HAND = '"Caveat", cursive'; // the handwriting on the notes
const PAL_EYE = new THREE.Color().setHSL((hsl.h + 0.5) % 1, 0.95, 0.74, SRGB);
const plastic = (c, rough = 0.3) => new THREE.MeshPhysicalMaterial({ color: c, roughness: rough, metalness: 0, clearcoat: 0.9, clearcoatRoughness: 0.18 });
const smooth = (x, a, b) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
const pulse = (x, a, b, c, d) => smooth(x, a, b) * (1 - smooth(x, c, d));
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const DOWN = V(0, -1, 0);
const UP = V(0, 1, 0);

// ---- poses: plain numbers, so any two mix. Hands are IK targets in chest space (+x is the
// mascot's left, which is the viewer's right), feet are ankle targets in the root's space.
const REST = {
  x: 0, y: 0, z: 0, turn: 0, bob: 0, squash: 0,
  lean: [0, 0], chest: [0, 0, 0], head: [0, 0, 0], shrug: 0,
  handL: [0.45, -0.34, 0.07], handR: [-0.45, -0.34, 0.07],
  footL: [0.15, ANKLE, 0.02], footR: [-0.15, ANKLE, 0.02], toeL: 0, toeR: 0,
  finger: [0, 0], thumb: [0, 0], look: [0, 0], face: 'normal',
};
function mixPose(a, b, k) {
  if (k <= 0) return a;
  if (k >= 1) return { ...a, ...b };
  const out = { ...a };
  for (const [key, v] of Object.entries(b)) {
    const from = a[key] !== undefined ? a[key] : REST[key];
    if (from === undefined) out[key] = v; // a setting only one side has (an elbow's pole): no blend
    else if (Array.isArray(v)) out[key] = v.map((x, i) => lerp(from[i], x, k));
    else if (typeof v === 'number') out[key] = lerp(from, v, k);
    else out[key] = k < 0.5 ? from : v;
  }
  return out;
}
// keyframes [[time, partial pose], ...], each eased into the next; holds the last
function track(keys, lt, base = REST) {
  let pose = mixPose(base, keys[0][1], 1);
  for (let i = 1; i < keys.length; i++) {
    const [t0] = keys[i - 1];
    const [t1, p] = keys[i];
    if (lt <= t0) break;
    pose = mixPose(pose, p, inOut((lt - t0) / Math.max(0.001, t1 - t0)));
  }
  return pose;
}

// ---- what the voice is doing: the caption words' times (render.js writes them from the voice)
let wordsCache = { count: -1, list: [] };
function spokenWords() {
  const els = document.querySelectorAll('.say i');
  if (els.length !== wordsCache.count) {
    const sec = (v) => { v = (v || '').trim(); return v.endsWith('ms') ? parseFloat(v) / 1000 : parseFloat(v); };
    wordsCache = {
      count: els.length,
      list: [...els].map((w) => ({ in: sec(w.style.getPropertyValue('--in')), done: sec(w.style.getPropertyValue('--done')), n: w.textContent.replace(/[^\p{L}\p{N}]/gu, '').length }))
        .filter((w) => Number.isFinite(w.in) && Number.isFinite(w.done) && w.done > w.in).sort((a, b) => a.in - b.in),
    };
  }
  return wordsCache.list;
}
// how open the mouth is at time t: a syllable or so per three letters of the word being said
function mouthAt(t, words) {
  for (const w of words) {
    if (w.in > t) break;
    if (t < w.done + 0.03) {
      const syl = Math.max(1, Math.round(w.n / 3));
      const ph = clamp((t - w.in) / (w.done - w.in)) * syl;
      return 0.2 + 0.8 * Math.sin(Math.PI * (ph % 1)) ** 0.7;
    }
  }
  return 0;
}
// a gesture beat: decays after each longer word starts; side alternates
function beatAt(t, words) {
  let out = 0, side = 1, n = 0;
  for (const w of words) {
    if (w.in > t) break;
    if (w.n < 4) continue;
    n++;
    const age = t - w.in;
    if (age < 1.2) { const k = Math.exp(-age * 4) * Math.min(1, age * 14); if (k > out) { out = k; side = n % 2 ? 1 : -1; } }
  }
  return [out, side];
}

// ---- the face: drawn each frame on the visor
function drawFace(g, f) {
  const [W2, H2] = [512, 328];
  g.clearRect(0, 0, W2, H2);
  const col = hex(PAL_EYE);
  g.save();
  g.shadowColor = col; g.shadowBlur = 22;
  g.fillStyle = col; g.strokeStyle = col; g.lineCap = 'round'; g.lineJoin = 'round';
  const lx = f.look[0] * 26, ly = -f.look[1] * 18;
  const eyes = [[180 + lx, 132 + ly], [332 + lx, 132 + ly]];
  const blink = clamp(f.blink);
  const pill = (x, y, w, h) => { g.beginPath(); g.roundRect(x - w / 2, y - h / 2, w, Math.max(6, h), w / 2); g.fill(); };
  const arc = (x, y) => { g.lineWidth = 22; g.beginPath(); g.arc(x, y + 22, 38, Math.PI * 1.13, Math.PI * 1.87); g.stroke(); };
  const heart = (x, y, s) => {
    g.beginPath(); g.moveTo(x, y + s * 0.62);
    g.bezierCurveTo(x - s * 1.1, y - s * 0.1, x - s * 0.55, y - s * 0.95, x, y - s * 0.38);
    g.bezierCurveTo(x + s * 0.55, y - s * 0.95, x + s * 1.1, y - s * 0.1, x, y + s * 0.62); g.fill();
  };
  const e = f.face;
  eyes.forEach(([x, y], i) => {
    if (e === 'happy' || (e === 'wink' && i === 1)) arc(x, y);
    else if (e === 'love') { g.fillStyle = '#ff6b8a'; g.shadowColor = '#ff6b8a'; heart(x, y + 6, 58); g.fillStyle = col; g.shadowColor = col; }
    else if (e === 'wow') { g.lineWidth = 18; g.beginPath(); g.arc(x, y, 44 * (1 - blink * 0.9), 0, 6.29); g.stroke(); g.beginPath(); g.arc(x, y, 12, 0, 6.29); g.fill(); }
    else {
      const h = (e === 'think' && i === 0 ? 70 : e === 'meh' ? 52 : 104) * (1 - blink * 0.94);
      pill(x, y + (e === 'meh' ? 24 : 0), 66, h);
      if (e === 'sad' || e === 'meh') { // a drooping lid
        g.save(); g.globalCompositeOperation = 'destination-out'; g.shadowBlur = 0; g.beginPath();
        const s = i ? -1 : 1; // the inner corners raised
        if (e === 'sad') { g.moveTo(x - 50, y - 70 + s * 26); g.lineTo(x + 50, y - 70 - s * 26); g.lineTo(x + 50, y - 26 - s * 26); g.lineTo(x - 50, y - 26 + s * 26); }
        else { g.rect(x - 50, y - 70, 100, 62); }
        g.fill(); g.restore();
      }
    }
  });
  // the mouth: open while a word is being said, otherwise the expression's
  const [mx, my] = [256 + lx * 0.6, 250 + ly * 0.5];
  g.lineWidth = 14;
  if (f.mouth > 0.04) {
    const o = clamp(f.mouth);
    g.beginPath(); g.ellipse(mx, my, 34 - 8 * o, 6 + 30 * o, 0, 0, 6.29); g.fill();
  } else if (e === 'wow') { g.beginPath(); g.ellipse(mx, my + 4, 15, 21, 0, 0, 6.29); g.fill(); }
  else if (e === 'sad') { g.beginPath(); g.arc(mx, my + 36, 30, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); }
  else if (e === 'think' || e === 'meh') { g.beginPath(); g.moveTo(mx - 22, my + 4); g.lineTo(mx + 26, my - 2); g.stroke(); }
  else { g.beginPath(); g.arc(mx, my - 18, 30, Math.PI * 0.18, Math.PI * 0.82); g.stroke(); }
  g.restore();
  const sheen = g.createLinearGradient(0, 0, 220, 330); // the glass's soft reflection
  sheen.addColorStop(0, 'rgba(255,255,255,.10)'); sheen.addColorStop(0.45, 'rgba(255,255,255,.04)'); sheen.addColorStop(0.46, 'rgba(255,255,255,0)');
  g.fillStyle = sheen; g.fillRect(0, 0, W2, H2);
  if (e === 'happy' || e === 'love' || e === 'wink') { // blush
    g.fillStyle = 'rgba(255,120,150,.32)';
    g.beginPath(); g.ellipse(112, 226, 34, 18, 0, 0, 6.29); g.ellipse(400, 226, 34, 18, 0, 0, 6.29); g.fill();
  }
}

// ---- the robot
function buildMascot() {
  const shell = plastic(PAL.pearl, 0.26);
  const body = plastic(PAL.accent, 0.3);
  const dark = new THREE.MeshPhysicalMaterial({ color: PAL.ink, roughness: 0.4, clearcoat: 0.6, clearcoatRoughness: 0.3 });
  const glowMat = new THREE.MeshBasicMaterial({ color: PAL_EYE, toneMapped: false });
  const j = {};
  const joint = (name, parent, x, y, z) => { const g = new THREE.Group(); g.position.set(x, y, z); if (parent) j[parent].add(g); j[name] = g; return g; };
  const mesh = (parent, geo, mat, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; j[parent].add(m); return m; };
  joint('root', null, 0, 0, 0);
  joint('squash', 'root', 0, 0, 0);
  joint('hips', 'squash', 0, 0.62, 0);
  joint('spine', 'hips', 0, 0.04, 0);
  joint('chest', 'spine', 0, 0.33, 0);
  joint('neck', 'chest', 0, 0.26, 0);
  joint('head', 'neck', 0, 0.05, 0);
  joint('antenna', 'head', 0, 0.7, 0);

  // body: a soft pear of the accent color, a pearl belly panel with a glowing core
  const profile = new THREE.SplineCurve([V(0.0, -0.1), V(0.27, -0.07), V(0.36, 0.08), V(0.375, 0.24), V(0.34, 0.4), V(0.26, 0.52), V(0.12, 0.6), V(0.0, 0.62)])
    .getPoints(40).map((p) => new THREE.Vector2(Math.max(0, p.x), p.y));
  mesh('spine', new THREE.LatheGeometry(profile, 56), body);
  const panel = mesh('spine', new RoundedBoxGeometry(0.4, 0.3, 0.06, 4, 0.05), shell, 0, 0.24, 0.335);
  panel.rotation.x = -0.08;
  const core = mesh('spine', new THREE.TorusGeometry(0.065, 0.018, 12, 40), glowMat, 0, 0.245, 0.37);
  core.rotation.x = -0.08;
  mesh('spine', new THREE.SphereGeometry(0.03, 16, 12), glowMat, 0, 0.245, 0.368);
  mesh('neck', new THREE.CylinderGeometry(0.09, 0.11, 0.12, 24), dark, 0, 0.0, 0);

  // head: a rounded pearl box, a dark glass visor with the face drawn on it, ears, an antenna
  mesh('head', new RoundedBoxGeometry(0.94, 0.7, 0.7, 6, 0.13), shell, 0, 0.35, 0);
  const visor = mesh('head', roundedPlane(0.76, 0.48, 0.12), new THREE.MeshBasicMaterial({ color: 0x0b0c10 }), 0, 0.35, 0.3515); // unlit: a flat glossy visor would mirror the key light white
  visor.castShadow = false;
  const [fc, fg] = canvas2d(512, 328);
  const faceTex = texture(fc);
  const face = mesh('head', new THREE.PlaneGeometry(0.72, 0.46), new THREE.MeshBasicMaterial({ map: faceTex, transparent: true, toneMapped: false, depthWrite: false }), 0, 0.35, 0.353);
  face.castShadow = false;
  for (const s of [1, -1]) {
    const ear = mesh('head', new THREE.CylinderGeometry(0.12, 0.12, 0.08, 32), body, s * 0.485, 0.36, 0);
    ear.rotation.z = Math.PI / 2;
    const cap = mesh('head', new THREE.CylinderGeometry(0.06, 0.06, 0.03, 24), dark, s * 0.535, 0.36, 0);
    cap.rotation.z = Math.PI / 2;
  }
  mesh('antenna', new THREE.CylinderGeometry(0.018, 0.024, 0.18, 12), dark, 0, 0.09, 0);
  const bulb = mesh('antenna', new THREE.SphereGeometry(0.062, 24, 16), glow(PAL.accent, 1.1), 0, 0.2, 0);

  // limbs: arms of the accent color with pearl mitten hands (a finger and a thumb that come out
  // for pointing and thumbs up), stubby legs with dark boots
  const limb = (r, len) => new THREE.CapsuleGeometry(r, len, 6, 20);
  const hands = {};
  for (const [s, side] of [['L', 1], ['R', -1]]) {
    joint('sh' + s, 'chest', side * 0.33, 0.13, 0);
    joint('el' + s, 'sh' + s, 0, -BONES.upper, 0);
    joint('ha' + s, 'el' + s, 0, -BONES.fore, 0);
    mesh('sh' + s, new THREE.SphereGeometry(0.095, 24, 16), body);
    mesh('sh' + s, limb(0.07, BONES.upper - 0.06), body, 0, -BONES.upper / 2, 0);
    mesh('el' + s, limb(0.064, BONES.fore - 0.06), shell, 0, -BONES.fore / 2, 0);
    mesh('ha' + s, new THREE.SphereGeometry(0.1, 24, 16), shell, 0, -0.04, 0);
    const finger = new THREE.Group(); finger.position.set(0, -0.08, 0.0); j['ha' + s].add(finger);
    const fm = new THREE.Mesh(limb(0.032, 0.09), shell); fm.position.y = -0.07; fm.castShadow = true; finger.add(fm);
    const thumb = new THREE.Group(); thumb.position.set(0, -0.03, 0); j['ha' + s].add(thumb);
    const tm = new THREE.Mesh(limb(0.034, 0.06), shell); tm.position.y = 0.07; tm.castShadow = true; thumb.add(tm);
    hands[s] = { finger, thumb };

    joint('hip' + s, 'hips', side * 0.15, -0.02, 0);
    joint('kn' + s, 'hip' + s, 0, -BONES.thigh, 0);
    joint('ft' + s, 'kn' + s, 0, -BONES.shin, 0);
    mesh('hip' + s, limb(0.085, BONES.thigh - 0.04), body, 0, -BONES.thigh / 2, 0);
    mesh('kn' + s, limb(0.075, BONES.shin - 0.06), shell, 0, -BONES.shin / 2, 0);
    mesh('ft' + s, new RoundedBoxGeometry(0.21, 0.12, 0.3, 4, 0.05), dark, 0, -0.045, 0.04);
    mesh('ft' + s, new RoundedBoxGeometry(0.22, 0.03, 0.31, 2, 0.012), shell, 0, -ANKLE + 0.015, 0.04);
  }
  return { root: j.root, j, hands, faceCanvas: fg, faceTex, bulb };
}

// two-bone IK: turns j1 and j2 so the chain's end reaches `target` (in j1's parent space),
// with the middle joint bending toward `pole` (a direction)
const _q = new THREE.Quaternion();
function reach(j1, j2, a, b, target, pole) {
  const d = target.clone().sub(j1.position);
  const len = Math.min(Math.max(d.length(), Math.abs(a - b) + 1e-3), a + b - 1e-3);
  const dir = d.normalize();
  const cosA = (a * a + len * len - b * b) / (2 * a * len);
  const p = pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir))).normalize();
  const elbow = dir.clone().multiplyScalar(a * cosA).add(p.multiplyScalar(a * Math.sqrt(Math.max(0, 1 - cosA * cosA))));
  j1.quaternion.setFromUnitVectors(DOWN, elbow.clone().normalize());
  const fore = dir.multiplyScalar(len).sub(elbow).normalize().applyQuaternion(_q.copy(j1.quaternion).invert());
  j2.quaternion.setFromUnitVectors(DOWN, fore);
}

const _m = new THREE.Matrix4();
const _wq = new THREE.Quaternion();
function applyPose(rig, pose) {
  const { j } = rig;
  j.root.position.set(pose.x, pose.y, pose.z);
  j.root.rotation.set(0, pose.turn, 0);
  j.squash.scale.set(1 + pose.squash * 0.5, 1 - pose.squash, 1 + pose.squash * 0.5);
  j.hips.position.y = 0.62 + pose.bob;
  j.hips.rotation.set(0, 0, 0);
  j.spine.rotation.set(pose.lean[0], 0, pose.lean[1]);
  j.chest.rotation.set(...pose.chest);
  j.head.rotation.set(pose.head[0], pose.head[1], pose.head[2]);
  j.neck.rotation.set(0, 0, 0);
  j.shL.position.y = j.shR.position.y = 0.13 + pose.shrug * 0.07;
  // arms, in chest space
  reach(j.shL, j.elL, BONES.upper, BONES.fore, V(...pose.handL), pose.poleL ? V(...pose.poleL) : V(0.55, -0.35, -0.75));
  reach(j.shR, j.elR, BONES.upper, BONES.fore, V(...pose.handR), pose.poleR ? V(...pose.poleR) : V(-0.55, -0.35, -0.75));
  // legs: foot targets in the root's space, into the hips' space
  j.squash.updateMatrix(); j.hips.updateMatrix();
  _m.multiplyMatrices(j.squash.matrix, j.hips.matrix).invert();
  for (const s of ['L', 'R']) {
    const f = pose['foot' + s];
    reach(j['hip' + s], j['kn' + s], BONES.thigh, BONES.shin, V(...f).applyMatrix4(_m), V(s === 'L' ? 0.12 : -0.12, 0, 1));
  }
  j.root.updateMatrixWorld(true);
  const rootQ = j.root.getWorldQuaternion(new THREE.Quaternion()).invert();
  for (const [i, s] of [[0, 'L'], [1, 'R']]) {
    // boots stay flat to the floor, tipping on their toes when asked
    const kq = j['kn' + s].getWorldQuaternion(_wq).premultiply(rootQ);
    j['ft' + s].quaternion.copy(kq.invert()).multiply(_q.setFromAxisAngle(V(1, 0, 0), pose['toe' + s]));
    // the finger points along the forearm; the thumb points up
    rig.hands[s].finger.scale.setScalar(Math.max(0.001, pose.finger[i]));
    rig.hands[s].thumb.scale.setScalar(Math.max(0.001, pose.thumb[i]));
    if (pose.thumb[i] > 0.001) {
      const hq = j['ha' + s].getWorldQuaternion(_wq);
      rig.hands[s].thumb.quaternion.setFromUnitVectors(UP, UP.clone().applyQuaternion(hq.invert()));
    }
  }
}

// ---- life on top of any action: breathing, a little weight shift, glances
function alive(p, lt, seed, amount = 1) {
  const b = Math.sin(lt * 2.1 + seed);
  return {
    ...p,
    bob: p.bob + 0.008 * b * amount,
    chest: [p.chest[0] - 0.02 * b * amount, p.chest[1] + 0.03 * Math.sin(lt * 0.7 + seed) * amount, p.chest[2] + 0.025 * Math.sin(lt * 0.9 + seed * 2) * amount],
    head: [p.head[0] + 0.025 * Math.sin(lt * 1.3 + seed) * amount, p.head[1] + 0.05 * Math.sin(lt * 0.6 + seed * 3) * amount, p.head[2] + 0.03 * Math.sin(lt * 0.8 + seed) * amount],
    lean: [p.lean[0], p.lean[1] + 0.015 * Math.sin(lt * 0.5 + seed) * amount],
  };
}

// presenting: hands loose in front, a beat gesture on the longer words
function talking(p, t, words, amount = 1) {
  const [k, side] = beatAt(t, words);
  const g = k * amount;
  const out = { ...p };
  const hand = side > 0 ? 'handL' : 'handR';
  const s = side > 0 ? 1 : -1;
  out[hand] = [p[hand][0] + s * 0.1 * g, p[hand][1] + 0.16 * g, p[hand][2] + 0.1 * g];
  out.head = [p.head[0] + 0.07 * g, p.head[1] - s * 0.05 * g, p.head[2]];
  out.chest = [p.chest[0] + 0.03 * g, p.chest[1] + s * 0.05 * g, p.chest[2]];
  return out;
}
const TALK = { handL: [0.3, -0.16, 0.3], handR: [-0.3, -0.16, 0.3], poleL: [0.7, -0.5, -0.4], poleR: [-0.7, -0.5, -0.4] };

// ---- the actions: each (lt, ctx) => pose, where lt is seconds into the shot
const ACTIONS = {
  talk(lt, c) { return talking(track([[0, TALK]], lt), c.t, c.words); },

  wave(lt, c) {
    const up = pulse(lt, -1, 0.35, 2.1, 2.5);
    const w = Math.sin(lt * 10.5);
    const p = mixPose(talking(mixPose(REST, TALK, smooth(lt, 2.1, 2.6)), c.t, c.words, smooth(lt, 2.3, 2.8)), {
      handR: [-0.76 - 0.07 * w, 0.36 + 0.03 * Math.abs(w), 0.14], poleR: [-0.3, -1, 0.1], chest: [0, 0.08, -0.07], head: [0.02, 0.06, 0.1], face: 'happy',
    }, up);
    return { ...p, bob: p.bob - 0.02 * up * Math.abs(Math.sin(lt * 5.25)), face: lt < 2.2 ? 'happy' : p.face };
  },

  point(lt, c) {
    const side = c.propSide;
    const aim = pulse(lt, 0.05, 0.45, 99, 100);
    const look = pulse(lt, 0.2, 0.55, 1.5, 1.9);
    const hand = side > 0 ? 'handL' : 'handR';
    const p = mixPose(talking(TALK_POSE(), c.t, c.words, 1 - aim), {
      [hand]: [side * 0.74, 0.18, 0.3], [side > 0 ? 'poleL' : 'poleR']: [side * 0.2, -1, -0.3],
      finger: side > 0 ? [1, 0] : [0, 1], chest: [0, side * 0.22, 0], lean: [0, -side * 0.03],
    }, aim);
    p.head = [p.head[0] + 0.05 * look, p.head[1] + side * 0.6 * look, p.head[2] - side * 0.06 * look];
    p.look = [side * look, 0.1 * look];
    return p;
  },

  present(lt, c) {
    const open = smooth(lt, 0.1, 0.55);
    const side = c.propSide || 0;
    const p = mixPose(TALK_POSE(), {
      handL: [0.62, 0.02 + (side > 0 ? 0.12 : 0), 0.22], handR: [-0.62, 0.02 + (side < 0 ? 0.12 : 0), 0.22],
      poleL: [0.3, -1, -0.2], poleR: [-0.3, -1, -0.2], lean: [-0.06, -side * 0.04], chest: [-0.05, side * 0.15, 0], head: [-0.06, side * 0.35, 0], face: 'happy',
    }, open);
    p.look = [side * 0.7 * pulse(lt, 0.2, 0.5, 1.4, 1.8), 0];
    p.head = [p.head[0], p.head[1] * (1 - smooth(lt, 1.4, 1.9) * 0.8), p.head[2]];
    return talking(p, c.t, c.words, smooth(lt, 1.2, 1.8) * 0.6);
  },

  cheer(lt, c) {
    const jumps = [0.35, 1.9];
    let p = mixPose(REST, { handL: [0.36, -0.2, -0.12], handR: [-0.36, -0.2, -0.12], bob: -0.1, squash: 0.08, lean: [0.12, 0], face: 'happy' }, pulse(lt, 0, 0.3, 0.32, 0.45));
    let air = 0;
    for (const t0 of jumps) {
      const u = (lt - t0) / 0.5;
      if (u > 0 && u < 1) air = Math.max(air, 4 * u * (1 - u));
    }
    const arms = smooth(lt, 0.3, 0.5);
    const pump = 0.06 * Math.sin(lt * 9) * smooth(lt, 0.9, 1.2);
    p = mixPose(p, { handL: [0.68, 0.48 + pump, 0.06], handR: [-0.68, 0.48 - pump, 0.06], poleL: [0.6, -1, 0], poleR: [-0.6, -1, 0], face: lt > 1.0 ? 'love' : 'happy' }, arms);
    const land = jumps.reduce((m, t0) => Math.max(m, pulse(lt, t0 + 0.48, t0 + 0.52, t0 + 0.56, t0 + 0.8)), 0);
    p.y = 0.55 * air;
    p.squash = p.squash - 0.1 * air + 0.12 * land;
    p.bob = p.bob - 0.1 * land;
    p.footL = [0.15, ANKLE + 0.08 * air, 0.02 - 0.05 * air]; p.footR = [-0.15, ANKLE + 0.08 * air, 0.02 - 0.05 * air];
    p.head = [p.head[0] - 0.15 * air, p.head[1], p.head[2]];
    return p;
  },

  think(lt, c) {
    const k = smooth(lt, 0, 0.5);
    const p = mixPose(REST, {
      handR: [-0.13, 0.27, 0.3], poleR: [-0.6, -0.7, -0.1], handL: [0.08, -0.06, 0.3], poleL: [0.8, -0.5, -0.2],
      head: [0.12, -0.18, 0.16], chest: [0.04, -0.08, 0.04], lean: [0.02, 0.03], face: 'think',
    }, k);
    p.look = [0.5 * k, 0.7 * k];
    p.head = [p.head[0] + 0.03 * Math.sin(lt * 2.4), p.head[1], p.head[2]];
    return p;
  },

  shrug(lt, c) {
    const k = pulse(lt, 0.05, 0.35, 1.7, 2.1);
    const p = mixPose(talking(TALK_POSE(), c.t, c.words, 1 - k), {
      handL: [0.56, -0.02, 0.26], handR: [-0.56, -0.02, 0.26], poleL: [0.4, -1, -0.3], poleR: [-0.4, -1, -0.3],
      shrug: 1, head: [-0.05, 0, 0.2], chest: [-0.04, 0, 0], face: 'meh',
    }, k);
    return p;
  },

  sad(lt) {
    const k = smooth(lt, 0, 0.6);
    const sigh = Math.sin(lt * 1.4);
    const p = mixPose(REST, {
      handL: [0.3, -0.36, 0.14], handR: [-0.3, -0.36, 0.14], lean: [0.2, 0], chest: [0.14, 0, 0], head: [0.32, 0, 0.05],
      bob: -0.03, face: 'sad',
    }, k);
    p.chest = [p.chest[0] + 0.03 * sigh, p.chest[1], p.chest[2]];
    p.shrug = -0.4 * k + 0.25 * Math.max(0, sigh) * k;
    p.look = [0, -0.4 * k];
    return p;
  },

  walk(lt, c) {
    const D = 1.6; // seconds of walking in, from the edge of the frame
    const dist = 1.75;
    const k = clamp(lt / D);
    const period = 0.62;
    const step = dist / (D / period) / 2;
    const walking = lt < D;
    const ph = (lt / period) % 1;
    const foot = (phase) => { // stance moves back, swing lifts forward
      const z = phase < 0.5 ? lerp(step, -step, phase / 0.5) : lerp(-step, step, smooth(phase, 0.5, 1));
      const y = phase < 0.5 ? 0 : 0.11 * Math.sin(Math.PI * (phase - 0.5) / 0.5);
      return [z, y];
    };
    let p;
    if (walking) {
      const [zl, yl] = foot(ph);
      const [zr, yr] = foot((ph + 0.5) % 1);
      p = {
        ...REST, x: -c.side * dist * (1 - k), turn: c.side * Math.PI / 2,
        bob: -0.035 + 0.035 * Math.abs(Math.cos(2 * Math.PI * ph)), lean: [0.08, 0],
        footL: [0.15, ANKLE + yl, zl], footR: [-0.15, ANKLE + yr, zr], toeL: yl > 0 ? 0.3 : 0, toeR: yr > 0 ? 0.3 : 0,
        handL: [0.42, -0.28, -zl * 1.4], handR: [-0.42, -0.28, -zr * 1.4],
        head: [0, -c.side * 0.65, 0], look: [0, 0], face: 'happy',
      };
    } else {
      const u = lt - D;
      p = mixPose({ ...REST, turn: c.side * Math.PI / 2, head: [0, -c.side * 0.65, 0], face: 'happy' }, { turn: 0, head: [0, 0, 0] }, smooth(u, 0, 0.35));
      const hop = pulse(u, 0, 0.12, 0.15, 0.3);
      p.bob -= 0.05 * hop;
      p = mixPose(p, ACTIONS.wave(u - 0.25, c), smooth(u, 0.2, 0.4));
    }
    return p;
  },

  dance(lt, c) {
    const beat = 60 / c.bpm;
    const ph = (c.t - c.drop) / beat;
    const b = Math.abs(Math.sin(Math.PI * ph));
    const side = Math.floor(ph / 2) % 2 ? 1 : -1;
    const sway = Math.sin(Math.PI * ph / 2);
    const up = Math.floor(ph) % 2 === 0;
    return {
      ...REST, x: 0.12 * sway, bob: -0.07 * (1 - b), squash: 0.05 * (1 - b) - 0.03 * b,
      lean: [0.04, -0.08 * sway], chest: [0, 0.18 * sway, 0.05 * sway], head: [0.1 * (1 - b), -0.1 * sway, 0.12 * sway],
      handL: up ? [0.66, 0.46, 0.12] : [0.35, -0.05, 0.3], handR: !up ? [-0.66, 0.46, 0.12] : [-0.35, -0.05, 0.3],
      poleL: [1, -0.3, -0.2], poleR: [-1, -0.3, -0.2],
      footL: [0.17 + 0.04 * Math.max(0, side), ANKLE + 0.05 * Math.max(0, -sway) * b, 0.03], footR: [-0.17 - 0.04 * Math.max(0, -side), ANKLE + 0.05 * Math.max(0, sway) * b, 0.03],
      face: 'happy',
    };
  },

  thumbs(lt, c) {
    const k = smooth(lt, 0.1, 0.45);
    const p = mixPose(talking(TALK_POSE(), c.t, c.words, 1 - k), {
      handR: [-0.2, 0.06, 0.4], poleR: [-0.7, -0.6, -0.2], thumb: [0, 1], lean: [0.06, 0.04], head: [0.04, -0.12, -0.12], face: 'wink',
    }, k);
    p.bob -= 0.02 * pulse(lt, 0.4, 0.5, 0.55, 0.75);
    return p;
  },

  wow(lt) {
    const k = smooth(lt, 0, 0.25);
    const p = mixPose(REST, {
      handL: [0.26, 0.24, 0.3], handR: [-0.26, 0.24, 0.3], poleL: [0.9, -0.4, -0.2], poleR: [-0.9, -0.4, -0.2],
      lean: [-0.12, 0], head: [-0.12, 0, 0], z: -0.15, face: 'wow',
    }, k);
    p.y = 0.12 * pulse(lt, 0, 0.12, 0.14, 0.3);
    return p;
  },
};
const TALK_POSE = () => mixPose(REST, TALK, 1);
const ACTION_EVENTS = { cheer: { jump: 0.35, land: 0.85 }, walk: { stop: 1.6 }, point: { point: 0.35 }, present: { open: 0.4 } };

// ---- props: what the mascot holds or shows (always the user's own screenshot, logo, or words)
// The user's screenshot on a screen w x h: cropped to fill it, or with fit 'contain' whole, over a
// blurred copy of itself when its shape differs from the screen's (a phone screenshot on a monitor).
async function screenCanvas(src, w, h, radius, fit = 'cover') {
  const [c, g] = canvas2d(w, h);
  g.beginPath(); g.roundRect(0, 0, w, h, radius); g.clip();
  let drawn = false, aspect = 0;
  if (src) {
    const img = await loadImage(src);
    aspect = img.width / img.height;
    const cover = Math.max(w / img.width, h / img.height);
    const k = fit === 'contain' ? Math.min(w / img.width, h / img.height) : cover;
    if (k !== cover) {
      g.filter = 'blur(28px) brightness(.55)';
      g.drawImage(img, (w - img.width * cover) / 2, (h - img.height * cover) / 2, img.width * cover, img.height * cover);
      g.filter = 'none';
    }
    g.drawImage(img, (w - img.width * k) / 2, (h - img.height * k) / 2, img.width * k, img.height * k);
    drawn = readable(g);
  }
  if (!drawn) { // a generic interface with no words, nothing to mistake for a real product
    const grad = g.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, hex(PAL.bg.clone().lerp(PAL.accent, 0.18)));
    grad.addColorStop(1, hex(PAL.bg));
    g.fillStyle = grad; g.fillRect(0, 0, w, h);
    const u = Math.min(w, h) / 600;
    g.fillStyle = hex(PAL.accent);
    g.beginPath(); g.roundRect(40 * u, 60 * u, w - 80 * u, 170 * u, 30 * u); g.fill();
    g.fillStyle = 'rgba(255,255,255,.55)';
    g.beginPath(); g.roundRect(80 * u, 105 * u, 240 * u, 28 * u, 14 * u); g.roundRect(80 * u, 155 * u, 160 * u, 24 * u, 12 * u); g.fill();
    const rows = Math.max(2, Math.floor((h - 420 * u) / (170 * u)));
    for (let i = 0; i < rows; i++) {
      const y = 270 * u + i * 170 * u;
      g.fillStyle = 'rgba(255,255,255,.07)';
      g.beginPath(); g.roundRect(40 * u, y, w - 80 * u, 140 * u, 26 * u); g.fill();
      g.fillStyle = hex([PAL.second, PAL.third, PAL.pearl][i % 3]);
      g.beginPath(); g.arc(110 * u, y + 70 * u, 36 * u, 0, 6.29); g.fill();
      g.fillStyle = 'rgba(255,255,255,.4)';
      g.beginPath(); g.roundRect(175 * u, y + 45 * u, Math.min(290 * u, w - 260 * u), 22 * u, 11 * u); g.roundRect(175 * u, y + 82 * u, 180 * u, 18 * u, 9 * u); g.fill();
    }
    g.fillStyle = hex(PAL.accent);
    g.beginPath(); g.roundRect(40 * u, h - 150 * u, w - 80 * u, 100 * u, 50 * u); g.fill();
  }
  return { c, g, drawn, aspect };
}

async function buildPhone(src) {
  const [w, h] = [0.4, 0.82];
  const s = await screenCanvas(src, 500, 1024, 56);
  const phone = new THREE.Group();
  const shellM = new THREE.Mesh(new RoundedBoxGeometry(w, h, 0.05, 5, 0.06), new THREE.MeshPhysicalMaterial({ color: PAL.ink, roughness: 0.3, metalness: 0.6, clearcoat: 1 }));
  shellM.castShadow = true;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.04, h - 0.04), new THREE.MeshBasicMaterial({ map: texture(s.c), toneMapped: false }));
  screen.position.z = 0.026;
  phone.add(shellM, screen);
  return { group: phone, w, h };
}

async function buildLaptop(src) {
  const [w, h] = [0.74, 0.47];
  const s = await screenCanvas(src, 1000, 636, 18);
  const alu = new THREE.MeshPhysicalMaterial({ color: PAL.pearl.clone().lerp(PAL.ink, 0.25), roughness: 0.35, metalness: 0.75, clearcoat: 0.4 });
  const laptop = new THREE.Group();
  const lid = new THREE.Group();
  const lidM = new THREE.Mesh(new RoundedBoxGeometry(w, h, 0.03, 4, 0.012), alu); lidM.position.y = h / 2; lidM.castShadow = true;
  const bezel = new THREE.Mesh(roundedPlane(w - 0.02, h - 0.02, 0.02), new THREE.MeshBasicMaterial({ color: 0x050507 })); bezel.position.set(0, h / 2, 0.0155);
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.07, h - 0.08), new THREE.MeshBasicMaterial({ map: texture(s.c), toneMapped: false })); screen.position.set(0, h / 2 + 0.008, 0.016);
  lid.add(lidM, bezel, screen);
  lid.rotation.x = -0.14;
  const base = new THREE.Mesh(new RoundedBoxGeometry(w, 0.03, 0.48, 4, 0.012), alu);
  base.position.set(0, -0.015, 0.24); base.castShadow = true;
  laptop.add(lid, base);
  return { group: laptop, w, h };
}

async function buildSign(text, src) {
  const [w, h] = [1.0, 0.57];
  const [c, g] = canvas2d(1160, 660);
  g.fillStyle = '#fbfaf7'; g.beginPath(); g.roundRect(0, 0, 1160, 660, 48); g.fill();
  g.strokeStyle = hex(PAL.accent); g.lineWidth = 18; g.beginPath(); g.roundRect(24, 24, 1112, 612, 34); g.stroke();
  if (src) {
    const img = await loadImage(src);
    const k = Math.min(860 / img.width, 440 / img.height);
    g.drawImage(img, 580 - img.width * k / 2, 330 - img.height * k / 2, img.width * k, img.height * k);
    if (!readable(g)) { g.fillStyle = '#fbfaf7'; g.fillRect(60, 60, 1040, 540); }
  } else if (text) {
    await document.fonts.load(`900 120px ${FONT}`);
    const words = text.split(/\s+/);
    let size = 150, lines;
    const fit = () => {
      g.font = `900 ${size}px ${FONT}`;
      lines = []; let cur = '';
      for (const wd of words) { const next = cur ? `${cur} ${wd}` : wd; if (g.measureText(next).width > 960 && cur) { lines.push(cur); cur = wd; } else cur = next; }
      lines.push(cur);
      return lines.length * size * 1.08 <= 520 && lines.every((l) => g.measureText(l).width <= 980);
    };
    while (!fit() && size > 50) size -= 6;
    g.fillStyle = hex(PAL.ink); g.textAlign = 'center'; g.textBaseline = 'middle';
    lines.forEach((l, i) => g.fillText(l, 580, 330 + (i - (lines.length - 1) / 2) * size * 1.08));
  }
  const sign = new THREE.Group();
  const board = new THREE.Mesh(new RoundedBoxGeometry(w, h, 0.03, 4, 0.04), plastic(PAL.pearl, 0.4)); board.castShadow = true;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: texture(c), transparent: true }));
  face.position.z = 0.0155;
  sign.add(board, face);
  return { group: sign, w, h };
}

async function buildScreen(src) {
  const probe = src ? await loadImage(src).catch(() => null) : null;
  const aspect = probe ? probe.width / probe.height : 16 / 10;
  const [w, h] = aspect >= 1 ? [1.5, 1.5 / aspect] : [1.5 * aspect, 1.5];
  const px = 1024;
  const s = await screenCanvas(src, Math.round(aspect >= 1 ? px : px * aspect), Math.round(aspect >= 1 ? px / aspect : px), 26);
  const g = new THREE.Group();
  const frame = new THREE.Mesh(new RoundedBoxGeometry(w + 0.06, h + 0.06, 0.05, 4, 0.04), plastic(PAL.ink, 0.35)); frame.castShadow = true;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: texture(s.c), toneMapped: false }));
  screen.position.z = 0.027;
  g.add(frame, screen);
  return { group: g, w, h };
}

// ---- the sets: a light seamless studio (the floor curving up into the wall), or the same at night.
// The light on the set is baked into its vertex colors, since a lit surface filling the whole frame
// costs more than everything else in it on a machine without a graphics card; shadows land on a
// small catcher around the mascot instead.
function cyclorama(color, { night = false } = {}) {
  const prof = [];
  for (let i = 0; i <= 24; i++) prof.push([12 - i * 0.6, 0]);
  for (let i = 1; i <= 20; i++) { const a = (i / 20) * Math.PI / 2; prof.push([-2.4 - 4 * Math.sin(a), 4 - 4 * Math.cos(a)]); }
  for (let i = 1; i <= 6; i++) prof.push([-6.4, 4 + i * 2]);
  const cols = 48;
  const pos = [], col = [], idx = [];
  const key = V(-0.45, 0.75, 0.5).normalize();
  const c = new THREE.Color();
  prof.forEach(([z, y]) => {
    const bend = Math.min(1, y / 4) * Math.PI / 2; // the floor faces up, the wall faces the camera
    const n = V(0, Math.cos(bend), Math.sin(bend));
    for (let k = 0; k <= cols; k++) {
      const x = -14 + 28 * k / cols;
      pos.push(x, y, z);
      // soft studio light: a key from the front left, sky fill, and a pool falling off from the middle
      const d = Math.hypot(x * 0.8, (z - 0.5) * 0.9, (y - 0.8) * 0.7);
      const pool = night ? 0.12 + 1.15 * Math.exp(-(d * d) / 3.2) : 0.78 + 0.3 * Math.exp(-(d * d) / 30);
      const lit = night ? pool : pool * (0.82 + 0.18 * Math.max(0, n.dot(key)));
      c.copy(color).multiplyScalar(lit);
      col.push(c.r, c.g, c.b);
    }
  });
  for (let r = 0; r < prof.length - 1; r++) for (let k = 0; k < cols; k++) {
    const a = r * (cols + 1) + k, b = a + cols + 1;
    idx.push(a, a + 1, b, b, a + 1, b + 1); // wound so the floor faces up and the wall faces the camera
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(idx);
  return new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ vertexColors: true }));
}

function studio({ night = false } = {}) {
  const scene = new THREE.Scene();
  scene.environment = env;
  const floor = night ? PAL.bg.clone().lerp(PAL.accent, 0.12).multiplyScalar(2.2) : new THREE.Color('#ece6dd').lerp(PAL.accent, 0.07);
  const far = floor.clone().multiplyScalar(night ? 0.12 : 0.8);
  scene.background = far;
  scene.fog = new THREE.Fog(far, 16, 40);
  scene.add(cyclorama(floor, { night }));
  const catcher = new THREE.Mesh(new THREE.PlaneGeometry(7, 5), new THREE.ShadowMaterial({ color: night ? 0x000000 : floor.clone().multiplyScalar(0.25), opacity: night ? 0.5 : 0.32 }));
  catcher.rotation.x = -Math.PI / 2;
  catcher.position.set(0, 0.002, -0.4);
  catcher.receiveShadow = true;
  scene.add(catcher);
  const hemi = new THREE.HemisphereLight(0xffffff, floor, night ? 0.25 : 0.85);
  const key = new THREE.DirectionalLight(0xffffff, night ? 1.6 : 2.3);
  key.position.set(night ? 0.4 : -3.2, night ? 8 : 6.5, night ? 3 : 5.5);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3.5, right: 3.5, top: 4, bottom: -1.5, near: 0.5, far: 20 });
  key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02; key.shadow.radius = 4;
  const rim = new THREE.DirectionalLight(PAL.accent, night ? 2.0 : 1.4);
  rim.position.set(4, 3, -4);
  const fill = new THREE.DirectionalLight(PAL.second, night ? 0.4 : 0.35);
  fill.position.set(5, 2, 4);
  scene.add(hemi, key, rim, fill);
  const camera = new THREE.PerspectiveCamera(28, W / H, 0.1, 200);
  return { scene, camera };
}

// ---- places: rooms the mascot stands in, so a video moves through places instead of one backdrop.
// Big surfaces are flat (their light painted in) and the shadows land on a catcher, which keeps
// them quick to draw in software; only what stands near the mascot is lit.
const SETS = ['room', 'stage', 'city', 'park'];
const muted = (c, s, l) => { const h = c.getHSL({}, SRGB); return new THREE.Color().setHSL(h.h, s, l, SRGB); };
function flat(tex, w, h, x, y, z, opts = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: !!opts.transparent, toneMapped: false, depthWrite: !opts.transparent, ...(opts.additive ? { blending: THREE.AdditiveBlending, depthWrite: false, transparent: true } : {}) }));
  m.position.set(x, y, z);
  if (opts.floor) m.rotation.x = -Math.PI / 2;
  return m;
}
function shadowCatcher(scene, opacity, color = 0x000000) {
  const c = new THREE.Mesh(new THREE.PlaneGeometry(7, 5), new THREE.ShadowMaterial({ color, opacity }));
  c.rotation.x = -Math.PI / 2;
  c.position.set(0, 0.006, -0.4);
  c.receiveShadow = true;
  scene.add(c);
}
function keyLight(scene, color, intensity, pos) {
  const key = new THREE.DirectionalLight(color, intensity);
  key.position.set(...pos);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3.5, right: 3.5, top: 4, bottom: -1.5, near: 0.5, far: 25 });
  key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02; key.shadow.radius = 4;
  scene.add(key);
  return key;
}
const radial = (g, x, y, r, inner, outer = 'rgba(0,0,0,0)') => { const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, inner); gr.addColorStop(1, outer); g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); };

// a living room by day: a window full of sky, a plant, a lamp, a rug, the sun on the wall
function roomSet(scene) {
  const wall = muted(PAL.second, 0.28, 0.7);
  const [c, g] = canvas2d(2304, 896); // 18 x 7 units, from y 0: wide enough for a landscape frame
  const U = 128, X = (x) => (x + 9) * U, Y = (y) => (7 - y) * U;
  const grad = g.createLinearGradient(0, 0, 2304, 896);
  grad.addColorStop(0, hex(wall.clone().offsetHSL(0, 0, 0.08))); grad.addColorStop(1, hex(wall.clone().offsetHSL(0, 0, -0.06)));
  g.fillStyle = grad; g.fillRect(0, 0, 2304, 896);
  g.fillStyle = hex(wall.clone().offsetHSL(0, 0.02, -0.12)); g.fillRect(0, Y(1.0), 2304, U * 1.0); // wainscot
  g.strokeStyle = 'rgba(255,255,255,.18)'; g.lineWidth = 4;
  for (let x = -8.7; x < 9; x += 0.9) g.strokeRect(X(x), Y(0.85), 0.7 * U, 0.65 * U);
  g.fillStyle = 'rgba(255,255,255,.55)'; g.fillRect(0, Y(1.02), 2304, 7); g.fillRect(0, Y(0.08), 2304, 10);
  // further out, for a wide frame: a bookcase on the left, a big painting on the right
  g.fillStyle = '#efe8dc'; g.fillRect(X(-7.6), Y(4.3), 2.4 * U, 4.3 * U);
  for (let sh = 0; sh < 5; sh++) {
    const y = Y(0.4 + sh * 0.85);
    g.fillStyle = '#d9cfbf'; g.fillRect(X(-7.5), y, 2.2 * U, 9);
    let bx = X(-7.4);
    for (let k = 0; k < 10; k++) { const w = 14 + ((sh * 5 + k * 7) % 12), h = 46 + ((sh * 3 + k * 13) % 36); g.fillStyle = hex([PAL.accent, PAL.second, PAL.third, PAL.ink, PAL.pearl][(sh + k) % 5].clone().multiplyScalar(0.9)); g.fillRect(bx, y - h, w, h); bx += w + 4; }
  }
  g.fillStyle = '#26232b'; g.fillRect(X(3.3), Y(4.0), 2.6 * U, 1.8 * U);
  const art = g.createLinearGradient(X(3.3), Y(4.0), X(5.9), Y(2.2)); art.addColorStop(0, hex(PAL.third)); art.addColorStop(1, hex(PAL.accent));
  g.fillStyle = art; g.fillRect(X(3.3) + 12, Y(4.0) + 12, 2.6 * U - 24, 1.8 * U - 24);
  g.fillStyle = 'rgba(255,255,255,.35)'; g.beginPath(); g.arc(X(4.2), Y(3.2), 0.45 * U, 0, 6.29); g.fill();
  // the window: sky, a far skyline, the frame, and the sunbeam it throws to the right
  const [wx0, wx1, wy0, wy1] = [X(-2.75), X(-0.55), Y(3.9), Y(1.35)];
  const sky = g.createLinearGradient(0, wy0, 0, wy1); sky.addColorStop(0, '#7fb8ec'); sky.addColorStop(1, '#d9ecf7');
  g.fillStyle = sky; g.fillRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
  g.fillStyle = 'rgba(255,255,255,.85)';
  [[0.3, 0.22, 46], [0.62, 0.35, 34], [0.2, 0.45, 28]].forEach(([fx, fy, r]) => { const x = wx0 + fx * (wx1 - wx0), y = wy0 + fy * (wy1 - wy0); g.beginPath(); g.ellipse(x, y, r * 1.8, r * 0.7, 0, 0, 6.29); g.ellipse(x + r, y - r * 0.3, r, r * 0.65, 0, 0, 6.29); g.fill(); });
  const rr = rng(4);
  for (let x = wx0; x < wx1; x += 14 + rr() * 18) { const h = 30 + rr() * 90; g.fillStyle = 'rgba(120,150,175,.75)'; g.fillRect(x, wy1 - h, 16 + rr() * 22, h); }
  g.fillStyle = '#5f8f55'; for (let x = wx0; x < wx1; x += 22) { g.beginPath(); g.arc(x, wy1 - 6, 16 + rr() * 12, 0, 6.29); g.fill(); }
  g.strokeStyle = '#f7f4ee'; g.lineWidth = 16; g.strokeRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
  g.lineWidth = 9; g.beginPath(); g.moveTo((wx0 + wx1) / 2, wy0); g.lineTo((wx0 + wx1) / 2, wy1); g.moveTo(wx0, (wy0 + wy1) / 2); g.lineTo(wx1, (wy0 + wy1) / 2); g.stroke();
  g.fillStyle = '#f7f4ee'; g.fillRect(wx0 - 24, wy1, wx1 - wx0 + 48, 16); // the sill
  g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = 'rgba(255,236,200,.16)';
  g.beginPath(); g.moveTo(wx1 + 40, wy0 + 30); g.lineTo(X(2.6), Y(3.1)); g.lineTo(X(3.6), Y(0.4)); g.lineTo(wx1 + 140, wy1 + 40); g.fill(); g.restore();
  // a framed print in the brand's colors, and a shelf of books
  g.fillStyle = '#26232b'; g.fillRect(X(0.55), Y(3.75), 1.35 * U, 1.6 * U);
  g.fillStyle = hex(PAL.pearl); g.fillRect(X(0.55) + 12, Y(3.75) + 12, 1.35 * U - 24, 1.6 * U - 24);
  radial(g, X(1.22), Y(3.05), 58, hex(PAL.accent), hex(PAL.accent)); g.fillStyle = hex(PAL.second); g.fillRect(X(0.8), Y(2.55), 0.85 * U, 14); g.fillRect(X(0.8), Y(2.4), 0.55 * U, 14);
  g.fillStyle = '#e9e2d6'; g.fillRect(X(0.3), Y(1.9), 2.2 * U, 12);
  let bx = X(0.42);
  const spines = [PAL.accent, PAL.second, PAL.third, PAL.ink, PAL.pearl, PAL.accent, PAL.second];
  spines.forEach((col, i) => { const w = 16 + (i * 7) % 12, h = 54 + (i * 13) % 26; g.fillStyle = hex(col.clone().multiplyScalar(0.92)); g.fillRect(bx, Y(1.9) - h, w, h); bx += w + 3; });
  g.fillStyle = hex(PAL.third); g.beginPath(); g.ellipse(X(2.1), Y(1.9) - 26, 22, 28, 0, 0, 6.29); g.fill();
  scene.add(flat(texture(c), 18, 7, 0, 3.5, -3.4));
  // the floor: warm planks, darker away from the light
  const [fc, fg] = canvas2d(512, 512);
  const base = new THREE.Color('#b98a5e');
  for (let y = 0; y < 512; y += 32) for (let x = -((y / 32) % 2) * 90; x < 512; x += 180) { fg.fillStyle = hex(base.clone().offsetHSL(0, 0, (rr() - 0.5) * 0.08)); fg.fillRect(x, y, 178, 30); }
  const ft = texture(fc); ft.wrapS = ft.wrapT = THREE.RepeatWrapping; ft.repeat.set(4, 4);
  ft.repeat.set(8, 5);
  const floorM = flat(ft, 24, 16, 0, 0, 2.6, { floor: true });
  scene.add(floorM);
  const [vc, vg] = canvas2d(256, 256); radial(vg, 128, 128, 128, 'rgba(0,0,0,0)', 'rgba(40,20,10,.55)');
  scene.add(flat(texture(vc), 24, 16, 0, 0.002, 2.6, { floor: true, transparent: true }));
  const [rc, rg] = canvas2d(512, 512);
  rg.fillStyle = hex(muted(PAL.accent, 0.45, 0.62)); rg.beginPath(); rg.arc(256, 256, 250, 0, 6.29); rg.fill();
  rg.strokeStyle = 'rgba(255,255,255,.45)'; rg.lineWidth = 10; [200, 150].forEach((r) => { rg.beginPath(); rg.arc(256, 256, r, 0, 6.29); rg.stroke(); });
  const rug = flat(texture(rc), 2.8, 2.8, 0, 0.004, 0.1, { floor: true, transparent: true }); rug.scale.y = 0.75;
  scene.add(rug);
  // a big plant by the window, a floor lamp on the right
  const pl = plant(); pl.scale.setScalar(2.6); pl.position.set(-1.75, 0, -2.6); scene.add(pl);
  const lamp = new THREE.Group();
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.9, 10), new THREE.MeshStandardMaterial({ color: '#2a2b33', metalness: 0.6, roughness: 0.4 })); pole.position.y = 0.95;
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.24, 0.04, 24), pole.material); foot.position.y = 0.02;
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.32, 0.4, 28, 1, true), new THREE.MeshStandardMaterial({ color: '#f3e7d3', emissive: '#ffd9a0', emissiveIntensity: 0.55, side: THREE.DoubleSide })); shade.position.y = 1.95;
  lamp.add(pole, foot, shade); lamp.position.set(1.75, 0, -2.55); scene.add(lamp);
  // a sofa against the far right wall, out of a tall frame, in a wide one
  const sofaM = plastic(muted(PAL.accent, 0.35, 0.5), 0.6);
  const sofa = new THREE.Group();
  [[0, 0.25, 0, 2.4, 0.5, 0.9], [0, 0.75, -0.35, 2.4, 0.6, 0.22], [-1.15, 0.45, 0, 0.22, 0.5, 0.9], [1.15, 0.45, 0, 0.22, 0.5, 0.9]].forEach(([x, y, z, w, h, d]) => {
    const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 3, 0.08), sofaM); m.position.set(x, y, z); m.castShadow = true; sofa.add(m);
  });
  sofa.position.set(4.6, 0, -2.75); scene.add(sofa);
  const pl2 = plant(); pl2.scale.setScalar(2.4); pl2.position.set(-3.9, 0, -2.7); scene.add(pl2);
  scene.background = wall.clone().multiplyScalar(0.8);
  scene.add(new THREE.HemisphereLight('#e8f2ff', '#b98a5e', 0.9));
  keyLight(scene, '#fff1dc', 2.2, [-4, 6.5, 5]);
  const rim = new THREE.DirectionalLight(PAL.accent, 0.9); rim.position.set(4, 3, -4); scene.add(rim);
  shadowCatcher(scene, 0.35, '#3a2516');
  return { tone: 'light' };
}

// a launch stage: an LED wall in the brand's colors, light beams sweeping through haze
function stageSet(scene) {
  const dark = PAL.bg.clone().lerp(PAL.accent, 0.04).multiplyScalar(0.55);
  scene.background = dark;
  scene.fog = new THREE.Fog(dark, 9, 30);
  const [gc, gg] = canvas2d(1024, 256);
  const cols = [PAL.accent, PAL.second, PAL.third, PAL.accent];
  const lg = gg.createLinearGradient(0, 0, 1024, 0);
  cols.forEach((col, i) => lg.addColorStop(i / (cols.length - 1), hex(col)));
  gg.fillStyle = lg; gg.fillRect(0, 0, 1024, 256);
  for (let i = 0; i < 6; i++) radial(gg, 90 + i * 170, 128 + (i % 2 ? 50 : -40), 130, 'rgba(255,255,255,.6)');
  const glowTex = texture(gc); glowTex.wrapS = THREE.RepeatWrapping; glowTex.repeat.set(1, 1);
  const led = flat(glowTex, 19.2, 5.6, 0, 3.2, -4.6);
  const [mc, mg] = canvas2d(512, 280); // the LED dots: dark everywhere but the little round pixels
  mg.fillStyle = 'rgba(8,8,12,.82)'; mg.fillRect(0, 0, 512, 280); mg.globalCompositeOperation = 'destination-out';
  for (let y = 4; y < 280; y += 8) for (let x = 4; x < 512; x += 8) { mg.beginPath(); mg.arc(x, y, 3.3, 0, 6.29); mg.fill(); }
  const maskTex = texture(mc); maskTex.wrapS = maskTex.wrapT = THREE.RepeatWrapping; maskTex.repeat.set(4, 2.15);
  const mask = flat(maskTex, 19.2, 5.6, 0, 3.2, -4.58, { transparent: true });
  const frameM = new THREE.Mesh(new THREE.BoxGeometry(19.5, 5.9, 0.1), new THREE.MeshBasicMaterial({ color: '#08080b' })); frameM.position.set(0, 3.2, -4.7);
  scene.add(frameM, led, mask);
  // a glossy floor that picks up the wall's glow
  const [fc, fg] = canvas2d(512, 512);
  fg.fillStyle = hex(dark.clone().multiplyScalar(0.7)); fg.fillRect(0, 0, 512, 512);
  const fl = fg.createLinearGradient(0, 0, 0, 512); fl.addColorStop(0, hex(PAL.accent.clone().multiplyScalar(0.55))); fl.addColorStop(0.45, 'rgba(0,0,0,0)');
  fg.fillStyle = fl; fg.fillRect(0, 0, 512, 512);
  radial(fg, 256, 330, 170, 'rgba(255,240,220,.35)');
  scene.add(flat(texture(fc), 24, 12, 0, 0, 0.4, { floor: true }));
  // beams from the rig above, through haze
  const [bc, bg] = canvas2d(64, 256);
  const bl = bg.createLinearGradient(0, 0, 0, 256); bl.addColorStop(0, 'rgba(255,255,255,.55)'); bl.addColorStop(1, 'rgba(255,255,255,0)');
  bg.fillStyle = bl; bg.fillRect(0, 0, 64, 256);
  const beamTex = texture(bc);
  const beams = [[-4.6, PAL.third], [-2.6, PAL.second], [-1.0, PAL.pearl], [1.0, PAL.pearl], [2.6, PAL.accent], [4.6, PAL.second]].map(([x, col], i) => {
    const m = new THREE.Mesh(new THREE.ConeGeometry(0.75, 6.5, 32, 1, true), new THREE.MeshBasicMaterial({ map: beamTex, color: col, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    m.geometry.translate(0, -3.25, 0); // the tip at the rig, the wide end on the floor
    m.position.set(x, 6.4, -1.8);
    scene.add(m);
    return { m, phase: i * 1.7 };
  });
  scene.add(new THREE.HemisphereLight('#6d6a8a', '#140f18', 0.35));
  keyLight(scene, '#fff6ea', 1.9, [0.5, 7, 6]);
  const r1 = new THREE.DirectionalLight(PAL.accent, 2.4); r1.position.set(4, 3, -4);
  const r2 = new THREE.DirectionalLight(PAL.second, 2.0); r2.position.set(-4, 3, -4);
  scene.add(r1, r2);
  shadowCatcher(scene, 0.55);
  return {
    tone: 'dark',
    update(lt) {
      glowTex.offset.x = lt * 0.06;
      beams.forEach((b) => { b.m.rotation.z = 0.32 * Math.sin(lt * 0.6 + b.phase); });
    },
  };
}

// a rooftop at dusk: a skyline under an orange and violet sky, string lights over a railing
function citySet(scene) {
  const [sc, sg] = canvas2d(256, 512);
  const sk = sg.createLinearGradient(0, 0, 0, 512);
  sk.addColorStop(0, '#1d2050'); sk.addColorStop(0.45, '#5b3a7a'); sk.addColorStop(0.75, '#d9707a'); sk.addColorStop(1, '#ffb27a');
  sg.fillStyle = sk; sg.fillRect(0, 0, 256, 512);
  radial(sg, 70, 430, 150, 'rgba(255,220,170,.85)');
  scene.add(flat(texture(sc), 70, 40, 0, 12, -42));
  const skyline = (z, w, h, color, lit, seed, top) => {
    const [c, g] = canvas2d(1024, 384);
    const r = rng(seed);
    for (let x = 0; x < 1024;) {
      const bw = 40 + r() * 70, bh = 120 + r() * 250 * top;
      g.fillStyle = color; g.fillRect(x, 384 - bh, bw, bh);
      for (let wy = 384 - bh + 10; wy < 376; wy += 16) for (let wx = x + 6; wx < x + bw - 8; wx += 12) if (r() < lit) { g.fillStyle = r() > 0.25 ? 'rgba(255,214,140,.9)' : 'rgba(170,210,255,.8)'; g.fillRect(wx, wy, 6, 8); }
      x += bw + 2 + r() * 10;
    }
    scene.add(flat(texture(c), w, h, 0, h / 2 - 0.3, z, { transparent: true }));
  };
  skyline(-30, 48, 18, '#2c2650', 0.22, 5, 0.8);
  skyline(-16, 26, 10, '#16152c', 0.35, 9, 1.0);
  scene.background = new THREE.Color('#1d2050');
  scene.fog = new THREE.Fog('#4a3a6e', 18, 60);
  // the roof, a railing, and the lights strung across it
  const [fc, fg] = canvas2d(512, 512);
  fg.fillStyle = '#3a3a48'; fg.fillRect(0, 0, 512, 512);
  fg.strokeStyle = 'rgba(0,0,0,.25)'; fg.lineWidth = 3; for (let i = 0; i <= 512; i += 64) { fg.beginPath(); fg.moveTo(i, 0); fg.lineTo(i, 512); fg.moveTo(0, i); fg.lineTo(512, i); fg.stroke(); }
  radial(fg, 256, 300, 260, 'rgba(255,190,120,.28)');
  const ft = texture(fc); ft.wrapS = ft.wrapT = THREE.RepeatWrapping;
  ft.repeat.set(2, 1);
  scene.add(flat(ft, 30, 10, 0, 0, 1.6, { floor: true }));
  const railM = new THREE.MeshStandardMaterial({ color: '#202030', metalness: 0.6, roughness: 0.4 });
  for (let x = -10.4; x <= 10.4; x += 0.8) { const post = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.05, 0.05), railM); post.position.set(x, 0.52, -2.4); scene.add(post); }
  const top = new THREE.Mesh(new THREE.BoxGeometry(21, 0.06, 0.08), railM); top.position.set(0, 1.05, -2.4); scene.add(top);
  const glassM = new THREE.MeshBasicMaterial({ color: '#9fb7ff', transparent: true, opacity: 0.08, depthWrite: false });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(20.8, 0.95), glassM); glass.position.set(0, 0.52, -2.42); scene.add(glass);
  const bulbs = [];
  const bulbM = new THREE.MeshBasicMaterial({ color: '#ffd59a', toneMapped: false });
  for (const [x0, x1, y, z, n] of [[-3.2, 3.2, 3.15, -1.7, 16], [-3.6, 0.6, 2.85, -3.0, 10], [3.6, 9.6, 3.2, -1.9, 16], [-9.8, -3.8, 3.0, -2.2, 16]]) {
    const pts = [];
    for (let i = 0; i <= n; i++) { const t = i / n; pts.push(V(lerp(x0, x1, t), y - 0.45 * Math.sin(Math.PI * t), z)); }
    const wire = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 48, 0.008, 4), new THREE.MeshBasicMaterial({ color: '#111' }));
    scene.add(wire);
    pts.forEach((p, i) => { if (i % 2) return; const b = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 8), bulbM.clone()); b.position.copy(p).add(V(0, -0.06, 0)); scene.add(b); bulbs.push(b); });
  }
  const pot = plant(); pot.scale.setScalar(2.2); pot.position.set(-2.1, 0, -1.9); scene.add(pot);
  scene.add(new THREE.HemisphereLight('#8f7fd0', '#2a2236', 0.55));
  keyLight(scene, '#ffcf9a', 2.0, [-3, 5.5, 5]);
  const rim = new THREE.DirectionalLight('#ff9a7a', 1.6); rim.position.set(-3, 2, -6); scene.add(rim);
  const rim2 = new THREE.DirectionalLight(PAL.second, 1.2); rim2.position.set(4, 3, -4); scene.add(rim2);
  shadowCatcher(scene, 0.5);
  return { tone: 'dark', update(lt) { bulbs.forEach((b, i) => b.material.color.setScalar(0.85 + 0.15 * Math.sin(lt * 2.3 + i * 1.7))); } };
}

// a park on a bright day: sky, drifting clouds, rolling hills, round trees, grass
function parkSet(scene) {
  const [sc, sg] = canvas2d(256, 512);
  const sk = sg.createLinearGradient(0, 0, 0, 512); sk.addColorStop(0, '#4f9be8'); sk.addColorStop(0.7, '#a9d4f5'); sk.addColorStop(1, '#e6f4fb');
  sg.fillStyle = sk; sg.fillRect(0, 0, 256, 512);
  radial(sg, 200, 120, 90, 'rgba(255,250,225,.9)');
  scene.add(flat(texture(sc), 80, 44, 0, 14, -45));
  scene.background = new THREE.Color('#a9d4f5');
  scene.fog = new THREE.Fog('#cfe6f5', 20, 60);
  const hills = (z, w, h, color, seed, amp) => {
    const [c, g] = canvas2d(1024, 256);
    const r = rng(seed); const ph = [r() * 6, r() * 6];
    g.fillStyle = color; g.beginPath(); g.moveTo(0, 256);
    for (let x = 0; x <= 1024; x += 8) g.lineTo(x, 256 - (110 + amp * Math.sin(x / 170 + ph[0]) + amp * 0.5 * Math.sin(x / 61 + ph[1])));
    g.lineTo(1024, 256); g.fill();
    scene.add(flat(texture(c), w, h, 0, h / 2 - 0.2, z, { transparent: true }));
  };
  hills(-34, 70, 14, '#8cbfa4', 3, 40);
  hills(-20, 44, 8, '#6fae6e', 7, 34);
  const clouds = [];
  const cloudM = new THREE.MeshBasicMaterial({ color: '#ffffff' });
  const r = rng(17);
  for (let i = 0; i < 6; i++) {
    const g = new THREE.Group();
    for (let k = 0; k < 4; k++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.9 + r() * 0.7, 16, 10), cloudM); m.position.set(k * 1.1 - 1.6, (k % 2) * 0.4, 0); m.scale.y = 0.6; g.add(m); }
    g.position.set(-14 + i * 5.5 + r() * 2, 7 + r() * 4, -26 - r() * 6);
    scene.add(g); clouds.push({ g, x: g.position.x, speed: 0.15 + r() * 0.15 });
  }
  const leafM = [new THREE.MeshStandardMaterial({ color: '#4f9b4f', roughness: 0.8 }), new THREE.MeshStandardMaterial({ color: '#69b35a', roughness: 0.8 })];
  const trunkM = new THREE.MeshStandardMaterial({ color: '#7a5537', roughness: 0.9 });
  [[-3.4, -6, 1.4], [3.2, -7.5, 1.7], [-1.6, -10, 1.2], [1.4, -12, 1.5], [-5.5, -11, 1.8], [5.4, -10, 1.3], [-8.6, -8, 1.6], [8.4, -7, 1.5], [-11.5, -13, 1.9], [11.8, -12, 1.7]].forEach(([x, z, s], i) => {
    const t = new THREE.Group();
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.16, 1.4, 10), trunkM); trunk.position.y = 0.7;
    const crown = new THREE.Mesh(new THREE.SphereGeometry(0.9, 20, 14), leafM[i % 2]); crown.position.y = 1.9;
    const crown2 = new THREE.Mesh(new THREE.SphereGeometry(0.6, 16, 12), leafM[(i + 1) % 2]); crown2.position.set(0.45, 1.55, 0.2);
    t.add(trunk, crown, crown2); t.scale.setScalar(s); t.position.set(x, 0, z); scene.add(t);
  });
  const [gc, gg] = canvas2d(512, 512);
  gg.fillStyle = '#7dbb5c'; gg.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2500; i++) { gg.fillStyle = r() > 0.5 ? 'rgba(60,120,50,.35)' : 'rgba(170,220,120,.3)'; gg.fillRect(r() * 512, r() * 512, 2, 6); }
  const gt = texture(gc); gt.wrapS = gt.wrapT = THREE.RepeatWrapping; gt.repeat.set(6, 6);
  scene.add(flat(gt, 40, 40, 0, 0, -8, { floor: true }));
  const flowerCols = [PAL.accent, '#ffffff', PAL.third, '#ff7aa8'];
  for (let i = 0; i < 26; i++) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), new THREE.MeshBasicMaterial({ color: flowerCols[i % 4] }));
    const a = r() * 6.28, d = 1.3 + r() * (WIDE ? 4.5 : 2.2);
    m.position.set(Math.cos(a) * d, 0.05, -0.5 + Math.sin(a) * d * 0.7);
    scene.add(m);
  }
  scene.add(new THREE.HemisphereLight('#cfe8ff', '#6fae6e', 0.95));
  keyLight(scene, '#fff3d6', 2.4, [3.5, 7, 4.5]);
  const rim = new THREE.DirectionalLight(PAL.accent, 0.7); rim.position.set(-4, 3, -4); scene.add(rim);
  shadowCatcher(scene, 0.32, '#1f3a14');
  return { tone: 'light', update(lt) { clouds.forEach((c) => { c.g.position.x = c.x + lt * c.speed; }); } };
}

// the user's own photo as the place: cropped to fill the frame and softly blurred, as if the
// camera were focused on the mascot standing in front of it
async function photoSet(scene, src) {
  const img = await loadImage(src);
  const [cw, ch] = [W / 2, H / 2];
  const [c, g] = canvas2d(cw, ch);
  const k = Math.max(cw / img.width, ch / img.height);
  g.filter = 'blur(5px) saturate(1.05)';
  g.drawImage(img, (cw - img.width * k) / 2, (ch - img.height * k) / 2, img.width * k, img.height * k);
  if (!readable(g)) throw new Error(`couldn't read ${src} into the 3D scene; open the page through render.js`);
  scene.background = texture(c);
  scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 0.9));
  keyLight(scene, '#ffffff', 2.0, [-3, 6.5, 5]);
  const rim = new THREE.DirectionalLight(PAL.accent, 1.0); rim.position.set(4, 3, -4); scene.add(rim);
  shadowCatcher(scene, 0.45);
  return { tone: 'dark' };
}

// The place for a shot: data-bg (a photo), data-set by name, or the next in turn, so a video's
// shots move through the room, the stage, the city, and the park.
function setFor(el) {
  const named = (el.dataset.set || '').toLowerCase();
  if (named) return named;
  const shots = [...document.querySelectorAll('.shot')].filter((s) => ['mascot', 'title', 'icons', 'button'].includes(s.dataset.shot));
  return SETS[Math.max(0, shots.indexOf(el)) % SETS.length];
}
async function buildSet(el) {
  const name = el.dataset.bg ? 'photo' : setFor(el);
  if (name === 'studio' || name === 'night') return { ...studio({ night: name === 'night' }), tone: name === 'night' ? 'dark' : 'light', update() {} };
  const scene = new THREE.Scene();
  scene.environment = env;
  scene.environmentIntensity = 0.7;
  const make = { room: roomSet, stage: stageSet, city: citySet, park: parkSet }[name];
  if (name !== 'photo' && !make) throw new Error(`unknown set "${name}" (known: ${[...SETS, 'studio', 'night'].join(', ')}, or data-bg for a photo)`);
  const built = name === 'photo' ? await photoSet(scene, el.dataset.bg) : make(scene);
  const camera = new THREE.PerspectiveCamera(28, W / H, 0.1, 200);
  return { scene, camera, tone: built.tone, update: built.update || (() => {}) };
}

// The bold look's captions are a taller block, so the subject sits higher above them.
const raised = ([y0, y1, p0, p1]) => {
  if (!document.body.classList.contains('bold')) return [y0, y1, p0, p1];
  const up = Math.min(150, p0 - 280);
  return [y0, y1, p0 - up, p1 - 150];
};

// A cheer jumps about half a unit: room above the head so it stays clear of the text at the top.
const jumpRoom = ([y0, y1, p0, p1], jumps) => (jumps ? [y0, y1 + 0.5, p0, p1] : [y0, y1, p0, p1]);

// Frames a span of the scene: world heights y0..y1 at pixel rows p0..p1 (feet at the bottom),
// from `push` times the distance that takes, `orbit` radians around, a little above eye level.
// The rows are for a 1920-tall frame, scaled to this one.
function frameSpan(camera, [y0, y1, p0, p1], { x = 0, z = 0, push = 1, orbit = 0, lift = 0.35 } = {}) {
  const ry = H / 1920;
  let [q0, q1] = [p0 * ry, p1 * ry];
  if (WIDE) { const c = (q0 + q1) / 2 - 40, h = (q1 - q0) * 0.64; [q0, q1] = [c - h, c + h]; } // a wide frame: closer in, so the subject isn't lost in it
  const ppu = (q1 - q0) / (y1 - y0);
  const d = (H / ppu) / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2)) * push;
  const yc = y1 - (H / 2 - q0) / ppu;
  camera.position.set(x + Math.sin(orbit) * d, yc + lift, z + Math.cos(orbit) * d);
  camera.lookAt(x, yc + lift * 0.15, z);
}

// confetti for a cheer: pieces launched at `t0`, fluttering down; a pure function of time
function confetti(scene, n = 90) {
  const geo = new THREE.PlaneGeometry(0.05, 0.085);
  const mesh = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, roughness: 0.6 }), n);
  const r = rng(21);
  const cols = [PAL.accent, PAL.second, PAL.third, PAL.pearl, PAL_EYE];
  const parts = Array.from({ length: n }, (_, i) => {
    mesh.setColorAt(i, cols[i % cols.length]);
    const a = r() * Math.PI * 2;
    return { vx: Math.cos(a) * (0.8 + r() * 2.2), vz: Math.sin(a) * (0.4 + r() * 1.0), vy: 1.4 + r() * 1.8, spin: [r() * 9, r() * 9, r() * 9], drift: r() * 6.28 };
  });
  mesh.frustumCulled = false;
  scene.add(mesh);
  const dummy = new THREE.Object3D();
  return (lt, t0, origin) => {
    parts.forEach((p, i) => {
      const u = lt - t0;
      if (u < 0) { dummy.position.set(0, -50, 0); dummy.scale.setScalar(0.0001); }
      else {
        const k = 1.6, vt = 0.9; // air drag, and the terminal speed it settles to
        const e = (1 - Math.exp(-k * u)) / k;
        dummy.position.set(origin.x + p.vx * e + 0.12 * Math.sin(u * 3 + p.drift), origin.y + (p.vy + vt) * e - vt * u, origin.z + p.vz * e);
        dummy.rotation.set(p.spin[0] * u, p.spin[1] * u, p.spin[2] * u);
        dummy.scale.setScalar(1);
      }
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
  };
}

// small 3D bits that tell the action: a thought, a rain cloud, sparkles
function thoughtDots(parent) {
  const g = new THREE.Group();
  const dots = [0.05, 0.075, 0.105].map((r, i) => {
    const m = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), plastic(PAL.pearl, 0.3));
    m.position.set(0.42 + i * 0.17, 2.0 + i * 0.2, 0.1);
    g.add(m); return m;
  });
  parent.add(g);
  return (lt) => dots.forEach((m, i) => m.scale.setScalar(Math.max(0.0001, smooth(((lt - 0.4 - i * 0.25) % 2.1 + 2.1) % 2.1, 0, 0.25) * (lt > 0.4 + i * 0.25 ? 1 : 0))));
}
function rainCloud(parent) {
  const g = new THREE.Group();
  const mat = plastic(new THREE.Color('#8f97a8'), 0.6);
  [[0, 0, 0.26], [0.26, -0.03, 0.2], [-0.26, -0.04, 0.19], [0.1, 0.12, 0.2], [-0.12, 0.1, 0.17]].forEach(([x, y, r]) => {
    const m = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16), mat); m.position.set(x, y, 0); m.castShadow = true; g.add(m);
  });
  const dropMat = new THREE.MeshBasicMaterial({ color: '#9fd3ff', toneMapped: false });
  const drops = Array.from({ length: 9 }, (_, i) => { const m = new THREE.Mesh(new THREE.CapsuleGeometry(0.012, 0.08, 4, 8), dropMat); g.add(m); return { m, x: -0.3 + i * 0.075, off: (i * 0.37) % 1 }; });
  g.position.set(0, 2.6, 0);
  parent.add(g);
  return (lt) => {
    g.position.y = 2.6 + 0.04 * Math.sin(lt * 1.5);
    g.scale.setScalar(Math.max(0.0001, smooth(lt, 0.1, 0.5)));
    for (const d of drops) { const u = (lt * 1.6 + d.off) % 1; d.m.position.set(d.x, -0.2 - u * 0.8, 0.05); d.m.visible = lt > 0.4; }
  };
}

// ---- the shot: the mascot on a set, doing data-do, holding data-prop
SHOTS.mascot = async (el, shot) => {
  const action = (el.dataset.do || (shot.first ? 'wave' : 'talk')).toLowerCase();
  if (!ACTIONS[action]) throw new Error(`unknown mascot action "${action}" (known: ${Object.keys(ACTIONS).join(', ')})`);
  const propName = (el.dataset.prop || '').toLowerCase();
  const place = await buildSet(el);
  const { scene, camera } = place;
  const rig = buildMascot();
  scene.add(rig.root);
  const total = parseFloat(document.body.dataset.duration) || 0;
  const topText = (shot.first && document.querySelector('.hook')) || (shot.in + shot.dur >= total - 0.05 && document.querySelector('.end'));
  const ctx = {
    words: [], t: 0, propSide: 0, side: rng(Math.round(shot.in * 10) + 3)() > 0.5 ? 1 : -1,
    bpm: parseFloat(document.body.dataset.bpm) || 112, drop: parseFloat(document.body.dataset.drop) || 0,
  };
  // the prop: held in the chest's space (so it moves with the body), or floating beside it
  let prop = null;
  if (propName === 'phone') prop = { kind: propName, ...(await buildPhone(el.dataset.src)) };
  else if (propName === 'laptop') prop = { kind: propName, ...(await buildLaptop(el.dataset.src)) };
  else if (propName === 'sign') prop = { kind: propName, ...(await buildSign(el.dataset.text, el.dataset.src)) };
  else if (propName === 'screen') prop = { kind: propName, ...(await buildScreen(el.dataset.src)) };
  else if (propName) throw new Error(`unknown mascot prop "${propName}" (known: phone, laptop, sign, screen)`);
  if (prop && prop.kind === 'screen') { scene.add(prop.group); ctx.propSide = 1; }
  else if (prop) rig.j.chest.add(prop.group);
  prop?.group.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  const standX = prop && prop.kind === 'screen' ? -0.62 : 0;
  const frame = el.dataset.frame || (prop && prop.kind === 'screen' ? 'wide' : prop || ['wave', 'talk', 'point', 'thumbs', 'think', 'shrug', 'wow'].includes(action) ? 'mid' : 'full');
  const span = jumpRoom(raised(topText && frame !== 'wide' ? (frame === 'mid' ? SPAN.midLow : SPAN.low) : SPAN[frame] || SPAN.full), action === 'cheer');
  const blob = contactShadow(1.4, 0.004, 0.42);
  scene.add(blob);
  // on the cover (the first shot at frame 0) the action is already under way, and a prop already up
  const settle = shot.first ? Math.max({ wave: 0.55, cheer: 1.1, walk: 2.2, point: 0.6, present: 0.7, thumbs: 0.6, think: 0.6, shrug: 0.5, sad: 0.7, wow: 0.35 }[action] || 0, prop ? 0.6 : 0) : 0;
  const fx = {
    confetti: action === 'cheer' ? confetti(scene) : null,
    dots: action === 'think' ? thoughtDots(rig.root) : null,
    cloud: action === 'sad' ? rainCloud(rig.root) : null,
  };
  const faceOverride = el.dataset.face;
  const lips = (el.dataset.talk || '').toLowerCase() !== 'no';
  const seed = shot.in * 1.7 + 0.3;
  const blinkAt = (lt) => { // a blink every 2-4.5 s, at times fixed by the shot
    const r = rng(Math.round(shot.in * 100) + 11);
    let t = 0.6 + r() * 1.4;
    while (t < lt + 0.2) { const d = lt - t; if (d >= 0 && d < 0.16) return 1 - Math.abs(d - 0.08) / 0.08; t += 2 + r() * 2.5; }
    return 0;
  };
  const poseAt = (lt) => {
    ctx.t = shot.in + lt;
    let p = ACTIONS[action](lt + settle, ctx);
    if (prop && prop.kind !== 'screen') p = holding(p, prop, lt + settle);
    p = alive(p, lt, seed, action === 'dance' || action === 'walk' ? 0.4 : 1);
    return { ...p, x: p.x + standX };
  };
  // the antenna lags behind the head on a spring, so every move ends with a wobble
  const wobble = (lt) => {
    const dt = 1 / 60;
    const steps = Math.round(Math.min(lt, 1.2) / dt);
    const drive = (u) => { const p = poseAt(u); return [p.x + 1.3 * (p.lean[1] + p.chest[2] + p.head[2]) + 0.2 * Math.sin(p.turn), p.y + p.bob]; };
    let [dx, dy] = drive(lt - steps * dt);
    let [px, py, vx, vy] = [dx, dy, 0, 0];
    for (let i = steps - 1; i >= 0; i--) {
      [dx, dy] = drive(lt - i * dt);
      vx += (-(px - dx) * 180 - vx * 7) * dt; px += vx * dt;
      vy += (-(py - dy) * 180 - vy * 7) * dt; py += vy * dt;
    }
    const lim = (v) => Math.max(-1, Math.min(1, v));
    return [lim((dx - px) * 2.2), lim((dy - py) * 2)];
  };
  const events = {};
  for (const [name, at] of Object.entries(ACTION_EVENTS[action] || {})) events[name] = Math.max(0, at - settle);
  if (prop && prop.kind !== 'screen') events.show = shot.first ? 0 : 0.45;
  return {
    scene, camera, events, tone: place.tone,
    update(lt) {
      place.update(lt);
      ctx.words = spokenWords();
      const [wx, wy] = wobble(lt);
      const pose = poseAt(lt);
      applyPose(rig, pose);
      blob.position.set(pose.x, 0.004, pose.z);
      blob.material.opacity = 0.42 / (1 + 3 * pose.y);
      blob.scale.setScalar(1 + 0.6 * pose.y);
      if (pose.prop) { prop.group.position.set(...pose.prop.pos); prop.group.rotation.set(...pose.prop.rot); }
      rig.j.antenna.rotation.set(-wy * 0.5, 0, -wx * 0.45);
      const said = lips ? mouthAt(shot.in + lt, ctx.words) : 0;
      drawFace(rig.faceCanvas, { face: faceOverride || pose.face, blink: blinkAt(lt), look: pose.look, mouth: said });
      rig.faceTex.needsUpdate = true;
      rig.bulb.material.emissiveIntensity = 0.9 + 0.5 * Math.max(0, Math.sin((shot.in + lt) * 3.1));
      if (prop && prop.kind === 'screen') {
        const k = shot.first ? 1 : back((lt - 0.1) / 0.7);
        prop.group.position.set(0.74, 1.32 + 0.04 * Math.sin(lt * 1.3), 0.15 - (1 - k) * 2);
        prop.group.rotation.set(0.03 * Math.sin(lt * 0.9), -0.28 + 0.04 * Math.sin(lt * 0.7), 0);
        prop.group.scale.setScalar(Math.max(0.001, k));
      }
      if (fx.confetti) fx.confetti(lt + settle, 0.6, V(pose.x, 2.0 + pose.y, 0.3));
      if (fx.dots) fx.dots(lt + settle);
      if (fx.cloud) fx.cloud(lt + settle);
      const k = inOut(lt / shot.dur);
      const land = action === 'cheer' ? pulse(lt + settle, 0.83, 0.86, 0.9, 1.1) : 0;
      frameSpan(camera, span, { x: (prop && prop.kind === 'screen' ? 0.26 : 0) + 0.1 * Math.sin(lt * 0.35), push: lerp(1.07, 0.96, k) - 0.02 * land, orbit: 0.06 * Math.sin(lt * 0.3 + seed) });
    },
  };
};

// holding a prop: where it sits in chest space over time (pose.prop, applied after the pose),
// and the hands on it. Pure, like the actions, so the antenna's spring can look back in time.
function holding(p, prop, lt) {
  const out = { ...p };
  const lift = smooth(lt, 0, 0.45);
  if (prop.kind === 'phone') { // held up beside the face, turned to the camera; the free hand presents it
    out.prop = { pos: [-0.56, lerp(-0.3, 0.24, lift), lerp(0.2, 0.3, lift)], rot: [-0.04, 0.16, 0.04 * Math.sin(lt * 1.2)] };
    out.handR = [-0.56, lerp(-0.62, -0.08, lift), 0.3];
    out.poleR = [-0.7, -0.6, -0.3];
    const show = pulse(lt, 0.9, 1.3, 2.4, 2.9);
    out.handL = mixPose(p, { handL: [0.12, 0.02, 0.42] }, show).handL;
    out.poleL = [0.6, -0.7, -0.2];
    const glance = pulse(lt, 0.3, 0.6, 1.5, 1.9);
    out.head = [p.head[0] + 0.06 * glance, p.head[1] - 0.45 * glance, p.head[2] + 0.05 * glance];
    out.look = [-0.8 * glance, -0.1 * glance];
  } else if (prop.kind === 'laptop') { // open, held out in front with the screen to the camera
    out.prop = { pos: [0, lerp(-0.5, -0.22, lift), 0.41], rot: [0, 0, 0.02 * Math.sin(lt * 1.1)] };
    out.handL = [0.36, lerp(-0.52, -0.25, lift), 0.44]; out.handR = [-0.36, lerp(-0.52, -0.25, lift), 0.44];
    out.poleL = [0.8, -0.5, -0.1]; out.poleR = [-0.8, -0.5, -0.1];
    out.head = [p.head[0] + 0.08, p.head[1], p.head[2]];
  } else if (prop.kind === 'sign') { // held up at the chest by its bottom corners
    out.prop = { pos: [0, lerp(-0.35, 0.06, lift), 0.4], rot: [-0.04, 0, 0.03 * Math.sin(lt * 1.2)] };
    out.handL = [0.44, lerp(-0.6, -0.2, lift), 0.4]; out.handR = [-0.44, lerp(-0.6, -0.2, lift), 0.4];
    out.poleL = [0.8, -0.5, -0.2]; out.poleR = [-0.8, -0.5, -0.2];
  }
  return out;
}

// ---- the desk: a cozy room at night, the mascot at a monitor showing the user's screen
function roomWall() {
  const [c, g] = canvas2d(2048, 768); // 16 x 6 units of wall, wide enough for a landscape frame
  const u = (x) => (x + 8) * 128, v = (y) => (6 - y) / 6 * 768;
  const base = new THREE.Color('#1b2133').lerp(PAL.bg, 0.4);
  const grad = g.createLinearGradient(0, 0, 0, 768);
  grad.addColorStop(0, hex(base.clone().multiplyScalar(0.55)));
  grad.addColorStop(1, hex(base));
  g.fillStyle = grad; g.fillRect(0, 0, 2048, 768);
  // a tall bookcase at the far left, books in the brand's colors
  g.fillStyle = '#2a2018'; g.fillRect(u(-7.2), v(4.2), u(-4.6) - u(-7.2), v(0) - v(4.2));
  for (let sh = 0; sh < 5; sh++) {
    const y = v(0.35 + sh * 0.8);
    g.fillStyle = '#3b2c20'; g.fillRect(u(-7.1), y, u(-4.7) - u(-7.1), 8);
    let bx = u(-7.0);
    for (let k = 0; k < 9; k++) { const w = 12 + ((sh * 5 + k * 7) % 11), h = 40 + ((sh * 3 + k * 13) % 34); g.fillStyle = hex([PAL.accent, PAL.second, PAL.third, PAL.pearl][(sh + k) % 4].clone().multiplyScalar(0.55)); g.fillRect(bx, y - h, w, h); bx += w + 4; }
  }
  // the window, left of the desk: a night city behind blinds
  const [wx0, wx1, wy0, wy1] = [u(-2.5), u(-0.75), v(3.55), v(1.55)];
  const sky = g.createLinearGradient(0, wy0, 0, wy1);
  sky.addColorStop(0, '#16213d'); sky.addColorStop(1, '#3b4e7e');
  g.fillStyle = sky; g.fillRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
  const r = rng(9);
  for (let i = 0; i < 70; i++) {
    const x = wx0 + r() * (wx1 - wx0), y = wy0 + (0.45 + r() * 0.55) * (wy1 - wy0);
    g.fillStyle = r() > 0.4 ? `rgba(255,${190 + Math.floor(r() * 50)},120,${0.35 + r() * 0.5})` : `rgba(160,200,255,${0.3 + r() * 0.4})`;
    g.beginPath(); g.arc(x, y, 1.5 + r() * 3.5, 0, 6.29); g.fill();
  }
  g.fillStyle = 'rgba(10,12,20,.55)';
  for (let y = wy0; y < wy1; y += 13) g.fillRect(wx0, y, wx1 - wx0, 6);
  g.strokeStyle = '#0d0f17'; g.lineWidth = 12; g.strokeRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
  // two framed prints in the brand's colors, and the lamp's warm glow on the wall
  [[1.15, 2.05, 2.35, 3.45, PAL.accent, PAL.second], [2.3, 3.0, 2.6, 3.3, PAL.third, PAL.accent]].forEach(([x0, x1, y0, y1, a, b]) => {
    g.fillStyle = '#0c0d12'; g.fillRect(u(x0) - 8, v(y1) - 8, u(x1) - u(x0) + 16, v(y0) - v(y1) + 16);
    const art = g.createLinearGradient(u(x0), v(y1), u(x1), v(y0));
    art.addColorStop(0, hex(a.clone().multiplyScalar(0.7))); art.addColorStop(1, hex(b.clone().multiplyScalar(0.5)));
    g.fillStyle = art; g.fillRect(u(x0), v(y1), u(x1) - u(x0), v(y0) - v(y1));
    g.fillStyle = 'rgba(255,255,255,.18)'; g.beginPath(); g.arc((u(x0) + u(x1)) / 2, (v(y0) + v(y1)) / 2, (u(x1) - u(x0)) * 0.28, 0, 6.29); g.fill();
  });
  const lamp = g.createRadialGradient(u(1.2), v(1.5), 10, u(1.2), v(1.5), 330);
  lamp.addColorStop(0, 'rgba(255,190,120,.42)'); lamp.addColorStop(1, 'rgba(255,190,120,0)');
  g.fillStyle = lamp; g.fillRect(0, 0, 2048, 768);
  const glowGrad = g.createRadialGradient(u(0.15), v(1.4), 10, u(0.15), v(1.4), 420);
  glowGrad.addColorStop(0, hex(PAL.accent.clone().lerp(PAL.pearl, 0.4)) + '55'); glowGrad.addColorStop(1, hex(PAL.accent) + '00');
  g.fillStyle = glowGrad; g.fillRect(0, 0, 2048, 768);
  return texture(c);
}

function keyboardTexture() {
  const [c, g] = canvas2d(768, 256);
  g.fillStyle = '#101117'; g.fillRect(0, 0, 768, 256);
  const cols = [PAL.accent, PAL.second, PAL.third];
  for (let row = 0; row < 5; row++) for (let k = 0; k < 15; k++) {
    const x = 18 + k * 49, y = 16 + row * 47;
    const t = k / 14;
    const col = cols[0].clone().lerp(cols[1], t).lerp(cols[2], Math.max(0, t - 0.5));
    g.fillStyle = '#2a2c36'; g.beginPath(); g.roundRect(x, y, 42, 40, 7); g.fill();
    g.fillStyle = hex(col) + '99'; g.beginPath(); g.roundRect(x + 4, y + 30, 34, 6, 3); g.fill();
  }
  g.fillStyle = '#2a2c36'; g.beginPath(); g.roundRect(170, 16 + 4 * 47, 330, 40, 7); g.fill();
  return texture(c);
}

function plant() {
  const g = new THREE.Group();
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.08, 0.17, 24), plastic(PAL.accent.clone().multiplyScalar(0.75), 0.6));
  pot.position.y = 0.085; g.add(pot);
  const leaf = new THREE.MeshStandardMaterial({ color: '#3f7d52', roughness: 0.55 });
  for (let i = 0; i < 8; i++) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), leaf);
    m.scale.set(0.045, 0.26 + 0.05 * (i % 3), 0.012);
    const a = (i / 8) * Math.PI * 2;
    m.position.set(Math.cos(a) * 0.05, 0.38, Math.sin(a) * 0.05);
    m.rotation.set(Math.sin(a) * 0.45, a, -Math.cos(a) * 0.45);
    g.add(m);
  }
  return g;
}

SHOTS.desk = async (el, shot) => {
  const scene = new THREE.Scene();
  scene.environment = env;
  scene.environmentIntensity = 0.3;
  scene.background = new THREE.Color('#07080c');
  const DESK = 0.82; // the desk top's height, sized to the mascot
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(16, 6), new THREE.MeshBasicMaterial({ map: roomWall() }));
  wall.position.set(0, 3, -1.45);
  const floorM = new THREE.Mesh(new THREE.PlaneGeometry(16, 8), new THREE.MeshStandardMaterial({ color: '#1d1714', roughness: 0.8 }));
  floorM.rotation.x = -Math.PI / 2; floorM.position.z = 1.5;
  scene.add(wall, floorM);
  const wood = new THREE.MeshStandardMaterial({ color: '#4a3326', roughness: 0.55 });
  const top = new THREE.Mesh(new RoundedBoxGeometry(2.7, 0.06, 1.15, 3, 0.02), wood);
  top.position.set(0.1, DESK - 0.03, -0.55);
  scene.add(top);
  for (const [x, z] of [[-1.15, -0.05], [1.35, -0.05], [-1.15, -1.05], [1.35, -1.05]]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.06, DESK - 0.06, 0.06), wood);
    leg.position.set(x, (DESK - 0.06) / 2, z); scene.add(leg);
  }
  // the monitor, turned a little toward the chair, with the user's screen on it
  const monitor = new THREE.Group();
  const [mw, mh] = [1.44, 0.88];
  const s = await screenCanvas(el.dataset.src, 1280, 782, 10, 'contain');
  const frame = new THREE.Mesh(new RoundedBoxGeometry(mw + 0.05, mh + 0.05, 0.05, 4, 0.02), new THREE.MeshStandardMaterial({ color: '#15161c', roughness: 0.4, metalness: 0.5 }));
  const screenMat = new THREE.MeshBasicMaterial({ map: texture(s.c), toneMapped: false });
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(mw, mh), screenMat);
  screen.position.z = 0.026;
  const note = new THREE.Mesh(new THREE.PlaneGeometry(0.13, 0.13), new THREE.MeshStandardMaterial({ color: '#f4d86b', roughness: 0.9 }));
  note.position.set(mw / 2 - 0.02, -mh / 2 + 0.06, 0.03); note.rotation.z = -0.12;
  monitor.add(frame, screen, note);
  const MON = { x: 0.15, y: DESK + 0.62, z: -0.72, turn: 0.04 };
  monitor.position.set(MON.x, MON.y, MON.z);
  monitor.rotation.y = MON.turn;
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.42, 0.04), new THREE.MeshStandardMaterial({ color: '#2a2b33', metalness: 0.7, roughness: 0.3 }));
  neck.position.set(MON.x + 0.03, DESK + 0.21, MON.z - 0.06);
  const foot = new THREE.Mesh(new RoundedBoxGeometry(0.42, 0.02, 0.26, 2, 0.008), neck.material);
  foot.position.set(MON.x + 0.03, DESK + 0.01, MON.z - 0.04);
  scene.add(monitor, neck, foot);
  // the keyboard glowing in the brand's colors, a mouse, a mug, a plant, a lamp
  const kb = new THREE.Group();
  const kbBody = new THREE.Mesh(new RoundedBoxGeometry(0.76, 0.03, 0.26, 2, 0.01), new THREE.MeshStandardMaterial({ color: '#16171d', roughness: 0.5 }));
  const keys = new THREE.Mesh(new THREE.PlaneGeometry(0.74, 0.24), new THREE.MeshBasicMaterial({ map: keyboardTexture(), toneMapped: false }));
  keys.rotation.x = -Math.PI / 2; keys.position.y = 0.0155;
  kb.add(kbBody, keys);
  kb.position.set(-0.62, DESK + 0.015, -0.2); kb.rotation.y = -0.32;
  const mouse = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), plastic(PAL.pearl, 0.3));
  mouse.scale.set(0.05, 0.025, 0.08); mouse.position.set(-0.12, DESK + 0.02, -0.12);
  const mug = new THREE.Group();
  const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.065, 0.15, 24), plastic(PAL.pearl, 0.35));
  const band = new THREE.Mesh(new THREE.CylinderGeometry(0.0705, 0.0705, 0.04, 24), plastic(PAL.accent, 0.35));
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.012, 8, 20), plastic(PAL.pearl, 0.35));
  handle.position.x = 0.075; band.position.y = 0.02;
  mug.add(cup, band, handle); mug.position.set(0.75, DESK + 0.075, -0.3);
  const pl = plant(); pl.position.set(-1.05, DESK, -0.85);
  const lamp = new THREE.Group();
  const metalM = new THREE.MeshStandardMaterial({ color: '#202128', metalness: 0.6, roughness: 0.35 });
  const lbase = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.13, 0.03, 24), metalM); lbase.position.y = 0.015;
  const arm1 = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.6, 8), metalM); arm1.position.set(-0.08, 0.3, 0); arm1.rotation.z = 0.28;
  const arm2 = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.45, 8), metalM); arm2.position.set(-0.05, 0.6, 0.1); arm2.rotation.set(-0.9, 0, -0.4);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.17, 24, 1, true), new THREE.MeshStandardMaterial({ color: PAL.accent, roughness: 0.4, side: THREE.DoubleSide }));
  shade.position.set(0.05, 0.72, 0.28); shade.rotation.x = 0.5;
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 10), new THREE.MeshBasicMaterial({ color: '#ffe2b8', toneMapped: false }));
  bulb.position.set(0.05, 0.67, 0.31);
  lamp.add(lbase, arm1, arm2, shade, bulb);
  lamp.position.set(1.0, DESK, -0.75);
  scene.add(kb, mouse, mug, pl, lamp);
  // light: moonlight from the window, the monitor's glow, the lamp, and the keyboard
  scene.add(new THREE.HemisphereLight('#41507a', '#1a1410', 0.55));
  const moon = new THREE.DirectionalLight('#8fb0ff', 0.7); moon.position.set(-4, 4, -1); scene.add(moon);
  const glowC = PAL.pearl.clone().lerp(PAL.accent, 0.25);
  const mGlow = new THREE.PointLight(glowC, 4.5, 4.5, 1.6);
  mGlow.position.set(MON.x - 0.1, MON.y, MON.z + 0.6); scene.add(mGlow);
  const lampLight = new THREE.SpotLight('#ffbf80', 9, 4, 0.75, 0.6, 1.5);
  lampLight.position.set(1.05, DESK + 0.67, -0.45); lampLight.target.position.set(0.6, DESK, -0.1);
  scene.add(lampLight, lampLight.target);
  const kGlow = new THREE.PointLight(PAL.accent, 1.2, 1.1, 2); kGlow.position.set(-0.62, DESK + 0.12, -0.2); scene.add(kGlow);

  // the mascot on a swivel chair, typing; it spins round to wave, then back to work
  const withMascot = (el.dataset.mascot || '').toLowerCase() !== 'no';
  const CHAIR = { x: -0.78, z: 0.5, turn: Math.PI - 0.32 };
  const chair = new THREE.Group();
  const chairM = plastic(PAL.ink.clone().lerp(PAL.accent, 0.12), 0.5);
  const seat = new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.08, 0.6, 3, 0.03), chairM); seat.position.y = 0.42;
  const backrest = new THREE.Mesh(new RoundedBoxGeometry(0.58, 0.46, 0.08, 3, 0.04), chairM); backrest.position.set(0, 0.74, -0.3);
  chair.add(seat, backrest);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.34, 12), metalM); stem.position.set(CHAIR.x, 0.2, CHAIR.z);
  const star = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.03, 5), metalM); star.position.set(CHAIR.x, 0.04, CHAIR.z);
  scene.add(chair, stem, star);
  const rig = withMascot ? buildMascot() : null;
  if (rig) scene.add(rig.root);
  const camera = new THREE.PerspectiveCamera(42, W / H, 0.05, 60);
  const D = shot.dur;
  const START = V(0.5, 2.7, 5.6);
  const normal = V(Math.sin(MON.turn), 0, Math.cos(MON.turn));
  const center = V(MON.x, MON.y, MON.z);
  const END = center.clone().add(normal.clone().multiplyScalar(WIDE ? 0.9 : 0.56)); // into the screen: past its height on a tall frame, to its width on a wide one
  const camTurn = Math.atan2(START.x - CHAIR.x, START.z - CHAIR.z);
  const PUSH = Math.min(1.2, D * 0.4); // the last stretch: into the screen
  const T1 = shot.first ? -1 : Math.min(1.1, D * 0.25); // the spin round to wave
  const T2 = shot.first ? 1.2 : T1 + Math.min(2.2, Math.max(1.2, D - PUSH - T1 - 0.9));
  const spin = (lt) => pulse(lt, T1, T1 + 0.55, T2, T2 + 0.55);
  const waving = D > 2.6 && withMascot;
  const poseAt = (lt) => {
    const k = waving ? spin(lt) : 0;
    const type = (ph) => 0.025 * Math.max(0, Math.sin(lt * 15 + ph));
    let p = {
      ...REST, x: CHAIR.x, z: CHAIR.z, turn: lerp(CHAIR.turn, camTurn + 2 * Math.PI * (camTurn < 0 ? 1 : 0), k), bob: -0.14,
      lean: [lerp(0.12, 0, k), 0], footL: [0.17, ANKLE, 0.32], footR: [-0.17, ANKLE, 0.32],
      handL: [0.17, 0.0 + type(0), 0.5], handR: [-0.17, 0.0 + type(2.1), 0.5], poleL: [0.6, -0.5, -0.6], poleR: [-0.6, -0.5, -0.6],
      head: [-0.06, 0.06 * Math.sin(lt * 0.7), 0], look: [0.15, 0.1], face: 'normal',
    };
    if (k > 0) p = mixPose(p, { ...ACTIONS.wave(lt - T1 - 0.2, ctx), x: CHAIR.x, z: CHAIR.z, turn: p.turn, bob: -0.14, footL: p.footL, footR: p.footR, lean: p.lean }, smooth(k, 0.3, 1));
    return alive(p, lt, 1.3, 0.5);
  };
  const ctx = { words: [], t: 0, bpm: 112, drop: 0, propSide: 0, side: 1 };
  const blinkAt = (lt) => { const d = (lt + 0.7) % 3.1; return d < 0.16 ? 1 - Math.abs(d - 0.08) / 0.08 : 0; };
  return {
    scene, camera, tone: 'dark',
    events: { ...(waving ? { turn: Math.max(0, T1) } : {}), enter: Math.max(0, D - 0.3) },
    update(lt) {
      ctx.t = shot.in + lt; ctx.words = spokenWords();
      const pose = poseAt(lt);
      chair.position.set(CHAIR.x, 0, CHAIR.z);
      chair.rotation.y = pose.turn;
      if (rig) {
        applyPose(rig, pose);
        drawFace(rig.faceCanvas, { face: pose.face, blink: blinkAt(lt), look: pose.look, mouth: mouthAt(shot.in + lt, ctx.words) * spin(lt) });
        rig.faceTex.needsUpdate = true;
      }
      kGlow.intensity = 1.0 + 0.4 * Math.sin(lt * 9);
      // the camera: a slow drift toward the desk, then a push into the screen until it fills the frame
      const drift = inOut(lt / Math.max(0.1, D - PUSH));
      const near = START.clone().lerp(center.clone().add(V(0.45, 0.6, 2.6)), 0.3 * drift);
      const k = clamp((lt - (D - PUSH)) / PUSH);
      const pos = near.clone().lerp(END, k * k * k);
      camera.position.copy(pos);
      camera.lookAt(center.clone().add(V(-0.32 * (1 - k), -0.42 * (1 - k), 0)));
      camera.fov = lerp(42, 44, k * k);
      camera.updateProjectionMatrix();
      screenMat.color.setScalar(1 + 0.25 * k);
    },
  };
};

// ---- big 3D letters dropping onto the studio floor, the mascot cheering beside them
function letterMesh(ch, color) {
  const [c, g] = canvas2d(256, 320);
  g.fillStyle = '#fff';
  g.font = `900 260px ${FONT}`;
  g.textAlign = 'center'; g.textBaseline = 'alphabetic';
  g.fillText(ch, 128, 268);
  const width = Math.max(60, g.measureText(ch).width) / 256;
  const tex = texture(c);
  const group = new THREE.Group();
  const LAYERS = 12, DEPTH = 0.16;
  const side = color.clone().multiplyScalar(0.62);
  for (let i = 0; i < LAYERS; i++) { // stacked cut-outs read as a solid letter from the front
    const front = i === LAYERS - 1;
    const mat = front
      ? new THREE.MeshStandardMaterial({ map: tex, color, alphaTest: 0.5, roughness: 0.35, envMapIntensity: 0.8 })
      : new THREE.MeshBasicMaterial({ map: tex, color: side.clone().multiplyScalar(0.8 + 0.2 * i / LAYERS), alphaTest: 0.5 });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1.25), mat);
    m.position.set(0, 0.625 - 0.07, -DEPTH + (i / (LAYERS - 1)) * DEPTH);
    m.castShadow = front || i === 0;
    group.add(m);
  }
  return { group, width };
}

SHOTS.title = async (el, shot) => {
  const text = (el.dataset.text || 'NEW').trim().toUpperCase().slice(0, 18);
  await document.fonts.load(`900 260px ${FONT}`);
  const place = await buildSet(el);
  const { scene, camera } = place;
  const withMascot = (el.dataset.mascot || '').toLowerCase() !== 'no';
  // one row, or two when it's long: the bottom row lands first, the top row on top of it
  const words = text.split(/\s+/);
  let rows = [text];
  if (text.length > 8 && words.length > 1) {
    let best = 1, diff = 99;
    for (let i = 1; i < words.length; i++) { const d = Math.abs(words.slice(0, i).join(' ').length - words.slice(i).join(' ').length); if (d < diff) { diff = d; best = i; } }
    rows = [words.slice(0, best).join(' '), words.slice(best).join(' ')];
  }
  const colors = [PAL.accent, PAL.ink];
  const letters = [];
  const built = rows.map((row, r) => [...row].map((ch) => (ch === ' ' ? { space: true, width: 0.35 } : letterMesh(ch, r === 0 && rows.length > 1 ? colors[1] : colors[0]))));
  const widest = Math.max(...built.map((row) => row.reduce((a, l) => a + l.width * 0.92, 0)));
  const room = (withMascot ? 1.7 : 2.5) * (WIDE ? 2 : 1);
  const size = Math.min(WIDE ? 1.25 : 0.95, room / widest);
  const offsetX = withMascot ? (WIDE ? -0.7 : -0.38) : 0;
  let order = 0;
  const rowOrder = rows.length > 1 ? [1, 0] : [0];
  for (const r of rowOrder) {
    const row = built[r];
    const w = row.reduce((a, l) => a + l.width * 0.92, 0) * size;
    let x = offsetX - w / 2;
    const baseY = rows.length > 1 && r === 0 ? 1.25 * size * 0.86 : 0;
    for (const l of row) {
      const lw = l.width * 0.92 * size;
      if (!l.space) {
        l.group.scale.setScalar(size);
        scene.add(l.group);
        const delay = (shot.first ? 0 : 0.25) + order * 0.14;
        letters.push({ ...l, x: x + lw / 2, y: baseY, z: 0.35, delay, tilt: (rng(order + 5)() - 0.5) * 0.5 });
        order++;
      }
      x += lw;
    }
  }
  const FALL = 0.42;
  const done = letters.length ? letters[letters.length - 1].delay + FALL : 0;
  const rig = withMascot ? buildMascot() : null;
  if (rig) scene.add(rig.root);
  const blob = contactShadow(1.4, 0.004, 0.42);
  if (rig) scene.add(blob);
  const ctx = { words: [], t: 0, bpm: 112, drop: 0, propSide: -1, side: 1 };
  const total = parseFloat(document.body.dataset.duration) || 0;
  const topText = (shot.first && document.querySelector('.hook')) || (shot.in + shot.dur >= total - 0.05 && document.querySelector('.end'));
  const fx = rig ? confetti(scene, 70) : null;
  return {
    scene, camera, tone: place.tone,
    events: { ...Object.fromEntries(letters.map((l, i) => [`letter-${i + 1}`, shot.first ? 0 : l.delay + FALL])), done: shot.first ? 0 : done },
    update(lt) {
      place.update(lt);
      for (const l of letters) {
        const u = shot.first ? 9 : lt - l.delay;
        const fall = clamp(u / FALL);
        const hop = u > FALL ? 0.1 * size * Math.max(0, Math.sin((u - FALL) / 0.28 * Math.PI)) * (u - FALL < 0.28 ? 1 : 0) : 0;
        const squash = u > FALL ? pulse(u, FALL, FALL + 0.04, FALL + 0.06, FALL + 0.22) : 0;
        l.group.position.set(l.x, l.y + (1 - fall * fall) * 4 + hop, l.z);
        l.group.rotation.set(0, 0, l.tilt * (1 - fall));
        l.group.scale.set(size * (1 + 0.12 * squash), size * (1 - 0.16 * squash), size);
        l.group.visible = u > 0;
      }
      if (rig) {
        ctx.t = shot.in + lt; ctx.words = spokenWords();
        const after = shot.first ? 9 : lt - done;
        let p = ACTIONS.present(Math.min(lt, 0.5) + 0.1, ctx);
        if (after > 0) p = mixPose(p, ACTIONS.cheer(after, ctx), smooth(after, 0, 0.2));
        p.y *= 0.5; // a smaller hop beside the letters
        p = { ...alive(p, lt, 2.2), x: WIDE ? 2.1 : 1.05, z: -0.35, turn: -0.35 };
        applyPose(rig, p);
        blob.position.set(p.x, 0.004, p.z);
        blob.material.opacity = 0.42 / (1 + 3 * p.y);
        drawFace(rig.faceCanvas, { face: p.face, blink: 0, look: [-0.6, 0], mouth: mouthAt(shot.in + lt, ctx.words) });
        rig.faceTex.needsUpdate = true;
        fx(Math.max(0, lt - done) + (shot.first ? 0.8 : 0), 0.1, V(-0.2, 1.6, 0.4));
      }
      const k = inOut(lt / shot.dur);
      frameSpan(camera, jumpRoom(raised(topText ? [-0.02, 2.3, 600, 1200] : [-0.02, 2.3, 420, 1170]), withMascot), { x: withMascot ? 0.15 : 0, push: lerp(1.05, 0.97, k), orbit: 0.08 * Math.sin(lt * 0.3) });
    },
  };
};

// ---- app tiles dropping into a grid, one per item ("🔍 Research"), the mascot in the last cell
const EMOJI_FONT = '"Noto Color Emoji"';
const splitIcon = (item) => {
  const m = /^\s*(\p{Extended_Pictographic}[️‍\p{Extended_Pictographic}]*)\s*(.*)$/u.exec(item);
  return m ? { glyph: m[1], label: m[2].trim() } : { glyph: '', label: item.trim() };
};
SHOTS.icons = async (el, shot) => {
  const withMascot = (el.dataset.mascot || '').toLowerCase() !== 'no';
  const items = (el.dataset.items || '').split(',').map((s) => s.trim()).filter(Boolean).slice(0, withMascot ? 8 : 9).map(splitIcon);
  if (!items.length) throw new Error('icons needs data-items, e.g. data-items="🔍 Research,📅 Calendar"');
  const place = await buildSet(el);
  const { scene, camera } = place;
  const night = place.tone === 'dark';
  await document.fonts.load(`800 72px ${FONT}`);
  for (const it of items) if (it.glyph) await document.fonts.load(`150px ${EMOJI_FONT}`, it.glyph);
  const cells = items.length + (withMascot ? 1 : 0);
  const cols = WIDE ? Math.min(4, cells) : cells === 4 ? 2 : Math.min(3, cells);
  const rows = Math.ceil(cells / cols);
  const [SX, SY, T] = [1.0, 1.08, 0.66]; // column and row spacing, tile size
  const tileMat = plastic(night ? PAL.pearl : PAL.ink, 0.32);
  const tiles = items.map((it, i) => {
    const g = new THREE.Group();
    const box = new THREE.Mesh(new RoundedBoxGeometry(T, T, 0.2, 5, 0.14), tileMat);
    box.castShadow = true;
    const [fc, fg] = canvas2d(256, 256);
    if (it.glyph) { fg.font = `150px ${EMOJI_FONT}`; fg.textAlign = 'center'; fg.textBaseline = 'middle'; fg.fillText(it.glyph, 128, 140); }
    else { fg.fillStyle = hex(PAL.accent); fg.font = `900 150px ${FONT}`; fg.textAlign = 'center'; fg.textBaseline = 'middle'; fg.fillText((it.label[0] || '').toUpperCase(), 128, 140); }
    const face = new THREE.Mesh(new THREE.PlaneGeometry(T * 0.78, T * 0.78), new THREE.MeshBasicMaterial({ map: texture(fc), transparent: true, toneMapped: false }));
    face.position.z = 0.101;
    const [lc, lg] = canvas2d(512, 112);
    let size = 76;
    do { lg.font = `800 ${size}px ${FONT}`; size -= 4; } while (lg.measureText(it.label).width > 500 && size > 40);
    lg.textAlign = 'center'; lg.textBaseline = 'middle'; lg.lineJoin = 'round';
    lg.strokeStyle = night ? 'rgba(0,0,0,.7)' : 'rgba(255,255,255,.75)'; lg.lineWidth = 12; lg.strokeText(it.label, 256, 58); // readable over a busy set
    lg.fillStyle = night ? '#f3f2ee' : hex(PAL.ink); lg.fillText(it.label, 256, 58);
    const label = new THREE.Mesh(new THREE.PlaneGeometry(SX * 0.98, SX * 0.98 * 112 / 512), new THREE.MeshBasicMaterial({ map: texture(lc), transparent: true, depthWrite: false }));
    label.position.y = -T / 2 - 0.15;
    g.add(box, face, label);
    scene.add(g);
    const r = rng(i * 7 + 3);
    return { g, box, col: i % cols, row: Math.floor(i / cols), delay: (shot.first ? 0 : 0.15) + i * 0.13, tilt: [(r() - 0.5) * 0.6, (r() - 0.5) * 0.8] };
  });
  const CY = (rows * SY) / 2 + 0.35; // the grid's middle, its bottom row clear of the floor
  const slot = (col, row) => [((col - (cols - 1) / 2) * SX), CY + ((rows - 1) / 2 - row) * SY];
  const rig = withMascot ? buildMascot() : null;
  const last = { col: items.length % cols, row: Math.floor(items.length / cols) };
  if (rig) { rig.root.scale.setScalar(0.36); scene.add(rig.root); }
  const ctx = { words: [], t: 0, bpm: 112, drop: 0, propSide: 0, side: 1 };
  const span = [CY - (rows * SY) / 2 - 0.2, CY + (rows * SY) / 2];
  const total = parseFloat(document.body.dataset.duration) || 0;
  const topText = (shot.first && document.querySelector('.hook')) || (shot.in + shot.dur >= total - 0.05 && document.querySelector('.end'));
  const FALL = 0.45;
  const mascotIn = (shot.first ? 0 : 0.15) + items.length * 0.13;
  return {
    scene, camera, tone: place.tone,
    events: { ...Object.fromEntries(tiles.map((t, i) => [`tile-${i + 1}`, shot.first ? 0 : t.delay + FALL])), done: shot.first ? 0 : mascotIn + FALL },
    update(lt) {
      place.update(lt);
      for (const t of tiles) {
        const u = shot.first ? 9 : lt - t.delay;
        const k = clamp(u / FALL);
        const squash = u > FALL ? pulse(u, FALL, FALL + 0.04, FALL + 0.06, FALL + 0.25) : 0;
        const [x, y] = slot(t.col, t.row);
        t.g.position.set(x, y + (1 - k * k) * 1.4 + 0.03 * Math.sin(lt * 1.6 + t.col + t.row), 0);
        t.g.scale.setScalar(0.55 + 0.45 * k);
        t.g.rotation.set(t.tilt[0] * (1 - k) + 0.04 * Math.sin(lt + t.row), t.tilt[1] * (1 - k) + 0.06 * Math.sin(lt * 0.8 + t.col), 0);
        t.box.scale.set(1 + 0.1 * squash, 1 - 0.14 * squash, 1);
        t.g.visible = u > 0;
      }
      if (rig) {
        ctx.t = shot.in + lt; ctx.words = spokenWords();
        const u = shot.first ? 9 : lt - mascotIn;
        const [x, y] = slot(last.col, last.row);
        let p = ACTIONS.wave(Math.max(0, u) + 0.2, ctx);
        p = { ...alive(p, lt, 4.1), x, y: y - T / 2 - 0.05 + (1 - clamp(u / FALL) ** 2) * 3.2, z: 0 }; // the root's own scale shrinks the robot, not where it stands
        applyPose(rig, p);
        rig.root.visible = u > 0;
        drawFace(rig.faceCanvas, { face: 'happy', blink: 0, look: [0, 0], mouth: mouthAt(shot.in + lt, ctx.words) });
        rig.faceTex.needsUpdate = true;
      }
      // fit the grid between the top of the frame and the captions, a little from above
      const px = raised([span[0], span[1], topText ? 470 : 300, 1230]);
      frameSpan(camera, px, { push: lerp(1.04, 0.98, inOut(lt / shot.dur)), orbit: 0.06 * Math.sin(lt * 0.35), lift: 0.6 });
    },
  };
};

// ---- sticky notes floating in the dark, the camera drifting through them
SHOTS.notes = async (el, shot) => {
  const items = (el.dataset.items || '').split(',').map((s) => s.trim()).filter(Boolean).slice(0, 8);
  if (!items.length) throw new Error('notes needs data-items, e.g. data-items="a launch video,a week of posts"');
  const light = (el.dataset.set || '').toLowerCase() === 'studio';
  const scene = new THREE.Scene();
  scene.environment = env;
  scene.environmentIntensity = 0.5;
  const bg = light ? new THREE.Color('#ece6dd').lerp(PAL.accent, 0.07) : PAL.bg.clone().lerp(PAL.accent, 0.05).multiplyScalar(0.7);
  scene.background = bg;
  scene.fog = new THREE.Fog(bg, 6, 15);
  scene.add(new THREE.HemisphereLight(0xffffff, bg, light ? 1.0 : 0.5));
  const key = new THREE.DirectionalLight('#fff4e6', light ? 1.8 : 2.2); key.position.set(-2, 3, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(PAL.accent, 1.2); rim.position.set(3, 1, -3); scene.add(rim);
  await document.fonts.load(`700 90px ${HAND}`);
  const paper = ['#fbf3c4', '#fde3d6', '#e3f1fb', '#f6f2ea'];
  const r = rng(13);
  const notes = items.map((text, i) => {
    const [c, g] = canvas2d(560, 560);
    g.fillStyle = paper[i % paper.length]; g.fillRect(0, 0, 560, 560);
    const grad = g.createLinearGradient(0, 0, 0, 560); grad.addColorStop(0, 'rgba(255,255,255,.25)'); grad.addColorStop(1, 'rgba(0,0,0,.06)');
    g.fillStyle = grad; g.fillRect(0, 0, 560, 560);
    g.fillStyle = 'rgba(255,255,255,.55)'; g.save(); g.translate(280, 22); g.rotate(-0.04); g.fillRect(-90, -20, 180, 46); g.restore();
    let size = 92, lines;
    const words = text.split(/\s+/);
    for (;;) {
      g.font = `700 ${size}px ${HAND}`;
      lines = []; let cur = '';
      for (const w of words) { const next = cur ? `${cur} ${w}` : w; if (g.measureText(next).width > 470 && cur) { lines.push(cur); cur = w; } else cur = next; }
      lines.push(cur);
      if ((lines.length * size * 1.1 <= 420 && lines.every((l) => g.measureText(l).width <= 490)) || size <= 48) break;
      size -= 6;
    }
    g.fillStyle = '#26232b'; g.textAlign = 'center'; g.textBaseline = 'middle';
    lines.forEach((l, k) => g.fillText(l, 280, 300 + (k - (lines.length - 1) / 2) * size * 1.1));
    const edge = new THREE.MeshStandardMaterial({ color: paper[i % paper.length], roughness: 0.9 });
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.78, 0.01), [edge, edge, edge, edge, new THREE.MeshStandardMaterial({ map: texture(c), roughness: 0.85 }), edge]);
    // scattered up the frame and back into the dark, nearest first, zig-zagging side to side
    const side = i % 2 ? 1 : -1;
    const z = -i * (3.2 / Math.max(1, items.length - 1));
    const x = side * (0.28 + 0.18 * r()) * (1 + i * 0.15) * (WIDE ? 2.6 : 1);
    const y = 1.8 + ((i % 3) - 1) * 0.58 + (r() - 0.5) * 0.2 + i * 0.05;
    scene.add(m);
    return { m, x, y, z, rot: [(r() - 0.5) * 0.25, (r() - 0.5) * 0.5, (r() - 0.5) * 0.35], phase: r() * 6.28, delay: (shot.first ? 0 : 0.1) + i * 0.12 };
  });
  const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 60);
  return {
    scene, camera, tone: light ? 'light' : 'dark',
    events: Object.fromEntries(notes.map((n, i) => [`note-${i + 1}`, shot.first ? 0 : n.delay])),
    update(lt) {
      for (const n of notes) {
        const k = shot.first ? 1 : out3((lt - n.delay) / 0.6);
        n.m.position.set(n.x, n.y + 0.06 * Math.sin(lt * 1.1 + n.phase) - (1 - k) * 0.6, n.z);
        n.m.rotation.set(n.rot[0] + 0.05 * Math.sin(lt * 0.9 + n.phase), n.rot[1] + 0.08 * Math.sin(lt * 0.7 + n.phase), n.rot[2]);
        n.m.scale.setScalar(Math.max(0.001, k));
      }
      // drift slowly forward into them
      const z = lerp(4.3, 4.3 - Math.min(1.6, 0.35 * shot.dur), inOut(lt / shot.dur));
      camera.position.set(0.2 * Math.sin(lt * 0.4), 1.5 + 0.08 * Math.sin(lt * 0.3), z);
      camera.lookAt(0, 1.62, z - 4);
    },
  };
};

// ---- a big button a cursor clicks (data-text, then data-done), the mascot cheering beside it
function cursorMesh() {
  const s = new THREE.Shape();
  [[0, 0], [0, -1], [0.27, -0.76], [0.45, -1.15], [0.6, -1.08], [0.43, -0.7], [0.75, -0.7]].forEach(([x, y], i) => (i ? s.lineTo(x, y) : s.moveTo(x, y)));
  s.closePath();
  const g = new THREE.Group();
  const fill = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.05, bevelEnabled: false }), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 }));
  const edge = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.04, bevelEnabled: true, bevelThickness: 0.01, bevelSize: 0.06, bevelSegments: 2 }), new THREE.MeshStandardMaterial({ color: 0x111114, roughness: 0.5 }));
  edge.position.z = -0.012;
  fill.castShadow = edge.castShadow = true;
  g.add(edge, fill);
  g.scale.setScalar(0.42);
  return g;
}
SHOTS.button = async (el, shot) => {
  const before = el.dataset.text || '☆ Star';
  const after = el.dataset.done || '★ Starred';
  const place = await buildSet(el);
  const { scene, camera } = place;
  await document.fonts.load(`800 120px ${FONT}`, before + after);
  const face = (text, bgCol, fg) => {
    const [c, g] = canvas2d(1024, 300);
    g.fillStyle = bgCol; g.beginPath(); g.roundRect(0, 0, 1024, 300, 150); g.fill();
    let size = 130;
    do { g.font = `800 ${size}px ${FONT}, ${EMOJI_FONT}`; size -= 6; } while (g.measureText(text).width > 860 && size > 60);
    g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(text, 512, 158);
    return texture(c);
  };
  const [BW, BH] = [1.9, 0.56];
  const offTex = face(before, '#17171d', '#ffffff');
  const onTex = face(after, hex(PAL.accent), '#ffffff');
  const button = new THREE.Group();
  const body = new THREE.Mesh(new RoundedBoxGeometry(BW, BH, 0.22, 6, BH / 2), plastic(PAL.ink, 0.35));
  body.castShadow = true;
  const top = new THREE.Mesh(new THREE.PlaneGeometry(BW, BH), new THREE.MeshBasicMaterial({ map: offTex, transparent: true, toneMapped: false }));
  top.position.z = 0.111;
  button.add(body, top);
  button.position.set(0, 2.85, 0.2);
  const cursor = cursorMesh();
  scene.add(button, cursor);
  const rig = buildMascot();
  scene.add(rig.root);
  const fx = confetti(scene, 70);
  const CLICK = shot.first ? 0.6 : 1.1;
  const total = parseFloat(document.body.dataset.duration) || 0;
  const topText = (shot.first && document.querySelector('.hook')) || (shot.in + shot.dur >= total - 0.05 && document.querySelector('.end'));
  const ctx = { words: [], t: 0, bpm: 112, drop: 0, propSide: 0, side: 1 };
  return {
    scene, camera, tone: place.tone, events: { click: CLICK },
    update(lt) {
      place.update(lt);
      const pressed = lt >= CLICK;
      const press = pulse(lt, CLICK - 0.06, CLICK, CLICK + 0.05, CLICK + 0.25);
      top.material.map = pressed ? onTex : offTex;
      body.material.color.copy(pressed ? PAL.accent.clone().multiplyScalar(0.85) : PAL.ink);
      button.position.z = 0.2 - 0.1 * press;
      button.scale.setScalar((shot.first ? 1 : back(lt / 0.5)) * (1 - 0.06 * press + 0.05 * pulse(lt, CLICK + 0.05, CLICK + 0.15, CLICK + 0.2, CLICK + 0.45)));
      button.rotation.set(0.04 * Math.sin(lt * 0.9), 0.06 * Math.sin(lt * 0.7), 0);
      // the cursor glides in from the bottom right, taps, and drifts off a little
      const k = inOut(clamp((lt - (CLICK - 0.85)) / 0.75));
      cursor.position.set(lerp(1.7, 0.35, k) + 0.08 * smooth(lt, CLICK + 0.2, CLICK + 0.8), lerp(1.2, 2.72, k) - 0.06 * press - 0.1 * smooth(lt, CLICK + 0.2, CLICK + 0.8), 0.45 - 0.08 * press);
      cursor.rotation.set(0, 0, 0.18);
      ctx.t = shot.in + lt; ctx.words = spokenWords();
      let p = ACTIONS.point(lt + 0.3, { ...ctx, propSide: 0 });
      p.head = [p.head[0] - 0.25, p.head[1], p.head[2]];
      p.look = [0, 0.8];
      p.handL = [0.62, 0.56, 0.16]; p.poleL = [0.8, -0.6, 0]; p.finger = [1, 0]; // pointing up at it
      if (pressed) p = mixPose(p, ACTIONS.cheer(lt - CLICK + 0.3, ctx), smooth(lt - CLICK, 0, 0.2));
      p.y *= 0.6;
      applyPose(rig, { ...alive(p, lt, 3.3), x: 0, z: -0.3 });
      drawFace(rig.faceCanvas, { face: pressed ? 'love' : 'happy', blink: 0, look: p.look, mouth: mouthAt(shot.in + lt, ctx.words) });
      rig.faceTex.needsUpdate = true;
      fx(lt, CLICK, V(0, 2.85, 0.3));
      frameSpan(camera, raised(topText ? [-0.02, 3.3, 560, 1330] : [-0.02, 3.3, 280, 1290]), { push: lerp(1.04, 0.98, inOut(lt / shot.dur)), orbit: 0.06 * Math.sin(lt * 0.3) });
    },
  };
};
"""
