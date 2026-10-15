# Pass 520: first-person versions of the moves (vanilla and bigger)

The catalogue (519) showed that from your eyes the arms never come into view for these moves. J picked all four groups
(flurries, slams, take-off and double jump, sprint and flight) and asked to see both styles.

- Open in Blender: `LanternLive\first_person_moves.blend`, scene "First Person Moves", 151 frames at 20 fps.
- Cameras `NN <move> - vanilla` and `NN <move> - bigger` (start on `01 Flurry F2 - vanilla`, press play).
  - **vanilla**: the arms come in from the lower corners at Minecraft's own first-person size.
  - **bigger**: the same motion, arms 1.3x bigger and a quarter closer.
- The camera rides the eyes of the picked 3rd-person take, with the same timings as in the catalogue, so the view rises,
  dives and flies as in 3rd person.
- A 2-block training dummy stands in for the target in the two flurries.

| NN | Move | 3rd-person take it follows | What the arms do |
|---|---|---|---|
| 01 | Flurry F2 | F2 (507) | guard; left jab at 6, ring cross at 11, ring arm winds across the chest and backfists out to the right at 18 |
| 02 | Flying flurry | A2 (509) | ring fist leads the flight; same jab, cross, backfist at 12/17/24; fist leads again |
| 03 | Big flight slam S3 | S3 H5 (510) | ring fist leads the dive; pull back at 33; fist driven into the ground at 34 with the free hand bracing; strong shake |
| 04 | Primed flight slam P1 | P1 (518) | as 03 at 30; at 70 the ring hand aims at the crater (left click to rebuild) |
| 05 | Primed super-jump slam P2 | P2 (518) | both hands push down for the jump; fist leads the head-down dive; slam at 56; the aim sweeps across the crater from 96 |
| 06 | Unprimed slide U1 | U1 (518) | ring fist low and forward; the free hand drags on the ground through the slide |
| 07 | Flight take-off F2 | F2 (216) | running pump; both hands push down at 26; rocket punch up at 29; fist levels out and leads |
| 08 | Double jump standing S1 | S1 (403) | both hands push down for the puff at 12; ring fist forward in the hover |
| 09 | Double jump running A2 | R3A2 (403) | running pump; push down at 19; ring fist leads the dart |
| 10 | Sprint with lantern S5a | S5a (227) | ring fist pumping with the stride; free hand low left holding the lantern by its handle |
| 11 | Ring arm leads flight D1 | D1 (404) | ring fist leads into each turn, 0.08 s ahead of the view |

## For the game
- `first_person_moves_poses.json` has, per move and style and per tick, each arm in view space in RingFirstPerson's
  terms: blocks, x right, y up, -z forward.
  - Each arm has a fist point and an elbow point (the arm runs from fist to elbow) and the back-of-hand direction.
  - Each tick also has the ring glow and the camera shake.
- Effects (craters, puffs, beams) are not drawn here; see each take's own .blend.

## Open for J
- vanilla or bigger, per move (or one style for all)
- KEEP / IMPROVE / DROP per move
