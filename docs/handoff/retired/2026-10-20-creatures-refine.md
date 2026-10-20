FOLDED 2026-10-20 by coordinator 4 (lessons -> lantern-ring-design; gotchas -> lantern-blender-modeller)

# Retired: the creatures refine chat (grizzly / Lantern enderman / shark), 2026-10-20

## Range / role

PC Blender modeller chat started by Lantern coordinator 4 for J's "I want grizzly refined, shark and the other i named
as well" (the round 4 Titan creatures; the Titan trial is shelved, so they are standalone mobs). Area Trials.
Passes used: **v2.0112** (rated) and **v2.0116** (last pass, rendering on J's PC when this chat retired).

## Open work

- **v2.0116 WAITING** (25 animated takes, frames 1-60 at 20 ticks a second): `LanternLive\trials\creatures_r2.blend`
  (the renderer builds it from the script), cameras `Cam <code>`. PB1-PB6 polar bear (idle, walk, sloth swipe, rear up,
  hurt, death); YE1-YE9 Yellow Lantern enderman (idle, teleports static / lantern / fold, lantern slam, lava throw,
  water cast, hurt, death); OE1-OE3 Orange Lantern enderman prayers; SK1 great whites 22/14/10/6, SK2 mako /
  hammerhead / tiger / thresher, SK3-SK7 10-block great white (cruise, fast, bite, hurt, death). All checks pass.
  The render was started by this chat at 23:08 (`lantern_review.py -- v2.0116`); if it didn't finish, rerun it.
  Still to do for J: `python tools/pc/take_grid.py grid v2.0116 --stars <stars>` and the rating questions. My ★
  picks: KEEP everything except IMPROVE PB4 (rise a bit slower/heavier), YE4 (the fold line is thin from far away),
  OE3 (the standing curl reads less like a prayer).
- **v2.0112** rated: IMPROVE G2a-c, E2a-c with J's notes (they became v2.0116); S2a-c not rated (J: the shark is
  "already great", so it was kept and scaled in v2.0116).
- Picture page for v2.0112: https://claude.ai/artifact/XGpo7dmcEvjnt9yZK6UN2N. No page yet for v2.0116.
- Not promised but open: none of these mobs is in the game; no hand-off brief written (J hasn't picked).

## Files

- `LanternLive\trials\grizzly_enderman_shark.blend` (v2.0112) is superseded by `creatures_r2.blend` once J rates
  v2.0116; keep until then. `trials\titan_killer2.blend` and its renders are the round 4 originals (keep for reference).
- `LanternLive\_previews\takegrid\v2.0112_{grizzly,enderman,shark}.jpg`: labelled strips sent in chat (can go).

## Lessons for the design skill

- **Creatures are mob-sized and animated, not set pieces**: "the bear is honestly too big ... proper animations on a
  much smaller mob than these models, for the shark as well and the other" (v2.0112). Bear 5 tall, enderman ~7 tall,
  sharks 22 down to 6 blocks.
- **Polar bear look**: "5 tall, should be skinner than the polar bear and have more textured, detailed color picker
  fur", "longer arms almost like a sloth with its claws" (v2.0112). Fur reads best as a few hand-picked colours placed by
  patches and height, plus guard-hair fringe, not per-voxel noise.
- **Lantern enderman**: no wings, crown or facial expressions (the stacked pauldron plates read as wings); it carries
  its lantern and uses it for moves; acquired constructs float near it ("lava blocks, water casting"), "faithful to
  minecraft frame time" (v2.0112).
- **Teleports get an animation with variations** (v2.0112 E2b): "the teleport should have an animation, give me more
  variations".
- **The Orange Lantern charge is a vulnerability pause**: "hugging the lantern extremely close and almost like
  whispering to themselves in a prayer looking down and closing their eyes" (v2.0112 E2c).
- **When J says a model is great, keep it and vary it**: "The one we have is already great, make smaller variations ...
  create different types of shark as well" (v2.0112 S2).
- **J needs the pictures in the chat to rate**: "I dont see where this is" when the stills were only on a page/side
  file; send labelled stills (SendUserFile, display render) right before the rating questions.

## Gotchas

- **Two-bone IK with a body that rolls**: solve in the limb parent's frame and swing the limb out about y so its plane
  passes through the target (`atan2(-dx, -dz)`), or planted feet drift ~0.13 blocks when the body leans.
- **Raising a limb with Euler blends crosses the face**: blend the limb *direction* (normalised lerp) and convert back
  (`aim_limb`), and apply abduction with the right sign for the current pitch.
- **Hugging arms drive elbows into thighs** with planar IK: roll the arm about the shoulder-to-hand line (hand stays put)
  to point the elbow out (`Rig.elbows_out`).
- **Capsule checks vs tapered limbs**: a capsule at the max radius reports false floor clips; split tapered limbs into
  two segments. Contact points on a horizontal shin/knee need a world-down offset, not a local one.
- **Scaled-to-nothing frames** (teleports, poofs) make every limb "collide": leave them out of the check frames.
- **Minecraft hurt flash in Blender**: an Attribute node (OBJECT, "hurt") mixing base colour to red, keyed on each
  part's custom property; works in EEVEE.
- **Cameras see neighbouring takes** across a 90-block gap: set `clip_end` to ~2.5x the camera distance.
- **A shot toward the camera reads as vertical**: throw/jet targets go across the view, not along it.
- **PowerShell 5.1**: `git commit -m @'...'@` with quotes splits into pathspecs; use `-F <file>`. `python - @"..."@`
  waits on stdin forever; write the script to a file. `Set-Content -Encoding utf8` adds a BOM: read with `utf-8-sig`.
- **`IndexOf("import math")` when slicing a script** can miss the line; check the header of a generated script.
- **BLENDER.lock is also taken by trial scripts** (spider_anim_tests.py), not only lantern_review: wait on it.
