#!/usr/bin/env node
'use strict';
/*
 * Depth maps for the montage's 3D photo moves: for each photo, how near or far each point of it
 * is, estimated by Depth Anything V2 Small (Apache-2.0), an open model that runs on this machine.
 * No account, no key, no per-use cost. Writes <photo>.depth.png next to each photo, white near
 * and black far; montage.js makes them on its own for the shots that move in 3D, and the page
 * moves the near parts of the photo more than the far ones, so the camera seems to move.
 *
 * Usage:
 *   node depth.js <photo> [<photo> ...] [--force]   # skips photos whose depth map is up to date
 *   node depth.js --check                           # whether it's set up
 *
 * One-time setup, from this folder: `npm install @huggingface/transformers` (already there if
 * kokoro-js is installed for voice.js). If that stops on a download it doesn't need (a GPU build
 * of ONNX Runtime), add --ignore-scripts. The first run downloads the model (about 100 MB) from
 * Hugging Face and caches it; after that it works offline.
 *
 * A depth map from anywhere else works too (a phone's portrait depth, another app): save it as a
 * grayscale image, white near, with the photo's shape, and name it in the montage script with
 * [depth: assets/file.png].
 */
const fs = require('fs');
const path = require('path');

const MODEL = 'onnx-community/depth-anything-v2-small';
const SETUP = 'From scripts/video, run once: npm install @huggingface/transformers\n(add --ignore-scripts if it stops on a download it doesn\'t need)';

function fail(message) {
  console.error(message);
  process.exit(2);
}

// photo.jpg -> photo.depth.png
const depthPath = (file) => file.replace(/\.[^./\\]+$/, '') + '.depth.png';

// a depth map newer than its photo
function fresh(file) {
  const out = depthPath(file);
  return fs.existsSync(out) && fs.statSync(out).mtimeMs >= fs.statSync(file).mtimeMs;
}

// whether the depth model's library is installed here
function available() {
  try {
    return fs.existsSync(path.join(path.dirname(require.resolve('@huggingface/transformers')), '..', 'package.json'));
  } catch {
    return false;
  }
}

async function main() {
  const argv = process.argv.slice(2);
  const files = argv.filter((a) => !a.startsWith('--'));
  if (argv.includes('-h') || argv.includes('--help') || (!files.length && !argv.includes('--check'))) {
    console.log(fs.readFileSync(__filename, 'utf8').split('*/')[0].replace(/^[\s\S]*?\/\*/, '').replace(/^ \* ?/gm, ''));
    process.exit(argv.includes('-h') || argv.includes('--help') ? 0 : 2);
  }
  if (argv.includes('--check')) {
    console.log(available() ? `Ready: ${MODEL} (downloaded on first use, then cached)` : `Not set up. ${SETUP}`);
    process.exit(available() ? 0 : 1);
  }
  for (const f of files) if (!fs.existsSync(f)) fail(`No photo at ${f}`);
  const todo = argv.includes('--force') ? files : files.filter((f) => !fresh(f));
  for (const f of files.filter((x) => !todo.includes(x))) console.log(`${depthPath(f)} (up to date)`);
  if (!todo.length) return;
  if (!available()) fail(`3D moves need a depth model. ${SETUP}`);
  const { pipeline, RawImage } = await import('@huggingface/transformers');
  let estimate;
  try {
    estimate = await pipeline('depth-estimation', MODEL);
  } catch (e) {
    fail(`Couldn't load the depth model (${MODEL}): ${String(e.message || e).split('\n')[0]}\nThe first run downloads it from huggingface.co (about 100 MB); check the connection, then try again.`);
  }
  for (const f of todo) {
    const started = Date.now();
    const { depth } = await estimate(await RawImage.read(f));
    await depth.save(depthPath(f));
    console.log(`${depthPath(f)} (${((Date.now() - started) / 1000).toFixed(1)}s)`);
  }
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { depthPath, fresh, available };
