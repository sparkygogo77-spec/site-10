# Pass 860: ring glow in first person, replacements for the light rays (WAITING)

**Script:** `docs/blender/blender_updates/860_ring_glow.update.py` (rig from 856)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\ring_glow.blend` (starts on Cam G1 - first person, tick 75; press play, 120 frames)
**Cameras:** `Cam <code> - first person` (120 deg horizontal, crosshair) and `Cam <code> - third person` for G1-G6, plus `Cam all`.
**Frames:** 1-60 ring charge rises 0 to 100% (the bar under each board), 60-90 holds at 100%, 90-120 Bridge is used: the ring
arm pushes out and a short Bridge construct forms ahead, tile by tile (91-103).

J on the in-game glow (bug note `docs/handoff/bugs/2026-10-15-green-glow-interference.md`, Bridge 6%, ring charge 100%,
Complementary Unbound patched): "these light rays from blender are not it". That was pale green streaks smeared down the
ring arm and sleeve, big translucent green panes near the camera, and haze. He also said "the glow is bad", and earlier
"W2 light rays and smoke look bad".

Every take here follows the same rules: nothing on or along the arm or sleeve, no translucent sheets, volumes or billboards
near the camera, no light shafts, a small emissive area so a shader pack's bloom stays small, and saturated green that is
never white. The ring sits on the fist's punching face over the middle finger (the jar's placement), as in 856.

| Take | What | Look at |
|---|---|---|
| G1 face glow = charge | Only the ring's face glows, steady. Its brightness is the charge. Nothing else. | 1-60, 75 |
| G2 rim line | A thin solid light line traces round the gold rim as charge rises: a full loop means 100%. Steady; the face stays dim. | 1-60, 75 |
| G3 orbit pixels | Small solid pixels circle slowly within 2 px of the ring face, one more at each 25% charge; they tuck in when Bridge fires. | 75 |
| G4 face meter | The ring face is a 5-step meter, dark to lit from one edge as charge rises. Using Bridge drops one step, which refills by 112. | 1-60, 92 |
| G5 pulse on use | The ring stays dark while charging and holding. Using Bridge gives one quick short pulse (face and rim, 90-96), then it's gone. | 90-96 |
| G6 knuckle light | A tiny green point light over the back of the fist lights the knuckles only (no geometry, reach 6 cm). Steady; brightness = charge. | 75 |

## For J

Pick the one that reads best as "charged" in first person. Each one could also be combined with G5's pulse on use.
