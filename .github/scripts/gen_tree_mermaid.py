#!/usr/bin/env python3
"""Generate a Mermaid graph LR from CAN/TREE-<quarter>.json.

Writes a ```mermaid block to stdout. Subtypes carrying reviewer feedback
(`rated` > 0 in the tree) show their net `value` and are coloured by outcome.
Called by update-tree-mermaid.yml; update TREE_FILE at quarter rollover.
"""

import json
import re
import sys

TREE_FILE = "CAN/TREE-2026Q3.json"


def safe_id(text: str) -> str:
    """Strip non-alphanumeric chars to make a valid Mermaid node id."""
    return re.sub(r"[^A-Za-z0-9]", "_", text)


def gen_mermaid(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    quarter = data["meta"]["quarter"]
    lines = [
        "```mermaid",
        "graph LR",
        f'  ROOT(["🔴 Red Wolf · {quarter}"])',
    ]

    # connections{} comes before tree[] in the JSON — render it first
    conns = data.get("connections", {})
    if conns:
        lines.append('  ROOT --> CONNECTIONS["connections"]')
        group_labels = {"own": "own", "associations": "associations", "partners": "partners"}
        for group, label in group_labels.items():
            members = conns.get(group, {})
            if not members:
                continue
            grp_id = f'CONN_{group}'
            lines.append(f'  CONNECTIONS --> {grp_id}["{label}"]')
            for name in members:
                mem_id = f'{grp_id}_{safe_id(name)}'
                lines.append(f'  {grp_id} --> {mem_id}("{name}")')

    classed = {"win": [], "lost": [], "tie": []}

    # tree[] — grouped under a TREE node to match JSON structure
    lines.append('  ROOT --> TREE["tree"]')
    for cat in data["tree"]:
        cat_id = safe_id(cat["category"])
        lines.append(f'  TREE --> {cat_id}["{cat["category"]}"]')
        for t in cat["types"]:
            type_id = f'{cat_id}_{safe_id(t["type"])}'
            lines.append(f'  {cat_id} --> {type_id}["{t["type"]}"]')
            for s in t["subtypes"]:
                sub_id = f'{type_id}_{safe_id(s["name"])}'
                label = s["name"]
                # value/rated are written by update_tree_values.py; only
                # subtypes with at least one rated post get a badge + colour.
                rated = s.get("rated", 0)
                if rated:
                    value = s.get("value", 0)
                    label += f' · {value:+d} ({rated})' if value else f' · 0 ({rated})'
                    outcome = "win" if value > 0 else "lost" if value < 0 else "tie"
                    classed[outcome].append(sub_id)
                lines.append(f'  {type_id} --> {sub_id}("{label}")')

    # Colour rated subtypes: green = net win, red = net lost, grey = tie
    lines.append("  classDef win fill:#d4edda,stroke:#2e7d32,color:#1b5e20")
    lines.append("  classDef lost fill:#f8d7da,stroke:#c62828,color:#7f0000")
    lines.append("  classDef tie fill:#e2e3e5,stroke:#6c757d,color:#343a40")
    for outcome, ids in classed.items():
        if ids:
            lines.append(f'  class {",".join(ids)} {outcome}')

    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else TREE_FILE
    print(gen_mermaid(path))
