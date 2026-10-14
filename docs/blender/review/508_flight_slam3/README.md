# Pass 508: flight slams, lock picked, mobs launched on contact (Chat C) — WAITING

J on 501: "locked .7s" (**L2 PICKED**: 14 ticks) and "mobs should be sent away as soon as i make contact instead of
sending out a shockwave that does a small amount of time to reach the mobs ... so the construct stays a little after
the area is immediately clear so just make the mobs launch instantly or almost".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\flight_slam3.blend`, Cam S2 M1, frames 14–64 (touchdown frame 35).
**Script:** `docs/blender/blender_updates/508_flight_slam3.update.py`. **Files:** `sheet.png`, `flight_slam3_poses.json`.

KEEP from 501: S2 medium + S3 big, dive, slam pose, crater, the 0.7 s lock with the landing block held, release pixels,
stand-up. Launch strength and direction unchanged. The ground pulse is now only a look; it doesn't time the hits.

| Take | Mobs launch | Crater |
|---|---|---|
| M1 | the tick after touchdown, all at once | 501 timing (ring d gone at 4 + 2d) |
| M2 | almost: 1 tick per 3 blocks (far edge of S3 by tick 2) | 501 timing |
| M3 | the tick after touchdown | stays lit 6 ticks longer, so the cleared area holds a moment |
