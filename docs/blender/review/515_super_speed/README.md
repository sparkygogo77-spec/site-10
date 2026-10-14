# Pass 515: super-speed flight on left click (Chat C) — WAITING

J: "a super speed flying left click ring flight speed/density enhance which obeys all the current mods we have and it
craters and slams if you dive harder". Picks: both activations to compare; looks: green light trail, afterimages,
ground wake; no bubbles (bubbles are for the omega beams only).

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\super_speed.blend`, Cam S1 (chase) / Cam S1 side / Cam S3 wide,
frames 1–120. **Script:** `docs/blender/blender_updates/515_super_speed.update.py`. **Files:** `sheet.png`, `super_speed_poses.json`.

| Take | Activation | Speed |
|---|---|---|
| S1 | hold left click: ramps 20 → 60 b/s over 1.5 s (smoothstep); release eases back to 20 in 1 s | 20–60 b/s |
| S2 | tap: straight to 60 b/s with a sonic boom ring + 16 pixels; holds 2 s, eases back | 60 b/s |
| S3 | S1, climbs to 16 blocks, then a hard dive | 60 b/s |

**Obeys the current mods (S3):** the pass 510 free-flight slam trigger (pitch ≥ 40°, speed ≥ 1 b/tick, height ≤ 5) —
at super speed the height becomes max(5, 3 × the fall per tick) so the slam animation still gets 3 ticks — then the
picked S3 M3 slam: 7×7 crater (D0 rules), mobs launched the tick after touchdown, crater lit longer, the 0.7 s lock.

**Looks** (scaled by speed above 30 b/s):
- Green light trail: 3 strands (both hands + body), length = 0.4 s of travel at the current speed (8 blocks at 60 b/s).
- Afterimages: 4 green copies (alpha 0.22), 1 tick apart, on above 40 b/s.
- Ground wake (below 4 blocks, above 30 b/s): 4 grass/dirt pixels a tick kicked up in a V behind you, and a flat
  construct ripple every 3 ticks, bigger the lower you fly.
- Ring glow rises 3 → 9 with speed. Posts every 12 blocks in the scene so the speed reads.
