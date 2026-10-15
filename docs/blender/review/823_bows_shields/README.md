# Pass 823: modern construct bows and arrows, and a bigger shield — WAITING

**Script:** `docs/blender/blender_updates/823_bows_shields.update.py` (replaces 808's bow and shield)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\bows_shields.blend` (Cam B1 close, press play; 64 frames;
each bow also has "Cam <take>" and "Cam <take> target"; each shield has "Cam <take>" and "Cam <take> back")
**Files here:** `sheet.png` (check: B1 at brace (18) and full draw (36), B2 and B3 at full draw, H1 at the block, B1's
arrow in the target. After it, the arrow drop was cut so it hits the face of the target, not below it.),
`bows_poses.json` (solver error per key)

J on 808: "the shield is too small and the bow and arrow is broken and out of place it needs to shoot like an actual
bow we will just make VERY in depth bow and arrow models, think modern day bow and arrows", and "there is also already
a spear in the game we should just use that new one, scrap the rest of construct weapons". The spear, whip, chain and
gauntlet are scrapped.

## The shot (a right-handed archer, ring on the draw hand; 20 ticks a second)

| Ticks | What happens |
|---|---|
| 1–14 | the bow forms in the left hand from the ring's pixels; the arrow forms on the string |
| 14–18 | side-on stance, left shoulder to the target, head turned to it; the bow arm comes up straight |
| 18–32 | the right hand draws the string straight back to the anchor under the jaw, elbow up behind (placed exactly by the solver); the string makes a V to the nock; the limbs flex in |
| 32–42 | hold and aim |
| 42 | release: the string snaps forward and shivers (5 ticks); the arrow leaves at 5 blocks a tick, flies nearly flat and sticks in a target 18 blocks out; the draw hand follows through back along the jaw |
| 42–60 | follow-through, then the bow comes down |

## Bows

| Take | Build |
|---|---|
| B1 compound | machined riser (front and back rails with a braced truss), limb pockets, split limbs swept back, two cams with modules, string and two cables to a cable guard, 3-pin sight in a housing, whisker-biscuit rest, front stabiliser with 3 weights, peep sight on the string; carbon arrow with a wrap, three vanes, nock, insert and field point |
| B2 Olympic recurve | long riser with a window, plunger, clicker, sight on a 0.3 m extension bar with an aperture, a 0.7 m long rod plus a V-bar with two weighted side rods, four-segment limbs that curve forward and recurve at the tips; target arrow with slightly helical spin vanes |
| B3 hunting compound | shorter riser and limbs, 5-pin sight, short stabiliser, bow quiver with four broadhead arrows, wrist sling; arrow with a three-blade broadhead |

## Shields (bigger)

Each forms on the ring forearm (ticks 2–8) and is held up in guard. A shot breaks on it at tick 30, and the arm gives a
little.

| Take | Shape |
|---|---|
| H1 big hex | 1.2 blocks across, about twice 808's |
| H2 tower | 0.9 × 1.6 blocks with a rim, a glowing spine and a viewport; covers the body |
| H3 dome wall | a curved hex-cell wall, 1.2 × 1.6 blocks, held out in front |

**For J:** KEEP / IMPROVE / DROP per bow and shield.
