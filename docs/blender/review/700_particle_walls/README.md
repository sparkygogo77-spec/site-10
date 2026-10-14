# Pass 700: particle walls W1-W5 (Chat E, 2026-10-14)

The five walls from `tools/blender_edits/particle_walls.py` (2026-10-13) never reached J: they were built into a copy of
`rage_battery_c.blend` that wasn't delivered. Pass 700 rebuilds the same five designs, unchanged, as a small standalone
scene on a dark floor: `C:\Users\Josh\Documents\LanternLive\particle_walls.blend` (0.2 MB), start on **Cam W1**,
frames 60-200 (the walls fill in over the first ~40 frames).

- W1 curtain: pixels pour down the face and are reborn at the top
- W2 lattice: pixels lock into a block grid, flicker, drop out and lock back in
- W3 swarm: a cloud of pixels swirling inside the wall's volume
- W4 rising: embers rising from the ground line, fading at the top
- W5 shards: bigger flat shards tumbling slowly over a dark shell

All corps greens, at most 99% opaque. `sheet.png`: frames 30/90/150 per wall. Script:
`docs/blender/blender_updates/700_particle_walls.update.py`.
Next: J picks; then Orange corps look and Blue B1-B3 tests (701+).
