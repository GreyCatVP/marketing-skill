# Results

What there is to show for "does it work?", and how each number was
made. Nothing here is rounded up: a check where the plugin makes no
difference stays in the table, and real results start from a handful of
posts.

## Plugin vs plain Claude

`evals/` holds seven cases for Claude Code's
[`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals.md),
which runs each one with the plugin loaded and again without it, and
scores both. The difference is what the plugin adds over Claude on its
own. Each case tests something a skill promises and a grader can check:

| Case | What passes |
|---|---|
| `reddit-nogo` | A subreddit bans self-promotion: it says so and hands over no promo post |
| `reddit-go-saasbuild` | r/saasbuild's rules ask for a lesson, examples, and a feedback question: the post has all three, no em dashes, and the sub's flair |
| `reddit-disclosure` | r/buildinpublic's "Transparency in Tools & Resources": the post says who built it and that it's free |
| `show-hn` | Title, URL, and the maker's first comment, and no asking for upvotes |
| `discord-no-rules` | A Discord server's rules can't be looked up: it asks for them |
| `seo-no-volumes` | No keyword tool connected: no made-up search volumes or difficulty scores |
| `competitor-no-invented` | Only a pricing page to go on: no invented funding, customers, or dates |

All seven run offline: the rules or source text are in the prompt, the
way you'd paste a sidebar.

### The latest run

2026-10-25, Claude Code 2.1.310, `claude-sonnet-5-5` doing the work and
judging, 3 runs a side, $4.59, after the skill descriptions were
rewritten (see [Does the skill fire?](#does-the-skill-fire)). A score is
the share of a case's checks that passed, averaged over its runs.
"Skill fired" is how many with-plugin runs actually used the skill.

| Case | With plugin | Without | Difference | Skill fired | Runs per side |
|---|---|---|---|---|---|
| competitor-no-invented | 0.00 | 0.67 | -0.67 | 3 of 3 | 3 |
| discord-no-rules | 1.00 | 0.00 | +1.00 | 3 of 3 | 3 |
| reddit-disclosure | 1.00 | 1.00 | +0.00 | 3 of 3 | 3 |
| reddit-go-saasbuild | 1.00 | 1.00 | +0.00 | 3 of 3 | 3 |
| reddit-nogo | 1.00 | 0.67 | +0.33 | 3 of 3 | 3 |
| seo-no-volumes | 1.00 | 1.00 | +0.00 | 3 of 3 | 3 |
| show-hn | 1.00 | 0.83 | +0.17 | 3 of 3 | 3 |

What it shows:

- **The skill fired in all 21 with-plugin runs**, up from 15 of 21 on
  the old descriptions, so every row now measures the skill.
- **One clear win: Discord.** Plain Claude wrote a ready-to-send post
  all 3 times without knowing the server's rules; with the plugin it
  asked for them all 3 times.
- **Two small leads, one run each.** One plain-Claude No-Go reply refused
  the sub and then wrote a promo for other subreddits whose rules it
  hadn't seen; one plain-Claude Show HN didn't have the Show HN shape (a
  "Show HN:" title, a URL, and a separate first comment). With 3 runs a side, one run is 0.33 (or 0.17 on a
  two-check case).
- **Three ties.** Plain Claude also got the r/buildinpublic disclosure,
  the r/saasbuild post, and an SEO brief with no made-up volumes right.
- **One loss: the battlecard.** Now that `competitor-research` fires,
  its battlecards fail the "nothing that isn't on the page" check all 3
  times. Asked why, the judge pointed at the skill's own comparison
  table: it marks the cheaper plans "No" for approvals and an API, when
  the page only says the top plan adds them (the skill's own "Not
  listed" was the honest label), and it calls Acme's focus "split"
  between freelancers and studios. Small, but exactly what the check is
  for, and the more structured the brief, the more of these it makes.
  The fix is in the skill: mark something absent only when the source
  says so.

The raw results, every judged reply included:
[this run](results-data/eval-2026-10-25-new-descriptions.json), and the
run on the old descriptions the same day
([results-data/eval-2026-10-25-old-descriptions.json](results-data/eval-2026-10-25-old-descriptions.json),
skill fired 15 of 21, mean difference +0.29). The battlecard row there
read +0.67 only because the skill never fired.

A run before both is left out: two of its regex checks were written
with an inline `(?i)` flag the eval's JavaScript regexes don't accept,
so they failed on every run of both sides, and its cheaper judge model
(`claude-haiku-5-5`) failed one with-plugin draft that met the check as
written. Both were fixed before the runs above.

To run it yourself (each run is a paid model call; this suite is 42 runs
plus the judge's):

```
claude plugin eval . --runs 3 -j 4 --trust-plugin --model claude-sonnet-5-5 \
  --judge-model claude-sonnet-5-5 --threshold 0.67 --max-cost-usd 15 \
  --json evals/results/latest.json
python3 scripts/results.py --eval evals/results/latest.json
```

## Does the skill fire?

The table above found that Claude often answers on its own instead of
using the skill, and whatever a skill adds only counts when it fires.
[`trigger-evals/`](../trigger-evals) measures that alone: 23 requests
run with the whole plugin loaded, so all 14 skills compete for them.

- **18 should fire a skill**, at least one per skill: requests that look
  easy enough for Claude to answer by itself (the subreddit's rules
  already pasted, only a pricing page and no web access, "turn this into
  a linkedin post: <a paragraph>").
- **5 near misses should fire none**: a README typo, a question about
  drip vs nurture emails, a follow-up to an existing client, a Python
  fix, and a LinkedIn post (not `community-post-generator`'s job).

Each runs 3 times with `claude plugin eval . --eval-dir trigger-evals
--ablation none`; a run passes when the right skill fires (or, for a
near miss, none does).

| Case | Before | After |
|---|---|---|
| fire-ad-copy | 3 of 3 | 3 of 3 |
| fire-calendar | 3 of 3 | 3 of 3 |
| fire-clip-montage | 3 of 3 | 3 of 3 |
| fire-community-discord | 3 of 3 | 3 of 3 |
| fire-community-nogo | 0 of 3 | 3 of 3 |
| fire-community-product-hunt | 3 of 3 | 3 of 3 |
| fire-community-sideproject | 3 of 3 | 3 of 3 |
| fire-competitor-battlecard | 0 of 3 | 3 of 3 |
| fire-competitor-quick | 2 of 3 | 3 of 3 |
| fire-email-outreach | 3 of 3 | 3 of 3 |
| fire-email-sequence | 3 of 3 | 3 of 3 |
| fire-full-pipeline | 3 of 3 | 3 of 3 |
| fire-montage-video | 3 of 3 | 3 of 3 |
| fire-publish | 3 of 3 | 3 of 3 |
| fire-repurposer | 0 of 3 | 3 of 3 |
| fire-seo | 3 of 3 | 3 of 3 |
| fire-short-form-video | 3 of 3 | 3 of 3 |
| fire-visual-brief | 1 of 3 | 3 of 3 |
| nofire-client-followup | 3 of 3 | 3 of 3 |
| nofire-drip-question | 3 of 3 | 3 of 3 |
| nofire-linkedin-not-community | 3 of 3 | 3 of 3 |
| nofire-python-ffprobe | 3 of 3 | 3 of 3 |
| nofire-readme-typo | 3 of 3 | 3 of 3 |

All runs: 57 of 69 before, 69 of 69 after. The right skill fired in 42 of
54 runs before and 54 of 54 after, and no near miss fired a skill either
time. Both runs: 2026-10-25, `claude-sonnet-5-5`, about $6 each. Raw
results: [before](results-data/trigger-2026-10-25-before.json),
[after](results-data/trigger-2026-10-25-after.json).

What changed between the two is only the skills' descriptions, the text
Claude reads to decide whether to use one:

- **Why to use it even when it looks easy.** The misses were all requests
  Claude felt it could answer itself. Each description now says when the
  skill is still worth it: "even when they pasted the rules or the post
  looks obvious", "even with no web access and only a pasted page".
- **Half the length, trigger first.** Claude Code fits every installed
  skill's description into about 1% of the context window and, past
  that, drops the least-used skills' descriptions and keeps only their
  names; a session with 280 skills had 222 down to their names. The 14
  descriptions went from 8,265 characters to 4,424, with "Use whenever"
  in the first 200 characters. `scripts/ci/lint_repo.py` now holds them
  to that.

Read it with care: the descriptions were rewritten after seeing which
requests missed, so the four cases that went from 0 or 1 to 3 are the
ones they were aimed at, not a held-out test. The cases that already
fired, and the near misses, are the check that nothing else got worse.
3 runs a case is small.

## Real posts

The author's own launch posts, logged in
[`results-data/post-log.md`](results-data/post-log.md) and summarized
with `python3 scripts/results.py --log-dir docs/results-data`.

_Not logged yet._ Three posts and one launch video are a handful, not
proof: they show what the numbers look like, not that the plugin works.

## What's untested

The advice built into the skills is common practice, not something this
project has measured: the hook patterns (`references/hooks.md`), the
70/20/10 mix of evergreen formats, trends, and experiments
(`references/fyp-formats.md`), the posting-time windows in
`short-form-video`, the outreach cadence and send times
(`references/outreach-strategy.md`), and the mix levels
(`references/sound-guide.md`). Once your own logs have enough rows,
`scripts/results.py` tells you what works on your account, and the skills
steer by that instead.
