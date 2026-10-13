# Red battery: reflect like a diamond block under shaders (2026-10-13)

From the Blender thread. J wants the Red corps battery to have "the same kind of reflectivity as the diamond" in
his shaders (Complementary in Lunar).

## What to change

`ShaderPackIds.lookLike` already gives some of our blocks a vanilla block's shader ID: Skystone uses purpur, and
Hope Quartz uses the quartz blocks.

1. Add the red battery block and the Lava Font to `lookLike` as `Blocks.DIAMOND_BLOCK`, state by state as the
   others are. Skip the glowing states, so they keep the light ID that `lightFor` gives them.
2. Do the same for the held item, so the battery shines in hand: give it `Items.DIAMOND_BLOCK`'s ID in
   `patchedItems`.
3. If the battery renders as an entity or a BbModel and not as a block model, the block-ID trick won't reach it.
   Use a LabPBR specular map instead: `red_battery_s.png` next to its texture, with smoothness about 0.9 and F0
   about 0.04 (a gem, not a metal). Complementary reads that when its PBR setting is LabPBR.

## Look (from `rage_battery_c.blend`)

- The stone parts are one smooth, glossy crimson: sRGB (188, 30, 47), the centre colour of the crimson diamond.
- They have no tiled facets, just a very soft large-scale variation, with shadowed parts a shade deeper.
- The glowing parts keep their light.
- The texture should be re-baked to that smooth crimson when the battery model comes over. I'll send the model
  once J has picked the handle (C1 arched, C2 ring or C3 horns).
