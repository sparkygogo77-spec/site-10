# Hand-off from the Blender thread: round 6 green construct textures to test (2026-10-13)

J's picks from `texture_round6.blend`, to test as green construct looks:

| File | Design | Shade |
|---|---|---|
| `construct_green_x5_emerald` | quantum ripple: rings breathing out from a bright core, fine dust between | emerald |
| `construct_green_x5_neon` | quantum ripple | neon |
| `construct_green_x3_emerald` | power aura: wispy strands of power flowing over each other | emerald |
| `construct_green_x1_emerald` | cosmic dust: a web of glowing filaments through dark space, twinkling stars | emerald |

**Format:** the same as the corps hand-off (`docs/handoff/2026-10-13-corps-looks/`):
- 256 px strips, 32 frames;
- `.mcmeta` with `interpolate: true` and frametime 5, so each loops in 8 s, moving gently all the time;
- seamless, with see-through dark parts;
- use them as translucent LAYER sprites.

**What to build:** add each one as a Ring Lab option for the green constructs, alongside R2 K1 and the round-4 picks.

**X5 note:** X5 has one ripple centre per 4 × 4 blocks, so on a big wall the centres repeat every 4 blocks.

**Jar size:**
- The 64 px set (`textures/`) is 8.8 MB; the 32 px set (`textures_32px/`) is 3.5 MB.
- Use the 32 px set. With the corps set (4.7 MB) the jar will be over its 30 MB limit unless something is cut.
- Ask me for 16 px versions or shorter loops if needed.
