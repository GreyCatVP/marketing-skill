#!/usr/bin/env python3
"""
The numbers behind "does this work?", computed from the plugin's own logs
instead of read off a table by eye:

  state/post-log.md      posts: how many went out where, how many were
                         removed, median score and comments, by the
                         Go/No-Go verdict they went out under
  state/video-log.md     videos: median views, average watch, and 3-second
                         hold by format and by hook pattern
  state/outreach-log.md  cold email: reply, bounce, and unsubscribe rates,
                         and whether subject line A or B actually gets
                         more replies (a two-proportion z-test)

Any group of fewer than 5 posts or videos is marked "too few to tell", and
an A/B split under 30 sends a side isn't called either way. Prints Markdown
tables; --json prints the same numbers for a skill to read.

  python3 scripts/results.py                         the logs under state/
  python3 scripts/results.py --log-dir docs/results-data
  python3 scripts/results.py --since 2026-10-01     only rows from that day on
  python3 scripts/results.py --eval evals/results/latest.json

--eval prints the with-plugin / without-plugin table from a
`claude plugin eval --json` result instead.

Standard library only; reads local files, never the network.
"""
import argparse
import json
import math
import os
import re
import statistics
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEW = 5           # fewer posts or videos than this in a group: too few to tell
AB_MIN = 30       # sends per subject-line variant before A/B is called either way
LEAD = 0.10       # a format leads only if its median beats the next by this much
CONTACTED = {"sent", "replied", "bounced", "unsubscribed", "do-not-contact"}
METRIC_WORDS = {"median_3s_hold_pct": "median 3-second hold", "median_avg_watch_pct": "median average watch",
                "median_avg_watch_s": "median average watch time", "median_views": "median views"}


def read_table(path):
    """The rows of the first Markdown table in a log, as dicts by column name. [] when the file or
    the table is missing."""
    if not os.path.exists(path):
        return []
    lines = open(path, encoding="utf-8").read().split("\n")
    for i in range(len(lines) - 1):
        if lines[i].startswith("|") and re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[i + 1]):
            columns = split_row(lines[i])
            rows = []
            for line in lines[i + 2:]:
                if not line.startswith("|"):
                    break
                cells = split_row(line)
                rows.append(dict(zip(columns, cells + [""] * (len(columns) - len(cells)))))
            return rows
    return []


def split_row(line):
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") and not body.endswith("\\|") else body
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", body)]


def number(cell):
    """A count as typed or pasted: 1234, 1,234, 1.2k, 3M. None when blank or not a number."""
    m = re.fullmatch(r"\s*([\d.,]+)\s*([kKmM]?)\s*", cell or "")
    if not m:
        return None
    try:
        value = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return value * {"": 1, "k": 1e3, "m": 1e6}[m.group(2).lower()]


def unit_value(cell, unit):
    """45% -> 45 for unit '%', 12.3s -> 12.3 for unit 's'; None for anything else."""
    m = re.fullmatch(r"\s*([\d.]+)\s*" + re.escape(unit) + r"\s*", cell or "")
    return float(m.group(1)) if m else None


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def fmt(value, suffix=""):
    if value is None:
        return ""
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}".rstrip("0").rstrip(".") + suffix
    return f"{int(value)}{suffix}"


def group(rows, key):
    groups = {}
    for row in rows:
        groups.setdefault(key(row) or "(blank)", []).append(row)
    # most posts first; never an implied ranking by result
    return sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def note(n):
    return "too few to tell" if n < FEW else ""


def post_stats(rows):
    def summary(name, items):
        # a post its author deleted wasn't removed by anyone, so it's left out of the rate
        known = [r for r in items if r.get("Removed", "").lower() not in ("", "deleted")]
        removed = [r for r in known if r.get("Removed", "").lower() != "no"]
        return {
            "group": name, "posts": len(items),
            "removed": len(removed), "removed_known": len(known),
            "removed_rate": len(removed) / len(known) if known else None,
            "median_score": median(number(r.get("Score")) for r in items),
            "median_comments": median(number(r.get("Comments")) for r in items),
            "median_views": median(number(r.get("Views")) for r in items),
            "note": note(len(items)),
        }
    return {
        "total": len(rows),
        "by_where": [summary(k, v) for k, v in group(rows, lambda r: r.get("Where"))],
        "by_verdict": [summary(k, v) for k, v in group(rows, lambda r: r.get("Verdict"))],
    }


def video_stats(rows):
    def summary(name, items):
        return {
            "group": name, "videos": len(items),
            "median_views": median(number(r.get("Views")) for r in items),
            "median_avg_watch_pct": median(unit_value(r.get("Avg watch"), "%") for r in items),
            "median_avg_watch_s": median(unit_value(r.get("Avg watch"), "s") for r in items),
            "median_3s_hold_pct": median(unit_value(r.get("3s hold"), "%") for r in items),
            "note": note(len(items)),
        }

    def leader(summaries):
        """The group whose median 3s hold (else average watch, else views) beats the next by
        LEAD or more, among groups big enough to tell. None when no group clearly leads."""
        for metric in ("median_3s_hold_pct", "median_avg_watch_pct", "median_avg_watch_s", "median_views"):
            ranked = sorted((s for s in summaries if not s["note"] and s[metric] is not None),
                            key=lambda s: -s[metric])
            if len(ranked) >= 2:
                top, second = ranked[0], ranked[1]
                if second[metric] and (top[metric] - second[metric]) / second[metric] >= LEAD:
                    return {"group": top["group"], "metric": metric, "over": second["group"]}
                return {"group": None, "metric": metric}
        return None

    by_format = [summary(k, v) for k, v in group(rows, lambda r: r.get("Format"))]
    by_hook = [summary(k, v) for k, v in group(rows, lambda r: r.get("Hook", "").split(":")[0].strip())]
    return {"total": len(rows), "by_format": by_format, "format_leader": leader(by_format),
            "by_hook_pattern": by_hook, "hook_leader": leader(by_hook)}


def z_test(replies_a, n_a, replies_b, n_b):
    """Two-sided p-value for a difference between two reply rates."""
    pooled = (replies_a + replies_b) / (n_a + n_b)
    spread = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    if spread == 0:
        return 1.0
    z = (replies_a / n_a - replies_b / n_b) / spread
    return math.erfc(abs(z) / math.sqrt(2))


def outreach_stats(rows):
    contacted = [r for r in rows if r.get("Status", "").strip().lower() in CONTACTED]
    status = lambda r: r.get("Status", "").strip().lower()  # noqa: E731
    count = lambda items, *names: sum(1 for r in items if status(r) in names)  # noqa: E731
    n = len(contacted)
    rate = lambda k: k / n if n else None  # noqa: E731
    variants = {}
    for v in ("A", "B"):
        items = [r for r in contacted if r.get("Subject Variant", "").strip().upper() == v]
        variants[v] = {"sent": len(items), "replied": count(items, "replied"),
                       "reply_rate": count(items, "replied") / len(items) if items else None}
    a, b = variants["A"], variants["B"]
    if a["sent"] < AB_MIN or b["sent"] < AB_MIN:
        verdict, p = f"too few to tell (needs {AB_MIN} sends a side)", None
    else:
        p = z_test(a["replied"], a["sent"], b["replied"], b["sent"])
        if p > 0.05:
            verdict = "no clear winner"
        else:
            verdict = "A gets more replies" if a["reply_rate"] > b["reply_rate"] else "B gets more replies"
    return {
        "contacted": n,
        "reply_rate": rate(count(contacted, "replied")),
        "bounce_rate": rate(count(contacted, "bounced")),
        "unsubscribe_rate": rate(count(contacted, "unsubscribed", "do-not-contact")),
        "subject_ab": {"A": a, "B": b, "p_value": p, "verdict": verdict},
    }


def pct(value):
    return "" if value is None else f"{value * 100:.0f}%"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def print_posts(stats):
    print(f"## Posts ({stats['total']})\n")
    if not stats["total"]:
        print("No rows yet in post-log.md.\n")
        return
    headers = ["Posts", "Removed", "Median score", "Median comments", "Median views", "Note"]
    for title, key in (("Where", "by_where"), ("Verdict", "by_verdict")):
        rows = [[s["group"], s["posts"],
                 f"{s['removed']} of {s['removed_known']} ({pct(s['removed_rate'])})" if s["removed_known"] else "",
                 fmt(s["median_score"]), fmt(s["median_comments"]), fmt(s["median_views"]), s["note"]]
                for s in stats[key]]
        print(table([title] + headers, rows) + "\n")


def print_videos(stats):
    print(f"## Videos ({stats['total']})\n")
    if not stats["total"]:
        print("No rows yet in video-log.md.\n")
        return
    headers = ["Videos", "Median views", "Median avg watch", "Median 3s hold", "Note"]
    for title, key, lead in (("Format", "by_format", "format_leader"), ("Hook pattern", "by_hook_pattern", "hook_leader")):
        rows = [[s["group"], s["videos"], fmt(s["median_views"]),
                 " / ".join(x for x in (fmt(s["median_avg_watch_pct"], "%"), fmt(s["median_avg_watch_s"], "s")) if x),
                 fmt(s["median_3s_hold_pct"], "%"), s["note"]] for s in stats[key]]
        print(table([title] + headers, rows) + "\n")
        leader = stats[lead]
        if leader and leader["group"]:
            print(f"Leading {title.lower()}: {leader['group']}, by {METRIC_WORDS[leader['metric']]} "
                  f"(at least {LEAD:.0%} over {leader['over']}).\n")
        elif leader:
            print(f"No {title.lower()} clearly leads (the top two are within {LEAD:.0%}).\n")


def print_outreach(stats):
    print(f"## Cold email ({stats['contacted']} sent)\n")
    if not stats["contacted"]:
        print("No sent emails yet in outreach-log.md.\n")
        return
    print(f"Replies {pct(stats['reply_rate'])}, bounces {pct(stats['bounce_rate'])}, "
          f"unsubscribes {pct(stats['unsubscribe_rate'])}.\n")
    ab = stats["subject_ab"]
    rows = [[v, ab[v]["sent"], ab[v]["replied"], pct(ab[v]["reply_rate"])] for v in ("A", "B")]
    print(table(["Subject", "Sent", "Replied", "Reply rate"], rows) + "\n")
    p = "" if ab["p_value"] is None else f" (p = {ab['p_value']:.2f})"
    print(f"Subject lines: {ab['verdict']}{p}.\n")


def eval_table(path):
    """The with / without / difference table from `claude plugin eval --json` output, plus how
    many with-plugin runs actually used the skill (its with-only `tool_used: Skill` grader)."""
    data = json.load(open(path, encoding="utf-8"))
    rows = []
    for case in data.get("cases", []):
        agg = case.get("aggregates") or {}
        with_runs = (case.get("arms") or {}).get("with") or []
        fired = [g["passed"] for run in with_runs for g in run.get("graders", [])
                 if g.get("withOnly") and not g.get("scored")]
        rows.append([case.get("name"), fmt2(agg.get("score")), fmt2(agg.get("scoreWithout")),
                     fmt2(agg.get("delta"), sign=True),
                     f"{sum(fired)} of {len(fired)}" if fired else "", case.get("runsPerCase", "")])
    return data, rows


def fmt2(value, sign=False):
    if value is None:
        return ""
    return f"{value:+.2f}" if sign else f"{value:.2f}"


def main():
    parser = argparse.ArgumentParser(description="The numbers behind the plugin's logs, or an eval result.")
    parser.add_argument("--log-dir", default=os.path.join(PLUGIN_ROOT, "state"),
                        help="Folder holding post-log.md, video-log.md, and outreach-log.md (default: state/).")
    parser.add_argument("--since", metavar="YYYY-MM-DD",
                        help="Only rows posted (or, for cold email, dated) on or after this day.")
    parser.add_argument("--json", action="store_true", help="Print the numbers as JSON instead of tables.")
    parser.add_argument("--eval", metavar="RESULT_JSON",
                        help="Print the with / without plugin table from a `claude plugin eval --json` result.")
    args = parser.parse_args()

    if args.eval:
        data, rows = eval_table(args.eval)
        columns = ["case", "with", "without", "difference", "skill_fired", "runs"]
        if args.json:
            print(json.dumps([dict(zip(columns, r)) for r in rows], indent=2))
            return 0
        print(table(["Case", "With plugin", "Without", "Difference", "Skill fired", "Runs per side"], rows))
        agg = data.get("aggregates") or {}
        if agg:
            print(f"\nMean score with the plugin {fmt2(agg.get('overallScore'))}, "
                  f"mean difference {fmt2(agg.get('meanDelta'), sign=True)}, "
                  f"{agg.get('casesPassed', '?')} of {agg.get('casesTotal', '?')} cases passed. "
                  f"Run {str(data.get('startedAt', ''))[:10]}, cost ${data.get('costUsd', 0):.2f}.")
        return 0

    def rows(name):
        found = read_table(os.path.join(args.log_dir, name))
        if args.since:
            found = [r for r in found if (r.get("Posted") or r.get("Date") or "") >= args.since]
        return found

    stats = {
        "posts": post_stats(rows("post-log.md")),
        "videos": video_stats(rows("video-log.md")),
        "outreach": outreach_stats(rows("outreach-log.md")),
    }
    if args.json:
        print(json.dumps(stats, indent=2))
        return 0
    print_posts(stats["posts"])
    print_videos(stats["videos"])
    print_outreach(stats["outreach"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
