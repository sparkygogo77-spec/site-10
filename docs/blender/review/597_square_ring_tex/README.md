# Pass 597: the square emblem ring with our animated textures — WAITING

**Script:** `docs/blender/blender_updates/597_square_ring_tex.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\lanterns\square_ring_tex.blend` (Cam P01 X5E ..., play)
**Sheet:** `sheet.png` at frame 70. Left to right, top to bottom: P01 H1, P01 X5E, P02 X5N, P03 X3D1, P04 W1, P04 X5E.

J: "can you put our textures on the ring yet, like the ripple?"

The rings P01–P04 from 596 each wear five textures on every green cell: X5 ripple emerald, X5 ripple neon, X3D1 ripples,
W1 neon weave and H1 neon hex.
- The textures are animated as in game: X5 and X3D1 at 32 frames × 5 ticks, W1 and H1 at 24 frames × 4 ticks, each
  frame fading into the next.
- One tile covers 4 model px.
- The voxel's own shade is multiplied on top, so the concentric steps still read.
- Gold, band, core and the light-up are unchanged from 596.

Cameras: `Cam row <ring>` shows a ring's five textures together; each ring also has its own `Cam <ring> <texture> ...`
and `... face` cameras.

While this was building, J also picked P03, N01 and N04 from 596 ("the glowing looks great").
