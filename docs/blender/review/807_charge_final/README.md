# Pass 807: the finished lantern charge look, three ways — WAITING

**Script:** `docs/blender/blender_updates/807_charge_final.update.py` (built on the approved G3b, pass 71)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\lanterns\charge_final.blend` (Cam L1 close; set the viewport to
Rendered to see the glow; 680 frames at 24 fps)
**Files here:** `sheet.png` (check render, Cam row, frame 330, near full. The row camera was widened after it.)

J: "the glow from the lantern charge should be much better by now". All three keep the G3b rules: the ring docks into
the port, 12 s to full, a 2 s overcharge climax, hold, a slow 7.5 s fade. The gold cracks flash, then settle dim until
the green swallows them. The dark stitch seams, the gold frame catching the light and the 3° helix also stay. Only the
way the light fills the glass changes:

| Take | How the light fills |
|---|---|
| L1 port spread | the front starts at the port and keeps spreading out from it as the charge grows (front = (0.25·touch + 0.75·charge) × 26 px), brightest along that front, so you can see the ring feeding it |
| L2 band climb | the glass fills from the bottom up like a rising level (level = 3 px + charge × 78% of the height), brightest just under the surface line; the overcharge tips it over the top |
| L3 core swirl | the strands winding round the core are 3× as strong and spin twice as fast; the heart flares more |

The stream into the ring is now saturated green, (0.2, 1.0, 0.35); it was (0.35, 1.0, 0.5).

**For J:** pick one take for the game's lantern shader / particle timing, or say which parts to mix (for example L2's
level with L3's swirl).

## J's verdict (2026-10-15)

KEEP, word for word: "L3 Core swirl wins this one".
