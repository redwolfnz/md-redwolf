#!/usr/bin/env python3
"""
Step 2: Generate weekly content batch.

Reads TREE JSON + MAY connection logs, calls the Claude API with the
generate-post skill as the system prompt, then appends 6 post rows
(one per pillar) to COULD/TABLE-2026Q3.csv.

Environment variables:
  ANTHROPIC_API_KEY  — required
  CONTENT_WEEK       — optional ISO week override (default: current week)
"""

import anthropic
import csv
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

QUARTER      = "2026Q3"
TABLE_PATH   = f"COULD/TABLE-{QUARTER}.csv"
TREE_PATH    = f"CAN/TREE-{QUARTER}.json"
SKILL_PATH   = ".claude/skills/generate-post/SKILL.md"
LOG_DIR      = Path("MAY")
FETCH_ANCHOR = "####### <!-- ANCHOR MARKER - ADD ALL NEW ENTRIES DIRECTLY BELOW THIS LINE -->"

SLUG_ORDER = [
    "REDWOLF", "NZSA", "ASIS", "NZPOLICE",
    "JOHNSON", "GALLAGHER", "INNERRANGE", "BOSCH", "ICT", "JACQUES",
]

PILLARS = ["SERVICES", "INDUSTRY", "AUTHORITY", "PEOPLE", "TRUST", "ENGAGEMENT"]

MODEL   = "claude-opus-4-8"


# ── helpers ──────────────────────────────────────────────────────────────────

def week_num() -> int:
    env = os.environ.get("CONTENT_WEEK", "")
    return int(env) if env else date.today().isocalendar()[1]


def load_skill() -> str:
    text = Path(SKILL_PATH).read_text(encoding="utf-8")
    # Strip YAML frontmatter if present
    if text.startswith("---"):
        end = text.index("---", 3) + 3
        return text[end:].lstrip()
    return text


def parse_latest_log_entry(slug: str) -> dict | None:
    log = LOG_DIR / f"{slug}-{QUARTER}.log"
    if not log.exists():
        return None
    text = log.read_text(encoding="utf-8")
    anchor_pos = text.find(FETCH_ANCHOR)
    if anchor_pos == -1:
        return None
    after = text[anchor_pos + len(FETCH_ANCHOR):]
    m = re.search(r"## \S+\n(\{[^\n]+\})", after)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def load_connections(window_start: date, window_end: date) -> list[dict]:
    connections = []
    for slug in SLUG_ORDER:
        data = parse_latest_log_entry(slug)
        if not data:
            continue
        recent = [
            p for p in data.get("recentPosts", [])
            if window_start <= date.fromisoformat(p["date"]) <= window_end
        ]
        connections.append({
            "slug": slug,
            "companyName": data.get("companyName", slug),
            "bio": data.get("bio", ""),
            "fetchedAt": data.get("fetchedAt", ""),
            "recentPosts": recent,
        })
    return connections


def load_csv() -> tuple[list[str], list[dict]]:
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    return fieldnames, rows


def used_subtypes(rows: list[dict]) -> list[dict]:
    return [
        {"topic": r["topic"], "type": r["type"], "subtopic": r["subtopic"]}
        for r in rows
        if r.get("topic") and r.get("type") and r.get("subtopic")
    ]


def next_item_num(rows: list[dict]) -> int:
    nums = [
        int(r["item"].replace("post-", ""))
        for r in rows
        if re.fullmatch(r"post-\d+", r.get("item", ""))
    ]
    return (max(nums) if nums else 0) + 1


def build_user_message(week: int, rows: list[dict], tree: dict) -> str:
    today = date.today()
    window_start = today - timedelta(days=7)
    connections = load_connections(window_start, today)
    return json.dumps(
        {
            "quarter": QUARTER,
            "week": week,
            "today": str(today),
            "window": f"{window_start} to {today}",
            "nextItemStart": next_item_num(rows),
            "usedSubtypes": used_subtypes(rows),
            "tree": tree,
            "connections": connections,
        },
        indent=2,
        ensure_ascii=False,
    )


# ── validation ────────────────────────────────────────────────────────────────

DOUBLE_HYPHEN = re.compile(r"--")

def validate_posts(posts: list[dict]) -> None:
    if len(posts) != 6:
        raise ValueError(f"Expected 6 posts, got {len(posts)}")

    topics = [p.get("topic") for p in posts]
    if sorted(topics) != sorted(PILLARS):
        raise ValueError(f"Posts must cover all 6 pillars. Got: {topics}")

    for p in posts:
        for field in ("title", "description"):
            val = p.get(field, "")
            if DOUBLE_HYPHEN.search(val):
                raise ValueError(
                    f"Double hyphen found in post {p.get('topic')} / {field}: {val[:80]}"
                )


# ── CSV write ─────────────────────────────────────────────────────────────────

def serialize_csv(rows: list[dict], fieldnames: list[str]) -> str:
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def append_posts(
    posts: list[dict],
    existing_rows: list[dict],
    fieldnames: list[str],
    week: int,
) -> list[dict]:
    today = str(date.today())
    item_num = next_item_num(existing_rows)
    new_rows = []
    for post in posts:
        row = {h: "" for h in fieldnames}
        row.update(
            {
                "week": str(week),
                "item": f"post-{item_num:03d}",
                "topic": post.get("topic", ""),
                "type": post.get("type", ""),
                "subtopic": post.get("subtopic", ""),
                "title": post.get("title", ""),
                "description": post.get("description", ""),
                "media": post.get("media", ""),
                "media-type": post.get("media-type", ""),
                "media URL": "",
                "linkedin account tag": post.get("linkedin account tag", ""),
                "hashtag": post.get("hashtag", ""),
                "score": str(post.get("score", "")),
                "createdat": today,
                "updatedat": today,
                "feedback": "",
                "feedback-comment": "",
                "sources": post.get("sources", ""),
            }
        )
        new_rows.append(row)
        item_num += 1
    return new_rows


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    week = week_num()
    fieldnames, existing_rows = load_csv()
    tree = json.loads(Path(TREE_PATH).read_text(encoding="utf-8"))
    system_prompt = load_skill()
    user_message = build_user_message(week, existing_rows, tree)

    print(f"Calling {MODEL} to generate week {week} batch…")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    response_text = message.content[0].text

    # Extract JSON array from response
    m = re.search(r"\[[\s\S]+\]", response_text)
    if not m:
        raise ValueError(
            f"No JSON array found in Claude response:\n{response_text[:500]}"
        )
    posts = json.loads(m.group(0))

    validate_posts(posts)

    new_rows = append_posts(posts, existing_rows, fieldnames, week)
    all_rows = existing_rows + new_rows

    with open(TABLE_PATH, "w", newline="", encoding="utf-8") as f:
        f.write(serialize_csv(all_rows, fieldnames))

    print(f"Added {len(new_rows)} posts:")
    for r in new_rows:
        print(f"  {r['item']} | {r['topic']} / {r['type']} / {r['subtopic']}")


if __name__ == "__main__":
    main()
