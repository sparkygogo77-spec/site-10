# Pass 864: ring glow in first person, round 2 (WAITING)

**Script:** `docs/blender/blender_updates/864_ring_glow2.update.py` (runs 860's rig, timeline and stage)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\ring_glow2.blend` (starts on Cam G1a - first person, tick 75;
press play, 120 frames)
**Cameras:** `Cam <code> - first person` (120 deg, crosshair) and `Cam <code> - third person` for the 9 takes, plus `Cam all`.
**Frames:** 1-60 charge 0 to 100%, 60-90 hold, 90-120 Bridge used (arm pushes out, tiles form 91-103).

J rated 860 G1 face glow, G2 rim line and G3 orbit pixels IMPROVE with no note, and dropped G4, G5 and G6. These are three
new takes of each, built differently. 860's rules hold: nothing on the arm or sleeve, no panes or shafts near the camera,
a small emissive area, saturated green that is never white.

Two fixes over 860, found in this pass's check render (built and rendered on J's PC):
- **The eye never sees the ring's front.** In first person the camera looks at the face's two back sides (measured:
  direction x+0.78 y+0.62 z+0.03 in the ring's space). Every take now reads on those sides.
- **Saturated, not mint.** 860's emission (up to 2.6) clipped the green toward pale mint; all emission is scaled by 0.6.

| Take | What | Look at |
|---|---|---|
| G1a breathing face | G1's face glow = charge, then at full it breathes slowly (+-15%, every 3 s). Never static. | 60-90 |
| G1b dark core | The face's centre stays dark glass; bright edge lines round it = charge. | 75 |
| G1c fills from the centre | Lit bars grow from the face's middle out to its edges as charge rises, like the lantern's light from the port. | 1-60 |
| G2a two lines meet | Two rim lines trace both ways from the bottom, meeting at the top at 100%; then one bright segment travels slowly round. | 1-60, 64-120 |
| G2b double rim | The outer rim line traces 0-50% charge, a belt round the face's sides 50-100%. | 30-60 |
| G2c dashed rim | Dark-green dashes round the rim light one by one with charge (like the lantern's stitches); at full a slow chase. | 1-60, 62-120 |
| G3a erratic orbit | 4 pixels on uneven orbits (own radius, speed, wobble), within 2 px of the face. One per 25% charge. | 75 |
| G3b trailing pixels | Each pixel pulls a 2-pixel tail of darker green; slower laps than 860 G3. | 75 |
| G3c tilted orbits | 2 pairs of pixels orbit on tilted planes round the ring, like an atom. | 75 |

## For J

Rate on the review site (pass 864). The pick unblocks the primed glow when you hold Shift (handover question 24).
