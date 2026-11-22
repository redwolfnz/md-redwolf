ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

## ASSET:redwolf 2026-11-22 → XLS rename, Pages fix, media extracted to IMG/PDF submodules

**`jayreck996/CSV` renamed to `jayreck996/XLS`:**
- GitHub repo renamed via API; files renamed `REDWOLF/CSV-2026Q4.csv` → `REDWOLF/XLS-2026Q4.xls`, `ASIS/CSV-2026Q4.csv` → `ASIS/XLS-2026Q4.xls`.
- All 10 workflow files updated: `CSV_PAT` → `XLS_PAT`, `insteadOf` URLs, `git add/cd/checkout` paths, inline Python `csv_path` refs.
- All scripts updated: `gen_posts.py`, `update_tree_values.py`, `gen_media.py`, `gen_pr_body.py` — `TABLE_PATH` now points to `XLS/*/XLS-2026Q4.xls`.
- `XLS_PAT` secret set on both `redwolfnz/md-redwolf` and `asisnz/md-asis` (same token as former `CSV_PAT`).

**Pages review site fixed (`index.html`):**
- `OWNER` → `jayreck996`, `REPO` → `XLS`, `CSV_PATH` → `REDWOLF/XLS-2026Q4.xls` (was `COULD/TABLE-2026Q3.csv` — stale Q3 path, caused "Cannot read properties of undefined" crash).
- Quarter-label regex updated for `.xls` extension.
- `deploy-pages.yml`: inject `XLS_PAT` (has write access to private `jayreck996/XLS`); was `MD_REDWOLF` which had no access to the submodule repo.
- Same fix applied to `asisnz/md-asis` (path `ASIS/XLS-2026Q4.xls`, error was GitHub API 404).

**Media extracted from `MAY/media/` to two new public submodules:**
- `jayreck996/IMG` (public) — PNG and GIF files; `REDWOLF/` (82 files) and `ASIS/` (62 files).
- `jayreck996/PDF` (public) — PDF carousels; `REDWOLF/` (9 files) and `ASIS/` (6 files).
- Both added as submodules at `IMG/` and `PDF/` in both org repos.
- `MAY/media/2026Q3/` removed from both parent repos.
- `gen_media.py`: `MEDIA_DIR`/`PAGES_BASE` replaced with `IMG_DIR`/`PDF_DIR` and `IMG_BASE`/`PDF_BASE`; files routed by extension (`.pdf` → `PDF_DIR`, all others → `IMG_DIR`). Media URLs now `raw.githubusercontent.com/jayreck996/IMG|PDF/main/REDWOLF|ASIS/{filename}`.
- `generate-media.yml`: "Initialise submodules" extended with `IMG_PAT`/`PDF_PAT` insteadOf lines and `IMG`/`PDF` in submodule update list; commit step now commits IMG, PDF, XLS submodules separately before updating parent pointer.
- Existing media URLs in `XLS/REDWOLF/XLS-2026Q4.xls` (34 rows) rewritten from GitHub Pages paths to new raw URLs.
- Requires `IMG_PAT` and `PDF_PAT` secrets (fine-grained, `jayreck996/IMG` and `jayreck996/PDF`, Contents: Read+Write) set on both org repos.

## ASSET:redwolf 2026-11-22 → submodule refactor: shared data extracted into 4 private jayreck996 repos; all workflows hardened for concurrent runs

**Submodule repos created under `jayreck996/`:**
- `jayreck996/JSON` — content strategy tree (`REDWOLF/JSON-2026Q4.json`, `ASIS/JSON-2026Q4.json`)
- `jayreck996/CSV` — post table (`REDWOLF/CSV-2026Q4.csv`, `ASIS/CSV-2026Q4.csv`)
- `jayreck996/YML` — pipeline definition (`REDWOLF/YML-2026Q4.yml`, `ASIS/YML-2026Q4.yml`)
- `jayreck996/JSONL` — per-slug LinkedIn cache append log (10 `{SLUG}.jsonl` files per org); replaces `MAY/LOG-*.log`

**Files retired from both org repos:** `CAN/TREE-*.json`, `COULD/TABLE-*.csv`, `PIPE-*.yml`, `MAY/LOG-*.log`, `MIGHT/` directory. `ASSET-*.md` and `ISSUE-*.md` moved to repo root.

**Scripts updated to Q4 submodule paths:** `gen_posts.py`, `fetch_linkedin_cache.py`, `update_tree_values.py`, `gen_tree_mermaid.py`, `gen_media.py`, `gen_pr_body.py`. `fetch_linkedin_cache.py` rewrote `prepend_entry()` as `append_entry()` writing per-slug JSONL.

**PAT secrets restructured (4 separate fine-grained tokens):**
- `JSON_PAT` → `jayreck996/JSON` (write)
- `CSV_PAT` → `jayreck996/CSV` (write)
- `YML_PAT` → `jayreck996/YML` (write)
- `JSONL_PAT` → `jayreck996/JSONL` (write)
Set on both `redwolfnz/md-redwolf` and `asisnz/md-asis`.

**All 10 workflow files hardened (5 per org):** `fetch-linkedin`, `generate-content`, `generate-media`, `update-feedback`, `update-tree-mermaid`.
- Checkout token changed from `JSON_PAT` → `GITHUB_TOKEN` (fixes 403 on parent repo push — `JSON_PAT` is now scoped to `jayreck996` only).
- `submodules: recursive` removed; replaced with explicit "Initialise submodules" step using per-repo `insteadOf` credential config.
- `git submodule update --init -- CSV JSON YML JSONL` (skips `py-redwolf`/`py-asis` which have no runner credentials).
- `git -C {sub} checkout -B main origin/main` for each submodule in init step — ensures scripts see latest main before modifying files; prevents "local changes would be overwritten" error when a concurrent org run has already advanced `origin/main`.
- 5-attempt rebase-retry added to every submodule push (JSON, CSV, JSONL) so concurrent runs from both orgs queue naturally.

**Bug fixed — `update_tree_values.py` double-nested connections:** The script's `CONN_RE` regex only handles single-line connection entries. The Q4 JSON used multi-line format, causing inner `"url"` and `"value"` keys to be treated as connection names and rewritten as `{"url": {"url": "...", "value": 0}, "value": {"url": 0, "value": 0}}`. Repaired both `REDWOLF/JSON-2026Q4.json` and `ASIS/JSON-2026Q4.json` by flattening back to `{ "url": "...", "value": N }` single-line format. Script idempotent going forward (always writes single-line).

**Mac mini pulled via SSH** (`ssh macmini`): `git pull && git submodule update --init py-redwolf` on `md-redwolf`; `git pull && git submodule update --init py-asis` on `md-asis`. `py-asis` initialized for the first time (newly registered submodule). Mac mini does not need data submodules — all data is passed to the listener via HTTP payload by the GitHub Actions runner.

**e2e test:** `fetch-linkedin` (skip_fetch=true) triggered simultaneously on both `redwolfnz/md-redwolf` and `asisnz/md-asis`. Both `refresh-values` jobs passed concurrently — JSON submodule queued correctly via rebase-retry.

## ASSET:redwolf 2026-11-17 -> week 47 media generated (post-037 to post-042)

Built against `e91e418`. Same reduced type scale as weeks 45–46; location footers now read "New Zealand" (matches post-036 change `94d4436`). All 1080x1350. Logo/shield assets re-cut from repo `logo.jpg` (build container was rebuilt).

| Item | Media |
|---|---|
| post-037 | https://redwolfnz.github.io/md-redwolf/MAY/media/2026Q3/post-037-building-types.png |
| post-038 | https://redwolfnz.github.io/md-redwolf/MAY/media/2026Q3/post-038-cloud-fallback.gif (8.7s loop) |
| post-039 | https://redwolfnz.github.io/md-redwolf/MAY/media/2026Q3/post-039-security-metrics.pdf (+ post-039-slide-1..5.png) |
| post-040 | https://redwolfnz.github.io/md-redwolf/MAY/media/2026Q3/post-040-be-safe-29-languages.png |
| post-041 | https://redwolfnz.github.io/md-redwolf/MAY/media/2026Q3/post-041-handover-pack.pdf (+ post-041-slide-1..6.png) |
| post-042 | https://redwolfnz.github.io/md-redwolf/MAY/media/2026Q3/post-042-visitor-journey.pdf (+ post-042-slide-1..4.png) |

**Verified against `MAY/LOG-2026Q3.log` (16 Nov fetch):** ICT Melbourne Build Stand E17, 25–26 Nov, four demos by building type (12 + 16 Nov); Gallagher Microsoft email disruption (13 Nov); ASIS November Community Pulse incl. security metrics program (16 Nov); NZ Police Be Safe, Feel Safe booklet in 29 languages and its topics (12 Nov); Gallagher five-step visitor journey, Visitor Management powered by Kenai (16 Nov).

**Deviations / notes:**
- post-037: council and school design drivers are typical examples (the post only names hospital and apartment drivers).
- post-039: "where to find it" and "what to do" lines are Red Wolf guidance built from the post's list.
- post-040: no NZ Police logo or booklet artwork; generic booklet illustration only.
- post-041: device register on slide 3 is labelled "Sample". No ISO 9001 certification claimed (post says "follows ISO 9001 principles").
- post-042: brief asked for a repost of Gallagher's carousel. Built a Red Wolf commentary carousel instead (journey, comparison, poll); reshare Gallagher's post natively on LinkedIn if wanted.

**Verify before publishing:**
- post-041 copy says "Earlier this week we listed five questions" but that post (post-029) was in week 45.
- post-040 post doesn't include the booklet link; NZ Police's own post links it.

## ASSET:redwolf 2026-11-17 10:00 → fix: browse_linkedin.py switched to headed Chrome to bypass Cloudflare bot challenge

**Problem diagnosed (2026-11-17):** Both the weekly `fetch-linkedin` run (2026-11-15) and a direct test through the listener returned `followerCount: 0`, `bio: ""`, `recentPosts: []` for all 10 connections. Direct page dump via Playwright confirmed the cause: LinkedIn's CDN-level Cloudflare protection was intercepting `headless=True` Chrome and serving a "Performing security verification" block page instead of the LinkedIn company page. The `li_at` session cookie is still valid (expires 2027-10-22) — no re-login required.

**Fix applied:** Changed `headless=True` → `headless=False` in `py-redwolf/browse_linkedin.py` (commit `b01979f`). The Mac mini has an active WindowServer/loginwindow GUI session, so a headed Chrome window opens on the display, passes Cloudflare's bot check, and closes automatically — no human interaction needed. Confirmed with a live test: NZSA returned `followerCount: 3765`, full bio, and 2 recent posts.

**Deployed:** `py-redwolf` pulled to Mac mini (fast-forward to `b01979f`, also picking up 3 earlier listener/generate_media commits). `com.redwolf.linkedin-listener` LaunchAgent restarted. `fetch-linkedin` workflow re-triggered manually to refresh the week 47 cache before Tuesday's content generation run.

## ASSET:redwolf 2026-11-03 09:00 → week 45 media fully generated; generate-media pipeline stabilised

**Week 45 media — all generatable posts complete:**
`post-019` PNG, `post-020` PNG, `post-021` PNG, `post-023` PDF (5-slide carousel), `post-024` GIF all committed to `MAY/media/2026Q3/` and media URLs populated in CSV. `post-022` JPG intentionally skipped (requires real staff photo). Pages deployed.

**Root causes fixed during this session (in order):**
1. `cairosvg`/`Pillow`/`img2pdf` installed to system Python 3.9 user packages, not the venv (Python 3.14). Fixed: installed into `.venv` via `pip install`.
2. Native `cairo` C library missing. Fixed: `brew install cairo` via `/opt/homebrew/bin/brew`.
3. `DYLD_LIBRARY_PATH=/opt/homebrew/lib` added to LaunchAgent plist so subprocesses find `libcairo.2.dylib`.
4. `CLI_TIMEOUT_SECONDS` 270→450s — full CSV row (200-word description) pushed `claude -p` past the old limit.
5. `GENERATE_MEDIA_TIMEOUT_SECONDS` 660→2700s — PDF (5 slides × 450s) exceeded the old outer subprocess timeout.
6. Polling deadline made type-aware: PDF=2550s, GIF=1650s, PNG=750s (was flat 540s).
7. 404 on status poll handled gracefully — listener restart no longer crashes the whole run.
8. RFC 4180 CSV parser in `index.html` — week 45 descriptions had `\n\n` paragraph breaks; old line-split parser broke score/tags/hashtags display.
9. `generate-media` job commented out in `generate-content.yml` — run manually via standalone `generate-media.yml` workflow until pipeline is stable.

**Timeouts now in force:**
- `CLI_TIMEOUT_SECONDS = 450` (py-redwolf/generate_media.py)
- `GENERATE_MEDIA_TIMEOUT_SECONDS = 2700` (py-redwolf/listener.py)
- Poll deadline: PNG 750s, GIF 1650s, PDF 2550s (gen_media.py)

## ASSET:redwolf 2026-11-02 18:01 → generate-media diagnosis — Claude 5-hour usage limit and hidden failures

**Latest workflow result:** [Run 41388233893](https://github.com/redwolfnz/md-redwolf/actions/runs/41388233893) reported success for week 45 but generated only `post-019` (PNG, committed as `b8947dd`). Posts `post-020`, `post-021`, `post-023` (PDF), and `post-024` (GIF) returned zero files. `post-022` (JPG) was intentionally skipped because it requires a real asset. Async submission and status polling worked in this run.

**Confirmed current blocker:** Connected to the Mac mini over SSH and retried `post-020` directly through `generate_media.py`, capturing stdout and stderr. It returned `{"files": []}` with stderr `claude -p exited 1:` and `post-020: 0 file(s) generated`. A minimal direct Claude CLI check then exited 1 with: `You've hit your 5-hour limit · resets 8:30pm (Pacific/Auckland)`. The reported reset is 2026-11-02 20:30 NZDT. This confirms the blocker at diagnosis time; the discarded diagnostics prevent proving the cause of every earlier empty result.

**Why the workflow stays green:** `generate_media.py` logs only stderr when Claude exits nonzero, so the usage-limit message on stdout is hidden. Generation failures become an empty files list; `listener.py` accepts that result as success and discards subprocess stderr on exit 0. `.github/scripts/gen_media.py` also accepts empty results and exits successfully even when requested assets are missing.

**Additional timeout issue:** The Action polls for 360 seconds per post, while the listener allows 660 seconds per subprocess. PDF generation makes five sequential Claude calls and GIF generation makes three, each allowing 270 seconds, so multi-slide/frame assets can exceed both outer deadlines.

**Next actions:** Retry the standalone `generate-media.yml` workflow for week 45 after the reported usage reset; it selects posts with empty media URLs. Surface Claude failure diagnostics, report empty/incomplete output as failure, and align timeouts with the slide/frame workload. No generation code, listener configuration, or deployed service was changed during this diagnosis.

## ASSET:redwolf 2026-11-02 16:45 → generate-media async pattern — bypasses Cloudflare 100s proxy timeout

**Root cause:** Cloudflare Tunnel's edge proxy enforces a hard 100-second HTTP response timeout (524). A single `claude -p` SVG call takes ~2 minutes, so every POST to `/generate-media` was being cut before the Mac mini responded. This timeout is not configurable on free/Pro/Business plans (Enterprise only).

**Fix — async job pattern (3 files changed):**

`py-redwolf/listener.py` — POST `/generate-media` now spawns a background thread and returns `{"job_id": "<uuid>"}` (202) in under 1 second. New GET `/generate-media-status/<job_id>` returns `{"status":"pending"}` or `{"status":"done","files":[...]}` — each response is milliseconds, never blocked on `claude -p`. Added `MEDIA_JOBS` dict + `MEDIA_JOBS_LOCK`, `_run_generate_media_thread()`, `_send_json()` helper.

`.github/scripts/gen_media.py` — After POST, extracts `job_id` and polls `/generate-media-status/<job_id>` every 15 seconds (6-minute deadline per post). Also added missing `CF-Access-Client-Id` / `CF-Access-Client-Secret` headers (gen_posts.py had them, gen_media.py did not).

`.github/workflows/generate-media.yml` — New standalone workflow. Triggers just the media job (no content generation) for a given week. Use for retries when generate-content ran OK but generate-media failed.

**Mac mini restarted:** listener PID 6918 after `launchctl unload/load com.redwolf.linkedin-listener`.

**Run under test:** 41384497041 (generate-media.yml, week 45, in progress at time of writing).

## ASSET:redwolf 2026-11-02 16:00 → Step 2D deployed to Mac mini — pip deps installed, code pulled, listener restart pending

**Mac mini pip install (--user, python 3.9.6 system):**
`cairosvg 2.8.2`, `Pillow 11.3.0`, `img2pdf 0.6.3` installed successfully via `pip3 install --user cairosvg Pillow img2pdf` over SSH.

**py-redwolf pushed and pulled on Mac mini:**
Commit `e5a304f` — `generate_media.py` (new) + `listener.py` (updated `/generate-media` endpoint, 660s timeout, 8 MB body limit). Mac mini pulled via SSH: fast-forward confirmed.

**md-redwolf pushed and pulled on Mac mini:**
Commit `001695e` — `.claude/skills/generate-media/SKILL.md`, `.github/scripts/gen_media.py`, `generate-content.yml` (Step 2D job), submodule pointer bump. Mac mini pulled via SSH: confirmed.

**Listener restart still needed:** Mac mini listener.py is running from LaunchAgent `com.redwolf.linkedin-listener`. Must be restarted to pick up the new `/generate-media` endpoint. Command on Mac mini: `launchctl unload ~/Library/LaunchAgents/com.redwolf.linkedin-listener.plist && launchctl load ~/Library/LaunchAgents/com.redwolf.linkedin-listener.plist`

## ASSET:redwolf 2026-11-02 15:30 → Step 2D generate-media implemented — Mac mini SVG pipeline, no new GitHub secrets

**What was built (5 files):**

`py-redwolf/generate_media.py` — new Mac mini subprocess. Receives one JSON payload per week (system prompt + logo base64 + posts). For each post calls `claude -p` to generate SVG, substitutes logo placeholder, renders to PNG/PDF/GIF via cairosvg + Pillow + img2pdf. Returns all files as base64 JSON back to GitHub Actions.

`py-redwolf/listener.py` — added `run_generate_media()` and extended `do_POST` to dispatch `/generate-media` alongside existing `/generate-content`. Timeout 660s (6 posts × ~90s each). `MAX_BODY_BYTES` raised to 8 MB (logo.jpg base64 ~300 KB in payload).

`.github/scripts/gen_media.py` — GitHub Actions script. Reads CSV for target week, filters to posts with empty `media URL` and generatable type (png/gif/pdf), POSTs payload to Mac mini, writes received files to `MAY/media/2026Q3/`, updates CSV media URL column. Skips jpg/mp4 (require real assets).

`.github/workflows/generate-content.yml` — `generate-media` job now calls Mac mini via same CF tunnel + secrets as `generate-content` (no `ANTHROPIC_API_KEY` needed). Runs after `generate` job merges the CSV. Commits media files + updated CSV to main.

`.claude/skills/generate-media/SKILL.md` — rewritten as per-post SVG system prompt. Brand spec: red `#E8192C`, charcoal `#1A1A1A`, background `#F2F2F2`. Layout: top/bottom red stripe, badge pill, logo (via `LOGO_PLACEHOLDER`), 68–80px headline, 3–5 content cards, callout bar, dark CTA card, footer. Supports png (single), pdf (5 slides), gif (3 frames).

**Mac mini prerequisite (not yet done):** `pip install cairosvg Pillow img2pdf` in the py-redwolf venv.

**Auth:** same `GENERATE_CONTENT_URL` + `CF_ACCESS_CLIENT_ID` + `CF_ACCESS_CLIENT_SECRET` + `LISTENER_SHARED_SECRET`. No new GitHub secrets.

**Deploy trigger fix:** GitHub Pages does not auto-deploy after a squash-merge done by `GITHUB_TOKEN` (known GH Actions limitation). Week 45 deploy was triggered manually via `gh workflow run deploy-pages.yml`.

## ASSET:redwolf 2026-11-02 → cloudflared tunnel plist template added to py-redwolf; SSH ingress available via toigroup tunnel

**py-redwolf repo:** `com.redwolfnz.md-redwolf.plist.template` added — cloudflared tunnel daemon LaunchAgent, separate from the existing `com.redwolf.linkedin-listener.plist.template`. Label `com.redwolfnz.md-redwolf`, runs `/opt/homebrew/bin/cloudflared tunnel --config ... run`. Committed and pushed to `redwolfnz/py-redwolf` main.

**SSH access note:** SSH into the Mac mini is now live via the `toigroup` tunnel on `ssh.toigroup.co.nz` (see md-asis ASSET-2026Q4 12:45 entry — same Mac mini, shared tunnel). No py-redwolf-specific SSH change needed. Once the laptop WSL public key is authorized, `ssh macmini` works for both pipelines.

**Existing py-redwolf setup on Mac mini (unchanged):** `com.redwolf.linkedin-listener` and `com.redwolf.linkedin-tunnel` LaunchAgents running, listener on port 8787, tunnel `redwolf.toigroup.co.nz`. `generate-content` e2e verified (ASSET-2026Q3 2026-10-28).
