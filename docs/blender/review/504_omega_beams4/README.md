# Pass 504: omega beams round 4 (Chat C) — WAITING

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_beams4.blend`, Cam O1a, frames 1–120.
**Script:** `docs/blender/blender_updates/504_omega_beams4.update.py`. **Files:** `sheet.png`, `omega_beams4_poses.json`.
Takes are scenario × bend style: O1 ground, O2 hover brake, O3 barrage; a zigzag, b snake, c hooks.

| J on 223 | Round 4 |
|---|---|
| "never be straight lines they should always have the past 3/4 turns in the lines animated at all times until it reaches the target ... two are supposed to run in parallel" | Every use is **one pair**, one laser from each eye, 0.22 blocks apart on the same path. The tail is 4.5 blocks and always shows 3–4 bends (wavelength 1.45 blocks); the bends travel along the line at 0.55 rad a tick, so it writhes until it hits. The bends fade out at the eyes and in the last block before a target, so the line leaves clean and strikes dead on; the pair opens out to hit two neighbouring blocks. Styles: **a** zigzag (triangle wave, amplitude 0.32, the zig plane slowly turning), **b** snake (S bends with a slow corkscrew), **c** hooks (curls that loop back on themselves). |
| "the hover brake looks good" | O2 KEEP. |
| "there should be some movement slowly allowed on the ground" | O1: you walk at 0.04 blocks a tick (0.8 b/s) while firing; the beams stay locked to the eyes as you move. |
| "the lasers should also instant incinerate a little faster" | Embers the tick it's hit, gone in 10 ticks (0.5 s; 223 took ~0.9 s), ash from tick 4. |
| Barrage: "look into a calm position and once the lasers leave the eyes of the character movement should be regranted ... a slight charge up is good ... the same 2 lasers destroy and find a path to all selected or immediate targets/mobs instead of shooting new ones" | O3: calm stance, head level, no turning. Charge 0.6 s (eyes build, 10 red sparks gather). One pair leaves at tick 18 and threads all 6 targets in turn, burning each. Once its tail is clear of the eyes (tick 24) you walk off at normal pace while it keeps going. |

Head speed 0.9 blocks a tick; each pair carries one red light.
