# Pass 811: a lantern shrine — WAITING

**Script:** `docs/blender/blender_updates/811_lantern_shrine.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\lanterns\lantern_shrine.blend` (Cam S1, press play; 260 frames)
**Files here:** `sheet.png` (check render, Cam all, tick 165, overcharged. After it the beam core was dimmed from 4 to
2.4 and the stone made a little lighter so the steps read.)

All the glow follows one charge value, `scene["lit"]`:

- 0 at rest.
- A player holds the ring to it in ticks 20–140, raising it to 1.
- Overcharge to 1.3 at tick 150, held to tick 190.
- Fades out by tick 250.

Every lit part has a threshold and lights over 0.25 of charge after it, so the light climbs the build in order. Each
lit part gets brightness × (1 + overcharge).

| Take | Build | Order of light |
|---|---|---|
| S1 charging altar | 3-step dais, altar with a gold-capped lantern, runes round each riser, 4 braziers | lantern and inlay → bottom-step runes → middle → top → braziers (0.85) → beam (0.95) |
| S2 lantern tower | 8-block tower, BR1-textured windows on the odd floors, glowing ledges, lantern on top, 8-spike crown | floor by floor from the bottom (0.08 → 0.93) → crown (0.9) → beam |
| S3 pillar ring | 8 pillars (W1-textured seams) round a plinth lantern, radius 4 | pillar by pillar round the circle (0.1 → 0.85) → arcs joining the tops (0.97) → beam up the middle |

The glow is saturated green. The lantern's point light follows lit².

**For J:** KEEP / IMPROVE / DROP per build. A kept one becomes a structure (or a block set) for the mc chat, with the
charge value coming from the lantern block's charge.
