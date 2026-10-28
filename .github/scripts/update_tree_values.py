#!/usr/bin/env python3
"""
Write review-feedback totals onto every subtype in CAN/TREE-<quarter>.json.

For each subtype: "rated" = number of posts with a win/tie/lost verdict and
"value" = wins minus losses (win +1, tie 0, lost -1). Counts come from
COULD/TABLE-<quarter>.csv, matched on topic/type/subtopic == category/type/
subtype name. Subtypes with no rated posts get "value": 0, "rated": 0.

The tree is hand-edited, so this rewrites only the one-line subtype objects
and leaves every other byte alone. Idempotent: running it twice is a no-op.
Feedback rows that match no subtype are printed to stderr (a renamed subtype
would otherwise silently lose its score).

Usage:  python3 .github/scripts/update_tree_values.py
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

QUARTER = "2026Q3"
ROOT = Path(__file__).resolve().parents[2]
TREE_PATH = ROOT / "CAN" / f"TREE-{QUARTER}.json"
TABLE_PATH = ROOT / "COULD" / f"TABLE-{QUARTER}.csv"

SCORES = {"win": 1, "tie": 0, "lost": -1}
CATEGORY_RE = re.compile(r'^\s*"category":\s*(".*"),?\s*$')
TYPE_RE = re.compile(r'^\s*"type":\s*(".*"),?\s*$')
SUBTYPE_RE = re.compile(r'^(\s*)(\{.*\})(,?)\s*$')


def load_totals() -> dict:
    totals = defaultdict(lambda: {"value": 0, "rated": 0})
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {(k or "").strip(): v for k, v in row.items()}
            verdict = (row.get("feedback") or "").strip().lower()
            if verdict not in SCORES:
                continue
            key = (row["topic"], row["type"], row["subtopic"])
            totals[key]["value"] += SCORES[verdict]
            totals[key]["rated"] += 1
    return totals


def main() -> None:
    totals = load_totals()
    seen = set()
    category = type_ = None
    out = []
    for line in TREE_PATH.read_text(encoding="utf-8").split("\n"):
        if m := CATEGORY_RE.match(line):
            category = json.loads(m.group(1))
        elif m := TYPE_RE.match(line):
            type_ = json.loads(m.group(1))
        elif (m := SUBTYPE_RE.match(line)) and '"name"' in line:
            sub = json.loads(m.group(2))
            key = (category, type_, sub["name"])
            seen.add(key)
            sub["value"] = totals[key]["value"] if key in totals else 0
            sub["rated"] = totals[key]["rated"] if key in totals else 0
            body = ", ".join(
                f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                for k, v in sub.items()
            )
            line = f"{m.group(1)}{{ {body} }}{m.group(3)}"
        out.append(line)

    for key in totals:
        if key not in seen:
            print(f"WARNING: feedback for {key} matches no tree subtype", file=sys.stderr)

    new = "\n".join(out)
    if new != TREE_PATH.read_text(encoding="utf-8"):
        TREE_PATH.write_text(new, encoding="utf-8")
        print("Tree values updated.")
    else:
        print("Tree values already current.")


if __name__ == "__main__":
    main()
