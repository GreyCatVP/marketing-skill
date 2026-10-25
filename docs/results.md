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

_The first full run is in progress; its numbers go here._

To run it yourself (each run is a paid model call; this suite is about
42 runs plus the judge's):

```
claude plugin eval . --runs 3 --trust-plugin --model claude-sonnet-5-5 \
  --judge-model claude-haiku-5-5 --threshold 0.67 --max-cost-usd 15 \
  --json evals/results/latest.json
python3 scripts/results.py --eval evals/results/latest.json
```

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
