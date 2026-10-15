# Pass 831: worn ring round 3 (jar ring placement, fist turned for the rise, new glow effects) — WAITING

**Script:** `docs/blender/blender_updates/831_worn_ring3.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\worn_ring3.blend` (Cam W5b rise, fist back 75 - first person; press play, 120 frames)
**Files here:** `sheet.png` (one check: each take's third-person and first-person camera; W2 at tick 90, W5 at tick 70)

J on 818: "W4b Rise 135 deg is good, how do i choose my fov so i can find the angle that looks best, i think the hand
should be turned more i drew where the ring model should actually be (we have a proper ring placement in the jar files
now), but i want the angle to be able to see the ring on top while flying up so change the angle. the light rays look
bad too and the smoke". KEEP: W4b's 135° rise.

**Ring placement (every take):** as the jar has it (`RingModels.placement`): on the fist's punching face, standing out
of it, 1 skin pixel in from the back of the hand, over the middle finger. Gold frame, green face, band over the back.

**The fist has a wrist now:** the last 4 px of the arm (the fist) bends back. Because the fist is a 4 px cube, bending
it pulls the ring about 0.15 m toward you, so the script places the arm so the *ring* stays at the same spot on screen.

| Take | What | First person at tick 70 |
|---|---|---|
| W2d halo | one soft camera-facing glow sprite on the ring, breathing every 2 s (in game: 1 billboard) | ring lower right |
| W2e pixel motes | square green motes drift up off the ring and shrink out, 1 per 3 ticks (enchant-particle style) | |
| W2f orbit motes | three motes circle the fist on tilted orbits, each with a 3-step fading trail | |
| W5a rise, fist back 45 | W4b + back of the hand up, fist bent back 45° | ring shows over the top of the fist (face at 97° to the eye) |
| W5b rise, fist back 75 | the same, 75° | ring face at 77° to the eye |
| W5c rise, fist back 105 | the same, 105° | ring face turned to you (53°) |

W2 keeps the construct texture forming up the arm (ticks 10–70). W5 keeps W4b's pull streaks. Ring glow is lower than
818 (0.9 → 1.5) because the check read mint at 2.2.

**FOV:** Scene properties > Custom Properties > **MC FOV** (default 70, Minecraft's default; the jar draws the hand at
a fixed 70°). It drives every first-person camera, which are set to Sensor Fit Vertical like Minecraft. Change it and
scrub to find the angle you like; tell me the number and I'll use it everywhere.

## For J

Pick a W2 effect (W2d / W2e / W2f) and a fist bend (W5a / W5b / W5c), and the MC FOV you liked.
