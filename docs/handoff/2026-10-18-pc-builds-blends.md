# J's PC now builds the .blend files (2026-10-18)

From the Claude Code chat on J's PC. For the coordinator: fold this into `lantern-blender-modeller` (and the
`lantern-ring-design` Delivering section) with `propose_skills`. J asked for it: "make lantern_review.py build the
.blend from the script on my PC and save it to the area folder, and draft the modeller skill change".

## What changed

`tools/review_site/lantern_review.py` (commit 9f7138b; live on `review-site` as 7e9bf1b8):
- When a pass has no `.blend` at its spec's `blend` path, the renderer runs the update script on J's PC
  (RTX 5070 Ti, Blender 5.2) and saves the built scene there, packed, before switching to review settings.
- When the script on this branch is newer than the `.blend` (by more than 60 s), it rebuilds and saves again; the old
  file moves to `LanternLive\_to_delete\<timestamp>-<name>.blend`. No script, or no git date: J's file is kept.
- Tested on pass 409: built in 0.9 s, 785 objects, 0.6 MB, same size as the hand-delivered file.

So a modeller chat no longer needs to pack and send the `.blend`: the script and spec are enough.

## Proposed skill edits (lantern-blender-modeller)

**Every finish**, replace step 2 (Deliver) with:

> 2. **Deliver = push.** J's PC builds the `.blend` from your script when it renders and saves it to the spec's
>    `blend` path (`<area>/<name>.blend`, areas: lanterns, movement, combat, constructs, red, suit). Don't pack or
>    `device_commit_files` it. Your script must build the whole scene from nothing (no file of yours on J's PC except
>    `kl_assets/` and the texture library) and must not depend on `LL_NO_RENDER` being unset. Send a packed `.blend`
>    only when J asks for it before the render.

**Every finish** step 1, change "one check render" to:

> one cheap check render (a still or two, Cycles 16 samples) to catch a broken scene; the real renders come from J's PC.

**Changing a take J rated IMPROVE**, add:

> Push the edited script: the PC sees it is newer than the `.blend` and rebuilds the file as well as the clip.

**Gotchas**, replace "No link to J's PC" with:

> - **The PC rebuilds from your script.** Anything you set by hand in a `.blend` and not in the script is lost on the
>   next rebuild. Put every change in the script.
> - **J's own edits win.** If J saves the `.blend` after your last script push, the PC keeps his file. To force a rebuild,
>   push a script change.

## Proposed skill edit (lantern-ring-design > Delivering)

Add:

> - **The PC builds the .blend.** Blender chats push scripts and specs; `lantern_review.py` on J's PC builds and saves
>   each pass's `.blend` to its area folder when it renders (rebuilds when the script is newer). A Claude Code chat
>   running on J's PC can build, render on the GPU and save files directly (`LanternLive\site-10` is its working copy).
