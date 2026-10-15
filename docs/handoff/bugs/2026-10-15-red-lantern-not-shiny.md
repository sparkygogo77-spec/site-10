# Red lantern in hand: flat matte red, not diamond-shiny (J, 2026-10-15 ~22:35 UTC)

Screenshot `2026-10-15-red-lantern-not-shiny.png` (first person, Red battery in hand, Complementary Unbound 5.81 patched, diamond
blocks around it shining). J: "this lantern also does not have my desired textures, i want it to shine like these diamond blocks".

Cause: the held/first-person lantern draws as a BbModel, and there is **no LabPBR specular map** for it
(`textures/entity/bb/red_battery_s.png`, `red_battery_cover_s.png`, `red_lantern_s.png` don't exist; only `dark_lantern_s.png` does).
The block-ID trick (`ShaderPackIds.lookLike` -> DIAMOND_BLOCK) can't reach a BbModel.

Fix (already specified, step 3 of `docs/handoff/2026-10-13-red-battery-diamond-reflect.md`, never done):
- `red_battery_s.png` (+ cover, + `red_lantern_s.png`) next to each texture: smoothness ~0.9, F0 ~0.04 (a gem, not a metal),
  glowing texels keep their emission (alpha channel). Same route as `dark_lantern_s.png` (`tools/pixel_dark_bbmodel.py`,
  `tools/construct_jade_specular.py`).
- Re-bake the stone parts to the approved smooth glossy crimson, sRGB (188, 30, 47), very soft large-scale variation, shadowed
  parts a shade deeper, no tiled facets (red battery final hand-off `docs/handoff/2026-10-13-red-battery-final/`).
- Check the block and held item `lookLike`/`patchedItems` DIAMOND_BLOCK entries exist too.
- Screenshot test under the patched pack next to a diamond block, before/after.
