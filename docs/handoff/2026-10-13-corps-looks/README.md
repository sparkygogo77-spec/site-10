# Hand-off from the Blender thread: a look for each corps' constructs, plus two lantern model fixes (2026-10-13)

J wants every corps to have its own construct textures, with a lantern and ring to match. These are his picks from
the Blender kits (`corps_red_yellow.blend`, `corps_blue_violet_orange.blend`). The game work is yours.

## 1. Construct textures for each corps (`textures/`, `textures_32px/`)

Each file is a strip in the same format as the earlier hand-off:
- 256 px wide (4 × 4 blocks at 64 px a block), frames stacked vertically;
- seamless and looping, and it passed the seam, loop and motion tests;
- a `.mcmeta` with `interpolate: true` and frametime 5, so most strips loop in 8 s (32 frames); R2 has 64 frames, a 16 s loop;
- dark parts are see-through, so use them as the translucent LAYER sprite, like `construct_ripples_*`.

| Corps | File (`construct_…`) | Design | J said |
|---|---|---|---|
| Red | `red_r1` | magma: dark crust plates split by molten cracks, embers rising | pick |
| Red | `red_r2` | bloodfire: red flames climbing the face | pick |
| Yellow | `yellow_y1` | scales: armour scales with a glint sweeping across | "all 3 yellow walls as options for now" |
| Yellow | `yellow_y2` | lightning: jagged forks crackling between hard points | same |
| Yellow | `yellow_y3` | dread: dark smoke with yellow sparks of fear | same |
| Violet | `violet_v1` | crystal: amethyst facets, each catching the light in turn | "try silk and crystal" |
| Violet | `violet_v3` | silk: flowing ribbons with a soft sheen | same |
| Blue | `blue_b1` | hope hex: calm hexagons breathing light | "the blue ones to test" |
| Blue | `blue_b2` | dawn: soft light rays sweeping across | same |
| Blue | `blue_b3` | renewal: orbs of light rising | same |

**What to build:**
- Where a corps has more than one pick, make each one a Ring Lab option for that corps' constructs, so J can switch between them in game.
- Use these in place of today's hue-shifted `construct_inner_<corps>` and `construct_rim_<corps>` for that corps.
- Green keeps its own textures.
- Orange is not picked yet.

**Jar size:**
- The 64 px set is 11.0 MB; the 32 px set is 4.7 MB.
- The jar was about 29.5 MB of 30 MB at the last hand-off, so use the 32 px set, and cut something if even that doesn't fit.
- If it still doesn't fit, I can make 16 px versions or shorter loops.

`all_corps_textures.png` shows every design from both kits (the picks plus the ones not picked).

## 2. Lantern model fixes (`models/`, laid out like the jar: `bbmodel/` and `textures/entity/bb/`)

`lantern_fixes_before_after.png` shows each lantern before and after.

**Red Lantern.** J: "red lantern geometry bleeds and flashes through a lot".
- **Cause:** every glass cube `body_N_i` has a twin `glow_body_N_i` in exactly the same place, so the solid and glow layers fight over the same pixels.
- **Also:** the rods, the housing and the lens sit flush on the glass and the glow.
- **Fix:**
  - The 138 glow cubes are inflated by 0.02 px, so the light sits just on top.
  - The 35 rod, housing, lens and frame-rod cubes are inflated by 0.01 px.
  - The texture is unchanged; the copy here is only so the folder is complete.
- **To do:** drop `red_lantern.bbmodel` in place of the jar's copy.

**Blue Lantern.** J: "blue lantern should be lit on both sides same way as this one is".
- **Cause:** the lit emblem window was only on the front; the back was a dark plate.
- **Fix:** 31 `glow_emblem_back_*` cubes, copies of the front emblem turned 180° about the lantern's vertical axis (origin 0,0,0), so the back glows the same.
- **To do:**
  - Drop `blue_lantern.bbmodel` in place of the jar's copy; its texture is unchanged.
  - If `LanternFirstPerson` or the item model rely on the old cube count, check them too.

Tool: `tools/fix_lantern_models.py` re-makes both from the jar's originals.
