ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

## ASSET:redwolf 2026-11-02 → cloudflared tunnel plist template added to py-redwolf; SSH ingress available via toigroup tunnel

**py-redwolf repo:** `com.redwolfnz.md-redwolf.plist.template` added — cloudflared tunnel daemon LaunchAgent, separate from the existing `com.redwolf.linkedin-listener.plist.template`. Label `com.redwolfnz.md-redwolf`, runs `/opt/homebrew/bin/cloudflared tunnel --config ... run`. Committed and pushed to `redwolfnz/py-redwolf` main.

**SSH access note:** SSH into the Mac mini is now live via the `toigroup` tunnel on `ssh.toigroup.co.nz` (see md-asis ASSET-2026Q4 12:45 entry — same Mac mini, shared tunnel). No py-redwolf-specific SSH change needed. Once the laptop WSL public key is authorized, `ssh macmini` works for both pipelines.

**Existing py-redwolf setup on Mac mini (unchanged):** `com.redwolf.linkedin-listener` and `com.redwolf.linkedin-tunnel` LaunchAgents running, listener on port 8787, tunnel `redwolf.toigroup.co.nz`. `generate-content` e2e verified (ASSET-2026Q3 2026-10-28).