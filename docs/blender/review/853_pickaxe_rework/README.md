# Pass 853: Pickaxe rework: 3D pick, block breaking, running crater swing — WAITING

**Script:** `docs/blender/blender_updates/853_pickaxe_rework.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\pickaxe_rework.blend` (scene "Pickaxe Rework", starts on Cam P1a1, press play; frames 1-93, each take ends between 76 and 93)
**Cameras:** "Cam <take>" first person (120 degree view, crosshair, moves with the player) and "Cam <take> side" third person from the right (also follows the player), for each of the 6 takes.

From 844 P1a "Pickaxe: quick mining taps" (IMPROVE). J's words: "make it a more 3d but still thin and denser axe, maybe
new destruction animations given I use physical block drops in my shaders. more variations of the pickaxe since it will be
different now. arm animations too, it should cause particles when i break things that keep things light, and if im running
through and holding the pickaxe i need extensive animations of swingins the pickaxe and about 8 blocks breaking at a time in
small crater domewide swing but it doesnt instantly destroy."

Kept from P1a: the pixel stream from the ring that builds the pick (P takes), the arm with the ring on the punching face,
120 degree first person with a crosshair. New everywhere:
- **Picks with real thickness**, thin and dense, each built a different way: P1a1 lofted diamond-section crescent with a
  glowing core inside the glass; P1a2 laminated plates (glowing core plate between stepped glass plates) with a twisted
  haft; P1a3 chamfered glass shell over a glowing core, straight diamond spikes, spiral-wrapped haft. R1/R2/R3 use them in
  that order. Construct glow is only on the pick.
- **Block breaking:** real 1 m stone and dirt blocks; pixel cracks spread across the faces over a few ticks, a small
  shudder, then each block breaks into a few physical chunks that fall, bounce off the floor and standing blocks, and
  settle like item drops. A light puff of small green construct sparks and a few dust motes; a couple of sparks on each
  strike. Nothing breaks instantly.
- **Running through (R takes):** the player sprints in and keeps a steady pace through a 3-high wall; each swing cracks the
  next 8 blocks of a dome-arch tunnel (3 wide, 2 high, plus a crown block), nearest the strike first. A small review light
  rides with the player so the tunnel reads.

| Take | What | Timing (frames) | Best frame |
|---|---|---|---|
| P1a1 | Faceted crescent pick: three quick taps, each cracks further, the third (bigger) breaks; steps in, mines the next | hits 19, 23, 28, 44, 48, 53; blocks break 30, 55 (6 chunks each); ends 76 | 32 |
| P1a2 | Laminated pick: forehand then backhand diagonal; cracks creep between strikes, the backhand breaks it | hits 21, 29, 47, 55; blocks break 32, 58; ends 78 | 34 |
| P1a3 | Shell-and-core pick: heavy wind-up strike bites in, crack spreads over 5 ticks, a wrist pry bursts it | hits 25, 52; blocks break 31, 58; ends 80 | 33 |
| R1 | Running overhead chops every 9 ticks (crescent pick); cracks spread out from the strike, break 5 ticks later | 7 swings, hits 19-73; 56 blocks; ends 93 | 55 |
| R2 | Running figure-eight, alternating diagonals every 7 ticks (laminated pick); cracks run along the swing, 4 ticks | 9 swings, hits 18-74; 72 blocks; ends 93 | 53 |
| R3 | Running dome arcs, high right over to low left every 10 ticks (shell pick); cracks follow the arc, 6 ticks | 6 swings, hits 20-70; 48 blocks; ends 90 | 60 |

**For J:** KEEP / IMPROVE / DROP for each take.
