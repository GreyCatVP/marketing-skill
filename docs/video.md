# Video

How `short-form-video` makes the actual video: with a connected
image/video tool, or rendered on your machine for free. The renderer is
the main path: templates for marketing and everyday posts, narrated
videos with captions synced to the voice (`compose.js`), 3D and
pixel-art animation narrated the same way, your own filmed takes
(`cut.js`), and the brand's look and sound on every one.

- [Connecting a visual-generation tool](#connecting-a-visual-generation-tool)
- [Connecting a short-form video generation tool](#connecting-a-short-form-video-generation-tool)
- [Rendering a short-form video locally](#rendering-a-short-form-video-locally)

## Connecting a visual-generation tool

`visual-brief-generator` checks your currently connected tools for an
image/video-generation MCP connector at runtime — it doesn't assume a
specific one. Higgsfield launched an official hosted MCP server in 2026
(Runway and Midjourney still have no known official one as of this
writing); a **Canva** connector also exists (requires connecting via
OAuth in your Claude settings) as another real option for visual asset
work — neither is hardcoded or assumed present. If none is connected, the
skill still produces the full written brief and prompts — just paste them
into whatever tool you use.

## Connecting a short-form video generation tool

`short-form-video` checks the same way, at runtime, for a connected
image/video-generation tool — it never assumes one is present, the same
rule `visual-brief-generator` follows above.

- **Higgsfield** is a real option if you have it connected: its hosted
  MCP server exposes 30+ image/video models (including Veo, Sora, Kling,
  and Seedance) through one connection, generating clips up to roughly 15
  seconds per generation from a text or image prompt. It isn't a default
  connector for every account, so if you have a Higgsfield account and
  want to use it here, add it yourself as a custom connector: in Claude,
  go to Customize → Connectors → Add custom connector, and give it a name
  plus Higgsfield's own MCP server URL from your Higgsfield account.
  Connecting the MCP server itself is free; **generating through it still
  spends Higgsfield's own credits** (published annual plans currently run
  from about $15/month for 200 credits up to $99/month for 3,000 — new
  accounts get some starter credits free). Being connected doesn't mean
  free generation, the same distinction this plugin's `email-outreach`
  skill already draws about a connected prospecting tool.
- **Figma Weave** is another option if you have the Figma connector: its
  `weave_*` tools can run named AI video models (Veo, for example). It
  spends your Weave credits — the skill shows you the quoted cost and
  waits for a yes before each run — and it only works once your Figma
  account is linked to Weave in Weave's own profile settings.
- **Canva** works here too, the same connector already documented above
  for `visual-brief-generator`.
- **Listed isn't the same as working.** A connector can appear in your
  session but still be waiting on authorization (Canva often is), or
  still need an account linked (Weave). The skill tells you which one and
  the exact fix, rather than just saying nothing is connected.
- **Once a clip is generated**, the skill downloads it to a local file
  right away, because generator links usually expire. That file is what
  `--platform youtube` uploads. For Instagram or TikTok, re-host it on a
  URL you control before posting: TikTok only fetches from a domain
  verified for your own app.
- **No connector at all?** The skill can still render the video itself
  on your machine, for free. See "Rendering a short-form video locally"
  below.
- **If none of these is connected**, the skill still produces the full script
  and per-platform package, and recommends current free tools to actually
  make the video yourself — **CapCut** is the most confident
  recommendation (genuinely free, no watermark on exports, built for
  vertical Shorts/Reels/TikTok-style editing specifically), with Canva's
  free tier as a second solid option. Plenty of other "free AI short-video
  generator" tools advertise themselves online; this plugin's research
  couldn't independently verify most of their actual quality or
  free-ness, so treat any of them beyond these two as something to vet
  yourself before trusting with real content.

## Rendering a short-form video locally

`scripts/video/render.js` turns an animated HTML page into a finished
vertical video, with no video-generation service involved. When you opt
in, `short-form-video` writes the page from its own script and renders
it. You can also run the renderer yourself.

**What it makes:** motion graphics (kinetic text, shapes, UI mockups) over
real backgrounds, or drawn 3D and pixel-art scenes (see "3D and pixel-art
animation" below), with music composed for your project, and a voiceover if
you record or generate one. It doesn't film your product or people, but it does finish
footage you film: `cut.js` takes a talking-head take from your phone, cuts
out the pauses, and makes the video from it with its own sound, captions,
your hook, music, and end card; `montage.js` edits several clips into a
montage (the `clip-montage` skill); and screen recordings play in the
how-to phone frame without being cropped. The output is 1080×1920
(9:16), 30fps H.264 with AAC audio mixed to about −14 LUFS, which is what
YouTube Shorts, Instagram Reels, and TikTok all expect.

**One-time setup:** you need Node 18+, ffmpeg (`brew install ffmpeg` or
`apt install ffmpeg`), and Playwright:

```
cd scripts/video
npm install                       # Playwright, and three.js for the 3D template
npx playwright install chromium   # skip if Google Chrome is installed; it's used as a fallback
npm install kokoro-js             # optional: free generated voiceovers (about 600 MB)
npm install @huggingface/transformers   # optional: 3D photo moves in montages (depth maps from huggingface.co; add --ignore-scripts if it stops on a GPU download)
```

For stock backgrounds, also get free API keys from
[Pexels](https://www.pexels.com/api/) and [Pixabay](https://pixabay.com/api/docs/)
and set them as `PEXELS_API_KEY` and `PIXABAY_API_KEY`. Without them, only
Openverse photos are available (no video clips).

**Usage:**

```
node render.js templates/promo.html out.mp4             # full render, in parallel: well under a minute for 24s
node render.js templates/promo.html out.mp4 --draft     # half size at 15fps, a few seconds, to check timing
node render.js --batch week/*.html --outdir renders     # a week of pages in one run, every hook variant included
node render.js templates/promo.html --check             # lint the layout over the whole timeline, in seconds
node render.js templates/promo.html --slides            # each scene's settled frame as a PNG (also a carousel)
node render.js templates/promo.html --stills 1.5,6,12   # preview frames at chosen times
node render.js templates/promo.html out.m4a --audio-only  # just the soundtrack, in seconds
node render.js --sample pop out.m4a --motif "1 3 5 3 | 6 5 3 -" --key D   # audition a sound
node render.js page.html out.mp4 --silent               # silent audio track instead of the soundtrack
node media.js search "cozy coffee shop morning" --out assets --count 3     # stock photos (+ --type video)
node media.js search "upbeat acoustic" --type music --out assets          # Creative Commons music, with tempo and credits
node check.js                                            # QA every template: layout, cues, fonts, loudness
node beats.js assets/track.mp3 --align 2 --duration 24   # a track's tempo and beats, started so its drop hits 2s
node voice.js script.md --out assets --voice af_heart     # a free voiceover, one WAV per script line
node voice.js --audition samples "One line to try."       # the same line in four voices, to pick one
node compose.js script.md                                 # a narrated video page from a script: voice, backgrounds, synced captions
node compose.js script.md --style 3d                      # the same, drawn as 3D scenes (or --style pixel, as pixel art)
node montage.js inspect clips/ --slug maple              # copy a client's clips or photos in: metadata stripped, contact sheet
node montage.js frames assets/maple-02.mp4 --every 1     # a clip's frame every second with its time, and when its sound is loud
node montage.js state/videos/2026-10-21-maple.md         # a montage page from them: clip moments, moves, beat-synced cuts, labels, end card
node depth.js assets/maple-02.jpg                        # a photo's depth map (montage.js makes them itself, for 3D moves)
node render.js page.html --voice-lengths                  # each voice line's start, length, and room in its scene
node captions.js assets/voice-1.wav --text "the line"     # when each word of a line is said
node brand.js page.html                                   # the Visual Identity: colors, font, a logo end card
node render.js page.html out.mp4 --variants a,b --cover 0 # one video per hook variant, plus the cover frame
node cut.js take.mp4 --text "what's said" --page page.html # a filmed talking-head take: pauses cut, captioned, ready to render
```

Every page's hook is on screen from the first frame, which is also the
default cover, and `--check` fails a page whose first frame has no text or
whose text leaves before it can be read. Hook variants (`data-variant`)
render several versions of one video to test, and `--cover` writes the
cover frame, checked against the 3:4 crop the profile grids show.
`brand.js` applies the Visual Identity saved in `brand-voice.md` (colors,
a display font, and an end card with the logo and handle that lands with
the sonic logo), the visual counterpart of the Sonic Identity.

Every render lints its layout as it goes: text outside the area the
platforms' buttons and captions leave clear, text spilling out of its box
or clipped, and text running into other text or a card all get reported
with the time they happen. That's what catches rewritten copy that runs
long. `check.js` runs the same lint over every template (or the pages you
name), checks every sound cue, the music settings, the fonts, and the
loudness, and writes a report with a contact sheet per page to look over.

Fonts (Inter, and TikTok Sans for everyday posts) and color emoji come from
Google Fonts. The renderer fetches and caches them itself, so after the
first run it works offline, and behind proxies the browser doesn't trust.

### Backgrounds

Every scene in a template has an empty background slot already timed to
it. Put a photo or clip in it and it fills the frame, with:
- a slow zoom or pan
- a crossfade to the next scene
- a scrim that keeps text readable (bright images get darkened
  automatically)
- one shared color grade, so mixed sources look like one set

`blur` softens a busy image, and `tint` washes it in your accent color.
An empty slot shows the gradient instead.

Where backgrounds come from:
- **Stock photos and video clips:** `scripts/video/media.js` searches
  Pexels, Pixabay, and Openverse for vertical media. It downloads into the
  page's `assets/` folder and writes `CREDITS.md`, with each file's license
  and the exact credit line to put in your caption when one is required
  (Pexels and CC BY photos need one). Openverse results are limited to
  licenses that allow commercial use and modification.
- **AI-generated images:** made with a connected image tool (Figma Weave
  once your Figma account is linked, or Higgsfield). The skill quotes the
  cost and waits for your yes before every image. If an AI image looks
  photorealistic, switch on the platform's AI-content label when posting;
  TikTok, YouTube, and Instagram all ask for it.

Stock and AI images set the scene only. They never stand in for your
customers, team, product, or results; those are always your own real
photos and screenshots.

### Sound

Every video gets music composed for it in your project's **sonic
identity**: one genre, tempo, key, energy, and signature hook. It's saved
in `references/brand-voice.md` and used for every video, so your sound
becomes recognizable the way a jingle does. There are twelve genres:
`pop`, `house`, `hiphop`, `acoustic`, `cinematic`, `tech`, `lofi`, `calm`,
three for very online Gen Z and Gen Alpha feeds: `phonk`, `jersey`
(jersey club), and `funk` (Brazilian funk), and `chiptune`, an old game
console's sound, for pixel art.
The first time you render, the skill proposes two identities that fit your
audience and plays you a short preview of each.
[`references/sound-guide.md`](../references/sound-guide.md) explains the
genres and how they map to audiences, and has a library of hooks.

How a video's soundtrack is put together:
- **The hook:** enters as the melody when the beat drops, answered by a
  variation every four bars. Chords are chosen to fit it.
- **The ending:** a **sonic logo**, the hook's first notes resolving
  home on the last beat.
- **Sound effects:** land on the moments the page marks (words popping
  in, list items, checkmarks, a button press, scene changes), in the
  music's key. Everyday posts also get the meme cues: a boom, a record
  scratch, an air horn, a rimshot, a sad trombone, a drumroll, a ding and
  a buzzer, message pings, typing, a camera shutter, a ka-ching, a glitch,
  and a sub drop. Pixel art gets 8-bit ones: a coin, a jump, a power-up,
  a dialog-box blip, and a hit.
- **No licensing:** it's all synthesized from scratch, so there's nothing
  to license, and it works when posting through an API, where in-app
  trending sounds can't be added.
- **Your own track instead:** add `data-music-src="assets/track.mp3"`.
  The renderer trims it, fades it, and dips it under the sound effects.
  `beats.js` finds the track's tempo, beats, bars, and its biggest lift
  (a drop or chorus), so the skill can start the track where the lift
  lands on your hook and cut scenes on the beat. It says how confident it
  is; on music without a steady beat, scenes follow the voice instead.
  `sound-guide.md` lists where to get licensed tracks; never use a
  popular song without a license.
- **Longer videos:** the generated music is written for shorts and
  repeats the same few bars, so for anything over about 45 seconds use
  your own track. The renderer warns when a long video doesn't.
- **A voiceover:** record each line of the script on your phone, put the
  files in `assets/`, and add `data-voice="assets/voice-1.m4a"` to the
  element each line belongs to (or `<body data-voice-src>` for one
  continuous take). The renderer trims the silence before each line,
  evens out their levels, and ducks the music and effects under your
  voice.
- **A free generated voice instead:** `voice.js` reads the script with
  Kokoro, an open-source voice model (Apache-2.0) that runs on your own
  machine, so there's no account, API key, or cost. It writes one WAV per
  line in any of 28 stock voices. Install it once with `npm install
  kokoro-js`; the first run downloads the model (about 90 MB) and then
  works offline. If a platform asks whether a video uses AI-generated
  audio, say yes.
- **Captions synced to the voice:** most people watch muted. A line in
  `<div class="say auto" data-voice="...">` is shown word by word in short
  chunks, the word being said highlighted, timed to the clip by
  `captions.js` with no service involved (about 50 ms from the true word
  starts on average, checked against synthesized speech). The render also
  writes an `.srt` caption file. `--whisper` uses Whisper's word timing
  instead, if `kokoro-js` is installed.
- **A narrated video in one step:** `compose.js` takes a script of numbered
  lines (each with an optional `[bg: search query]`), voices it or uses
  your takes, fetches a background per line, times every scene to its line
  with cuts on the beat, and writes the page with the hook on screen from
  the first frame.

### Templates by video type

`short-form-video` picks a type from
[`references/video-types.md`](../references/video-types.md), a catalog of 23
marketing video types with the beats for each, how it gets made, and what
background and sound suit it. It then starts from the matching template
in `scripts/video/templates/`:

| Template | Length | For | Default sound |
|---|---|---|---|
| `promo.html` | 24s | Ads, brand profile, explainer, educational lists (it's a promo for this plugin) | tech |
| `how-to.html` | 20s | Tutorials, and product demos told as steps on a phone screen | tech |
| `testimonial.html` | 20s | Customer testimonials, case studies with counted-up results, interview pull-quotes | calm |
| `faq.html` | 18s | FAQ replies to a comment, myth vs fact | pop |
| `announcement.html` | 18s | Launches, plus event, webinar, and live-stream promos | house |
| `team.html` | 18s | Meet the team, the people side of a company profile | acoustic |
| `narrated.html` | per script | A voiceover over one background per line, with captions synced to the voice: explainers, tips, text-led brand stories (built by `compose.js`) | the identity, energy −1 |
| `3d.html` | per script | The same, over 3D scenes in the brand's colors: explainers, launches, a product reveal with your screenshot (`compose.js`, `style: 3d`) | the identity, energy −1 |
| `pixel.html` | per script | The same, over pixel-art game scenes with a dialog box for captions: playful explainers, tips, brand stories (`compose.js`, `style: pixel`) | `chiptune` |
| `montage.html` | per script | A client's own clips or photos (a home, a product, a shop, an event), each clip at its best moment and each photo moving, cut on the beat, with labels, a clip's own sound or a voiceover, price and specs, and a contact end card (built by `montage.js`, for `clip-montage` and `montage-video`) | the client's identity |

The skill swaps each template's default sound for your sonic identity.

### Templates for everyday posts

Most of a feed isn't ads. It's the memeable, comment-driven posts in
between: POVs, tier lists, text-message skits, storytimes. There are 22
templates for the formats that have lasted, each 10–18 seconds, written in
TikTok's own caption style (TikTok Sans, boxed captions, stickers, and
stamps):

| Group | Templates |
|---|---|
| Meme captions | `pov`, `nobody-me` (nobody: / me:), `expectation-reality`, `tell-me-without`, `makes-sense` (things that just make sense), `starter-pack` |
| Comment bait | `tier-list`, `this-or-that`, `hot-take` (with a poll), `flags` (green / red), `quiz` (guess it in 3 seconds), `rating` |
| UI skits | `text-chat`, `notifications` (a lock screen filling up), `post-card` (likes and replies), `loading` (a stalled bar and an error) |
| Story & everyday | `storytime` (word-by-word captions), `countdown` (top 5), `day-in-life`, `reveal` (wait for it), `before-after` (a wipe), `slideshow` (also a photo carousel) |

[`references/fyp-formats.md`](../references/fyp-formats.md) covers each one:
why it gets engagement, its beats, the sound, a line of copy at a playful
and a professional tone, and when not to use it. It also covers planning a
week of them: about 70% evergreen formats, 20% trends, and 10%
experiments, with no format repeated within a week. `content-calendar`
follows that rotation. The copy follows your brand voice: lowercase,
slang, and emoji only if `brand-voice.md` allows them.

Skits are always fiction: generic roles ("client", "a friend") with emoji
avatars, never a real person's name, post, or messages, never a real
app's look, and never a reply praising the product. There are no
copyrighted meme images, and the jokes are about situations and habits,
never about groups of people. Trending sounds are added in the app when
you post.
Types that need real footage (behind the scenes, vlogs, UGC, on-camera
testimonials) get a phone shot list and edit notes instead; the renderer
doesn't fake real people or events. The testimonial and team templates
ship with bracketed placeholders, which the skill replaces only with real,
permissioned material from you.

### 3D and pixel-art animation

Two templates draw their own frames instead of showing photos: `3d.html`
with WebGL (three.js) and `pixel.html` on a canvas. The 3D one stars your
brand's **mascot**: a robot in your colors that walks, waves, points at
your product, holds up your phone or laptop screen, cheers under confetti,
and lip-syncs to the voiceover, so a video without footage still has a
character to watch instead of floating text. Both are narrated like
`narrated.html`: a voiceover line by line, word-by-word captions synced to
the voice, the hook on screen from the first frame. The text stays on top
as ordinary page text, so the QA pass, sound cues, and captions work the
same as on every other template.

Behind each line is a **shot**, from a small library in each template:

| Style | Shots | Sound |
|---|---|---|
| `3d` | `mascot` (the mascot in a light studio or at night, doing `do=wave`, `talk`, `point`, `present`, `cheer`, `think`, `shrug`, `sad`, `walk`, `dance`, `thumbs`, or `wow`, holding `prop=phone`, `laptop`, or `sign`, or presenting `prop=screen`, all with your screenshot), `desk` (the mascot typing at a monitor showing your screen at night, spinning round to wave, then the camera flies into the screen), `title` (big 3D letters of your word dropping onto the floor), and the abstract ones: `shapes`, `hero` (a phone with your screenshot), `cards`, `chart` (your real numbers), `coin` (your logo), `rings`, `globe` | Your sonic identity |
| `pixel` | `walk` (a robot walking through a scrolling landscape, by day, sunset, or night), `boss` (the robot beating a slime: the problem, defeated), `coins` (a chest bursting with coins), `levelup` (a burst of light), `city` (a night city), `space` (a rocket through the stars), `photo` (your image, pixelated) | `chiptune`, in your identity's key and hook |

Both take their colors from your Visual Identity: the 3D mascot and its
scenes wear your accent color, and so does the pixel robot. Both robots
are original characters; nothing is borrowed from a real game or studio.
The mascot's mouth follows the words of the captions, which are timed to
the voice, so it lip-syncs to a generated voice or your own recording.

The quickest way to make one is a script with a style:

```
---
title: late invoices
style: 3d                        # or pixel
hook: you're losing money on every late invoice
cta: one money habit a week
---
1. Most freelancers lose money on invoices they send late. [shot: mascot do=sad]
2. I built a tool for it at 2 a.m. [shot: desk src=assets/app.png]
3. One tap and the invoice is out. [shot: mascot do=point prop=screen src=assets/app.png]
4. Paid. [shot: title text="Paid"]
5. Follow for one money habit a week. [shot: mascot do=cheer]
```

`compose.js` voices it, gives every line a shot (the ones named, the rest
in turn: with `style: 3d` the mascot waves, talks, points, and cheers),
times everything to the voice, and writes the page.
`[shot: mascot do=talk prop=laptop src=assets/app.png]`,
`[shot: cards items="Plan,Film,Post"]`, `[shot: chart values=12,30,85]`,
and `[shot: walk time=night]` set a shot's details. Each template's
comment lists every shot and what it takes.

- **Your material only:** a screenshot on the mascot's phone, laptop,
  monitor, or screen, a logo on the coin or sign, numbers on the chart, and
  a pixelated photo must be the real ones. Without them, the screens show
  a generic interface and the chart a plain rising icon, never made-up
  data. The mascot is your brand's character, never a stand-in for a
  customer or a team member.
- **Render time:** pixel art renders as fast as any template. 3D is
  fastest on a computer with a graphics card; without one (most cloud
  machines) it's drawn in software: the mascot's scenes take about half a
  second a frame per core, so a 20-second video takes a few minutes on a
  4-core machine. `--draft` checks the motion in a fraction of that.
- **Other styles** (cartoon characters, anime, claymation, or your own
  mascot's design in place of the robot): those need a video model,
  through a connected tool such as Higgsfield or Figma Weave (see the
  start of this guide), with the style in the prompt. That spends the
  tool's credits.

### The bold look (a cover that stops the scroll)

The big creator ads open on a face, a product, and a few huge words:
`I BUILT AN AI THAT MAKES VIRAL VIDEO ADS`, white capitals boxed in
black, the selling words in yellow, a series tag in the corner. Add
`captions: bold` to any script for that look:

```
---
title: week 2
captions: bold
hook: I built an *AI* that makes *viral* video ads
series: week 2
brand: Your Name
---
1. I built an *AI* that makes *viral* video ads. [bg: assets/me-laptop.jpg screen=assets/app.png at=412,700,980,690,990,1100,405,1120]
2. ...
```

- Each line's whole caption is on screen at once, each word popping as
  it's said, and the first one from frame 0, so the first frame is the
  cover. `*Words*` in asterisks stay yellow (they aren't spoken).
- `series:` and `brand:` put a tag in each top corner.
- `screen=` and `at=` put your screenshot on the laptop or phone in your
  own photo, from the screen's four corners in the photo's pixels
  (clockwise from the top left). Any photo of you holding the device
  works; the screen's content gets replaced.
- No photo of you? The mascot holds your product instead:
  `[shot: mascot do=talk prop=laptop src=assets/app.png]` with
  `style: 3d`.
- A filmed take gets the same look with `cut.js ... --bold`.

### A montage from your clips (the default)

The `clip-montage` skill edits the phone videos you or a client film (a
home or a room, a product, a shop or a restaurant, an event) into a
vertical montage, with your own music and voiceover if you have them.
It's free: everything renders locally, and nothing is generated. It's
the default for any montage. With only photos, it asks for a few clips
first and otherwise hands over to `montage-video` (below).

```
node montage.js inspect ~/Desktop/taco-night --slug taco-night
node montage.js frames state/videos/assets/taco-night-02.mp4 --every 1
node montage.js state/videos/2026-10-23-taco-night.md
```

- **inspect** copies every clip in with its picture and sound as they
  are and its metadata stripped (a phone's GPS location included), and
  prints each one's length, shape, and whether it has sound.
- **frames --every 1** lays out a frame every second with its time, and
  prints when the sound is loud, so the skill can pick each clip's best
  moment without playing it.
- **The script** gives each shot its stretch, `[from: 3.5] [to: 6.5]`,
  fitted to the beat. A long clip can give several shots. `[sound]` keeps
  a clip's own sound in sync (someone talking, the sizzle) with the music
  ducked under it, and a `[say: ...]` on it captions the exact words.
  `[focus: 30%,50%]` keeps that point in frame when a landscape clip is
  cut to 9:16. A slow `push-in` on top of a clip works too.
- **Your music:** `music: assets/track.mp3` (its beat is read and the
  cuts land on it), the client's sound, or `none` to add a trending sound
  in the app.
- **Your voiceover:** `voiceover: assets/vo.m4a`, one recording (a voice
  memo is fine) under the whole video, with `voiceover-text:` (its words)
  for synced captions. The music ducks under it, and the shots stretch to
  cover it.
- **Long clips** render fast: only the stretch a shot plays is turned
  into frames, not the whole file.

### A montage from your photos (property and product)

The `montage-video` skill makes a vertical reel from a client's own photos
when there are no clips: a home for sale or rent, a single room, or a
product. `montage.js` does the work in two steps:

```
node montage.js inspect ~/Desktop/maple-photos --slug maple
node montage.js state/videos/2026-10-21-maple.md
```

- **inspect** copies every photo and clip into `state/videos/assets/`
  (`maple-01.jpg`, ...). Photos come out upright, sized for the frame,
  and with their metadata stripped, a phone photo's GPS location
  included. iPhone HEIC photos are converted when the machine has a
  converter. It prints each file's size, shape, and brightness, flags
  dark or low-resolution ones, and writes a numbered contact sheet and a
  starter script.
- **The script** lists one shot per line: the file, a label, and tags
  for the move (`pan-left`, `push-in focus=40%,55%`, ...), the fit
  (`contain` shows a whole photo, `card` sets a packshot on a soft
  backdrop), a voiceover line (`[say: ...]`), a hold, a transition, a
  "Virtually staged" badge, a callout, or a before/after wipe. The
  frontmatter sets the hook, a status sticker, the price, the specs, the
  CTA, the music (the client's sound, a genre, or a licensed track), the
  voice (none, a free local voice, or your recordings), and the pace or
  target length. Every option is listed at the top of
  `scripts/video/montage.js`.
- **The page** shows the photos bright, without the darkening other
  templates use behind text. Wide photos pan across the 9:16 frame so the
  whole room is seen.
- **3D moves:** with the depth model set up (`npm install
  @huggingface/transformers`, about 100 MB downloaded on first use),
  `depth.js` estimates how far each point of a photo is (Depth Anything V2
  Small, an open model that runs locally), and the page draws the photo
  from it with WebGL. Near things move more than far ones, so the camera
  seems to circle the room (`orbit`), move into it (`dolly-in`), or lift
  (`rise`) rather than slide over a flat picture. The moves stay small,
  since a photo shows one viewpoint: nothing behind the sofa or around a
  corner. A depth map from any other app works too (`[depth: file]`).
  Without the model, shots move flat. 3D shots render about three times
  slower on a machine without a graphics card. Every cut lands on the music's beat (a licensed
  track's beats are read with `beats.js`), or follows the voice. A shot is
  held longer when its label needs time to be read. It ends on an end
  card with the client's logo, handle, contact lines, and fine print.
  Render it like any page.
- **AI camera moves:** with a connected video model (Figma Weave's
  Seedance or Veo, or Higgsfield), each photo becomes a short clip where
  the camera really moves, orbiting or gliding into the room from new
  angles. Generating spends the user's credits on a paid plan (Weave runs
  video models only on paid Figma plans), so the skill offers it only
  when you say you have one, and quotes each run for your approval first.
  Filmed clips (`clip-montage`) give real camera moves for free. `montage.js frames <clip> --photo <photo>` puts the
  clip's frames beside the photo, so any clip that changed the room is
  caught and dropped. AI shots carry an "AI-animated" badge (`[ai]`).
- **Clients:** each one has a profile in `state/clients/<slug>.md` with
  their colors, font, logo, sound, contact details, and the preferences
  they've asked for (`state/clients/README.md`). A script picks one with
  `client: <slug>`. Profiles are kept out of git.
- **Editing:** change the script and run `montage.js` again. The timing is
  recomputed, so "faster", "kitchen first", or "different music" is a
  one-line edit. Render each round as a new version (`maple-v2.mp4`).

Both skills' shot order, filming tips, moves, music by mood, and the
wording rules for property ads (describe the home, never who should live
there) are in [`references/montage-guide.md`](../references/montage-guide.md).

### How a page works

A comment at the top of `promo.html` documents how a page works: CSS
animations timed with `animation-delay` (the renderer seeks every one
frame by frame, so output is frame-exact on any machine), the background
slots, the music settings on `<body>`, and `data-sfx` cues. A page that
draws its own frames defines `window.renderFrame(t)`, which the renderer
calls with each frame's time (see `3d.html` and `pixel.html`). The
templates are built from one shared base by `templates/build.py` (the
everyday ones are defined in `templates/fyp.py`, and the drawn ones in
`scene3d.py` and `pixel.py`); edit those and run `python3 build.py`
rather than hand-editing 32 copies.

The skill saves its pages and renders under `state/videos/`, with media in
`state/videos/assets/`. Rendered MP4s and downloaded media are git-ignored;
`CREDITS.md` is kept.
