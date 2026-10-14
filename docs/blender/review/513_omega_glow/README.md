# Pass 513: glowing omega beams, random targets in view, chasing a horse (Chat C) — WAITING

J on 511/512: "the omega beam shouldnt consider the closest target as the next threat, it should decide on a random
basis regardless of distance once the laser is set the targets just have to be in your FOV ... now i need the light of
the beams themselves to be a texture that glows but is still brighter in the current body/or center of the laser, it
needs to glow along the entire line". Then: "Q3 P3 mixed is good do .8-.3.2 and I need a moving target like a running
horse" → **P3 PICKED**, sides now **0.8–3.2 blocks** (55–72°).

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_glow.blend`, Cam C-G1 (horse) or Cam B-G1 wide (barrage),
frames 1–140. **Script:** `docs/blender/blender_updates/513_omega_glow.update.py`. **Files:** `sheet.png`, `omega_glow_poses.json`.

## Targeting
- Only targets inside your field of view (110° across, in front of you) are taken; blocks behind you are ignored.
- The order is random every shot, never nearest-first.

## Chasing (moving targets)
- Each new side aims where the target **will be** when the line gets there (lead = distance / (0.45 × head speed),
  capped at 2 s), so it intercepts a running target instead of trailing it.
- Within one short side (0.8 blocks) the last side homes in, re-aimed every tick.
- Past 2× the starting distance the switchbacks close in at 25–40° (never one long straight line).
- Switchbacks swing mostly sideways (the plane tilts at most 40°) so the line always makes headway and never digs
  into the ground.

## Glow (for the game's render)
- Every laser is a **hot core** (pink-red (255, 71, 51), radius 0.03 blocks) inside a **glow sheath** (deep red
  (255, 10, 5), radius 0.13 blocks) that runs the whole line. The sheath fades to its edges (strongest where it faces
  you), with bloom. Never washed to white.
- G1: core + glow. G2: + pulses of light running out from the eyes (brightness × (0.6 + 0.9·max(0, sin(2.4·d − 1.1·tick))),
  d = blocks from the eyes). G3: + 2 red embers a tick shed from random points on the line, drifting off, 8-tick life.
- Two red lights per pair (head and middle of the line).

| Take | What | Hits (ticks) |
|---|---|---|
| B-G1..G3 | barrage, 6 targets in view (3 behind ignored), random order | all six by tick 89–96 |
| C-G1..G3 | chasing a horse galloping across at 13 b/s, 18 blocks ahead | 42–45 |
