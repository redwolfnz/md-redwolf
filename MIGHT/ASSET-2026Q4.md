ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

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