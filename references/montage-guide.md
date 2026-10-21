# Montage guide

How `montage-video` turns a client's photos into a montage: which shot
goes first, how many fit, how each one moves, what music suits it, and
how to word it. The skill reads this file in its steps 5 to 7. Edit it
like `brand-voice.md` if your clients' taste differs.

## Length and number of shots

| Length | Shots | Each shot | Good for |
|---|---|---|---|
| ~15s | 6–8 | about 2s | A teaser, "just listed", a single product, Stories |
| ~30s | 10–14 | 2–2.5s | The default listing or product reel |
| ~60s | 18–24 | 2.5–3s | A full tour, a luxury home, a product with several uses |

- Fewer, better photos beat every photo. A viewer remembers the three
  best rooms, not the hallway.
- Under about 1.5s a shot can't be taken in, and over about 4s it drags
  (`montage.js` warns at both ends). Give a hero shot, the view, or the
  best room a longer hold (`[hold: 2 bars]`) rather than slowing them all.
- A label needs time to be read, about four words a second. `montage.js`
  holds a shot longer when its text needs it.

## Property: the order

1. **The hook shot.** The strongest image, usually the front exterior at
   its best angle, or the single most striking room or view when the
   front is plain. The hook text and any status ("just listed", "open
   house sat 1–4") go on it.
2. **The way in:** the entry or the first view inside.
3. **Living spaces:** living room, then kitchen, then dining. The kitchen
   is usually the second-strongest shot.
4. **The main bedroom, then its bathroom.**
5. **Other bedrooms and bathrooms.** One or two is enough. Skip
   near-duplicates.
6. **Outdoor space or the view:** backyard, balcony, pool, the street.
7. **Something special:** a fireplace, an office, a renovated detail.
8. **The close:** a twilight exterior or the best shot again, with the
   price, specs, and CTA (`[facts]`, or the last shot).

For a rental or a vacation stay, swap the price for the nightly or
monthly rate and lead with what guests book for (the view, the pool).

## Product: the order

1. **The hero:** the product, clean, at its best angle. A packshot on
   white looks best with `[fit: card]`.
2. **The problem, or the moment of use.**
3. **Details:** texture, materials, the label, a button, a seam, each a
   push-in on that spot, or a `[callout: x%,y% ...]`.
4. **In use, or in its setting** (lifestyle photos).
5. **Options:** colors, sizes, scale next to a hand or an everyday object.
6. **What's in the box,** if that sells it.
7. **The offer:** price, any real discount, and the CTA.

## Moves

`montage.js` picks a move for each shot that doesn't name one. Override
it with `[move: ...]` when the photo asks for something else.

- **Wide room (landscape photo):** a slow pan toward the focal point
  (`pan-left` / `pan-right`). A 3:2 photo in a 9:16 frame shows only
  about 40% of its width at once, so a pan is how the viewer sees the
  whole room. Set `focus=` to the part that matters, and the pan centers
  on it.
- **Tall space** (stairs, a vaulted ceiling, a chandelier): `pan-up`.
- **Detail** (a faucet, a fireplace, a product label): `push-in` with
  `focus=` on the detail.
- **Exterior or reveal:** `pull-out` from the front door or the view.
- **Product on white:** `[fit: card]` with a gentle `push-in`.
- **A photo that must be seen whole** (a floor plan, a group shot):
  `[fit: contain]`, with `move: none` or a slow push-in.
- **Video clips** keep their own motion (`none`).
- Consecutive shots move in different directions. A pan never moves
  faster than about a sixth of the frame a second, since faster reads as
  a shaky phone.

## Transitions

- **fade** (the default): calm, for homes and premium products.
- **cut:** on the beat, energetic. Product reels, younger brands.
- **slide / wipe:** walking from one room to the next.
- **zoom:** stepping into a space or onto a product.
- **flash:** a reveal or a "sold".
Use one transition for most of the video and a different one only where
it means something (the reveal, the before/after).

## Music by mood

The client's saved Sonic Identity comes first. Change it for one video
only when the property or product calls for it, and say so.

| Property or product | Genre | Tempo | Shots |
|---|---|---|---|
| Luxury home, high-end product | `cinematic` or `calm` | 70–90 BPM | Longer holds, fades |
| Family home, suburban listing | `acoustic` | 90–105 BPM | Fades and slides |
| City condo, modern build | `house` or `lofi` | 110–124 BPM | Cuts on the bar |
| Vacation rental | `acoustic` or `funk` | 100–115 BPM | Slides, zooms |
| Tech or gadget | `tech` | 115–125 BPM | Cuts, zooms |
| Fashion, beauty | `pop` or `house` | 110–124 BPM | Cuts on the beat |
| Food and drink | `acoustic` or `funk` | 95–112 BPM | Slides |

Longer than about 45 seconds, the generated music repeats itself, so use
a licensed track (`media.js search --type music`) instead. A track's beat
is read with `beats.js`, so the cuts land on it.

## Voiceover

- One sentence per shot, 8 to 14 words, about what's on screen right
  then. Don't read the label aloud. Add what the photo can't show ("The
  kitchen was redone last year").
- Every fact in the voiceover comes from the user or the client.
- Music-only is often better for a listing: most people watch muted, and
  the labels carry the facts. Offer a voice for a tour, a story, or a
  product that needs explaining.
- The free local voice speaks English. For another language, the user
  records each line in their own voice (`recordings:`), and captions
  follow their words.

## Labels and hooks

- A label names the space or the feature in 1 to 4 words ("Chef's
  kitchen"), with an optional second line for one detail ("quartz island
  · gas range").
- Hooks for property: the news ("just listed in maple grove"), the
  standout ("a backyard you won't believe for under $700k"), or a question
  ("would you live here?"). For a product: the result, the problem, or
  the reveal. See `hooks.md`.
- Specs read best as short chips: `4 bd · 3 ba · 2,450 sq ft`.

## Wording for property

US fair-housing rules apply to every ad for a home, a reel included.
Describe the property and the area. Never describe who should live
there.

- **Say:** "three bedrooms", "fenced yard", "single-level living", "near
  the park and the train", "quiet street", "walk-in shower".
- **Don't say:** "perfect for families", "ideal for young
  professionals", "great for retirees", "bachelor pad", "exclusive
  neighborhood", "safe area", or anything about race, color, religion,
  national origin, sex, disability, or family status, even as a
  compliment.
- An accessibility feature is a feature ("step-free entry", "grab bars
  in the main bath"). Say what it is, not who it's for.
- Many states and brokerages require the brokerage name or a license
  number on ads, and many agents show "Equal Housing Opportunity". These
  go in the client's `Fine print`, shown on the end card. Ask; don't
  guess.

## Staged and edited photos

- Color, exposure, white balance, and straightening are fine.
- Virtual staging (furniture added by software) is allowed in most
  places only when it's disclosed. Every virtually staged photo gets the
  `[staged]` badge, and the caption says the photos include virtual
  staging.
- Never remove a defect (a crack, a power line, a neighbor's wall), add a
  feature, or replace the sky or view in a way that changes what a buyer
  would see in person.
- AI-animated clips of a property (from a connected video model) can
  change details. Check every frame against the photo, and drop any clip
  that changes the property.

## Photos: rights and privacy

- Use photos the client owns, or the listing photographer's photos
  licensed to the client. Never pull photos from a listing site or
  another agent's listing.
- `montage.js inspect` strips each photo's metadata, a phone photo's GPS
  location included, from the copies it makes.
- Leave out photos that show a recognizable person who didn't agree to
  appear, or the occupants' personal items (family photos, mail,
  documents, a car's plate).
