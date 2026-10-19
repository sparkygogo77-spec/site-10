# STATE: the one file every Lantern chat reads first

Lives on `claude/lantern-redesign-pass2`. Two kinds of Claude work on this project and they never talk directly, so
this file (plus the repo) is the hand-off between them:

| Side | Where | Good at |
|---|---|---|
| **Project threads** (claude.ai Code project "Site 10") | cloud, headless Blender on CPU | building passes, game code, PRs, merging, jars |
| **Desktop session** (Claude Code app, folder `C:\Users\Josh\Documents\LanternLive`) | J's PC, GPU, the real `.blend` files | rendering passes (EEVEE), the review site push, anything that needs the PC |

Account setting "Require trusted devices" blocks project threads from reaching the PC, so nothing can be pushed to it:
all sharing goes through git.

## Rules (both sides)

1. **Start:** `git pull`, read this file top to bottom. Don't re-read the whole repo; follow the links below.
2. **End:** edit the sections below (queue, waiting on J, handoff log), `git pull --rebase`, push. A chat that ends
   without updating this file has not finished.
3. Don't copy facts that already live elsewhere; link them. The source of truth for passes is
   `docs/blender/review/INBOX.md`, for ratings `RATINGS.md`, for J's chat decisions `DECISIONS.md`.
4. Keep it short (target under 80 lines). Move finished items out; history lives in git.
5. Only the desktop session pushes to `review-site` (each push is one Vercel deploy), via the renderer. Cloud threads
   never push there except to change site code.

## Render queue (desktop session owns it)

- **What needs rendering:** every INBOX entry marked `[status: WAITING]`
  (`grep -c "status: WAITING" docs/blender/review/INBOX.md`; 25 on 2026-10-19). Start with 863, 860, 859, 861, 862.
- **How:** from `C:\Users\Josh\Documents\LanternLive`: `git -C review-site pull` (a stale `lantern_review.py` was why
  863 failed), then double-click `Render Lantern Review.cmd` or run
  `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python review-site\tools\lantern_review.py -- --all`.
  It renders only what needs it, rebuilds the site's status panel and pushes once. Details: `tools/review_site/README.md`.
- **Render log** (desktop session adds a line per run, newest first: date, passes rendered, failures + error line):
  - (none yet)

## Waiting on J

- 30 open design questions with ★ picks: `docs/handoff/2026-10-18-total-handover.md` Part 1 (copy of J's handover).
- Rate the passes on https://lantern-review-j.vercel.app (D1-D12 on Pass 950 first).
- Not Claude's to decide: PR #356, #360 and #361 review/merge (below).

## Open PRs (2026-10-19)

- #361 `tools/blender_pipeline/check_pass.py` one-process EEVEE self-check (target: Blender branch)
- #360 review site "Most recent" ordering (target: `review-site`, draft)
- #356 README/CLAUDE.md catch-up (target: `main`)

## Project threads (cloud)

Tidy up site-10 (#356) · Blender model system plan (#361) · Pass 863 render failure (waiting on the PC fix above) ·
Most recent passes view (#360) · Link desktop renderer and project (this file).

## Last jar

2.1.1712+26.3 (main at #339). Link: https://github.com/sparkygogo77-spec/site-10/raw/builds/lantern-ring-latest.jar.
Check `git show origin/builds:latest.json` for newer.

## Handoff log (newest first, one line each: date, side, what changed, what the next chat should do)

- 2026-10-19 project thread: created STATE.md and the desktop kickoff prompt (`docs/handoff/DESKTOP-KICKOFF.md`).
  Next: desktop session renders the WAITING passes and fills in the render log above.
