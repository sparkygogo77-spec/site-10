# Pass 601: the lantern charge in 6 seconds (Chat D) — WAITING

J: "I need a much shorter charge animation now maybe 6 seconds to match how much animation time we have with the lantern".

**Open:** `C:\Users\Josh\Documents\LanternLive\lanterns\lantern_charge6.blend`, Cam C6a / C6b / C6c (side), frames 1–120.
**Script:** `docs/blender/blender_updates/601_lantern_charge6.update.py`. **Poses:** `lantern_charge6_poses.json`.

KEEP: L1c (stand, half step, ring fist into the port, two pushes that tip the lantern), the charge light running from
the port down the whole lantern, the G3 order (fill → overcharge → let-go flash → fade), saturated green, never white.
The whole sequence is now 6 s (120 ticks); L1c's keys stretched to fit: idle 0, lean 9, push 30, lean 52, push 74,
lean 96, idle 120. Idle glow 0.12 before and after.

| Take | Fill (0.12 → 1) | Overcharge (→ 1.25, pulsing) | Let-go flash + fade |
|---|---|---|---|
| C6a | 4 s (ticks 9–90) | 1 s (90–110) | 0.5 s (110–120) |
| C6b | 4.5 s (9–100) | 0.6 s (100–112) | 0.4 s (112–120) |
| C6c | 3.3 s (9–75) | 1.5 s (75–105) | 0.75 s (105–120) |

Brightness lowered so the full glow stays green in Blender (glass ×2.2, inner glow cubes 1 + 5 × charge, lamp 25 × charge).
