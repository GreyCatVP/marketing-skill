# Explainer v3

A 1080x1920 (9:16) explainer of the plugin for r/claudeskills, about 80
seconds: all fourteen skills, then the new video features. It's made the
way the plugin makes any narrated video, from one script:

- `script.md`: 22 lines, one shot each, in `style: 3d` with the bold
  captions. The mascot presents; the `desk`, `icons`, `notes`, `title`,
  and `button` shots are the launch-video moves it borrows.
- `explainer.html`: the page `compose.js` wrote from it. Don't edit its
  timing by hand; edit the script and compose again.
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

From this folder, with the track at `assets/funky-diesel.mp3`:

```
node ../../../scripts/video/compose.js script.md --out explainer.html
node ../../../scripts/video/render.js explainer.html marketing-skill-v3.mp4 --cover 0
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
