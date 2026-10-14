# Pass 509: flying flurry with the backfist finisher (Chat C) — WAITING

J on 507: "the back fist is good" (**F2 jab - cross - spinning backfist PICKED**), then "i need these flurrys while flying
now, and if i connect the first hit while flying the mob should follow the direction of my punches and i want to see the
backhand while flying send someone into a crater from the angle i punched them into the ground flying, atleast 50 blocks
if through the air they should regain control if they didnt collide and crater anything".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\flying_flurry.blend`, Cam A1, frames 1–100. Also `Cam <take> target`
(follows the target) and `Cam <take> wide`.
**Script:** `docs/blender/blender_updates/509_flying_flurry.update.py`. **Files:** `sheet.png`, `flying_flurry_poses.json`.

- F2's string in flight at 12 blocks up: jab tick 12, cross 17, spinning backfist 24 (a full turn from tick 19).
- You fly at 20 b/s, slow to 10 b/s from the first hit, and ease to a hover after the backfist.
- From the first hit the target is carried 1.7 blocks in front of you, nudged 0.25–0.3 blocks the way each punch goes.
- The backfist launches it at 2.4 blocks a tick along the angle of the hit (gravity 0.03/tick, drag 0.99, tumbling).

| Take | Angle | Result |
|---|---|---|
| A1 | down 20°, a little left | craters ~33 blocks ahead at tick 37 (3×3, D0 rules, impact ring, dirt), stuck in at that angle |
| A2 | level | no gravity while launched; after 50 blocks with nothing hit it regains control at tick 48: stops tumbling, rights itself in 6 ticks, brakes, drops and lands on its feet (tick 73) |
| A3 | down 60° | craters ~13 blocks away at tick 30 |

In game the crater/regain choice is automatic: whatever it hits first craters; 50 blocks with no hit means regain.
