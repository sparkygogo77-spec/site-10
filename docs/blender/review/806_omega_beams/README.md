# Pass 806: glowing omega beams — WAITING

**Script:** `docs/blender/blender_updates/806_omega_beams.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\omega_beams.blend` (Cam B1 side, press play; 70 frames)
**Files here:** `sheet.png` (check render, Cam all, frame 30. The impact light was cut from 600 to 150 W after it, so
the wall spot stays green instead of washing out.)

J: "the omega beams are very particle-y and hard to see". These beams are solid geometry with a bright core you can
always read. The arm is straight out, and the beam leaves the ring.

| Take | Look |
|---|---|
| B1 core + sheath | core (radius 0.045 blocks, emission 4) inside a hard-light sheath (radius 0.12, 45% opaque) with two rim lines |
| B2 pulsing rings | the same core and sheath, with rings of light running down it, one every 3 ticks, each crossing in 6 ticks |
| B3 twin braid + sparks | two cores twisting round each other (radius 0.07, one turn per 1.5 blocks), a sheath, construct sparks thrown off the wall every 2 ticks |

Timing for all three, at 20 ticks a second: fire at tick 10, reach the wall 16 blocks away by tick 14 (4 blocks a
tick), hold until tick 54 with a small thickness flicker (±12%), pull back into the ring by tick 58. The ring goes
5 → 10 while firing. The impact is a lit disc plus a point light on the wall.

**For the game:** draw it as geometry (a beam renderer with a core quad and a sheath quad) rather than particles. Keep
particles only for B3's sparks.

## J's verdict (2026-10-15)

KEEP, word for word: "B1 wins this one". More B1 designs in pass 819.
