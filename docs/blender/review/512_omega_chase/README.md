# Pass 512: omega beams chasing a moving target (Chat C) — WAITING

J: "I need to see the omega beams chasing a moving target in blender now, same physics".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_chase.blend`, Cam C1 (or Cam C1 wide / Cam C1 target),
frames 1–80. **Script:** `docs/blender/blender_updates/512_omega_chase.update.py`. **Files:** `sheet.png`, `omega_chase_poses.json`.

Same beams as 511 (P2 long sides; set `STYLE` in the script to "P1"/"P3" to compare): one parallel pair, straight sides
with sharp switchback corners, built out of the eyes and joined to them, head 1.8 blocks a tick, burns away from the
eye end after the hit, 0.5 s incinerate.

**Chasing rule (for the game):** the line is laid tick by tick. Each time a side is finished, the next side is aimed at
where the target is *now* (switchback angle and plane as in 511), so the line bends after it. Once the target is within
one short side (2.5 blocks for P2), the last side homes straight in, re-aimed every tick. If a route has run 3× the
starting distance it homes straight away. You walk slowly; your head tracks the target (±1 rad yaw, ±0.6 rad pitch).

| Take | Target | Fired | Hit |
|---|---|---|---|
| C1 | runner, sprinting across 18 blocks ahead at 6 b/s | tick 16 | tick 51 |
| C2 | dodger, zigzagging away, switching every 0.6 s | tick 16 | tick 48 |
| C3 | flyer, circling at 12 b/s, 4–8 blocks up | tick 16 | tick 39 |
