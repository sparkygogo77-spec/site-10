# Red Lantern battery not in game yet + Rage Bull construct texture (lead Blender chat to coordinator)

J, 2026-10-14, in game on the latest jar (2.1.623): "the bull needs texture construct updates, where is my red
lantern toggle setting do we not have the latest iteration in game yet?" His screenshot still shows the old Red
lantern (gold frame, red drum, round emblem).

## 1. The final Red battery (never landed)
`docs/handoff/2026-10-13-red-battery-final/` on branch `claude/lantern-redesign-pass2` has everything:
`red_battery.bbmodel` + `red_battery_cover.bbmodel` + textures, the charge/heartbeat/drip behaviour, the diamond
reflect brief and the barrier surfaces. The retiring battery chat couldn't confirm its last messages reached you,
and `origin/main` has no `red_battery.bbmodel`. Please put it in, with a **Ring Lab toggle: Red lantern =
New battery / Classic** (default New), so J can flip between them in game.

## 2. Rage Bull skin
`ConstructSkins.get("rage_bull", ..., Corps.RED)` still lays the old green R2 K1 jade fragments over the bull and
tints them red. J picked his Red construct looks on 2026-10-13 (`LabSettings.redLook`: R1 magma, R2 bloodfire,
`construct_ripples_red_r1/r2.png`). Give Red constructs (bull first) that pattern instead of tinted jade, following
the `red_look` setting, animated like the Wall if the skin can step frames; one frame is fine to start.
Keep the bright rim and the glow layer.
