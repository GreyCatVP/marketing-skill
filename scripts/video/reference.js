#!/usr/bin/env node
'use strict';
/*
 * Reads how a reference video is edited, so a new video can be made the same way: every cut and
 * how long each shot holds, whether the camera moves through long takes or cuts, how much moves on
 * screen, how bright it is and in what colors, how long the hook holds before the first cut, its
 * tempo and whether the cuts land on the beat, and how loud it is. It also writes a numbered
 * sheet of one frame per shot: the captions (size, case, boxed or not, where they sit), the
 * framing, what's on screen, and the transitions are read from it by eye. Then it writes a plan
 * in compose.js's own settings to match.
 *
 * Usage:
 *   node reference.js <video> [--out <dir>] [--json]
 *
 * Writes <dir>/reference.md (the read and the plan), reference.json, and sheet-1.jpg, sheet-2.jpg
 * ... (default dir: <video name>-reference/ next to the video). --json prints reference.json.
 *
 * It copies how a video is edited, never what's in it: none of its footage, music, characters,
 * logos, or words go into the new video. Runs locally with ffmpeg; no service or key.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { analyseTrack } = require('./beats');

const CUT = 0.3; // ffmpeg's scene score for a hard cut
const W = 64, H = 36; // the size frames are read at, for motion and color
const MAX_FRAMES = 60; // on the sheets; a busier video is sampled evenly
const WORDS_PER_SEC = 2.6; // a voiceover's usual pace

function fail(message) {
  console.error(message);
  process.exit(2);
}

function parseArgs(argv) {
  const args = { positional: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') args.out = argv[++i];
    else if (a === '--json') args.json = true;
    else if (a === '-h' || a === '--help') args.help = true;
    else args.positional.push(a);
  }
  return args;
}

const ffmpeg = (args, opts = {}) => spawnSync('ffmpeg', ['-hide_banner', '-nostdin', ...args], { maxBuffer: 1 << 30, ...opts });
const round = (v, d = 2) => Math.round(v * 10 ** d) / 10 ** d;
const clock = (t) => `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`;
const median = (v) => { const s = [...v].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : 0; };
const mean = (v) => (v.length ? v.reduce((s, x) => s + x, 0) / v.length : 0);

function probe(file) {
  const run = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate:format=duration', '-of', 'json', file], { encoding: 'utf8' });
  if (run.error) fail('ffprobe (part of ffmpeg) is needed: install ffmpeg first.');
  if (run.status !== 0) fail(`Couldn't read ${file}: ${run.stderr.trim()}`);
  const info = JSON.parse(run.stdout);
  const video = info.streams.find((s) => s.codec_type === 'video');
  if (!video) fail(`${file} has no video stream.`);
  const [n, d] = (video.r_frame_rate || '30/1').split('/').map(Number);
  return { width: video.width, height: video.height, fps: d ? n / d : 30, duration: parseFloat(info.format.duration), audio: info.streams.some((s) => s.codec_type === 'audio') };
}

// Hard cuts, from ffmpeg's scene-change score on a small copy of the picture.
function findCuts(file) {
  const run = ffmpeg(['-i', file, '-an', '-vf', `scale=320:-2,select='gt(scene,${CUT})',showinfo`, '-f', 'null', '-'], { encoding: 'utf8' });
  return [...(run.stderr || '').matchAll(/pts_time:([\d.]+)/g)].map((m) => parseFloat(m[1]));
}

// The whole video at W x H and `fps` frames a second, as RGB bytes.
function readFrames(file, fps) {
  const run = ffmpeg(['-v', 'error', '-i', file, '-an', '-vf', `fps=${fps},scale=${W}:${H}:flags=area`, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']);
  if (run.status !== 0) fail(`ffmpeg couldn't decode ${file}: ${run.stderr.toString().trim()}`);
  const size = W * H * 3;
  const frames = [];
  for (let o = 0; o + size <= run.stdout.length; o += size) frames.push(run.stdout.subarray(o, o + size));
  return frames;
}

const luma = (f) => { let s = 0; for (let i = 0; i < f.length; i += 3) s += 0.2126 * f[i] + 0.7152 * f[i + 1] + 0.0722 * f[i + 2]; return s / (f.length / 3) / 255; };
const diff = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += Math.abs(a[i] - b[i]); return s / a.length / 255; };
// how alike two frames' brightness patterns are, -1 to 1 (1: the same picture, however bright)
function correlation(a, b) {
  let ma = 0, mb = 0;
  for (let i = 0; i < a.length; i++) { ma += a[i]; mb += b[i]; }
  ma /= a.length; mb /= b.length;
  let ab = 0, aa = 0, bb = 0;
  for (let i = 0; i < a.length; i++) { const x = a[i] - ma, y = b[i] - mb; ab += x * y; aa += x * x; bb += y * y; }
  return aa > 1e-6 && bb > 1e-6 ? ab / Math.sqrt(aa * bb) : aa <= 1e-6 && bb <= 1e-6 ? 1 : 0;
}

function hsv(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [(h * 60 + 360) % 360, mx ? d / mx : 0, mx / 255];
}
const HUES = [[15, 'red'], [45, 'orange'], [70, 'yellow'], [160, 'green'], [200, 'cyan'], [255, 'blue'], [290, 'purple'], [335, 'pink'], [360, 'red']];
const hueName = (h) => HUES.find(([top]) => h < top)[1];
const hex = (rgb) => `#${rgb.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('')}`;

// The palette: how much of the picture is near-black, neutral, or colored, and the colors that
// cover the most of it (saturated pixels, grouped by hue), from a frame a second.
function palette(frames, fps) {
  const step = Math.max(1, Math.round(fps));
  const groups = new Map();
  let dark = 0, neutral = 0, colored = 0, sat = 0;
  for (let f = 0; f < frames.length; f += step) {
    const px = frames[f];
    for (let i = 0; i < px.length; i += 3) {
      const [h, s, v] = hsv(px[i], px[i + 1], px[i + 2]);
      sat += s;
      if (v < 0.12) { dark++; continue; }
      if (s < 0.22) { neutral++; continue; }
      colored++;
      const name = hueName(h);
      const g = groups.get(name) || { n: 0, rgb: [0, 0, 0] };
      g.n++; g.rgb[0] += px[i]; g.rgb[1] += px[i + 1]; g.rgb[2] += px[i + 2];
      groups.set(name, g);
    }
  }
  const total = dark + neutral + colored || 1;
  const colors = [...groups.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 4)
    .map(([name, g]) => ({ name, hex: hex(g.rgb.map((c) => c / g.n)), share: round(g.n / total) }))
    .filter((c) => c.share >= 0.02);
  return { dark: round(dark / total), neutral: round(neutral / total), colored: round(colored / total), saturation: round(sat / total), colors };
}

// Integrated loudness (LUFS), or null.
function loudness(file) {
  const run = ffmpeg(['-i', file, '-vn', '-af', 'ebur128', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = /I:\s+(-?[\d.]+) LUFS/.exec((run.stderr || '').split('Summary:').pop());
  return m ? parseFloat(m[1]) : null;
}

// One frame from the middle of each shot, labeled with its number and time, tiled into sheets of
// up to 30. Without ffmpeg's drawtext, the frames go unlabeled (the numbers are in reading order).
function sheets(file, shots, dir, wide) {
  const pick = shots.length <= MAX_FRAMES ? shots : Array.from({ length: MAX_FRAMES }, (_, i) => shots[Math.floor((i * shots.length) / MAX_FRAMES)]);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'reference-'));
  const [w, cols] = wide ? [400, 5] : [216, 8];
  let labeled = true;
  pick.forEach((s, i) => {
    const at = s.start + Math.min(s.length * 0.5, Math.max(0.05, s.length - 0.1));
    const out = path.join(tmp, `${String(i + 1).padStart(3, '0')}.jpg`);
    const label = `#${s.n}  ${clock(s.start)}  ${s.length.toFixed(1)}s${s.from === 'transition' ? '  ~' : ''}`.replace(/:/g, '\\:');
    const base = ['-v', 'error', '-y', '-ss', String(at), '-i', file, '-frames:v', '1'];
    const text = `drawtext=text='${label}':x=8:y=8:fontsize=${wide ? 20 : 16}:fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=6`;
    let run = labeled ? ffmpeg([...base, '-vf', `scale=${w}:-2,${text}`, out]) : null;
    if (!run || run.status !== 0) {
      labeled = false;
      run = ffmpeg([...base, '-vf', `scale=${w}:-2`, out]);
    }
  });
  const per = cols * (wide ? 6 : 4);
  const files = [];
  for (let k = 0; k * per < pick.length; k++) {
    const out = path.join(dir, `sheet-${k + 1}.jpg`);
    const n = Math.min(per, pick.length - k * per);
    const rows = Math.ceil(n / cols);
    ffmpeg(['-v', 'error', '-y', '-start_number', String(k * per + 1), '-i', path.join(tmp, '%03d.jpg'), '-frames:v', '1',
      '-vf', `tile=${cols}x${rows}:padding=6:color=0x111111`, '-q:v', '3', out]);
    if (fs.existsSync(out)) files.push(out);
  }
  fs.rmSync(tmp, { recursive: true, force: true });
  return { files, labeled, sampled: pick.length < shots.length ? pick.length : null };
}

function analyse(file, dir) {
  const info = probe(file);
  if (!(info.duration > 0)) fail(`Couldn't tell how long ${file} is.`);
  const fps = info.duration > 600 ? 4 : 10;
  const frames = readFrames(file, fps);
  const lum = frames.map(luma);
  const motion = frames.map((f, i) => (i ? diff(frames[i - 1], f) : 0));

  // Scene changes. A frame's structure (its brightness pattern) against the one before: a hard cut
  // is a one-frame spike, and a transition (a dissolve, a push through, a whip, flying into a
  // screen) is a few frames of change that end on a different picture. Pixel differences alone
  // miss a cut between two dark scenes; ffmpeg's own scene score catches what's left.
  const ys = frames.map((f) => { const y = new Float32Array(W * H); for (let i = 0; i < y.length; i++) y[i] = 0.2126 * f[3 * i] + 0.7152 * f[3 * i + 1] + 0.0722 * f[3 * i + 2]; return y; });
  const change = ys.map((y, i) => (i ? 1 - correlation(ys[i - 1], y) : 0));
  const events = [];
  for (let i = 1; i < change.length; i++) {
    const c = change[i];
    if (c > 0.45 && c >= 2 * Math.max(change[i - 1], change[i + 1] ?? 0)) events.push({ t: (i - 0.5) / fps, kind: 'cut' });
  }
  for (const t of findCuts(file)) if (!events.some((e) => Math.abs(e.t - t) < 0.25)) events.push({ t, kind: 'cut' });
  for (let i = 1; i < change.length;) {
    if (change[i] <= 0.22) { i++; continue; }
    let j = i;
    while (j + 1 < change.length && change[j + 1] > 0.22) j++;
    const spans = j - i + 1;
    if (spans >= 2 && 1 - correlation(ys[i - 1], ys[j]) > 0.45 && !events.some((e) => e.kind === 'cut' && e.t >= (i - 1) / fps && e.t <= (j + 1) / fps)) {
      events.push({ t: (i + j) / 2 / fps, kind: 'transition' });
    }
    i = j + 1;
  }
  events.sort((x, y) => x.t - y.t);
  // one change at a time: events closer than 0.6s are one (a cut wins), none at the very ends
  const changes = [];
  for (const e of events.filter((e) => e.t > 0.2 && e.t < info.duration - 0.2)) {
    const last = changes[changes.length - 1];
    if (last && e.t - last.t < 0.6) { if (e.kind === 'cut') Object.assign(last, e); continue; }
    changes.push({ ...e, t: round(e.t) });
  }
  const cuts = changes.filter((e) => e.kind === 'cut').map((e) => e.t);
  const transitions = changes.filter((e) => e.kind === 'transition').map((e) => e.t);
  const edges = [0, ...changes.map((e) => e.t), info.duration];
  const shots = edges.slice(0, -1).map((start, i) => {
    const end = edges[i + 1];
    const f0 = Math.ceil(start * fps) + 1, f1 = Math.floor(end * fps) - 1; // skip the frames either side of a change
    const inside = motion.slice(Math.max(1, f0), Math.max(f0, f1));
    const m = mean(inside);
    return {
      n: i + 1, start: round(start), end: round(end), length: round(end - start), from: i ? changes[i - 1].kind : 'start',
      motion: round(m, 4), moves: m < 0.008 ? 'still' : m < 0.025 ? 'gentle' : 'moving',
      brightness: round(mean(lum.slice(Math.floor(start * fps), Math.max(Math.floor(start * fps) + 1, Math.floor(end * fps)))), 2),
    };
  });
  const lengths = shots.map((s) => s.length);
  const third = Math.max(1, Math.floor(shots.length / 3));
  // the shot length a viewer mostly watches: half the running time is in shots at least this long
  // (a plain median lets a few flashes outvote a minute-long take)
  let acc = 0;
  const typical = [...lengths].sort((a, b) => b - a).find((l) => (acc += l) >= info.duration / 2) || 0;
  // bursts: four or more quick shots in a row, a montage inside the video
  const bursts = [];
  for (let i = 0; i < shots.length;) {
    let j = i;
    while (j < shots.length && shots[j].length < 2) j++;
    if (j - i >= 4) bursts.push({ from: shots[i].start, to: shots[j - 1].end, shots: j - i, average: round(mean(lengths.slice(i, j))) });
    i = Math.max(j, i + 1);
  }
  const pace = {
    shots: shots.length, average: round(mean(lengths)), median: round(median(lengths)), typical: round(typical),
    shortest: round(Math.min(...lengths)), longest: round(Math.max(...lengths)),
    cuts: cuts.length, transitions: transitions.length,
    cutsPerMinute: round((cuts.length / info.duration) * 60, 1), changesPerMinute: round((changes.length / info.duration) * 60, 1), hook: shots[0].length,
    opening: round(mean(lengths.slice(0, third))), closing: round(mean(lengths.slice(-third))), bursts,
  };
  const moving = shots.filter((s) => s.moves !== 'still').reduce((t, s) => t + s.length, 0) / info.duration;
  // a continuous camera: few hard cuts outside its montage bursts, and more transitions than cuts
  const steadyCuts = cuts.filter((t) => !bursts.some((x) => t >= x.from - 0.05 && t <= x.to + 0.05)).length;
  const camera = !changes.length ? 'one continuous shot'
    : (steadyCuts / info.duration) * 60 < 6 && transitions.length >= steadyCuts ? 'one moving camera, from scene to scene'
    : typical < 1.6 ? 'fast cutting' : moving > 0.6 ? 'cuts between moving shots' : 'cuts between steady shots';
  // fades: moments near black between brighter ones
  let blacks = 0;
  for (let i = 1; i < lum.length - 1; i++) if (lum[i] < 0.04 && lum[i - 1] >= 0.04) blacks++;
  const look = { brightness: round(mean(lum), 2), ...palette(frames, fps), dipsToBlack: blacks };
  look.tone = look.brightness < 0.22 ? 'dark' : look.brightness > 0.55 ? 'light' : 'mid';

  // sound: the tempo, and whether the cuts land on its beats more often than they would by chance
  let sound = { audio: info.audio };
  if (info.audio && info.duration >= 6) {
    const t = analyseTrack(file);
    const period = 60 / t.bpm;
    const window = Math.min(0.09, period * 0.18);
    const near = cuts.filter((c) => t.beats.some((b) => Math.abs(b - c) <= window)).length;
    sound = {
      ...sound, bpm: t.bpm, confidence: t.confidence, loudness: loudness(file),
      cutsOnBeat: cuts.length ? round(near / cuts.length) : null, chance: round(Math.min(1, (2 * window) / period)),
    };
  } else if (info.audio) sound.loudness = loudness(file);
  const sheet = sheets(file, shots, dir, info.width >= info.height);
  return { file: path.resolve(file), width: info.width, height: info.height, duration: round(info.duration), pace, camera, moving: round(moving), look, sound, shots, sheets: sheet };
}

// The read, and the plan in compose.js's settings.
function report(r) {
  const wide = r.width > r.height;
  const square = Math.abs(r.width - r.height) / Math.max(r.width, r.height) < 0.05;
  const p = r.pace;
  const s = r.sound;
  const L = r.look;
  const words = Math.round(r.duration * WORDS_PER_SEC);
  const perShot = Math.max(3, Math.round(p.typical * WORDS_PER_SEC));
  const onBeat = s.cutsOnBeat !== null && s.cutsOnBeat !== undefined && s.confidence >= 0.5 && s.cutsOnBeat >= Math.max(0.5, s.chance * 1.6);
  const sheetNames = r.sheets.files.map((f) => path.basename(f)).join(', ');
  const out = [];
  out.push(`# How ${path.basename(r.file)} is edited`, '');
  out.push(`${r.width}x${r.height}${square ? ' (square)' : wide ? ' (16:9 or wider)' : ' (vertical)'}, ${r.duration}s. ${p.shots} scene${p.shots === 1 ? '' : 's'} (${p.cuts} hard cut${p.cuts === 1 ? '' : 's'}, ${p.transitions} transition${p.transitions === 1 ? '' : 's'}), ${r.camera}: half the running time is in scenes of ${p.typical}s or longer${p.bursts.length ? `, with ${p.bursts.length === 1 ? 'a burst' : `${p.bursts.length} bursts`} of quick cuts (${p.bursts.map((b) => `${b.shots} shots at ${clock(b.from)}–${clock(b.to)}`).join('; ')})` : ''}. The hook holds ${p.hook}s before the first change. ${L.tone[0].toUpperCase() + L.tone.slice(1)} overall${L.colors.length ? `, mostly ${L.colors.map((c) => `${c.name} (${c.hex})`).join(', ')}` : ', with little color'}.${s.bpm ? ` Music around ${s.bpm} BPM${s.confidence < 0.5 ? ' (an unsteady beat)' : ''}${onBeat ? ', cut on the beat' : ''}.` : s.audio ? '' : ' No sound.'}`);
  out.push('', `Look at ${sheetNames} (one frame per shot${r.sheets.labeled ? ', labeled with its number, time, and length' : ', in shot order'}${r.sheets.sampled ? `; ${r.sheets.sampled} of the ${p.shots} shots, evenly spaced` : ''}) for what the numbers can't show: the captions (size, case, boxed or plain, where they sit, a phrase or a word at a time), the framing, what's on screen (a person, a product, screens, graphics), the camera moves, and the transitions.`);
  out.push('', '## Pacing', '');
  out.push(`- Scenes: ${p.shots}, changing by ${p.cuts} hard cut${p.cuts === 1 ? '' : 's'} and ${p.transitions} transition${p.transitions === 1 ? '' : 's'} (a dissolve, a push through, a whip, or a move into a new picture); ${p.changesPerMinute} changes a minute`);
  out.push(`- Scene length: ${p.shortest}–${p.longest}s, average ${p.average}s, median ${p.median}s; half the running time is in scenes of ${p.typical}s or longer`);
  for (const b of p.bursts) out.push(`- A burst of ${b.shots} quick cuts at ${clock(b.from)}–${clock(b.to)}, ${b.average}s each: a montage inside the video`);
  if (p.closing < p.opening * 0.75) out.push(`- It speeds up: ${p.opening}s scenes at the start, ${p.closing}s at the end`);
  else if (p.closing > p.opening * 1.33) out.push(`- It slows down: ${p.opening}s scenes at the start, ${p.closing}s at the end`);
  out.push(`- Hook: ${p.hook}s before the first change`);
  out.push(`- On screen: ${Math.round(r.moving * 100)}% of the time something is moving (camera or subject)`);
  if (L.dipsToBlack) out.push(`- Dips to black: ${L.dipsToBlack}`);
  out.push('', '## Look', '');
  out.push(`- Brightness: ${L.tone} (${L.brightness} of white on average); ${Math.round(L.dark * 100)}% near-black, ${Math.round(L.neutral * 100)}% gray or white, ${Math.round(L.colored * 100)}% colored`);
  if (L.colors.length) out.push(`- Colors: ${L.colors.map((c) => `${c.name} ${c.hex} (${Math.round(c.share * 100)}%)`).join(', ')}`);
  out.push('', '## Sound', '');
  if (!s.audio) out.push('- No sound track.');
  else {
    if (s.bpm) out.push(`- Tempo: about ${s.bpm} BPM (confidence ${s.confidence}${s.confidence < 0.5 ? ': not a steady beat, or the voice covers it' : ''})`);
    if (s.cutsOnBeat !== null && s.cutsOnBeat !== undefined) out.push(`- Cuts on the beat: ${Math.round(s.cutsOnBeat * 100)}% (by chance it would be about ${Math.round(s.chance * 100)}%)`);
    if (s.loudness !== null && s.loudness !== undefined) out.push(`- Loudness: ${s.loudness} LUFS`);
    out.push('- Is there a voiceover, and whose? Listen, or read the captions on the sheet.');
  }
  out.push('', '## To match it', '');
  out.push('In a compose.js script (references/video-rendering.md):', '');
  out.push(`- \`format: ${square ? 'portrait' : wide ? 'landscape' : 'portrait'}\`${square ? ' (the renderer makes 9:16 or 16:9; crop to square afterwards if the post needs it)' : ''}`);
  out.push(`- Length: about ${Math.round(r.duration)}s, which is about ${words} spoken words.`);
  const lines = Math.max(2, Math.round(words / perShot));
  if (r.camera === 'one continuous shot') out.push(`- One shot all the way through: about ${lines} lines of about ${perShot} words over a single scene (one \`mascot\` or screen shot, or a \`player\`).`);
  else if (r.camera === 'one moving camera, from scene to scene') out.push(`- About ${lines} lines of about ${perShot} words, the picture moving on to a new scene with each line or two (it changes scene ${p.shots - 1} times).`);
  else if (p.typical >= 1.6) out.push(`- One numbered line per shot: about ${Math.min(p.shots, lines)} lines of about ${perShot} words each.`);
  else out.push(`- Its shots (${p.typical}s) are quicker than a voiceover line, so either write short lines (3 or 4 words) or make it a montage of clips cut on the beat (montage.js) rather than a narrated video.`);
  for (const b of p.bursts) out.push(`- The burst at ${clock(b.from)}: show many things fast there, with a \`wall\` of the real things it made, \`icons\`, or a run of short lines.`);
  if (r.camera === 'one moving camera, from scene to scene') out.push('- One continuous camera: `style: 3d` with the screen shots (terminal, agent, wall, player), which hand over without cuts, opened by a `desk` push-in, rather than a cut per line.');
  else if (r.camera === 'fast cutting') out.push('- Fast cutting: a shot per line with short lines, the bold captions, and sound effects on the cuts.');
  else out.push(`- A cut per line${r.moving > 0.6 ? ', each shot moving (the 3D shots and the photo backgrounds\' slow zoom both do)' : ', steady shots'}.`);
  if (L.tone === 'dark') out.push('- Dark: `set=night` for mascot shots, the screen shots and `notes` (they\'re dark), or dark photo backgrounds; keep one palette throughout.');
  else if (L.tone === 'light') out.push('- Light: `set=studio` for mascot shots, light photo backgrounds; keep one palette throughout.');
  if (L.colors.length) out.push(`- Its main color is ${L.colors[0].name} (${L.colors[0].hex}). Use the brand's own accent; borrow the color only if it suits the brand.`);
  if (s.bpm && s.confidence >= 0.5) out.push(`- Music: a track around ${Math.round(s.bpm)} BPM (\`music: assets/track.mp3\`, a licensed one, or the Sonic Identity's genre)${onBeat ? '; compose.js cuts on its beat' : ''}.`);
  out.push(`- The hook: the first line on screen from frame 0, holding about ${p.hook}s.`);
  out.push('- Captions, from the sheet: small plain subtitles a phrase at a time → `captions: subtitle`; big boxed capitals → `captions: bold`; a word or a few at a time → the default captions; none → leave the words in the voice only.');
  out.push('', 'Copy how it\'s edited, never what\'s in it: none of its footage, music, characters, logos, or words.');
  return out.join('\n') + '\n';
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const file = args.positional[0];
  if (args.help || !file) {
    console.log(fs.readFileSync(__filename, 'utf8').split('*/')[0].replace(/^[\s\S]*?\/\*/, '').replace(/^ \* ?/gm, ''));
    process.exit(args.help ? 0 : 2);
  }
  if (!fs.existsSync(file)) fail(`No video at ${file}`);
  const dir = path.resolve(args.out || path.join(path.dirname(file), `${path.basename(file, path.extname(file))}-reference`));
  fs.mkdirSync(dir, { recursive: true });
  const r = analyse(file, dir);
  fs.writeFileSync(path.join(dir, 'reference.json'), JSON.stringify(r, null, 2) + '\n');
  fs.writeFileSync(path.join(dir, 'reference.md'), report(r));
  if (args.json) console.log(JSON.stringify(r, null, 2));
  else {
    console.log(report(r));
    console.log(`Wrote ${path.join(dir, 'reference.md')}, reference.json, and ${r.sheets.files.map((f) => path.basename(f)).join(', ')}`);
  }
}

if (require.main === module) main();

module.exports = { analyse, report };
