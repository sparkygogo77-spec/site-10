# Pass 502: combat poses round 4, from J's notes on P1–P6 (Chat C) — WAITING

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\combat_poses4.blend`, Cam P1a, frames 1–40 (every take is a
seamless 40-tick loop). Every take has `Cam <take>` (over the right shoulder), `Cam <take> fp` (first person) and
`Cam <take> front`. **Script:** `docs/blender/blender_updates/502_combat_poses4.update.py`.
**Files:** `sheet_P1_P2.png`, `sheet_P4_P5_P6.png`, `combat_poses4_poses.json` (per-tick part rotations).

| J on 221 | Verdict | Round 4 takes |
|---|---|---|
| P1 "doesnt look like an actual punch" | IMPROVE | The hips and ring shoulder now drive the punch (221 turned the shoulder back). P1a straight cross, P1b step-in jab (0.45 block step), P1c hook. Ring flash + 7 construct pixels on each impact. |
| P2 "blast is good but the non ring hand shouldnt move so much as the ring hand both first person and third" | KEEP + fix | The free hand stays braced and follows the ring hand's recoil by P2a 0%, P2b 25%, P2c 50%. Bolt is now saturated green. |
| P3 "the shield looks like a worse version of the one we have" | DROP | The game's shield stays. |
| P4 beam "should have maybe a different effect … a looped feedback animation where the ring arm shakes a little and the other arm is to stabilize" | IMPROVE | 2 s loop. The ring arm shakes (5/7/11/13/17-cycle sine layers, about ±0.06 rad); the free hand grips the ring forearm and pushes back at 40% opposite; the knees pump slightly. New beams: P4a helix (two pixel strands spiralling a thin core), P4b pulse rings running out along it, P4c pixel stream. |
| P5 wall "is good but only use the ring arm" | KEEP + fix | Only the ring arm sweeps up. Free arm: P5a relaxed, P5b fist at the chest, P5c out and back for balance. |
| P6 slam "is good … but wastes time by putting the arm up first" | KEEP + fix | One smooth drop from standing into the slam, no wind-up: P6a 5 ticks, P6b 7, P6c 10 to impact. |

Beam shake (for the game's first-person arm): ring xRot += 0.045 sin(5·2πt/40) + 0.025 sin(11·2πt/40 + 1) +
0.012 sin(17·2πt/40); yRot += 0.03 sin(7·2πt/40 + 2) + 0.015 sin(13·2πt/40). Free arm gets −0.4× the same.
