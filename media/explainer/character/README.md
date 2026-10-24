# Your own character

A 22-second demo of the 3D template with other characters in the robot
mascot's place (`character:` in a script, `templates/character.py`), at
1920x1080 (16:9). Three different rigs, one per kind of model a user
might bring:

- **Michelle** (a Mixamo character with no clips of her own but a dance):
  her skeleton is posed from the robot's poses. She waves, points at the
  product on a floating screen, and cheers.
- **X Bot** (Mixamo's mannequin, with idle and walk clips): it presents
  over its idle clip, and holds a laptop that's come down below its chin,
  hands on it.
- **RobotExpressive** (Blender bone names, its own clips and face
  shapes): it plays its own thumbs-up clip.

The files:

- `script.md`: six lines, a `character=` on each shot to switch between
  them (one `character:` in the frontmatter puts one character in every
  shot).
- `your-own-character.mp4`: the demo, a lighter encode for the repo, with
  its captions in the `.srt` beside it. `poster.jpg` is what the main
  README shows.

## The models

The three characters aren't in the repo (`assets/*.glb` is git-ignored):
they're the sample models in three.js's own examples
(`examples/models/gltf/` in [mrdoob/three.js](https://github.com/mrdoob/three.js)).
RobotExpressive is by Tomás Laulhé (CC0). Michelle and X Bot are Mixamo
characters: Adobe's Mixamo terms allow them in rendered videos like this
one, but not redistributing the model files. For your own videos, use your
own character.

## Credits

```
Music from #Uppbeat (free for Creators!): https://uppbeat.io/music/tracks/21-on-the-block/funky-diesel License code: WKCBH1LMDV3AQDIE
Voiceover: AI voice (Kokoro, af_heart), generated locally
```

## Making it again

From this folder, with `Michelle.glb`, `Xbot.glb`, and
`RobotExpressive.glb` in `assets/`, the track at
`assets/funky-diesel.mp3`, `assets/renders.png` from
`../v3/assets/`, and the voice lines at `assets/c-1.wav` ... `c-6.wav`
(delete the `recordings:` line to have `voice.js` voice them):

```
node ../../../scripts/video/compose.js script.md --out page.html
node ../../../scripts/video/render.js page.html your-own-character.mp4 --cover 0
```
