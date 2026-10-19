# Retired: review site Control tab and Jar view (side chat of the PC chat), 2026-10-19

## Range / role
Review-site pages only, no pass range (last pass touched: 807, re-rendered, not rebuilt). Built and shipped:
- **Control tab** (`#control`): Now (live render, last upload, desktop-only `lanternrender://go`), Waiting on you
  (★ = unrated takes + 5 x later passes naming it), Pick what's next (jar models / .blend files / textures -> sheet with
  takes 1/3/5, colour, note -> copies `Menu: build next <id>, N takes: <note>`), Chats (start-up / close-out / thread
  prompts). Data: `data/control.json` + `data/control/*.png` from `tools/review_site/gen_control.py` (jar models drawn
  from their bbmodel cubes in pure Python, cached by blob id).
- **Jar view** (`#jar`, the "In the game" button): jar + Download + Lunar install, recent first-parent merges on main
  as cards with their `whats_new.json` steps and pass links, "New to you" since `seenBefore`. Data: `data/jar.json`
  from `tools/review_site/gen_jar.py`, run by gen_control.py on every render (rides `live/`, no deploy).
- `tools/pc/menu.html` links to the Control tab. Pass 807 rendered onto the site.

## Open work
- None WAITING or PARKED. Promise kept: one push per change, J asked each time.
- `J:lantern_port` has no Control picture (its model draws empty); low priority.
- Jar view "New to you" is seeded at 2.1.681 (run 681, built 2026-10-12 12:41 UTC); it moves on by itself when the
  version in Lunar profile 26 changes.

## Files
- `C:\Users\Josh\Downloads\charge_final.blend` is a duplicate of `lanterns\charge_final.blend` (copied in for pass
  807): the Downloads copy can go to `_to_delete\`.

## Lessons for the design skill
- Pages for J are pictures to tap, not text to read: "buttons dont lead anywhere just from looking at it i can tell
  ima have to read everything" (Control tab brief, 2026-10-18). Every action is a picture or one big button; anything
  the chat must do is copied as a ready prompt with "Copied: paste into your PC chat (Ctrl+V, Enter)".
- Don't build heavy files for everything up front; let J pick: "let me choose which one to start gib files seperately
  from the take variations because some arent worth buildign the file for yet" (catalogue .glb, 2026-10-18).
- Show what changed in his game, newest first, with how to see it: "i need a better version on the site aswell for the
  jar showcase of recent updates" (Jar view, 2026-10-18).

## Gotchas
- **Never edit `LanternLive\review-site` in place**: RENDER.ps1 checks out origin over everything but media/ and data/,
  and lantern_review.py runs `git add -A` and pushes. Work in a `git worktree` of it (scratchpad), push
  `<branch>:review-site`.
- **site-10's checkout has other chats' uncommitted edits**: never pull/stash there; commit from a worktree of
  `origin/claude/lantern-redesign-pass2`. review-site `tools/` copies lag site-10's `tools/review_site/` (READMEs
  differed): diff before copying and check the commit only adds lines.
- **INBOX has two status formats**: `[status: WAITING]` and older `[WAITING]` / `[PICKED: ...]`; parse both.
- **whats_new.json** has one entry per line (`\t\t{"id": ...`): match added ids with `^\+[\s{]*"id":`.
- **The site URL 307-redirects** to the branch alias: use `curl -L` when checking a deploy, or a poll never succeeds.
- **No Pillow, ffmpeg, node or gh on the PC**: PNG read/write in pure Python (zlib); GitHub's public API via curl
  (works while site-10 is public). Windows Python can't open `/c/...` paths: cd and use relative paths.
- **Built-in browser**: navigating to the same URL with only a new #hash doesn't reload; add `?v=N`. Clipboard can be
  refused there; the page falls back to `execCommand("copy")`, then a selected box.
- **Long JS in a Bash heredoc** failed ("unexpected EOF"): write the code with the Write tool and patch with a small
  Python script that asserts each anchor occurs once.
- **A stray .blend in Downloads** is invisible to the site and the renderer (charge_final.blend for 807): when J says a
  version is missing, search Downloads and `_to_delete` too.
