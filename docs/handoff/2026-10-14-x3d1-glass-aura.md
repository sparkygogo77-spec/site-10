# X3D1 glass aura + lighter falling constructs (lead Blender chat to coordinator)

J, 2026-10-14, on the falling Anvil in game: the X3 power aura "is good, needs more detail and maybe less stressful on
the game; we need the code to treat it like glass so it doesn't need to be so dense". He picked **X3D1 glass aura**.
He also said the W1 neon wave "looks fine" and the bright-edged box look in his last screenshot "looks good too".

## Texture (done)
`textures/block/construct_ripples_green_x3d1_emerald.png` (+ mcmeta): 256 px strip, 32 frames, frametime 5, made by
`tools/construct_designs10.py`. X3's strands plus hair-thin wisps and sparks. Every pixel is either alpha 0 (clear)
or 255 (solid). Add it as `ConstructLook.X3D1_EMERALD` ("green_x3d1_emerald") next to X3.

## Code (needs you)
1. **Draw it cutout, like glass**: alpha test instead of blending for this look (and solid under a shader pack, as now).
   No sorting, no stacked haze, cheap.
2. **Only the outer shell of a moving construct**: ConstructDisplays already skips faces between touching boxes; the
   turned drill pieces still use the block model with every face. For those, either draw them through
   ConstructDisplays too or merge them into fewer boxes. J's screenshot showed 11.6 of 14.8 GB in use with a big drop.
3. Picture: `docs/screenshots/x3_detail_takes.png` (top: one face; bottom: 12 faces behind each other).
