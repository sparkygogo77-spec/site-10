# Omega beams (lead Blender chat; draft, not sent to the coordinator yet: J said "not yet" on hand-offs)

Blender: passes 223 (`omega_beams.blend`: O1 locked on the ground, O2 braking to a hover, O3 barrage) and 224
(`omega_beams2.blend`: Q1 round the corner, Q2 chase, Q3 through a window).

J's game rules (2026-10-14):
- **Trigger:** hold a key while aiming, any corps.
- **Beams:** 2 a use, one from each eye. Eyes flash red first; on the ground the body locks, in the air it brakes to a hover.
- **Look:** thin red lasers, irregular paths every time, any approach angle, glowing (light the air and ground).
- **Chase:** while the key is held the beams keep chasing the targeted opponent until they catch it or the key is let go.
  They route around solid blocks (A* on a half-block grid in Blender, steering with a turn limit for moving targets).
- **Damage:** each hit incinerates the block it lands on, and any mob it hits (embers, then ash drifting up).
