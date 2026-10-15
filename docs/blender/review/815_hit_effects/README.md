# Pass 815: hit effects — F1, F3 KEEP; F2, F4 waiting

**Script:** `docs/blender/blender_updates/815_hit_effects.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\hit_effects.blend` (Cam F4, press play; 60 frames)
**Files here:** `sheet.png` (check render, tick 24. After it the ground ring was thinned so it stays a line, the air
ripple dropped to 22% opaque, and the overview camera was widened.)

A step-punch (wind up from tick 14, the hit at tick 20) with each effect on its own, then all three together.

| Take | Effect | Numbers |
|---|---|---|
| F1 | construct shatter | a 64-pixel construct wall breaks from the hit point outward; each pixel goes 3 ticks per block of distance later, flies out (nearer ones faster, 0.22/(0.6+d) blocks a tick), tumbles, falls (gravity 0.01/tick²) and shrinks out over 16 ticks |
| F2 | knockback shockwave | a ground ring to radius 4 in 10 ticks plus an air ripple shell in 6; the mob is thrown out 0.8 and up 0.5 blocks a tick, then vanilla gravity 0.08 and drag 0.98, and it tumbles while airborne |
| F3 | outline flash | a construct-green shell round every part of the mob: on for 3 ticks, gone by 9; 24 sparks spray off the hit (9 ticks); the mob rocks 12° |
| F4 | all three | the wall shatters, then 2 ticks later the shockwave, knockback, outline and sparks |

**For J:** KEEP / IMPROVE / DROP per effect. In game F1 is particles, F2 is a ring particle plus velocity, and F3 is
an entity outline render (like glowing, but construct green and only 9 ticks).

## J's verdict (2026-10-15)

KEEP, word for word: "the outline flash is good the construct break is good." (F3 outline flash, F1 construct
shatter). F2 knockback shockwave and F4 all three: no word yet.
