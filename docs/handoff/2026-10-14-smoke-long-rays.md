# Pass 304: smoke long rays, refined (super jump / smoke chat, 2026-10-14)

J picked "long rays" from pass 94 (`construct_smoke_rays2.blend`): every side of a construct glows, the glow fades
out over 4 blocks, and light beams leave every side. Pass 304 refines that.

- **File to open:** `LanternLive\smoke_long_rays.blend` (scene "Smoke Long Rays"), built by
  `docs/blender/blender_updates/304_smoke_long_rays.update.py`. Needs `LanternLive\texture_library\blender_mp4`.
- **Cameras:** `Cam L1` ... `Cam L3y`, plus `Cam all`. Renders: `docs/blender/renders/304_rays_<take>.png`
  (Cycles, frame 80). Watch the motion in Rendered view.

| Take | What it is |
|---|---|
| L1 as picked | Pass 94's L1 rebuilt: one wide spot out of each side and the top, 4-block glow. |
| L2 shafts | Each side throws a row of narrow beams (16°) fanned apart instead of one wide cone. Haze is thickest at the wall and thins to a trace by 6 blocks, so beams fade out instead of lighting the whole sky. Glow at half strength so the beams read. |
| L3 streaks | L2, plus the glow itself broken into soft rays fanning out from the wall, drifting slowly (noise on the direction from the wall's centre). |
| L4 breathing | L3 with the light breathing every 4 s: the glow reach swings 3 to 5 blocks and the strength ±30%. |
| L3c / L3y | L3 in H1 crimson and H1 yellow. |

All takes keep S1 wisps (smoke streaming up off the top).

## For the game (when J picks)

Not briefed to the coordinator yet: waiting on J's pick. In game the parts map to:
- face glow = block light on every face (shader packs make rays from light sources);
- the 4-block fading glow = a translucent emissive shell or particles whose alpha falls off with distance;
- the beams = thin additive quads (cutout under Iris, see the shader-safe glow rule) out of each face;
- streaks = the same quads with slow per-ray alpha noise; breathing = a 4 s sine on alpha and length.

## Pass 305: more detail (J: build as detailed as the Cowork chats)

- **File to open:** `smoke_rays_detail.blend` (scene "Smoke Rays Detail"), from
  `docs/blender/blender_updates/305_smoke_rays_detail.update.py`. Also in project files under `blender/smoke-rays/` with
  its `texture_library`. Renders: `docs/blender/renders/305_detail_<take>.png`.
- Every take adds a block-grid ground (16 px per block, a darker seam pixel per block), a plain 1.8-block figure for scale,
  and dust motes drifting in the light. Face lights are stronger, so the ground round the construct is lit.

| Take | What it is |
|---|---|
| D1 streaks+ | L3 streaks with the detail. |
| D2 shafts+ | L2 shafts with the detail. |
| D3 pixel smoke | L3 with Minecraft-style pixel smoke puffs rising off the top in place of soft wisps; the puffs carry the corps light and lose it over 4 blocks. |
| D3c | D3 in H1 crimson. |

In game: motes and pixel puffs map straight onto particles (the library's `particle_<tex>_<colour>_mote.png`).
