# Hand-off: Dread Warren spiders, Hunter and Weaver (pass v2.0107)

J's picks (review site, 2026-10-19): pass v2.0107 W2b1, W2b2, W2b3 (Hunter) and W2c1, W2c2, W2c3 (Weaver), all KEEP.
J asked for "Hand off + improve all" in chat. Broodlings, Dread Phantom and the Matron are still being improved
(next: pass v2.0108), so build only these two spiders for now.

## What to build

Two fear-construct spider mobs for the Dread Warren trial (`docs/plans/trials/2026-10-19-trials-concept.md`), each with
three looks J kept. Pick one as the default and offer the other two as Ring Lab options, the way construct looks work:

| Take | Spider | Look |
|---|---|---|
| W2b1 | Hunter (1.6x vanilla, about 2.6 blocks across the legs) | Plate: a black core under yellow hard-light scale bands with dark gaps, small glowing knees and ankles, eight glowing eyes |
| W2b2 | Hunter | Shard: faceted see-through yellow fear glass round a dark core, shard spines on the back, spiked knees |
| W2b3 | Hunter | Bristle: a dark furred body bristling with yellow spines, banded legs, a glowing eye mark on the abdomen |
| W2c1 | Weaver (1.3x, long thin legs, about 3.7 blocks across) | Plate |
| W2c2 | Weaver | Shard |
| W2c3 | Weaver | Bristle |

- Voxel pixel art at 1/16 block (one model pixel = one voxel). Export to Blockbench with greedy boxes and box UV, as in
  `tools/pixel_rage_battery_bbmodel.py`; keep each model near 2,500 boxes.
- Glow parts (eyes, joints, eye mark) are their own cubes, inflated 0.02 px against z-fighting; yellow glow stays
  saturated, never white.
- Fear glass (the shard look) uses dithered/cutout transparency, never blended (it goes see-through from some angles; 608).

## Poses J saw (every take shows all five, turning)

walking (feet lifting in turn), clinging to a wall, dropped on a hard-light thread, rearing to strike (front legs up,
fangs out), dead on its back (legs curled). **Ceiling walking is ON HOLD** until J watches the Stormie's Spiders test
world (DECISIONS 2026-10-19): walls and drops only, no upside-down ceiling movement.

## Sources

- Script (builds everything from nothing): `docs/blender/blender_updates/v2.0107_dread_warren_r2.update.py`, function
  `spider2(name, kind, style, pose, seed)`; kind `hunter` / `weaver`, style `plate` / `shard` / `bristle`.
- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r2.blend` (or the smaller
  `dread_warren_r2_spiders.blend`), cameras "Cam W2b1 Hunter: plate" ... "Cam W2c3 Weaver: bristle", frames 1-120.
- Review: https://lantern-review-j.vercel.app/#report/v2.0107

## Still open (not for this hand-off)

Broodlings, Dread Phantom, the Matron, Lights out and the caves: pass v2.0108 (improve round).
