# Pass 400: power landing, stop dead or one-foot slide (Blender designer chat, 2026-10-14)

**J's request:** "a power landing that either stops you dead or if you are moving above a certain limit create a slide
animation ... a construct texture animation clearing the blocks i slide to until i come to a halt and the animation for
the slide should be a strong one foot stop". His in-game shots show the current physics sliding him a long way after the
landing crater.

**His picks before the build:** show all 3 thresholds, both clearing styles as takes, the **left foot** plants (ring hand
free), and short and brutal: **5 blocks at most**.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\power_slide.blend`; start on **Cam A2** and scrub frames 16–40
  (touchdown is tick 20, which is frame 21).
- Script: `docs/blender/blender_updates/400_power_slide.update.py`
- Poses: `power_slide_poses.json` (per tick, per part `rot` + `offset_px`; per cleared block, when it turns construct and
  when it is gone)
- Sheet: `sheet.png` (rows: D0 side, A3 over the shoulder, A3 side, B3 over the shoulder, B3 front; frames 16–36)

## Takes

| Take | Lands at | Threshold | What happens |
|---|---|---|---|
| D0 stop dead | 5 b/s | under it | Two-foot squat, ring fist to the ground. The block you land on turns construct and holds you (fades back over 1 s); the 8 around it light up and dissolve into pixels; ground pulse, radius 3. |
| A1 / A2 / A3 dissolve | 10 / 18 / 28 b/s | 8 / 15 / 25 | Left foot plants and skids, body leans back, ring arm thrown back and out, free arm forward. Blocks ahead of the foot light up in construct texture about 1.6 blocks out and break into pixels as the foot reaches them. A construct pad under the foot keeps you level over the trench. Halts on the solid block at the end with a forward rock onto the planted knee, holds for 10 ticks, then stands. |
| B1 / B2 / B3 plough | 10 / 18 / 28 b/s | 8 / 15 / 25 | Same body. A construct bow-wave blade half a block ahead of the foot shoves each block out of the path. The blocks tumble aside in construct texture, land square on the surface beside the trench, and dissolve into pixels 12 ticks later. At the halt the blade pushes on a little and fades. |

## Numbers for the game

- Slide length = `min(5, 5 × speed / 28)` blocks, so 10 b/s gives 1.8, 18 b/s gives 3.2 and 28 b/s gives 5.0.
- Slide time = `round(2 × length / speed × 20)` ticks, which is 7 ticks for all three. The deceleration is constant, and
  the position is `-len × (1 - (1 - k/n)²)`.
- Trench width: 1 block under 15 b/s, 3 at 15 and above. The trench runs from the touchdown block to the block before
  the halt; the halt block stays.
- Pose timing after touchdown:

  | Ticks | Pose |
  |---|---|
  | 0–2 | REACH → IMPACT (absorb: `sink` 1.5 px, planted knee 0.95) |
  | 2–n | → SKID |
  | n to n+4 | → HALT (rock forward) |
  | 10 more | hold |
  | 14 | → STAND |

- Ring glow: 18 at the impact, 16 through the skid, easing to 7.
- D0: squat in 3 ticks, hold to tick 20, stand by tick 34.

## Open for J

1. D0, A or B? Which threshold: 8, 15 or 25 b/s?
2. Should the slide angle with your movement when you land moving sideways (ties into pass 401, the directional
   take-off)?
