# Video setup: what to ask before making videos

A new user doesn't know what this plugin can do with what they already
have: a character, a video they like, a paid tool, their own voice. Ask,
so the first video uses it, and save the answers under **Video Setup** in
`references/brand-voice.md` so they're asked once, not every time.

`/marketing-skill:marketing-setup` asks these when the user's content
types include video. `short-form-video` (and `clip-montage` for the
questions that apply to a montage) asks whichever are still unanswered,
or that this request changes, before writing a script: in one short
message, numbered, with the default for each, so "defaults" is a whole
answer. Never block on them; a skipped question takes its default.

## The questions

1. **Where will the videos be posted?** It decides the shape.
   - TikTok, Reels, Shorts: 9:16 (the default).
   - YouTube (a regular video), Reddit, LinkedIn, X, a website, or a
     README: 16:9 (`format: landscape`).
   - Both: one script, both cuts (compose it twice, once with
     `--format landscape`).
2. **Who presents the videos?**
   - **You, on camera** (free): they film a phone take; `cut.js` cuts
     the pauses, captions their exact words, and adds the look and music.
     A photo of them holding their laptop or phone makes the bold cover.
   - **Your own character** (free, local): their mascot or avatar as a
     rigged 3D file (`.glb`, a VRoid `.vrm`, or Mixamo's `.fbx`). Save its path as
     `Character:` under Visual Identity; it takes the robot's place in
     every 3D video. A character that's only a drawing or a logo can't be
     animated locally: offer to have it modeled and rigged (Mixamo rigs a
     humanoid model for free), the robot in their colors meanwhile, or a
     paid video model (question 4).
   - **The plugin's robot** (free, local): a 3D mascot in the brand's
     colors that walks, talks, points at the product, and lip-syncs.
   - **A realistic AI avatar** (paid): a lifelike presenter from HeyGen,
     Synthesia, D-ID, Hedra, or similar (question 4). Its talking clip
     goes through `cut.js` like a filmed take. A stock avatar, or their own
     likeness, never a real person who didn't agree; labeled as AI when
     posted.
   - **No presenter** (free, local): the product's own screens (the
     product demo look), or words over photos, clips, or animation.
3. **Is there a video whose style you want to follow?** Their own past
   video or anyone's. Ask for the file (a link alone isn't enough: don't
   download from TikTok, Instagram, or YouTube against their terms; the
   user can save their own videos or screen-record one). Save its path as
   `Style reference:`; `scripts/video/reference.js` reads how it's edited
   when a video is made, and the new video copies the editing, never the
   content.
4. **Which paid tools do you have, if any?** List what they name, so it's
   offered when it fits, and note that having an account isn't the same
   as it being connected to this session (`short-form-video` step 3
   checks):
   - video models: Higgsfield, Figma Weave, Runway, Pika, Kling, Veo;
   - AI avatars: HeyGen, Synthesia, D-ID, Hedra;
   - voices: ElevenLabs (a cloned voice only of the user, or someone who
     agreed);
   - music: Epidemic Sound, Artlist, Uppbeat, Musicbed (a licensed track
     replaces the generated soundtrack; keep its license and credit
     line);
   - stock: a Pexels or Pixabay key (stock video clips, not just photos);
   - editing: Canva Pro, CapCut Pro.
   Every one of these spends the user's credits or plan: never use one
   without asking first for that video, with the cost when the tool
   gives one.
5. **Whose voice?** The free local AI voice (Kokoro, a few to pick from),
   their own recordings (one file per line), or a paid or cloned voice
   from question 4.

## Saving the answers

Under `## Video Setup` in `references/brand-voice.md`, replacing the
placeholder:

```
- Posted to: TikTok, Reels, Shorts (9:16); Reddit (16:9)
- Presenter: own character (see Character under Visual Identity)
- Style reference: /Users/me/Videos/launch-we-like.mp4
- Paid tools: HeyGen (avatars), Epidemic Sound (music)
- Voice: Kokoro af_heart
```

A skipped question stays out of the list. The character's path goes under
Visual Identity as `Character:` (so `brand.js` puts it in every 3D video),
not here. Paths are saved as the user gives them; an absolute path is the
safest.

## Defaults, when they skip

Posted to TikTok, Reels, and Shorts (9:16); no presenter chosen, so the
look fits the video type (`video-types.md`) and a 3D video gets the
robot; no reference; no paid tools; the free local voice.

## Before using an answer

- **A character file:** check it exists and ends in `.glb`, `.vrm`, or
  `.fbx`; ask
  that it's theirs (made, commissioned, or licensed for this use), never a
  famous studio's or game's character.
- **A reference video:** check it exists; run `reference.js` on it, look
  at its sheets, and say in a line what's being matched.
- **A paid tool:** check it's connected this session; if not, say how to
  connect it (`short-form-video` step 3) and offer the free way meanwhile.
- **A real person** (on camera, as an avatar, or as a voice): only the
  user or someone who agreed; never make one up.
