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
 * The shots and their settings are listed at the top of each template.
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

const ROOT = path.resolve(__dirname, '..', '..');
const LEAD = 0.15; // the first line starts almost at once; the hook is already on screen
const GAP = 0.35; // a beat between one line ending and the next scene
const TAIL = 1.2; // after the last line, room for the sonic logo
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
    shots: ['shapes', 'hero', 'cards', 'chart', 'coin', 'rings', 'globe'],
    first: 'shapes', last: 'coin', cycle: ['globe', 'rings', 'cards', 'shapes'],
    sfx: { cards: 'swish:card-1', coin: 'ding:land' },
  },
  pixel: {
    template: 'pixel.html', canvas: '<canvas class="art" width="135" height="240" data-lint="off"></canvas>',
    shots: ['walk', 'boss', 'coins', 'levelup', 'city', 'space', 'photo'],
    first: 'walk', last: 'space', cycle: ['boss', 'coins', 'levelup', 'city'],
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
    const kv = /^\s*([\w-]+)\s*:\s*(.*?)\s*(?:#.*)?$/.exec(line);
    if (kv) meta[kv[1].toLowerCase()] = kv[2].replace(/^["']|["']$/g, '');
  }
  return { meta, body: text.slice(m[0].length) };
}

const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'narrated';
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const r2 = (t) => Math.round(t * 100) / 100;

// The Sonic Identity from brand-voice.md, or null while it's still the placeholder.
function sonicIdentity() {
  const file = path.join(ROOT, 'references', 'brand-voice.md');
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

function bgSlot(i, a, b, last, media) {
  const start = i === 0 ? 0 : r2(a - 0.25);
  const end = last ? null : r2(b - 0.2);
  const dur = r2((last ? b : b + 0.45) - start);
  const style = `--in:${start}s; ${end !== null ? `--out:${end}s; ` : ''}--dur:${dur}s`;
  const inner = !media ? ''
    : VIDEO_EXT.test(media) ? `<video class="bg-media" src="${esc(media)}"></video>`
      : `<img class="bg-media" src="${esc(media)}" alt="">`;
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
    const bg = /\[bg:\s*([^\]]+)\]/i.exec(text);
    const shot = /\[shot:\s*([^\]]+)\]/i.exec(text);
    return {
      n, text: text.replace(/\s*\[(bg|shot):[^\]]*\]/gi, '').trim(),
      bg: bg ? bg[1].trim() : meta.bg || '', shot: shot ? parseShot(shot[1]) : null,
    };
  }).filter((l) => l.text);
  if (!lines.length) fail(`No lines in ${scriptFile}; number them "1. ...", one per scene.`);
  if (style.shots) {
    if (lines.some((l) => l.bg)) console.warn(`Note: [bg: ...] and bg: are for photo backgrounds; style ${styleName} draws each line's background, so they're ignored (use [shot: ...]).`);
    const bad = lines.filter((l) => l.shot && !style.shots.includes(l.shot.name));
    if (bad.length) fail(`Unknown shot${bad.length > 1 ? 's' : ''} for style ${styleName}: ${bad.map((l) => `"${l.shot.name}" (line ${l.n})`).join(', ')}. The shots are ${style.shots.join(', ')}.`);
    let k = 0;
    lines.forEach((l, i) => {
      if (l.shot) return;
      const name = i === 0 ? style.first : i === lines.length - 1 && lines.length > 1 ? style.last : style.cycle[k++ % style.cycle.length];
      l.shot = { name, attrs: {} };
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

  const scenes = [];
  let t = LEAD;
  let drop = 0;
  lines.forEach((l, i) => {
    const { length } = prepareVoice(path.join(dir, clips[i]));
    const start = t;
    let end = start + length + GAP;
    if (i === 0) drop = r2(end);
    else if (snap) end = drop + Math.ceil((end - drop) / beat - 1e-6) * beat;
    scenes.push({ ...l, clip: clips[i], start: r2(start), length, end: r2(end) });
    t = end;
  });
  const duration = r2(scenes[scenes.length - 1].start + scenes[scenes.length - 1].length + TAIL);
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
    `class="${bodyClass}"`, `data-duration="${duration}"`, `data-drop="${drop}"`,
    ...(musicSrc ? [`data-music-src="${esc(musicSrc)}"`, 'data-music="none"'] : [`data-music="${sound.music}"`]),
    ...['bpm', 'key', 'mode', 'energy', 'motif'].filter((k) => sound[k] !== undefined).map((k) => `data-${k}="${esc(String(sound[k]))}"`),
  ].join(' ');
  const sceneHtml = scenes.map((s, i) => {
    const last = i === scenes.length - 1;
    const parts = [];
    if (i === 0 && meta.hook) parts.push(`    <div class="cap hook"><span>${esc(meta.hook)}</span></div>`);
    if (last && meta.cta) parts.push(`    <div class="end"><div class="cap hl pop" style="--in:${s.start}s" data-sfx="chime"><span>${esc(meta.cta)}</span></div></div>`);
    parts.push(`    <div class="say auto" data-voice="${esc(s.clip)}" style="--voice:${s.start}s">${esc(s.text)}</div>`);
    return `  <!-- line ${s.n}, ${s.start}–${s.end}s -->\n  <div class="scene narr center"${last ? '' : ` style="--out:${r2(s.end - 0.15)}s"`}>\n${parts.join('\n')}\n  </div>`;
  }).join('\n\n');
  // what's behind the text: a drawn style's canvas and one shot per line, or a photo slot per line
  const layers = style.shots
    ? [`  ${style.canvas}`, '  <div class="art-scrim" data-lint="off"></div>', '',
      ...scenes.map((s, i) => {
        const settings = Object.entries(s.shot.attrs).map(([k, v]) => ` data-${k}="${esc(v)}"`).join('');
        const sfx = style.sfx[s.shot.name] ? ` data-sfx="${style.sfx[s.shot.name]}"` : '';
        return `  <div class="shot" data-shot="${s.shot.name}" style="--in:${i === 0 ? 0 : s.start}s"${settings}${sfx}></div>`;
      })].join('\n')
    : ['  <div class="glow g1"></div>', '  <div class="glow g2"></div>',
      ...scenes.map((s, i) => bgSlot(i, i === 0 ? 0 : scenes[i - 1].end, s.end, i === scenes.length - 1, s.media))].join('\n');
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

${sceneHtml}
</body>
</html>
`;
  // the brand's colors, font, and end card, from the Visual Identity
  const look = visualIdentity();
  const branded = look ? applyIdentity(doc, look, { pageDir: dir }) : { html: doc, changes: [], problems: [] };
  fs.writeFileSync(page, branded.html);

  console.log(`Wrote ${page}: ${scenes.length} lines, ${duration}s`);
  for (const s of scenes) console.log(`  ${String(s.n).padStart(2)}. ${s.start.toFixed(2)}–${s.end.toFixed(2)}s  ${s.clip}${s.media ? `  bg ${s.media}` : ''}${s.shot && style.shots ? `  shot ${s.shot.name}` : ''}  ${s.text.slice(0, 48)}${s.text.length > 48 ? '...' : ''}`);
  if (style.shots) console.log(`  style: ${styleName} (templates/${style.template})`);
  console.log(`  sound: ${musicSrc ? `licensed track ${musicSrc}` : `${sound.music}${sound.music !== 'none' ? `, ${sound.bpm} BPM, ${sound.key} ${sound.mode || ''}, energy ${sound.energy}, cuts on the beat` : ''}`}${identity ? ' (the Sonic Identity)' : ' (the template default; no Sonic Identity saved yet)'}`);
  console.log(`  look: ${branded.changes.length ? branded.changes.join('; ') : 'the template default; no Visual Identity saved yet'}`);
  for (const p of branded.problems) console.warn(`Note: ${p}`);
  if (!meta.hook) console.warn('Note: no hook in the frontmatter, so the first frame has no text. Add "hook: ..." to stop the scroll.');
  if (musicSrc) console.warn(`Note: set data-music-start from beats.js (node beats.js ${musicSrc} --align ${drop} --duration ${duration}) and record the track's license with media.js credit.`);
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
