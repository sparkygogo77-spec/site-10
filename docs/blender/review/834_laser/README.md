# Pass 834: a new laser — WAITING

**Script:** `docs/blender/blender_updates/834_laser.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\laser.blend` (Cam L1 close (also "Cam <take> eye", first person); press play)

J: "we absolutely need a better laser than the one that shoots right now".

**Today's Beam** (HelixBeams): two translucent tubes twisting round the line, up 3 ticks, held 2, gone in 3. It reads as
a soft green smear (L0 rebuilds it for comparison).

**New takes**, all drawn the way the game can do cheaply: a thin solid core, ONE glow quad turned to the camera (here 3
crossed quads so every Blender camera sees it) with a pattern scrolling to the target, a wider faint haze, and a soft
flare at the ring and at the hit. It reaches the wall in 2 ticks, holds to 40 (a held shot; a tap is its first 8 ticks),
thins out 40-44. The arm kicks 4 degrees on firing. The ring sits on the punching face (jar placement).

| Take | What |
|---|---|
| L0 the game now | for comparison |
| L1 hard-light lance | core + streak glow (noise drawn out along the beam, flowing 0.6 blocks a tick) + haze + flares |
| L2 construct lance | core + your hex construct texture flowing on the glow + haze + flares |
| L3 pulse lance | core + bright bands racing to the target + O4's two spinning rim lines + sparks at the hit (O3) |
| L4 charged | L1 wider and hotter, three shock rings sliding down the beam on firing, sparks, a scorch on the wall |

After the check render the core and glow were turned down (they read white) and the eye cameras moved in front of the
face.

**For J:** KEEP / IMPROVE / DROP per take; the pick goes to the mc chat for HelixBeams.

## J's verdict (2026-10-15)

"L1 -3 need more variations, l0 can be improved laser" - pass 836. L4 not rated yet.
