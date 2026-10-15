# Pass 837: eye beam chain round 3 (omega physics, speed by distance) — WAITING

**Script:** `docs/blender/blender_updates/837_eye_beam_chain3.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\eye_beam_chain3.blend` (Cam R1 top; also "Cam <take> side" and "Cam <take> eyes" first person; press play)

J on 833: "E1 and E3 for the eye chain but we made physics for how it should behave before, the lines should be much more erratic and not limited to a certain axis or rotation at all, they also move a little too fast it should move more proportional to how far its target is". KEEP noted: E1's look (streak glow) and E3's (pulse glow, sparks off the corners).

**Routing = the omega physics already picked** (`docs/handoff/2026-10-14-omega-beams-final/`, E2 wild + K1 snap), run
target to target along C1's layout:
- each new side aims at a blend of the target and a random direction (tipped up 0.3); the blend w starts at 0.15 and
  rises with the beam laid: w = 0.15 + 0.85 × (laid / (3 × the leg's distance))^1.5;
- at every corner the line rolls round half a turn ± 1.2 rad and bends 55° to 72° + 48° × (1 − w) off its aim, in any
  direction in 3D (55°–63° once w > 0.95), so nothing is tied to an axis;
- sides 0.8–3.2 blocks (shorter for a close target); corners stay 0.4–14 blocks up; never through a pillar;
- a hit on any touch (0.75 blocks); K1 snap strike once w > 0.6 and the target is within 1.5 long sides;
- through every target to the last; stops in a player; after the last hit it lets go and burns away from the eye end
  at 2.5× the head's speed.

**Speed (new):** head speed = k × the straight distance to the next target, 0.6 to 2.2 blocks a tick, set per target.
833 ran a flat 3 blocks a tick.

| Take | Look | k | Hits (ticks) |
|---|---|---|---|
| R1 | E1 streak | 0.3 | 23, 40, 59, 72 |
| R2 | E3 pulse + corner sparks | 0.3 | 21, 31, 50, 61 |
| R3 | E1 streak | 0.2 (slower) | 40, 61, 85, 109 |
| R4 | E3 pulse + corner sparks | 0.45 (faster) | 24, 31, 43, 57 |

**Colour:** the omega red you picked in 516 (core 191, 26, 13; darker glow 140, 3, 0), drawn with the laser kit (core
0.06 across, a camera-facing glow 0.32 wide, a faint haze) so it can be seen. Two lines from the eyes, 0.26 apart. After the
check render the glow starts after the first 1.3 blocks (right at the eyes it filled the first-person view).

**For J:** KEEP / IMPROVE / DROP per take, and the speed (k) you like.
