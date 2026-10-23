# Explainer v3

An explainer of the plugin for r/claudeskills, about 80 seconds, in two
cuts: 1920x1080 (16:9) for Reddit and the README, and 1080x1920 (9:16)
for TikTok, Reels, and Shorts. It covers all fourteen skills, then the
new video features, and it's made the way the plugin makes any narrated
video, from one script:

- `script.md`: 22 lines, one shot each, in `style: 3d` with the bold
  captions. The mascot presents; the `desk`, `icons`, `notes`, `title`,
  and `button` shots are the launch-video moves it borrows.
- `explainer.html` and `explainer-landscape.html`: the pages `compose.js`
  wrote from it, vertical and landscape. Don't edit their timing by hand;
  edit the script and compose again.
- `marketing-skill-v3-landscape.mp4` and `marketing-skill-v3.mp4`: the
  two cuts, lighter encodes for the repo (the full-quality renders are
  what get posted), with their captions in the `.srt` files beside them.
  `poster-landscape.jpg` is what the main README shows; `poster.jpg` is
  the vertical cut's.
- `assets/skills.png` (the real `skills/` folder, from
  `skills-screen.html`), `renders.png` and `templates.png` (real frames
  from the template gallery) are what the screens show.

## Credits

Put these in the post or description:

```
Music from #Uppbeat (free for Creators!): https://uppbeat.io/music/tracks/21-on-the-block/funky-diesel License code: WKCBH1LMDV3AQDIE
Voiceover: AI voice (Kokoro, af_heart), generated locally
```

The track and the voice files aren't in the repo (both are git-ignored):
the track's license doesn't allow redistributing the file, and the voice
is regenerated from the script.

## Making it again

From this folder, with the track at `assets/funky-diesel.mp3`, the vertical
cut (TikTok, Reels, Shorts) and the landscape one (Reddit, YouTube, the
README), from the same script and voice:

```
node ../../../scripts/video/compose.js script.md --out explainer.html
node ../../../scripts/video/render.js explainer.html marketing-skill-v3.mp4 --cover 0
node ../../../scripts/video/compose.js script.md --format landscape --out explainer-landscape.html
node ../../../scripts/video/render.js explainer-landscape.html marketing-skill-v3-landscape.mp4 --cover 0
```

The voice lines are `assets/v3-1.wav` ... `v3-22.wav`, Kokoro's
`af_heart` voice, one per line (SEO spoken as "S.E.O.", 3D as "three-D").
To have the plugin voice them instead, delete the `recordings:` line from
the script; `compose.js` then voices it with `scripts/video/voice.js`. For
your own voice, record each line as `assets/v3-<n>.m4a` and point
`recordings:` at them.

`compose.js` reads the track's beat (108 BPM), starts it so its lift lands
as the first line ends, and puts every cut on a beat. The render takes
about 25 minutes on a 4-core machine without a graphics card.
