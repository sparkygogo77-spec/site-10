# Pass 802: first-person construct tool animations — WAITING

**Script:** `docs/blender/blender_updates/802_fp_tools.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\fp_tools.blend` (Cam S1, press play)
**Files here:** `sheet.png` (S2 in first person at ticks 8, 16, 24: forming, formed, wind-up), `fp_tools_poses.json`

J: "i need the tool animations 1st person reworked and i need them to fill up my item bar instead of forcing me to use
them". He picked every tool (sword, pickaxe, axe, shovel, hoe, hammer), 3+ sword takes, and forming pixel by pixel.
On the hand: "the ring should stay on when wearing it, make a ring slot in the inventory for your right hand". The
ring slot and the hotbar behaviour are game code and went to the mc chat. Here, the ring stays on the right hand in
every take.

Every take starts with the tool **forming**: construct pixels stream out of the ring and the tool's boxes lock in from
grip to tip (ticks 0–14). Then the swing plays twice. The tools are the jar's construct tool models, in see-through
glass with their glowing parts lit.

| Take | Swing | Ticks | Hit tick |
|---|---|---|---|
| S1 | sword fast slash: high right to low left, snaps back | 8 | 4 |
| S2 | sword heavy chop: raised high, wind-up, big downward chop with follow-through | 16 | 11 |
| S3 | sword sweep pair: flat sweep right to left, then a backhand return | 14 | 6 |
| S4 | sword thrust: pulled back, straight stab, drawn back | 9 | 5 |
| P1 | pickaxe: overhead strike into the block, small bounce | 10 | 7 |
| A1 | axe: slanted chop from the right with a recoil | 12 | 8 |
| V1 | shovel: forward-down scoop, lift and flick | 11 | 6 |
| O1 | hoe: reach out, hook down, drag back | 11 | 6 |
| H1 | hammer overhead (J's default) | 18 | 13 |
| H2 | hammer from the side into a wall (J) | 13 | 8 |

The JSON holds per-tick arm pitch, yaw and roll (pitch 90 = straight ahead) and the tool's tilt in the fist, plus the
hit ticks, for the game's first-person renderer.

Cameras: `Cam <take>` is the eye in first person, `Cam <take> side` reads the arc from the right, plus `Cam all`.
