# Pass 510: big slam (S3 M3 picked) triggered from free flight (Chat C) — WAITING

J on 508: "S3 M3 instant launch, i should be able to fly freefully and the animation should maybe start once I start
to nose dive and the animation should start when im flying at a certain speed and reach a certain distance from the
ground (5 or 3 blocks?)". **S3 M3 PICKED** (7×7 crater, mobs launched the tick after touchdown, crater lit 6 ticks
longer, 0.7 s lock).

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\flight_slam4.blend`, Cam S3 H5, frames 1–60 (touchdown frame 35).
**Script:** `docs/blender/blender_updates/510_flight_slam4.update.py`. **Files:** `sheet.png`, `flight_slam4_poses.json`.

- You fly freely (weaving and banking, 14 blocks up) in the normal flight pose, then nose-dive yourself; the body just
  follows your pitch.
- **Trigger rule** (checked once a tick): pitched down ≥ 40°, speed ≥ 1.0 blocks a tick (20 b/s), height ≤ the trigger
  height. Then the slam animation fits into what is left of the fall: the ring fist swings forward to lead, the legs
  swing under, you land in the slam.

| Take | Trigger height | Fired at | Speed | Pitch | Animation length |
|---|---|---|---|---|---|
| H6 | 6 blocks | 5.1 blocks | 1.16 b/tick | 67° | 4 ticks |
| H5 | 5 blocks | 4.0 blocks | 1.24 b/tick | 69° | 3 ticks |
| H3 | 3 blocks | 2.7 blocks | 1.32 b/tick | 70° | 2 ticks |

Dive steeper or faster and the same height gives fewer ticks. Below 20 b/s or shallower than 40° nothing triggers
(you just land as normal).
