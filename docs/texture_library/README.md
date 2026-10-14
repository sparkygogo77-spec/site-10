# Lantern Ring texture library

This folder holds every construct texture J called good, in all six corps colours, in each format the game and Blender use. It was made on 2026-10-14 by `tools/texture_library.py`; re-run it to rebuild:

```
python tools/texture_library.py <textures/block dir> docs/texture_library --mp4 <mp4 dir>
```

J's notes on each texture:

| Texture | J's note |
|---|---|
| BR1 bricks | KEEP: "the most construct like" |
| W1 neon weave | good |
| H1 hex | "the hex that should be for all colours", made from H1 blue |
| R1 magma | good |
| R2 bloodfire | good |
| V1 crystal | good |
| X3D1 glass aura | J's pick in the lead Blender chat: drawn cutout, like glass |

**Colours:** `green`, `blue`, `crimson` (Red), `yellow`, `violet`, `orange`.

Where a texture already existed in a colour, that strip is used as it is:
- BR1 emerald (green);
- W1 neon (green);
- X3D1 (green);
- H1 blue (blue);
- R1 and R2 (crimson);
- V1 (violet);
- BR1 blue (blue): BR1 jade in dark blue, J's call.

Every other colour is the original's brightness run through that colour's ramp. The ramps are in `index.json`.

## Files: `<colour>/<texture>/`

| File | What it is |
|---|---|
| `construct_<tex>_<colour>.png` + `.mcmeta` | Game strip at its own size (128 px wide = 32 px a block; 256 = 64) |
| `construct_<tex>_<colour>_32px.png` + `.mcmeta` | 32 px a block (only when the strip is bigger) |
| `barrier_<tex>_<colour>.png` + `.mcmeta` | Landing barrier / shell: the light stays solid, the rest at 40% alpha |
| `particle_<tex>_<colour>_pane.png` | 16 px square of the texture with a bright rim, for construct pieces |
| `particle_<tex>_<colour>_shard.png` | 8 px triangle chip, for crumbling and breaking |
| `particle_<tex>_<colour>_mote.png` | 8 px soft dot, for sparks, the ribbon and smoke |
| `blender_<tex>_<colour>.png` | Frame 1, opaque on dark, for Blender |

**Blender movies:** `blender_mp4/blender_<tex>_<colour>.mp4` play each loop as the game does, at 20 fps. They are on J's PC in `Documents\LanternLive\texture_library\blender_mp4` and are not kept in the repo.

**Crimson diamond block:** `crimson/diamond/` holds the Red battery's C1 cut-gem tile as a block, made by `tools/crimson_diamond_block.py`:
- `diamond_crimson.png`: 32 px;
- `_16px`: one tile;
- `_s`: a LabPBR specular map, so it shines like a gem under shader packs.

`sheet_all.png` shows frame 1 of every texture in every colour.
