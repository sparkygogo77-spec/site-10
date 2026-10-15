# Green glow interference in game (J, 2026-10-15 ~21:00 UTC)

Screenshot: `2026-10-15-green-glow-interference.png` (same folder). J: "a ton of glowing interference in game".

What the shot shows (Wall mode, 5%, green ring, underground, first person, jar 2.1.667/668):
- a green haze over most of the view: big soft translucent green sheets/volumes across the cave walls, not just around the construct
- a broken construct-brick wall with shards flying out (looks like the pass 815 F1 shatter, commit 3d8dc7ce, `HitFx`)
- many large, bright square glow particles (sparks/motes) drifting around the hand, much bigger and brighter than the rest of the effect
- a translucent green box around the held hand/ring

Suspects to check (mc chat): HitFx shatter bits (`entityTranslucentEmissive` cubes, `ShaderGlow.light(0.8f)`, 0.9 alpha) and its 24 sparks/motes
per hit, piling up on repeated hits (MAX_BITS); construct particle size/brightness under a shader pack; any Wall/held-construct glow
volume. Ask J which shader pack and what he was doing (punching the wall? holding Wall?) if it doesn't reproduce.

## Update (J, second screenshot `2026-10-15-green-glow-interference-2.png`)
- Shader: **Complementary Unbound 5.81, the Lantern Ring patched version**. J: "the glow is bad".
- Bridge mode (6%), overworld at dusk, **"Ring charge: 100%"** on screen, no construct being hit.
- Large flat translucent green panes/triangles fill the lower half of the view right in front of the camera, a green light column
  rises behind the crosshair, and the held arm is washed pale green.
- So it is NOT only the 815 shatter. New top suspects: the ring/charge glass aura (commit 8564b6e5 "Glass aura strands glow softly
  under the patched shader pack", 088ca166 "glass glows from the start") drawing big emissive sheets near the camera at full charge,
  and the patched pack's handling of emissive translucent geometry close to the eye (bloom/light shafts). Check what draws at full
  ring charge in first person under the patched pack.

## Update (J, third screenshot `2026-10-15-green-glow-interference-3.png`, to the 800-899 modeller chat)
- J: **"these light rays from blender are not it"**. Bridge mode 6%, snowy plains at night, lantern in the left hand, ring hand on the right.
- What shows: pale-green light streaks smeared down the ring arm and sleeve, big translucent green squares/panes floating at the
  bottom right near the camera, a bright ring flare with sparks above the crosshair, and a green haze over the ground.
- So the Blender-derived light rays / shafts / glow sheets near the camera are rejected in game as they are (likely the glass
  aura strands and the 305 D2 shafts look). Remove them from first person near the eye; keep the solid, readable beams and
  constructs. Any replacement comes back through a Blender round first.
- J (same chat, right after): **"that glow is also the light coming off from deluge, our light physics are bad"**. So the
  Deluge hold glow is part of it: `DelugeGlare` (soft screen-space glow round the ring in first person) plus the rays and
  sparks `BeamChargeGlow.renderHold` draws on the fist. The light that the effects throw (onto the arm, as haze, as panes)
  is wrong as a whole, not one effect. Replacement ring-glow looks to pick from: pass 860 (G1-G6: nothing on the arm, no
  panes, no shafts, small emissive area).

## What J likes (screenshot `2026-10-15-good-beam-light.png`, red zig-zag eye beam at dusk)
J: "the glow from the omega beams are good they light up properly especially its immediate vicinity whats the difference in that
light and the one that spreads amongst the area slower".
- **Good (the beams):** real block light. `RingPowers.lightBeam` / `lightShot` drop invisible `BEAM_GLOW` light blocks every 3-4
  blocks along the path; they light the blocks right around them (vanilla light falls off one level per block), the patched
  Complementary pack colours that light by corps (voxel coloured lighting), and they fade out quickly. It lights surfaces, not the air.
- **Bad (the slow spreading glow / haze / arm streaks):** (1) the Deluge liquid is itself a light source (`ModFluids`, level 13
  pool, 10 runoff), so the light creeps across the area as the liquid flows; (2) `ShaderGlow.light(...)` marks the ring, charge,
  particles and held things as emissive, and the pack's bloom (a screen-space blur of bright pixels) smears big halos, worst
  for anything right in front of the eye; (3) `DelugeGlare` draws a soft glow on screen round the ring.
- **Direction:** use the beam method for every effect's light (short-lived invisible light blocks at the source, coloured by the
  pack), and cut the screen-space glow near the camera (no ShaderGlow emission on the first-person hand/ring/close particles,
  drop DelugeGlare). Ring look in first person: pick from pass 860.
