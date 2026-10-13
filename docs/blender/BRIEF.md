# Blender models brief: Lantern Live (for every thread in the mc project)

The files sit on branch `claude/lantern-redesign-pass2`, in `docs/blender/`.

## The models (`docs/blender/models/`)

| File | What it is | Status |
|---|---|---|
| `dark_lantern_L1.glb` / `dark5_l1.npz` | Dark Lantern (Power Battery), glassy ribs, 5 dashed middle lines | **In game.** J's current pick |
| `dark_lantern_L2.glb` / `dark5_l2.npz` | Same, with deeper ribs (rib_depth 2) | Alternative |
| `blue_lantern.glb` / `blue_lantern.npz` | Blue Lantern: thicker cup, domed lens, no plaque or grate | In game |

- **The .glb files** open anywhere (Blender: File > Import > glTF). They carry per-face colours, 1 unit = 1 block.
- **The .npz files** are the source: `quads` (N×4×3, in model pixels, 16 = 1 block), `col` (N×3 sRGB), `kind`
  (0 matte, 1 metal, 3 fleck, 4 body, 5 vein) and `glow` (per-quad charge weight, 0..1).
- **The generator** is `tools/pixel_dark_lantern4.py`. It builds a 64-pixels-per-block voxel grid:
  - `profile` gives the bulge
  - ribs only off the bulge
  - crazed plates
  - branching gold "lightning" cracks
  - collars, stepped foot, top plate, handle
  - the port with the Green Lantern logo (brackets, open ring, glowing heart)

  `face_colour` and `glow_weight` are shared by the Blender export and the game export.
- **`lantern_live.blend`** is J's scene file. It was saved before the Dark Lantern work, so rebuild that by
  running the updates (below).

## Live link (how Blender gets changes)

- **The add-on.** `lantern_live_link.py` is the Blender add-on. It watches J's folder
  `C:\Users\Josh\Documents\LanternLive` and runs every new `*.update.py` with `bpy`, `np` and `FOLDER`.
  J must re-run it and press Watch after every Blender restart. `live_status.txt` shows the last update applied.
- **The update history** is in `blender_updates/`. Key ones:
  - 18: swing with the game's LanternSway physics (STIFF 0.14, DAMP 0.86, clamp 40)
  - 21–34: Dark Lantern materials, cameras ("Dark Camera", "Detail Camera"), gold metallic 0.8 / roughness 0.28
  - 32: gentle squared glow
  - 33–34: logo close-ups
  - 35: the swirl charge light (not yet applied on J's PC)
- **Materials.** Colour attributes are `col` and `glow`. Everything is driven by `"Lantern Controls"["charge"]`.
  Use EEVEE (not Cycles), Pixel Size 1x.
- **Renders.** Updates write stills to `renders/` in that folder; fetch them to check work without screen access.

## Getting a model into the game

1. `python tools/pixel_dark_bbmodel.py src/main/resources/assets/lanternring l1` writes `bbmodel/dark_lantern`
   (2080 greedy-merged boxes, 512² texture) and `dark_lantern_glow`: 1554 boxes and 12 baked charge frames
   (a ball, a swirl and flares; 2.5 s loop).
2. `python tools/bbmodel_json.py` writes the block model.
3. `LanternFirstPerson` (DARK) cross-fades the glow frames while charging.
4. Recompress the jar's PNGs with oxipng: the jar is **29.9 MiB, right at the 30 MiB limit**. Any new texture
   needs a size cut first.

## J's standing rules for lanterns
- The Dark Lantern is dark green jade at rest, with darker ribbed bands. Both light only when charging.
- Gold flecks glint now and then.
- The glow builds gently, never maxes out fast. Darker pixels stay darker.
- The middle lines are dashed in the darkest green.
- He wants several options every round. He picks between them in Blender renders.

## Open items
- The underhand charge animation: the fist hits the lantern from below, with the lantern held closer.
  This is waiting on J explaining "not turned 90 degrees to the left of me".
- 35_swirl renders: waiting on J restarting the watcher.
