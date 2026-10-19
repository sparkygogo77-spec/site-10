# STATE: the one file every Lantern chat reads first

Lives on `claude/lantern-redesign-pass2`. Two kinds of Claude work on this project and they never talk directly, so
this file (plus the repo) is the hand-off between them:

| Side | Where | Good at |
|---|---|---|
| **Project threads** (claude.ai Code project "Site 10") | cloud, headless Blender on CPU | building passes, game code, PRs, merging, jars |
| **Desktop session** = the **PC chat** (Claude Code app, folder `C:\Users\Josh\Documents\LanternLive`) | J's PC, RTX 5070 Ti, the real `.blend` files | rendering passes (EEVEE), building each pass's `.blend` from its script, GPU look-dev, the review site push, managing project threads |

Project threads can't reach the PC ("Require trusted devices"), so they share through git. The PC chat reaches them:
it reads and posts in the project through its built-in browser, and picks up `docs/pc_requests/` every 10 minutes.
**New Blender thread:** paste `docs/handoff/NEW-CHAT-PROMPT.md` (brief: `PROJECT-CHAT-BRIEF.md`, menu:
`docs/library/LIBRARY.md`).

## Next chat

Paste into a new Claude Code session in LanternLive (also in `LanternLive/NEXT-CHAT-PROMPT.txt`):

```
Start up as my Lantern Ring PC chat: pull C:\Users\Josh\Documents\LanternLive\site-10, then follow
site-10\docs\handoff\PC-CHAT-BRIEF.md section 1 in full and show me the menu.
Today: proper lantern models from J:dark_lantern (passes 600-699).
```

## Rules (both sides)

1. **Start:** `git pull`, read this file top to bottom. Don't re-read the whole repo; follow the links below.
2. **End:** edit the sections below (queue, waiting on J, handoff log), `git pull --rebase`, push. A chat that ends
   without updating this file has not finished.
3. Don't copy facts that already live elsewhere; link them. The source of truth for passes is
   `docs/blender/review/INBOX.md`, for ratings `RATINGS.md`, for J's chat decisions `DECISIONS.md`.
4. Keep it short (target under 80 lines). Move finished items out; history lives in git.
5. Only the desktop session pushes to `review-site` (each push is one Vercel deploy). Renders and site saves go to the
   `site-data` branch instead (no deploy; `tools/review_site/README.md` "Saving without a deploy"). Cloud threads
   never push to review-site except to change site code.

## Render queue (desktop session owns it)

- **What needs rendering:** every INBOX entry marked `[status: WAITING]`
  (`grep -c "status: WAITING" docs/blender/review/INBOX.md`; 26 on 2026-10-19). Start with 863, 860, 859, 861, 862; new: 410 (movement\flight_barrier2.blend) and 409 P3 rev 4.
- **How:** from `C:\Users\Josh\Documents\LanternLive`: `git -C review-site pull` (a stale `lantern_review.py` was why
  863 failed), then double-click `Render Lantern Review.cmd` or run
  `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python review-site\tools\lantern_review.py -- --all`.
  It renders only what needs it, rebuilds the site's status panel and pushes to `site-data` (no deploy). Details: `tools/review_site/README.md`.
- **Render log** (desktop session adds a line per run, newest first: date, passes rendered, failures + error line):
  - 2026-10-18 18:51 PC: 863 (17 takes, 0 failed) after the texture-library fix; earlier run: 409 done, 863 failed (y1 texture missing).

## Waiting on J

- 30 open design questions with ★ picks: `docs/handoff/2026-10-18-total-handover.md` Part 1 (copy of J's handover).
- Rate the passes on https://lantern-review-j.vercel.app (D1-D12 on Pass 950 first).
- Not Claude's to decide: PR #356, #360 and #361 review/merge (below).
- From the PC chat fold-in: (1) adopt the "PC builds the .blend" Deliver-step change in the modeller skill? (2) should cloud
  chats stop running `pull_reviews.py`?

## Open PRs (2026-10-19)

- #361 `tools/blender_pipeline/check_pass.py` one-process EEVEE self-check (target: Blender branch)
- #360 review site "Most recent" ordering (target: `review-site`, draft)
- #356 README/CLAUDE.md catch-up (target: `main`)

## Project threads (cloud)

Tidy up site-10 (#356) · Blender model system plan (#361) · Pass 863 render failure (waiting on the PC fix above) ·
Most recent passes view (#360) · Link desktop renderer and project (this file) ·
Blender: new thread test (movement 400-499): 409 P3 rev 4, pass 410 P1a-c, waiting on render and J's pick.

## Last jar

2.1.1712+26.3 (main at #339). Link: https://github.com/sparkygogo77-spec/site-10/raw/builds/lantern-ring-latest.jar.
Check `git show origin/builds:latest.json` for newer.

## Handoff log (newest first, one line each: date, side, what changed, what the next chat should do)
- 2026-10-18 PC side session: site saves and PC renders go to branch `site-data` (private site-10) via `/api/files`
  and `assets/sitefiles.js` (no Vercel deploy). Next: features that save files (catalogue "Make 3D for this") use `SiteFiles.save`.

- 2026-10-19 J: saved updated `lantern-ring-design` and `lantern-coordinator` skills from `retired/2026-10-18-pc-chat.md`
  (marked FOLDED; modeller skill unchanged). Next: J answers the two open questions in "Waiting on J".
- 2026-10-19 project thread (Blender, movement 400-499): J said "p 409". Pushed pass 410 (primed lance P1a-c, script + spec + review folder)
  and 409 P3 rev 4 (brick nose). Next: PC renders 410 and 409 P3 (builds `movement\flight_barrier2.blend`); J picks. Note:
  `pull_reviews.py` got a proxy 403 in the cloud session, so ratings were read from the repo copy.
- 2026-10-18 PC chat: renderer builds `.blend` files from scripts (9f7138b); one-prompt Blender threads
  (`NEW-CHAT-PROMPT.md`), skills copied to `docs/skills/`, asset library `docs/library/`, request queue `docs/pc_requests/`.
  Next: threads push scripts + specs only; coordinator folds `2026-10-18-pc-builds-blends.md` into the skills.
- 2026-10-19 project thread: created STATE.md and the desktop kickoff prompt (`docs/handoff/DESKTOP-KICKOFF.md`).
  Next: desktop session renders the WAITING passes and fills in the render log above.
