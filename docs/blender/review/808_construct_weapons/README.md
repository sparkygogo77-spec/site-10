# Pass 808: construct weapons — WAITING

**Script:** `docs/blender/blender_updates/808_construct_weapons.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\construct_weapons.blend` (Cam K1, press play; 80 frames)
**Files here:** `sheet.png` (check render, tick 44: K3's overhand before the throw and K4's whip lash. The overview camera
was widened after it to fit all six.), `weapons_poses.json` (forming and hit ticks)

Every weapon forms pixel by pixel from the ring in ticks 1–20, grip first and tip last, with pixels streaming out of
the ring to each piece. Then it does its job against a dummy 6 blocks ahead, and the dummy rocks on each hit. The glass
is 62% opaque and the glow is saturated green.

| Take | Weapon | Action | Hit tick |
|---|---|---|---|
| K1 | bow (13-piece arc, glowing string) | forms in the left hand; the arrow forms at the ring; draw to the cheek, hold, loose; the string snaps back; the arrow sticks in the dummy | 48 |
| K2 | hex shield (37 tiles, rim, boss) | forms on the ring forearm; guard up; an incoming shot hits it and breaks into pixels; the shield glass flashes and the arm gives a little | 43 |
| K3 | spear (1.8 blocks, banded shaft, edged head) | draw back, step-thrust; then overhand throw, and it flies and sticks | 36, 58 |
| K4 | whip (16 links) | wound back over the shoulder, lashed forward; the wave runs out to the tip and cracks at the dummy | 44 |
| K5 | chain (12 links, alternating) | swung round overhead twice, thrown out, wraps the dummy, pulled back in | 52 |
| K6 | gauntlet (a fist 2.2× the hand, knuckle rims, banded cuff) | grows over the hand; wind up, step-punch; a shock ring at the hit | 32 |

**For J:** KEEP / IMPROVE / DROP per weapon. The kept ones go to the mc chat with their hit ticks, and as first-person
versions in the 803 style (edge leading) if you want them.
