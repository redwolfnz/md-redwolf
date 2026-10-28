#!/usr/bin/env python3
"""
Step 1b: write reviewer-feedback "value" onto CAN/TREE-<quarter>.json.

One rule, applied to both sides of every rated post:
    value = wins - losses   (win +1, tie 0, lost -1)

  - subtypes: each rated post credits the subtype named by its
    topic / type / subtopic (== tree category / type / subtype name).
    Written as "value" on the one-line subtype objects.
  - connections: each rated post credits every connection cited in its
    free-text "sources" column (own / associations / partners). Written to a
    top-level "connectionsValue" object laid out like connections{}. It is a
    sibling key on purpose: connections{} maps name -> url and the fetch
    script, skill and Mermaid generator all read it that way.

Counts come from COULD/TABLE-<quarter>.csv. Unrated posts count for nothing.

The tree is hand-edited, so only the subtype lines and the connectionsValue
block are rewritten; every other byte is left alone. Idempotent. A stale
"rated" field or "connectionsUsed" block from earlier versions is removed.
Feedback rows that match no subtype are printed to stderr (a renamed subtype
would otherwise silently lose its value).

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
BLOCK_KEYS = ('  "connectionsValue"', '  "connectionsUsed"')  # current, retired

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


def load_rated_rows() -> list:
    """Rows with a win/tie/lost verdict: [(score, topic, type, subtopic, sources)]."""
    rows = []
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {(k or "").strip(): v for k, v in row.items()}
            verdict = (row.get("feedback") or "").strip().lower()
            if verdict in SCORES:
                rows.append((SCORES[verdict], row["topic"], row["type"],
                             row["subtopic"], row.get("sources") or ""))
    return rows


def alias_patterns(name: str) -> list:
    spellings = {re.sub(r"\s*\(.*?\)", "", name).strip(), name, *ALIASES.get(name, [])}
    spellings.update(re.findall(r"\(([^)]+)\)", name))
    return [re.compile(rf"(?<!\w){re.escape(x)}(?!\w)", re.I) for x in spellings if x]


def connection_values(connections: dict, rated: list) -> dict:
    values = {}
    for group in GROUPS:
        values[group] = {}
        for name in connections.get(group, {}):
            pats = alias_patterns(name)
            values[group][name] = sum(
                score for score, _, _, _, sources in rated
                if any(p.search(sources) for p in pats)
            )
    return values


def render_block(values: dict) -> list:
    lines = ['  "connectionsValue": {']
    groups = [g for g in GROUPS if values.get(g)]
    for gi, group in enumerate(groups):
        lines.append(f'    {json.dumps(group)}: {{')
        names = list(values[group])
        for ni, name in enumerate(names):
            comma = "," if ni < len(names) - 1 else ""
            lines.append(f'      {json.dumps(name, ensure_ascii=False)}: {values[group][name]}{comma}')
        lines.append("    }" + ("," if gi < len(groups) - 1 else ""))
    lines.append("  },")
    return lines


def apply_block(lines: list, block: list) -> list:
    """Replace an existing (or retired) connections block, else insert before "tree"."""
    for i, line in enumerate(lines):
        if line.startswith(BLOCK_KEYS):
            end = next(j for j in range(i, len(lines)) if lines[j] == "  },")
            return lines[:i] + block + lines[end + 1:]
    at = next(i for i, line in enumerate(lines) if line.startswith('  "tree"'))
    return lines[:at] + block + lines[at:]


def main() -> None:
    rated = load_rated_rows()
    subtype_values = defaultdict(int)
    for score, topic, type_, subtopic, _ in rated:
        subtype_values[(topic, type_, subtopic)] += score

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
            sub.pop("rated", None)
            sub["value"] = subtype_values.get(key, 0)
            body = ", ".join(
                f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                for k, v in sub.items()
            )
            line = f"{m.group(1)}{{ {body} }}{m.group(3)}"
        out.append(line)

    for key in subtype_values:
        if key not in seen:
            print(f"WARNING: feedback for {key} matches no tree subtype", file=sys.stderr)

    connections = json.loads(TREE_PATH.read_text(encoding="utf-8")).get("connections", {})
    out = apply_block(out, render_block(connection_values(connections, rated)))

    new = "\n".join(out)
    if new != TREE_PATH.read_text(encoding="utf-8"):
        TREE_PATH.write_text(new, encoding="utf-8")
        print("Tree values updated.")
    else:
        print("Tree values already current.")


if __name__ == "__main__":
    main()
