# Hand-off: eight ring lasers to test in game (Blender pass 836, 2026-10-15)

J on pass 836 (`LanternLive\combat\laser2.blend`): "H3 N1 N2 N3 P1 C1 C2 C3 are all pretty close", then "put those in
the game to test". He picks in game, so all eight go in as **Ring Lab options** for the Beam, next to today's
HelixBeams, with the Ring Lab's KEEP / IMPROVE / DROP rating. H1, H2, P2 and P3 are not in this list.

Blender reference: `LanternLive\combat\laser2.blend` (Cam <take> close / Cam <take> eye).
Script: `docs/blender/blender_updates/836_laser2.update.py`. Textures: `textures/` here, made by
`tools/laser_textures.py`.

## Suggested setting

`LabSettings.BeamLook { HELIX (today), H3_BRAID, N1_NEEDLE, N2_LAYERED, N3_CRACKLE, P1_PULSES, C1_WEAVE, C2_BRICK,
C3_HEX_TUBE }`, default HELIX, shown in Ring Lab > Beam with the usual rating buttons. Only the look changes: range,
damage, charge and the hit explosion stay as they are.

## How every new look is drawn (shared)

- **Pieces, all straight along the line from the ring to the hit:** a core ribbon, a glow ribbon, a haze ribbon (each
  one quad strip turned to the camera, like a beacon beam's sprite but facing you), a flare sprite at the ring and one at
  the hit. Sizes below are full widths in blocks.
- **Textures** (`textures/`): u runs across the ribbon, v along it at 32 px a block; each tiles in v. They are white/grey
  (RGB = alpha = intensity): tint with the corps colour per vertex (green (8, 255, 56); CorpsTint for the rest), so the
  glow stays saturated, never white.
- **Render type:** additive, as BeamChargeGlow does: `RenderTypes.energySwirl(tex, 0, vOffset)` with
  `vOffset = -flow × ageInTicks / tileBlocks` (that is the scrolling toward the target); under a shader pack
  `entityTranslucentEmissive(tex)` with the same UVs shifted by hand. Full bright.
- **Start:** the ring on the punching face (the jar's RingModels placement); the beam starts 0.02 blocks off it.
- **Timeline:** full length in 2 ticks (it grows from the ring to the hit); a tap holds 4 ticks, a charged shot holds
  while it lasts; then every width shrinks to 5% over 4 ticks and it is gone. (Today: 3 up, 2 held, 3 down.)
- **Core flicker:** core width × (1 + wobble × sin(2.3 × age)), per tick.
- **Flares** (`laser_flare.png`, one camera-facing sprite each): 0.42 wide at the ring from the first tick, 0.9 wide at
  the hit from tick 2, both × (0.85 + 0.15 × sin(1.9 × age)), gone with the beam.
- **Tile lengths** (blocks per texture repeat, also in `textures/tile_blocks.json`): streak 9, needle 25, layer inner 9,
  layer outer 6, crackle 3, pulse 1; the construct ones are 1 block a frame-tile (see C1).

## The eight looks

| Look | Core (texture, width, wobble) | Glow (texture, width, flow b/t) | Haze width | Extra |
|---|---|---|---|---|
| **H3 braid** | laser_core, 0.04, 0.15 | laser_glow_streak, 0.26, 0.6 | 0.75 | three strands (below) |
| **N1 needle** | laser_core, 0.036, 0.15 | laser_glow_needle, 0.24, 1.4 | 0.5 | |
| **N2 layered** | laser_core, 0.064, 0.15 | laser_glow_layer_inner, 0.30, 1.3 **and** laser_glow_layer_outer, 0.75, 0.35 | 0.75 | the two glows slide at different speeds (depth) |
| **N3 crackle** | laser_core, 0.064, **0.4** | laser_glow_crackle, 0.42, 1.0 | 0.75 | |
| **P1 rapid pulses** | laser_core, 0.064, 0.15 | laser_glow_pulse, 0.42, 2.0 | 0.75 | sparks at the hit (below) |
| **C1 weave** | laser_core, 0.064, 0.15 | laser_glow_weave, 0.55, 0.6 | 0.75 | animated construct texture (below) |
| **C2 brick** | laser_core, 0.064, 0.15 | laser_glow_brick, 0.55, 0.6 | 0.75 | animated construct texture |
| **C3 hex tube** | laser_core, 0.064, 0.15 | laser_glow_streak, 0.5, 0.6 | 0.75 | a see-through tube (below) |

The haze is `laser_haze.png` in every look, not scrolled.

- **H3 strands:** three strands round the axis at radius 0.07, 120° apart, winding 4.5 rad a block (a tight braid),
  the whole braid spinning 0.25 rad a tick. The radius opens from 0 at the ring to full over the first 1.5 blocks (as
  HelixBeams' EMERGE). Each strand is a camera-facing ribbon 0.032 wide (`laser_strand.png`) plus one 0.07 wide
  (`laser_strand_sheath.png`), drawn in short pieces (0.08-0.12 blocks, like HelixBeams' STEP). It grows with the beam.
- **P1 sparks:** at the hit, 4 small green sparks every 2 ticks while it holds; each flies back and up
  (about 0.08 blocks a tick), falls (0.004 × t²) and shrinks out over 12 ticks. ModParticles' construct spark is fine.
- **C1 / C2 animated texture:** `laser_glow_weave.png` / `laser_glow_brick.png` are 24 frames of 32 × 32 (each frame is
  2 tiles of the construct strip = 1 block), frametime 4 like the blocks. They are plain textures, so pick the frame by
  hand: frame k = (age / 4) mod 24, v range [k / 24, (k + 1) / 24], then scroll inside the frame with the flow.
  (Or put them on the block atlas with their .mcmeta.)
- **C3 tube:** a 6-8 sided tube of radius 0.1 round the core, like a HelixBeams tube but straight, wearing
  `laser_tube_hex.png` (24 frames, as C1) wrapped twice round, scrolling 0.6 b/t, about half see-through
  (the texture's alpha already is). Glow outside it as in the table.

## Checks for the mc chat

- Look at each one in the Ring Lab at 5, 20 and 48 blocks: the core should stay a solid line far off (keep a 1-2 px
  minimum width, as OmegaFx does with CORE_PX) and the glow should never turn white.
- J tests on Lunar Client (Sodium) and with shader packs: both paths need to work.
