## What this changes

<!-- What does this pull request do, and which skills, scripts, or docs does it touch? -->

## Why

<!-- The problem it fixes or what it makes possible. Link the issue if there is one. -->

## How I tested it

<!-- What you asked Claude (or Codex) and what came back. Screenshots or a short clip help for video changes. -->

- [ ] `python3 scripts/ci/lint_repo.py` passes
- [ ] `bash scripts/ci/smoke_publish.sh` passes
- [ ] `python3 scripts/video/templates/build.py` leaves `scripts/video/templates` unchanged
- [ ] `node check.js` passes in `scripts/video` (only if this touches `scripts/video/`)
- [ ] Tried it in Claude Code with the plugin installed from my branch

## Checklist

- [ ] Nothing here sends, posts, or marks anything `Approved` without a person approving it in a live conversation
- [ ] No personal setup, `state/` rows, client profiles, credentials, or media I can't redistribute
- [ ] A new skill has its README row and the skill count updated (README and `.claude-plugin/` descriptions)
- [ ] `CHANGELOG.md` has a bullet, if users will notice this change
