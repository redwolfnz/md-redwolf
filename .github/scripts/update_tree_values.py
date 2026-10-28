#!/usr/bin/env python3
"""
Write review-feedback totals onto every subtype in CAN/TREE-<quarter>.json
(step 1b), and per-connection source counts next to connections{}.

For each subtype: "rated" = number of posts with a win/tie/lost verdict and
"value" = wins minus losses (win +1, tie 0, lost -1). Counts come from
COULD/TABLE-<quarter>.csv, matched on topic/type/subtopic == category/type/
subtype name. Subtypes with no rated posts get "value": 0, "rated": 0.

The tree is hand-edited, so this rewrites only the one-line subtype objects
and leaves every other byte alone. Idempotent: running it twice is a no-op.
Feedback rows that match no subtype are printed to stderr (a renamed subtype
would otherwise silently lose its score).

It also counts, per connection in connections{}, how many posts cite that
connection in the CSV's free-text "sources" column (each post counted once per
connection) and writes the counts to a top-level "connectionsUsed" object laid
out like connections{} (own / associations / partners). It is a sibling key on
purpose: connections{} maps name -> url and the fetch script, skill and Mermaid
generator all read it that way.

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
GROUPS = ("own", "associations", "partners")

# Extra spellings the generator may use in "sources" for each connection
# (its full name, and any parenthetical in it, are always matched too).
# Keep in sync with connections{} when one is added.
ALIASES = {
    "Red Wolf High Level Security Ltd": ["Red Wolf", "RedWolf"],
    "New Zealand Security Association (NZSA)": ["NZSA"],
    "NZ Police": ["New Zealand Police"],
    "Johnson Controls": ["Johnson"],
    "Gallagher Security": ["Gallagher"],
    "Inner Range ANZ": ["Inner Range"],
    "Bosch Security and Safety Systems": ["Bosch"],
    "Integrated Control Technology (ICT)": ["ICT"],
    "Jacques Technologies": ["Jacques"],
}
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


def load_sources() -> list:
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        return [
            {(k or "").strip(): v for k, v in row.items()}.get("sources", "")
            for row in csv.DictReader(f)
        ]


def alias_patterns(name: str) -> list:
    spellings = {re.sub(r"\s*\(.*?\)", "", name).strip(), name, *ALIASES.get(name, [])}
    spellings.update(re.findall(r"\(([^)]+)\)", name))
    return [re.compile(rf"(?<!\w){re.escape(x)}(?!\w)", re.I) for x in spellings if x]


def count_connections(connections: dict, sources: list) -> dict:
    used = {}
    for group in GROUPS:
        used[group] = {}
        for name in connections.get(group, {}):
            pats = alias_patterns(name)
            used[group][name] = sum(any(p.search(text or "") for p in pats) for text in sources)
    return used


def render_used_block(used: dict) -> list:
    lines = ['  "connectionsUsed": {']
    groups = [g for g in GROUPS if used.get(g)]
    for gi, group in enumerate(groups):
        lines.append(f'    {json.dumps(group)}: {{')
        names = list(used[group])
        for ni, name in enumerate(names):
            comma = "," if ni < len(names) - 1 else ""
            lines.append(f'      {json.dumps(name, ensure_ascii=False)}: {used[group][name]}{comma}')
        lines.append("    }" + ("," if gi < len(groups) - 1 else ""))
    lines.append("  },")
    return lines


def apply_used_block(lines: list, block: list) -> list:
    """Replace an existing connectionsUsed block, else insert before "tree"."""
    for i, line in enumerate(lines):
        if line.startswith('  "connectionsUsed"'):
            end = next(j for j in range(i, len(lines)) if lines[j] == "  },")
            return lines[:i] + block + lines[end + 1:]
    at = next(i for i, line in enumerate(lines) if line.startswith('  "tree"'))
    return lines[:at] + block + lines[at:]


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

    connections = json.loads(TREE_PATH.read_text(encoding="utf-8")).get("connections", {})
    out = apply_used_block(out, render_used_block(count_connections(connections, load_sources())))

    new = "\n".join(out)
    if new != TREE_PATH.read_text(encoding="utf-8"):
        TREE_PATH.write_text(new, encoding="utf-8")
        print("Tree values updated.")
    else:
        print("Tree values already current.")


if __name__ == "__main__":
    main()
