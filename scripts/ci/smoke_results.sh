#!/usr/bin/env bash
# Checks scripts/results.py against the made-up logs in scripts/ci/fixtures/logs:
# the rates, medians, and "too few to tell" calls it prints are the numbers the
# skills quote, so they're pinned here. Also checks the shipped, empty logs.
set -euo pipefail
cd "$(dirname "$0")/../.."

r=scripts/results.py
logs=scripts/ci/fixtures/logs
expect() {
  local name=$1 pattern=$2
  grep -qF -- "$pattern" <<<"$out" || { echo "FAIL: $name (expected: $pattern)"; echo "$out"; exit 1; }
  echo "ok: $name"
}

out=$(python3 $r)
expect "empty logs" "No rows yet in post-log.md."

out=$(python3 $r --log-dir $logs)
expect "removal rate leaves out a post its author deleted" "| r/SaaS | 6 | 2 of 5 (40%) | 35 | 2.5 |  |  |"
expect "a group of one is too few to tell" "| Show HN | 1 |  | 12 | 5 |  | too few to tell |"
expect "split by verdict" "| Go (hedged) | 2 | 1 of 2 (50%) | 45 | 4.5 |  | too few to tell |"
expect "a format that clearly leads" "Leading format: tier-list, by median 3-second hold (at least 10% over pov)."
expect "pasted counts like 1.2k" "| pov | 5 | 1200 | 32% | 52% |  |"
expect "reply, bounce, unsubscribe rates" "Replies 33%, bounces 4%, unsubscribes 4%."
expect "12 sends a side isn't called" "Subject lines: too few to tell (needs 30 sends a side)."

out=$(python3 $r --log-dir $logs --json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["posts"]["total"], d["outreach"]["contacted"])')
expect "--json" "8 24"

out=$(python3 -c 'import importlib.util as u; s=u.spec_from_file_location("r","scripts/results.py"); m=u.module_from_spec(s); s.loader.exec_module(m); print(round(m.z_test(10,100,20,100),3))')
expect "two-proportion z-test" "0.048"

out=$(python3 $r --eval $logs/eval-result.json)
expect "--eval table" "| reddit-nogo | 1.00 | 0.33 | +0.67 | 2 of 3 | 3 |"

out=$(python3 $r --log-dir $logs --since 2026-09-05)
expect "--since drops earlier rows" "## Posts (4)"

out=$(python3 $r --eval $logs/eval-result.json --compare $logs/eval-result.json)
expect "--compare before / after" "All runs: 3 of 3 before, 3 of 3 after."
