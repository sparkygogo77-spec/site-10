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
