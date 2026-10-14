# Omega beams: put in the game (lead Blender chat to coordinator, J said "do omega beams", 2026-10-14)

Blender reference: passes 223, 224, 225 (`docs/blender/blender_updates/22[345]_omega_beams*.update.py`; J has
`omega_beams.blend`, `omega_beams2.blend`, `omega_beams3.blend`). J's rules:

## Use
- **Trigger:** hold a key while aiming; any corps.
- **Start:** the eyes flash red. On the ground the body locks in place; in the air it brakes to a hover while firing.
  Make the four starts from pass 225 Ring Lab options ("Omega start"): E1 snap (hard flash, head snaps to target),
  E2 smoulder (eyes build up ~1 s with red smoke, then fire), E3 air brake (pitch upright to brake, hover), E4 crackle
  (little red arcs round the eyes). Default E1.
- **Beams:** 2 a use, one from each eye.
- **Chase:** while the key is held the beams chase the targeted opponent until they catch it or the key is let go.
  **Let go mid-chase:** they keep going straight and hit whatever is ahead.

## Look
- Thin red lasers (about 0.8 px wide), colour ~(255, 15, 8), full-bright, with a bright head and a ~1.4-block fading
  tail, each carrying a red light (dynamic light or Iris-friendly glow) so it lights the air and the ground it passes.
- **Irregular paths every time:** per beam, 2-4 random waypoints thrown off the straight line (sigma ~0.28 x distance,
  biased upward), a random final approach direction so it can strike from any angle, joined by a smooth curve
  (Catmull-Rom). Head speed ~0.85 blocks a tick.
- **Around obstacles:** plan the route round solid blocks (A* on a half-block grid with a little random cost, then a
  handful of waypoints, jittered and smoothed). **Moving targets:** steer toward the target each tick with a turn limit
  (~0.22 rad a tick at ~0.55 blocks a tick, plus small noise) so they swing round after it.

## Damage
- Each hit incinerates the block it lands on (one block per beam) and any mob it hits: it turns to glowing embers
  (orange, ~1 s, with a warm light), then crumbles to ash particles that drift up.
