# Crimson diamond surface (super jump Blender chat to the coordinator and the lead chat, 2026-10-14)

## What J wants

J: "I want the diamond blocks that reflect, used as the surface with the same code, because it reflects well in my shaders and looks like good metal". He wants it "turned into the crimson red hue like we've made in Blender before".

So the surface is the vanilla diamond block, keeping its shader behaviour, recoloured to the Red battery's C1 crimson. It is not the cut-gem tile in `docs/texture_library/crimson/diamond/`; that one was a misread, so ignore it.

## In game (coordinator)

1. **The shader ID:** give the crimson surface block the diamond block's shader ID with `ShaderPackIds.lookLike(..., Blocks.DIAMOND_BLOCK)`. This is the same code as `docs/handoff/2026-10-13-red-battery-diamond-reflect.md`.
2. **The colour:** don't ship a copy of Mojang's texture. Recolour `minecraft:block/diamond_block` at load time instead.
   - **Option 1:** a sprite source or resource reload listener that reads the vanilla sprite and maps each pixel's brightness through the C1 ramp.
   - **Option 2:** a block-colour tint, though plain multiply comes out darker.
   - **The ramp:** (28,2,8), (88,6,20), (150,14,34), (214,52,66), (255,176,180), from `tools/pixel_rage_battery3.py` `REDS["c1"]`.
   - **The mapping:** brightness is normalised over the tile, and the darkest pixels sit at 12% so they stay off black.
   - **Reference:** `tools/crimson_diamond_recolour.py` does exactly this.
3. **Where it goes:** the Red towers' surfaces (pass 95). Row A puts it on the accents, row B on the whole body. It could also go on other Red builds.

## Blender

- **Scene:** `LanternLive\red_tower_v3.blend` (pass 95).
- **Shading:** shaded as polished metal (metallic 0.85, roughness 0.16, light coat) to stand in for how the diamond ID shines under J's shaders.
- **Preview texture:** `LanternLive\red_tex\diamond_block_crimson.png`, made from J's own game jar and used for the preview only.

## J's notes

- **C1 Fang spire** "looks good".
- **Constructs:** "not all constructs will look good on it". `crimson_diamond_pairings.png` sets each crimson construct look beside the surface for him to pick from.

## J's picks after pass 95 (2026-10-14)

- **Crimson construct looks:** use BR1, W1, H1 and R2 (crimson) on the crimson diamond surface. R1, X3D1 and V1 don't sit well on it.
- **Stone mix (pass 97, `LanternLive\red_tower_v5.blend`):**
  - **Body:** blackstone and polished blackstone bricks, polished and unpolished.
  - **Polished deepslate:** replaces the nether bricks and the basalt columns.
  - **Crimson diamond:** the accents, on the red bricks, crimson planks and stems.
  - **Glowing redstone blocks:** replace the gilded trim rings, so bands of red light run round the towers. In game, vanilla redstone blocks give no light, so these need a light-emitting variant (or the mod's light blocks) and the shader light ID.
  - **The four rows:** BR1, W1, H1 and R2 as the construct look on the ribs, claws, crowns and glass, so J can pick per tower.
- **Smoke and rays: J picked the bottom row of pass 94, "long rays".**
  - Every face of a construct glows.
  - The glow in the air fades smoothly to nothing over 4 blocks.
  - Light beams leave every side as well as the top.
  - **In game:** a light source on each face, plus a soft volumetric glow particle field fading over 4 blocks.
