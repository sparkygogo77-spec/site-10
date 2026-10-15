# Pass 805: the worn ring, first and third person — WAITING

**Script:** `docs/blender/blender_updates/805_worn_ring.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\worn_ring.blend` (Cam W3 third person, press play; 80 frames)
**Files here:** `sheet.png` (check render: W3 at frame 27, outline flash and light ring. The camera was pulled back
after this render.)

J: "the ring should stay on when wearing it, make a ring slot in the inventory for your right hand". The ring is on
the right hand in every shot. Each take has a first-person camera (the arm in view) and a third-person camera.

| Take | What happens | Timing (20 ticks a second) |
|---|---|---|
| W1 idle | steady glow, a small shimmer (emission 5 ± 0.4), the arms sway | loops every 80 ticks |
| W2 charge pulse | the ring rises to 9, then a band of light runs hand → elbow → shoulder → chest, and the eyes light | ticks 13–30, twice per 80 |
| W3 equip power-up | the ring forms on the finger pixel by pixel (ticks 10–22), flashes to 14, a light ring rushes out from the hand, fist up, the body outline flashes | flash at 22, outline 25–33 |

Glow is saturated green throughout (the construct rim's emission was cut from 6.5 to 3.8 so the bloom stays green, not
white). This pass also sets a lower rim and glow for every later pass from 805 on.

**For J:** KEEP / IMPROVE / DROP per take. For the mc chat: W1 is the always-on look, W2 fits "ring charged / power
ready", and W3 fits the moment the ring goes into the new ring slot.
