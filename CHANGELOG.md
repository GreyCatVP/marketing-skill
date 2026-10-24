# Changelog

What changed in each version of the plugin (`.claude-plugin/plugin.json`).
Skills that read "our changelog" for source material read this file too.

## 0.8.0 (unreleased)

- **A 3D mascot that moves, for videos with no footage.** `style: 3d` now
  stars the brand's mascot, a robot in the Visual Identity's colors, built
  and rigged in `templates/mascot.py`. It blinks, breathes, gestures on
  the words, and lip-syncs to the voice (from the caption timing), with
  an antenna that wobbles after every move. `[shot: mascot do=...]` picks
  the action: `wave`, `talk`, `point`, `present`, `cheer` (a jump and
  confetti), `think`, `shrug`, `sad` (under a rain cloud), `walk`,
  `dance` (on the music's beat), `thumbs`, or `wow`. `prop=phone`,
  `laptop`, or `sign` puts the user's screenshot or words in its hands,
  and `prop=screen` floats the screenshot beside it to point at. It
  stands in a light seamless studio with soft shadows, or `set=night`
  under a spotlight. With no shots named, the mascot waves, talks, points,
  and cheers through the script.
- Two cinematic 3D shots: `desk`, the mascot typing at a monitor showing
  the user's screen in a cozy room at night, spinning round to wave
  before the camera flies into the screen; and `title`, big 3D letters
  dropping onto the studio floor while the mascot cheers.
- **The bold look, for a cover that stops the scroll.** `captions: bold`
  in a script shows each line's whole caption at once in heavy capitals
  boxed in black, each word popping as it's said, with `*keywords*` in
  yellow and the first line on screen from frame 0. `series: week 2` and
  `brand:` put a tag in each top corner. Photos keep their light under
  it. `cut.js --bold` gives a filmed take the same look.
- A screen in the user's own photo: `[bg: assets/me.jpg
  screen=assets/app.png at=...]` puts their screenshot on the laptop or
  phone they're holding, from the screen's four corners, moving with the
  photo's zoom.
- **Your own character in the mascot's place**: `character:
  assets/hero.glb` in a script (or `Character:` in the Visual Identity, or
  `character=` on one shot) puts the user's own rigged 3D character in
  every shot the robot appears in, from `templates/character.py`. It
  loads any rigged glTF (`.glb`, or a VRoid `.vrm`; Draco and meshopt
  compression work), matches its bones by name (Mixamo, Blender `.L`/`.R`,
  VRoid, Ready Player Me), and stands it at the robot's height, facing the
  camera. Its own clips play when their names match an action (`Wave`,
  `Walking`, `Dance`, `ThumbsUp`, `Jump`, `Idle`); otherwise two-bone IK
  poses its arms and legs from the robot's poses, at its own proportions.
  Props come down below its chin with its hands on them, and it lip-syncs
  through its blend shapes (`jawOpen`, `viseme_aa`, `A`), its jaw bone, or
  a nod on the words. A model without a skeleton moves as a whole.
- **The product demo, a launch video's look**: five screen shots for
  showing a product working instead of a presenter, in `templates/demo.py`.
  `terminal` types the product's real commands and prints their output,
  `agent` plays an AI agent's session (the request typed, its tool calls
  streaming in, the document it wrote sliding in beside it), `wall` floats
  the real things it made past the camera, `player` plays the user's video
  in a window, and `comments` ends on a handwritten question over a
  comment box. The camera moves over each screen and pushes through into
  the next instead of cutting, and a `desk` right before one shows it live
  on the monitor and pushes in until the screen is the frame.
  `captions: subtitle` keeps the words small, white, and a phrase at a
  time. Screens render several frames a second. The plugin's own
  launch-video cut is in `media/explainer/v4/`.
- **Landscape videos**: `format: landscape` in a script (or `compose.js
  --format landscape`) renders the same video 1920x1080 for YouTube,
  Reddit, and LinkedIn. `render.js` reads the frame size from the page
  (`<body data-size="1920x1080">`), the captions sit low and centered,
  and the 3D shots open out to the wider frame.
- **Places for the mascot**: a living room by day, a launch stage with an
  LED wall and light beams, a city rooftop at dusk, and a park, each in
  the brand's colors. Shots take them in turn (`set=` names one), so a
  video moves through places instead of standing on one plain backdrop,
  and `bg=assets/photo.jpg` stands the mascot in front of the user's own
  photo, softly blurred.
- Three more 3D shots, after the big launch videos: `icons` (app tiles
  of features or skills dropping into a grid, the mascot waving in the
  last cell), `notes` (handwritten sticky notes floating in the dark),
  and `button` (a cursor clicking the call to action, "☆ Star" to
  "★ Starred", under confetti).
- `compose.js` cuts on a licensed track's beat: with `music:
  assets/track.mp3`, it starts the track so its biggest lift lands as the
  hook ends, moves every scene change onto a beat, and sets the page's
  tempo to the track's (when `beats.js` is confident in the beat). In the
  bold look, lines over 8 words show a few words at a time.
- The plugin's v3 explainer (`media/explainer/v3/`): a narrated tour of
  all fourteen skills and the new video features, made with `compose.js`
  from one script.
- The 3D studio's light is baked into the set, so a mascot frame renders
  in about half the time it would with the floor lit live.

- **Montages from your own videos: `clip-montage`, a fourteenth skill, and
  the default for montages.** Send the phone clips you or a client filmed
  (a home, a product, a shop, an event), plus your own music or voiceover
  if you have them, and get a finished vertical montage, free: it renders
  locally, with no credits, and nothing is generated. The skill:
  - looks at every clip frame by frame and picks each one's best moment
    (`[from:]` to `[to:]`), two or three from a long clip;
  - cuts on the beat of your own track (or the client's generated sound,
    or none, for a trending sound added in the app);
  - keeps a clip's own sound where someone talks, with the music ducked
    under it and the exact words captioned;
  - lays your voiceover under the whole video with synced captions;
  - with only photos, asks for clips first and hands over to
    `montage-video`.
  `montage-video` now offers AI camera moves only when the user says they
  have a paid video-model plan, and quotes each run first. Figma Weave
  runs video models only on paid Figma plans.
- `scripts/video/montage.js` for clips:
  - `[to: 6]` ends a clip's stretch.
  - `[sound]` keeps a clip's own sound in sync, and a `[say: ...]` on it
    captions what's said.
  - `[focus: 30%,50%]` keeps that point in frame when a landscape clip is
    cut to 9:16.
  - `voiceover:`, `voiceover-text:`, and `voiceover-at:` put one recording
    under every shot, with captions, the shots stretching to cover it.
  - `frames <clip> --every 1` lays out a frame every second with its time,
    and prints when the clip's sound is loud.
  - `inspect` strips a clip's metadata (a phone's location) while keeping
    its picture, sound, and rotation, and says whether each clip has sound.
  - A pan on a clip now slides the zoomed clip. Before, it did nothing,
    since a clip is cut to the frame first.
- `scripts/video/render.js` turns only the stretch a clip plays into
  frames (`data-length`), not the whole file, so long phone clips render
  quickly. It crops a clip to 9:16 around `data-focus`.

- **Montages from a client's own photos: `montage-video`, a thirteenth
  skill.** Hand over photos or phone clips of a home, a room, or a
  product, and get a finished vertical reel:
  - each photo moving with purpose (a pan across a wide room, so a 3:2
    photo is seen whole in a 9:16 frame; a push in on a detail; a pull
    out to reveal), each move the other way from the one before;
  - cuts on the music's beat, or timed to a voiceover;
  - a label on every shot, the hook on the first, and a status sticker
    ("just listed", "20% off");
  - the price, specs, and CTA;
  - a "Virtually staged" badge, callouts on a product's details, and
    before/after wipes;
  - the client's logo, contact lines, and fine print on the end card.

  The skill looks at every photo to choose and order the shots, then keeps
  editing the video on request ("faster", "kitchen first", "calmer
  music"), saving each version. `references/montage-guide.md` holds its
  shot order, moves, music by mood, and the wording rules for property
  ads (describe the home, never who should live there).
- `scripts/video/montage.js`:
  - `inspect <folder>` copies the photos in, upright and sized for the
    frame, with their metadata (GPS location included) stripped, and
    converts iPhone HEIC photos where the machine can. It writes a
    numbered contact sheet and a starter script.
  - `montage.js <script.md>` writes the page from a script of one shot
    per photo. It reads a licensed track's beats with `beats.js` and cuts
    on its bars. It holds a shot longer when its text needs the time to
    be read.
  - The new `montage.html` template shows photos bright, without the
    darkening behind text. It adds `panX`, `shiftX`, `shiftY`, `pushIn`,
    `pullOut`, and `drift` moves, `contain` and `card` fits, and cut,
    slide, zoom, wipe, and flash transitions.
- **3D camera moves in montages.** `scripts/video/depth.js` estimates each
  photo's depth with Depth Anything V2 Small (Apache-2.0, runs locally;
  `npm install @huggingface/transformers` once). The montage page draws
  the photo from it with WebGL, using parallax occlusion mapping so near
  things cover what's behind them. That gives `orbit` (the camera circles
  the focus while traveling across a wide room), `dolly-in` / `dolly-out`
  (near things grow faster than the far wall), and `rise`. They're the
  default moves when a depth map is available, made as needed and kept
  next to each photo, with `amount=` for strength, `[depth: file]` for a
  depth map from elsewhere, and `depth: off` for flat moves. Without the
  model, every shot moves flat, as before.
- **AI camera moves in montages.** With a connected video model (Figma
  Weave's Seedance or Veo, or Higgsfield), `montage-video` turns each photo
  into a short clip where the camera really moves (an orbit, a dolly in, a
  glide through a doorway) and edits the clips on the beat, two angles per
  clip where it can. The skill:
  - quotes every run and asks before spending credits;
  - checks each clip against its photo with the new `montage.js frames`
    (the photo beside the clip's first, middle, and last frames), and drops
    any clip that changed the room;
  - labels AI shots with an `[ai]` "AI-animated" badge.

  `references/montage-guide.md` has a prompt library for the moves and
  notes on the models.
- **Client profiles** in `state/clients/<slug>.md` (format in its
  README). Each holds a client's colors, font, logo, sound, contact
  details, and the preferences they've asked for. They're kept out of
  git. A client's video never falls back to your own brand.
- `brand.js` end cards take contact lines, fine print, and a length.
  `compose.js`'s `sonicIdentity()` reads a client's profile. `beats.js`
  exports its track alignment (`alignTrack`). A frontmatter value can hold
  a `#` ("lot #12"), since a comment now starts at ` # `.
- The renderer warns that a background will look soft when the frame
  enlarges it more than 1.25x, filling the frame or shown whole, rather
  than whenever it's under 1080x1920. Blurred backdrops are skipped.

- **3D and pixel-art animation, with voice.** Two templates that draw their
  own frames: `3d.html` (three.js, lit in the brand's colors: floating
  shapes, a phone with your screenshot, feature cards, a bar chart, a coin
  with your logo, a ring tunnel, a globe) and `pixel.html` (an original
  robot hero walking, fighting a boss, opening a chest of coins, leveling
  up, in a 16-color palette, with captions in a game dialog box). Each is
  narrated with word-by-word captions synced to the voice. `compose.js`
  makes either from a script with `style: 3d` or `style: pixel`, one shot
  per line (`[shot: hero src=assets/screen.png]` picks one).
- The renderer seeks pages that draw with WebGL or a canvas frame by frame
  (`window.renderFrame(t)`), serves three.js from `scripts/video/node_modules`
  (now a dependency) so renders work offline, and reports page script
  errors. A shot change counts as a change on screen in the pacing check.
- **Chiptune**, a twelfth genre: a pulse-wave lead, an arpeggio for chords,
  a triangle bass, and noise-channel drums. And five 8-bit sound effects:
  `coin`, `jump`, `powerup`, `blip`, `hurt`.
- `gallery.js` builds a strip of the drawn templates' shots, and can build
  just the strips you name.
- **Narrated videos with synced captions.** `scripts/video/compose.js`
  turns a script of numbered lines into a finished page: a voiceover
  (Kokoro or your own takes), a background per line, scenes timed to the
  voice with cuts on the beat, the hook on screen from the first frame, and
  word-by-word captions synced to the voice. New `narrated.html` template.
- `scripts/video/captions.js`: when each word of a voice line is said,
  from the clip's pauses and the words' lengths (no service; about 50 ms
  from the true word starts on average against synthesized speech), with
  Whisper as an option. `<div class="say auto" data-voice>` gets captions
  in any template, and renders with captions write an `.srt`.
- The renderer prepares voice clips before capturing frames: silence is
  trimmed from both ends, `--voice-lengths` lists each line's start, length,
  and room in its scene, and a line running past its scene is reported.
- `voice.js` writes each line's sentence timings next to its WAV.
- **The hook is on screen from the first frame** in every template (a new
  `now` class), since that frame is the default cover and the swipe
  decision. `--check` and `check.js` now fail a page with a blank first
  frame or first second, or with text that leaves before it can be read,
  and note stretches over 3 seconds where nothing changes.
- **Visual Identity**: colors, a display font, a logo, and a handle saved in
  `brand-voice.md` (asked for in setup), applied by `scripts/video/brand.js`
  (and by `compose.js`), with an end card after the last scene that lands
  with the sonic logo, and contrast warnings.
- **Hook variants**: `data-variant` on a page, and `render.js --variants
  a,b,c` renders one video per hook; `--check` and `check.js` check each.
  `references/hooks.md` has hook patterns by goal.
- **Covers**: `render.js --cover <t>` writes the cover frame and checks it
  against the 3:4 profile-grid crop; `publish_direct.py --cover-ms` sets it
  on TikTok and Instagram, and `--cover-url` gives Instagram a cover image.
- **Your own footage.** `scripts/video/cut.js` turns a talking-head take
  filmed on a phone into a finished video: it cuts out the pauses, times
  captions to the cut, and writes a page with the clip full-frame and its
  own sound, the hook, the music, and the end card. In any page,
  `<video data-audio>` plays a clip's own sound in sync with it, and
  `.say auto[data-clip]` captions it. Screen recordings in the how-to phone
  frame are cut to the screen's shape instead of being cropped to 9:16
  first.
- **Faster renders**: frames render in parallel across browsers (the
  explainer's approach, now shared), with faster screenshots; a 12-second
  template went from 76s to 25s on a 4-core machine. `--draft` makes a
  half-size 15fps check in seconds, and `--batch` renders a week of pages,
  every variant included.
- **Licensed music**: `media.js search --type music` finds Creative
  Commons tracks on Openverse that allow commercial use, records their
  credits, and reports each one's tempo and beat confidence.
- **Learning what works**: `state/video-log.md` records every posted
  video, and `publish_direct.py --metrics` reads its numbers from YouTube,
  Instagram, or TikTok. With about ten posts logged, `short-form-video`
  and `content-calendar` steer formats, hooks, and posting times by the
  account's own results.
- **A shorter README** that leads with a gallery of the templates
  (`docs/gallery/`, rebuilt by `scripts/video/gallery.js`) and a summary
  of making videos, with the long platform and tool sections moved,
  word for word, to `docs/video.md`, `docs/publishing.md`,
  `docs/community-posting.md`, and `docs/outreach.md`. CI now checks
  every link and anchor in the README, docs, and references.
- `short-form-video`'s local-render steps moved to
  `references/video-rendering.md`, and its worked example to
  `references/short-form-video-example.md`, so script-only runs load less.
  `community-post-generator`'s per-platform research moved to
  `references/community-research.md` and its examples to
  `references/community-post-examples.md`.
- `/marketing-skill:marketing-setup` is under 4 KB again, so Codex turns
  it into a skill.
- CI: repo checks (skill frontmatter, command size, paths the skills point
  at), dry-run smoke tests for both publish scripts, templates in sync
  with `build.py`, and `check.js` over every template.

## 0.7.0 (2026-10-03)

- 22 everyday FYP templates (POV, tier list, text-message skit, storytime,
  and more), meme sound effects, and `check.js`, the QA pass.
- Codex support.
- Voiceover support in the renderer, free local voices with Kokoro
  (`voice.js`), and beat analysis for licensed tracks (`beats.js`).
- A 16:9 explainer video of the plugin (`media/explainer/`).

## 0.6.0 (2026-10-02)

- Real backgrounds (stock photos and clips via `media.js`, or AI images)
  and a per-project sonic identity for rendered videos.

## 0.5.0 (2026-10-02)

- A local video renderer with an original soundtrack (`scripts/video/`).

## 0.4.1 (2026-10-02)

- Better discoverability in skill search and plugin directories.

## 0.4.0 (2026-09-26)

- `short-form-video` for YouTube Shorts, Instagram Reels, and TikTok.

## 0.3.0 (2026-09-26)

- `email-outreach`: personalized daily cold outreach with prospect
  research and deduplication.

## 0.2.0 (2026-09-25)

- Content calendar, three more content skills, and the approval-gated
  publish step.
- `community-post-generator` for Reddit, Product Hunt, Hacker News, Indie
  Hackers, Discord, Slack, Telegram, and dev.to.

## 0.1.0 (2026-09-25)

- The first five marketing skills as a Claude Code plugin.
