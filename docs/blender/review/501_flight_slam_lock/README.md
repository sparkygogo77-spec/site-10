# Pass 501: flight slam tiers S2 + S3, locked in place on touchdown (Chat C) — WAITING

J on pass 500: "big slam and medium slam will be two tiers we keep before i test and assign it to a ring and how the
gameplay should work, it should lock me in place briefly where i touched down for the slam since this isnt the slide".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\flight_slam2.blend`, Cam S2 L2, frames 14–64 (touchdown frame 35).
**Script:** `docs/blender/blender_updates/501_flight_slam_lock.update.py`. **Files:** `sheet.png`, `flight_slam2_poses.json`.

## Kept from 500 unchanged
S2 medium (dive from 12, 5×5 crater, shockwave 5) and S3 big (dive from 20, 7×7, shockwave 7): the dive, slam pose,
D0 crater rules, ground pulse and mob knock. S1 dropped.

## New: the lock
- From touchdown you are held on the landing block for the lock: no movement input, no slide, no knockback. You hold
  the one-knee slam pose; looking around stays free.
- The landing block stays construct for exactly the lock (the "held" cue), then fades back over 6 ticks while a small
  ring of 8 pixels pops off your feet.
- Then you stand up in 8 ticks and are free.

| Take | Lock | Free to move at (ticks after touchdown) |
|---|---|---|
| L1 | 0.4 s (8 ticks) | 16 |
| L2 | 0.7 s (14 ticks) | 22 |
| L3 | 1.0 s (20 ticks, what 500 held for) | 28 |

Each of S2 and S3 comes with L1, L2 and L3 (6 takes). Per-tick `locked` flags are in the JSON.

## Open for J
1. Which lock length, and the same for both tiers or longer for the big slam?
2. Can movement input end the stand-up early (cancel into a walk), or only after it finishes?
