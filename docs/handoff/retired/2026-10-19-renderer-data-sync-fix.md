# Retired: renderer data/ sync fix (side session)

## Range / role
One-off fix to the PC review renderer. No passes; last pass number used: none.

Bug: `sync_with_site()` in the renderer (and the same lines in `LanternLive\RENDER.ps1`) ran
`reset --mixed origin/review-site`, then checked out everything except `media/` and `data/`, then `add -A`. Data files
other chats added online (decisions.json, jar.json, history.json) didn't exist in the PC clone, so they were staged as
deletions on every run.

Fix: after that checkout, list `data/` on origin (`git ls-tree -r --name-only origin/review-site data`) and check out
only the files missing locally. Files that already exist locally (site.json, status.json, control.json, control/
built by this PC) are not touched.

- site-10: ecd7fd7a `tools/review_site/lantern_review.py` (pushed on claude/lantern-redesign-pass2)
- review-site: a0466873 `tools/lantern_review.py` (1 deploy, J approved "★ Push now")
- `LanternLive\RENDER.ps1`: edited in place (not in git)
- Dry run: old code staged `D` for decisions/jar/history; new code staged none, and the local status.json stayed.

## Open work
None. The render that was running during the push (PID 6596, 2026-10-18 night) had the old code loaded, so one more
deletion from that run was possible. If decisions.json or jar.json went missing online after it, restore them from
the commit before.

## Files
Nothing stray. Scratch worktrees and temp branches (dry-*, fix-push, a `review-site` branch the dry run made in
site-10) were removed.

## Lessons for the design skill
None (no design work).

## Gotchas
- The renderer has two paths: `tools/review_site/lantern_review.py` on claude/lantern-redesign-pass2 and
  `tools/lantern_review.py` on review-site. Before copying one over the other, diff them (they were identical).
- `sync_with_site()` runs `checkout -B review-site`. In a git worktree that creates or moves the shared `review-site`
  branch of that repo. To dry-run it, give the worktree its own branch and delete any `review-site` branch it makes.
- `git fetch origin review-site` in site-10 only sets FETCH_HEAD. To get a ref to diff against, use
  `git fetch origin review-site:refs/remotes/origin/review-site`.
- Running a .ps1 directly is blocked by execution policy. Use `powershell -ExecutionPolicy Bypass -File ...`, as
  RENDER.cmd does.
- `git pull --rebase` won't run in site-10 while other chats leave uncommitted files there, and stashing is not
  allowed. Instead, fetch and check `git rev-list --left-right --count HEAD...origin/<branch>`. If it's not behind,
  no rebase is needed.
- When a render runs (RENDERING lock with a live PID), push site tools from a scratch worktree of site-10 instead of
  `LanternLive\review-site`. The renderer retries its own push after a re-sync if the site moved on.
