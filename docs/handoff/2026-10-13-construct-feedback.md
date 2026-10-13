# J's in-game feedback on constructs and the lantern (2026-10-13)

From the Blender thread. These are game changes, so they're yours. J tested in Lunar Client with Complementary shaders.

## Keep

- **The construct dissolving when the ring starts charging is great.** Keep it exactly as it is.

## Fix

1. **Constructs are too opaque.** J: "these textures can have less opacity" (Dome, Burst and Anvil all read as solid green).
   - Multiply construct alpha by about **0.5** (the inner layer is about 80% alpha today), keeping the rim and light lines a bit stronger.
   - Better: add a Ring Lab slider, "Construct opacity", from 0.2 to 1.0 with a default of 0.5, so J can pick.
2. **Block seams show on multi-block constructs.** J: "the edges of the anvil make it clear the block repetition, it wasn't supposed to be like that on the edges".
   - Every block draws its own rim/edge on all six faces, so a 4×4 face shows a grid.
   - Draw the rim/edge only where the neighbouring block is **not** part of the same construct (connected-texture style: the outer silhouette only).
   - Inner faces between two construct blocks shouldn't render at all.
3. **The texture stretches on scaled constructs.** J: "I see the texture stretches over larger items?" (Anvil at 2.5×).
   - The texels grow with the model scale.
   - Keep texel density fixed in world space: 64 px per world block, so UVs repeat ×scale. The pattern should look the same size on a 1× and a 2.5× Anvil.

## New

4. **The lantern should emit low-level light at all times**, not only while charging.
   - **Held** (hand or off-hand): a moving light of about level 6 around the player. Use a server-side light block that follows the player, or LambDynamicLights compatibility if it's present.
   - **Visual:** the glass never goes fully dark. Keep an idle glow of about 10–15% of the charge glow in the corps colour (the G3 centre ball, dim and slowly turning).
   - **Placed:** already level 13 (`POWER_BATTERY`); no change.
5. **Every corps gets its own look.** J: "every ring will probably have to have a different look for its textures of constructs, and its associated lantern/ring match".
   - Each corps (Green, Red, Yellow, Blue, Violet, Orange) gets its own construct texture design, and a lantern and ring that match it.
   - Today the other corps are hue shifts of the green textures (`construct_inner_<corps>`, `construct_rim_<corps>`, `construct_brick_<corps>`).
   - I'm designing the per-corps sets in Blender next and will send J's picks as a hand-off. Until then, keep the hue shifts.
