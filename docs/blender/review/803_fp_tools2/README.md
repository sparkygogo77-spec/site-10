# Pass 803: first-person construct tool animations, round 2 — WAITING

**Script:** `docs/blender/blender_updates/803_fp_tools2.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\fp_tools2.blend` (Cam C1, press play)
**Files here:** `sheet.png` (check render: S2, S4, A1, H1, P1, V1 around their hits; the shovel was changed after it),
`fp_tools2_poses.json`

J on 802: the axe hits at an angle that doesn't match the blade; the hammer is flat, the wrong way round and not the
construct hammer; the pickaxe is used wrongly; the slash is almost fine but needs a combo / mix-up; S2 should be
diagonal and cut with the edge, not the flat; S3 is closer; the thrust must draw back, then go forward, not press down;
the shovel is poor.

**The working edge leads.** Each tick the tool turns about its own length so its edge (sword), point (pickaxe), blade
(axe, hoe) or striking face (hammer) faces the way it is actually moving. That turn is worked out from the tool tip's
motion and saved per tick as `tool_twist`. The thrust holds the edge upright, and the shovel holds its blade flat.

**Construct hammer.** A solid block head with depth, striking faces on both ends, glowing rims and a glowing core
(like Hammer mode, pass 503), on a banded haft.

**Reach.** The shoulder can now pull back and drive forward (`reach`, in metres), for the thrust, shovel and hoe.

| Take | Swing | Hits (tick) |
|---|---|---|
| S1 | sword slash (kept), edge true | 4 |
| S2 | sword diagonal chop, upper right to lower left | 11 |
| S3 | sword sweep pair (kept, J: "closer to good"), edge true | 5, 10 |
| S4 | sword thrust: drawn back 0.24 m, then a straight stab 0.34 m forward, edge upright | 8 |
| C1 | sword combo: slash, backhand, diagonal chop | 4, 9, 15 |
| C2 | sword combo: sweep, then draw back and thrust | 5, 13 |
| P1 | pickaxe: raised, point-first strike, bounce | 9 |
| A1 | axe: controlled diagonal chop, blade leading, short recoil | 9 |
| V1 | shovel: blade flat, driven in ahead, levered back, lifted and flicked | 6 |
| O1 | hoe: raised, blade hooked into the ground ahead, dragged back | 6 |
| H1 | construct hammer overhead, face-first | 13 |
| H2 | construct hammer from the side into a wall | 8 |

Every take forms pixel by pixel from the ring first (ticks 0–14), and the ring stays on the right hand.
