# Green Deluge: brighter liquid (lead Blender chat to coordinator)

J, 2026-10-13, testing jar 2.1.612 under shaders: "green deluge also isnt bright enough at all", and earlier
"the water looks like it may ripple too much".

## Why it's dim
`LanternRingClient` draws `ModFluids.SOURCE/FLOWING` with vanilla `water_still/flow/overlay` tinted
`0xFF2EE866`. Water's textures are dark blue-grey and see-through, so the tint lands dark, and
`ShaderPackIds` gives the liquid the pack's water ID, so Complementary shades it as dark reflective water.

## The fix
1. Textures (done, art side): `tools/hardlight_liquid_textures.py <assets> W1|W2|W3` writes
   `textures/block/hardlight_still.png` (16 px) and `hardlight_flow.png` (32 px), 32 frames each, with mcmeta.
   Near-white, more opaque, ripples at half vanilla's strength. Takes: W1 calm glow, W2 light lines (default),
   W3 solid light. Preview: `docs/screenshots/deluge_green_W.png`. Use whichever J picks.
2. Register them in place of vanilla water (still, flow, and still again as the overlay), tint unchanged.
3. Brightness in code (needs you):
   - liquid light level 15 for sources (13 today), 12 for flowing;
   - under Iris, give the liquid a glowing ID instead of water (as the Red Deluge got ID 32003 via
     ShaderPackPatcher), so the pack lights it as emissive and doesn't darken it like deep water.
     Keep the water physics; only the look changes.
4. Check in game against J's screenshots (level 2 and 3 pools on grass, Complementary + sunset fog).
