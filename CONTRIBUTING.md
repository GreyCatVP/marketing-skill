# Contributing

Thanks for helping out. Fixes, new skills, better references, docs, and
video templates are all welcome.

## Where things go

- **A bug:** open an [issue](https://github.com/marcosmodly/marketing-skill/issues)
  with the skill or script, what you asked for, what happened, and what
  you expected.
- **A question:** ask in
  [Q&A](https://github.com/marcosmodly/marketing-skill/discussions/categories/q-a).
- **Something you made with the skills:** post it in
  [Show and tell](https://github.com/marcosmodly/marketing-skill/discussions/categories/show-and-tell).
- **A change to the code or docs:** open a pull request (below). For a
  new skill or a big change, open an issue first so we can agree on the
  shape before you spend time on it.

## Sending a change

1. Fork the repo and create a branch from `main`.
2. Make your change.
3. Run the checks (next section) and try it in Claude Code.
4. Open a pull request against `main` and fill in the template.

CI runs the same checks on every pull request. If this is your first
contribution, a maintainer has to approve the run before it starts, so
it may wait a little.

## Running the checks

The repo checks need Python 3.12 and nothing else:

```
python3 scripts/ci/lint_repo.py        # skill frontmatter, command size, manifests, paths, links
bash scripts/ci/smoke_publish.sh       # both publish scripts, dry run only, with fake credentials
python3 scripts/video/templates/build.py
git diff --exit-code -- scripts/video/templates   # the built templates must match build.py
```

If you touched anything under `scripts/video/`, also run the template QA
pass. It needs Node 18+ (CI uses 22), ffmpeg, and Playwright:

```
cd scripts/video
npm install
npx playwright install chromium
node check.js --out check-report
```

## Trying your change in Claude Code

Install the plugin from your clone instead of from GitHub:

```
cd marketing-skill && git checkout <your-branch>
claude plugin marketplace add ./
claude plugin install marketing-skill@marketing-skill
```

Then ask for what the skill does, in the words a user would use. The
skills also run in Codex (see [Using with Codex](README.md#using-with-codex)),
so keep anything you write working there too.

## What the repo depends on

The lint checks most of these, but not all.

**Skills**

- One folder per skill: `skills/<name>/SKILL.md`. The frontmatter
  `name` matches the folder name.
- The `description` is under 1024 characters, has no XML or HTML tags,
  and says both what the skill does and the phrases that should trigger
  it. Claude picks a skill by its description, so this is the most
  important line in the file.
- Point at files in the plugin as `${CLAUDE_PLUGIN_ROOT}/references/...`,
  and only at files that exist (`state/` paths are created at runtime and
  are skipped). Codex doesn't fill in that placeholder, so keep the
  "Plugin root" paragraph that every skill has near the top of its steps.
- Read `references/brand-voice.md` before producing output, like the
  other skills do.
- A new skill also needs a row in the README's [Skills](README.md#skills)
  table, and the skill count updated wherever it's written: the top of
  the README, "Using with Codex", "Repo layout", and the descriptions in
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

**Commands**

- Keep each file in `commands/` under 4 KB. Codex only turns commands
  smaller than that into skills.

**Nothing sends without a person approving it**

This is the rule every skill follows, and pull requests that weaken it
won't be merged:

- Skills that draft content write `Planned`, `Drafted`, or
  `Ready for Approval`, never `Approved`. Only `publish-pipeline` marks a
  row `Approved`, and only after a person replies in a live conversation.
  See [Content calendar & approval model](README.md#content-calendar--approval-model).
- `email-outreach` drafts and never sends.
- `publish_webhook.py` and `publish_direct.py` refuse to run without
  `--dry-run` or `--confirmed`. Keep them standard-library only.
- Skills don't make up numbers: no invented search volumes, follower
  counts, or results.

**Video templates**

- The pages in `scripts/video/templates/` are generated. Edit `build.py`
  (or `fyp.py`, `scene3d.py`, `pixel.py`, `drawn.py`, `mascot.py`,
  `demo.py`), run `python3 scripts/video/templates/build.py`, and commit
  the rebuilt pages with your change.

## Keep these out of your pull request

- Your own setup: a filled-in `references/brand-voice.md` or
  `references/outreach-strategy.md`, and your rows in `state/` (the
  content calendar, the outreach log, the video log, queued posts and
  emails). Change these files only when you're changing their template
  for everyone.
- Client profiles in `state/clients/` (they hold people's contact
  details; `.gitignore` already skips them).
- API keys, tokens, webhook URLs, or anything else secret.
- Rendered videos, and music or media you don't have the right to
  redistribute. Stock media that is committed needs its line in the
  folder's `CREDITS.md`.

## Changelog

If users will notice your change, add a bullet to the top section of
[CHANGELOG.md](CHANGELOG.md) saying what it does for them. Leave the
version in `plugin.json` as it is; it's set when a release goes out.

## Commits

Write the subject line as what changed, for example
`seo-brief: ask for the page's URL before researching`. Keep unrelated
changes in separate pull requests.

## License

This project is under the [MIT License](LICENSE). By opening a pull
request, you agree that your contribution is released under the same
license.
