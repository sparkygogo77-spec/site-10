# Pass v2.0110: spider moving attacks

J on the final lair set (round 10): "we will need more extending or movement attacks from the spider to make it not
just stationary". The R2 brute (36-block span) now lands every hit while it keeps moving. Lair rules kept: legs never
through the floor, each other, the body or you; every hit touches you (0 blocks).

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\spider_anims5.blend` (cameras `M1 cam` ... `M4 cam`)
- Clips: `C:\Users\Josh\Documents\LanternLive\trials\renders_anim4\` (stills in `stills\`)
- Build: `blender -b --python site-10\tools\trials\spider_anim_tests.py -- <out.blend> --only M1,M2,M3,M4 [--check] [--stills] [--video] --rdir renders_anim4`
  (`--check` builds and measures in about 30 s without rendering). Update script for the site's renderer:
  `docs/blender/blender_updates/v2.0110_spider_moving_attacks.update.py`.

| Take | Moving how | Hits (frame) | Floor / legs touching / through you |
|---|---|---|---|
| M1 drive-back combo | walking: charges in, then walks you back at 5 blocks/s | L chest 34, R chest 52, L head 70, R chest 90 (throw) | 0 / 0 / 0 |
| M2 circling strikes | turning: circles you crabwise ~27 out, darts in, reverses | L chest 52, R head 79 (head on), R chest 136 (throw) | 0 / 0 / 0 |
| M3 climbing strike | climbing: up a 28-block cliff, stabs over the lip mid-climb, rolls over | R legs 86, L chest 110, R chest 137 (throw) | 0 / 0 / 0 |
| M4 chase-down | you running at 5 blocks/s, R2 at 12 | R legs 78 (you fall), L chest 116 | 0 / 0 / 0 |

How the hits stay real while moving: each hit's frame is picked within 10 frames of its cue so the spike reaches you
at about 78% of the leg (never a straight leg); the striking leg is driven by the round 9 strike driver (now shared,
`strike_driver()`), 0.1 block into you (0.25 poked out of your thin side); every other leg keeps the round 8-10 leg IK.
New check: "through you" (any leg that isn't the striking spike passing through your body).

Not done: wall-to-ceiling or ceiling strikes (C1's ceiling patrol), and leaps (R2 never leaves the ground).
