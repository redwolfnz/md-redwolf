#!/usr/bin/env python3
"""Replace the Mermaid block between <!-- TREE-START --> and <!-- TREE-END -->
markers in a file containing a PR body. Writes the updated body to stdout.

Usage: replace_tree_section.py <body_file> <mermaid_file>
"""

import sys

START_MARKER = "<!-- TREE-START -->"
END_MARKER = "<!-- TREE-END -->"


def replace_section(body: str, new_mermaid: str) -> str:
    start = body.find(START_MARKER)
    end = body.find(END_MARKER)

    if start == -1 or end == -1:
        # Markers missing — append the section at the end
        return (
            body.rstrip()
            + f"\n\n{START_MARKER}\n{new_mermaid}\n{END_MARKER}\n"
        )

    return (
        body[: start + len(START_MARKER)]
        + "\n"
        + new_mermaid
        + "\n"
        + body[end:]
    )


if __name__ == "__main__":
    body_file, mermaid_file = sys.argv[1], sys.argv[2]

    with open(body_file, encoding="utf-8") as f:
        body = f.read()
    with open(mermaid_file, encoding="utf-8") as f:
        new_mermaid = f.read().strip()

    print(replace_section(body, new_mermaid), end="")
