# No first-person animation for the punch or the flying flurry (J, 2026-10-15 ~21:55 UTC)

J: "no 1st person animation for the punch currently, no flurry either". Screenshots `2026-10-15-no-fp-punch-*.png`
(third person shows the punch pose fine; first person shows nothing special).

Cause (from the code on main): `RingFirstPerson.aimArm` only plays vanilla's bare-hand swing for a punch; the only combat poses wired
into first person are the slam dive and the rebuild (`CombatPoses.slamFist`, `CombatPoses.rebuilding`). The punches and the flying
flurry exist only in third person (`PlayerModelMixin`, CombatPoses).

To build in first person, from J's KEEPs:
- **Punches, pass 502:** P1b step-in jab (0.45-block step in) and P1c hook, 40-tick loops. Blender: `LanternLive\combat\...` (502
  spec `docs/blender/review/specs/502.json`, its first-person cameras `camfp`, clips on the review site). P1a (straight cross) is
  still IMPROVE ("switch hand unless it's on both").
- **Flying flurry, F2** (commit f6f84a1f, "flying flurry F2"): needs a first-person version of the same strikes, ending in the backfist.
- Match the review site's first-person clips (120° view) so what J rated is what he sees in game.
