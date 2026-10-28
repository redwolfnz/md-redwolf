#!/usr/bin/env python3
"""Generate a PR body for the weekly content batch.

Reads the key files and assembles the PR description in
CAN → COULD → MAY → MIGHT section order.

Usage:
    python3 .github/scripts/gen_pr_body.py <week_number>

Example:
    python3 .github/scripts/gen_pr_body.py 44 > /tmp/pr_body.md
    gh pr create --title "content(w44): ..." --body-file /tmp/pr_body.md
"""

import csv
import json
import re
import subprocess
import sys
import yaml
from datetime import date, timedelta
from pathlib import Path

QUARTER = "2026Q3"
TABLE   = f"COULD/TABLE-{QUARTER}.csv"
ASSET   = f"MIGHT/ASSET-{QUARTER}.md"
PIPE    = f"PIPE-{QUARTER}.yml"

FETCH_ANCHOR = "####### <!-- ANCHOR MARKER - ADD ALL NEW ENTRIES DIRECTLY BELOW THIS LINE -->"

SLUG_ORDER = [
    "REDWOLF", "NZSA", "ASIS", "NZPOLICE",
    "JOHNSON", "GALLAGHER", "INNERRANGE", "BOSCH", "ICT", "JACQUES",
]


def pipe_mermaid() -> str:
    with open(PIPE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    meta = data.get("meta", {})
    root_label = f"{meta.get('name', PIPE)} · {meta.get('quarter', QUARTER)}"
    lines = ["```mermaid", "graph LR", f'  ROOT(["{root_label}"])']
    for step in data.get("steps", []):
        sid = step["id"].replace("-", "_").upper()
        lines.append(f'  ROOT --> {sid}["{step["id"]} · {step["name"]}"]')
        for sub in step.get("substeps", []):
            subid = f'{sid}_{sub["id"].replace("-", "_").upper()}'
            lines.append(f'  {sid} --> {subid}("{sub["id"]} · {sub["name"]}")')
    lines.append("```")
    return "\n".join(lines)


def mermaid_block() -> str:
    return subprocess.check_output(
        ["python3", ".github/scripts/gen_tree_mermaid.py"], text=True
    ).strip()


def _parse_latest_entry(slug: str) -> dict | None:
    """Newest entry for this connection in the single fetch log (newest first)."""
    log_path = Path(f"MAY/LOG-{QUARTER}.log")
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8")
    after = text[text.find(FETCH_ANCHOR) + len(FETCH_ANCHOR):]
    for m in re.finditer(r"## \S+ (\S+)\n(\{[^\n]+\})", after):
        if m.group(1) != slug:
            continue
        try:
            return json.loads(m.group(2))
        except json.JSONDecodeError:
            return None
    return None


def connection_activity(week: int) -> str:
    """Return posts from MAY/LOG-*.log within the last 7 days (rolling window).

    Anchored to today so the section is fairly labelled as this week's signals
    regardless of where the ISO week boundary falls.
    """
    end   = date.today()
    start = end - timedelta(days=7)

    blocks = []
    for slug in SLUG_ORDER:
        data = _parse_latest_entry(slug)
        if not data:
            continue
        week_posts = [
            p for p in data.get("recentPosts", [])
            if start <= date.fromisoformat(p["date"]) <= end
        ]
        if not week_posts:
            continue
        company = data.get("companyName", slug)
        lines = [f"**{company}**"]
        for p in week_posts:
            snippet = p["text"][:120].replace("\n", " ")
            if len(p["text"]) > 120:
                snippet += "…"
            lines.append(f"- {p['date']}: {snippet}")
        blocks.append("\n".join(lines))

    if not blocks:
        return f"_No connection posts in the last 7 days ({start} – {end})._"
    return "\n\n".join(blocks)


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


def asset_entry() -> str:
    """Return the most recent ASSET entry (between anchor and next ##)."""
    text = open(ASSET, encoding="utf-8").read()
    anchor = "<!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE -->"
    after = text[text.find(anchor) + len(anchor):]
    m = re.search(r"(## ASSET:.*?)(?=\n## ASSET:|\Z)", after, re.DOTALL)
    return m.group(1).strip() if m else "_No asset entry found._"


def gen_pr_body(week: int) -> str:
    return f"""\
## Pipeline (`PIPE-{QUARTER}.yml`)

{pipe_mermaid()}

## Content Strategy Tree (`CAN/TREE-{QUARTER}.json`)

> Auto-updated whenever the tree JSON changes on main — suggest changes by commenting below.

<!-- TREE-START -->
{mermaid_block()}
<!-- TREE-END -->

## Posts (`COULD/TABLE-{QUARTER}.csv`)

{posts_table(week)}

## Connection activity (`MAY/`)

{connection_activity(week)}

## Assets (`MIGHT/ASSET-{QUARTER}.md`)

{asset_entry()}
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <week_number>", file=sys.stderr)
        sys.exit(1)
    print(gen_pr_body(int(sys.argv[1])), end="")
