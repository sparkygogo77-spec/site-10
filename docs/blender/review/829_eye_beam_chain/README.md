# Pass 829: eye beam chain, corner hunter through every target — WAITING

**Script:** `docs/blender/blender_updates/829_eye_beam_chain.update.py` (Z1 from pass 820, extended)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\eye_beam_chain.blend` (Cam C1 top, press play; 110
frames; also "Cam <take> side", "Cam <take> eyes", "Cam all")
**Files here:** `sheet.png` (one check at tick 30: Cam all left, Cam C2 side right)

J on 820: "Corner hunter and the pattern should continue from there and go through each targer to the last, if it hits
a player it does not continue through them". Z1 is the pick.

**How it works:**
- The twin eye beams, in the B1 look, turn hard right angles (Z1's pattern) to reach the first target.
- They pass straight through it, run 0.8 blocks out the far side, then corner-hunt to the next target, alternating
  x-first and y-first turns, and so on to the last target.
- Each target gets the outline flash you kept (815 F3) and a small knock as the beam passes through.
- If the next target is a **player**, the beam stops inside them, and nothing after them is hit.

| Take | Layout | Hits (tick) |
|---|---|---|
| C1 | four mobs round two pillars; the beam chains through all four | 14, 16, 19, 20 |
| C2 | mob, mob, then a player; the beam stops in the player, and the fourth mob behind is never touched | 14, 16, 19 (player) |
| C3 | five mobs in a loop round a pillar, with B1's soft glow and light along the path | 14, 15, 17, 19, 22 |

The front travels 3 blocks a tick so you can follow it in Blender (the game can go faster). It holds 40 ticks, then
pulls back from the eyes outward.

**For the game:** a chain of straight beam segments. The path is: eyes → 2 blocks out → for each target, a right-angle
turn then straight to it → through it 0.8 blocks → the next. It stops at the first player.

## J's verdict (2026-10-15)

"the lines shouldnt go around corners so predictably ... the one on the right [C1] is the best looking, we need better textures" - pass 833.
