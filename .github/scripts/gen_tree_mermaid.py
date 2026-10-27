#!/usr/bin/env python3
"""Generate a Mermaid mindmap block from CAN/TREE-<quarter>.json.

Writes the block to stdout. Called by update-tree-mermaid.yml.
Update TREE_FILE at quarter rollover.
"""

import json
import sys

TREE_FILE = "CAN/TREE-2026Q3.json"


def gen_mermaid(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    quarter = data["meta"]["quarter"]
    lines = [
        "```mermaid",
        "mindmap",
        f"  root((Red Wolf<br/>Content Tree<br/>{quarter}))",
    ]

    for cat in data["tree"]:
        lines.append(f"    {cat['category']}")
        for t in cat["types"]:
            lines.append(f"      {t['type']}")
            for s in t["subtypes"]:
                lines.append(f"        {s['name']}")

    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else TREE_FILE
    print(gen_mermaid(path))
