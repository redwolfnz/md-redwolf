ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

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
