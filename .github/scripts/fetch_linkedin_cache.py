#!/usr/bin/env python3
"""
Called by .github/workflows/fetch-linkedin.yml (weekly cron).

Reads CAN/TREE-2026Q3.json's connections{}, maps each to its fixed slug
(same table as .claude/skills/fetch-linkedin/SKILL.md — keep both in
sync if connections{} ever changes), and calls py-redwolf's listener
once per connection, sequentially with a pause between calls, writing
each successful response to CAN/TREE-<SLUG>-2026Q3.json.

A failed/unreachable call for one connection is logged and skipped —
it never fails the whole job, and never overwrites that connection's
existing cache file with bad data. A missing cache file is exactly
what the fetch-linkedin skill (STEP 1a) already treats as MISSING.

Quarter is hardcoded as 2026Q3, matching every other file in this
repo this quarter — update it at quarter rollover alongside the rest
of README.md's QUARTER ROLLOVER section.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUARTER = "2026Q3"
TREE_FILE = REPO_ROOT / "CAN" / f"TREE-{QUARTER}.json"
SECONDS_BETWEEN_CALLS = 30
REQUEST_TIMEOUT = 90

# Must match .claude/skills/fetch-linkedin/SKILL.md's mapping table.
SLUG_MAP = {
    "Red Wolf High Level Security Ltd": "REDWOLF",
    "New Zealand Security Association (NZSA)": "NZSA",
    "ASIS International": "ASIS",
    "NZ Police": "NZPOLICE",
    "Johnson Controls": "JOHNSON",
    "Gallagher Security": "GALLAGHER",
    "Inner Range ANZ": "INNERRANGE",
    "Bosch Security and Safety Systems": "BOSCH",
    "Integrated Control Technology (ICT)": "ICT",
    "Jacques Technologies": "JACQUES",
}


def load_connections() -> list[tuple[str, str, str]]:
    """Returns [(slug, companyName, url), ...] from connections{}."""
    data = json.loads(TREE_FILE.read_text())
    connections = data.get("connections", {})
    out = []
    for group in ("own", "associations", "partners"):
        for name, url in connections.get(group, {}).items():
            slug = SLUG_MAP.get(name)
            if not slug:
                print(f"WARNING: no slug mapping for connection {name!r} — "
                      f"skipping. Add it to SLUG_MAP and the fetch-linkedin "
                      f"skill's table.", file=sys.stderr)
                continue
            out.append((slug, name, url))
    return out


def fetch_one(base_url: str, slug: str, company_name: str, url: str,
              cf_client_id: str, cf_client_secret: str, shared_secret: str) -> bytes | None:
    qs = urllib.parse.urlencode({"slug": slug, "companyName": company_name, "url": url})
    full_url = f"{base_url}?{qs}"
    # urllib's default User-Agent ("Python-urllib/x.y") gets blocked
    # outright before reaching the tunnel at all — confirmed live: every
    # connection came back HTTP 403 on the first real run, and curl with
    # that same UA spoofed got blocked identically, while a normal UA
    # (or this custom one) passes. Most likely Cloudflare's Bot Fight
    # Mode or a similar default WAF rule blocking known bot/script UAs.
    headers = {
        "User-Agent": "redwolf-linkedin-fetch/1.0 (+https://github.com/redwolfnz/md-redwolf)",
    }
    if cf_client_id and cf_client_secret:
        headers["CF-Access-Client-Id"] = cf_client_id
        headers["CF-Access-Client-Secret"] = cf_client_secret
    if shared_secret:
        headers["X-Listener-Secret"] = shared_secret

    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                print(f"slug={slug}: HTTP {resp.status} — skipping", file=sys.stderr)
                return None
            return resp.read()
    except urllib.error.HTTPError as exc:
        print(f"slug={slug}: HTTP {exc.code} — skipping", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"slug={slug}: request failed ({exc}) — skipping", file=sys.stderr)
        return None


def main() -> int:
    base_url = os.environ.get("LINKEDIN_FETCH_URL", "")
    if not base_url:
        print("LINKEDIN_FETCH_URL is not set — nothing to do", file=sys.stderr)
        return 1

    cf_client_id = os.environ.get("CF_ACCESS_CLIENT_ID", "")
    cf_client_secret = os.environ.get("CF_ACCESS_CLIENT_SECRET", "")
    shared_secret = os.environ.get("LISTENER_SHARED_SECRET", "")

    connections = load_connections()
    print(f"Fetching {len(connections)} connections, "
          f"{SECONDS_BETWEEN_CALLS}s apart...")

    fetched, skipped = 0, 0
    for i, (slug, company_name, url) in enumerate(connections):
        body = fetch_one(base_url, slug, company_name, url,
                          cf_client_id, cf_client_secret, shared_secret)
        if body is None:
            skipped += 1
        else:
            out_path = REPO_ROOT / "CAN" / f"TREE-{slug}-{QUARTER}.json"
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                print(f"slug={slug}: non-JSON response — skipping", file=sys.stderr)
                skipped += 1
                continue
            out_path.write_text(json.dumps(parsed, indent=2) + "\n")
            fetched += 1
            print(f"slug={slug}: wrote {out_path.relative_to(REPO_ROOT)}")

        if i < len(connections) - 1:
            time.sleep(SECONDS_BETWEEN_CALLS)

    removed = _remove_orphaned_cache_files(connections)

    print(f"Done: {fetched} written, {skipped} skipped, {removed} orphaned removed.")
    return 0  # never fail the job over individual connection failures


def _remove_orphaned_cache_files(connections: list) -> int:
    """connections{} in CAN/TREE-2026Q3.json can change at any time —
    a connection being removed/renamed shouldn't leave its old cache
    file sitting in CAN/ forever, where it'd never be read (the skill
    only looks up slugs it finds in the CURRENT connections{}) but
    would clutter the repo indefinitely. Removes any
    CAN/TREE-<SLUG>-2026Q3.json whose slug isn't in this run's
    connections list."""
    current_slugs = {slug for slug, _, _ in connections}
    removed = 0
    for path in (REPO_ROOT / "CAN").glob(f"TREE-*-{QUARTER}.json"):
        slug = path.stem[len("TREE-"):-len(f"-{QUARTER}")]
        if slug not in current_slugs:
            print(f"slug={slug}: connection no longer in connections{{}} — "
                  f"removing orphaned {path.relative_to(REPO_ROOT)}")
            path.unlink()
            removed += 1
    return removed


if __name__ == "__main__":
    sys.exit(main())
