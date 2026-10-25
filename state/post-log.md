<!-- MARKETING-SKILL:POST-LOG -->
# Post Log

> One row per community or text post that went out (Reddit, Hacker News,
> dev.to, Indie Hackers, Product Hunt, LinkedIn, X, and so on), with how it
> did, so "does this work?" has an answer from real posts rather than
> general advice. Videos go in `state/video-log.md` instead.
> `community-post-generator` and `publish-pipeline` add a row when a post
> goes out (or when you tell them one did), and the numbers are filled in
> by `scripts/publish_direct.py --metrics --log` (Reddit and dev.to) or
> pasted from the platform. Safe to hand-edit: add a row, correct a
> number, delete a test.
>
> **How the skills use it.** `scripts/results.py` reads this file and
> prints the numbers: how many posts went out where, how many were
> removed, and the median score and comments, split by the Go/No-Go
> verdict they were posted under. Skills quote that output rather than
> judging the table by eye, and any group of fewer than 5 posts is "too
> few to tell", never ranked.
>
> **Columns.** `Where` is the community: `r/buildinpublic`, `Show HN`,
> `dev.to #showdev`, a Discord channel. `Post` is a short label for
> recognizing it later (the title, shortened). `Skill` is the skill that
> drafted it, or `manual`. `Verdict` is the Go/No-Go it was posted under:
> `Go`, `Go (hedged)` for a Go resting on secondary or user-supplied
> sources, `No-Go` if it went out anyway, or blank. `Link / ID` is the
> post's URL or platform ID (the `Posted:` line `publish_direct.py` prints).
> `Removed` is `no`, or who removed it: `moderator`, `automod`, `reddit`
> (site-wide spam filter), or `deleted` (by you). `Score` is upvotes (or
> reactions on dev.to), `Ratio` Reddit's upvote ratio, `Views` where the
> platform shows them. Leave a cell blank when the platform doesn't report
> it, never guess. Escape `|` as `\|` and keep each cell to one line.

| Posted | Platform | Where | Post | Skill | Verdict | Link / ID | Removed | Score | Ratio | Comments | Views | Updated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
