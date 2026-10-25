# Publishing

How finished content leaves this plugin: to your own automation through a
webhook, or straight to a platform with your own credentials. Nothing
sends without an explicit `--confirmed` after a human has seen it; see
[the approval model](../README.md#content-calendar--approval-model).

## Automation handoff

`publish-pipeline` and `full-pipeline` send a JSON payload to your own
automation (n8n, Make, or anything else with an incoming webhook) via
`scripts/publish_webhook.py`. Point it at your webhook:

```
export MARKETING_WEBHOOK_URL="https://your-n8n-or-make-webhook-url"
```

or pass `--url` directly. The script refuses to run at all unless you
pass exactly one of `--dry-run` (prints the exact request, sends nothing)
or `--confirmed` (actually sends) — there's no default-sends behavior:

```
echo '{"hello": "world"}' | python3 scripts/publish_webhook.py --dry-run
```

If you have a **Make** MCP connector connected in your session (tools
like `scenarios_run`), `publish-pipeline` can call it directly instead of
the webhook script — mention that preference when the skill asks how to
send.

## Posting directly to a platform (optional, needs your own credentials)

`scripts/publish_direct.py` posts straight to LinkedIn, X, Meta (Facebook
Page), Reddit, Discord, Slack, Telegram, dev.to, YouTube (Shorts),
Instagram (Reels), or TikTok instead of going through your own automation
— `python3 scripts/publish_direct.py --help`
lists what each platform needs. **Read the script's module docstring
before using it.** It was written without a connected account or live
credentials for any of these platforms to test against, so it's
best-effort against each platform's last publicly documented API, not a
verified integration — confirm the endpoint is still current against that
platform's own developer docs (developers.linkedin.com, developer.x.com,
developers.facebook.com, Reddit's own API docs, Discord's own API docs,
Slack's own API docs, Telegram's own Bot API docs at
core.telegram.org/bots/api, and developers.forem.com/api for dev.to),
confirm you actually have write-access API scope (X in particular gates
this behind a paid tier, Reddit closed instant self-service app
registration in late 2025 for a manual approval queue — existing approved
apps still work, and Slack may need a Workspace Owner/Admin to approve the
app a webhook requires — see below), and do one manual `--confirmed` test
post yourself before trusting it in anything automated. The first eight
platforms (LinkedIn/X/Meta/Reddit/Discord/Slack/Telegram/dev.to) are
text-only — no media attachments, and a plain text-only Instagram post
isn't supported at all since Instagram has no such endpoint. YouTube,
Instagram, and TikTok are the three video exceptions, added specifically
for short-form video from the `short-form-video` skill — see "Posting to
YouTube Shorts, Instagram Reels & TikTok" below for what each actually
needs, since none of the three share a setup cost with each other or with
the eight text platforms above. Same `--dry-run`/`--confirmed` safety
pattern as the webhook script, including credential redaction in
`--dry-run` output —
for Discord and Slack specifically, the webhook URL itself is the
credential (there's no separate token), so that whole URL gets redacted,
not just a header; for Telegram, only the bot token embedded in the URL
path gets redacted, since the rest of the URL is just the API endpoint
shape, not a secret; for dev.to, the API key is a static value in a custom
`api-key` header, redacted the same simple way a bearer token would be —
no OAuth flow, no webhook URL, the simplest credential shape of the eight.
For Reddit, a successful response doesn't guarantee the post survives that
subreddit's AutoModerator — see [Community posts](community-posting.md)
before sending anything for real.

**Discord is one of the easiest to actually set up** — a webhook needs no
OAuth app review at all, just `MANAGE_WEBHOOKS` permission on the channel
to create one (Channel Settings → Integrations → Webhooks). That's one
place this script is easier than the platform it's replacing, not harder:
`community-post-generator` can't independently verify a Discord server's
rules the way it can for the researchable five (see below), so the actual
bottleneck for Discord is research, not access. It's not the unconditional
floor, though — see dev.to below for the one platform here whose access
doesn't depend on any permission over the specific target at all.

**Slack looks similar to Discord but isn't as simple, and the difference
matters.** The direct-webhook-URL path is legacy; creating one now means
creating a Slack App, and many workspaces require a Workspace Owner/Admin
to approve new apps before that's even possible — confirm your
workspace's app-approval setting rather than assuming self-serve setup
the way Discord's is. Slack also expects plain text formatted in its own
**mrkdwn** syntax, not standard Markdown — a single asterisk (`*bold*`)
is bold in Slack, the opposite of standard Markdown's italic, and
`community-post-generator` drafts Slack posts in mrkdwn for exactly that
reason. Character limit is shaped differently too: this script hard-caps
at Slack's technical ceiling of 40,000 characters (rejecting, not
truncating, past that) but only warns, doesn't block, between 4,000 and
40,000, since 4,000 is a display recommendation, not a hard limit —
compare Discord's flat 2,000-character rejection.

**Telegram's setup friction is shaped differently from both Discord's and
Slack's — easy at first, then a second gate neither of the others has.**
Creating the bot itself, via Telegram's own @BotFather, needs no approval
from anyone — genuinely as easy as Discord's webhook creation. But a bot
can only post into a chat one of that chat's admins has actually added it
to; creating the bot isn't the same as being authorized to post anywhere,
so budget for that second step separately. Telegram also offers two
formatting modes, HTML and MarkdownV2 — this script defaults to HTML
because MarkdownV2 requires escaping over a dozen characters and a single
missed escape fails the entire send, not just that character's
formatting; `community-post-generator` drafts in HTML for the same
reason. Character limit is a flat 4096, rejected outright like Discord's
limit, not truncated like Slack's.

**dev.to has the simplest access story of the eight — not just easy, but
unconditionally easy.** An API key comes from your own account settings,
full stop; no approval process was found in this skill's research, and
unlike every other platform above, access doesn't depend on any
permission over the specific target either — Discord's webhook still
needs `MANAGE_WEBHOOKS` on that channel, Telegram's bot still needs a chat
admin to add it, but a dev.to API key works under whatever tags your
account can post to, which is all of them. That ease is about access,
though, not content: a Tag Moderator can still strip a tag from the
result afterward, and this skill's research couldn't confirm the Code of
Conduct's specific self-promotion wording (dev.to's own domain was
unreachable during that research) — a 2xx response means the article was
accepted, not that it was welcomed. Posts as a full title+body Markdown
article with up to 4 tags (`--tags`), not a short message, and optionally
under a dev.to Organization (`--org-id`) instead of your personal account.
No documented character limit, unlike the four chat platforms above.

**Product Hunt, Hacker News, and Indie Hackers all have no direct-send
path here, for different reasons.** Product Hunt's write API
(`createPost`, etc.) requires special approval from Product Hunt itself —
the free/default API tier is explicitly read-only, non-commercial (see
[Community posts](community-posting.md)) — so unlike LinkedIn/X/Meta/Reddit/Discord/Slack/Telegram/dev.to,
there's no "just bring your own API credentials" option to script
against, though that approval process at least exists. Hacker News has no write API to even
apply for — its official API is read-only by design, full stop, so this
isn't a "not yet approved" situation, it's "nothing to approve." Indie
Hackers is genuinely unverified rather than confirmed either way — some
sources mention an API, but it looks scoped to read-only product/revenue
data, and nothing confirms a way to submit a post through it.
`community-post-generator` still drafts the post text either way; you
paste it into producthunt.com, news.ycombinator.com, or indiehackers.com
yourself.

## Posting to YouTube Shorts, Instagram Reels & TikTok

`short-form-video` drafts the script and per-platform package; sending it
for real is `scripts/publish_direct.py`'s job via `--platform youtube`,
`--platform instagram`, or `--platform tiktok`, same as the eight text
platforms above — but these three post actual video, and each one's
access story is genuinely different from the other two, not a shared
"video posting" tier:

**AI-made videos get labeled.** A video with realistic AI-made content
(an AI avatar presenting, a cloned voice, a lifelike generated scene)
takes `--ai-generated`. On YouTube that sets the video's own disclosure
(`status.containsSyntheticMedia`). TikTok and Instagram have their own AI
labels that this script can't set through the API, so with
`--ai-generated` it stops for those two and says to post from the app with
the label on. The plugin's 3D mascot, pixel art, and motion graphics are
clearly animated and don't need it.

**YouTube is the most self-serve of the three.** It uses the standard
YouTube Data API v3 (there's no separate "Shorts API" — a video becomes a
Short by being vertical and short enough, optionally reinforced with a
`#Shorts` tag in the description). All you need is your own Google Cloud
project's OAuth2 client, authorized against the channel you're uploading
to — no platform-side approval queue the way Reddit or TikTok require. A
mid-2026 quota change helps here too: video uploads now draw from their
own ~100-per-day bucket on your project instead of competing with every
other API call against the old shared 10,000-unit pool, so ordinary
personal or small-team posting volume shouldn't need special quota
approval anymore — confirm your project's current bucket size in Google
Cloud Console rather than assuming. It's also the one platform of the
three where the video is actually uploaded (a local file, via a resumable
upload) rather than fetched by the platform from a URL. `publish_direct.py`
defaults `--privacy-status` to `private` specifically so a `--confirmed`
run never goes public by accident.

**Instagram Reels needs the heaviest setup of the three.** You need an
Instagram Business or Creator account linked to a Facebook Page, a Meta
app with the `instagram_business_content_publish` permission actually
approved through Meta's app review (Development Mode alone only lets your
app's own admins/developers/testers post — fine for your own account,
not for anyone else's), and the video already hosted somewhere publicly
reachable: unlike YouTube, the Instagram Graph API has no raw-upload
endpoint at all — it fetches the video from a URL you give it. The real
flow is three steps, not one (create a media container, wait for
Instagram to finish processing the video, then publish it), which
`publish_direct.py` handles by polling rather than assuming it's instant.

**TikTok sits in between, with a real ceiling the other two don't have.**
Its Content Posting API needs an app approved for the `video.publish`
scope, and — this is the one to know before promising "just post it" —
**until your app passes TikTok's own audit, TikTok only accepts posts set
to private (`SELF_ONLY`), on a creator account that is itself set to
private. Anything else is rejected outright, not quietly posted as
private.** Audit review reportedly takes anywhere from a few days to about
two weeks; until it passes, TikTok posting through this script is useful
for testing the pipeline, not for actually reaching an audience. Before
every post, `publish_direct.py` also asks TikTok which privacy levels and
interaction settings the creator currently allows (TikTok requires this
step). It stops if `--privacy-level` isn't one of them, and turns off
duets, comments, or stitching wherever the creator already has. Like Instagram, it
fetches the video from a URL rather than accepting an upload — that URL's
domain also has to be pre-verified for your app in TikTok's developer
portal. And a 2xx response from either Instagram's or TikTok's API means
the request was accepted, not that the video is live yet — both process
the video asynchronously afterward, so confirm the actual result (TikTok's
own status-fetch endpoint, or checking the account directly) before
reporting a send as done.

**Covers:** `--cover-ms` picks the cover frame on TikTok
(`video_cover_timestamp_ms`) and Instagram (`thumb_offset`), and
`--cover-url` gives Instagram a cover image instead; `render.js --cover`
prints the value for the frame it checked. YouTube's Shorts cover is
chosen in its app.

**How it did:** `publish_direct.py --platform youtube|instagram|tiktok
--metrics --post-id <id>` reads a posted video's views, average watch,
likes, comments, shares, and saves (read-only, so it needs no
`--confirmed`) and prints the cells for `state/video-log.md`; add `--log`
and it writes them into the row whose Link / ID holds that video. Every
send prints a `Posted:` line with the new post's ID and link, which is
what goes in that column (TikTok's is the exception: it returns a
publish ID, so take the video ID from the post's link). Like the rest of
`publish_direct.py`, it's written against each platform's documented API
without a live account to test on; YouTube's average-watch figure also
needs the `yt-analytics.readonly` scope.

**How a post did:** the same `--metrics` works for `--platform reddit`
(score, upvote ratio, comments, and whether it was removed and by whom:
a moderator, AutoMod, or Reddit's spam filter) and `--platform devto`
(reactions, comments, and views), with the post's link or ID as
`--post-id` and the same credentials as posting. `--log` writes those
into `state/post-log.md`. LinkedIn and X have no metrics path here: X's
read API is a paid tier, and LinkedIn's post statistics need its
Community Management API approval, so paste their numbers into the log
by hand.

**The numbers:** `python3 scripts/results.py` reads the three logs and
prints what they add up to: posts and removals by community and by the
Go/No-Go they went out under, median views, average watch, and 3-second
hold by video format and hook pattern, and cold email reply, bounce, and
unsubscribe rates with a significance test on the subject-line A/B.
Groups under 5 are marked "too few to tell", and the A/B isn't called
under 30 sends a side. `short-form-video`, `content-calendar`, and
`email-outreach` steer by its output instead of reading the tables by
eye.

None of this blocks the default path: `short-form-video` always produces
the full script, caption, and hashtags regardless of whether any of this
is set up, and posting it yourself by hand — download or generate the
clip, paste the caption, tap post — works the same as it always has.
