# Hand-off from the Blender thread: particle-barrier surfaces for the game (2026-10-13)

J's picks from Blender (`rage_battery_c.blend`, the T row): **T1, T2, T3, T5, T6, T7 and T9** should go in game.
They are the moving surface of the particle constructs (barrier, wall, dome).

**Format:** `construct_barrier_<t>.png` strips in the usual format:
- 256 px, 4 × 4 blocks;
- 32 frames, frametime 5 (an 8 s loop), interpolated;
- seamless and looping: every strip passed the seam, loop and motion tests;
- each has a `.mcmeta`.

**What each strip contains:**
- a faint green shell;
- construct pixels twinkling on it;
- the T layer moving in more than one direction.

The alpha is capped at 252/255 (99%), so the barrier is never fully opaque. Use the strips as translucent LAYER sprites on the barrier faces.

| File | Design |
|---|---|
| `construct_barrier_t1` | bands ×3: wide soft dark bands running three ways |
| `construct_barrier_t2` | warped bands: dark bands bent by slow noise |
| `construct_barrier_t3` | radial bands: soft dark rings breathing outward (one centre per 4 × 4 blocks) |
| `construct_barrier_t5` | radial glow: a soft ring of light expanding (one centre per 4 × 4 blocks) |
| `construct_barrier_t6` | light clouds: patches of light drifting |
| `construct_barrier_t7` | soft veins: two layers drifting opposite ways |
| `construct_barrier_t9` | bands + veins: crossing soft bands with faint veins |

**What to build:**
- Make each one a Ring Lab option for the particle barrier's surface.
- Render only the barrier's outer shell: no faces between neighbouring barrier blocks, as in the earlier seam fix.
- In Blender, the real particles (drifting pixels) sit over the shell. In game, spawn the matching construct pixel particles on the barrier's outside faces in the corps' shades, a few per block, drifting slowly. The twinkling pixels in the strip stand in for them at a distance.

**Jar size:**
- The 32 px set (`textures_32px/`) is 1.8 MB.
- The 64 px set (`textures/`) is 2.3 MB.
- `barrier_surfaces.png` is a contact sheet of all seven.

**Not picked yet:** J is also reviewing five new particle wall designs (W1–W5) in Blender.

Tool: `tools/construct_designs9.py`.
