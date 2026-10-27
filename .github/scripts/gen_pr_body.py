#!/usr/bin/env python3
"""Generate a PR body for the weekly content batch.

Reads the four key files and assembles the PR description in
CAN → COULD → MAY → MIGHT section order.

Usage:
    python3 .github/scripts/gen_pr_body.py <week_number>

Example:
    python3 .github/scripts/gen_pr_body.py 44 > /tmp/pr_body.md
    gh pr create --title "content(w44): ..." --body-file /tmp/pr_body.md
"""

import csv
import re
import subprocess
import sys

QUARTER = "2026Q3"
TABLE   = f"MAY/TABLE-{QUARTER}.csv"
LOG     = f"COULD/LOG-{QUARTER}.log"
ASSET   = f"MIGHT/ASSET-{QUARTER}.md"


def mermaid_block() -> str:
    return subprocess.check_output(
        ["python3", ".github/scripts/gen_tree_mermaid.py"], text=True
    ).strip()


def posts_table(week: int) -> str:
    with open(TABLE, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if int(r["week"]) == week]
    if not rows:
        return f"_No posts found for week {week}._"
    lines = [
        "| Post | Pillar | Subtype | Score | Media |",
        "|------|--------|---------|-------|-------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['item']} | {r['topic']} | {r['type']} / {r['subtopic']}"
            f" | {r['score']} | {r['media-type']} |"
        )
    return "\n".join(lines)


def log_entry(week: int) -> str:
    """Return the log block for the given week's version entry."""
    text = open(LOG, encoding="utf-8").read()
    # Match  ## v<N> — w<NN> — <date>  up to the next ## or end of file
    pattern = rf"(## v\d+ — w{week:02d}.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else f"_No log entry found for week {week}._"


def asset_entry() -> str:
    """Return the most recent ASSET entry (between anchor and next ##)."""
    text = open(ASSET, encoding="utf-8").read()
    anchor = "<!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE -->"
    after = text[text.find(anchor) + len(anchor):]
    m = re.search(r"(## ASSET:.*?)(?=\n## ASSET:|\Z)", after, re.DOTALL)
    return m.group(1).strip() if m else "_No asset entry found._"


def gen_pr_body(week: int) -> str:
    posts = posts_table(week)
    first_post = f"post-{(week - 1) * 6 + 1:03d}"
    last_post  = f"post-{week * 6:03d}"

    return f"""\
## Week {week:02d} — 6 posts, all BLOCKED pending media

## Content Strategy Tree (`CAN/TREE-{QUARTER}.json`)

> Auto-updated whenever the tree JSON changes on main — suggest changes by commenting below.

<!-- TREE-START -->
{mermaid_block()}
<!-- TREE-END -->

## Activity log (`COULD/LOG-{QUARTER}.log`)

{log_entry(week)}

## Posts (`MAY/TABLE-{QUARTER}.csv`)

{posts}

## Assets (`MIGHT/ASSET-{QUARTER}.md`)

{asset_entry()}
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <week_number>", file=sys.stderr)
        sys.exit(1)
    print(gen_pr_body(int(sys.argv[1])), end="")
