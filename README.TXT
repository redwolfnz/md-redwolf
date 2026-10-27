RED WOLF — LinkedIn Content Orchestration Plan
Last updated: 2026-10-22

Client:   Red Wolf High Level Security Ltd
Platform: LinkedIn
Purpose:  Structured weekly content generation, review, and publishing

============================================================
REPO STRUCTURE
============================================================
  CAN/   — what the content must follow (strategy, rules)
  COULD/ — what the content should contain (posts, media)
  MAY/  — what the content could reference (assets, values)
  MIGHT/  — what has happened (activity log)

============================================================
CONTENT STRUCTURE
============================================================
tree[]
  category        — one of 6 pillars (see below)
    type          — content format within that pillar
      subtype     — specific angle or topic

6 pillars and their role:
  SERVICES    — what Red Wolf does (installs, monitoring, consulting)
  INDUSTRY    — market context (threats, regulation, technology)
  AUTHORITY   — credibility signals (awards, thought leadership, partnerships)
  PEOPLE      — human side (team, culture, careers)
  TRUST       — proof (case studies, testimonials, certifications)
  ENGAGEMENT  — audience interaction (polls, debates, campaigns)

connections{}
  own           — Red Wolf's own LinkedIn page (tag every post)
  associations  — NZSA, ASIS International, NZ Police
  partners      — Johnson Controls, Gallagher, Inner Range ANZ,
                  Bosch, ICT, Jacques Technologies

============================================================
ORCHESTRATION — HOW TO RUN A CONTENT BATCH
============================================================

STEP 1 — RESEARCH
  1a. fetch-linkedin skill
      Read CAN/TREE-2026Q3.json's connections{} for the list of
      connections and their fixed slugs, then read each connection's
      CAN/TREE-<SLUG>-2026Q3.json — these are pre-cached LinkedIn
      snapshots committed weekly by the GitHub Action fetch-linkedin.yml.
      Claude does not fetch LinkedIn directly and does not use
      claude-in-chrome.

      How the cache is built (private repo py-redwolf, included here as the
      py-redwolf/ submodule; the listener runs from that checkout):
        GitHub Action (weekly cron)
          → Cloudflare Tunnel → py-redwolf/listener.py on mac mini
              → runs: browse_linkedin.py (Playwright, saved LinkedIn session)
                  → returns JSON per slug
          → Action commits CAN/TREE-<SLUG>-2026Q3.json to this repo

      For each TREE-<SLUG> file:
        note recent posts, announcements, or campaigns relevant
          to the upcoming content angles
        do not tag a connection whose recentPosts[] is empty or stale

      Fallback (a connection's cache file is missing or stale — the
      pipeline is live as of 2026-10-22, see MAY/ASSET-2026Q3.md, but
      an individual fetch can still fail, e.g. the LinkedIn session
      expiring):
        run a web search for that connection's slug instead.

  1b. select topic
      Read CAN/TREE-2026Q3.json — for each of the 6 pillars
      select a type and subtype that is relevant given what
      was found in step 1a (recent partner activity, industry
      news, or campaign timing should inform the angle).
      Apply the scoring guide to assign a score to each post.

  1c. choose artifact
      For each selected post decide the media-type:
        png  — branded graphic, infographic, diagram, card, timeline
        jpg  — photo (staff, site, event)
        gif  — short looping animation (diagram, flow, before/after)
        pdf  — multi-slide carousel / document
        mp4  — video

STEP 2 — GENERATE
  Open COULD/TABLE-2026Q3.csv and add 6 new rows for the next
  week number — one per pillar — using the selections from STEP 1:
    topic, type, subtopic, score, media-type already decided
    write title, description, tags, hashtags
    tags: @Red Wolf always; partners only if directly relevant
  Set all new posts to BLOCKED status until media is ready

STEP B — OPEN WEEKLY PR
  After STEP 2, commit directly to main and open a PR from main so the
  client can review posts and suggest changes through STEPS 3–5.

  1. Stage and commit the generated files:
       git add COULD/TABLE-2026Q3.csv MIGHT/LOG-2026Q3.log
       git commit -m "content(w<NN>): generate week <NN> batch — post-0XX to post-0XX"
       git push

  2. Open the PR using the template below.
     The <!-- TREE-START --> / <!-- TREE-END --> markers tell the
     update-tree-mermaid GitHub Action where to refresh the Mermaid
     diagram automatically whenever CAN/TREE-<quarter>.json changes on main.

  PR TEMPLATE
  ───────────
  ## Week <NN> — 6 posts, all BLOCKED pending media

  | Post | Pillar | Subtype | Score | Media |
  |------|--------|---------|-------|-------|
  | post-0XX | <PILLAR> | <Type> / <Subtype> | <score> | <ext> |
  ... (one row per post)

  ## Research signals (STEP 1a)

  - **<CONNECTION>** (<date>) — <finding> → post-0XX
  ... (one bullet per signal that drove a selection)
  - **BOSCH** — page inactive (Keenfinity Group since Jul 2026); not tagged
  - **JACQUES** — last post <date>; not tagged   (if still inactive)

  ## Next steps

  - [ ] Generate media for post-0XX to post-0XX (STEP 3)
  - [ ] Client review via index site (STEP 4)
  - [ ] Update status from BLOCKED → READY when media is approved

  ---

  ## Content Strategy Tree

  > Auto-updated from `CAN/TREE-<quarter>.json` — suggest changes by commenting below.

  <!-- TREE-START -->
  <paste current output of: python3 .github/scripts/gen_tree_mermaid.py>
  <!-- TREE-END -->
  ───────────

STEP 3 — MEDIA
  Generate or source media, save to COULD/media/<quarter>/,
  log each asset in MAY/ASSET-2026Q3.md.

STEP 4 — REVIEW
  Client reviews posts via the index site (GitHub Pages).
  Feedback is written back to the CSV via GitHub Actions.

STEP 5 — PUBLISH
  Download media locally (LinkedIn does not accept URLs).
  Copy title, description, tags, and hashtags from the CSV.
  Upload to LinkedIn and log outcome in MIGHT/LOG-2026Q3.log.

============================================================
CONTENT GENERATION RULES
============================================================
1. One post per pillar per week — 6 posts per batch.
2. Do not repeat the same subtype within the same quarter.
3. Score each post using the scoring guide below.
4. Research (STEP 1) must be completed before generating —
   subtype selection in 1b must be informed by what 1a found.
5. Only tag partners when the post is directly relevant to
   their product or domain.
6. Set media-type to the expected output file format:
     png  — branded graphic, infographic, diagram, card, timeline
     jpg  — photo (staff, site, event)
     gif  — short looping animation (diagram, flow, before/after)
     pdf  — multi-slide carousel / document
     mp4  — video
7. All new posts go into TABLE-2026Q3.csv with status BLOCKED
   until media and any required approvals are in place.
8. Each batch must use at least 3 distinct media types.

============================================================
SCORING GUIDE
============================================================
Score = base pillar score, adjusted down by type or subtype
where the content carries less authority or proof weight.

Base scores by pillar:
  AUTHORITY   — 10  (strongest credibility signal)
  TRUST       — 9   (proof and social validation)
  INDUSTRY    — 8   (market relevance)
  PEOPLE      — 8   (human interest)
  SERVICES    — 7   (what we do)
  ENGAGEMENT  — 7   (audience interaction)

Type/subtype adjustments (override base where listed):
  AUTHORITY / Awards & Milestones       — 10  (no adjustment)
  AUTHORITY / Thought Leadership        — 8   (opinion, not proof)
  AUTHORITY / Accreditations            — 8   (credential signal)
  TRUST / Case Studies                  — 9   (no adjustment)
  TRUST / Testimonials & Social Proof   — 8   (softer than case study)
  TRUST / Compliance & Certifications   — 8
  PEOPLE / Team Spotlight / Staff Profile — 7 (lower reach)
  ENGAGEMENT / Campaigns & Seasonal     — 8   (higher reach potential)

Calculation:
  1. Start with the base pillar score.
  2. If the type or subtype appears in the adjustments above,
     use that value instead.
  3. If the subtype is weaker than the type average (e.g. a
     poll vs a campaign), round down by 1.
  4. Final score must be between 1 and 10.

============================================================
EXTENDING THE TREE
============================================================
- New subtypes can be added to any existing type.
- New types require a new entry under the relevant category.
- New categories require a new pillar entry and a justification
  for why it fits the Red Wolf brand strategy.
- Connection slugs must be verified on LinkedIn before adding.

============================================================
KEY FILES
============================================================
  CAN/TREE-2026Q3.json              content strategy skeleton
  CAN/TREE-<SLUG>-2026Q3.json       per-connection LinkedIn cache
                                      (written by fetch-linkedin.yml;
                                      none exist yet — see ASSET log)
  COULD/TABLE-2026Q3.csv            all posts, all weeks
  COULD/media/2026Q3/               post media files
  MAY/ASSET-2026Q3.md              asset log (status, verify notes)
  MIGHT/LOG-2026Q3.log               activity log
  .claude/skills/fetch-linkedin/     STEP 1a skill (reads the cache above)
  .github/workflows/fetch-linkedin.yml   weekly cache-refresh Action

============================================================
QUARTER ROLLOVER
============================================================
  At the start of a new quarter:
  - Create CAN/TREE-<year><Q>.json   (copy + update meta)
  - Create COULD/TABLE-<year><Q>.csv (new header, empty rows)
  - Create MAY/ASSET-<year><Q>.md   (fresh log)
  - Create MIGHT/LOG-<year><Q>.log    (fresh log)
  - Update this file: client, quarter, key files section
============================================================
