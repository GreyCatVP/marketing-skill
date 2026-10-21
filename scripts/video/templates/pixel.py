"""The pixel-art template (pixel.html): a narrated video whose backgrounds are pixel-art scenes
drawn on a 135x240 canvas (each pixel 8x8 on screen) in a 16-color palette plus the brand's
accent, with a game dialog box for the captions and chiptune music. build.py imports
PIXEL_TEMPLATES.

The engine is a library of shots, each a pure function of time: walk, boss, coins, levelup,
city, space, and photo (the user's own image, pixelated). The hero is an original robot.
"""
from drawn import NARRATED_CSS, TIMELINE_JS, drawn_body

SHOT_DOC = """  Shots (data-shot), each running from its --in until the next shot starts:
    walk     the robot walking through a scrolling landscape.
             data-time="day" (default), "sunset", or "night".
    boss     the robot fighting a slime with a health bar: the problem being
             beaten. Events: --hit, --hit-2, --hit-3, --ko.
    coins    the robot opening a chest of coins: a payoff, a saving, a win.
             Events: --open, --jump.
    levelup  the robot leveling up in a burst of light: a result, an upgrade.
             Event: --up.
    city     a night city with windows switching on: calm, a story, time passing.
    space    a rocket flying through stars: a launch, a hook, a CTA.
    photo    the user's own image (data-src="assets/photo.jpg"), pixelated into
             the palette and sharpening into view: a product, a logo, a place.
             Event: --sharp. Never a stand-in for a real person or result.
  data-sfx on a shot cues a sound on one of its events, e.g. data-sfx="coin:open";
  the 8-bit sounds (coin, jump, powerup, blip, hurt) suit them best."""

ENGINE_JS = r"""
// ---- canvas, palette, helpers
const PW = 135, PH = 240, GROUND = 150; // 135x240 pixels, each 8x8 on screen; the ground line
const cv = document.querySelector('canvas.art');
const g = cv.getContext('2d', { willReadFrequently: true });
g.imageSmoothingEnabled = false;
const PAL = {
  night: '#1a1c2c', purple: '#5d275d', red: '#b13e53', orange: '#ef7d57', yellow: '#ffcd75', lime: '#a7f070',
  green: '#38b764', teal: '#257179', navy: '#29366f', blue: '#3b5dc9', sky: '#41a6f6', cyan: '#73eff7',
  white: '#f4f4f4', grey: '#94b0c2', slate: '#566c86', dark: '#333c57',
};
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const toHex = (c) => `#${c.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('')}`;
const mix = (a, b, k) => toHex(rgb(a).map((v, i) => v + (rgb(b)[i] - v) * k));
const accentCss = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
PAL.accent = /^#[0-9a-f]{6}$/i.test(accentCss) ? accentCss : '#e07a55';
PAL.accentDark = mix(PAL.accent, '#000000', 0.38);
PAL.accentLight = mix(PAL.accent, '#ffffff', 0.4);
const clamp = (x) => Math.min(1, Math.max(0, x));
const lerp = (a, b, k) => a + (b - a) * k;
const out3 = (x) => 1 - (1 - clamp(x)) ** 3;
const hash = (a, b = 0, c = 0) => { let h = Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263) + Math.imul(c | 0, 2147483647); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const rect = (c, x, y, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const bayer = (x, y) => (BAYER[(y & 3) * 4 + (x & 3)] + 0.5) / 16;
// an offscreen canvas, painted once
function layer(w, h, paint) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const x = c.getContext('2d');
  x.imageSmoothingEnabled = false;
  paint(x, w, h);
  return c;
}
const dot = (x, c, px, py, w = 1, h = 1) => { x.fillStyle = c; x.fillRect(px, py, w, h); };
// A vertical gradient through palette colors, dithered rather than blended, the way the hardware did it.
function gradient(stops, h, w = PW) {
  return layer(w, h, (x) => {
    for (let py = 0; py < h; py++) {
      const t = py / Math.max(1, h - 1);
      let i = 0;
      while (i + 2 < stops.length && t > stops[i + 1][0]) i++;
      const [t0, c0] = stops[i];
      const [t1, c1] = stops[i + 1];
      const k = (t - t0) / Math.max(1e-6, t1 - t0);
      for (let px = 0; px < w; px++) dot(x, k > bayer(px, py) ? c1 : c0, px, py);
    }
  });
}
// A scrolling strip that wraps: drawn twice, at whole-pixel offsets.
function scroll(img, speed, lt, y = 0) {
  const off = Math.floor((speed * lt) % img.width);
  g.drawImage(img, -off, y);
  g.drawImage(img, img.width - off, y);
}
// A ridge of hills or mountains whose outline repeats every `w` pixels.
function ridge(w, base, amp, seed, fill, edge) {
  return layer(w, PH, (x) => {
    for (let px = 0; px < w; px++) {
      const a = (px / w) * Math.PI * 2;
      const top = Math.round(base - amp * (0.6 * Math.sin(2 * a + seed) + 0.3 * Math.sin(5 * a + seed * 2) + 0.15 * Math.sin(11 * a + seed * 3)));
      dot(x, fill, px, top, 1, PH - top);
      if (edge) dot(x, edge, px, top, 1, 1);
    }
  });
}
function clouds(w, seed, count, y0, y1) {
  return layer(w, PH, (x) => {
    for (let k = 0; k < count; k++) {
      const cx = Math.floor(hash(seed, k) * w), cy = Math.floor(lerp(y0, y1, hash(seed, k, 1)));
      const r = 4 + Math.floor(hash(seed, k, 2) * 4);
      const puffs = [[0, 0, r], [-r, 2, r - 1], [r, 2, r - 2], [-2 * r + 2, 4, r - 3], [2 * r - 2, 4, r - 3]];
      for (let px = -3 * r; px <= 3 * r; px++) {
        for (let py = -r; py <= 6; py++) {
          const inside = (dx, dy) => puffs.some(([ox, oy, rr]) => rr > 0 && (dx - ox) ** 2 + (dy - oy) ** 2 <= rr * rr) && dy <= 5;
          if (!inside(px, py)) continue;
          const c = !inside(px, py + 2) ? PAL.grey : PAL.white;
          dot(x, c, (cx + px + w) % w, cy + py);
        }
      }
    }
  });
}
// The ground: a grass edge over dark soil flecked with stones; repeats every 32 pixels.
function ground(w, grass = PAL.lime, turf = PAL.green, soil = PAL.dark) {
  return layer(w, PH - GROUND, (x) => {
    dot(x, soil, 0, 0, w, PH - GROUND);
    for (let px = 0; px < w; px++) {
      dot(x, grass, px, 0);
      dot(x, turf, px, 1, 1, 2 + (hash(px % 32, 7) > 0.7 ? 1 : 0));
      for (let py = 5; py < PH - GROUND; py += 1) if (hash(px % 32, py, 3) > 0.94) dot(x, PAL.slate, px, py);
    }
  });
}
function disc(cx, cy, r, c, shadeC) {
  for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) {
    if (x * x + y * y > r * r + r * 0.5) continue;
    rect(shadeC && x + y > r * 0.5 ? shadeC : c, cx + x, cy + y);
  }
}

// ---- the robot: an original mascot, 14x18, drawn from rows of letters
const ROBOT_TOP = [
  '......aa......',
  '......gg......',
  '...wwwwwwww...',
  '..wwwwwwwwww..',
  '..wkkkkkkkkw..',
  '..wkcckkcckw..',
  '..wkcckkcckw..',
  '..wkkkkkkkkw..',
  '..wwwwwwwwww..',
  '...gwwwwwwg...',
  '....aaaaaa....',
  '..gaaayyaaag..',
  '..gaaaaaaaag..',
  '..w.aaaaaa.w..',
  '....AAAAAA....',
];
const ROBOT_LEGS = {
  stand: ['....dd..dd....', '....dd..dd....', '...ddd..ddd...'],
  stride: ['...dd....dd...', '..dd......dd..', '..dd......dd..'],
  pass: ['.....dddd.....', '.....d..d.....', '....dd..dd....'],
  jump: ['...dd....dd...', '...d......d...', '..............'],
};
// Draws rows of letters at `scale` canvas pixels per sprite pixel; '.' is see-through.
function sprite(rows, colors, x, y, scale = 2) {
  rows.forEach((row, r) => {
    for (let c = 0; c < row.length; c++) if (row[c] !== '.') rect(colors[row[c]], x + c * scale, y + r * scale, scale, scale);
  });
}
const SPRITE_COLORS = () => ({ a: PAL.accent, A: PAL.accentDark, g: PAL.grey, w: PAL.white, k: PAL.night, c: PAL.cyan, y: PAL.yellow, d: PAL.dark });
// The robot is drawn at 2x (28x36 canvas pixels, 224x288 on screen) so it reads on a phone;
// x, y is its top left, so it stands on the ground at y = GROUND - 36.
const robot = (x, y, pose = 'stand') => sprite([...ROBOT_TOP, ...ROBOT_LEGS[pose]], SPRITE_COLORS(), Math.round(x), Math.round(y));
const CHEST_SHUT = ['kkkkkkkkkkkk', 'kaaaaaaaaaak', 'kaaaaaaaaaak', 'kyyyyyyyyyyk', 'kAAAAyyAAAAk', 'kAAAAyyAAAAk', 'kAAAAAAAAAAk', 'kAAAAAAAAAAk', 'kkkkkkkkkkkk'];
const CHEST_OPEN = ['.kkkkkkkkkk.', 'kaaaaaaaaaak', 'kyyyyyyyyyyk', 'kkkkkkkkkkkk', 'kyyyyyyyyyyk', 'kAAAAyyAAAAk', 'kAAAAAAAAAAk', 'kAAAAAAAAAAk', 'kAAAAAAAAAAk', 'kkkkkkkkkkkk'];
const walkPose = (lt, rate = 8) => ['stride', 'stand', 'pass', 'stand'][Math.floor(lt * rate) % 4];

// ---- the shots
const SHOTS = {};
const SKIES = {
  day: [[0, PAL.blue], [0.55, PAL.sky], [1, PAL.cyan]],
  sunset: [[0, PAL.purple], [0.45, PAL.red], [0.8, PAL.orange], [1, PAL.yellow]],
  night: [[0, PAL.night], [0.6, PAL.navy], [1, PAL.blue]],
};

// A landscape scrolling past the walking robot.
SHOTS.walk = async (el) => {
  const time = SKIES[el.dataset.time] ? el.dataset.time : 'day';
  const sky = gradient(SKIES[time], GROUND);
  const far = ridge(270, 112, 16, 1.3, time === 'night' ? PAL.navy : time === 'sunset' ? PAL.purple : PAL.slate, null);
  const near = ridge(270, 132, 9, 4.1, time === 'night' ? PAL.dark : PAL.teal, time === 'night' ? PAL.slate : PAL.green);
  const sky2 = clouds(270, 3, 4, 26, 70);
  const soil = ground(270, time === 'night' ? PAL.teal : PAL.lime, time === 'night' ? PAL.dark : PAL.green, time === 'night' ? PAL.night : PAL.dark);
  return {
    draw(lt) {
      g.drawImage(sky, 0, 0);
      if (time === 'night') {
        for (let k = 0; k < 40; k++) if (hash(k, Math.floor(lt * 3 + k)) > 0.25) rect(PAL.white, hash(k, 1) * PW, hash(k, 2) * 100);
        disc(100, 34, 9, PAL.white, PAL.grey);
      } else disc(time === 'sunset' ? 67 : 104, time === 'sunset' ? 104 : 30, time === 'sunset' ? 16 : 10, PAL.yellow, time === 'sunset' ? PAL.orange : null);
      if (time !== 'night') scroll(sky2, 3, lt);
      scroll(far, 5, lt);
      scroll(near, 13, lt);
      scroll(soil, 30, lt, GROUND);
      const pose = walkPose(lt);
      robot(53, GROUND - 36 - (pose === 'pass' ? 2 : 0), pose);
    },
  };
};

// The robot beating a slime, its health bar dropping hit by hit: the problem, defeated.
SHOTS.boss = async () => {
  const sky = gradient([[0, PAL.night], [0.7, PAL.purple], [1, PAL.red]], GROUND);
  const far = ridge(270, 120, 14, 2.2, PAL.dark, PAL.purple);
  const soil = ground(270, PAL.slate, PAL.dark, PAL.night);
  const HITS = [0.7, 1.3, 1.9], KO = 2.3;
  const BX = 96, BW = 22;
  const slime = (lt, flash) => {
    const squash = 1 + 0.06 * Math.sin(lt * 7);
    const rw = Math.round(BW * squash), rh = Math.round(30 / squash);
    for (let y = -rh; y <= 0; y++) for (let x = -rw; x <= rw; x++) {
      const e = (x / rw) ** 2 + ((y + 2) / rh) ** 2;
      if (e > 1) continue;
      let c = e > 0.82 || x > rw * 0.55 ? PAL.purple : PAL.red;
      if ((x + rw * 0.45) ** 2 + (y + rh * 0.6) ** 2 < 20) c = PAL.orange;
      rect(flash ? PAL.white : c, BX + x, GROUND + y);
    }
    if (flash) return;
    const ey = GROUND - Math.round(rh * 0.62);
    for (const ex of [-9, 4]) {
      rect(PAL.white, BX + ex, ey, 5, 5);
      rect(PAL.night, BX + ex + (ex < 0 ? 0 : 2), ey + 2, 3, 3);
      for (let i = 0; i < 5; i++) rect(PAL.night, BX + ex + i, ey - 3 + (ex < 0 ? Math.floor(i / 2) : 2 - Math.floor(i / 2)));
    }
    rect(PAL.night, BX - 8, ey + 9, 17, 4);
    for (let i = 0; i < 4; i++) rect(PAL.white, BX - 7 + i * 4, ey + 9, 2, 2);
  };
  return {
    events: { hit: HITS[0], 'hit-2': HITS[1], 'hit-3': HITS[2], ko: KO },
    draw(lt) {
      g.drawImage(sky, 0, 0);
      scroll(far, 0, lt);
      g.drawImage(soil, 0, GROUND);
      // the robot dashes in for each hit and back
      let rx = 8;
      for (const h of HITS) {
        if (lt > h - 0.15 && lt < h) rx = lerp(8, 46, (lt - (h - 0.15)) / 0.15);
        else if (lt >= h && lt < h + 0.25) rx = lerp(46, 8, (lt - h) / 0.25);
      }
      robot(rx, GROUND - 36, rx > 10 ? 'stride' : 'stand');
      const hitsTaken = HITS.filter((h) => lt >= h).length;
      if (lt < KO) {
        slime(lt, HITS.some((h) => lt >= h && lt < h + 0.1));
        // health bar: white frame, red fill, and the lost part flashing as it drains
        const hp = 1 - hitsTaken / HITS.length;
        const last = HITS[hitsTaken - 1];
        const drain = hitsTaken ? clamp((lt - last) / 0.35) : 1;
        const shown = hp + (1 - drain) / HITS.length;
        rect(PAL.white, BX - 21, GROUND - 46, 42, 6);
        rect(PAL.night, BX - 20, GROUND - 45, 40, 4);
        rect(PAL.yellow, BX - 20, GROUND - 45, Math.round(40 * shown), 4);
        rect(PAL.red, BX - 20, GROUND - 45, Math.round(40 * hp), 4);
      } else {
        const k = (lt - KO) / 0.6;
        for (let i = 0; i < 26 && k < 1; i++) {
          const a = hash(i, 9) * 6.28, d = out3(k) * (14 + hash(i, 8) * 20);
          rect(i % 3 ? PAL.red : PAL.white, BX + Math.cos(a) * d, GROUND - 14 + Math.sin(a) * d - k * 10, 2, 2);
        }
      }
      // a slash on each hit
      for (const h of HITS) {
        const k = (lt - h) / 0.18;
        if (k < 0 || k > 1) continue;
        for (let i = 0; i < 12; i++) rect(PAL.white, BX - 14 + i * 2, GROUND - 34 + i * 2 - Math.round(k * 4), 2, 1);
      }
    },
  };
};

// The robot walking up to a chest that bursts with coins.
SHOTS.coins = async (el, shot) => {
  const sky = gradient(SKIES.day, GROUND);
  const hills = ridge(270, 130, 10, 0.7, PAL.teal, PAL.green);
  const sky2 = clouds(270, 8, 4, 24, 66);
  const soil = ground(270);
  const OPEN = 1.0, JUMP = 1.25, CX = 92;
  const coins = Array.from({ length: 14 }, (_, i) => ({ t0: OPEN + i * 0.07, vx: (hash(i, 1) - 0.5) * 150, vy: -110 - hash(i, 2) * 60 }));
  const coin = (x, y, lt) => {
    const w = [6, 4, 2, 4][Math.floor(lt * 14) % 4];
    for (let py = 0; py < 6; py++) for (let px = 0; px < w; px++) {
      const edge = py === 0 || py === 5 || px === 0 || px === w - 1;
      rect(edge ? PAL.orange : px === 1 && py === 1 && w > 2 ? PAL.white : PAL.yellow, x - w / 2 + px, y + py);
    }
  };
  return {
    events: { open: OPEN, jump: JUMP },
    draw(lt) {
      g.drawImage(sky, 0, 0);
      scroll(sky2, 3, lt);
      scroll(hills, 0, lt);
      g.drawImage(soil, 0, GROUND);
      // the chest: shut until OPEN, then its lid flips up
      const open = lt >= OPEN;
      sprite(open ? CHEST_OPEN : CHEST_SHUT, SPRITE_COLORS(), CX - 12, GROUND - (open ? 20 : 18));
      const arrive = shot.first ? 0 : 0.8;
      const rx = lerp(-24, CX - 44, clamp(lt / Math.max(arrive, 0.001)));
      const jt = (lt - JUMP) / 0.45;
      const jy = jt > 0 && jt < 1 ? Math.round(-28 * 4 * jt * (1 - jt)) : 0;
      robot(rx, GROUND - 36 + jy, jt > 0 && jt < 1 ? 'jump' : lt < arrive ? walkPose(lt) : 'stand');
      for (const c of coins) {
        const t = lt - c.t0;
        if (t < 0 || t > 1.6) continue;
        const y = GROUND - 22 + c.vy * t + 170 * t * t;
        if (y > GROUND + 4) continue;
        coin(CX + c.vx * t, y, lt + c.t0);
      }
    },
  };
};

// The robot leveling up: rays, rising sparkles, a flash.
SHOTS.levelup = async (el, shot) => {
  const sky = gradient([[0, PAL.night], [0.6, PAL.navy], [1, PAL.purple]], GROUND);
  const UP = shot.first ? 0.3 : 0.6;
  const CX = 67, CY = 100;
  return {
    events: { up: UP },
    draw(lt) {
      g.drawImage(sky, 0, 0);
      // rotating rays behind, as a sparse dither of the accent
      const spin = lt * 0.6;
      for (let y = 20; y < GROUND; y++) for (let x = 0; x < PW; x++) {
        const a = Math.atan2(y - CY, x - CX) + spin;
        if (Math.floor(((a + 6.2832) % 6.2832) / (Math.PI / 8)) % 2 === 0 && bayer(x, y) < 0.22) rect(PAL.accentDark, x, y);
      }
      rect(PAL.dark, 0, GROUND, PW, PH - GROUND);
      rect(PAL.night, 40, GROUND, 55, 6);
      rect(PAL.accent, 40, GROUND, 55, 1);
      const jt = (lt - UP) / 0.4;
      const jy = jt > 0 && jt < 1 ? Math.round(-24 * 4 * jt * (1 - jt)) : 0;
      robot(53, GROUND - 36 + jy, jt > 0 && jt < 1 ? 'jump' : 'stand');
      for (let i = 0; i < 22; i++) {
        const p = (lt * (0.35 + hash(i, 4) * 0.4) + hash(i, 5)) % 1;
        const x = 30 + hash(i, 6) * 75, y = GROUND - p * 120;
        const c = i % 3 ? PAL.yellow : PAL.white;
        rect(c, x, y);
        if (hash(i, Math.floor(lt * 6)) > 0.5) { rect(c, x - 1, y); rect(c, x + 1, y); rect(c, x, y - 1); rect(c, x, y + 1); }
      }
      const f = (lt - UP) / 0.25;
      if (f > 0 && f < 1) { g.globalAlpha = 1 - f; rect(PAL.white, 0, 0, PW, PH); g.globalAlpha = 1; }
    },
  };
};

// A night city scrolling slowly, its windows switching on and off.
SHOTS.city = async () => {
  const sky = gradient([[0, PAL.night], [0.7, PAL.navy], [1, PAL.purple]], GROUND + 10);
  const blocks = (seed, minH, maxH) => {
    const out = [];
    for (let x = 0, i = 0; x < 270; i++) {
      const w = 10 + Math.floor(hash(seed, i) * 14);
      out.push({ x, w, h: Math.floor(lerp(minH, maxH, hash(seed, i, 1))) });
      x += w + 1;
    }
    return out;
  };
  const far = blocks(1, 30, 70), near = blocks(2, 20, 55);
  const drawBlocks = (list, speed, lt, color, windows) => {
    const off = Math.floor((speed * lt) % 270);
    for (const b of list) for (const shift of [0, 270]) {
      const x = b.x - off + shift;
      if (x > PW || x + b.w < 0) continue;
      rect(color, x, GROUND - b.h, b.w, b.h);
      if (!windows) continue;
      for (let wy = GROUND - b.h + 3; wy < GROUND - 3; wy += 4) for (let wx = x + 2; wx < x + b.w - 2; wx += 3) {
        if (hash(b.x + wx - x, wy, Math.floor(lt * 0.8 + hash(b.x, wy) * 5)) > 0.55) rect(PAL.yellow, wx, wy);
      }
    }
  };
  return {
    draw(lt) {
      g.drawImage(sky, 0, 0);
      for (let k = 0; k < 45; k++) if (hash(k, Math.floor(lt * 2 + k * 0.37)) > 0.2) rect(k % 5 ? PAL.grey : PAL.white, hash(k, 1) * PW, hash(k, 2) * 90);
      disc(98, 40, 10, PAL.white, PAL.grey);
      rect(PAL.grey, 94, 37, 2, 2); rect(PAL.grey, 100, 44, 3, 2);
      drawBlocks(far, 3, lt, PAL.navy, false);
      drawBlocks(near, 8, lt, PAL.dark, true);
      rect(PAL.night, 0, GROUND, PW, PH - GROUND);
      const dash = Math.floor((lt * 30) % 12);
      for (let x = -dash; x < PW; x += 12) rect(PAL.slate, x, GROUND + 8, 6, 1);
    },
  };
};

// A rocket flying up through streaming stars, past a ringed planet.
SHOTS.space = async () => {
  const sky = gradient([[0, PAL.night], [1, PAL.navy]], PH);
  const stars = Array.from({ length: 90 }, (_, i) => ({ x: hash(i, 1) * PW, y: hash(i, 2) * PH, speed: [12, 30, 70][i % 3] }));
  const RX = 61, RY = 60;
  return {
    draw(lt) {
      g.drawImage(sky, 0, 0);
      for (const s of stars) {
        const y = (s.y + s.speed * lt) % PH;
        rect(s.speed > 60 ? PAL.white : s.speed > 20 ? PAL.grey : PAL.slate, s.x, y, 1, s.speed > 60 ? 3 : 1);
      }
      // the planet, lit from the upper right, with a ring
      const py = 128 + lt * 5;
      for (let y = -20; y <= 20; y++) for (let x = -20; x <= 20; x++) {
        if (x * x + y * y > 400) continue;
        const light = (x - y) / 40 + 0.5;
        rect(light > 0.7 ? PAL.accentLight : light > 0.35 || bayer(x + 40, y + 40) < light ? PAL.accent : PAL.accentDark, 30 + x, py + y);
      }
      for (let x = -32; x <= 32; x++) { const y = Math.round(x * 0.22); if (Math.abs(x) > 19 || y > 0) rect(PAL.cyan, 30 + x, py + y); }
      // the rocket
      const bob = Math.round(Math.sin(lt * 3) * 2);
      const x0 = RX, y0 = RY + bob;
      const flame = Math.floor(lt * 14) % 3;
      for (let i = 0; i < 6 + flame * 2; i++) rect(i < 3 ? PAL.yellow : i < 6 ? PAL.orange : PAL.red, x0 + 3 + (i % 2), y0 + 30 + i, 4 - (i > 5 ? 2 : 0), 1);
      for (let y = 0; y < 30; y++) {
        const half = y < 8 ? Math.ceil((y + 1) * 0.75) : 6;
        for (let x = -half; x < half; x++) rect(x > 2 ? PAL.grey : PAL.white, x0 + 5 + x, y0 + y);
      }
      disc(x0 + 5, y0 + 13, 3, PAL.cyan, PAL.blue);
      rect(PAL.accent, x0 - 4, y0 + 22, 3, 9); rect(PAL.accent, x0 + 12, y0 + 22, 3, 9);
      rect(PAL.accent, x0 - 1, y0 + 26, 12, 3);
    },
  };
};

// The user's own image, pixelated into the palette with ordered dithering, sharpening into view.
SHOTS.photo = async (el, shot) => {
  const bg = gradient([[0, PAL.night], [1, PAL.navy]], PH);
  const SHARP = shot.first ? 0 : 0.9;
  const colors = Object.values(PAL).map(rgb);
  let pic = null;
  if (el.dataset.src) {
    const img = await new Promise((resolve, reject) => {
      const im = new Image();
      im.onload = () => resolve(im);
      im.onerror = () => reject(new Error(`image didn't load: ${el.dataset.src}`));
      im.src = el.dataset.src;
    });
    const k = Math.min(100 / img.width, 110 / img.height);
    const w = Math.max(8, Math.round(img.width * k)), h = Math.max(8, Math.round(img.height * k));
    pic = layer(w, h, (x) => {
      x.imageSmoothingEnabled = true;
      x.drawImage(img, 0, 0, w, h);
      let data;
      try { data = x.getImageData(0, 0, w, h); } catch { return; } // a browser preview may refuse a local file
      const d = data.data;
      for (let i = 0; i < w * h; i++) {
        const t = (bayer(i % w, Math.floor(i / w)) - 0.5) * 48;
        const p = [d[i * 4] + t, d[i * 4 + 1] + t, d[i * 4 + 2] + t];
        let best = colors[0], bd = Infinity;
        for (const c of colors) { const e = (c[0] - p[0]) ** 2 * 0.3 + (c[1] - p[1]) ** 2 * 0.59 + (c[2] - p[2]) ** 2 * 0.11; if (e < bd) { bd = e; best = c; } }
        d[i * 4] = best[0]; d[i * 4 + 1] = best[1]; d[i * 4 + 2] = best[2]; d[i * 4 + 3] = 255;
      }
      x.putImageData(data, 0, 0);
    });
  }
  if (!pic) { // a framed landscape icon in its place: nothing real is implied
    pic = layer(80, 60, (x) => {
      dot(x, PAL.sky, 0, 0, 80, 60);
      for (let px = 0; px < 80; px++) { const top = 34 - Math.round(14 * Math.max(0, 1 - Math.abs(px - 30) / 22)); dot(x, PAL.teal, px, top, 1, 60 - top); }
      for (let px = 0; px < 80; px++) { const top = 44 - Math.round(10 * Math.max(0, 1 - Math.abs(px - 60) / 20)); dot(x, PAL.green, px, top, 1, 60 - top); }
      for (let y = -6; y <= 6; y++) for (let px = -6; px <= 6; px++) if (px * px + y * y <= 36) dot(x, PAL.yellow, 62 + px, 14 + y);
    });
  }
  const w = pic.width, h = pic.height;
  const x0 = Math.round((PW - w) / 2), y0 = Math.round(95 - h / 2);
  const small = document.createElement('canvas');
  return {
    events: { sharp: SHARP },
    draw(lt) {
      g.drawImage(bg, 0, 0);
      rect(PAL.night, x0 - 3, y0 - 3 + 4, w + 6, h + 6);
      rect(PAL.white, x0 - 3, y0 - 3, w + 6, h + 6);
      rect(PAL.accent, x0 - 2, y0 - 2, w + 4, h + 4);
      const block = SHARP ? [16, 8, 4, 2, 1][Math.min(4, Math.floor((lt / SHARP) * 5))] : 1;
      if (block === 1) g.drawImage(pic, x0, y0);
      else {
        small.width = Math.ceil(w / block); small.height = Math.ceil(h / block);
        const s = small.getContext('2d');
        s.imageSmoothingEnabled = false;
        s.drawImage(pic, 0, 0, small.width, small.height);
        g.save();
        g.beginPath();
        g.rect(x0, y0, w, h); // the last row and column of blocks overhang the picture
        g.clip();
        g.drawImage(small, 0, 0, small.width, small.height, x0, y0, small.width * block, small.height * block);
        g.restore();
      }
    },
  };
};

// Cuts between shots dissolve through the night color in 3x3 blocks, in dither order.
const FADE = 0.2;
const draw = (view, lt, shot) => {
  view.draw(lt);
  const k = Math.max(shot.first ? 0 : 1 - lt / FADE, 1 - (shot.dur - lt) / FADE, 0);
  if (k <= 0) return;
  g.fillStyle = PAL.night;
  for (let y = 0; y < PH; y += 3) for (let x = 0; x < PW; x += 3) if (bayer(x / 3, y / 3) < k) g.fillRect(x, y, 3, 3);
};
"""

LINES = [
    (0.2, "Every freelancer starts at level one."),
    (3.0, "The first boss? Invoices paid late."),
    (6.2, "Send yours the day the work ends, and the coins roll in."),
    (9.8, "One habit, one level up."),
    (12.3, "Follow for one money habit a week."),
]

PIXEL_TEMPLATES = {}
PIXEL_TEMPLATES["pixel.html"] = dict(
    bgs=[],
    g1="#000", g2="#000",
    doc=f"""  Template: pixel art, narrated (references/video-types.md: explainer,
  educational, brand story; and everyday posts that play like a game). 15.5
  seconds: a voiceover over pixel-art scenes with an original robot hero,
  captions in a game dialog box synced to the voice, chiptune music, and the
  hook on screen from the very first frame.

  Usually made by scripts/video/compose.js with "style: pixel" in the
  script's frontmatter: it voices the script, gives each line a shot
  ([shot: boss] on a line picks one), times everything to the voice, and
  writes this page. By hand, it works like 3d.html: a scene per line with
  <div class="say auto" data-voice="..." style="--voice:...">, and an empty
  <div class="shot" data-shot="..." style="--in:...">, usually one per line.

{SHOT_DOC}

  How it draws: window.renderFrame(t) paints the frame for time t on a
  135x240 canvas, scaled up 8x with hard pixel edges, so it's frame-exact.
  The robot's suit takes --accent, so brand.js recolors it. The copy is a
  playful default for a fictional invoicing app; rewrite it in the brand's
  voice. The text uses Pixelify Sans, a pixel font from Google Fonts.""",
    body_attrs='class="pixel" data-duration="15.5" data-drop="3.0" data-music="chiptune" data-bpm="150" data-key="C" data-mode="major" data-energy="2" data-motif="1 5 3 5 | 4 6 5 -"',
    css=NARRATED_CSS + """  .art { image-rendering: pixelated; }
  .art-scrim { display: none; }
  html body.pixel { font-family: "Pixelify Sans", "Noto Color Emoji", monospace; }
  .pixel .cap { font-weight: 700; }
  .pixel .cap > span { background: #f4f4f4; color: #1a1c2c; border-radius: 0; padding: .04em .3em; box-shadow: 0 8px 0 #1a1c2c; }
  .pixel .cap.hl > span { background: var(--accent); color: #fff; }
  .pixel .hook { font-size: 64px; line-height: 1.5; }
  /* captions in a game dialog box */
  .pixel .say { font-size: 64px; font-weight: 700; line-height: 1.25; -webkit-text-stroke: 0; paint-order: normal;
                text-shadow: 5px 5px 0 #1a1c2c; --hi: #ffcd75; }
  .pixel .narr .say { background: rgba(26, 28, 44, .92); border: 6px solid #f4f4f4; box-shadow: 0 0 0 6px #1a1c2c, 0 14px 0 6px rgba(26, 28, 44, .5);
                      align-self: stretch; padding: 20px 28px; min-height: 220px; animation: fadeIn .15s steps(3) var(--voice, 0s) both; }
""",
    head_extra="""<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&display=block">
<script type="module">""" + ENGINE_JS + TIMELINE_JS + """</script>
""",
    body=drawn_body(
        '<canvas class="art" width="135" height="240" data-lint="off"></canvas>',
        [(0, "walk", ""),
         (3.0, "boss", ' data-sfx="hurt:hit hurt:ko"'),
         (6.2, "coins", ' data-sfx="coin:open"'),
         (9.8, "levelup", ' data-sfx="powerup:up"'),
         (12.3, "space", "")],
        LINES, "freelancing is basically a video game", "one money habit a week"),
)
