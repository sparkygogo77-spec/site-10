# Pass 405: double-tap landing, tighter and faster (Blender designer chat, 2026-10-14)

J, testing in game:

> "when im moving forward i cant descend like when im standing still to stop flying and land, it should also be toned
> down so i land much closer than a few blocks from where i started it from, should be faster too"

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\movement\land_tight.blend`. Start on **Cam L5 close**, frames
  14–32. The double tap is at tick 16.
- Script: `docs/blender/blender_updates/405_land_tight.update.py`
- Poses: `land_tight_poses.json`

Every take flies forward at 0.8 blocks a tick (16 b/s), 5 blocks up, then double taps.

| Take | Brake | Descent | Carry after the tap | Touchdown after the tap |
|---|---|---|---|---|
| L2 (403, reference) | none | 8 ticks + 3 + run-out | **8.1 blocks** | 0.60 s, still running |
| L4 | 2 ticks | 5 ticks, eased | **0.8 blocks** | 0.30 s |
| L5 | 1 tick | 4 ticks, eased | **0.4 blocks** | 0.25 s |
| L6 | instant | 3 ticks, falling (z = 5 × (1 − w²)), deeper knee absorb (×1.35) | **0 blocks** | 0.20 s |

- **No run-out.** Touchdown goes into an absorb crouch (2 ticks), then stand (7 ticks), with a construct cushion ring
  at the feet.
- **Game rule (the bug J hit):** descend (sneak) and the double tap must work in flight whether or not you are moving
  forward. Neither input may be ignored while moving.

Open: L4, L5 or L6? The bundle ships **L5** as the default, with L4 and L6 as Ring Lab options; L2 is dropped.
