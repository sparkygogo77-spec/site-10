# Pass 814: ring-hand gestures — OLD (redone as 816)

**Script:** `docs/blender/blender_updates/814_ring_gestures.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\ring_gestures.blend` (Cam X1, press play; 70 frames)
**Files here:** `sheet.png` (check render, tick 24: X2's column of light, X3's hand at the brow with the eyes lit, X4's
burst. The overview camera was widened after it.), `gestures_poses.json` (per-tick keys for third and first person)

The rig is blocky with knees and elbows. The ring is on the right hand and the neck stays within 57°. Each gesture has
a third-person camera ("Cam <take>") and a first-person camera ("Cam <take> first person").

| Take | Gesture | Beats (tick) |
|---|---|---|
| X1 | point to cast | the arm snaps straight out at 12, the other hand steadies the wrist, the ring flares to 14, a construct bolt leaves it (14–24), held to 34 |
| X2 | fist-raise oath | the fist goes straight up by 18, the head tilts up after it (40°), a column of light rises from the ring (18–26), held to 44 |
| X3 | ring to forehead | the hand comes to the brow by 12, the head bows 34°, the face and eyes light (14–40), a slow breath, the hand drops by 54 |
| X4 | power-up as the ring goes on | the left hand slides the ring on at 14, the arms flex down and out, the knees bend 45°, the ring flares to 16, a light ring bursts out, the body outline flashes (20–31) |

**For J:** KEEP / IMPROVE / DROP per gesture. Possible triggers in game: X1 when firing a power, X2 as an emote or a
charge-complete pose, X3 for the lantern oath, X4 when the ring goes into the ring slot (pairs with 805 W3).

## J's verdict (2026-10-15)

"the X4 ring the camera names need another description or in blender I need a better description of what the model
is for ... these animations were also subpar they dont look well." Redone as pass 816.
