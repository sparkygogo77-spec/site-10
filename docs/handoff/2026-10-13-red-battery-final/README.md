# Final hand-off from the Blender thread: the Red corps (rage) battery (2026-10-13)

This is the last hand-off from this Blender chat, which retires now. The new Blender lead chat owns everything
else. Branch: `claude/lantern-redesign-pass2`.

## 1. The model (`bbmodel/`, `textures/entity/bb/`)

These are drop-in files for the jar, in the same format as the other lanterns: box UV, and cubes named `glow_*`
render full-bright.

**`red_battery.bbmodel` + `red_battery.png`**
- The battery is about 3.4 blocks tall in model pixels, so scale it in the renderer as the Dark Lantern is.
- It is J's B2 build, plus:
  - **Handle:** C1, the arched rune handle.
  - **Stone:** one smooth, glossy crimson, sRGB (188, 30, 47), the centre colour of the crimson diamond block.
  - **Glow cubes:**
    - `glow_port`: the hole behind the cover, plus the light ring round it. This is the charge light.
    - `glow_rune`: runes, and the raised claw mark on the cap and both side drums.
    - `glow_vein`: molten cracks.
    - `glow_blood`: the blood channels and basin.
    - `glow_glass`.
    - `glow_bright`.
- 2,449 boxes and 2.9 MB, about the same as `dark_lantern.bbmodel`. Check the jar budget.

**`red_battery_cover.bbmodel`**
- The stone cover over the port, as its own model, so the game can dissolve it.

**Handle note:** J never picked a handle. The lead chat said to finish the battery, so I went with C1. To swap it,
re-run `python tools/pixel_rage_battery_bbmodel.py OUTDIR c2` (ring handle) or `c3` (horns).

## 2. Behaviour J approved in Blender (`rage_battery_c.blend`)

- **At rest:** dripping blood, as long thin pixel streaks running down from under the port and the channels.
- **Flying:** the streaks lift and trail back and up.
- **Charge (a full 8 s):**
  - The cover disintegrates pixel by pixel into red construct particles, and its own light goes out.
  - The hole is pure light: no mark shows in it.
  - The light builds smoothly through the hole (`glow_port`, brightness about charge²).
  - Red pixel lightning crackles round the port, more as the charge rises.
  - Light rays come out of the front.
- **After the charge:** the light fades over about 2 s and the cover re-forms.
- **Heartbeat:** a slow double beat every 2 s on the runes, veins and blood glow.

## 3. Reflect like a diamond block under shaders

See `docs/handoff/2026-10-13-red-battery-diamond-reflect.md`.
- Add the battery (and the Lava Font) to `ShaderPackIds.lookLike` as `Blocks.DIAMOND_BLOCK`, state by state.
  Skip the glowing states, so they keep their light ID.
- Give the held item diamond_block's item ID.
- If the battery is drawn as a BbModel, use a LabPBR `red_battery_s.png` instead: smoothness about 0.9, F0 about
  0.04.

## 4. Barrier surface

See `docs/handoff/2026-10-13-barrier-surfaces/`.
- J's picks: T1, T2, T3, T5, T6, T7 and T9.
- They are 8 s seamless strips, at most 99% opaque.
- Make them Ring Lab options for the particle barrier surface, outer shell only, with construct pixels drifting on
  the outside faces.

## Not sent before, to be confirmed

My last two messages to the coordinator chat didn't show up there, so I can't confirm they arrived:
- the barrier surfaces;
- the battery shader ID.

This folder and those two brief files are the complete record.

## Files

- **Blender:** update 100 (`docs/blender/blender_updates/100_red_battery_final.update.py`) loads these exact models
  into `LanternLive\red_battery_final.blend`.
- **Tools:**
  - `tools/pixel_rage_battery*.py` builds the voxel model.
  - `tools/pixel_rage_battery_bbmodel.py` exports it.
  - `tools/construct_designs9.py` makes the barrier strips.
  - `tools/blender_edits/` holds the Blender edits.
