**FOLDED 2026-10-19** (v# age and reply colours -> design skill; site-data saves, Preview deploys, data gotchas -> coordinator)

# Retired: review site saves without a deploy (PC side session, 2026-10-18 to 19)

## Range / role
Side session of the PC chat for the review site (https://lantern-review-j.vercel.app, branch `review-site`). No pass
numbers used. Built: saving to git from the site and renders reaching the site without a Vercel deploy; pass
versions and age; republished pass 606; proposed the renderer data-file fix (done by its own session, a0466873).

## How it works now
- **Saves from the site** → `POST /api/files` (review-site `api/files.js`) → one commit on the **`site-data` branch of
  site-10** through the GitHub API. Vercel never deploys that branch (`git.deploymentEnabled` in vercel.json on both
  branches). Page code: `<script src="assets/sitefiles.js">`, `SiteFiles.save([{path, blob|text}], "msg")`,
  `SiteFiles.list(prefix)`, `SiteFiles.url(listing, path)`, `SiteFiles.readJSON(path)`. Shows in about 5 s.
- **Reads**: `GET /api/files?prefix=` (newest commit + list, cached 5 s); file urls `/api/files?path=…&b=<blob>&s=<size>`
  are cached by Vercel for good; Range works (phone video); files over 4 MB redirect to a short-lived GitHub link.
  site-10 is private, so nothing uses public raw/jsDelivr links.
- **Renders**: `lantern_review.py` pushes `media/<key>/` + `data/` to `live/` on site-data via a single-branch clone at
  `LanternLive\review-data`; falls back to the old review-site push (1 deploy) if that fails; `--deploy` forces it.
  The page uses `live/data/*.json` when its `generatedAt` is at least as new, and points media/data paths at `live/`.
- **Versions**: `gen_site.py` keeps `data/history.json` (v1, v2… per pass; new version when a take first gets media or
  its `.rev` goes up; backfilled from git) and round links (superseded_by + older pass numbers in title/first sentence).
- Full docs: `tools/review_site/README.md` ("Saving without a deploy", "Versions and age").
- Tested 2026-10-19: save from the live page → commit 393a2663 on site-data, listed after 4.3 s, deployments unchanged.

## Token setup (J only; never in chat or git)
Fine-grained token, only `site-10`, Contents: Read and write → Vercel `lantern-review` → Environment Variables →
`GITHUB_TOKEN`, **Production + Preview**, Sensitive. Expires in a year: when saves answer 503/401, make a new one.

## Open work
- Not yet seen: a real PC render going to site-data (first one creates `LanternLive\review-data`). Check its log says
  "pushed to site-data (no deploy)" and the pass shows on the site.
- Catalogue chat: "Make 3D for this" should save with `SiteFiles.save([{path:"models/<id>.glb", blob}])` (≤3 MB per
  call; bigger .glb: git push to site-data from the PC, not under live/).
- Old media stays on review-site; nothing moves it. Could migrate later to shrink deploys.
- `record_decision.py` comment still names lantern-review-data (it uses the API, so it works).

## Files
- Stray: `LanternLive\site-data` (a worktree from the first version, unused) — remove with
  `git -C review-site worktree remove --force ..\site-data`. The `lantern-review-data` repo was never created.
- site-data branch holds test files `checks/first-save.txt`, `checks/from-site.txt` (harmless).

## Lessons for the design skill
- Workflow: "I need the age or I need a chronological v.# update for every website pass" — every pass on the site
  shows `v# · age` (from 2026-10-19).
- Workflow: J follows side sessions through the first chat; every turn-ending reply starts with 🟡 QUESTION /
  🔵 DONE / 🔴 PERMISSION.

## Gotchas
- **lantern-review deploys are Preview builds** of branch review-site (target null); the domain points at the branch
  alias. Env vars must include **Preview**, and "Redeploy" must be on a review-site deployment — redeploying a `main`
  one is cancelled by the ignoreCommand.
- **The renderer shares `LanternLive\review-site`** and runs `git add -A` + push: never leave uncommitted edits there
  (they get pushed or wiped). Work in a scratch worktree (`git worktree add`) and push from it.
- **Renderer sync kept local `data/`**, deleting data files other chats added (decisions.json, jar.json): fixed in
  a0466873; when republishing by hand, `git checkout origin/review-site -- <missing data files>` first.
- **Port 8765** is used by other sessions' servers; test locally on another port.
- Python heredocs on Windows Git Bash mangle `\b`/`\` in regexes; use the Edit tool for regex lines.
- Media file mtimes are wrong in fresh clones (checkout time): never ship data/site.json built in a scratch worktree;
  let the PC's render rebuild it.
