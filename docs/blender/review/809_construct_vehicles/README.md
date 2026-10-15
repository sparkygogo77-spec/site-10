# Pass 809: construct vehicles and mounts — WAITING

**Script:** `docs/blender/blender_updates/809_construct_vehicles.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\constructs\construct_vehicles.blend` (Cam V4, press play; 100 frames)
**Files here:** `sheet.png` (check render: Cam V3 following the horse mid-gallop, tick 50)

Each one forms under the rider pixel by pixel from the ring, front to back, in ticks 1–24, then moves off. Every
surface wears one of your animated construct textures from the texture library (green, 4 ticks a frame,
crossfaded), at 90% opaque, with glowing rims.

| Take | Mount | Texture | Motion |
|---|---|---|---|
| V1 | jet: swept stepped wings, twin engines with flames, canopy, fin | H1 hex | rolls 6 blocks, lifts off, climbs to 9 blocks and banks ±25° |
| V2 | motorbike: spoked wheels, tank, bars, lamp | W1 weave | rides off (wheels turn at the right speed for the distance), leans 22° into a turn, leaves a light trail |
| V3 | horse: barrel, neck, head, mane, tail, 4 legs with knees | BR1 bricks | a four-beat gallop (10-tick stride), the body bobs, the head and tail move with the stride |
| V4 | dragon: 6-link neck, horned head with a jaw, 8-link tail, two-part wings with glowing spars | X3D1 ripples | wings beat every 16 ticks, the neck and tail wave, the legs tuck, it takes off and climbs |

The rider sits with the ring hand forward on the controls. "Cam <take>" follows behind; "Cam <take> side" is fixed.

**For J:** KEEP / IMPROVE / DROP per mount, and say whether the texture should change per mount or follow the
player's Ring Lab pick.

## J's verdict (2026-10-15)

"horse is the only flying construct i want right now ... give me a flying baby dragon to ride on and also a ghast
construct". The jet, bike and big dragon are dropped; the flying horse, baby dragon and ghast are pass 824.
