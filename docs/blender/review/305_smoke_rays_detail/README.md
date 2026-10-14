# Pass 305: smoke rays with more detail

J (2026-10-14): the Blender chats should build as detailed as the Cowork chats. Pass 304's long rays (4-block glow,
every side glowing, beams from every side), plus a block-grid ground (16 px per block, a darker seam pixel per block),
a plain 1.8-block figure for scale and dust motes drifting in the light. Cameras `Cam D1` ... `Cam D3c`; frame 80.
Rebuild: `docs/blender/blender_updates/305_smoke_rays_detail.update.py`.

| Take | What it is |
|---|---|
| D1 streaks+ | L3 streaks with the detail. |
| D2 shafts+ | L2 shafts with the detail. |
| D3 pixel smoke | L3 with Minecraft-style pixel smoke puffs (0.18-block cubes) rising off the top in place of soft wisps; the puffs carry the corps light and lose it over 4 blocks. |
| D3c | D3 in H1 crimson. |

For the game later: motes and pixel puffs map onto particles (the library's `particle_<tex>_<colour>_mote.png`).
Open questions for J: ray style (from 304), and pixel smoke (D3) or soft wisps.
