# Pass 506: omega beams round 5, irregular zigzag (Chat C) — WAITING

J on 504: "zigzag is the one but shorter streaks maybe and it should go in all kinds of directions randomly instead of
direct so it can hit from unpredictable angles every time zigzag is it but the streaks are shorter and turn more often".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_beams5.blend`, Cam O1-Z2, frames 1–140.
**Script:** `docs/blender/blender_updates/506_omega_beams5.update.py`. **Files:** `sheet.png`, `omega_beams5_poses.json`.

KEEP from 504 (zigzag picked): one parallel pair per use (0.22 blocks apart), the 4.5-block tail that is never straight
and keeps moving, O1 slow walk, O2 hover brake, 0.5 s incinerate, O3 calm chaining barrage.

**New zigzag (lightning-like):** corners at random gaps along the line, each kicked 0.14–0.32 blocks out in its own
direction round the line; every kick keeps turning at its own rate (±0.35 rad a tick), so the short straight streaks
keep flickering into new shapes. 504 had a regular switchback every 0.72 blocks.

**Unpredictable routes:** 2–6 waypoints thrown well off the straight line (each detour capped at 3 blocks), and every
target approached from a random side 1.2–2.4 blocks out, including from above, the side or behind. New seed per shot.
Head speed 1.3 blocks a tick (504: 0.9) so the wandering doesn't slow the hit.

| Style | Corner gap | Route spread | Waypoints |
|---|---|---|---|
| Z1 | 0.35–0.6 blocks | 0.35 × distance | 2–4 |
| Z2 | 0.22–0.4 blocks | 0.35 × distance | 2–4 |
| Z3 | 0.22–0.4 blocks | 0.5 × distance | 4–6 |

Hit times (ticks from the start): O1 volleys 28–34 / 64–77; O2 38–46; O3 barrage all 6 targets by tick 89–118.
