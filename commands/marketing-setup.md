---
description: Asks the 4 setup questions (and, for video, what videos can be made with) and saves the answers to references/brand-voice.md.
allowed-tools: Read, Write
---

# Marketing Skill Setup

Fills in `references/brand-voice.md`, the shared config every skill in
this plugin reads, so priority, audience, and tone are set once. Run it
for first-time setup or to update answers.

**Plugin root:** if `CLAUDE_PLUGIN_ROOT` below is unexpanded (e.g. in
Codex), use the output of `printenv CLAUDE_PLUGIN_ROOT`, else the nearest
folder above this file that contains `references/brand-voice.md`, else
ask the user.

## Process

1. Read `${CLAUDE_PLUGIN_ROOT}/references/brand-voice.md`.
2. If its first line is `<!-- MARKETING-SKILL:CONFIGURED (last updated:
   ...) -->`, show the current Priority Task, Content Types, Target
   Audience, Brand Voice & Tone, and Default Output Format first, and ask
   whether to update everything or just specific fields.
3. Ask these, one at a time (skip any not being updated):
   1. "Which marketing task should this plugin prioritize first?" (e.g.
      weekly newsletters, competitor research, blogs to social posts,
      video, publishing automation)
   2. "What type(s) of content do you want to produce?" (short-form
      video, long-form video scripts, text/social posts, email, images,
      or a mix; this sets the default medium for skills like
      `content-calendar`)
   3. "Who's your target audience, and what tone should content use?"
   4. "What output format do you want by default?" (e.g. hook + bullets
      + CTA, a full long-form draft, a numbered thread)
4. Optionally offer to customize the banned words or formatting
   constraints; if declined, leave the placeholders.
   If their content types include video, also offer a **sonic identity**:
   read `${CLAUDE_PLUGIN_ROOT}/references/sound-guide.md` and propose two
   that fit the audience and tone (genre, tempo, key and mode, energy,
   hook, and one line on why). They can hear previews with that guide's
   `--sample` commands, or at the first render. Save a pick; otherwise
   leave the placeholder. Then offer a **visual identity**: brand colors
   (a website link or a description is enough; you pick the hex values
   for accent, background, and text), a Google Fonts display font, a logo
   file, and the account handle. Save what they give under Visual
   Identity. Then the **video setup** questions in
   `${CLAUDE_PLUGIN_ROOT}/references/video-setup.md` (where they post,
   who presents, a style reference, paid tools, whose voice), one at a
   time, saying what each choice costs; save them under Video Setup, and
   a character file as `Character:` under Visual Identity.
5. Write the answers into the same file. Keep every existing `##`
   heading exactly as it is, replacing only the placeholder text under
   each, so every skill's reads keep working. Replace the first line with
   `<!-- MARKETING-SKILL:CONFIGURED (last updated: YYYY-MM-DD) -->`
   using today's date. A file from before Video Setup existed gets that
   section added at the end.
6. Confirm in one line: `Saved: priority=<...>, content_types=<...>,
   audience=<...>, tone=<...>, format=<...>` (plus `sound=<genre, key,
   hook>`, `look=<accent, font>`, and `video=<presenter, shape>` if
   chosen), and note they can re-run
   this or edit the file.

## Rules

- Ask conversationally, one question at a time.
- Never invent an answer; a skipped question leaves its placeholder.
- Keep the confirmation to one line.
