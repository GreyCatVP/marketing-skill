# Explainer video

A 1920x1080 (16:9), 60fps explainer of this plugin, about 1:40. v3 walks
through all 14 skills in nine voiced lines, the two montage skills new
since v2 (`clip-montage` and `montage-video`) included. Like v2, made after
feedback on r/claudeskills:

- **Music:** a licensed track instead of the generated loop.
- **Voiceover:** one line per scene.
- **Readable on a phone:** nothing on screen under 40px.
- **Real content:** the skill folders, the files every skill reads, frames
  from the plugin's own templates (3D and pixel art included), the format
  of `montage.js`'s output, and the approval checkpoint from `EXAMPLE.md`,
  instead of mock screens.

`explainer.html` is the animated page. `render.js` renders it with
`scripts/video/render.js` (frame-exact seeking, the music and voice mix at
-14 LUFS), at landscape size and in parallel. v1 and v2 are in git history.

## Credits

Put these in the description wherever the video is posted:

```
Music from #Uppbeat (free for Creators!): https://uppbeat.io/music/tracks/21-on-the-block/funky-diesel License code: WKCBH1LMDV3AQDIE
Voiceover: AI voice, Kokoro-82M (open model, Apache-2.0)
```

The track and the voice files aren't in the repo (both are git-ignored):
the track's license doesn't allow redistributing the file, and the voice
files are generated, `assets/voice-1.wav` ... `voice-9.wav`.

## Making it with your voice and music

The lines can be your own recordings, or a free generated voice. v3's
voice is Kokoro-82M's `af_heart` at 1.06x, the same model and voice as the
plugin's `scripts/video/voice.js`. That script downloads the model from
huggingface.co on first use (`npm install kokoro-js` in `scripts/video`
once):

```
node ../../scripts/video/voice.js --audition samples "Last time I shared my marketing plugin for Claude Code, it had twelve skills."
node ../../scripts/video/voice.js voiceover-script.md --out assets --voice af_heart --speed 1.06
```

Where huggingface.co is blocked (some cloud sandboxes), the same model runs
from its GitHub release with the `kokoro-onnx` Python package
(`kokoro-v1.0.onnx` and `voices-v1.0.bin` from
github.com/thewh1teagle/kokoro-onnx/releases), one WAV per line.

1. Record the nine lines in `voiceover-script.md` as `assets/voice-1.m4a`
   ... `assets/voice-9.m4a` (or generate them, above).
2. Measure the lines and paste the printed `LINES` into `explainer.html`:

   ```
   node render.js --voice-lengths assets
   ```

3. In `explainer.html`, set `VOICE = 'assets/voice-{n}.m4a'` (or `.wav`).
   The music is `assets/music/funky-diesel.mp3`, which git ignores because
   its license doesn't allow redistributing the file, so put it there
   before rendering. The page places the track so its ending lands at the
   video's end and moves each scene change onto a beat. For a different
   track, point `TRACK` at it and replace `TRACK_LENGTH`, `TRACK_LIFT`, and
   `TRACK_BEATS` with the output of
   `node ../../scripts/video/beats.js assets/music/<file> --json`.
4. Check and render:

   ```
   node render.js explainer.html --check                 # no visible text under 40px
   node render.js explainer.html --sheet --every 2.5     # contact sheet of the whole timeline
   node render.js explainer.html marketing-skill-explainer.mp4
   ```

Other options: `--stills 12,40` for single frames, and `--from 30 --to 45`
for a silent preview of one stretch. `render.js` finds Playwright in
`scripts/video/node_modules`, or in a global install when `NODE_PATH` points
at it.
