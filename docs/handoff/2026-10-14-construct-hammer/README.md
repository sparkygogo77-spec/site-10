# Construct hammer (R2) — for the game (J picked, 2026-10-14)

J: "i may even prefer it is done ring only and without the hand motions, just the hammer forming from any angle looks
best to destroy whats in front of me" (on 226), then on 503: "the hammer should swing from the side if hitting a wall
but over head most of the time". **Picked: R2a overhead by default, R2b from the side when the target is a wall.**

Blender reference: `C:\Users\Josh\Documents\LanternLive\combat\combat_round4.blend`, Cam R2a and Cam R2b (frames 1–60).
Script: `docs/blender/blender_updates/503_combat_round4.update.py`. Poses: `poses/combat_round4_poses.json` (takes R2a, R2b).

## Rule
- **Default (R2a, overhead):** the hammer swings down in a vertical plane from behind/above you onto the target
  (start angle 115° above the forward line, ends 45° below it).
- **Wall (R2b, from the side):** when the block hit is part of a wall (a vertical face: the hit face is a side face,
  or the block above the target is solid too), the hammer swings in from your side in a near-horizontal plane
  (tilted 45°), start 115° round, ends square on the wall.

## Timing (20 ticks a second, from the key press)
- You only aim the ring (ring arm out, no other hand motion); the free arm stays relaxed.
- Ticks 10–22: the hammer assembles from 36 construct pixels flying in to their places along the haft and head.
- Ticks 26–33: the swing, accelerating (angle ∝ progress²).
- Tick 33: impact on the target 4 blocks ahead. The head sinks 0.45 blocks into the hit over the next 3 ticks.
- Crater 3×3 on the ground (D0 rules: ring d lights at tick d, gone at 4 + 2d after impact); on a wall, the same rule
  on the wall face. A shockwave ring spreads from the impact (0.3 + 0.35 blocks a tick, 16 ticks).
- Mobs at the impact: knocked away at (0, 0.55 forward, 0.5 up) blocks a tick.
- Tick 47 (0.7 s after impact): the hammer breaks into 16 construct pixels.

## Shape
- Haft 2.4 blocks × 0.14, head 0.75 × 0.55 × 0.55 blocks, construct material (see-through, at most 99% opaque).
- Ring glow 10 while it forms and swings, 26 for 3 ticks at the impact, then back to 3.
