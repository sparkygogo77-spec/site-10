**FOLDED 2026-10-19** (lesson -> design skill 'Pages, cards and replies'; gotchas and 3D catalogue workflow -> coordinator 'Review site tools/gotchas')

# Retired 2026-10-19: catalogue chat (3D models of jar models for the review site)

## Range / role
Side session started from the Control-page chat: make the review site's model catalogue (`catalogue.html`) show jar models
in 3D. No Blender pass numbers used. Pushed: review-site `3ab42ecd`, site-10 `f3b163a`.

## Open work
- Only `dark_lantern` has a `.glb`. J chose NOT to convert everything: models get a `.glb` one by one, when he taps
  "Make 3D for this" (jar tile sheet in the Control tab). That copies `Menu: make 3D J:<name>`; the PC chat runs
  `jar_to_glb.py --only <name> ...` (row in `PC-CHAT-BRIEF.md` section 2), checks `catalogue.html#<name>` at phone and
  desktop widths, asks J, pushes once per batch.
- Site saves now go through the `site-data` branch, so the "Make 3D" request could be saved from the site without a
  deploy instead of copy/paste (not built; the button only copies text today).
- Not pushed from here, still local only: nothing (worktree `scratchpad/cat`, branch `catalogue-all`, can be deleted).
- Per-model caveats found by a full trial run (all 80 loaded and spun on phone and desktop, 8.5 MB total, biggest
  `red_battery` 0.69 MB, no size limit in `tools/review_site/README.md`): `nebula_light_l1` has no texture in the jar (shown
  plain white); `diving_hawk` applies its outliner group rotations, so it differs from the flat Control picture (which
  ignores groups).

## Files
- Converter source of truth: `site-10/tools/review_site/catalogue/jar_to_glb.py` (copy to `review-site/tools/catalogue/`).
- Nothing stray on J's PC. Scratch worktree `...\scratchpad\cat` of review-site may be removed (`git worktree remove`).

## Lessons for the design skill
- J, on 3D catalogue files: "let me choose which one to start gib files seperately from the take variations because some
  arent worth buildign the file for yet" (catalogue chat, 2026-10-19). Rule: never bulk-generate per-model assets; give J a
  click to choose which ones are worth building, and keep that separate from build-take variations.

## Gotchas
- `review-site` is a render clone: RENDER.ps1 resets it from origin. Work in a separate `git worktree` of it, then rebase
  on `origin/review-site` before the one push (renders push often; the base was stale within an hour).
- Port 8765 is often already taken by another session's local server serving an old copy: check `netstat -ano | grep :PORT`
  and use another port, or the browser silently shows the old page.
- bbmodel quirks the converter handles: elements with only `uv_offset` (box UV, no `faces`); outliner group rotations
  (nested, innermost first, Euler order Z·Y·X); hidden groups; textures at `textures/entity/bb/<name>.png`, numbered-only
  textures (`dark_lantern_swirl_0`), and a placeholder texture with no image (`nebula_light_l1`).
- Python here needs `pip install numpy pillow` before the converter runs. In bash heredocs backslashes get mangled: write
  edit scripts to a file instead.
- `data/control.json` carries a `catalogue` flag per jar tile, rebuilt by `gen_control.py` on each render run; when adding
  a model between runs set the flag by hand (don't run gen_control from a worktree: it scans the parent folder for .blend files).
