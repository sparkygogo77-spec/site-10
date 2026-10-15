# Pass 830: ring beam round 3 (construct textures, spinning rims, sparks, game glow) — WAITING

**Script:** `docs/blender/blender_updates/830_ring_beam3.update.py`
**Open in Blender:** `ring_beam3.blend` (sent as a file; Cam T5 close, press play; 70 frames)
**Files here:** `sheet.png` (one check: every take's close camera at tick 30)

J on 819: "O4 looks better (different texture is necessary,) O2 might be good if its a real glow in game i cant tell
though, O3 sparks are good too, give me more designs and find a way to apply my construct textures". KEEP noted: O4's
spinning rims, O3's sparks.

**Every take** keeps B1's core and O4's spinning helix rims. The sheath is now a tube wearing one of your construct
textures from the texture library, wrapped round the beam (55% opaque). The texture flows toward the target at 1.5
blocks a tick while its own frames animate.

**The glow (T4, T5):** this is a real glow, drawn the way the game would draw it. It is one flat strip along the beam
that turns to face the camera, bright in the middle and fading at the edges, drawn additively: one quad per beam.

| Take | Design |
|---|---|
| T1 | hex flow + sparks |
| T2 | brick flow + sparks |
| T3 | weave flow, thicker rims |
| T4 | ripple flow + game glow |
| T5 | hex flow + sparks + game glow |
| T6 | double helix (two sets turning opposite ways) + R2 flow + sparks |

**For J:** KEEP / IMPROVE / DROP per take.
