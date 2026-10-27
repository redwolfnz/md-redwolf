#!/usr/bin/env python3
"""Generate a Mermaid graph LR from CAN/TREE-<quarter>.json.

Writes a ```mermaid block to stdout.
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

    for cat in data["tree"]:
        cat_id = safe_id(cat["category"])
        lines.append(f'  ROOT --> {cat_id}["{cat["category"]}"]')
        for t in cat["types"]:
            type_id = f'{cat_id}_{safe_id(t["type"])}'
            lines.append(f'  {cat_id} --> {type_id}["{t["type"]}"]')
            for s in t["subtypes"]:
                sub_id = f'{type_id}_{safe_id(s["name"])}'
                lines.append(f'  {type_id} --> {sub_id}("{s["name"]}")')

    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else TREE_FILE
    print(gen_mermaid(path))
