# Pass 703: BRD bricks and X5E ripples, three takes each

J re-rated 701 at 18:47:
- **BRD** (was KEEP, now IMPROVE): "try giving this one more detail on the bricks, or make them one of our new metallic
  materials for the brick material (not the glowing lines though)"
- **X5E:** "we need textures where the ripples are more efficiently packed onto big texture surfaces"
- X1 and X3 are now DROP, so their 702 variations are out of spec 702. BRN stays KEEP.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\constructs\skin_variations2.blend`. Cameras are
  `Cam <code> close` (for example `Cam BRDb close`), the same 8-second close tour as 701: wall, dome, particles, suit.
- Textures: `tools/construct_designs11.py` (strips in `LanternLive\suit_tex\`: brdc_neon, brdc_mask, x5g/x5i/x5r_emerald).

The ripple takes are X5Pa-c (renamed from X5Ea-c so they don't clash with 702's X5Ea-c).

| Take | What changed |
|---|---|
| BRDa carved | bevelled brick edges lit from the top left, stone grain, hairline cracks, chipped corners, pits; mortar and sparks as BRD |
| BRDb brushed alloy | bricks are brushed metal (pass 603's pinstripe alloy), the carving as relief; only mortar and sparks glow |
| BRDc dark gunmetal | bricks are dark hammered metal (pass 603's hex plate metal), the carving as relief; only mortar and sparks glow |
| X5Pa ripple grid | one ripple source per block (16 per tile instead of 1), rings interlocking at the block edges |
| X5Pb interference | seven sources per tile, waves adding into a moving lattice over the whole surface |
| X5Pc ripple rain | 46 small ripples spawning all over at different times, like rain on water |

Render on J's PC: double-click `C:\Users\Josh\Documents\LanternLive\RENDER.cmd` (it renders every pass that needs it,
one run at a time; if a run is already going, 703 is picked up by the next one).
