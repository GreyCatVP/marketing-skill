#!/usr/bin/env node
'use strict';
/*
 * Builds a narrated video page from a script, in one step: a voiceover line by line, one
 * background per line, word-by-word captions synced to the voice, the hook on screen from the
 * first frame, and the project's sound. The page is templates/narrated.html's look (or, with a
 * style, 3d.html's or pixel.html's), timed to the voice; render.js turns it into the MP4.
 *
 * Usage:
 *   node compose.js <script.md> [--out <page.html>] [--voice af_heart] [--speed 1]
 *                   [--style photo|3d|pixel] [--no-media] [--no-check]
 *
 * The script is Markdown: optional frontmatter, then numbered lines, one per scene. A line can
 * end with a background: [bg: a search query] fetches a stock photo for it (media.js), and
 * [bg: assets/file.jpg] uses a file (a .mp4 or .mov plays as a clip).
 *
 *   ---
 *   title: three invoice mistakes
 *   hook: you're losing money on every late invoice     # on screen from the first frame
 *   cta: one money habit a week                         # on screen in the last scene
 *   voice: af_heart                                     # a voice.js voice, or:
 *   recordings: assets/invoices-{n}.m4a                 # the user's own takes, one per line, instead
 *   bg: freelancer desk                                 # for lines without their own [bg: ...]
 *   bg-type: photo                                      # or video (needs a Pexels or Pixabay key)
 *   music: identity                                     # identity (default), none, a genre, or assets/track.mp3
 *   ---
 *   1. Most freelancers lose money on invoices they send late. [bg: stressed laptop night]
 *   2. Clients pay fastest when the invoice lands the day the work ends.
 *
 * Animated styles: "style: 3d" draws each line's background as a 3D scene (templates/3d.html)
 * and "style: pixel" as pixel art (templates/pixel.html, with chiptune music in the identity's
 * key and hook). Each line gets a shot instead of a photo, picked in turn unless the line names
 * one, with the shot's settings as key=value pairs:
 *   1. Every freelancer starts at level one. [shot: walk time=sunset]
 *   2. We built it for this screen. [shot: hero src=assets/app-screen.png]
 *   3. Plan it, film it, post it. [shot: cards items="Plan,Film,Post"]
 * The shots and their settings are listed at the top of each template. With "style: 3d" and no
 * shots named, the brand's 3D mascot presents: it waves, talks with the voice, points, and cheers.
 *   1. We built an editor that edits for you. [shot: desk src=assets/app-screen.png]
 *   2. Here it is. [shot: mascot do=present prop=screen src=assets/app-screen.png]
 *
 * The bold look ("captions: bold"): heavy capitals boxed in black, each word popping as it's
 * said. A short line (up to 8 words) shows whole, a longer one a few words at a time so it
 * doesn't bury the picture, and the first line shows whole from frame 0, so it makes the cover. *Words* in asterisks stay yellow, in the lines and the hook (the asterisks
 * aren't spoken). When the hook is the first line, it shows once, as that line's caption.
 * "series: week 2" and "brand: Your Name" put a tag in each top corner for the whole video.
 *
 * A screen in a photo: [bg: assets/me-laptop.jpg screen=assets/app.png at=x1,y1,x2,y2,x3,y3,x4,y4]
 * puts the user's screenshot on the laptop or phone screen in their own photo, from the screen's
 * four corners in the photo's pixels (top left, top right, bottom right, bottom left), moving
 * with the photo's zoom. Check the fit with render.js --stills.
 *
 * Voices come from voice.js (Kokoro, free and local; `npm install kokoro-js` once) unless
 * `recordings` points at the user's own files. The music follows the Sonic Identity saved in
 * references/brand-voice.md, one energy step lower so it sits under the voice, with scene
 * changes moved onto its beat, and the look follows its Visual Identity (brand.js), end card
 * included. Without --out, the page goes to state/videos/<date>-<slug>.html,
 * with media and voice files in state/videos/assets/.
 */
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { parseScript } = require('./voice');
const { prepareVoice } = require('./render');
const { visualIdentity, applyIdentity } = require('./brand');
const { analyseTrack, alignTrack } = require('./beats');

const ROOT = path.resolve(__dirname, '..', '..');
const LEAD = 0.15; // the first line starts almost at once; the hook is already on screen
const GAP = 0.35; // a beat between one line ending and the next scene
const TAIL = 1.2; // after the last line, room for the sonic logo
const BOLD_WHOLE = 8; // in the bold look, lines of up to this many words show whole
const MEDIA_EXT = /\.(jpe?g|png|webp|gif|mp4|mov|webm|m4v)$/i;
const VIDEO_EXT = /\.(mp4|mov|webm|m4v)$/i;

// The looks a script can take: photo backgrounds, or a background drawn per line. A drawn style
// opens on `first`, closes on `last`, and takes the middle lines' shots from `cycle` in turn,
// each with the sound it lands on (one per shot, so effects don't crowd the voice). The cycles
// leave out shots that would claim something: a chart without the user's numbers, or a product
// screen without their screenshot.
const STYLES = {
  photo: { template: 'narrated.html' },
  '3d': {
    template: '3d.html', canvas: '<canvas class="art" width="1080" height="1920" data-lint="off"></canvas>',
    shots: ['mascot', 'desk', 'title', 'icons', 'notes', 'button', 'shapes', 'hero', 'cards', 'chart', 'coin', 'rings', 'globe'],
    // the mascot presents, with a few abstract shots between its lines for pace
    first: 'mascot do=wave', last: 'mascot do=cheer',
    cycle: ['mascot do=talk', 'globe', 'mascot do=point', 'cards', 'mascot do=thumbs', 'rings', 'mascot do=present', 'shapes'],
    sfx: { cards: 'swish:card-1', coin: 'ding:land', 'mascot:cheer': 'pop:land', 'mascot:walk': 'pop:stop', desk: 'whoosh:enter', title: 'pop:done', icons: 'pop:done', notes: 'swish:note-1', button: 'click:click' },
  },
  pixel: {
    template: 'pixel.html', canvas: '<canvas class="art" width="135" height="240" data-lint="off"></canvas>',
    shots: ['walk', 'boss', 'coins', 'levelup', 'city', 'space', 'photo'],
    first: 'walk', last: 'space', cycle: ['boss', 'coins', 'levelup', 'city'], // pixel's own shots, no mascot
    sfx: { boss: 'hurt:hit', coins: 'coin:open', levelup: 'powerup:up' },
    music: 'chiptune', // in the identity's key and hook, the way everyday posts borrow a genre
  },
};

// "[shot: hero src=assets/screen.png]" -> { name: 'hero', attrs: { src: 'assets/screen.png' } }
function parseShot(text) {
  const [name, ...rest] = text.trim().split(/\s+/);
  const attrs = {};
  for (const m of rest.join(' ').matchAll(/([\w-]+)=(?:"([^"]*)"|'([^']*)'|(\S+))/g)) attrs[m[1].toLowerCase()] = m[2] ?? m[3] ?? m[4];
  return { name: name.toLowerCase(), attrs };
}

function fail(message) {
  console.error(message);
  process.exit(2);
}

function parseArgs(argv) {
  const args = { positional: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--no-media') args.noMedia = true;
    else if (a === '--no-check') args.noCheck = true;
    else if (['--out', '--voice', '--speed', '--style'].includes(a)) args[a.slice(2)] = argv[++i];
    else if (a === '-h' || a === '--help') args.help = true;
    else args.positional.push(a);
  }
  return args;
}

function parseFrontmatter(text) {
  const m = /^---\n([\s\S]*?)\n---\n?/.exec(text);
  if (!m) return { meta: {}, body: text };
  const meta = {};
  for (const line of m[1].split('\n')) {
    // a comment starts at " # ", so a value can still hold "#" ("lot #12", "DRE #0123")
    const kv = /^\s*([\w-]+)\s*:\s*(.*?)(?:\s+#\s.*)?\s*$/.exec(line);
    if (kv) meta[kv[1].toLowerCase()] = kv[2].replace(/^["']|["']$/g, '');
  }
  return { meta, body: text.slice(m[0].length) };
}

// "assets/me.jpg screen=assets/app.png at=1,2,3,4,5,6,7,8" -> { query: 'assets/me.jpg', screen, at }
function parseBg(text) {
  const opts = {};
  const query = text.replace(/\s+([\w-]+)=("[^"]*"|\S+)/g, (_, k, v) => { opts[k.toLowerCase()] = v.replace(/^"|"$/g, ''); return ''; }).trim();
  return { query, ...opts };
}

// *keywords* in a line: the text without the asterisks (what's spoken and captioned), and the
// words to keep lit in the bold look
const plainText = (s) => s.replace(/\*([^*]+)\*/g, '$1');
const wordKey = (w) => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
const keywords = (s) => [...s.matchAll(/\*([^*]+)\*/g)].flatMap((m) => m[1].split(/\s+/)).map(wordKey).filter(Boolean);

const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'narrated';
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const r2 = (t) => Math.round(t * 100) / 100;

// The Sonic Identity from brand-voice.md (or a client's profile), or null while it's still the placeholder.
function sonicIdentity(file = path.join(ROOT, 'references', 'brand-voice.md')) {
  if (!fs.existsSync(file)) return null;
  const text = fs.readFileSync(file, 'utf8');
  const section = (/^## Sonic Identity\n([\s\S]*?)(?=^## |$(?![\s\S]))/m.exec(text) || [])[1] || '';
  if (!section.trim() || /not yet configured/i.test(section)) return null;
  const field = (name) => ((new RegExp(`^-\\s*${name}:\\s*(.+)$`, 'mi')).exec(section) || [])[1];
  const key = /([A-G](?:#|b)?)\s*(major|minor)?/i.exec(field('Key') || '');
  const id = {
    music: (field('Genre') || '').trim().toLowerCase(),
    bpm: parseFloat(field('Tempo')),
    key: key ? key[1].toUpperCase() + key[1].slice(1) : undefined,
    mode: key && key[2] ? key[2].toLowerCase() : undefined,
    energy: parseFloat(field('Energy')),
    motif: (field('Hook') || '').trim(),
  };
  return id.music ? id : null;
}

// The template's own body settings, as the fallback for anything the identity doesn't set.
function templateDefaults(html) {
  const body = /<body([^>]*)>/.exec(html)[1];
  const out = {};
  for (const m of body.matchAll(/data-([\w-]+)="([^"]*)"/g)) out[m[1]] = m[2];
  return out;
}

function run(cmd, args, opts = {}) {
  return spawnSync(process.execPath, [path.join(__dirname, cmd), ...args], { encoding: 'utf8', ...opts });
}

// One stock photo or clip for a query, via media.js. Returns a path relative to the page, or null.
function fetchBackground(query, assets, type) {
  const res = run('media.js', ['search', query, '--out', assets, '--count', '1', ...(type === 'video' ? ['--type', 'video'] : [])]);
  if (res.status !== 0) {
    console.warn(`Note: no background for "${query}": ${(res.stderr || '').trim().split('\n').slice(-3).join(' ')}`);
    return null;
  }
  try {
    const data = JSON.parse(res.stdout.slice(res.stdout.indexOf('{')));
    return `assets/${data.files[0].file}`;
  } catch {
    return null;
  }
}

// The user's screenshot on the screen in their photo: a projective map from the screenshot's own
// corners to the four in data-at (photo pixels, after the photo is cropped to fill the frame),
// set before the first frame. It sits in .bg-insert, which zooms with the photo.
const INSERT_JS = `<script>
window.renderReady = Promise.all([...document.querySelectorAll('.bg-insert')].map(async (box) => {
  const photo = box.parentElement.querySelector('img.bg-media');
  const shot = box.querySelector('img');
  await Promise.all([photo.decode(), shot.decode()]);
  const k = Math.max(1080 / photo.naturalWidth, 1920 / photo.naturalHeight);
  const [ox, oy] = [(1080 - photo.naturalWidth * k) / 2, (1920 - photo.naturalHeight * k) / 2];
  const at = box.dataset.at.split(/[\\s,]+/).map(Number);
  const [w, h] = [shot.naturalWidth, shot.naturalHeight];
  const rows = [], rhs = [];
  [[0, 0], [w, 0], [w, h], [0, h]].forEach(([x, y], i) => {
    const [u, v] = [ox + at[2 * i] * k, oy + at[2 * i + 1] * k];
    rows.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); rhs.push(u);
    rows.push([0, 0, 0, x, y, 1, -v * x, -v * y]); rhs.push(v);
  });
  for (let c = 0; c < 8; c++) { // Gaussian elimination with partial pivoting
    let p = c;
    for (let r = c + 1; r < 8; r++) if (Math.abs(rows[r][c]) > Math.abs(rows[p][c])) p = r;
    [rows[c], rows[p]] = [rows[p], rows[c]]; [rhs[c], rhs[p]] = [rhs[p], rhs[c]];
    for (let r = 0; r < 8; r++) {
      if (r === c) continue;
      const f = rows[r][c] / rows[c][c];
      for (let j = c; j < 8; j++) rows[r][j] -= f * rows[c][j];
      rhs[r] -= f * rhs[c];
    }
  }
  const [a, b, c, d, e, f, g, hh] = rhs.map((v, i) => v / rows[i][i]);
  shot.style.width = w + 'px';
  shot.style.height = h + 'px';
  shot.style.transform = 'matrix3d(' + [a, d, 0, g, b, e, 0, hh, 0, 0, 1, 0, c, f, 0, 1].join(',') + ')';
}));
</script>
`;

function bgSlot(i, a, b, last, media, insert) {
  const start = i === 0 ? 0 : r2(a - 0.25);
  const end = last ? null : r2(b - 0.2);
  const dur = r2((last ? b : b + 0.45) - start);
  const style = `--in:${start}s; ${end !== null ? `--out:${end}s; ` : ''}--dur:${dur}s`;
  const inner = !media ? ''
    : VIDEO_EXT.test(media) ? `<video class="bg-media" src="${esc(media)}"></video>`
      : `<img class="bg-media" src="${esc(media)}" alt="">${insert ? `<div class="bg-insert" data-at="${esc(insert.at)}"><img src="${esc(insert.screen)}" alt=""></div>` : ''}`;
  return `  <!-- background, ${r2(a)}–${r2(b)}s -->\n  <div class="${i === 0 ? 'bg now' : 'bg'}" style="${style}">${inner}</div>`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scriptFile = args.positional[0];
  if (args.help || !scriptFile) {
    console.log(fs.readFileSync(__filename, 'utf8').split('*/')[0].replace(/^[\s\S]*?\/\*/, '').replace(/^ \* ?/gm, ''));
    process.exit(args.help ? 0 : 2);
  }
  if (!fs.existsSync(scriptFile)) fail(`No script at ${scriptFile}`);
  const { meta, body } = parseFrontmatter(fs.readFileSync(scriptFile, 'utf8'));
  const styleName = String(args.style || meta.style || 'photo').toLowerCase();
  const style = STYLES[styleName];
  if (!style) fail(`Unknown style "${styleName}" (use ${Object.keys(STYLES).join(', ')}).`);
  const lines = parseScript(body).map(({ n, text }) => {
    const bg = parseBg(((/\[bg:\s*([^\]]+)\]/i.exec(text) || [])[1] || meta.bg || '').trim());
    const shot = /\[shot:\s*([^\]]+)\]/i.exec(text);
    const said = text.replace(/\s*\[(bg|shot):[^\]]*\]/gi, '').trim();
    return {
      n, text: plainText(said), kw: keywords(said),
      bg: bg.query, screen: bg.screen, at: bg.at, shot: shot ? parseShot(shot[1]) : null,
    };
  }).filter((l) => l.text);
  const bold = String(meta.captions || '').toLowerCase() === 'bold';
  if (!lines.length) fail(`No lines in ${scriptFile}; number them "1. ...", one per scene.`);
  if (style.shots) {
    if (lines.some((l) => l.bg)) console.warn(`Note: [bg: ...] and bg: are for photo backgrounds; style ${styleName} draws each line's background, so they're ignored (use [shot: ...]).`);
    const bad = lines.filter((l) => l.shot && !style.shots.includes(l.shot.name));
    if (bad.length) fail(`Unknown shot${bad.length > 1 ? 's' : ''} for style ${styleName}: ${bad.map((l) => `"${l.shot.name}" (line ${l.n})`).join(', ')}. The shots are ${style.shots.join(', ')}.`);
    let k = 0;
    lines.forEach((l, i) => {
      if (l.shot) return;
      l.shot = parseShot(i === 0 ? style.first : i === lines.length - 1 && lines.length > 1 ? style.last : style.cycle[k++ % style.cycle.length]);
    });
  } else if (lines.some((l) => l.shot)) {
    console.warn('Note: [shot: ...] needs "style: 3d" or "style: pixel" in the frontmatter; ignored for photo backgrounds.');
  }

  const slug = slugify(meta.title || path.basename(scriptFile, path.extname(scriptFile)));
  const page = path.resolve(args.out || path.join(ROOT, 'state', 'videos', `${new Date().toISOString().slice(0, 10)}-${slug}.html`));
  const dir = path.dirname(page);
  const assets = path.join(dir, 'assets');
  fs.mkdirSync(assets, { recursive: true });
  for (const l of lines) {
    const src = l.shot && l.shot.attrs.src;
    if (src && !fs.existsSync(path.join(dir, src))) console.warn(`Note: ${src} (line ${l.n}'s ${l.shot.name} shot) not found next to the page; put it in assets/`);
    if (l.screen && !fs.existsSync(path.join(dir, l.screen))) console.warn(`Note: ${l.screen} (line ${l.n}'s screen) not found next to the page; put it in assets/`);
    if (l.screen && !/^(\s*-?[\d.]+\s*,){7}\s*-?[\d.]+\s*$/.test(l.at || '')) fail(`Line ${l.n}: screen= needs at=x1,y1,x2,y2,x3,y3,x4,y4, the screen's corners in the photo's pixels (top left, top right, bottom right, bottom left).`);
  }

  // ---- the voice: the user's recordings, or a generated voice
  let clips;
  if (meta.recordings) {
    clips = lines.map((l) => meta.recordings.replace('{n}', String(l.n)));
    const missing = clips.filter((c) => !fs.existsSync(path.join(dir, c)));
    if (missing.length) fail(`Recordings not found (relative to ${dir}):\n${missing.map((m) => `- ${m}`).join('\n')}`);
  } else {
    const voice = args.voice || meta.voice || 'af_heart';
    const speed = String(args.speed || meta.speed || 1);
    const prefix = `${slug}-`;
    clips = lines.map((l) => `assets/${prefix}${l.n}.wav`);
    const fresh = lines.every((l, i) => {
      const json = path.join(dir, clips[i].replace(/\.wav$/, '.json'));
      if (!fs.existsSync(path.join(dir, clips[i])) || !fs.existsSync(json)) return false;
      const m = JSON.parse(fs.readFileSync(json, 'utf8'));
      return m.text === l.text && m.voice === voice && String(m.speed) === speed;
    });
    if (!fresh) {
      const tmp = path.join(assets, `.${slug}-script.md`);
      fs.writeFileSync(tmp, lines.map((l) => `${l.n}. ${l.text}`).join('\n') + '\n');
      console.log(`Voicing ${lines.length} lines with ${voice} (voice.js)...`);
      const res = run('voice.js', [tmp, '--out', assets, '--voice', voice, '--speed', speed, '--prefix', prefix], { stdio: ['ignore', 'inherit', 'pipe'] });
      fs.rmSync(tmp, { force: true });
      if (res.status !== 0) {
        fail(`${(res.stderr || '').trim()}\n\nOr use the user's own recordings: record each line as its own file in assets/ and add\n"recordings: assets/${slug}-{n}.m4a" to the script's frontmatter.`);
      }
    }
  }

  // ---- timing: each scene is its line plus a beat, with cuts on the music's beat
  const html = fs.readFileSync(path.join(__dirname, 'templates', style.template), 'utf8');
  const defaults = templateDefaults(html);
  const identity = sonicIdentity();
  const music = (meta.music || 'identity').trim();
  const sound = { ...defaults };
  if (identity) {
    Object.assign(sound, Object.fromEntries(Object.entries({
      music: identity.music, bpm: identity.bpm, key: identity.key, mode: identity.mode,
      energy: Number.isFinite(identity.energy) ? Math.max(1, identity.energy - 1) : undefined, motif: identity.motif,
    }).filter(([, v]) => v !== undefined && v !== '' && !Number.isNaN(v))));
  }
  if (style.music && !meta.music) sound.music = style.music; // an explicit music: line, identity included, wins
  let musicSrc = '';
  if (music === 'none') sound.music = 'none';
  else if (MEDIA_EXT.test(music) || /\.(mp3|m4a|wav|aac|ogg|flac)$/i.test(music)) musicSrc = music;
  else if (music !== 'identity') sound.music = music;
  const beat = 60 / (parseFloat(sound.bpm) || 112);
  const snap = !musicSrc && sound.music !== 'none';
  // A licensed track with a steady beat gets the same treatment as the generated music: it starts
  // so its biggest lift lands as the hook ends, and scenes cut on its beats (beats.js). Below 0.5
  // confidence the scenes follow the voice alone.
  let track = null;
  if (musicSrc && fs.existsSync(path.join(dir, musicSrc))) {
    track = analyseTrack(path.join(dir, musicSrc));
    if (track.confidence < 0.5) {
      console.warn(`Note: ${musicSrc}'s beat is unclear (confidence ${track.confidence}), so scenes follow the voice, not the beat.`);
      track = null;
    }
  }
  const trackNotes = [];

  const scenes = [];
  let t = LEAD;
  let drop = 0;
  lines.forEach((l, i) => {
    const { length } = prepareVoice(path.join(dir, clips[i]));
    const start = t;
    let end = start + length + GAP;
    if (i === 0) {
      drop = r2(end);
      if (track) trackNotes.push(...alignTrack(track, { align: drop })); // the length is checked below, once it's known
    } else if (snap) end = drop + Math.ceil((end - drop) / beat - 1e-6) * beat;
    else if (track) end = track.video.beats.find((b) => b >= end - 1e-6 && b - end < 0.7) ?? end;
    scenes.push({ ...l, clip: clips[i], start: r2(start), length, end: r2(end) });
    t = end;
  });
  const duration = r2(scenes[scenes.length - 1].start + scenes[scenes.length - 1].length + TAIL);
  if (track) sound.bpm = track.bpm; // the page's tempo is the track's, so anything on the beat (the mascot's dance) follows it
  scenes[scenes.length - 1].end = duration;

  // ---- backgrounds (a drawn style draws its own)
  for (const s of scenes) {
    if (!s.bg || style.shots) continue;
    if (MEDIA_EXT.test(s.bg)) {
      if (!fs.existsSync(path.join(dir, s.bg))) console.warn(`Note: background ${s.bg} not found next to the page`);
      s.media = s.bg;
    } else if (!args.noMedia) {
      s.media = fetchBackground(s.bg, assets, meta['bg-type']);
    }
  }

  // ---- the page
  const head = html.slice(html.indexOf('<html>'), html.indexOf('</head>') + '</head>'.length);
  const bodyClass = (/<body[^>]*\bclass="([^"]*)"/.exec(html.slice(html.indexOf('</head>'))) || [])[1] || 'fyp';
  const attrs = [
    `class="${bodyClass}${bold ? ' bold' : ''}"`, `data-duration="${duration}"`, `data-drop="${drop}"`,
    ...(musicSrc ? [`data-music-src="${esc(musicSrc)}"`, 'data-music="none"', ...(track ? [`data-music-start="${track.musicStart}"`] : [])] : [`data-music="${sound.music}"`]),
    ...['bpm', 'key', 'mode', 'energy', 'motif'].filter((k) => sound[k] !== undefined).map((k) => `data-${k}="${esc(String(sound[k]))}"`),
  ].join(' ');
  // the bold look shows the first line from frame 0; a hook that is that line isn't shown twice
  const hookIsLine = bold && meta.hook && wordKey(plainText(meta.hook)) === wordKey(scenes[0].text);
  const lit = (text) => esc(text).replace(/\*([^*]+)\*/g, '<b class="kw">$1</b>');
  const sceneHtml = scenes.map((s, i) => {
    const last = i === scenes.length - 1;
    const parts = [];
    if (i === 0 && meta.hook && !hookIsLine) parts.push(`    <div class="cap hook"><span>${lit(meta.hook)}</span></div>`);
    if (last && meta.cta) parts.push(`    <div class="end"><div class="cap hl pop" style="--in:${s.start}s" data-sfx="chime"><span>${esc(plainText(meta.cta))}</span></div></div>`);
    // bold: a short line shows whole; a long one a few words at a time, so it doesn't bury the picture.
    // The first line is always whole: it's the cover.
    const whole = i === 0 || s.text.split(/\s+/).length <= BOLD_WHOLE;
    const cls = bold ? `say auto${whole ? ' line' : ''}${i === 0 ? ' now' : ''}` : 'say auto';
    const kw = s.kw.length ? ` data-kw="${esc([...new Set(s.kw)].join(','))}"` : '';
    parts.push(`    <div class="${cls}" data-voice="${esc(s.clip)}" style="--voice:${s.start}s"${kw}>${esc(s.text)}</div>`);
    return `  <!-- line ${s.n}, ${s.start}–${s.end}s -->\n  <div class="scene narr center"${last ? '' : ` style="--out:${r2(s.end - 0.15)}s"`}>\n${parts.join('\n')}\n  </div>`;
  }).join('\n\n');
  // what's behind the text: a drawn style's canvas and one shot per line, or a photo slot per line
  const layers = style.shots
    ? [`  ${style.canvas}`, '  <div class="art-scrim" data-lint="off"></div>', '',
      ...scenes.map((s, i) => {
        const settings = Object.entries(s.shot.attrs).map(([k, v]) => ` data-${k}="${esc(v)}"`).join('');
        const cue = style.sfx[`${s.shot.name}:${s.shot.attrs.do || ''}`] || style.sfx[s.shot.name];
        const sfx = cue ? ` data-sfx="${cue}"` : '';
        return `  <div class="shot" data-shot="${s.shot.name}" style="--in:${i === 0 ? 0 : s.start}s"${settings}${sfx}></div>`;
      })].join('\n')
    : ['  <div class="glow g1"></div>', '  <div class="glow g2"></div>',
      ...scenes.map((s, i) => bgSlot(i, i === 0 ? 0 : scenes[i - 1].end, s.end, i === scenes.length - 1, s.media,
        s.screen && s.media && !VIDEO_EXT.test(s.media) ? { screen: s.screen, at: s.at } : null))].join('\n');
  const corners = [['brand', meta.brand], ['series', meta.series]].filter(([, v]) => v)
    .map(([k, v]) => `  <div class="corner ${k}" style="--out:${duration}s">${esc(v)}</div>`).join('\n');
  const inserts = !style.shots && scenes.some((s) => s.screen && s.media) ? INSERT_JS : '';
  const doc = `<!doctype html>
<!--
  Narrated video, written by scripts/video/compose.js from ${path.relative(dir, path.resolve(scriptFile))}.
  Edit the script and run compose.js again rather than editing the timing here; it's
  measured from the voice. Page conventions: see the comment at the top of
  templates/promo.html, and templates/${style.template} for this layout${style.shots ? ' and its shots' : ''}.
-->
${head}
<body ${attrs}>
${layers}
${corners}

${sceneHtml}
${inserts}</body>
</html>
`;
  // the brand's colors, font, and end card, from the Visual Identity
  const look = visualIdentity();
  const branded = look ? applyIdentity(doc, look, { pageDir: dir }) : { html: doc, changes: [], problems: [] };
  fs.writeFileSync(page, branded.html);

  console.log(`Wrote ${page}: ${scenes.length} lines, ${duration}s`);
  for (const s of scenes) console.log(`  ${String(s.n).padStart(2)}. ${s.start.toFixed(2)}–${s.end.toFixed(2)}s  ${s.clip}${s.media ? `  bg ${s.media}` : ''}${s.shot && style.shots ? `  shot ${s.shot.name}` : ''}  ${s.text.slice(0, 48)}${s.text.length > 48 ? '...' : ''}`);
  if (style.shots) console.log(`  style: ${styleName} (templates/${style.template})`);
  console.log(`  sound: ${musicSrc ? `licensed track ${musicSrc}${track ? `, ${track.bpm} BPM, started at ${track.musicStart}s so its lift lands as the hook ends, cuts on its beat` : ''}` : `${sound.music}${sound.music !== 'none' ? `, ${sound.bpm} BPM, ${sound.key} ${sound.mode || ''}, energy ${sound.energy}, cuts on the beat` : ''}`}${musicSrc ? '' : identity ? ' (the Sonic Identity)' : ' (the template default; no Sonic Identity saved yet)'}`);
  console.log(`  look: ${branded.changes.length ? branded.changes.join('; ') : 'the template default; no Visual Identity saved yet'}`);
  for (const p of branded.problems) console.warn(`Note: ${p}`);
  if (!meta.hook && !bold) console.warn('Note: no hook in the frontmatter, so the first frame has no text. Add "hook: ..." to stop the scroll.');
  for (const n of trackNotes) console.warn(`Note: ${musicSrc}: ${n}`);
  if (track && track.musicStart + duration > track.duration) console.warn(`Note: ${musicSrc} runs out ${r2(track.musicStart + duration - track.duration)}s before the video ends; shorten the script or pick a longer track.`);
  if (musicSrc && !track) console.warn(`Note: set data-music-start from beats.js (node beats.js ${musicSrc} --align ${drop} --duration ${duration}).`);
  const credited = musicSrc && fs.existsSync(path.join(assets, 'CREDITS.md')) && fs.readFileSync(path.join(assets, 'CREDITS.md'), 'utf8').includes(path.basename(musicSrc));
  if (musicSrc && !credited) console.warn(`Note: record the track's license with media.js credit (node media.js credit ${musicSrc} --source ... --license ...), and put any required credit in the post.`);
  if (!args.noCheck) {
    const check = run('render.js', [page, '--check'], { stdio: 'inherit' });
    if (check.status !== 0) console.warn('Fix what --check lists (usually by shortening a line or the hook), then compose again.');
  }
  const show = (f) => (path.relative(process.cwd(), f).startsWith('..') ? f : path.relative(process.cwd(), f));
  console.log(`Next: node ${show(path.join(__dirname, 'render.js'))} ${show(page)} --slides, then render it to an .mp4.`);
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { parseFrontmatter, sonicIdentity };
