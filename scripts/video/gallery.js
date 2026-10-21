#!/usr/bin/env node
'use strict';
/*
 * Builds the template gallery shown in the README: one strip per group of templates, each tile
 * a template's middle scene (or the moment PICK names), settled, with its name under it. Run it
 * after changing templates.
 *
 * Usage: node gallery.js [group ...] [--out ../../docs/gallery]   (every group, or just those named)
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const r = require('./render');

const GROUPS = {
  marketing: ['promo', 'how-to', 'narrated', 'testimonial', 'faq', 'announcement', 'team'],
  'meme-captions': ['pov', 'nobody-me', 'expectation-reality', 'tell-me-without', 'makes-sense', 'starter-pack'],
  'comment-bait': ['tier-list', 'this-or-that', 'hot-take', 'flags', 'quiz', 'rating'],
  'skits-and-stories': ['text-chat', 'notifications', 'post-card', 'storytime', 'countdown', 'reveal', 'before-after'],
  // the drawn templates, a few shots each: "template@seconds"
  animation: ['3d@1.2', '3d@4.6', '3d@8.5', '3d@12.3', '3d@15.6', 'pixel@1.2', 'pixel@3.6', 'pixel@7.7', 'pixel@10.6', 'pixel@13.5'],
};
const TILE = { w: 270, h: 480 };
// where a template's middle scene isn't its best face: a time in seconds, or a scene number (0-based)
const PICK = { narrated: { t: 1.2 }, testimonial: { slide: 3 }, team: { slide: 4 } };

async function main() {
  const argv = process.argv.slice(2);
  const at = argv.indexOf('--out');
  const out = path.resolve(at >= 0 ? argv[at + 1] : path.join(__dirname, '..', '..', 'docs', 'gallery'));
  const only = argv.filter((a, i) => !a.startsWith('--') && argv[i - 1] !== '--out');
  for (const g of only) if (!GROUPS[g]) throw new Error(`no group "${g}" (groups: ${Object.keys(GROUPS).join(', ')})`);
  fs.mkdirSync(out, { recursive: true });
  const { chromium } = r.loadPlaywright();
  const browser = await r.launchBrowser(chromium);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gallery-'));
  for (const [group, names] of Object.entries(GROUPS).filter(([g]) => !only.length || only.includes(g))) {
    const tiles = [];
    for (const entry of names) {
      const [name, when] = entry.split('@');
      const { page, settings } = await r.preparePage(browser, path.join(__dirname, 'templates', `${name}.html`), {});
      const times = await r.slideTimes(page, settings.duration);
      const pick = when ? { t: Number(when) } : PICK[name] || {};
      await r.seek(page, pick.t ?? times[pick.slide ?? Math.floor((times.length - 1) / 2)]);
      const file = path.join(tmp, `${tiles.length}.png`);
      await page.screenshot({ path: file });
      // a drawn template's tiles are labeled with the shot on screen
      const shot = when ? await page.evaluate(() => document.querySelectorAll('.shot')[Number(document.body.dataset.shot)]?.dataset.shot) : null;
      await page.close();
      tiles.push({ name: shot ? `${name} · ${shot}` : name, file });
    }
    // each tile scaled down with its name in a band underneath, then side by side
    const inputs = tiles.flatMap((t) => ['-i', t.file]);
    const labeled = tiles.map((t, i) => `[${i}:v]scale=${TILE.w}:${TILE.h},pad=${TILE.w}:${TILE.h + 44}:0:0:color=0x16161c,`
      + `drawtext=text='${t.name}':x=(w-text_w)/2:y=${TILE.h + 11}:fontsize=22:fontcolor=0xd8d7de[t${i}]`).join(';');
    const filter = `${labeled};${tiles.map((_, i) => `[t${i}]`).join('')}hstack=inputs=${tiles.length}`;
    const file = path.join(out, `${group}.jpg`);
    const run = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', filter, '-frames:v', '1', '-q:v', '4', file], { encoding: 'utf8' });
    if (run.status !== 0) throw new Error(run.stderr);
    console.log(`${file} (${tiles.length} templates)`);
  }
  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
