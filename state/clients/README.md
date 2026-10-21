# Client profiles

One file per client you make videos for, used by `montage-video` (and
`scripts/video/montage.js` through a script's `client:` line). A profile
holds that client's look, sound, and contact details, so every video for
them looks and sounds like their brand, not yours. Your own business stays
in `references/brand-voice.md`.

Everything in this folder except this README is kept out of git
(`.gitignore`), because profiles hold people's phone numbers and logos.
Back the folder up yourself if you need to.

Save a profile as `state/clients/<slug>.md` (the slug is what scripts use:
`client: acme-realty`), and the client's logo as
`state/clients/<slug>/logo.png`. The skill writes both the first time you
make a video for someone. To edit one by hand, keep the section headings
as they are:

```
# Acme Realty (Jane Doe)

## Contact
- Name: Jane Doe
- Business: Acme Realty
- Phone: (555) 010-0000
- Website: acmerealty.com
- Fine print: Acme Realty · DRE #01234567 · Equal Housing Opportunity

## Visual Identity
- Accent: #1e5bb8
- Background: #0d1424
- Text: #f5f7ff
- Font: Montserrat
- Logo: state/clients/acme-realty/logo.png
- Handle: @janedoe.homes

## Sonic Identity
- Genre: acoustic
- Tempo: 100 BPM
- Key: G major
- Energy: 2 (of 5)
- Hook: 1 3 5 6 | 5 3 2 -

## Notes
- Never show the price on screen; it goes in the caption.
- Likes calm music and slow pans.
```

- **Contact:** shown on the end card under the logo and handle: the name
  and business on one line, the phone and website (or an `Email:`) on the
  next, and the fine print small below them. Leave out any line the client
  doesn't want shown.
- **Visual Identity** and **Sonic Identity:** the same fields as the
  sections of the same name in `references/brand-voice.md`. `brand.js`
  and the renderer read them the same way, and `references/sound-guide.md`
  explains the sound fields. A section that's missing falls back to the
  template's default look or sound, never to your own brand's.
- **Notes:** what this client has asked for, written by the skill when
  they say something that should hold for later videos, and read before
  each new one.
