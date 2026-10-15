# Pass 833: eye beam chain round 2 — WAITING

**Script:** `docs/blender/blender_updates/833_eye_beam_chain2.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\eye_beam_chain2.blend` (Cam E1 top; press play)

J on 829: "the lines shouldnt go around corners so predictably either otherwise the one on the right is the best looking, we need better textures for the omega beams i dont think i saw them much in game last time". C1 (chain through four) is the base for every take.

**Corners:** the hunter picks its own route to each target: 1-4 turns at random split points, mixing 90 and 45 degree
turns, never through a pillar. Both eyes take the same route side by side. Through every target to the last; stops in
a player (as 829).

**Seeing them:** in game today the eye beam core is 0.04 blocks across (OmegaFx `CORE = 0.02` half width), which is
why they were hard to see. These use the laser kit from 834: a solid core 0.06 across, one glow quad turned to the
camera (0.32 wide) with a pattern flowing along it, and a faint haze (0.5 wide), in the corps colour.

| Take | Route | Glow |
|---|---|---|
| E1 loose hunt | random 90/45 turns | streak (noise drawn out along the beam) |
| E2 staircase | runs of 3-5 uneven steps | your hex construct texture flowing |
| E3 swerve | each corner overshoots then cuts back | pulse bands, sparks off every corner |

After the check render the first leg was lowered (at eye height it filled the first-person view) and the haze slimmed.

**For J:** KEEP / IMPROVE / DROP per take.

## J's verdict (2026-10-15)

"E1 and E3 for the eye chain but we made physics for how it should behave before, the lines should be much more erratic and not limited to a certain axis or rotation at all, they also move a little too fast it should move more proportional to how far its target is" - E1 and E3 looks kept; pass 837.
