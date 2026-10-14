# Pass 593: the skin workshop — WAITING

**Script:** `docs/blender/blender_updates/593_skin_workshop.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\constructs\skin_workshop.blend` (27.8 MB, textures packed).
Start on Cam W1 and press play. Everything forms over frames 1–34, then the textures play to frame 400.
**Sheet:** `sheet.png`, the check render at frame 100: the W1 stand, the T5 stand, particle walls, rings, lanterns.
Rings and lanterns were re-framed after this render.

J: "a skin workshop of all of our current textures and necessary skin textures and construct / particle skin renders".
J's picks: one Blender file with a shelf per group; green picks, barrier surfaces + particle walls, ring and lantern looks;
each texture on the suit, as a block wall, as a dome and as particles.

## Shelves (left to right)

| Shelf | Contents |
|---|---|
| Green picks (16) | W1 neon, W1 emerald, H1 neon, H2 neon, HW emerald, BR1 emerald/jade/lime/neon, BRD neon, X1, X3, X5 emerald, X5 neon, X3D1, R2 K1 (default, static) |
| Barrier surfaces (7) | T1, T2, T3, T5, T6, T7, T9 |
| Particle walls | W1 curtain, W2 lattice, W3 swarm, W4 rising, W5 shards (pass 700 code, unchanged) |
| Rings (2× size) | square emblem ring (default), A, B, B1–B4, C, L1–L3 |
| Lanterns | Dark Lantern L1, L2, Dark Lantern 5 L1, L2, Blue Lantern |

Each texture stand has four pieces, all in that one texture, animated as the game strip:
- the A1 Plates suit (J's pick from 590/591);
- a 3×2 block wall, outer shell only, one tile per block face;
- a dome/shield of radius 1.5;
- a particle construct: about 420 pixels living on a sphere, each showing its own patch of the texture, over a faint
  shell of the same texture.

## Cameras

- `Cam <code>`: a whole stand, e.g. `Cam BRJ`, `Cam T5`.
- `Cam <code> suit`, `Cam <code> wall`, `Cam <code> dome`, `Cam <code> particles`: one piece of a stand.
- `Cam shelf Green picks`, `Cam shelf Barrier surfaces`.
- `Cam walls`, `Cam wall W1`..`W5`, `Cam rings`, `Cam lanterns`, `Cam workshop`.
