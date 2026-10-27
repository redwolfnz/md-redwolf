#!/usr/bin/env python3
"""Replace the Mermaid block between <!-- TREE-START --> and <!-- TREE-END -->
in a GitHub PR description.

Usage: replace_tree_section.py <pr_number> <mermaid_file>

Requires the gh CLI and GH_TOKEN in the environment.
"""

import subprocess
import sys

START_MARKER = "<!-- TREE-START -->"
END_MARKER = "<!-- TREE-END -->"


def get_pr_body(pr_number: str) -> str:
    result = subprocess.run(
        ["gh", "pr", "view", pr_number, "--json", "body", "--jq", ".body"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def set_pr_body(pr_number: str, body: str) -> None:
    subprocess.run(
        ["gh", "pr", "edit", pr_number, "--body", body],
        check=True,
    )


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
    pr_number, mermaid_file = sys.argv[1], sys.argv[2]

    with open(mermaid_file, encoding="utf-8") as f:
        new_mermaid = f.read().strip()

    body = get_pr_body(pr_number)
    updated = replace_section(body, new_mermaid)

    if updated != body:
        set_pr_body(pr_number, updated)
        print(f"PR #{pr_number} description updated.")
    else:
        print("No change — Mermaid block already up to date.")
