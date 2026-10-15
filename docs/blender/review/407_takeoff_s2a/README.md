# Pass 407: standing take-off, S2a settling at 2.2 blocks

J on the review site (403 S2a, IMPROVE): "Maybe settles at 2.2"; then "Just 2.2" (one take).

| Take | What | Height |
|---|---|---|
| S2a | fast spring (90% of the climb in 2 ticks, critically damped, never overshoots) | settles at **2.2** blocks |
| S1 | snap, 3 ticks (unchanged, for comparison) | 3.2 |
| S2b | fastest spring (unchanged, J's in-game pick) | 3.2 |

Measured from the poses: S2a sits at 2.2 blocks (2.27 with the 0.07 hover bob) at tick 30; S1/S2b at 3.2.
Everything else as 403: second jump 4 ticks into the first, puff ring, 0.5° shake over 4 ticks, hover bob, then free flight.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\movement\takeoff_s2a.blend` (Cam S2a side, frames 1–45)
- Poses: `takeoff_s2a_poses.json` (same format as 403). Check render: `check.png` (S2a top, S1 bottom, tick 34).
