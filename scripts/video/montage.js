#!/usr/bin/env node
'use strict';
/*
 * Builds a montage page from the user's own photos or phone clips of a property or a product:
 * one shot per photo, each moving (a pan across a wide room, a push in on a detail), cut on the
 * music's beat or timed to a voiceover, with a label on each shot, the hook on the first, the
 * price, specs, and CTA near the end, and a client's look with their contact details on the end
 * card. The page is templates/montage.html's look; render.js turns it into the MP4.
 *
 * Usage:
 *   node montage.js inspect <folder | files...> --slug <slug> [--out <dir>] [--force]
 *   node montage.js <script.md> [--out <page.html>] [--no-check]
 *
 * inspect copies the photos and clips into state/videos/assets/ (or <dir>/assets) as
 * <slug>-01.jpg, <slug>-02.mp4, ...: photos upright and sized for the frame, as JPEG without
 * their metadata (a phone photo's location included), PNGs as PNG to keep transparency, clips
 * as they are. The originals aren't touched. It prints each file's size, shape, and brightness,
 * writes a numbered contact sheet, <slug>-contact.png, to look at them all at once, and a
 * starter script, state/videos/<date>-<slug>.md, one shot per file in name order (--force
 * replaces an existing one).
 *
 * The script is Markdown: frontmatter, then numbered shots, one per photo or clip: the file
 * (no spaces in its name), a label (with a second, smaller line after "|"), and any tags.
 *
 *   ---
 *   title: 42 maple st
 *   kind: property                     # property or product: the default moves and sound
 *   client: acme-realty                # state/clients/acme-realty.md: look, sound, contact card
 *   hook: just listed in maple grove   # on screen from the first frame; hook-b:, hook-c: for variants
 *   status: open house sat 1–4         # a sticker under the hook
 *   price: $689,000                    # shown on the facts shot ([facts], or the last)
 *   specs: 4 bd · 3 ba · 2,450 sq ft
 *   cta: book a showing · link in bio  # on the last shot
 *   music: identity                    # identity (default), none, a genre, or assets/track.mp3
 *   voice: none                        # none (default), a voice.js voice for the [say: ...] lines, or
 *   recordings: assets/maple-{n}.m4a   # the user's own takes, one per [say: ...] line
 *   pace: 1 bar                        # each shot: N bars, N beats, or seconds (2.5s); or instead
 *   length: 30                         # a target length for the shots, in seconds (the end card adds ~3s)
 *   transition: fade                   # fade (default), cut, slide, zoom, wipe, or flash
 *   depth: auto                        # auto (default): 3D moves where a depth map can be had; off
 *   bpm: 100                           # the generated music's tempo (and energy: 1-5), to override
 *   ---
 *   1. assets/maple-01.jpg  Welcome home  [move: pull-out]
 *   2. assets/maple-02.jpg  Sun-filled living room | vaulted ceilings  [move: pan-right focus=40%,55%]
 *   3. assets/maple-03.jpg  Chef's kitchen  [say: The kitchen was redone last year.]
 *   4. assets/maple-04.jpg  Main suite  [staged]
 *   5. assets/maple-05.mp4  The backyard  [from: 3.5]
 *
 * Tags:
 *   [move: push-in | pull-out | pan-left | pan-right | pan-up | pan-down | drift | none]
 *        with focus=x%,y% (the point of the photo to frame and move toward) and zoom=1.2
 *   [move: orbit | orbit-left | orbit-right | dolly-in | dolly-out | rise]   3D moves: the photo is
 *        drawn from its depth map, near parts moving more than far ones, so the camera seems to
 *        circle the focus, move into the room, or lift; amount=1.5 makes it stronger. They show
 *        only what's in the photo, so the moves stay small (about a step, or a slight turn).
 *   [fit: cover | contain | card]   cover fills the frame (the default); contain shows the whole
 *        photo over a blurred copy of it; card sets a packshot on a soft backdrop in the accent
 *        color, where a white background melts away
 *   [say: ...]          a voiceover line for this shot, captioned word by word
 *   [hold: 2 bars]      this shot's length (bars, beats, or seconds), instead of the pace
 *   [transition: cut]   how this shot comes in
 *   [staged]            the "Virtually staged" badge a virtually staged photo needs
 *   [callout: 30%,60% solid oak]    a dot at that point of the photo, with a label; the shot holds still
 *   [before: assets/maple-04-before.jpg]   this shot's photo wipes in over the before photo
 *   [from: 3.5]         where a clip starts, in seconds
 *   [facts]             the price and specs go on this shot instead of the last
 *   [depth: assets/maple-02-depth.png]   a depth map from elsewhere (white near) for this photo
 *
 * A shot without a move gets one that suits it, each the other way from the last: with a depth
 * map, an orbit across a wide photo and a dolly in or a rise on a tall one; without, a pan or a
 * push in. A clip keeps its own motion. Depth maps come from depth.js (a free local model, set
 * up once with `npm install @huggingface/transformers`), made as they're needed and kept next to
 * each photo; without it, every shot moves flat. Without a voice, every shot is a
 * whole number of the music's beats, with the first cut where the beat drops (a licensed track
 * is read with beats.js and cut on its bars when its beat is steady). With a voice, a shot
 * lasts at least its line. A shot is held longer when its label needs the time to be read.
 * Edit the script and run montage.js again rather than editing the page.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { pathToFileURL } = require('url');
const { parseScript } = require('./voice');
const { prepareVoice, meanLuma, launchBrowser } = require('./render');
const { visualIdentity, applyIdentity } = require('./brand');
const { parseFrontmatter, sonicIdentity } = require('./compose');
const { analyseTrack, alignTrack } = require('./beats');
const { GENRES } = require('./soundtrack');
const depthMaps = require('./depth');

const ROOT = path.resolve(__dirname, '..', '..');
const W = 1080;
const H = 1920;
// the .scene box text sits in, and the box a card-fit packshot sits in (templates/montage.html)
const SCENE = { left: 90, top: 330 };
const CARD = { left: 90, top: 250, w: 900, h: 1000 };
const PHOTO_EXT = /\.(jpe?g|png|webp|heic|heif|tiff?|bmp|gif|avif)$/i;
const CLIP_EXT = /\.(mp4|mov|webm|m4v)$/i;
const AUDIO_EXT = /\.(mp3|m4a|wav|aac|ogg|flac)$/i;
const SHORT_SIDE = 2160; // photos are sized down to this short side: sharp in a 1080x1920 frame, quick to render
const PAN_SPEED = 170; // px a second, at most, that a pan moves the photo across the frame
const MIN_SHOT = 1.5;
const MAX_SHOT = 5;
const DEFAULT_SHOT = { property: 2.6, product: 2.0 }; // seconds, rounded to whole beats
const READ_WPS = 4; // words a second, the reading pace render.js --check holds text to
const TRANSITIONS = { fade: 0.45, cut: 0, flash: 0, slide: 0.5, zoom: 0.5, wipe: 0.6 };
// 3D moves draw the photo from its depth map, so the camera seems to move through the space
const MOVES_3D = ['orbit', 'orbit-left', 'orbit-right', 'dolly', 'dolly-in', 'dolly-out', 'rise'];
const MOVES = ['push-in', 'pull-out', 'pan-left', 'pan-right', 'pan-up', 'pan-down', 'drift', 'none', ...MOVES_3D];
// each 3D move's flat stand-in, for a shot without a depth map
const FLAT = { orbit: 'pan-right', 'orbit-left': 'pan-left', 'orbit-right': 'pan-right', dolly: 'push-in', 'dolly-in': 'push-in', 'dolly-out': 'pull-out', rise: 'pan-up' };
const FITS = ['cover', 'contain', 'card'];
const TAGS = ['move', 'fit', 'say', 'hold', 'transition', 'staged', 'callout', 'before', 'from', 'facts', 'depth'];

function fail(message) {
  console.error(message);
  process.exit(2);
}

function parseArgs(argv) {
  const args = { positional: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--no-check') args.noCheck = true;
    else if (a === '--force') args.force = true;
    else if (['--out', '--slug'].includes(a)) args[a.slice(2)] = argv[++i];
    else if (a === '-h' || a === '--help') args.help = true;
    else args.positional.push(a);
  }
  return args;
}

const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'montage';
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const r2 = (t) => Math.round(t * 100) / 100;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const pct = (v) => `${r2(v * 100)}%`;
const words = (s) => (s ? String(s).trim().split(/\s+/).length : 0);

function run(cmd, args, opts = {}) {
  return spawnSync(process.execPath, [path.join(__dirname, cmd), ...args], { encoding: 'utf8', ...opts });
}

function ffmpeg(args) {
  return spawnSync('ffmpeg', ['-y', '-loglevel', 'error', ...args], { encoding: 'utf8' });
}

// Width, height (as shown, after any rotation), and length of a photo or clip, or null.
function probe(file) {
  const res = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries',
    'stream=width,height:stream_side_data=rotation:format=duration', '-of', 'json', file], { encoding: 'utf8' });
  if (res.status !== 0) return null;
  let data;
  try {
    data = JSON.parse(res.stdout);
  } catch {
    return null;
  }
  const s = (data.streams || [])[0];
  if (!s || !s.width) return null;
  const rotation = Math.abs(Number(((s.side_data_list || []).find((d) => d.rotation !== undefined) || {}).rotation || 0));
  const [w, h] = rotation === 90 || rotation === 270 ? [s.height, s.width] : [s.width, s.height];
  return { w, h, duration: parseFloat((data.format || {}).duration) || 0 };
}

// The EXIF orientation of a JPEG (1 is upright), read from its APP1 segment.
function jpegOrientation(file) {
  try {
    const buf = fs.readFileSync(file);
    if (buf[0] !== 0xff || buf[1] !== 0xd8) return 1;
    let i = 2;
    while (i + 4 < buf.length && buf[i] === 0xff) {
      const marker = buf[i + 1];
      if (marker === 0xda) break;
      const len = buf.readUInt16BE(i + 2);
      if (marker === 0xe1 && buf.toString('latin1', i + 4, i + 10) === 'Exif\0\0') {
        const t = i + 10;
        const le = buf.toString('latin1', t, t + 2) === 'II';
        const u16 = (o) => (le ? buf.readUInt16LE(o) : buf.readUInt16BE(o));
        const u32 = (o) => (le ? buf.readUInt32LE(o) : buf.readUInt32BE(o));
        const ifd = t + u32(t + 4);
        for (let k = 0, n = u16(ifd); k < n; k++) {
          const e = ifd + 2 + k * 12;
          if (u16(e) === 0x0112) return u16(e + 8) || 1;
        }
        return 1;
      }
      i += 2 + len;
    }
  } catch { /* unreadable: treat as upright */ }
  return 1;
}
// ffmpeg filters that turn each EXIF orientation upright
const UPRIGHT = { 2: 'hflip', 3: 'hflip,vflip', 4: 'vflip', 5: 'transpose=0', 6: 'transpose=1', 7: 'transpose=3', 8: 'transpose=2' };

const has = (cmd) => spawnSync(cmd, ['--help'], { stdio: 'ignore' }).error === undefined;

// An iPhone HEIC photo as a JPEG, with whichever converter this machine has. Returns a path or null.
function heicToJpeg(src, tmp) {
  const out = path.join(tmp, `${path.basename(src).replace(/\.[^.]+$/, '')}.jpg`);
  const tries = [
    ['sips', ['-s', 'format', 'jpeg', src, '--out', out]],
    ['heif-convert', ['-q', '95', src, out]],
    ['magick', [src, out]],
    ['ffmpeg', ['-y', '-loglevel', 'error', '-i', src, '-frames:v', '1', '-q:v', '2', out]],
  ];
  for (const [cmd, args] of tries) {
    if (!has(cmd)) continue;
    spawnSync(cmd, args, { stdio: 'ignore' });
    const info = fs.existsSync(out) && probe(out);
    if (info && Math.min(info.w, info.h) >= 480) return out;
  }
  return null;
}

// Copies one photo in, upright and sized for the frame. Returns { file } or { error }.
function importPhoto(src, base, tmp) {
  let input = src;
  if (/\.(heic|heif)$/i.test(src)) {
    input = heicToJpeg(src, tmp);
    if (!input) return { error: 'a HEIC photo this machine can\'t convert; export it as JPEG (on an iPhone, Settings > Camera > Formats > Most Compatible) and run inspect again' };
  }
  const info = probe(input);
  if (!info) return { error: 'not a photo ffmpeg can read' };
  const orient = /\.jpe?g$/i.test(input) ? jpegOrientation(input) : 1;
  const [w, h] = orient >= 5 ? [info.h, info.w] : [info.w, info.h];
  const k = Math.min(1, SHORT_SIDE / Math.min(w, h));
  const even = (v) => 2 * Math.round(v / 2);
  const filters = [UPRIGHT[orient], k < 1 ? `scale=${even(w * k)}:${even(h * k)}:flags=lanczos` : ''].filter(Boolean);
  const png = /\.png$/i.test(src);
  const file = `${base}${png ? '.png' : '.jpg'}`;
  const res = ffmpeg(['-noautorotate', '-i', input, ...(filters.length ? ['-vf', filters.join(',')] : []),
    '-frames:v', '1', '-map_metadata', '-1', ...(png ? [] : ['-q:v', '2']), file]);
  if (res.status !== 0) return { error: `ffmpeg couldn't convert it: ${(res.stderr || '').trim().split('\n').pop()}` };
  return { file };
}

// A numbered sheet of every file, to look at them all at once. Drawn in the browser so the
// numbers and names are legible; plain tiles from ffmpeg if Playwright isn't set up.
async function contactSheet(items, out, tmp) {
  const cells = items.map((it) => {
    let src = it.file;
    if (it.clip) {
      src = path.join(tmp, `${path.basename(it.file)}.jpg`);
      ffmpeg(['-ss', String(Math.min(1, it.duration / 2)), '-i', it.file, '-frames:v', '1', '-vf', 'scale=640:-2', src]);
    }
    return { ...it, src };
  });
  const cols = cells.length > 16 ? 5 : 4;
  let playwright = null;
  try {
    playwright = require('playwright');
  } catch {
    try {
      playwright = require('playwright-core');
    } catch { /* falls back to ffmpeg */ }
  }
  if (playwright) {
    const page = path.join(tmp, 'contact.html');
    fs.writeFileSync(page, `<!doctype html><meta charset="utf-8"><style>
  body { margin: 0; padding: 16px; background: #111; font: 600 20px/1.2 "Liberation Sans", Arial, sans-serif; color: #eee;
         display: grid; grid-template-columns: repeat(${cols}, 300px); gap: 14px; width: ${cols * 314 + 18}px; }
  figure { margin: 0; } .img { position: relative; height: 225px; background: #222; }
  img { width: 100%; height: 100%; object-fit: contain; }
  b { position: absolute; left: 8px; top: 8px; background: #ffd23f; color: #111; padding: 2px 10px 4px; border-radius: 8px; font-size: 26px; }
  figcaption { padding-top: 6px; font-size: 15px; color: #bbb; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>${cells.map((c) => `<figure><div class="img"><img src="${pathToFileURL(c.src).href}"><b>${c.n}</b></div><figcaption>${esc(path.basename(c.file))} · ${c.w}×${c.h}${c.clip ? ` · ${c.duration.toFixed(1)}s clip` : ''}</figcaption></figure>`).join('')}`);
    const browser = await launchBrowser(playwright.chromium);
    const tab = await browser.newPage({ viewport: { width: cols * 314 + 18, height: 400 } });
    await tab.goto(pathToFileURL(page).href, { waitUntil: 'load' });
    await tab.screenshot({ path: out, fullPage: true });
    await browser.close();
    return out;
  }
  const list = path.join(tmp, 'tiles.txt');
  fs.writeFileSync(list, cells.map((c) => `file '${c.src.replace(/'/g, "'\\''")}'`).join('\n'));
  const res = ffmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-vf',
    `scale=300:225:force_original_aspect_ratio=decrease,pad=300:225:(ow-iw)/2:(oh-ih)/2,tile=${cols}x${Math.ceil(cells.length / cols)}:padding=8`,
    '-frames:v', '1', out]);
  return res.status === 0 ? out : null;
}

async function inspect(args) {
  if (!args.slug) fail('Pass --slug <name>: the short name the copies are saved under (e.g. --slug maple).');
  const slug = slugify(args.slug);
  const inputs = [];
  for (const p of args.positional) {
    if (!fs.existsSync(p)) fail(`Not found: ${p}`);
    if (fs.statSync(p).isDirectory()) {
      for (const f of fs.readdirSync(p).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))) {
        if (PHOTO_EXT.test(f) || CLIP_EXT.test(f)) inputs.push(path.join(p, f));
      }
    } else inputs.push(p);
  }
  if (!inputs.length) fail('No photos or clips found (jpg, png, webp, heic, mp4, mov, ...).');
  const videos = args.out ? path.resolve(args.out) : path.join(ROOT, 'state', 'videos');
  const assets = path.join(videos, 'assets');
  fs.mkdirSync(assets, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'montage-'));
  const items = [];
  const skipped = [];
  inputs.forEach((src, i) => {
    const n = i + 1;
    const base = path.join(assets, `${slug}-${String(n).padStart(2, '0')}`);
    let file;
    if (CLIP_EXT.test(src)) {
      file = `${base}${path.extname(src).toLowerCase()}`;
      fs.copyFileSync(src, file);
    } else {
      const res = importPhoto(src, base, tmp);
      if (res.error) {
        skipped.push(`${path.basename(src)}: ${res.error}`);
        return;
      }
      file = res.file;
    }
    const info = probe(file);
    if (!info) {
      skipped.push(`${path.basename(src)}: unreadable`);
      return;
    }
    const clip = CLIP_EXT.test(file);
    const shape = info.w / info.h > 1.1 ? 'landscape' : info.w / info.h < 0.9 ? 'portrait' : 'square';
    // how much a frame-filling shot enlarges it
    const enlarge = Math.max(W / info.w, H / info.h);
    items.push({ n, src, file, clip, ...info, shape, luma: clip ? null : meanLuma(file), enlarge });
  });

  console.log(`Copied ${items.length} file${items.length === 1 ? '' : 's'} into ${assets}:`);
  for (const it of items) {
    const notes = [];
    if (it.luma !== null && it.luma < 0.3) notes.push('dark');
    if (it.luma !== null && it.luma > 0.85) notes.push('very bright');
    if (!it.clip && it.enlarge > 1.25) notes.push(`low resolution: ${it.enlarge.toFixed(1)}x to fill the frame, so it will look soft (try fit: contain)`);
    if (it.clip && it.duration < 2) notes.push('very short clip');
    console.log(`  ${String(it.n).padStart(2)}. ${path.basename(it.file).padEnd(18)} ${`${it.w}x${it.h}`.padEnd(10)} ${it.shape.padEnd(9)} ${it.clip ? `clip ${it.duration.toFixed(1)}s`.padEnd(15) : `brightness ${it.luma === null ? '?' : it.luma.toFixed(2)}`.padEnd(15)} ${path.basename(it.src)}${notes.length ? `  (${notes.join('; ')})` : ''}`);
  }
  for (const s of skipped) console.warn(`Skipped ${s}`);
  if (!items.length) fail('Nothing could be copied.');

  console.log(depthMaps.available()
    ? '3D moves: on (depth maps are made for the photos that use them)'
    : '3D moves: off until the depth model is set up; from scripts/video, run once: npm install @huggingface/transformers');
  const sheet = await contactSheet(items, path.join(assets, `${slug}-contact.png`), tmp);
  fs.rmSync(tmp, { recursive: true, force: true });
  if (sheet) console.log(`Contact sheet: ${sheet}`);

  const script = path.join(videos, `${new Date().toISOString().slice(0, 10)}-${slug}.md`);
  if (fs.existsSync(script) && !args.force) {
    console.log(`Starter script ${script} already exists; left as it is (--force replaces it).`);
    return;
  }
  const rel = (f) => path.relative(videos, f).split(path.sep).join('/');
  fs.writeFileSync(script, `---
title: ${slug.replace(/-/g, ' ')}
kind: property                 # property or product
hook:                          # on screen from the first frame; under about 8 words
cta:                           # on the last shot
music: identity                # identity, none, a genre, or assets/track.mp3
voice: none                    # none, or a voice.js voice for [say: ...] lines
transition: fade               # fade, cut, slide, zoom, wipe, or flash
---
${items.map((it) => `${it.n}. ${rel(it.file)}`).join('\n')}

## Notes
Order the shots, give each a label, and add tags; see the top of scripts/video/montage.js.
`);
  console.log(`Starter script: ${script}`);
}

// ---------------------------------------------------------------- building a page

// "1. assets/a.jpg  Chef's kitchen | quartz island  [move: pan-left focus=40%,50%] [staged]"
const TAG = /\[([a-z][\w-]*)(?::\s*([^\]]*))?\]/gi;
function parseShotLine({ n, text }) {
  const tags = {};
  for (const m of text.matchAll(TAG)) tags[m[1].toLowerCase()] = m[2] === undefined ? true : m[2].trim();
  const rest = text.replace(TAG, ' ').replace(/\s+/g, ' ').trim();
  const m = /^(\S+)\s*(.*)$/.exec(rest);
  if (!m) return null;
  const [label = '', sub = ''] = m[2].split('|').map((s) => s.trim());
  return { n, media: m[1], label, sub, tags };
}

// "2 bars", "6 beats", "2.5s", "2.5" -> { beats } or { seconds }
function parseLength(v) {
  const m = /^\s*(\d+(?:\.\d+)?)\s*(bars?|beats?|s|sec|secs|seconds?)?\s*$/i.exec(String(v || ''));
  if (!m) return null;
  const n = parseFloat(m[1]);
  const unit = (m[2] || 's').toLowerCase();
  if (unit.startsWith('bar')) return { beats: n * 4, bars: true };
  if (unit.startsWith('beat')) return { beats: n };
  return { seconds: n };
}

// "push-in focus=40%,55% zoom=1.2" -> { name, focus: [0.4, 0.55], zoom } (amount=1.5 for a 3D move's strength)
function parseMove(v) {
  const [name = '', ...rest] = String(v).trim().toLowerCase().split(/\s+/);
  const out = { name };
  for (const kv of rest) {
    const [k, val] = kv.split('=');
    if (k === 'focus') {
      const xy = val.split(',').map((p) => parseFloat(p) / 100);
      if (xy.length === 2 && xy.every((p) => p >= 0 && p <= 1)) out.focus = xy;
    } else if (k === 'zoom' && parseFloat(val) > 1) out.zoom = Math.min(1.6, parseFloat(val));
    else if (k === 'amount' && parseFloat(val) > 0) out.amount = Math.min(2.5, parseFloat(val));
  }
  return out;
}

// A client's profile: state/clients/<slug>.md, with ## Contact, ## Visual Identity, ## Sonic Identity.
function clientProfile(slug) {
  const file = path.join(ROOT, 'state', 'clients', `${slug}.md`);
  if (!fs.existsSync(file)) fail(`No client profile at ${file}. Make one first (state/clients/README.md has the format).`);
  const text = fs.readFileSync(file, 'utf8');
  const section = (/^## Contact\n([\s\S]*?)(?=^## |$(?![\s\S]))/m.exec(text) || [])[1] || '';
  const field = (name) => (((new RegExp(`^-\\s*${name}:\\s*(.+)$`, 'mi')).exec(section) || [])[1] || '').trim();
  return { file, name: field('Name'), business: field('Business'), phone: field('Phone'), website: field('Website'), email: field('Email'), fine: field('Fine print') };
}

// The template's own body settings, the fallback for anything the identity doesn't set.
function templateDefaults(html) {
  const body = /<body([^>]*)>/.exec(html.slice(html.indexOf('</head>')))[1];
  const out = {};
  for (const m of body.matchAll(/data-([\w-]+)="([^"]*)"/g)) out[m[1]] = m[2];
  return out;
}

// Where a photo sits in the frame: its size there, the object-position that centers the focus,
// and where the focus lands (px), for a shot's fit.
function placement(info, fit, focus) {
  const [fx, fy] = focus || [0.5, 0.5];
  const box = fit === 'card' ? CARD : { left: 0, top: 0, w: W, h: H };
  const s = fit === 'cover' ? Math.max(box.w / info.w, box.h / info.h) : Math.min(box.w / info.w, box.h / info.h);
  const dw = info.w * s;
  const dh = info.h * s;
  const pos = (frame, disp, f) => (disp > frame + 1 ? clamp((frame / 2 - f * disp) / (frame - disp), 0, 1) : 0.5);
  const ox = pos(box.w, dw, fx);
  const oy = pos(box.h, dh, fy);
  return {
    ox, oy, overflowX: Math.max(0, dw - box.w), overflowY: Math.max(0, dh - box.h),
    x: box.left + (box.w - dw) * ox + fx * dw, y: box.top + (box.h - dh) * oy + fy * dh,
  };
}

// The slot's move: the --kb keyframes and the variables they read.
function resolveMove(shot, dur, defaults, prev) {
  const asked = shot.move.name;
  const place = placement(shot.info, shot.fit, shot.move.focus);
  const vars = { '--ox': pct(place.ox), '--oy': pct(place.oy), '--fx': pct(place.x / W), '--fy': pct(place.y / H) };
  let name = asked || defaults.next(shot, place, prev);
  const notes = [];
  if (shot.tags.callout && name !== 'none') {
    if (asked) notes.push(`shot ${shot.n} has a callout, so it holds still (no ${asked})`);
    name = 'none';
  }
  if (shot.fit !== 'cover' && /^pan-/.test(name)) {
    notes.push(`shot ${shot.n} shows the whole photo (fit: ${shot.fit}), so there's nothing to pan across; it drifts instead`);
    name = 'drift';
  }
  const zoom = shot.move.zoom;
  if (name === 'orbit') name = /-right$/.test(prev) ? 'orbit-left' : 'orbit-right';
  if (name === 'dolly') name = 'dolly-in';
  if (MOVES_3D.includes(name)) {
    // drawn by the page from the depth map (templates/montage.html); a wide photo also travels
    // across, the way the camera does
    const [fx, fy] = shot.move.focus || [0.5, 0.5];
    const depth = { move: name, focus: [fx, fy], pos: [place.ox, place.oy], zoom: zoom || 1.08, amount: shot.move.amount || 1 };
    if (/^orbit/.test(name) && place.overflowX >= 120) {
      const span = Math.min(0.6, (0.7 * PAN_SPEED * dur) / place.overflowX);
      const sign = name === 'orbit-right' ? 1 : -1;
      const a = clamp(place.ox - (sign * span) / 2, 0, 1);
      const b = clamp(place.ox + (sign * span) / 2, 0, 1);
      depth.pan = [a, b];
    }
    vars['--kb'] = 'none';
    return { name, vars, place, notes, depth };
  }
  if (name === 'pan-left' || name === 'pan-right') {
    const sign = name === 'pan-right' ? 1 : -1;
    if (place.overflowX >= 120) {
      // across the photo, around the focus, no faster than PAN_SPEED
      const span = Math.min(0.85, (PAN_SPEED * dur) / place.overflowX);
      let a = place.ox - (sign * span) / 2;
      let b = place.ox + (sign * span) / 2;
      const shift = Math.min(a, b) < 0 ? -Math.min(a, b) : Math.max(a, b) > 1 ? 1 - Math.max(a, b) : 0;
      a += shift;
      b += shift;
      Object.assign(vars, { '--kb': 'panX', '--x0': pct(a), '--x1': pct(b) });
    } else {
      // no room to pan: zoom in a little and slide
      const z = zoom || 1.2;
      const t = Math.min(((z - 1) / (2 * z)) * 0.9, (PAN_SPEED * dur) / 2 / (W * z));
      Object.assign(vars, { '--kb': 'shiftX', '--zoom': z, '--t0': pct(sign * t), '--t1': pct(-sign * t) });
    }
  } else if (name === 'pan-up' || name === 'pan-down') {
    const z = zoom || 1.2;
    const t = Math.min(((z - 1) / (2 * z)) * 0.9, (PAN_SPEED * dur) / 2 / (H * z));
    const sign = name === 'pan-up' ? 1 : -1;
    Object.assign(vars, { '--kb': 'shiftY', '--zoom': z, '--t0': pct(-sign * t), '--t1': pct(sign * t) });
  } else if (name === 'push-in' || name === 'pull-out') {
    Object.assign(vars, { '--kb': name === 'push-in' ? 'pushIn' : 'pullOut', ...(zoom ? { '--zoom': zoom } : shot.fit === 'cover' ? {} : { '--zoom': 1.06 }) });
  } else if (name === 'drift') {
    vars['--kb'] = 'drift';
  } else {
    vars['--kb'] = 'none';
  }
  return { name, vars, place, notes };
}

// The default moves, each the other way from the shot before. With a depth map, a wide photo
// orbits (and travels across), a tall one dollies in or rises, a product dollies in and orbits.
// Without one, wide photos pan, tall ones push in and pull out, a product pushes in and drifts.
// A clip keeps its own motion.
function moveDefaults(kind) {
  return {
    next(shot, place, prev) {
      if (shot.clip) return 'none';
      if (shot.depthFile) {
        if (kind === 'product') return prev === 'dolly-in' ? 'orbit' : 'dolly-in';
        if (place.overflowX >= 200) return 'orbit';
        return prev === 'dolly-in' ? 'rise' : 'dolly-in';
      }
      if (kind === 'product' || shot.fit !== 'cover') return prev === 'push-in' ? 'drift' : 'push-in';
      if (place.overflowX >= 200) return /-right$/.test(prev) ? 'pan-left' : 'pan-right';
      return prev === 'push-in' ? 'pull-out' : 'push-in';
    },
  };
}

async function build(args) {
  const scriptFile = args.positional[0];
  if (!fs.existsSync(scriptFile)) fail(`No script at ${scriptFile}`);
  const { meta, body } = parseFrontmatter(fs.readFileSync(scriptFile, 'utf8'));
  const kind = String(meta.kind || 'property').toLowerCase();
  if (!DEFAULT_SHOT[kind]) fail(`kind: ${kind}? Use property or product.`);
  const page = path.resolve(args.out || scriptFile.replace(/\.md$/i, '') + '.html');
  const dir = path.dirname(page);
  const assets = path.join(dir, 'assets');
  fs.mkdirSync(assets, { recursive: true });
  const slug = slugify(meta.title || path.basename(scriptFile, '.md'));
  const notes = [];

  // ---- the shots
  const shots = parseScript(body).map(parseShotLine).filter(Boolean);
  if (!shots.length) fail(`No shots in ${scriptFile}; number them "1. assets/photo.jpg  Label", one per photo.`);
  const missing = [];
  for (const s of shots) {
    for (const t of Object.keys(s.tags)) if (!TAGS.includes(t)) notes.push(`shot ${s.n}: unknown tag [${t}] ignored (a bracketed placeholder left in?)`);
    const file = path.join(dir, s.media);
    if (!fs.existsSync(file)) {
      missing.push(s.media);
      continue;
    }
    s.clip = CLIP_EXT.test(s.media);
    if (!s.clip && !PHOTO_EXT.test(s.media)) fail(`shot ${s.n}: ${s.media} isn't a photo or a clip`);
    s.info = probe(file);
    if (!s.info) fail(`shot ${s.n}: can't read ${s.media}`);
    s.fit = String(s.tags.fit || 'cover').toLowerCase();
    if (!FITS.includes(s.fit)) fail(`shot ${s.n}: fit: ${s.fit}? Use ${FITS.join(', ')}.`);
    if (s.clip && s.fit !== 'cover') {
      // the renderer cuts a full-frame clip to 9:16 before it's placed
      notes.push(`shot ${s.n} is a clip, which always fills the frame; fit: ${s.fit} is for photos`);
      s.fit = 'cover';
    }
    s.move = s.tags.move ? parseMove(s.tags.move) : { name: '' };
    if (s.move.name && !MOVES.includes(s.move.name)) fail(`shot ${s.n}: move: ${s.move.name}? Use ${MOVES.join(', ')}.`);
    s.transition = String(s.tags.transition || meta.transition || 'fade').toLowerCase();
    if (TRANSITIONS[s.transition] === undefined) fail(`shot ${s.n}: transition: ${s.transition}? Use ${Object.keys(TRANSITIONS).join(', ')}.`);
    if (typeof s.tags.before === 'string') {
      if (!fs.existsSync(path.join(dir, s.tags.before))) missing.push(s.tags.before);
      if (s.fit !== 'cover' || s.clip) fail(`shot ${s.n}: [before: ...] works with a photo that fills the frame`);
    }
    if (typeof s.tags.callout === 'string') {
      const m = /^(\d+(?:\.\d+)?)%?\s*,\s*(\d+(?:\.\d+)?)%?\s+(.+)$/.exec(s.tags.callout);
      if (!m) fail(`shot ${s.n}: write a callout as [callout: 30%,60% the label]`);
      s.callout = { x: parseFloat(m[1]) / 100, y: parseFloat(m[2]) / 100, text: m[3].trim() };
    }
  }
  if (missing.length) fail(`Not found (relative to ${dir}):\n${missing.map((m) => `- ${m}`).join('\n')}\nRun "node montage.js inspect <folder> --slug ${slug}" to copy the photos in.`);
  // the price and specs go on the shot marked [facts], or the last
  const marked = shots.findIndex((s) => s.tags.facts);
  const facts = { shot: marked >= 0 ? marked : shots.length - 1 };

  // ---- the look and sound: a client's profile, or the project's own brand
  let profile = null;
  let look;
  let identity;
  if (meta.client) {
    profile = clientProfile(slugify(meta.client));
    look = visualIdentity(profile.file);
    identity = sonicIdentity(profile.file);
    if (!look) notes.push(`${path.basename(profile.file)} has no Visual Identity yet, so the page keeps the template's colors (not your own brand's)`);
    if (!identity) notes.push(`${path.basename(profile.file)} has no Sonic Identity yet, so the music is the template default (not your own brand's)`);
  } else {
    look = visualIdentity();
    identity = sonicIdentity();
  }

  // ---- depth maps, for the shots that move in 3D: the ones that ask for it, and (unless the
  // script says depth: off) every photo that fills the frame and has no move of its own
  const auto3d = String(meta.depth || 'auto').trim().toLowerCase() !== 'off';
  const flatOnly = (s) => (s.clip ? 'is a clip' : s.fit !== 'cover' ? `shows the whole photo (fit: ${s.fit})` : s.callout ? 'has a callout' : s.tags.before ? 'is a before/after' : '');
  for (const s of shots) {
    const why = !auto3d ? 'the script says depth: off' : flatOnly(s) ? `it ${flatOnly(s)}` : '';
    if (MOVES_3D.includes(s.move.name) && why) {
      notes.push(`shot ${s.n} can't move in 3D (${why}); it gets ${FLAT[s.move.name]} instead`);
      s.move.name = FLAT[s.move.name];
    }
  }
  const want = auto3d ? shots.filter((s) => !flatOnly(s) && (MOVES_3D.includes(s.move.name) || !s.move.name)) : [];
  const own = (s) => typeof s.tags.depth === 'string' && s.tags.depth;
  for (const s of want) if (own(s) && !fs.existsSync(path.join(dir, s.tags.depth))) fail(`shot ${s.n}: depth map ${s.tags.depth} not found (relative to ${dir})`);
  const toMake = [...new Set(want.filter((s) => !own(s) && !depthMaps.fresh(path.join(dir, s.media))).map((s) => path.join(dir, s.media)))];
  if (toMake.length && depthMaps.available()) {
    console.log(`Making depth maps for ${toMake.length} photo${toMake.length === 1 ? '' : 's'} (depth.js)...`);
    const res = run('depth.js', toMake, { stdio: ['ignore', 'inherit', 'pipe'] });
    if (res.status !== 0) notes.push(`no depth maps, so those shots move flat: ${(res.stderr || '').trim().split('\n').slice(0, 2).join(' ')}`);
  }
  for (const s of want) {
    if (own(s)) s.depthFile = s.tags.depth;
    else if (depthMaps.fresh(path.join(dir, s.media))) s.depthFile = path.relative(dir, depthMaps.depthPath(path.join(dir, s.media))).split(path.sep).join('/');
  }
  const flat = want.filter((s) => !s.depthFile);
  for (const s of flat.filter((x) => MOVES_3D.includes(x.move.name))) {
    notes.push(`shot ${s.n} has no depth map, so its ${s.move.name} is a flat ${FLAT[s.move.name]}`);
    s.move.name = FLAT[s.move.name];
  }
  if (flat.length && !depthMaps.available()) notes.push(`3D moves are off: they need a depth model. From scripts/video, run once: npm install @huggingface/transformers`);

  // ---- the voice: the user's recordings, or a generated voice, for the [say: ...] lines
  let said = shots.filter((s) => typeof s.tags.say === 'string' && s.tags.say);
  const voiceName = String(meta.voice || '').trim();
  if (said.length && !meta.recordings && voiceName.toLowerCase() === 'none') {
    notes.push('voice: none, so the [say: ...] lines are left out; set a voice (or recordings:) to voice them');
    said = [];
  } else if (!said.length && ((voiceName && voiceName.toLowerCase() !== 'none') || meta.recordings)) {
    notes.push('a voice is set, but no shot has a [say: ...] line');
  }
  if (said.length && meta.recordings) {
    for (const s of said) s.clipFile = meta.recordings.replace('{n}', String(s.n));
    const gone = said.filter((s) => !fs.existsSync(path.join(dir, s.clipFile)));
    if (gone.length) fail(`Recordings not found (relative to ${dir}):\n${gone.map((s) => `- ${s.clipFile}`).join('\n')}`);
  } else if (said.length) {
    const voice = voiceName || 'af_heart';
    const speed = String(meta.speed || 1);
    const prefix = `${slug}-say-`;
    for (const s of said) s.clipFile = `assets/${prefix}${s.n}.wav`;
    const fresh = said.every((s) => {
      const json = path.join(dir, s.clipFile.replace(/\.wav$/, '.json'));
      if (!fs.existsSync(path.join(dir, s.clipFile)) || !fs.existsSync(json)) return false;
      const m = JSON.parse(fs.readFileSync(json, 'utf8'));
      return m.text === s.tags.say && m.voice === voice && String(m.speed) === speed;
    });
    if (!fresh) {
      const tmp = path.join(assets, `.${slug}-say.md`);
      fs.writeFileSync(tmp, said.map((s) => `${s.n}. ${s.tags.say}`).join('\n') + '\n');
      console.log(`Voicing ${said.length} line${said.length === 1 ? '' : 's'} with ${voice} (voice.js)...`);
      const res = run('voice.js', [tmp, '--out', assets, '--voice', voice, '--speed', speed, '--prefix', prefix], { stdio: ['ignore', 'inherit', 'pipe'] });
      fs.rmSync(tmp, { force: true });
      if (res.status !== 0) fail(`${(res.stderr || '').trim()}\n\nOr use the user's own recordings: one file per [say: ...] line in assets/, and\n"recordings: assets/${slug}-{n}.m4a" in the frontmatter.`);
    }
  }
  for (const s of said) {
    s.say = s.tags.say;
    s.voiceLength = prepareVoice(path.join(dir, s.clipFile)).length;
  }

  // ---- the sound
  const template = fs.readFileSync(path.join(__dirname, 'templates', 'montage.html'), 'utf8');
  const sound = templateDefaults(template);
  delete sound.duration;
  delete sound.drop;
  if (identity) {
    Object.assign(sound, Object.fromEntries(Object.entries({
      music: identity.music, bpm: identity.bpm, key: identity.key, mode: identity.mode,
      energy: Number.isFinite(identity.energy) ? Math.max(1, identity.energy - (said.length ? 1 : 0)) : undefined, motif: identity.motif,
    }).filter(([, v]) => v !== undefined && v !== '' && !Number.isNaN(v))));
  } else if (kind === 'product') {
    Object.assign(sound, { music: 'pop', bpm: '112', energy: '3' });
  }
  const music = String(meta.music || 'identity').trim();
  let musicSrc = '';
  if (music.toLowerCase() === 'none') sound.music = 'none';
  else if (AUDIO_EXT.test(music)) {
    musicSrc = music;
    if (!fs.existsSync(path.join(dir, musicSrc))) fail(`Music not found: ${musicSrc} (relative to ${dir})`);
  } else if (music.toLowerCase() !== 'identity') {
    if (!GENRES[music.toLowerCase()]) fail(`music: ${music}? Use identity, none, a track file, or a genre: ${Object.keys(GENRES).join(', ')}.`);
    sound.music = music.toLowerCase();
  }
  if (parseFloat(meta.bpm) > 0) sound.bpm = String(parseFloat(meta.bpm));
  if (parseFloat(meta.energy) > 0) sound.energy = String(clamp(Math.round(parseFloat(meta.energy)), 1, 5));

  // ---- the beat: the generated music's tempo, or a licensed track's beats
  let beat = 60 / (parseFloat(sound.bpm) || 100);
  let track = null;
  if (musicSrc) {
    track = analyseTrack(path.join(dir, musicSrc));
    beat = 60 / track.bpm;
    if (track.confidence < 0.5) notes.push(`${musicSrc} has no steady beat to cut on (confidence ${track.confidence}), so the shots are timed in seconds instead`);
  }
  const snap = musicSrc ? track.confidence >= 0.5 : sound.music !== 'none';
  const pace = parseLength(meta.pace);
  if (meta.pace && !pace) fail(`pace: ${meta.pace}? Write it as "1 bar", "6 beats", or "2.5s".`);
  const toSeconds = (len) => (len.seconds !== undefined ? len.seconds : len.beats * beat);
  const unitBeats = (pace && pace.bars) || shots.some((s) => s.tags.hold && (parseLength(s.tags.hold) || {}).bars) ? 4 : 1;

  // ---- each shot's length: its hold, the pace, a share of the target length, or the default
  const holds = shots.map((s) => {
    if (!s.tags.hold) return null;
    const len = parseLength(s.tags.hold);
    if (!len) fail(`shot ${s.n}: hold: ${s.tags.hold}? Write it as "2 bars", "6 beats", or "3s".`);
    return toSeconds(len);
  });
  let each;
  if (pace) each = toSeconds(pace);
  else if (parseFloat(meta.length) > 0) {
    const free = holds.filter((h) => h === null).length;
    const left = parseFloat(meta.length) - holds.reduce((a, h) => a + (h || 0), 0);
    each = free ? left / free : MIN_SHOT;
    if (each < MIN_SHOT) notes.push(`${shots.length} shots in ${meta.length}s is ${each.toFixed(1)}s a shot, too quick to take in; drop about ${Math.ceil(shots.length - left / 2.2)} shots, or make it longer`);
    if (each > MAX_SHOT) notes.push(`${shots.length} shots in ${meta.length}s is ${each.toFixed(1)}s a shot, which drags; add about ${Math.ceil(left / 3 - shots.length)} photos, hold the best ones, or make it shorter`);
  } else each = DEFAULT_SHOT[kind];
  if (snap) each = Math.max(unitBeats, Math.round(each / (beat * unitBeats)) * unitBeats) * beat;

  // the least time a shot needs: its voice line, and long enough to read its text
  const hookWords = Math.max(words(meta.hook), words(meta['hook-b']), words(meta['hook-c']));
  const read = (n, lead) => (n >= 3 ? lead + n / READ_WPS + 0.6 : 0);
  const needs = shots.map((s, i) => {
    const textIn = i === 0 ? 0.6 : 0.2 + TRANSITIONS[s.transition] / 2;
    let need = Math.max(MIN_SHOT, read(words(s.label), textIn), read(words(s.sub), textIn));
    if (i === 0) need = Math.max(need, read(hookWords, 0), read(words(meta.status), 0.35));
    if (i === facts.shot) need = Math.max(need, read(words(meta.specs), 0.5), i === shots.length - 1 ? read(words(meta.cta), 0.9) : 0);
    if (i === shots.length - 1) need = Math.max(need, read(words(meta.cta), 0.9));
    if (s.callout) need = Math.max(need, read(words(s.callout.text), textIn + 0.3));
    if (s.say) need = Math.max(need, (i === 0 ? 0.15 : 0.3) + s.voiceLength + 0.35);
    return need;
  });

  // ---- the cuts: on the beat where there is one, after the first shot (where the beat drops)
  let grid = null;
  let musicStart;
  let t = 0;
  shots.forEach((s, i) => {
    const start = t;
    const planned = holds[i] ?? each;
    let end = start + Math.max(planned, needs[i]);
    const last = i === shots.length - 1;
    if (snap) {
      if (i === 0) {
        if (track) {
          for (const n of alignTrack(track, { align: r2(end), duration: end + (shots.length - 1) * each + 6 })) notes.push(`${musicSrc}: ${n}`);
          musicStart = track.musicStart;
          grid = unitBeats === 4 && track.barConfidence >= 0.15 ? track.video.bars : track.video.beats;
          // the first cut on the grid point nearest the lift, as long as the shot keeps its time
          const at = grid.filter((g) => g >= needs[0] - 1e-6).sort((a, b) => Math.abs(a - end) - Math.abs(b - end))[0];
          if (at !== undefined) end = at;
        }
      } else if (grid) {
        // the grid point nearest the planned cut that still leaves the shot its time
        // (the last shot, or one that needs a little longer than a bar, on a beat instead)
        const nearest = (points) => points.filter((g) => g >= start + needs[i] - 1e-6).sort((a, b) => Math.abs(a - end) - Math.abs(b - end))[0];
        let at = nearest(last ? track.video.beats : grid);
        if (at !== undefined && grid !== track.video.beats && at - (start + needs[i]) > 2 * beat) at = nearest(track.video.beats) ?? at;
        if (at !== undefined) end = at;
        else notes.push(`${musicSrc} ends before shot ${s.n}; it plays unsnapped from there`);
      } else {
        // the generated music's beat comes in at the first cut, so the grid starts there
        const drop = shots[0].end;
        // (the last shot, or one that needs a little longer than a bar, on a beat instead)
        let step = beat * (last ? 1 : unitBeats);
        const planned = end;
        end = drop + Math.ceil((end - drop) / step - 0.001) * step;
        if (end - start < needs[i] - 1e-6) end += step;
        if (step > beat && end - (start + needs[i]) > 2 * beat && planned < start + needs[i] + 1e-6) {
          step = beat;
          end = drop + Math.ceil((start + needs[i] - drop) / step - 0.001) * step;
        }
      }
    }
    if (needs[i] > planned + 0.01 && !s.say) notes.push(`shot ${s.n} held to ${(end - start).toFixed(1)}s so its text can be read`);
    s.start = r2(start);
    s.end = r2(end);
    t = end;
  });
  const drop = shots[0].end;
  const duration = shots[shots.length - 1].end;

  // ---- the backgrounds: one slot per shot, its move, fit, and transition
  const defaults = moveDefaults(kind);
  const slots = shots.map((s, i) => {
    const tr = TRANSITIONS[s.transition];
    const last = i === shots.length - 1;
    const next = shots[i + 1];
    const into = i === 0 ? 0 : r2(s.start - (s.transition === 'cut' || s.transition === 'flash' ? 0 : Math.min(0.3, tr / 2 + 0.05)));
    // a fade crossfades; under a cut, slide, or wipe this slot stays until the next covers it
    let out = null;
    if (!last) {
      const nextIn = r2(next.start - (next.transition === 'cut' || next.transition === 'flash' ? 0 : Math.min(0.3, TRANSITIONS[next.transition] / 2 + 0.05)));
      out = next.transition === 'fade' ? r2(s.end - 0.2) : r2(nextIn + TRANSITIONS[next.transition] + 0.05);
    }
    const dur = r2((last ? s.end : (out ?? s.end) + 0.45) - into);
    const move = resolveMove(s, dur, defaults, i > 0 ? shots[i - 1].moveName : '');
    notes.push(...move.notes);
    s.moveName = move.name;
    s.is3d = !!move.depth;
    s.place = move.place;
    const cls = ['bg', i === 0 ? 'now' : '', s.fit === 'cover' ? '' : s.fit === 'contain' ? 'fit' : 'card',
      i > 0 && s.transition !== 'fade' ? `t-${s.transition === 'flash' ? 'cut' : s.transition}` : ''].filter(Boolean).join(' ');
    const vars = { '--in': `${into}s`, ...(out !== null ? { '--out': `${out}s` } : {}), '--dur': `${dur}s`, '--shade': 0, ...move.vars };
    if (s.tags.before) vars['--at'] = `${r2(s.start + Math.max(0.8, 0.4 * (s.end - s.start)))}s`;
    const style = Object.entries(vars).map(([k, v]) => `${k}:${v}`).join('; ');
    const src = esc(s.media);
    const media = (extra = '') => (s.clip
      ? `<video class="bg-media${extra}" src="${src}" data-loop="false"${s.tags.from ? ` data-offset="${parseFloat(s.tags.from) || 0}"` : ''}></video>`
      : `<img class="bg-media${extra}" src="${src}" alt="">`);
    let inner;
    if (move.depth) {
      const d = move.depth;
      const r3 = (v) => Math.round(v * 1000) / 1000;
      inner = `<canvas class="bg-media depth" width="${W}" height="${H}" data-src="${src}" data-depth="${esc(s.depthFile)}" data-move="${d.move}"`
        + ` data-focus="${r3(d.focus[0])},${r3(d.focus[1])}" data-pos="${r3(d.pos[0])},${r3(d.pos[1])}"${d.pan ? ` data-pan="${r3(d.pan[0])},${r3(d.pan[1])}"` : ''}`
        + ` data-zoom="${d.zoom}" data-amount="${d.amount}"></canvas>`;
    } else if (s.fit === 'contain') inner = media(' backdrop') + media(' whole');
    else if (s.fit === 'card') inner = media(' whole');
    else if (s.tags.before) inner = `<img class="bg-media" src="${esc(s.tags.before)}" alt="">${media(' after')}<div class="seam"></div>`;
    else inner = media();
    const sfx = i > 0 && ['slide', 'wipe', 'zoom'].includes(s.transition) ? ' data-sfx="whoosh"' : '';
    const flash = i > 0 && s.transition === 'flash' ? `\n  <div class="flash" style="--in:${s.start}s" data-sfx="shutter"></div>` : '';
    if (s.clip && s.info.duration - (parseFloat(s.tags.from) || 0) < s.end - into) {
      notes.push(`shot ${s.n}'s clip runs ${(s.info.duration - (parseFloat(s.tags.from) || 0)).toFixed(1)}s, less than the shot; it holds on its last frame`);
    }
    return `  <!-- shot ${s.n}, ${s.start}–${s.end}s: ${s.media} -->\n  <div class="${cls}" style="${style}"${sfx}>${inner}</div>${flash}`;
  });

  // ---- the text on each shot
  const hooks = [meta.hook, meta['hook-b'], meta['hook-c']].filter(Boolean);
  // under a voice, sounds only at the cuts (and the price), so they don't talk over it
  const quiet = said.length > 0;
  const scenes = shots.map((s, i) => {
    const last = i === shots.length - 1;
    const textIn = r2(s.start + (i === 0 ? 0.6 : 0.2 + TRANSITIONS[s.transition] / 2));
    const parts = [];
    if (i === 0 && (hooks.length || meta.status)) {
      const top = hooks.map((h, k) => `      <div class="cap left hook now"${hooks.length > 1 ? ` data-variant="${'abc'[k]}"` : ''}><span>${esc(h)}</span></div>`);
      if (meta.status) top.push(`      <div class="sticker yellow pop" style="--in:.35s" data-sfx="pop">${esc(meta.status)}</div>`);
      parts.push(`    <div class="top">\n${top.join('\n')}\n    </div>`);
    }
    if (i === facts.shot && (meta.price || meta.specs || (last && meta.cta))) {
      const f = [];
      if (meta.price) f.push(`      <div class="price pop" style="--in:${r2(s.start + 0.2)}s" data-sfx="chime">${esc(meta.price)}</div>`);
      if (meta.specs) f.push(`      <div class="specs rise" style="--in:${r2(s.start + 0.5)}s">${meta.specs.split(/\s*[·|•]\s*/).filter(Boolean).map((x) => `<span>${esc(x)}</span>`).join('')}</div>`);
      if (last && meta.cta) f.push(`      <div class="cap hl pop" style="--in:${r2(s.start + 0.9)}s"><span>${esc(meta.cta)}</span></div>`);
      // on a packshot, below the product rather than over it
      parts.push(`    <div class="facts${s.fit === 'card' ? ' low' : ''}">\n${f.join('\n')}\n    </div>`);
    } else if (last && meta.cta) {
      parts.push(`    <div class="facts">\n      <div class="cap hl pop" style="--in:${r2(s.start + 0.4)}s" data-sfx="chime"><span>${esc(meta.cta)}</span></div>\n    </div>`);
    }
    if (s.tags.before) {
      const at = r2(s.start + Math.max(0.8, 0.4 * (s.end - s.start)));
      parts.push(`    <div class="stack ba"><div class="sticker dark swap" style="--in:${textIn}s; --out:${at}s">before</div><div class="sticker swap" style="--in:${at}s"${quiet ? '' : ' data-sfx="whoosh"'}>after</div></div>`);
    }
    if (s.tags.staged) parts.push(`    <div class="staged fade" style="--in:${textIn}s">Virtually staged</div>`);
    if (s.label) parts.push(`    <div class="lt pop" style="--in:${textIn}s"><b>${esc(s.label)}</b>${s.sub ? `<small>${esc(s.sub)}</small>` : ''}</div>`);
    if (s.callout) {
      const pl = placement(s.info, s.fit, [s.callout.x, s.callout.y]);
      const cls = `${pl.x > W / 2 ? ' left' : ''}${pl.y < SCENE.top + 180 ? ' below' : ''}`;
      parts.push(`    <div class="callout pop${cls}" style="--in:${r2(textIn + 0.3)}s; left:${Math.round(pl.x - SCENE.left)}px; top:${Math.round(pl.y - SCENE.top)}px"${quiet ? '' : ' data-sfx="pop"'}><i></i><span>${esc(s.callout.text)}</span></div>`);
    }
    if (s.say) parts.push(`    <div class="say auto" data-voice="${esc(s.clipFile)}" style="--voice:${r2(s.start + (i === 0 ? 0.15 : 0.3))}s">${esc(s.say)}</div>`);
    return `  <!-- shot ${s.n}, ${s.start}–${s.end}s -->\n  <div class="scene shot"${last ? '' : ` style="--out:${r2(s.end - 0.15)}s"`}>\n${parts.join('\n')}\n  </div>`;
  });

  // ---- the page
  const head = template.slice(template.indexOf('<html>'), template.indexOf('</head>') + '</head>'.length);
  const attrs = [
    'class="montage"', `data-duration="${duration}"`, `data-drop="${drop}"`,
    ...(musicSrc ? [`data-music-src="${esc(musicSrc)}"`, `data-music-start="${musicStart ?? 0}"`, 'data-music="none"'] : [`data-music="${sound.music}"`]),
    ...['bpm', 'key', 'mode', 'energy', 'motif'].filter((k) => sound[k] !== undefined).map((k) => `data-${k}="${esc(String(sound[k]))}"`),
  ].join(' ');
  const doc = `<!doctype html>
<!--
  Montage, written by scripts/video/montage.js from ${path.relative(dir, path.resolve(scriptFile))}.
  Edit the script and run montage.js again rather than editing the timing here. Page
  conventions: see the comment at the top of templates/promo.html, and templates/montage.html
  for the moves, fits, transitions, and overlays.
-->
${head}
<body ${attrs}>
  <div class="glow g1"></div>
  <div class="glow g2"></div>
${slots.join('\n')}

${scenes.join('\n\n')}
</body>
</html>
`;

  // ---- the look, and the end card with the client's contact details
  const lines = profile ? [[profile.name, profile.business].filter(Boolean).join(' · '), [profile.phone, profile.website || profile.email].filter(Boolean).join(' · ')].filter(Boolean) : [];
  const fine = profile ? profile.fine : '';
  const longest = Math.max(0, ...lines.map(words), words(fine));
  const seconds = r2(clamp(longest / READ_WPS + 1.3, 2.5, 4.5));
  if (words(fine) > 14) notes.push(`the fine print is ${words(fine)} words; it gets ${seconds}s on the end card, so keep it short or put the rest in the caption`);
  const branded = look || lines.length || fine
    ? applyIdentity(doc, look || {}, { pageDir: dir, lines, fine, seconds })
    : { html: doc, changes: [], problems: [] };
  fs.writeFileSync(page, branded.html);
  const total = parseFloat((/<body[^>]*data-duration="([\d.]+)"/.exec(branded.html.slice(branded.html.indexOf('</head>'))) || [])[1]) || duration;

  console.log(`Wrote ${page}: ${shots.length} shots, ${total}s${total !== duration ? ` (${duration}s of shots and the end card)` : ''}`);
  for (const s of shots) {
    const what = [s.is3d ? `${s.moveName} (3D)` : s.moveName, s.fit !== 'cover' ? `fit ${s.fit}` : '', s.transition !== 'fade' && s.n !== shots[0].n ? s.transition : '', s.say ? 'voiced' : '', s.tags.staged ? 'staged' : ''].filter(Boolean).join(', ');
    console.log(`  ${String(s.n).padStart(2)}. ${s.start.toFixed(2)}–${s.end.toFixed(2)}s  ${s.media.padEnd(22)} ${what.padEnd(24)} ${[s.label, s.sub].filter(Boolean).join(' | ').slice(0, 44)}`);
  }
  const soundLine = musicSrc
    ? `licensed track ${musicSrc}${track ? `, ${track.bpm} BPM, from ${musicStart ?? 0}s${snap ? `, cuts on the ${unitBeats === 4 && track.barConfidence >= 0.15 ? 'bar' : 'beat'}` : ''}` : ''}`
    : `${sound.music}${sound.music !== 'none' ? `, ${sound.bpm} BPM, ${sound.key} ${sound.mode || ''}, energy ${sound.energy}, cuts on the ${unitBeats === 4 ? 'bar' : 'beat'}` : ''}${identity ? ` (${sound.music === identity.music ? '' : 'in the key and hook of '}${profile ? 'the client\'s' : 'the'} Sonic Identity)` : ' (no Sonic Identity saved; the template default)'}`;
  console.log(`  sound: ${soundLine}`);
  if (said.length) console.log(`  voice: ${meta.recordings ? `the user's recordings (${meta.recordings})` : voiceName || 'af_heart'}, ${said.length} line${said.length === 1 ? '' : 's'}`);
  console.log(`  look: ${branded.changes.length ? branded.changes.join('; ') : 'the template default'}${profile ? ` (client ${path.basename(profile.file, '.md')})` : ''}`);
  for (const p of branded.problems) notes.push(p);
  if (!hooks.length) notes.push('no hook, so the first frame has no text; add "hook: ..." to stop the scroll');
  if (!meta.cta) notes.push('no cta, so the video ends without asking for anything; add "cta: ..."');
  for (const n of [...new Set(notes)]) console.warn(`Note: ${n}`);
  if (!args.noCheck) {
    const check = run('render.js', [page, '--check'], { stdio: 'inherit' });
    if (check.status !== 0) console.warn('Fix what --check lists (usually a label that runs long), then run montage.js again.');
  }
  const show = (f) => (path.relative(process.cwd(), f).startsWith('..') ? f : path.relative(process.cwd(), f));
  console.log(`Next: node ${show(path.join(__dirname, 'render.js'))} ${show(page)} --slides, then render it to an .mp4.`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.positional.length) {
    console.log(fs.readFileSync(__filename, 'utf8').split('*/')[0].replace(/^[\s\S]*?\/\*/, '').replace(/^ \* ?/gm, ''));
    process.exit(args.help ? 0 : 2);
  }
  if (args.positional[0] === 'inspect') {
    args.positional.shift();
    if (!args.positional.length) fail('Give the folder (or files) to inspect: node montage.js inspect <folder> --slug <name>');
    return inspect(args);
  }
  return build(args);
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { parseShotLine, parseLength, placement };
