# Pass 516: omega beams round 9 — erratic, twisting at every joint, darker; W2 sleeve (Chat C) — WAITING

J on 514: "the beams should rotate on their joins more so they dont obviously directly chase the individual they should
make erratic paths unpredictable completely. and they should be darker. W2 boiling sleeve is the best but there should be
more of it along the beam and it should stay a little after the beam disappears but in and out or very quickly".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_erratic.blend`, Cam E2 wide (or `Cam <take>` / `Cam <take> target`),
frames 1–130. **Script:** `docs/blender/blender_updates/516_omega_erratic.update.py`.

KEEP from 514: one parallel pair from the eyes, sides ×1.4 with a running target's speed, head closing at 95% of a fast
target's speed, leading the target, 0.5 s incinerate.

**Erratic (for the game):**
- Each corner rolls the line round by about half a turn ± 70° (it twists in 3D, not a flat zigzag).
- Each new side aims at a blend of a random direction and the target: w = w0 + (1 − w0) × (age / T)^1.5;
  direction = normalize(w × to-target + (1 − w) × random). Early on it can loop up, swing wide or double back.
- Goes in once w > 0.6 and the target is within one long side, or once fully committed within two. Stays between 0.4
  and 14 blocks up.

| Take | w0 | Commit time | Corners up to | Sides | Hit tick |
|---|---|---|---|---|---|
| E1 restless | 0.45 | 1.5 s | 72° | 0.8–3.2 | 51 |
| E2 wild (J's sketch) | 0.15 | 2.25 s | 120° | 0.8–3.2 | 88 |
| E3 wild + long bursts | 0.15 | 2.25 s | 120° | 0.8–4.5 early | 100 |
| F2 fast flyer, E2 | | | | ×1.4 | 73 |
| U1 / U2 under water (E1 / E2) | | | | | 39 / 49 |

**Darker:** core (191, 26, 13) strength 5, glow (140, 3, 0) strength 1.6 (about half of 514), flickering hot spots, 2 embers a tick.

**Under water, W2 sleeve PICKED:** 9 small bubbles a tick all along the beam (514: 4), each in and out in 4 ticks;
when the beam is gone the sleeve fizzes on for 0.4 s along where it was, 9 → 0 a tick.
