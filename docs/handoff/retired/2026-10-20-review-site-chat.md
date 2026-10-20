FOLDED 2026-10-20 by coordinator 4 (gotchas -> lantern-coordinator "Review site tools on J's PC")

# Retired: review site chat (parked site sub-chat), 2026-10-20

## Range / role

Site chat for the review site (https://lantern-review-j.vercel.app), no Blender builds, no pass numbers used.
Started by coordinator 3 (2026-10-19), last reported to coordinator 4. Three jobs, all live:

| Job | J's words | Commits |
|---|---|---|
| Per-pass report: Copy report / Download report / Report link on each pass page and Control card, `#report/<pass>` URL; header button renamed "Copy all ratings" | "adjust the site so i can take the report of a specific pass from the site" | review-site `39db98ce` |
| Trials area (v2.0106-v2.0108 and later passes with spec `"area": "Trials"`) | "Yes ★", then "Yes, and fix live now" | review-site `713b3ebe`, site-10 `cbdf4979`, site-data `547698b5` |
| Ratings no longer revert when GitHub's rate limit is hit | "Rated it on the website but the website reverted?", "Yes, wake it to fix saves", "Yes, push it ★" | review-site `32486eb7` |

## Open work

None. No WAITING or PARKED passes, no promises outstanding.

## Files

- `LanternLive\review-site` (the renderer's clone) had 3 local render commits not on origin/review-site
  (v2.0104, v2.0105, "left over") as of 2026-10-19. Renders now go to site-data `live/`, so they look like harmless
  leftovers; the renderer resets that clone itself. Nothing else stray; my scratch worktrees are removed.

## Lessons for the design skill

None (site work only).

## Gotchas

- **GitHub rate limit is per user, not per token.** The site's `GITHUB_TOKEN` shares J's 5000 calls/hour with every
  other tool using his account. The biggest site user is `/api/files` serving pictures/clips (`/git/blobs`): about 40
  at once per page open, the first time each new render's files are seen in a CDN region. Vercel's CDN caches them
  after that (Range requests too: `X-Vercel-Cache: HIT`). Fix in place: conditional reads (`If-None-Match`, a 304 is
  free), memory caches (trees, blobs, last good JSON), save = 1 call, render progress written every 30 s, and 429 +
  `resetAt` instead of 500. Runtime logs: Vercel MCP `get_runtime_logs` (Hobby keeps only the last hour: `since: "55m"`).
- **The page must never treat an error reply as data.** `fetch(...).json()` on a 500 gives `{error}`, which looked like
  "no ratings". The page now checks `r.ok`, keeps the last good ratings (`lr-reviews`) and queues taps (`lr-queue`),
  sent as `POST /api/reviews {items:[...]}` with backoff. The old single `{id, rating}` POST still works.
- **Testing site API code without node:** no node/deno on J's PC. Parse-check `api/*.js` in the browser
  (`new Function` after stripping import/export), and run them as blob-URL modules with a fake `fetch` and a small
  `Buffer` shim to test logic. A Python stand-in server for `/api/reviews` (modes ok / limit / 500) plus a read-only
  proxy of other `/api/*` to the live site tests the page without touching live ratings. Through such a proxy, fetch
  source files as `/%61pi/x.js` so they aren't proxied.
- **Shell quoting eats backslashes:** Python one-liners and heredocs turned `\\b` into a backspace and `C:\\Users`
  into `C:Users`. Write patch scripts with the Write tool, and assert each anchor occurs exactly once.
- **The live pass list comes from the PC:** the renderer runs review-site `tools/gen_site.py`, and the page loads the
  newer of the deployed `data/site.json` and site-data `live/data/site.json`. To change an area today, edit both
  copies of `gen_site.py` (site-10 `tools/review_site/` too) and, for an instant change, the `live/` copy.
  A spec's `"area"` only counts if it is listed in `AREAS`.
- **Pushes on another chat's relayed request were blocked** by the safety check; J's yes in this chat unblocked them
  (AskUserQuestion with a "Don't ask, use ★" option).
- **Built-in browser clipboard is refused:** copy buttons need the `execCommand("copy")` fallback, and a real click,
  not a JS `.click()`.
