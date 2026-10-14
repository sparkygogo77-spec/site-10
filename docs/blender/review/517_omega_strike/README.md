# Pass 517: omega beams round 10 — wild (E2), hit on contact, strike endings (Chat C) — WAITING

J on 516: "wild is good fast flyer is also good, for underwater restless looks better maybe because its faster ... i want
wild but at the speed of the restless, also when for some targets it zips to the mob at the last second when it thinks
its close enough but the damage should accurately capable of being applied when the line makes another angle and when
that angle which obeys the particle capabilities it should default to a certain type of strike animation".
**E2 wild PICKED; F2 fast flyer kept.**

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_strike.blend`, Cam K1 target (follows the horse) or Cam K1 wide,
frames 1–130. **Script:** `docs/blender/blender_updates/517_omega_strike.update.py`.

## Rules for the game
- **Hit on contact:** every tick the beam head is swept (0.25-block samples) against the target's box (0.75 blocks):
  the moment any side touches it, on any angle, it is hit.
- **No last-second zip:** sides are never longer than one normal side (0.8–3.2 × speed scale). Once committed
  (w > 0.6) the corners stay in the 55–63° half so it keeps gaining. When committed and within 1.5 sides it makes a
  final corner and ends in a strike (lands within 0.75 blocks of the target):
  - **K1 snap:** a sharp kink 0.6 blocks off the line, then straight in.
  - **K2 coil:** two short sides wrapping round the target (0.9 blocks out, 120° apart), then in.
  - **K3 pierce:** straight through, carrying on 1.2 blocks past before burning away.
  - Every strike: a flash ring growing 0.3 → 1.8 blocks in 7 ticks, then the 0.5 s incinerate.
- **Wild at restless speed:** wildness now counts blocks of beam laid (
  w = w0 + (1 − w0) × (laid / (2.2 × T))^1.5), so a faster head makes the same wild shape sooner.
  U3: E2 at 1.6× head speed (hit tick 49), U4: E2 at 2× (hit tick 46), both with the W2 boiling sleeve.

| Take | Strike | Hit tick |
|---|---|---|
| K1 | snap | 106 |
| K2 | coil | 76 |
| K3 | pierce | 82 |
| F2 | fast flyer, snap | 86 |
| U3 / U4 | under water, wild 1.6× / 2× | 49 / 46 |
