# Flight ram barrier, model takes (Blender pass 410)

The ram barrier is the shell in front of a flyer that smashes through blocks. These are four
models for `RamBarrierFx`'s model hook. J picks one.

All four drop in with no code change: the hook already loads `bbmodel/ram_barrier.bbmodel` with
`forCorps` textures. They follow the hook's spec:
- origin at the flyer's middle;
- facing north (-Z);
- radius 4.5 blocks (72 px);
- cap half-angle acos(0.57), about 55 degrees.

Each model is drawn with `renderPackSafe` and the hook's fade. On your own flyer the hook dims it
further (`OWN`), so the "own" renders are brighter than you'll see in game.

## Takes

| Take | Look | Boxes | Size, 6 corps |
|---|---|---|---|
| **R1 Glass shell** | A faint see-through cap with a bright rim and dark seams: the classic force field | 385 | 120 KB |
| **R2 Lattice** | Spokes and a web of glowing struts with clear gaps: a ram built as a construct | 321 | 112 KB |
| **R3 Particle field** | Hundreds of motes over a barely-there shell: J's "pixels living on the surface" idea | 997 | 232 KB |
| **R4 Pressure rings** | Concentric shock rings with a hot spark at the tip: reads as speed and impact | 457 | 132 KB |

**How they're built:**
- All four are axis-aligned voxels: 4 px cells, thin tiles 1 px deep, and no rotated cubes. The game
  draws exactly what Blender shows.
- Cube names pick the draw path: `glass_*` is see-through, `glow_*` glows.
- Colours come from one small 128x64 swatch texture per corps, using each corps' own five-stop
  palette, with no hue shift.

## Where to look

- `renders/takes.png`: all four takes, each in side, front and the flyer's own view.
- `renders/<take>_{side,front,own}.png`: the full-size views.
- `blender/ram_barrier.blend` (textures relative, in `blender/textures/`). Its cameras are
  "Cam R1 side/front/own" to "Cam R4 side/front/own". Each take is 200 m apart so they don't show
  through each other.

## Swapping a pick in (game thread)

1. Copy `takes/<pick>/assets/lanternring/` over `src/main/resources/assets/lanternring/`. That
   adds `bbmodel/ram_barrier.bbmodel` and `textures/entity/bb/ram_barrier[_blue|_red|_yellow|_violet|_orange].png`.
2. That's all. The particle placeholder in `RamBarrierFx` steps aside once the model exists.

To regenerate: `python tools/ram_barrier_takes.py OUT`. Set `FACES=1` to add per-face UVs for
Blockbench or Blender; the game reads box UV only. The Blender scene is
`tools/blender_edits/ram_barrier_scene.py`.

**Not checked in game yet:** how it looks under Complementary at flight speed.
