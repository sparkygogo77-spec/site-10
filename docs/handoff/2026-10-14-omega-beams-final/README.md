# Omega beams, final (J picked, 2026-10-14) — for the game

Supersedes the beam look and routing in `docs/handoff/2026-10-14-omega-beams.md`. Starts (E1–E4 Ring Lab options),
trigger (hold a key while aiming) and the hover brake stay as in that brief.

Blender reference: `C:\Users\Josh\Documents\LanternLive\combat\omega_strike.blend` (pass 517, takes K1, F2, U3) and
`omega_erratic.blend` (pass 516, look). Scripts: `docs/blender/blender_updates/51[1-7]_omega_*.update.py`.

## J's picks, in order
- 511 → 513: straight sides with sharp corners, built out of the eyes; **P3 "mixed is good do .8-3.2"**.
- 513: barrage targets "random ... regardless of distance ... just have to be in your FOV".
- 514: "obey the movement physics totally"; running targets: sides "up to 1.4", chase a fast flyer "at about 95% of their speed".
- 516: "rotate on their joins more ... erratic paths unpredictable completely ... darker"; **W2 boiling sleeve** under water.
- 517: **E2 wild**, fast flyer kept; hit "when the line makes another angle"; **K1 snap** strike; **U3** "wild at the speed of the restless" (1.6× under water).

## The beam
- One **pair** per use, one laser from each eye, 0.26 blocks apart, running side by side.
- The line is **built out of the eyes**: it stays joined to the eyes and grows from them while it runs; after the hit it
  lets go and burns away from the eye end at 2.5× head speed.
- Sides are straight, joined by sharp corners. Side length 0.8–3.2 blocks × speed scale.
- **Head speed** = max(2.2, 0.95 × target speed / 0.45) blocks a tick (× 1.6 under water). Speed scale for sides =
  1 + 0.4 × min(1, target speed / 1.5 blocks a tick) (×1.4 at 30 b/s).
- Gives up after 5 s (100 ticks) and burns away.

## Erratic routing (E2), per new side
- w = 0.15 + 0.85 × (laid / (2.2 × 45))^1.5, capped at 1, where `laid` = blocks of beam laid so far (counts distance,
  not time, so a faster head keeps the same wild shape).
- aim = the target's position `lead` ticks ahead, lead = min(40, distance / (head speed × 0.45)).
- direction = normalize(w × to_aim + (1 − w) × random unit vector (z + 0.3, then normalized; forced downward above 12 blocks)).
- roll += π ± 1.2 rad (uniform); the side bends off `direction` by angle A toward (cos roll · v + sin roll · w⊥),
  A uniform in [55°, 72° + 48° × (1 − w)] while w < 0.95, then [55°, 63°] (keeps gaining).
- Keep every corner between 0.4 and 14 blocks up (reflect off the floor).

## Hitting
- **Hit on contact:** every tick, sweep the head's step in 0.25-block samples against the target box (0.75 blocks);
  any touch, on any angle, is a hit.
- **K1 snap strike:** when w > 0.6 and the target is within 1.5 sides (1.5 × 3.2 × scale), the next two sides are a
  kink 0.6 blocks off the line at 35% of the way, then straight to where the target will be on arrival. Lands within
  0.75 blocks. Flash ring 0.3 → 1.8 blocks over 7 ticks at the hit.
- **Incinerate:** the target turns to embers the tick it is hit, gone in 10 ticks (0.5 s), ash rising from tick 4 for 20 ticks.

## Barrage
- Calm stance, head level, no turning. 0.6 s charge (eyes build, 10 red sparks gather).
- Targets: only those inside a 110° field of view in front; the order is random every shot (never nearest first).
- The **same pair** threads every target in turn (each one: erratic sides, then a K1 strike). Movement comes back
  once the line lets go of the eyes at 10 blocks long.

## Ground use
- Slow walk allowed while firing: 0.04 blocks a tick (0.8 b/s); head tracks the target.

## Look (darker, pass 516)
- Core: (191, 26, 13), radius 0.02 blocks, full-bright. Glow sheath: (140, 3, 0), radius 0.07, fading to its edges.
  Never washed to white. Bloom/Iris-friendly glow.
- Flickering hot spots along the line: brightness × 0.55–1.8 from noise ~0.5 blocks, moving 0.4 blocks a tick.
- 2 embers a tick shed from random points on the line, 8-tick life, drifting up.
- One red light at the head (and one mid-line if cheap).

## Under water
- Head speed × 1.6 (U3), same E2 wild shape.
- **W2 boiling sleeve:** 9 small bubbles (0.05 blocks) a tick from random points along the whole beam, rising
  0.05 blocks a tick, each in and out in 4 ticks. After the beam is gone the sleeve fizzes on for 0.4 s (8 ticks) along
  where it was, 9 → 0 bubbles a tick.

## Files
- `poses/omega_strike_poses.json` — per take: fire tick, hit tick, strike, head speed.
- `assets/sheet_517.png`, `assets/sheet_516.png` — contact sheets.
