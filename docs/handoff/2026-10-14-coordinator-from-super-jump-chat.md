# For the coordinator: everything from the super jump Blender chat that isn't in game yet (2026-10-14)

This chat is splitting into two (see `2026-10-14-new-chat-briefs.md`). Everything is on `claude/lantern-redesign-pass2`. The order below is J's priority as best I can tell.

## 1. Super jump (brief: `2026-10-13-super-jump-ring-lab-brief.md`)

1. **Landing default:** make **E2** the default for `super_landing`. J picked E2; it's E1 now.
2. **Coverage:** add a `super_coverage` setting with four values:
   - `CRATER` (P2);
   - `RIM_HALF` (P4a, the rim goes ½ block straight up);
   - `RIM_FULL` (P4b, 1 block);
   - `WIDE` (P3, the crater plus a one-block lip).

   All four are wanted. Give each ring its own default and keep it swappable between rings later.
3. **Rising arm (G2 + G3):**
   - elevation = clamp(75° + 0.5 × look pitch, 55°, 90°);
   - it rests 15° forward;
   - yaw follows the head, with the body taking 1/3;
   - the arm wears the square emblem ring.
4. **Ribbon R1:**
   - it trails the ring fist on the way up and down;
   - it is never more than 1–2 blocks long: life = min(2 ticks, cap / speed);
   - the tail tapers.

   The glow build-up toward touchdown is 20 + 150·u^2.2.
5. **Blocks:** crater blocks crumble and drop. J runs a block-drop physics mod, so no upward launch.
6. **Deeper falls:** use E3, with guard walls that rise and then fade.

## 2. Construct textures (`docs/texture_library/`, see its README)

- **Good textures for every corps colour:**
  - BR1, W1, H1 (the only hex), R1, R2, V1 and X3D1;
  - colours: green, blue, crimson, yellow, violet and orange.
- **Files per texture:** the block strip and `.mcmeta`, a 32 px version, a landing-barrier strip, three particle sprites and a Blender preview. Wire them up as the per-corps looks.
- **Crimson constructs:** use BR1, W1, H1 and R2.
- **Blue:** BR1 jade in dark blue (`br1_blue`).
- **Drop:**
  - the classic textures and `WallLook.CLASSIC`;
  - H2 and HW;
  - X5;
  - my X3 XM1–XM3 takes (X3D1 is the X3 pick).
- **R2 K1:** J wants it tested in game.

## 3. Construct smoke and light (`92_` / `94_construct_smoke_rays*`)

J picked "long rays":
- every face of a construct glows;
- the glow in the air fades smoothly to nothing over 4 blocks;
- light beams leave every side and the top.

In game this needs a real light source on each face, so shader packs make rays, plus a soft glow particle field fading over 4 blocks.

## 4. Corps metals (`2026-10-14-crimson-diamond-surface.md`)

- **Which blocks:**
  - diamond, emerald, iron, gold, netherite and copper;
  - chiseled quartz, quartz bricks and quartz pillars;
  - red, chiseled and cracked nether bricks.
- **Colours:** each block in every corps hue plus black. The ramps are in `tools/corps_metal_recolour.py`.
- **Shader ID:** keep each source block's shader ID with `ShaderPackIds.lookLike`, so they reflect like diamond in J's shaders.
- **Textures:** recolour the vanilla texture at load time. Don't ship Mojang's textures.
- **Glowing nether bricks:** the brick is metal and the mortar is lit, using `tools/glowing_nether_bricks.py`. It needs an emissive overlay or LabPBR emission.
- **Smooth black metal:** our own texture from `tools/smooth_black_metal.py`, which can ship.

## 5. Red corps towers (Blender only for now)

- **Rule:** one design idea per tower, colours that blend, no pillars.
- **Latest:** `red_tower_f.blend`, waiting on J's pick:
  - F1 crimson diamond;
  - F2 construct brick;
  - F3 smooth black metal.
- **Glowing redstone:** vanilla redstone blocks give no light, so they need a light-emitting variant.
