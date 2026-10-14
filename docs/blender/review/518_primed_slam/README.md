# Pass 518: primed slams, instant craters, rebuild, slide trench (Chat C) — WAITING

J (after testing in game): "if im flying fast and i hold shift and fly into the ground it should be a primed slam and it
should lock me into the landing motion, i need to see the crater happen instantly though, I want the construct to last
for a little longer too after making the crater, AFTER the crater though i should be able to look at it and left click
and rebuild the blocks as the construct dissolves away. the slam should also work that way if im super jumping holding
crouch as im coming down ... the crater still is only constructed in the center when i need it to spread if i slight
off the construct i need that sliding animation for the small crater if i dont lock into place".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\primed_slam.blend`. Cameras `Cam P1`, `Cam P2`, `Cam U1` (over the
shoulder), `... side`, `... top`. Frames 1–150. **Script:** `docs/blender/blender_updates/518_primed_slam.update.py`.

| Take | Prime | Lands | Crater | Construct | Rebuild |
|---|---|---|---|---|---|
| P1 primed flight slam | flying ≥ 1 b/tick + **shift** held → locked into the ring-fist dive at once (tick 18) | tick 30 | 7×7, **every block opens the tick you land** | floor + rim lining for **3 s** | left click at 2 s (tick 70): blocks re-form from where you look, rippling out 1 tick a block (construct → real look in 10 ticks) |
| P2 primed super-jump slam | super jump to 24 blocks, **crouch** held on the way down → locked head-down (tick 40) | tick 56 | 9×9, instant | 3 s | left click held at 2 s: rebuild follows your crosshair sweeping across, 2 ticks a column |
| U1 unprimed landing (no shift) | — | tick 30 | slide 5 blocks on one knee; trench 3 wide × 6 long, each block lights as you reach it, opens 2 ticks later | lining spreads **one block out all round the trench** (not just the centre), holds 2 s | — |

Rules for the game:
- Crater blocks (top layer) are removed the tick after touchdown, all at once; mobs launch the same tick (M3).
- The crater floor and a one-block rim round it become construct (the lining) for 3 s (2 s for the slide), then
  dissolve to pixels; the rim returns to normal blocks, the floor stays.
- While the lining is up, left click on a crater block rebuilds it and the ones around it (ripple from the looked-at
  block, 1 tick per block of distance); held left click rebuilds as the crosshair sweeps. Rebuilt blocks appear as
  construct and fade to their real texture over 10 ticks. Unrebuilt blocks are gone when the lining dissolves.
- Primed slams always lock (0.7 s) — no slide. Unprimed fast landings always slide.
