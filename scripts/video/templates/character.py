"""The user's own character for the 3D template (3d.html): a rigged glTF model (.glb, from
Blender, Mixamo, Ready Player Me, VRoid, or any 3D tool) standing in for the robot mascot.
scene3d.py appends CHARACTER_JS to its engine after the mascot, and every shot the robot appears
in (mascot, desk, title, icons, button) takes the character instead when the page names one:
<body data-character="assets/hero.glb">, or data-character on one shot.

It plays the actions the same way the robot does. When the model has its own animation clip for
an action (a clip named "Wave", "Walking", "Dance", ...), it plays that clip, seeked to the frame's
time so render.js can still render any frame on its own. Otherwise its skeleton is posed from the
robot's poses: the bones are matched by name (Mixamo's mixamorig:LeftForeArm, Blender's
forearm.L, VRoid's J_Bip_L_LowerArm, ...), the arms and legs are solved with two-bone IK from the
same hand and foot targets, scaled to the character's own proportions, on top of its idle clip
when it has one. Its face follows the voice through its blend shapes (jawOpen, viseme_aa, A,
blink, smile, ...), or its jaw bone, or a small nod on the words when it has neither.
"""

CHARACTER_DOC = """  The user's own character in the mascot's place: data-character="assets/
  hero.glb" on <body> (every mascot shot) or on one shot. A rigged glTF
  model from Blender, Mixamo, Ready Player Me, or VRoid, exported as one
  .glb file (glTF binary; Draco or meshopt compression is fine; a VRoid
  .vrm works as it is). Its own clips play when their names match
  an action (Wave, Walking, Dance, ThumbsUp, Idle...); otherwise its skeleton
  is posed like the robot's. Its blend shapes (jawOpen, viseme_aa, blink,
  smile) or jaw bone lip-sync it to the voice."""

CHARACTER_JS = r"""
// ================= the user's own character: a rigged glTF model in the mascot's place =================
const CHAR_HEIGHT = 2.1; // the robot's height to the top of its head, so every framing still fits
const _cq1 = new THREE.Quaternion(), _cq2 = new THREE.Quaternion(), _cq3 = new THREE.Quaternion();
const _cv1 = new THREE.Vector3(), _cv2 = new THREE.Vector3(), _cv3 = new THREE.Vector3();

// one load per file, cloned for every shot that shows it
const charFiles = new Map();
function loadCharacterFile(src) {
  if (!charFiles.has(src)) {
    const loader = new GLTFLoader();
    const draco = new DRACOLoader();
    draco.setDecoderPath(import.meta.resolve('three/addons/libs/draco/gltf/')); // through the import map, so render.js serves it locally
    loader.setDRACOLoader(draco);
    loader.setMeshoptDecoder(MeshoptDecoder);
    // read with XHR, not fetch: a page opened from a file (as render.js opens it) may read local
    // files through XHR only. A .glb carries its textures inside, so nothing else is fetched.
    const bytes = new Promise((resolve, reject) => {
      const x = new XMLHttpRequest();
      x.open('GET', src);
      x.responseType = 'arraybuffer';
      x.onload = () => (x.response && x.response.byteLength ? resolve(x.response) : reject(new Error('empty or missing file')));
      x.onerror = () => reject(new Error('not found, or the browser may not read it'));
      x.send();
    });
    charFiles.set(src, bytes.then((b) => loader.parseAsync(b, src.replace(/[^/]*$/, '')))
      .catch((e) => { throw new Error(`character ${src} didn't load: ${e.message || e}`); }));
  }
  return charFiles.get(src);
}

// ---- matching bones by name, whatever tool named them
const SKIP_WORDS = new Set(['mixamorig', 'mixamo', 'j', 'bip', 'bip01', 'def', 'org', 'mch', 'b', 'bone', 'bones', 'jnt', 'joint', 'armature', 'c', 'cc', 'base', 'rig', 'sk', 'ik', 'fk']);
// "mixamorig:LeftForeArm", "forearm.L", "J_Bip_L_LowerArm" -> { side: 'L', base: 'forearm' / 'lowerarm' }
function boneKey(name) {
  const words = name.replace(/^.*[:|]/, '').replace(/([a-z0-9])([A-Z])/g, '$1 $2').split(/[^A-Za-z0-9]+/).map((w) => w.toLowerCase()).filter(Boolean);
  let side = '';
  const rest = [];
  for (const w of words) {
    if (w === 'left' || w === 'l') side = 'L';
    else if (w === 'right' || w === 'r') side = 'R';
    else if (!SKIP_WORDS.has(w)) rest.push(w);
  }
  return { side, base: rest.join('') };
}
// each part of the robot's rig, by the names it goes by (the first one found wins)
const BONE_NAMES = {
  hips: ['hips', 'pelvis', 'hip', 'root'],
  spine: ['spine', 'spine0', 'abdomen', 'spine01', 'waist', 'lowerback'],
  chest: ['upperchest', 'chest', 'spine2', 'spine02', 'torso', 'spine1', 'spine01', 'upperback'],
  neck: ['neck', 'neck1', 'neck01'],
  head: ['head'],
  jaw: ['jaw', 'chin'],
  clav: ['shoulder', 'clavicle', 'collar'],
  upper: ['upperarm', 'arm', 'uparm', 'armupper'],
  fore: ['forearm', 'lowerarm', 'elbow', 'armlower'],
  hand: ['hand', 'wrist', 'palm', 'palm2'],
  thigh: ['upleg', 'upperleg', 'thigh', 'legupper'],
  shin: ['leg', 'lowerleg', 'calf', 'shin', 'knee', 'leglower'],
  foot: ['foot', 'ankle'],
  toe: ['toebase', 'toe', 'toes', 'ball'],
};
function matchBones(bones) {
  const keyed = bones.map((b) => ({ b, ...boneKey(b.name) }));
  const find = (part, side) => {
    for (const name of BONE_NAMES[part]) {
      const hit = keyed.find((k) => k.base === name && k.side === side);
      if (hit) return hit.b;
    }
    return null;
  };
  const m = {};
  for (const part of ['hips', 'spine', 'chest', 'neck', 'head', 'jaw']) m[part] = find(part, '');
  for (const s of ['L', 'R']) for (const part of ['clav', 'upper', 'fore', 'hand', 'thigh', 'shin', 'foot', 'toe']) m[part + s] = find(part, s);
  if (m.chest === m.spine) m.chest = null;
  // a hand without its own bone: the forearm's first child (a palm), so the chain still has an end
  for (const s of ['L', 'R']) if (!m['hand' + s] && m['fore' + s]) m['hand' + s] = m['fore' + s].children.find((c) => c.isBone) || null;
  return m;
}

// ---- its own clips for the robot's actions, by name
const CLIP_NAMES = {
  wave: ['wave', 'waving', 'hello', 'greet', 'greeting'],
  walk: ['walk', 'walking'],
  dance: ['dance', 'dancing', 'samba', 'sambadance', 'hiphop', 'salsa'],
  cheer: ['cheer', 'cheering', 'victory', 'celebrate', 'celebration', 'jump'],
  thumbs: ['thumbsup', 'thumbs', 'thumbup'],
  talk: ['talk', 'talking', 'explain', 'speak', 'speaking'],
  think: ['think', 'thinking'],
  shrug: ['shrug', 'shrugging'],
  sad: ['sad', 'sadpose', 'sadidle', 'cry', 'crying', 'defeated'],
  wow: ['surprised', 'surprise', 'wow', 'shocked'],
  point: ['point', 'pointing'],
  present: ['present', 'presenting'],
  idle: ['idle', 'breathing', 'breathingidle', 'standing', 'stand', 'idle1'],
};
const clipKey = (name) => name.toLowerCase().replace(/^.*\|/, '').replace(/mixamo\.?com/, '').replace(/[^a-z0-9]/g, '');
function clipFor(clips, action) {
  const names = CLIP_NAMES[action] || [];
  const usable = clips.filter((c) => !/^(t|a|bind)pose/.test(clipKey(c.name)) && c.duration > 0.05);
  return usable.find((c) => names.includes(clipKey(c.name)))
    || usable.find((c) => names.some((n) => n.length > 3 && clipKey(c.name).startsWith(n))) || null;
}

// ---- its face: the blend shapes for each part of an expression, by the names they go by
const MORPH_NAMES = {
  mouth: ['jawopen', 'mouthopen', 'visemeaa', 'aa', 'a', 'vaa', 'vrcvaa', 'fclmtha', 'mouthaa', 'open'],
  blink: ['eyeblink', 'eyesclosed', 'eyeclosed', 'blink', 'fcleyeclose', 'eyesclose', 'eyeclose'],
  happy: ['mouthsmile', 'smile', 'happy', 'joy', 'fclalljoy', 'fclmthjoy'],
  sad: ['sad', 'sorrow', 'mouthfrown', 'frown', 'fclallsorrow'],
  wow: ['surprised', 'surprise', 'wow', 'shocked', 'fclallsurprised'],
};
function matchMorphs(meshes) {
  const out = Object.fromEntries(Object.keys(MORPH_NAMES).map((k) => [k, []]));
  for (const mesh of meshes) {
    for (const [name, index] of Object.entries(mesh.morphTargetDictionary || {})) {
      const n = name.toLowerCase().replace(/[^a-z0-9]/g, '');
      for (const [part, names] of Object.entries(MORPH_NAMES)) {
        if (names.some((a) => (a.length <= 3 ? n === a : n === a || n.startsWith(a)))) { out[part].push([mesh, index]); break; }
      }
    }
  }
  return out;
}
const FACE_MIX = { // how much of each blend shape the robot's faces call for
  normal: {}, happy: { happy: 0.75 }, love: { happy: 1 }, wink: { happy: 0.6 }, think: {}, meh: { sad: 0.3 }, sad: { sad: 0.85 }, wow: { wow: 1 },
};

// two-bone IK in world space for any skeleton: aims the upper bone so the middle joint lands where
// the chain bends toward `pole`, then the lower bone at the target. Works whatever way the bones
// point at rest, since it turns each bone by the rotation from where its child is to where it
// should be.
function aimBone(bone, child, at) {
  const from = child.getWorldPosition(_cv1).sub(bone.getWorldPosition(_cv3)).normalize();
  const to = _cv2.copy(at).sub(_cv3).normalize();
  if (from.lengthSq() < 1e-8 || to.lengthSq() < 1e-8) return;
  const turn = _cq1.setFromUnitVectors(from, to);
  const world = bone.getWorldQuaternion(_cq2).premultiply(turn);
  bone.quaternion.copy(bone.parent.getWorldQuaternion(_cq3).invert().multiply(world));
  bone.updateMatrixWorld(true);
}
function ikChain(a, b, c, target, pole, la, lb) {
  const s = a.getWorldPosition(new THREE.Vector3());
  const d = target.clone().sub(s);
  const len = Math.min(Math.max(d.length(), Math.abs(la - lb) + 1e-3), la + lb - 1e-3);
  const dir = d.normalize();
  const cosA = clamp((la * la + len * len - lb * lb) / (2 * la * len));
  const p = pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir)));
  if (p.lengthSq() < 1e-8) p.set(0, 0, -1);
  p.normalize();
  const mid = s.clone().add(dir.clone().multiplyScalar(la * cosA)).add(p.multiplyScalar(la * Math.sqrt(Math.max(0, 1 - cosA * cosA))));
  aimBone(a, b, mid);
  aimBone(b, c, s.add(dir.multiplyScalar(len)));
}

// The character, cloned for one shot, with the same face the robot shows the shots: root, j.chest
// (props), j.antenna and bulb (nothing to wobble or light), and pose(), face(), placeProp().
async function buildCharacter(src) {
  const gltf = await loadCharacterFile(src);
  const model = SkeletonUtils.clone(gltf.scene);
  const meshes = [];
  model.traverse((o) => {
    if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; meshes.push(o); }
  });
  const skinned = meshes.find((m) => m.isSkinnedMesh);
  const bones = [];
  model.traverse((o) => { if (o.isBone) bones.push(o); });
  const B = matchBones(bones);
  // a limb can be posed when each bone hangs from the one before it (some rigs drive their feet
  // from separate control bones; those legs keep their clip or bind pose)
  const chain = (...bs) => bs.every(Boolean) && bs.slice(1).every((b, i) => { for (let p = b.parent; p; p = p.parent) if (p === bs[i]) return true; return false; });
  const posable = !!B.hips && chain(B.upperL, B.foreL, B.handL) && chain(B.upperR, B.foreR, B.handR);
  const legs = posable && chain(B.thighL, B.shinL, B.footL) && chain(B.thighR, B.shinR, B.footR);
  const mixer = new THREE.AnimationMixer(model);
  const clips = gltf.animations || [];
  const idle = clipFor(clips, 'idle');

  // its bind pose, to reset to every frame (so each frame is a pure function of its time)
  const rest = bones.map((b) => [b, b.position.clone(), b.quaternion.clone(), b.scale.clone()]);
  const reset = () => { for (const [b, p, q, s] of rest) { b.position.copy(p); b.quaternion.copy(q); b.scale.copy(s); } };

  // stand it up: the right size, feet on the floor, centered, and facing the camera (+z); a model
  // facing away (toes behind the ankles) is turned round
  const holder = new THREE.Group(); // the shot moves this, like the robot's root
  const fit = new THREE.Group(); // this sizes and turns the model once
  fit.add(model);
  holder.add(fit);
  if (idle) { mixer.clipAction(idle).play(); mixer.setTime(0); }
  holder.updateMatrixWorld(true);
  const facingAway = B.footL && B.toeL && B.toeL.getWorldPosition(_cv1).z < B.footL.getWorldPosition(_cv2).z - 1e-4;
  if (facingAway) { fit.rotation.y = Math.PI; holder.updateMatrixWorld(true); }
  const box = new THREE.Box3().setFromObject(model, true);
  const k = CHAR_HEIGHT / Math.max(1e-6, box.max.y - box.min.y);
  fit.scale.setScalar(k);
  holder.updateMatrixWorld(true);
  box.setFromObject(model, true);
  const center = (B.hips ? B.hips.getWorldPosition(new THREE.Vector3()) : box.getCenter(new THREE.Vector3()));
  fit.position.set(-center.x, -box.min.y, -center.z);
  mixer.stopAllAction();
  reset();
  holder.updateMatrixWorld(true);

  // its proportions against the robot's, from the bind pose, in the holder's space (the robot's root space)
  const local = (b) => holder.worldToLocal(b.getWorldPosition(new THREE.Vector3()));
  const dims = {};
  if (posable) {
    dims.armL = local(B.foreL).distanceTo(local(B.upperL)); dims.foreL = local(B.handL).distanceTo(local(B.foreL));
    dims.armR = local(B.foreR).distanceTo(local(B.upperR)); dims.foreR = local(B.handR).distanceTo(local(B.foreR));
    dims.kArm = (dims.armL + dims.foreL) / (BONES.upper + BONES.fore);
    if (legs) {
      dims.thighL = local(B.shinL).distanceTo(local(B.thighL)); dims.shinL = local(B.footL).distanceTo(local(B.shinL));
      dims.thighR = local(B.shinR).distanceTo(local(B.thighR)); dims.shinR = local(B.footR).distanceTo(local(B.shinR));
      dims.kLeg = (dims.thighL + dims.shinL) / (BONES.thigh + BONES.shin);
      dims.ankleL = local(B.footL); dims.ankleR = local(B.footR);
    }
  }
  // the parts of the robot's rig the shots reach into
  const j = { chest: new THREE.Group(), antenna: new THREE.Object3D() };
  holder.add(j.chest);
  const morphs = matchMorphs(meshes);
  const hasMouth = morphs.mouth.length > 0;
  const chestBone = B.chest || B.spine || B.hips;
  const chestRest = chestBone ? chestBone.getWorldQuaternion(new THREE.Quaternion()).premultiply(holder.getWorldQuaternion(new THREE.Quaternion()).invert()) : new THREE.Quaternion();
  // the chest's current turn from its bind pose, in the holder's space
  const chestTurn = () => {
    if (!chestBone) return new THREE.Quaternion();
    const now = chestBone.getWorldQuaternion(new THREE.Quaternion()).premultiply(holder.getWorldQuaternion(_cq1).invert());
    return now.multiply(chestRest.clone().invert());
  };
  // a point in the robot's chest space, at the character's proportions: near a shoulder it's
  // placed from that shoulder, in the middle from between them
  const SH = 0.33, SHY = 0.13;
  const fromChest = (p, turn) => {
    const sL = local(B.upperL), sR = local(B.upperR);
    const w = clamp(0.5 + p.x / (2 * SH));
    const base = sR.clone().lerp(sL, w);
    const off = V(p.x - lerp(-SH, SH, w), p.y - SHY, p.z).multiplyScalar(dims.kArm).applyQuaternion(turn);
    return base.add(off);
  };
  const turnInHolder = (bone, euler) => {
    if (!bone) return;
    const q = _cq1.setFromEuler(new THREE.Euler(euler[0], euler[1], euler[2]));
    const hq = holder.getWorldQuaternion(_cq2);
    const dq = hq.clone().multiply(q).multiply(hq.clone().invert());
    const world = bone.getWorldQuaternion(_cq3).premultiply(dq);
    bone.quaternion.copy(bone.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(world));
    bone.updateMatrixWorld(true);
  };
  let said = 0;
  const arms = {}; // where each hand was sent this frame (world), so a held prop can move them with it
  const rig = {
    custom: true, root: holder, j, hands: null, bulb: { material: {} },
    // pose: the robot's pose; action and lt: the action it comes from, and how far in
    pose(p, action, lt = 0) {
      reset();
      holder.position.set(p.x, p.y, p.z);
      holder.rotation.set(0, p.turn, 0);
      const clip = action ? clipFor(clips, action) : null;
      const base = clip || (action ? idle : null);
      mixer.stopAllAction();
      if (base) { mixer.clipAction(base).play(); mixer.setTime(lt % Math.max(0.05, base.duration)); }
      // a clip that walks off on its own stays where the shot puts it
      if (base && B.hips) { const hp = rest.find((r) => r[0] === B.hips)[1]; B.hips.position.x = hp.x; B.hips.position.z = hp.z; }
      holder.updateMatrixWorld(true);
      if (!posable || clip) { // its own clip, or a model without a skeleton to pose: it moves as a whole
        if (!posable) holder.position.y += Math.max(0, -p.bob) * 0.3;
        if (!hasMouth && (B.head || B.neck)) turnInHolder(B.head || B.neck, [0.05 * said, 0, 0]);
        return;
      }
      // the body: the hips down for a crouch or a seat, then the spine, chest, and head
      if (legs) {
        const hipsWorld = B.hips.getWorldPosition(new THREE.Vector3());
        const down = holder.localToWorld(V(0, p.bob * dims.kLeg, 0)).sub(holder.getWorldPosition(_cv1));
        B.hips.position.copy(B.hips.parent.worldToLocal(hipsWorld.add(down)));
        B.hips.updateMatrixWorld(true);
      }
      turnInHolder(B.spine, [p.lean[0], 0, p.lean[1]]);
      turnInHolder(B.chest, p.chest);
      const nod = hasMouth ? 0 : 0.05 * said;
      turnInHolder(B.neck, [p.head[0] * 0.4, p.head[1] * 0.4, p.head[2] * 0.4]);
      turnInHolder(B.head || B.neck, [p.head[0] * (B.neck ? 0.6 : 1) + nod, p.head[1] * (B.neck ? 0.6 : 1), p.head[2] * (B.neck ? 0.6 : 1)]);
      if (p.shrug) { turnInHolder(B.clavL, [0, 0, 0.18 * p.shrug]); turnInHolder(B.clavR, [0, 0, -0.18 * p.shrug]); }
      if (B.jaw && !hasMouth) turnInHolder(B.jaw, [0.22 * said, 0, 0]);
      // the legs, from the robot's foot targets moved by as much (in the character's stride),
      // with the feet kept as they were at rest
      if (legs) {
        for (const s of ['L', 'R']) {
          const restFoot = REST['foot' + s];
          const f = p['foot' + s];
          const target = holder.localToWorld(dims['ankle' + s].clone().add(V(f[0] - restFoot[0], f[1] - restFoot[1], f[2] - restFoot[2]).multiplyScalar(dims.kLeg)));
          const footQ = B['foot' + s].getWorldQuaternion(new THREE.Quaternion());
          const knee = holder.localToWorld(V(s === 'L' ? 0.1 : -0.1, 0, 1)).sub(holder.getWorldPosition(_cv1));
          ikChain(B['thigh' + s], B['shin' + s], B['foot' + s], target, knee, dims['thigh' + s], dims['shin' + s]);
          B['foot' + s].quaternion.copy(B['foot' + s].parent.getWorldQuaternion(_cq1).invert().multiply(footQ));
          B['foot' + s].updateMatrixWorld(true);
        }
      }
      // the arms, from the robot's hand targets in its chest space
      const turn = chestTurn();
      for (const s of ['L', 'R']) {
        const h = p['hand' + s];
        const target = holder.localToWorld(fromChest(V(h[0], h[1], h[2]), turn));
        const pole = p['pole' + s] || (s === 'L' ? [0.55, -0.35, -0.75] : [-0.55, -0.35, -0.75]);
        const poleW = V(...pole).applyQuaternion(turn).applyQuaternion(holder.getWorldQuaternion(_cq1));
        ikChain(B['upper' + s], B['fore' + s], B['hand' + s], target, poleW, dims['arm' + s], dims['fore' + s]);
        arms[s] = { target, pole: poleW };
      }
    },
    face(f) {
      said = f.mouth || 0;
      for (const list of Object.values(morphs)) for (const [mesh, i] of list) mesh.morphTargetInfluences[i] = 0;
      const mix = FACE_MIX[f.face] || {};
      for (const [part, w] of Object.entries(mix)) for (const [mesh, i] of morphs[part]) mesh.morphTargetInfluences[i] = w;
      for (const [mesh, i] of morphs.mouth) mesh.morphTargetInfluences[i] = Math.min(1, 0.75 * said);
      for (const [mesh, i] of morphs.blink) mesh.morphTargetInfluences[i] = Math.max(f.blink || 0, f.face === 'wink' ? 1 : 0);
    },
    // a held prop where the robot would hold it, at a size that suits the character. The robot's
    // big head sits well above its hands; a person's doesn't, so a prop held in front of the face
    // (a laptop, a sign) comes down below the chin, and the hands holding it come down with it.
    placeProp(group, { pos, rot }) {
      const turn = chestTurn();
      group.quaternion.setFromEuler(new THREE.Euler(...rot)).premultiply(turn);
      if (!posable) { group.position.set(pos[0], pos[1] + 0.99, pos[2]); return; }
      group.position.copy(fromChest(V(...pos), turn));
      group.scale.setScalar(0.85 * Math.min(1, dims.kArm));
      const head = B.head || B.neck;
      if (!head) return;
      group.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(group);
      const chin = head.getWorldPosition(new THREE.Vector3());
      const reachX = 0.18 * holder.getWorldScale(_cv1).x; // about a head's width either side
      const front = box.min.x < chin.x + reachX && box.max.x > chin.x - reachX;
      const over = box.max.y - (chin.y - 0.04 * holder.getWorldScale(_cv1).y);
      if (!front || over <= 0) return;
      group.position.y -= over / holder.getWorldScale(_cv1).y;
      box.expandByScalar(0.25);
      for (const s of ['L', 'R']) {
        const a = arms[s];
        if (!a || !box.containsPoint(a.target)) continue;
        a.target.y -= over;
        ikChain(B['upper' + s], B['fore' + s], B['hand' + s], a.target, a.pole, dims['arm' + s], dims['fore' + s]);
      }
    },
  };
  return rig;
}

// The mascot a shot shows: the page's own character when it names one, or the robot.
async function mascotFor(el) {
  const src = (el && el.dataset.character) || document.body.dataset.character;
  return src ? buildCharacter(src) : buildMascot();
}
"""
