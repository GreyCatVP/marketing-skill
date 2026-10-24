# Explainer v4: the launch-video cut

The plugin's explainer again, about a minute long at 1920x1080 (16:9),
edited the way product launch videos are: the product's own screens
instead of a presenter. It opens on an empty desk at night, drifts in,
and pushes into the monitor until the terminal on it is the frame; the
real install commands type out with their real output; Claude Code runs
the skills; the templates' real frames float past; and the camera moves
from one screen to the next instead of cutting, under small subtitles.
The mascot gets one line, and the 3D letters, the icons, the notes, and
the star button break up the screens. It ends on "this video? It made
this too", with its own opening playing in a player window.

- `script.md`: 16 lines, one shot each, in `style: 3d` with
  `captions: subtitle`. The terminal lines are what `claude plugin
  marketplace add` and `claude plugin install` print; the agent steps
  are the tools each skill uses, and its documents are each skill's real
  output headings. The competitor is the made-up Acme.
- `explainer-landscape.html`: the page `compose.js` wrote from it. Don't
  edit its timing by hand; edit the script and compose again.
- `marketing-skill-v4-landscape.mp4`: the cut, a lighter encode for the
  repo, with its captions in the `.srt` beside it. `poster-landscape.jpg`
  is what the main README shows.
- `assets/t-*.jpg`: real frames of the templates (cut from
  `docs/gallery/`), for the wall of templates.

## Credits

Put these in the post or description:

```
Music from #Uppbeat (free for Creators!): https://uppbeat.io/music/tracks/21-on-the-block/funky-diesel License code: WKCBH1LMDV3AQDIE
Voiceover: AI voice (Kokoro, af_heart), generated locally
```

The track, the voice files, and `assets/opening.mp4` aren't in the repo
(all git-ignored): the track's license doesn't allow redistributing the
file, and the voice and the opening are regenerated from the script.

## Making it again

From this folder, with the track at `assets/funky-diesel.mp3` and the
voice lines at `assets/v4-1.wav` ... `v4-16.wav` (Kokoro's `af_heart`,
one per line; delete the `recordings:` line to have `voice.js` voice
them instead):

```
node ../../../scripts/video/compose.js script.md --out explainer-landscape.html
node ../../../scripts/video/render.js explainer-landscape.html assets/opening.mp4 --duration 7
node ../../../scripts/video/render.js explainer-landscape.html marketing-skill-v4-landscape.mp4 --cover 0
```

The second command renders the video's own first seven seconds, which the
player on line 14 plays. The render takes about ten minutes on a 4-core
machine without a graphics card; the screens render several times faster
than the 3D shots.
