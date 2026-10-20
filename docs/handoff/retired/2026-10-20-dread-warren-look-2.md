# Retired: Dread Warren look, modeller chat 2 (PC, Trials), 2026-10-19/20

Started by coordinator 3 for "IMPROVEs + caves"; reported to coordinator 4 (local_ff09b134-9e28-43ae-9598-ac2bcc88d743).
Passes: **v2.0109, v2.0111, v2.0113, v2.0114, v2.0115** (v2.0110 and v2.0112 belong to other chats). Next free number:
check `docs/blender/review/specs/` (v2.0116+). J: "prepare to retire soon" (2026-10-20).

## Open work

- **v2.0115** (5 takes: textured mine and ravine, modern shaft, dungeon, dripstone cave): pushed (65cee9f0); render
  queued behind the Blender lock if not done. `trials\dread_warren_r8.blend`, stills frame 30.
- **v2.0114** (11 takes): J KEEP W1a7a, W1a7b, W1a7c in chat ("all three are good") - save them to the site with
  `python tools/pc/take_grid.py rate v2.0114 W1a7a=KEEP W1a7b=KEEP W1a7c=KEEP` once the pass is rendered. Steps 1-4
  (W1a5a1 ... W1a5a4c) were shown in chat and steered; they need no rating.
- **The entrance design is decided** (DECISIONS 2026-10-20): an ordinary mineshaft (in caves, sometimes cut open on a
  ravine wall) with our section on one dead end; any mineshaft within the Warren structure's radius (~200 blocks; the
  lair cave is ~230 x 160) has a chance to carry it. Worth a hand-off to the game chat once J says so: a brief in
  `docs/handoff/` (worldgen: attach a piece to vanilla mineshaft dead ends near a Warren; blocks: old dark timber,
  dread stone lining; the modern shaft would need new blocks).
- **Unrated, leave alone until J rates:** v2.0109 W1b3 W1c1-c3 W2a3c1-c3 W2d2a1; v2.0111 W3c1a1c W3c1a2a W3c1a2b and
  all W3c3 (12); v2.0113 everything except W1a5a.
- **v2.0111 KEEP W1b6** ("Great idea", ledge over the pit), **W3c1b3b**; **v2.0109 KEEP W2d2b1, W3c1c1, W3c1c2,
  W3c3c1** - not handed off yet.
- Ceiling walking still on hold (Stormie's Spiders test).

## Files (LanternLive\trials\)

dread_warren_r4.blend (v2.0109, 38 MB; split copies dread_warren_r4_caves/_creatures/_lights_out_scream/
_shell_and_funnel.blend were made only for SendUserFile), dread_warren_r5.blend (v2.0111), dread_warren_r6.blend
(v2.0113), dread_warren_r7.blend (v2.0114), dread_warren_r8.blend (v2.0115). Take-grid pages:
`_previews\takegrid\v2.01NN.page.html`. Chat-only stills from v2.0114's steps are in this session's scratchpad (gone).

## Lessons for the design skill

- Entrances are ordinary world features, as common as their landform and placed at random, never a tell-tale sign:
  J: "try to make it look natural, it should be calculated to be as common as a certain rivine is mountain is, it
  should be random though" (v2.0113 W1a5a).
- Reuse what the game already generates and attach our part to it: J: "natural mineshafts that have the additional
  portion of ours attached to it" and "perfect utilization of existing generations" (v2.0114 W1a7a-c, all KEEP).
- Show the place itself, not calm/danger pairs: "the DANGER below variations are worthless I dont know why this
  became a thing" (v2.0114). Webs-only-in-danger stays a game rule, not a picture format.
- Every pick question gets a "New iterations" option: "give me a new iterations button" (v2.0114).
- "One at a time" iterations work: build one, still above an AskUserQuestion, steer the next from his answer (v2.0114:
  five steps to a design he called "all three are good").
- Webs never across the walkway: "THE WEBBING ON THE INSIDE SHOULDNTBE HERE" (v2.0111 W1b4).
- The boss's own eyes must be the brightest thing in the dark: "Cant see boss spiders eyes as well" (v2.0111 W3c1b1a).
- Less yellow: "too much yellow", "pure yellow i cant see the detail" (v2.0109 W2d2b1, W2d2a3): quiet stone, cool rim
  light on black-core constructs.
- Big caves / doll's-house cutaways and islands were all dropped ("these were all scrappable", v2.0109); eye-height
  views of real-looking places were kept.

## Gotchas

- **A SUN light lights every take in the file** (no cutoff): use big AREA lights with a cutoff per take (v2.0111).
- **Area light rotation:** `rot=(radians(-40), 0, ...)` points it away from the scene (-y); +X rotation points it +y,
  onto what the camera looks at (v2.0114).
- **Shadowing a helper:** a local variable named `ground` hid the `ground()` function ("'numpy.ndarray' object is not
  callable"); name height maps `gnd` (v2.0111).
- **Eye-height cameras into pits/cracks:** the line of sight hits the near ground; stand at the rim (2-3 blocks) and
  aim at the far wall, not the bottom (v2.0114 sinkhole).
- **1-block timber frames in a 3x3 corridor read as doorways**; carve corridors 5 wide, 4 tall (v2.0114).
- **mine_seg skips cells within 2 of the grid edge**: start corridors at y >= 2 or the camera ends up in solid rock.
- **web_fade alpha 0.03 still shows up close**; use 0.0 while calm (v2.0114).
- **Git Bash heredocs** halve backslashes and choke on some quoting in long Python: write the patch to a file with the
  Write tool and run it (v2.0113).
- **The site's renders are darker than quick test renders** (different samples/settings): light calm scenes brighter
  than looks right in a test.
- **BLENDER.lock can be held by another chat's non-review Blender job** (spider_anim_tests.py): wait, don't break it.
