# Nebula lantern, lean redo (Blender pass 400)

J (2026-10-14 02:50): "Nebula needs to be redone in blender with different more efficient textures."

**Size.** Each take below costs about 0.45-0.64 MB for all six corps. The Nebula on main costs
about 6.9 MB:

| Part on main | Size |
|---|---|
| 512x512 glass frames | 3.9 MB |
| block strips | 2.4 MB |
| block models | 0.6 MB |

## How it got small

| What changed | Before | Now |
|---|---|---|
| Glass shape | 10 stepped boxes, each face painted uniquely | 21 thin panels: a rounder column |
| Light shape | 20 panels | 24 panels, with the same breathing glow copies |
| Glass frame | 512x512, 4 texels per model px | 126x18, 2 texels per model px |
| Light frame | 256x256 | 96x18 |
| Frames | 24 glass at 3 ticks + 32 light at 2 ticks | 32 + 32, at frametime 4 (6.4 s loop, interpolated) |
| PNG format | RGBA | 64-colour palette |

**Why no seams and no jump.** Each take's pattern is periodic round the column and loops in time.

**Corps colours.** Each corps is painted with its own five-stop palette, not a hue shift.

**Texture layout.** The panels sit in Minecraft box-UV slots, because BbModel reads `uv_offset` only. Each
panel's outer face is followed by its inner face, mirrored. Per-face UVs in the bbmodel match the
slots, so `tools/bbmodel_json.py` builds the placed block from the same files.

## Takes (J picks one)

| Take | Look | Size, 6 corps |
|---|---|---|
| **N1 Smoke & ice** | Today's Nebula, lean: slow smoke rising, pale ice veins, a few far stars | 639 KB |
| **N2 Spiral arms** | Two galaxy arms winding round the glass and gliding sideways, with dust lanes | 595 KB |
| **N3 Aurora** | Soft upright veils swaying round the glass, brightest at the middle band | 600 KB |
| **N4 Deep stars** | Dark gas, with two layers of pixel stars rising at different speeds | 443 KB |

Every take keeps the shared rules:
- dark glass with the light glowing through it;
- the ends fade to near-black;
- the pattern glides in one direction;
- it is never static and never fast.

**Where to look:**
- `renders/takes.png`: all four takes side by side;
- `renders/closeups.png`: close-ups of each take;
- `renders/takes.gif`: the takes moving;
- `renders/corps_<take>.png`: all six corps for one take.

**In Blender:**
- open `blender/nebula_lean.blend` (textures relative, in `blender/textures/`);
- cameras: "Cam takes", "Cam N1" to "Cam N4", and "Cam corps N1" to "Cam corps N4";
- press Space to play the 32-frame loop.

## Swapping a pick in (game thread)

1. **Copy the files.** Copy `takes/<pick>/assets/lanternring/` over `src/main/resources/assets/lanternring/`. This
   replaces:
   - `bbmodel/nebula_glass.bbmodel` and `bbmodel/nebula_light.bbmodel`;
   - `textures/block/nebula_{glass,light}[_corps].png` and their `.mcmeta` files;
   - `textures/entity/bb/nebula_{glass,light}_f0..f31[_corps].png`.
2. **Delete the stale files.** Delete the old 512 px entity frames that aren't overwritten. `nebula_glass_f24..f31`
   are overwritten, but every corps file from main that the pick doesn't write must go:
   `git status` lists them after the copy.
3. **Update the timing in `LanternFirstPerson`:**
   - set `NEBULA_FRAMES = 32` and `NEBULA_FRAME_TICKS = 4`;
   - set `LIGHT_FRAME_TICKS = 4` (`LIGHT_FRAMES` stays 32).
4. **Regenerate the placed block's models.** Run `python tools/bbmodel_json.py`. The glass and light now come from
   the new bbmodels.
5. **Keep the generators in step.** The old painters in `tools/blockbench_models.py` would overwrite this. Either skip
   `nebula_glass` and `nebula_light` there, or call `tools/nebula_lean.py` instead. That script
   regenerates everything: `python tools/nebula_lean.py OUT` writes all four takes.

**Optional, about another 50% off.** Each frame is shipped twice, once in the block strip and once as an entity
frame. LanternFirstPerson could draw the held lantern from the block strip with a V offset, and the
entity frames could then go.

**Unchanged:**
- the body: `nebula_lantern.bbmodel`, plus 14 KB of textures per corps;
- the six block models, about 95 KB each. They only differ by texture, so one model with tinted
  textures could save about 0.5 MB more, if the jar needs it.

## Checks

| Check | Result |
|---|---|
| Glass frames | 126x18, palette, alpha kept (min 150, mean about 170/255) |
| Light frames | 96x18, opaque |
| Loop seam (frame 31 to 0) | Every time term turns a whole number of times per loop, and the drifting noise is cross-faded one loop apart |
| Round seam | The noise is sampled on a circle in noise space, and the bands use whole-number angular frequencies |

**Block conversion:** checked. `tools/bbmodel_json.py` on take N1 writes `nebula_lantern.json` with
the 21 glass panels as free-angle elements (y = -8.57 degrees and so on, 26.x element rotation) and
matching UVs.

**Not checked in game yet:** how it looks under Complementary. That is J's final check.
