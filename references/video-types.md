# Marketing video types

A working catalog of the marketing video types `short-form-video` can
plan, and how each one actually gets made as a 9:16 short (TikTok,
Instagram Reels, YouTube Shorts). The skill reads this file in its scope
and script steps. Edit it like `brand-voice.md` if your mix differs.

For a longer survey of the formats, see Sparkhouse's
[22 Types of Video Content for Marketing](https://www.thesparkhouse.com/blog/22-types-of-video-content-for-marketing).

## How each type gets made

- **Render:** `scripts/video/render.js` makes it from text alone, as motion
  graphics (kinetic text, shapes, UI mockups) with an original soundtrack.
- **Narrate:** a voiceover over one background per line, with captions
  synced to the voice (`narrated.html`, built from a script by
  `scripts/video/compose.js`). The voice is the user's own takes or a free
  generated one.
- **Animate:** the same narrated script drawn as animation instead of over
  photos: the brand's 3D mascot presenting in its colors (`3d.html`) or a
  pixel-art game with chiptune music (`pixel.html`), both made by
  `compose.js` with `style: 3d` or `style: pixel`. Free and local. Other
  styles (cartoon, anime, claymation, the user's own character design)
  are Generate.
- **Render + your assets:** renderable, but only with real material from
  you, such as screenshots, photos, a logo, a customer's actual words, or
  real numbers. The skill asks for these and never invents them.
- **Generate:** an AI video tool (Higgsfield, Figma Weave) can produce
  footage-style shots. This spends that tool's credits.
- **Film:** needs real footage of real people or places. The skill gives
  you a phone shot list, filming tips, and edit notes. Once you've filmed
  a talking-head take, `scripts/video/cut.js` cuts out the pauses and
  makes the finished video from it: your clip with its own sound,
  captions, the hook, your music, and your end card.
- **Cut-down:** a long-form format. The short is a promo or a highlight of
  it, not the thing itself.
- **Montage:** the user's own clips (or photos) of a place, a product,
  or an event, cut on the beat, with labels, facts, a clip's own sound or
  a voiceover, and a contact end card (`montage.html`, built by
  `scripts/video/montage.js`; the `clip-montage` skill runs it for clips,
  `montage-video` for photos).

Template names refer to `scripts/video/templates/`.

## Picking a type by goal

| Goal | Start with |
|---|---|
| Get discovered / build awareness | Ad, educational tips, brand profile, social/trend (`fyp-formats.md`) |
| Explain what you do | Explainer, product demo, how-to |
| Answer objections | FAQ, myth vs fact, comparison |
| Build trust before a purchase | Testimonial, case study, UGC, meet the team |
| Launch something / fill a date | Announcement, event or webinar promo, live promo |
| Humanize the brand | Meet the team, behind the scenes, vlog, brand story |
| Sell a home, a product, or a place from your own clips or photos | Property tour, product showcase, business showcase (below; the `clip-montage` skill, or `montage-video` for photos only) |
| Recap an event or a day | Event recap (below; the `clip-montage` skill) |

When the goal doesn't settle it, offer the user two or three fitting
types with a line on each rather than picking silently.

## The types

Beats are for a 20–45s short. The hook is always the first 1–3 seconds
and has to work with the sound off.

### Ad (paid or organic promo)
- **Goal:** awareness to conversion; the format most likely to be run as a paid ad.
- **Made by:** Render (`promo.html`), or Generate for footage-style shots.
- **Beats:** pain or bold claim → the product as the fix → one proof point → offer → CTA. Show the brand in the first 3 seconds, since many viewers never reach the end.

### Brand / company profile
- **Goal:** awareness; who you are, what you believe, what makes you different.
- **Made by:** Render (`promo.html`), plus your logo and real proof points.
- **Beats:** a belief or problem you exist for → what you do in one line → how you're different → proof (customer count, a known customer) → CTA.

### Brand story / brand film
- **Goal:** emotional connection; the origin or mission story.
- **Made by:** Film or Generate for the full version. Narrate (`narrated.html`) tells it in five spoken lines over atmospheric backgrounds; Render can do a text-only "story in five lines" short.
- **Beats:** the moment it started → the problem you saw → what you did about it → where it is now → the line you want remembered.

### Explainer
- **Goal:** consideration; make the value proposition obvious.
- **Made by:** Narrate (`narrated.html`), Animate (`3d.html` or `pixel.html`), or Render (`promo.html` or `how-to.html`).
- **Beats:** the problem → how it works in three simple steps → the outcome → CTA. One idea per scene, no jargon.

### Animation & motion graphics
- **Goal:** any stage; make abstract or complex ideas concrete.
- **Made by:** Render for kinetic text and UI motion (every template applies), or Animate for a 3D or pixel-art piece, narrated (`3d.html`, with the brand's mascot as the character, or `pixel.html`). Character animation in a particular style (cartoon, anime, claymation) is Generate.
- **Beats:** follow whichever type the animation serves. In pixel art the story maps onto a game: the problem is a boss to beat, the payoff is coins or a level up.

### Product demo
- **Goal:** consideration; show the product doing the job in a real use case.
- **Made by:** Render + your assets (`how-to.html` with real screenshots or screen recordings in the phone frame), or Film (the physical product).
- **Beats:** the job to be done → the product doing it, feature by feature (one per scene) → the result → CTA. Show, don't list.

### Tutorial / how-to
- **Goal:** consideration and retention; teach a specific task.
- **Made by:** Render + your assets (`how-to.html` with real screenshots, or a screen recording of each step in the phone frame).
- **Beats:** "How to X in N steps" → one step per scene, each with the exact tap or click → "Done" → CTA (save it, follow for more).

### Educational / tips
- **Goal:** awareness; useful on its own, so people share and save it.
- **Made by:** Narrate (`narrated.html`, one tip per line), or Render (`promo.html` as a list, or `faq.html`).
- **Beats:** a promise ("3 things I wish I knew about X") → one tip per beat → a payoff line → CTA (follow for more). Tips should be correct and specific; check facts before drafting.

### FAQ
- **Goal:** consideration; answer the question that's blocking a decision.
- **Made by:** Render (`faq.html`), or Film (someone answering on camera).
- **Beats:** the question as a comment bubble → the short answer → two or three supporting points → CTA (ask yours below). Use real questions customers actually ask.

### Myth vs fact / comparison
- **Goal:** consideration; correct a misconception or position against alternatives.
- **Made by:** Render (`faq.html`).
- **Beats:** the myth, struck through → the fact → why it matters → CTA. Never name a competitor unless `brand-voice.md` allows it, and only with claims you can back up.

### Presentation
- **Goal:** consideration; one key insight from a deck or report.
- **Made by:** Render (`promo.html`), or Cut-down from a recorded talk.
- **Beats:** the headline finding → the data behind it → what it means for the viewer → where to get the full deck or report.

### Webinar
- **Goal:** consideration; deep education and lead capture.
- **Made by:** Cut-down. Before the event, render a promo (`announcement.html`); after it, a highlight clip from the recording (Film/existing footage).
- **Beats (promo):** the topic as a question → who's speaking → what you'll learn (three points) → date and time → register CTA.

### Live stream
- **Goal:** engagement; real-time Q&A, launches, events.
- **Made by:** Cut-down. A countdown promo (`announcement.html`) before, a highlight clip after.
- **Beats (promo):** what's happening → why to show up live → date and time → set a reminder.

### Event (promo or recap)
- **Goal:** awareness and attendance; or social proof after the fact.
- **Made by:** Render for the promo (`announcement.html`). Film for the recap.
- **Beats (promo):** the event in one line → who's there → date and place → CTA. **Recap:** the best moment first → three quick highlights → "see you next year".

### Announcement / launch
- **Goal:** awareness spike; something is new, changing, or opening.
- **Made by:** Render (`announcement.html`).
- **Beats:** tease → reveal (the name, big) → what's in it (three features) → when and where → CTA.

### Interview / expert Q&A
- **Goal:** authority; borrow credibility from someone who knows.
- **Made by:** Film. Render can do a pull-quote card (`testimonial.html`) with a real, attributed quote.
- **Beats:** their most surprising line first → who they are → the question → their answer → CTA to the full interview.

### Customer testimonial
- **Goal:** trust at the decision stage.
- **Made by:** Film is strongest. Render + your assets (`testimonial.html`) works with the customer's real quote, name, role, and photo, used with their permission.
- **Beats:** the result in their words → who they are → what it was like before → what changed → CTA.
- **Never** invent, embellish, or "tighten" a quote into words they didn't say, and never use a name, photo, or logo without permission.

### Case study
- **Goal:** decision stage; proof with numbers.
- **Made by:** Render + your assets (`testimonial.html`) with the customer's real numbers.
- **Beats:** the headline result → the customer and their challenge → what they did → the results as counted-up numbers → CTA to the full story. Every number must be real and sourced.

### User-generated content (UGC)
- **Goal:** trust and reach; customers showing it in their own words.
- **Made by:** Film, by customers. You repost it with permission and add a caption; the skill can write the ask and the caption, not the video.
- **Beats:** whatever the creator made. Your caption adds the context and CTA.

### Meet the team
- **Goal:** humanize the brand; trust in who's behind it.
- **Made by:** Render + your assets (`team.html` with real photos, names, and roles), or Film (each person says one line).
- **Beats:** "The people behind X" → one person per beat, with name, role, and one human detail → the group → CTA (we're hiring, or say hi).

### Behind the scenes
- **Goal:** humanize the brand; show the process, people, or culture.
- **Made by:** Film (phone clips). It can't be faked with motion graphics.
- **Beats:** "Here's how X actually gets made" → three to five quick process shots → the finished thing → CTA.

### Vlog / day in the life
- **Goal:** humanize the brand and build a following.
- **Made by:** Film.
- **Beats:** a time-stamped hook ("6:45am, first call with a customer") → four to six moments with on-screen times → a takeaway line.

### Social / trend (everyday posts)
- **Goal:** reach and engagement; the memeable, comment-driven posts that fill a feed between campaigns.
- **Made by:** Render, from 22 templates for the formats that last (POV, nobody / me, expectation vs reality, tier list, this or that, hot take, text-message skit, notifications, storytime, top-5 countdown, and more). Film for a dance or a trend that needs people on camera.
- **Beats:** each format's own, in `fyp-formats.md`, which also covers the weekly mix, rotating formats, and writing the copy in the brand's voice. A trend that's peaking this week is checked in the app before making it; this plugin can't see trends live.

## Made from the user's clips or photos (clip-montage, montage-video)

When the user brings their own clips of a place, a product, or an event,
the `clip-montage` skill makes the video instead of `short-form-video`;
with only photos, `montage-video` does. Their shot order, filming tips,
moves, music, and wording rules are in `montage-guide.md`.

### Property tour / listing video
- **Goal:** showings and inquiries for a home for sale or rent, or bookings for a stay.
- **Made by:** Montage (`montage.html`), from the listing's own clips (a walk-through filmed on a phone) or photos.
- **Beats:** the strongest shot with the hook and any status ("just listed") → the way in → living spaces → main suite → outdoor space or view → the price, specs, and CTA → the agent's contact end card. Describe the home, never who should live there.

### Product showcase
- **Goal:** consideration to purchase, for a physical product.
- **Made by:** Montage (`montage.html`), from the product's own photos and clips; a packshot on white sits on a soft backdrop (`fit: card`).
- **Beats:** the hero shot with the hook → the problem or the moment of use → details and callouts → in use → options → the price, any real offer, and the CTA.

### Business showcase
- **Goal:** visits, bookings, or orders for a shop, a restaurant, a salon, a studio, or a service.
- **Made by:** Montage (`montage.html`), from the business's own clips, with the music ducked under any clip where someone talks (`[sound]`).
- **Beats:** the hero moment with the hook (the dish, the finished cut, the reveal) → the people making it → details up close → the space → customers enjoying it (with their OK) → the CTA (book, visit, order).

### Event recap
- **Goal:** reach after an event, and sign-ups for the next one.
- **Made by:** Montage (`montage.html`), from clips filmed at the event.
- **Beats:** the peak moment with the hook (the crowd, the reveal, the toast) → arriving or setting up → the highlights in order → a speaker's or a guest's line with its own sound → the close (a thank-you, the next date).

## Backgrounds and sound by type (for local renders)

Backgrounds come from stock photos, stock clips, or AI images
(`scripts/video/media.js`, or a connected image tool). Sound comes from the
project's sonic identity in `brand-voice.md` (see `sound-guide.md`).

| Type | Background | Sound |
|---|---|---|
| Ad, brand profile, explainer, educational, presentation | A setting or mood that fits each beat; clips for energy | The identity |
| Narrated (any type told as a voiceover) | One setting per line, the same light and palette throughout | The identity, one energy step lower under the voice |
| Animated in 3D | A shot per line from `3d.html`, lit in the accent color; the user's screenshot on the phone, their logo on the coin | The identity, one energy step lower under the voice |
| Animated in pixel art | A shot per line from `pixel.html`: the problem as a boss, the payoff as coins or a level up | `chiptune`, in the identity's key and hook |
| Product demo, how-to | Real screenshots in the phone frame, over a soft (blurred) setting | The identity |
| FAQ, myth vs fact | One calm setting, blurred, so the text leads | The identity |
| Announcement; event, webinar, or live promo | Bold photos or energetic clips | The identity, energy +1 |
| Testimonial, case study, interview pull-quote | The customer's own photo; otherwise a blurred ambient setting | `calm`, in the identity's key and hook |
| Meet the team | The team's own photos; their real workspace if supplied, otherwise blurred ambient | The identity, or `calm` |
| Brand story (text-led) | Wide, atmospheric settings | The identity |
| Social / trend (everyday posts) | The moment itself (a desk, a coffee, a commute); the person's own clips for day in the life | The format's genre, in the identity's key and hook (`sound-guide.md`) |

Stock and AI images set the scene; they never stand in for a customer, a
team member, the product, or a result.

## Filming notes (for Film types)

When a type needs footage, the skill's Generation Status says so and gives
a phone shot list. For a talking-head take (an FAQ answered on camera, a
founder's story, an interview answer, an on-camera testimonial with the
person's permission), `cut.js` then turns the raw take into the finished
video; for several shots, `clip-montage` edits them into a montage (or
use CapCut or similar).
- Shoot vertical (9:16) at 1080×1920 or higher, in daylight or facing a
  window, with the phone at eye level.
- Record audio close to the speaker (a clip-on mic if possible); viewers
  forgive soft video long before bad sound.
- Get each shot in a few takes of 3–6 seconds, plus a few seconds of
  silence before and after for cutting.
- For one talking-head take, don't trim it yourself: `cut.js` removes the
  pauses and captions it. Pauses longer than about a third of a second
  are cut, so speak naturally and leave clear gaps between thoughts.
- For several shots, `clip-montage` picks each one's moment and cuts it
  on the beat. By hand, in CapCut or similar: cut on the action, add
  captions (most people watch muted), and keep the first second the most
  interesting one.
