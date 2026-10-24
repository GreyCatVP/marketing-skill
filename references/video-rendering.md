# Rendering a video locally

How `short-form-video` makes the finished video on the user's machine with
`scripts/video/render.js`. The skill reads this file when the user opts in
to a local render (its steps 3 and 6). `${CLAUDE_PLUGIN_ROOT}` is the
plugin folder, resolved the way the skill describes.

## What it makes

Motion graphics (kinetic text, shapes, UI mockups) over stock photos, stock
video clips, or AI images, or narrated animation drawn in 3D (the brand's
own mascot, a character that moves and lip-syncs) or pixel art (below),
with an original soundtrack in the project's sonic identity and
sound effects synced to what's on screen. It's not filmed footage of the
user's product or people, and the only voiceover is one the user records
or supplies (or a free generated one, below). It suits the types
`video-types.md` marks Render, Narrate, Animate, or Render + your assets,
not anything that needs real people or places on camera. It costs nothing
to run.

Check it's usable with `node --version` (18+), `ffmpeg -version`, and
`node -e "require('playwright')"` run from `scripts/video`. If anything is
missing, give the user the one-time setup from "Rendering a short-form
video locally" in `docs/video.md` rather than installing it unasked.

## A narrated video: compose.js

For a voiceover over backgrounds (an explainer, tips, a text-led brand
story, a storytime), don't hand-edit a template. Write the script as
numbered lines, one per scene, and let `compose.js` build the page:

```
---
title: late invoices
hook: you're losing money on every late invoice
cta: one money habit a week
voice: af_heart
bg: freelancer desk morning
---
1. Most freelancers lose money on invoices they send late. [bg: stressed laptop night]
2. Clients pay fastest when the invoice lands the day the work ends.
3. So send it before you close the laptop, not on Friday.
4. Follow for one money habit a week.
```

Save it as `${CLAUDE_PLUGIN_ROOT}/state/videos/<date>-<slug>.md` and run
`node ${CLAUDE_PLUGIN_ROOT}/scripts/video/compose.js <that file>`. It
voices each line (or uses the user's takes, one file per line, with
`recordings: assets/<slug>-{n}.m4a`; `state/videos/assets/` is shared by
every video, so name takes after the video), fetches a background per `[bg: ...]` (a query, or
a file in `assets/`), times every scene to its line with cuts on the
music's beat, applies the Sonic Identity one energy step lower so it sits
under the voice, puts word-by-word captions synced to the voice under each
line, and runs `--check`. The hook sits on screen from the first frame;
always set one. Keep lines short (one idea, under about 15 words) and the
hook under about 8 words. Then preview and render as below; the render
also writes an `.srt` caption file next to the MP4.

To change a line, edit the script and run `compose.js` again: the timing is
measured from the voice, so don't hand-edit it in the page. Send the user
the voice (`--audio-only`) or a render to check, since you can't hear it.

**Landscape (16:9).** The renders are vertical (9:16) for TikTok, Reels,
and Shorts. For YouTube's main feed, Reddit, LinkedIn, or a website, add
`format: landscape` to the script's frontmatter (or run `compose.js
--format landscape` to make a second cut from the same script): the page
is 1920x1080 with the captions low and centered, and the 3D shots open out
to the wider frame (more of each set, the mascot framed closer). Both cuts
share the voice files, so make the vertical one first, then compose again
with `--format landscape --out <name>-landscape.html`. Pixel art is
vertical only.

## A montage of the user's clips or photos: montage.js

When the user's own clips of a place, a product, or an event are the
video, that's the `clip-montage` skill; with only photos, the
`montage-video` skill. Both follow their own steps with
`scripts/video/montage.js` (`inspect` to bring the clips or photos in,
then a script of one shot per clip moment or photo) and
`templates/montage.html`. Render the page it writes the same way as
below.

## 3D or pixel-art animation: a style

When the user asks for a 3D animation, a mascot or animated character,
pixel art, an 8-bit or retro game look, or "an animated video" with no
footage, write the same numbered
script and add `style: 3d` or `style: pixel` to its frontmatter. Each line
then gets a drawn shot instead of a photo: `compose.js` picks them in turn,
or a line names one, with its settings as key=value pairs:

```
---
title: launch week
style: 3d
hook: we rebuilt invoicing from scratch
cta: try it free · link in bio
---
1. Invoicing used to take a whole afternoon. [shot: mascot do=sad]
2. So we built this, late at night. [shot: desk src=assets/app-screen.png]
3. Here's the new app. [shot: mascot do=point prop=screen src=assets/app-screen.png]
4. Three steps, and it's sent. [shot: title text="Sent"]
5. Try it free this week. [shot: mascot do=cheer]
```

- **3d** (`templates/3d.html`) is led by the brand's mascot: a robot in
  the Visual Identity's colors that moves like a character, not a slide.
  It blinks, breathes, gestures on the words, and its mouth moves with
  the voice (from the caption timing, so it lip-syncs to whatever voice
  the page has). With no shots named, `compose.js` has it wave on the
  first line, talk, point, give a thumbs up, and cheer on the last, with
  a few abstract shots between for pace.
  - `mascot`: `do=` the action: `wave`, `talk` (presenting), `point`
    (at the screen prop, or at the viewer without one), `present` (ta-da),
    `cheer` (jumps, confetti), `think`, `shrug`, `sad` (the problem, under
    a rain cloud), `walk` (walks in, then waves), `dance` (on the music's
    beat), `thumbs`, `wow`. `prop=` puts something in its hands: `phone`
    or `laptop` with `src=` the user's real screenshot (a laptop held up
    with the mascot behind it is the 3D version of the classic "founder
    holding the laptop" cover), `sign` with `text=` (or `src=` their
    logo), or `screen`, the screenshot floating beside it for `point`
    and `present`. `set=` picks the place: `room` (a living room by
    day), `stage` (an LED wall and light beams), `city` (a rooftop at
    dusk), `park` (sky, hills, and trees), `studio` (light and seamless),
    or `night`; without one, shots take the room, stage, city, and park in
    turn, so a video moves through places. Pick them to fit the line (the
    stage for a launch, the room for working, the park for a payoff).
    `bg=assets/<photo>` stands the mascot in front of the user's own photo
    (their office, their shop), softly blurred; `face=` (`happy`, `wow`, `love`, `sad`, `think`,
    `wink`) overrides the expression; `frame=mid` or `full` the framing;
    `talk=no` keeps its mouth shut when the voice isn't the mascot's.
  - `desk`: a cozy desk at night, the mascot typing at a monitor showing
    `src=` (the user's screenshot), spinning round on its chair to wave,
    then the camera pushes in and flies into the screen. A strong opener,
    and a transition into the product: follow it with a `mascot`
    shot holding or pointing at the same screen. `mascot=no` leaves the
    chair empty.
  - `title`: `text=` (one to three short words) as big 3D letters
    dropping onto the studio floor one by one, the mascot cheering beside
    them. For a launch name, a result ("Sent", "Posted"), or a number the
    user gave.
  - `icons`: app tiles dropping into a grid, a small mascot waving in the
    last cell: `items="🔍 Research,📅 Calendar"` (an emoji, then a short
    label; up to 8). For a product's features, a plugin's skills, or the
    tools it works with; two `icons` lines show up to 16.
  - `notes`: handwritten sticky notes floating in the dark, the camera
    drifting through them: `items="a launch video,a week of posts"` (up to
    8). Ideas, requests, or a week's plan; never a quote someone didn't
    say.
  - `button`: the call to action as a big button a cursor clicks,
    `text="☆ Star"` changing to `done="★ Starred"` (or "+ Follow" to
    "Following") under confetti while the mascot cheers.
  - The product's own screens, for a launch video or a demo: `terminal`,
    `agent`, `wall`, `player`, and `comments` (see "The product demo"
    below).
  - The abstract shots still work alongside: `shapes`, `hero` (a phone;
    `src=` the user's real screenshot), `cards` (`items=` short labels),
    `chart` (`values=` the user's real numbers only), `coin` (`src=` their
    logo), `rings`, `globe`.
  - The mascot is the brand's character, not a person: never present it
    as a customer, a reviewer, or a team member, and never give it a
    quote someone didn't say.
- **pixel** (`templates/pixel.html`): `walk` (`time=day`, `sunset`, or
  `night`), `boss` (the problem, beaten), `coins` (a payoff), `levelup` (a
  result), `city`, `space`, `photo` (`src=` the user's image, pixelated).
  The robot hero wears the accent color, captions sit in a game dialog box,
  and the music is `chiptune` in the identity's key and hook (say so to the
  user, and offer `music: identity` if they'd rather keep their usual genre).
- Pick shots that match each line's meaning: `icons` when the line lists
  what the product does, `notes` for ideas or a plan, `button` under the
  CTA, `mascot do=sad` or `boss` under the problem, `desk` or `mascot prop=laptop` when the work or the
  product is the point, `point` or `present` with `prop=screen` to show
  the product, `cheer`, `title`, `coins`, or `levelup` under the payoff,
  `chart` only with real numbers, `wave` or `thumbs` under the CTA. Never
  pass a screenshot, logo, photo, or number the user didn't supply; the
  shots fall back to generic artwork without them.
- Each template's comment lists every shot, its settings, and the events
  a sound can be cued on (`data-sfx="pop:land"`); `compose.js` adds one
  fitting sound per shot.
- Look at `--slides` before rendering, as always. 3D renders slowly on a
  machine without a graphics card (the mascot's shots at about a frame
  every half second per core in software), so tell the user to expect a
  few minutes for a 20-second video, and use `--draft` to check the
  motion first; pixel art is as quick as any template.
- **The user's own character in the robot's place:** when they have
  their mascot or avatar as a rigged 3D model, it stars instead of the
  robot, rendered locally like everything else. Ask for it as one `.glb`
  file (glTF binary; a `.vrm` from VRoid works too), put it in `assets/`,
  and add `character: assets/<name>.glb` to the script's frontmatter
  (`character=` on one shot puts it in just that shot; a `Character:`
  line in the Visual Identity puts it in every 3D video). Every shot the
  robot appears in takes it: `mascot` with all its actions and props,
  `desk`, `title`, `icons`, and `button`.
  - Its own animation clips play when their names match an action
    (`Wave`, `Walking`, `Dance`, `ThumbsUp`, `Jump` for `cheer`, `Idle`).
    Otherwise its skeleton is posed like the robot's (bones are matched
    by name: Mixamo's, Blender's `.L`/`.R`, VRoid's, Ready Player Me's),
    on top of its idle clip if it has one.
  - It lip-syncs through its blend shapes (`jawOpen`, `viseme_aa`, `A`,
    `mouthOpen`), blinks (`eyeBlink`, `Blink`), and smiles or looks sad or
    surprised when the action calls for it; with no blend shapes it opens
    its jaw bone, or nods on the words.
  - Where to get one: a character uploaded to Mixamo (free) comes back
    rigged and with animations (download as FBX, then export as glTF
    binary from Blender), Ready Player Me and VRoid export rigged avatars,
    and any rigged model from a 3D artist works. Use the user's own
    character, one they made or bought the rights to, never a famous
    studio's or game's. A model without a skeleton still works, moving
    as a whole.
- **Other animation styles** (cartoon or anime characters drawn in 2D,
  claymation, or the user's own mascot when it's only a drawing, with no
  3D model) can't be drawn locally. They need a connected video model
  (Higgsfield or Figma Weave, step 3 of the skill) with the style in the
  prompt, which spends the user's credits; offer the 3D mascot or pixel
  art as the free alternative.

## The bold look: the cover that stops the scroll

Add `captions: bold` to a script's frontmatter (any style) for the look
of the big creator ads: heavy capitals boxed in black, the subject big
above them, and the first line whole on screen from frame 0, so the first
frame is the cover. Short lines (up to 8 words) show whole; longer ones
come a few words at a time, so a long explainer doesn't bury its picture. Mark the
words that sell it with asterisks, in the lines and the hook (`I built
an *AI* that makes *viral* video ads`); they stay yellow, and the
asterisks aren't spoken. Write the first line as the hook itself and set
`hook:` to the same words, so it shows once. `series: week 2` and
`brand: Your Name` put a tag in each top corner for the whole video
(a series number brings viewers back for the next one).

The subject is what makes the cover: the user's own face (a photo of
them, or their filmed take), their product, or the mascot holding their
product (`[shot: mascot do=talk prop=laptop src=assets/app.png]`).

- **The user's photo with their product on its screen.** Ask for a photo
  of them holding their laptop or phone (any screen content), and their
  screenshot. Put the screenshot on that screen:
  `[bg: assets/me-laptop.jpg screen=assets/app.png at=x1,y1,x2,y2,x3,y3,x4,y4]`,
  with the screen's four corners in the photo's own pixels, clockwise from
  the top left (look at the photo to read them). It moves with the photo's
  zoom. Check it with `--stills 0` and nudge the corners until the edges
  sit on the screen's.
- **Their filmed take:** `cut.js ... --bold [--series "week 2"] [--brand
  "Name"]` gives a talking-head video the same look, a few words at a
  time, with `*keywords*` in `--text` and `--hook`.
- Never make up the person: a face on the cover is the user's own, or
  someone who agreed to it, never stock or an AI image passed off as a
  real customer or founder.

## The product demo: a launch video's look

When the user wants a launch video, a product demo, or "a video like
<some product>'s launch", show the product working rather than a
presenter talking about it. Launch videos that get shared spend most of
their time on the product's own screens, move the camera from one to the
next instead of cutting, stay in one dark palette, and keep the words
small. In `style: 3d`, with `captions: subtitle`:

```
---
title: the launch
style: 3d
captions: subtitle
format: landscape
---
1. I built a plugin that does my marketing. [shot: desk mascot=no]
2. Two commands install it. [shot: terminal lines="$ claude plugin marketplace add you/repo|✔ Successfully added marketplace: repo"]
3. Ask it for a battlecard. [shot: agent ask="Research Acme" steps="Skill(you:research)|Web Search(acme pricing)|⎿ Did 1 search in 2s" done="Battlecard ready." doc="# Acme brief|## Bottom line|## SWOT|## Sources"]
4. It made every one of these. [shot: wall items="assets/a.jpg,assets/b.jpg,assets/c.jpg" labels="promo,quiz,pov"]
5. Oh, and this video? It made this too. [shot: player src=assets/opening.mp4 aspect=16:9 offset=1.5]
6. What should it make next? [shot: comments text="What should it make next?" ask="a podcast clip maker"]
```

- `desk mascot=no` opens on an empty desk at night with the next shot
  live on the monitor; the camera drifts in and pushes into the screen
  until the screen is the frame, with no cut.
- `terminal`: `lines=` the real commands (a line starting `$ ` is typed,
  the rest print as its output; `|` between lines), `title=` the window.
  Run the commands and copy what they really print; never invent output.
- `agent`: an AI agent's session (Claude Code by default, `app=Codex` for
  Codex): `ask=` typed at its prompt, `steps=` its tool calls streaming in
  (`Web Search(...)`, `Read(...)`, `Write(...)`; a step starting `⎿` is
  the result of the one above), `done=` the last line, and `doc=` the
  document it wrote sliding in beside it (`# ` a title, `## ` a heading,
  `- ` a bullet) while the camera pans over. Use the steps the skill
  really takes and its real output headings; a made-up competitor is
  `Acme` at `acme.example`, never a real company with invented facts.
- `wall`: `items=` the real things the product made (frames, thumbnails,
  screenshots; up to 24), `labels=` under them, floating in the dark as
  the camera flies through.
- `player`: the user's real video or picture in a player window, the
  scrubber moving; `aspect=16:9` for a clip, `offset=` where to start.
  For "this video made itself", render the page's first seconds
  (`render.js page.html assets/opening.mp4 --duration 7`), then render
  the whole page.
- `comments`: the ending, a handwritten question over an empty comment
  box whose placeholder types `ask=`. It never shows anyone's comments.
- Between two screen shots the camera pushes through one into the next;
  between a screen and a 3D shot it hands over the same way, so the
  video reads as one take. A light `icons set=studio` line in the middle
  is a good change of pace (the subtitles get a soft dark backing over
  it); keep the mascot, if any, to one or two lines.
- Screen shots render quickly (several frames a second), so a
  screen-heavy video renders in a fraction of a mascot video's time.

## Start the page

For everything else, copy the template `video-types.md` or `fyp-formats.md` names, from
`${CLAUDE_PLUGIN_ROOT}/scripts/video/templates/`, to
`${CLAUDE_PLUGIN_ROOT}/state/videos/<date>-<slug>.html`. There are eight
marketing templates (`promo`, `how-to`, `testimonial`, `faq`,
`announcement`, `team`, `narrated`, which `compose.js` uses, and
`montage`, which `montage.js` uses), 22
everyday ones (`pov`, `tier-list`,
`text-chat`, `storytime`, and the rest listed in `fyp-formats.md`), and the
two drawn ones, `3d` and `pixel`, which are easiest made with `compose.js`
and a style (above). Put any images the user supplied in
`state/videos/assets/`.

Rewrite its scenes to the script: one scene per beat, the hook readable
within the first second, and every line of text inside the `.scene` box
(each platform's UI covers the bottom quarter and right edge). Keep the
template's colors and type unless `brand-voice.md` says otherwise.
Everyday templates use TikTok Sans, the platform's own caption font, and
the shared pieces (captions, stickers, stamps, chat and notification
mockups, tier lists, polls, timers) documented at the top of `promo.html`.

## The sound

Set the `<body>` music attributes from the Sonic Identity in
`brand-voice.md`: `data-music`, `data-bpm`, `data-key`, `data-mode`,
`data-energy`, `data-motif`.
- Testimonials and sensitive topics use `data-music="calm"`, keeping the
  project's key and hook.
- Pixel art uses `data-music="chiptune"`, keeping the project's key and
  hook; its 8-bit cues (`coin`, `jump`, `powerup`, `blip`, `hurt`) go on
  the shots' events.
- An announcement can raise energy one step.
- An everyday post can take its template's genre (`phonk` under a
  "nobody: / me:", `lofi` under a text skit), keeping the identity's key
  and hook, within what the brand voice allows (see "Everyday and FYP
  posts" in `sound-guide.md`). Its meme cues (`scratch`, `boom`,
  `rimshot`, `ding`, `buzzer`, and the rest) are listed there; one or two
  per video is plenty.
- Add `data-break="<start>-<end>"` under a quote or any moment the words
  should carry alone.
- **No identity saved yet:** propose two from
  `${CLAUDE_PLUGIN_ROOT}/references/sound-guide.md`, each with one line on
  why it fits. Render a preview of each (`node
  ${CLAUDE_PLUGIN_ROOT}/scripts/video/render.js --sample <genre> <out.m4a>
  --motif ... --key ... --mode ... --energy ...`, a few seconds each). Send
  both to the user to listen to, and save their pick to `brand-voice.md`
  before rendering. You can't hear audio, so their ear decides.
- **Finding a licensed track:** `node
  ${CLAUDE_PLUGIN_ROOT}/scripts/video/media.js search "<mood or genre>"
  --type music --out ${CLAUDE_PLUGIN_ROOT}/state/videos/assets --count 3`
  downloads Creative Commons music from Openverse that allows commercial
  use and changes, records each track's credit line, and reports its tempo
  and how steady its beat is (from `beats.js`). Prefer a confidence of 0.5
  or more for cutting on the beat. Send the user the files to listen to;
  you can't hear them.
- **The user has a licensed track they'd rather use:** put it in
  `assets/`, set `data-music-src` and `data-music-start`, and record its
  license with `node ${CLAUDE_PLUGIN_ROOT}/scripts/video/media.js credit
  <file> --source ... --license ...`. Don't use a track without a license
  note. Then read its rhythm: `node
  ${CLAUDE_PLUGIN_ROOT}/scripts/video/beats.js assets/<file> --align <end
  of the hook, s> --duration <length>`. If the confidence is 0.5 or more,
  use the `data-music-start` it prints and move scene changes and key cues
  onto its bar (or beat) times; if it's lower, don't snap anything and time
  scenes to the voice or reading pace. Tell the user what you did ("104
  BPM, started at 0:32 so the drop hits as the hook ends, cuts on the
  bar"), and send an `--audio-only` render to check the sync, since you
  can't hear it. For a narrated script, `music: assets/<file>` in its
  frontmatter does all of this in `compose.js`: it reads the beat, starts
  the track so its lift lands as the hook ends, and moves every scene
  change onto a beat.
- **Longer than about 45 seconds:** the generated music repeats the same
  few bars and wears thin, so ask for a licensed track instead. The
  renderer warns about it.

## A voiceover

The user's own recording, a free generated voice from
`${CLAUDE_PLUGIN_ROOT}/scripts/video/voice.js` (Kokoro, runs locally, no
key or cost; see "A free generated voice" in `sound-guide.md` for setup,
and send the user `--audition` samples to pick a voice, since you can't
hear them), or a voice they generate with a service they have their own
key for.

Write the script line by line, ask them to record each line as its own
file (`voice-1.m4a`, `voice-2.m4a`, ...), and put the files in `assets/`.
Add `data-voice="assets/voice-1.m4a"` to the element each line belongs
to; it plays at that element's `--voice` time, or `--in`. For one
continuous take, use `<body data-voice-src="..." data-voice-start="...">`
instead. The renderer trims the silence at both ends of each line, levels
the lines to match, and ducks the music and effects under the voice.
`render.js <page> --voice-lengths` lists each line's start, length, and the
room its scene leaves; time each scene to it, and the renderer warns when a
line runs past its scene. Under a voice, keep sound effects to scene
changes; the renderer warns past one every 3 seconds.

**Captions synced to the voice:** put the line's text in
`<div class="say auto" data-voice="assets/voice-2.m4a"
style="--voice:3.4s">...</div>` and the renderer shows it word by word,
in short chunks, with the word being said highlighted, timed to the clip
(`captions.js`, from the clip's pauses and the words' lengths; about 50 ms
from the true word starts on average). Most people watch muted, so caption
every voiced line. `--whisper` times them with Whisper instead, if
`kokoro-js` is installed and huggingface.co is reachable; it falls back on
its own when Whisper's timing doesn't hold up.

Never imitate a real person's voice without their permission, and if the
voice is AI-generated, have the user check whether the platform asks for
an AI-content label.

## The backgrounds

Every scene has an empty `.bg` slot timed to it.
- **What to search for:** for each scene, pick a setting or mood that fits
  the beat and the project's audience (e.g. "small bakery counter
  morning", "city at night aerial"). Not the product, a person, or a
  result.
- **Stock photos and clips:** `node
  ${CLAUDE_PLUGIN_ROOT}/scripts/video/media.js search "<query>" --out
  ${CLAUDE_PLUGIN_ROOT}/state/videos/assets [--type video]` searches Pexels
  (`PEXELS_API_KEY`) and Pixabay (`PIXABAY_API_KEY`), both free keys, and
  Openverse (photos only, no key). It downloads into `assets/` and records
  each file's license and required credit in `CREDITS.md` there. With no
  keys set, say that Openverse is the only source and it has no video
  clips, and point to the free keys rather than going without.
- **AI-generated images:** only with a connected image tool. That's Figma
  Weave once the user's Figma account is linked (find the model with
  `weave_find_model`, then `weave_run_model`, which quotes a cost first),
  or Higgsfield. Show the quoted cost and get an explicit yes before every
  run, since it spends the user's credits. Download each result into
  `assets/` and record it with `node
  ${CLAUDE_PLUGIN_ROOT}/scripts/video/media.js credit <file> --ai "<tool /
  model>" --prompt "<prompt>"`.
- **Placing:** put `<img class="bg-media" src="assets/<file>" alt="">`, or
  `<video class="bg-media" src="assets/<clip>">`, in the slot.
- **Look:** a consistent set reads as produced. Prefer the same light and
  palette across scenes. Use `class="bg blur"` on busy images, and
  `class="bg tint"` to pull mismatched ones toward the brand color. The
  renderer darkens bright backgrounds automatically; for a busy one, add
  `blur` or a heavier `--shade` on the slot.
- **People and real things:** a testimonial's or team video's person is
  always their own photo, never stock or AI.

## Timing and cues

Set `<body data-duration>` to the script's length and `data-drop` to when
the hook ends, so the beat drops as the body starts. Put `data-sfx` cues
only on moments that should land: words popping in, list items, a
checkmark, a button press, a scene change. A sound on everything reads as
noise. The comment at the top of `promo.html` documents the sounds, music
settings, background slots, and attributes, and each template's own
comment says what to replace. Replace every bracketed placeholder; never
ship one.

## Your own footage

- **Screen recordings** go straight into the how-to phone frame:
  `<video class="shot" src="assets/step-1.mp4" data-loop="false">` in a
  `.screen`. The renderer cuts a clip in a smaller box to that box's own
  shape, so a tall phone recording isn't cropped at the top and bottom.
  The product shown must be the real one.
- **A talking-head take** (filmed on a phone, one take): ask the user for
  the clip and, word for word, what they say in it. Then
  `node ${CLAUDE_PLUGIN_ROOT}/scripts/video/cut.js <take.mp4> --text "<what's
  said>" --hook "<hook>" --cta "<cta>" --page
  ${CLAUDE_PLUGIN_ROOT}/state/videos/<date>-<slug>.html` cuts out the pauses
  (`--min-pause`, default 0.35s), and writes a page with the clip full
  frame and its own sound, captions synced to it, the hook from the first
  frame, the music one energy step lower, and the brand's end card. It runs
  `--check`; render as usual. Captions use the person's real words only,
  never a tidied version, and only post people who agreed to it.
- **A realistic avatar's clip** (a talking presenter made by a connected
  AI avatar tool such as HeyGen, Synthesia, D-ID, or Hedra) goes through
  `cut.js` the same way, with the script it was given as `--text`. Label
  it as AI-generated when posting, and use a stock avatar or the user's
  own likeness with their consent, never a real person who didn't agree.
- **By hand:** `<video class="bg-media" id="take" src="assets/take.mp4"
  data-audio>` plays a clip's own sound in sync with it (from its
  `data-offset`, while the clip is on screen), leveled like a voiceover
  with the music ducked under it, and `<div class="say auto"
  data-clip="take">what's said</div>` captions it.

## Copy a reference video's editing

When the user sends a video they like ("make ours like this"), read how
it's edited before writing anything:

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/video/reference.js <video> [--out <dir>]
```

It writes `reference.md`, `reference.json`, and `sheet-1.jpg`... (one
frame per scene, labeled with its number, time, and length; `~` marks a
scene that arrives by a transition rather than a cut) in
`<video name>-reference/` next to the video. It measures:

- the scenes: every hard cut and every transition (a dissolve, a push
  through, a whip, flying into a screen), how long scenes hold (half the
  running time is in scenes at least this long), bursts of quick cuts (a
  montage inside the video), whether it speeds up, and how long the hook
  holds before the first change;
- the camera: one moving camera from scene to scene, fast cutting, or
  cuts between moving or steady shots;
- the look: dark, mid, or light, and its main colors;
- the sound: the tempo, whether the cuts land on the beat more often than
  chance, and the loudness.

Then look at the sheets for what numbers can't show: the captions (size,
case, boxed or plain, where they sit, a phrase or a word at a time), the
framing, what's on screen, and the transitions. `reference.md` ends with
a plan in compose.js's own settings (format, line count and length, the
shots that move the same way, the sets for its palette, the music tempo,
the caption style); follow it, adjusting for the user's own content and
brand. Tell the user what you're matching in a line or two.

Copy how it's edited, never what's in it: none of its footage, music,
characters, logos, or words go into the new video. Where the reference
does something the renderer can't (a photoreal 3D room, real footage of
people), say so and offer the nearest thing it can.

## The hook, the look, and the cover

- **The hook is on screen from frame 0.** The first frame is the default
  cover and the moment a viewer decides to stay. Every template's hook has
  class `now` (shown at once, with a small settle) instead of an entrance;
  keep it that way when rewriting, and `--check` fails a page whose first
  frame or first second has no text. It also fails text that leaves before
  it can be read (about four words a second), and notes stretches over 3
  seconds where nothing changes ("Pacing", advice only).
- **Hook variants.** To test hooks, put each version on the same page with
  `data-variant="a"`, `"b"`, `"c"` on the elements that differ (usually
  just the hook caption; everything else stays shared). `render.js <page>
  out.mp4 --variants a,b,c` writes `out-a.mp4`, `out-b.mp4`, ... and
  `--check` checks every variant. Write the three from different patterns
  in `hooks.md`. Instagram's trial reels, or one variant per platform, are
  ways to test them.
- **The brand's look.** Run `node ${CLAUDE_PLUGIN_ROOT}/scripts/video/brand.js
  <page>` after rewriting a template. It applies the Visual Identity from
  `brand-voice.md` (colors, display font) and, on marketing and narrated
  pages, adds a 1.6-second end card with the logo and handle after the
  last scene, landing with the sonic logo. It warns when the colors are too
  low in contrast to read. Running it again replaces what it added.
  `compose.js` does this itself. With no Visual Identity saved yet, ask
  for one (colors from their site or a description, a font, the logo, the
  handle) and save it there first, or keep the template's look.
- **The cover.** `render.js <page> --cover 0` writes the cover frame as a
  PNG next to the page and checks its text sits inside the 3:4 crop the
  profile grids show; with a render (`render.js <page> out.mp4 --cover 0`)
  it lands next to the video. Pass the time it prints to
  `publish_direct.py --cover-ms` (TikTok and Instagram), or host the PNG
  and pass `--cover-url` (Instagram). YouTube's cover is picked in its app.

## Preview, then render

The full render takes a couple of minutes, so preview first:
- `node ${CLAUDE_PLUGIN_ROOT}/scripts/video/render.js <page> --check` lints
  the whole timeline in seconds: text outside the safe area, spilling out
  of its box, clipped, or running into other text or a card. Fix
  everything it lists (usually by shortening the line) and run it again
  until it's clean.
- `node ${CLAUDE_PLUGIN_ROOT}/scripts/video/render.js <page> --slides`
  writes each scene's settled frame as a PNG to a `slides/` folder next to
  the page (`--stills <times>` picks the moments instead). Look at every
  one for what a lint can't judge: legibility over the background, emoji,
  and whether the joke reads.
- Those `--slides` PNGs double as a photo carousel (TikTok photo mode, an
  Instagram carousel). Offer that for `slideshow` and any list-style post.

Render: `node ${CLAUDE_PLUGIN_ROOT}/scripts/video/render.js <page>
${CLAUDE_PLUGIN_ROOT}/state/videos/<date>-<slug>.mp4`. The output is
1080×1920, 30fps H.264 with AAC audio mixed to about −14 LUFS, which is
what all three platforms expect. That file is what `--platform youtube`
uploads directly. Frames render in parallel (one browser per core but one,
up to four; `--workers` sets it), so a 12-second video takes well under a
minute on a laptop. For a quick look at timing and sync before the real
render, `--draft` makes a half-size 15fps version in a fraction of the
time; never post a draft. Several pages at once (a week of videos):
`render.js --batch <page> <page> ... [--outdir dir] [--cover 0]` renders
each to `<page>.mp4`, every hook variant included.

## Credits and labels

Copy the credit line from `assets/CREDITS.md` into every platform's
caption or description when it says one is required (Pexels, CC BY
photos, some tracks). If any AI image is photorealistic, tell the user to
switch on the platform's AI-content label when posting. TikTok, YouTube,
and Instagram all ask for it for realistic synthetic scenes.
