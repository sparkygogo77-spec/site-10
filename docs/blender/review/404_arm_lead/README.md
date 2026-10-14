# Pass 404: the ring arm leads where you fly (Blender designer chat, 2026-10-14)

J on 403 (screenshot of the dart, ring arm up past the head):

> "arm should be animated in the directions a player could move with the arm leading the body by like .08s"

Also: "L2 for the ease landing", so the soft landing pick is **L2** (pass 403).

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\movement\arm_lead.blend`. Start on **Cam D1** (chase), then
  Cam D1 close.
  - Turns: frames 14–54.
  - Climb: frames 62–78.
  - Dive: frames 86–102.
- Script: `docs/blender/blender_updates/404_arm_lead.update.py`
- Poses: `arm_lead_poses.json`. Per tick: parts, pos, body_heading/body_climb, arm_heading/arm_climb, roll_deg.

## The rule

- **Ring arm:** points along the way you are moving now, from your input or velocity.
  - `xRot = -(90° + climb)`: flat ahead when level, raised into a climb, lowered into a dive. It is no longer up past
    the head.
  - `yRot = arm heading − body heading`: it swings left or right into a turn.
- **Body:** follows that same direction **1.6 ticks (0.08 s) later**, so in every turn, climb or dive the arm gets
  there first and the body follows.
- **Free arm:** A2 (slightly forward of the body line) until J picks A1, A2 or A3.

The course flies straight, a hard right (60°), a hard left (90°), a 30° climb, a 30° dive, then level, at 0.7
blocks a tick.

## Takes

| Take | What |
|---|---|
| D1 | Pure lead: arm = where you move now, body = where you moved 0.08 s ago. |
| D2 | Lead plus anticipation: the arm also overshoots by 25% of the turn rate, then settles. |
| D3 | Lead plus bank: D1 with the body rolling into turns, up to 35° (J's earlier bank pick). |

## For the game

- Every tick, keep a 2-tick history of the movement direction and blend the body to the direction from 1.6 ticks
  ago.
- Set the ring arm's xRot and yRot from the current direction.
- This holds in all flight (cruise, take-off arc, landing L2). It never changes where the player goes; it is pose
  only.

## Open for J

1. D1, D2 or D3?
2. Free arm A1, A2 or A3?
3. Standing take-off: S1, S2a or S2b (pass 403)?
