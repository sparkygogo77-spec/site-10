# Pass v2.0120: spider ceiling and leap strikes

J kept v2.0110 M1, M3 and M4 (dropped M2) and picked "Ceiling and leap strikes": spiders dropping from the ceiling
and leaping at you. The R2 brute (36-block span); lair rules kept and measured on every frame.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\spider_anims6.blend` (cameras `L1 cam` ... `L4 cam`;
  the v2.0110 KEEPs `M1 cam`, `M3 cam`, `M4 cam` are in the same file)
- Clips: `C:\Users\Josh\Documents\LanternLive\trials\renders_anim5\` (stills in `stills\`)
- Build: `blender -b --python site-10\tools\trials\spider_anim_tests.py -- <out.blend> --only M1,M3,M4,L1,L2,L3,L4 [--check] [--stills] [--video --video-codes L1,L2,L3,L4] --rdir renders_anim5`

| Take | Move | Hits (frame) | Floor or roof / legs touching / through you |
|---|---|---|---|
| L1 thread drop | ceiling walk upside down, dragline drop, rights itself, hangs and strikes, lands | L chest 76, R head 89 (hanging), R chest 114 (throw) | 0 / 0 / 0 |
| L2 leap strike | crouch, 30-block leap about 12 high | R chest 61 (coming down), L head 67, R chest 94 (throw) | 0 / 0 / 0 |
| L3 ceiling pounce | you hover; it kicks off the roof, rolls upright, you both fall | L chest 62, R chest 70 (mid-air), R chest 116 (on the floor) | 0 / 0 / 0 |
| L4 cliff leap | runs off a 28-block cliff at you below | R chest 61 (falling), L head 66, R chest 94 (throw) | 0 / 0 / 0 |

In the air every leg that isn't striking tucks toward the hips, then spreads to a landing pose over the last 6 frames
(`air_foot` in `move_take`); a striking leg that finishes in the air goes back to that pose instead of reaching for
the ground. The leg checks still run on every airborne frame.

Not done: a web-line swing (Tarzan-style) and wall-to-wall leaps.
