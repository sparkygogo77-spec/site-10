# Pass 401: directional take-off, 16 directions × 2 body styles (Blender designer chat, 2026-10-14)

**J's request:** "the flight take off is problematic not being able to control it ... I need the animations to look
natural while leaving me feel control in the direction i want to go, generate animations for every direction faced and
direction moved as animations for the way someone flies off".

**His picks before the build:** 16 directions (every 22.5° of movement relative to the look), show both body styles,
and bank into turns.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\takeoff_dirs.blend`; start on **Cam A rose**, the view from
  above. The rose layout puts each direction 14 blocks out from the centre and launches it outward, so the whole fan
  reads at once.
- Then look over the shoulder:
  - `Cam A000` to `Cam A338` and `Cam B000` to `Cam B338` (degrees clockwise from the look: 090 is right, 180 is back,
    270 is left). The camera keeps the LOOK direction, the way your game camera does.
  - `Cam <take> side` for each take.
  - `Cam all`.
- Script: `docs/blender/blender_updates/401_takeoff_dirs.update.py`
- Poses: `takeoff_dirs_poses.json`. Per mode and direction, per tick:
  - part `rot` and `offset_px`;
  - `body_yaw_deg`, `travel_deg` and `roll_deg`;
  - `pos` (right, forward, up);
  - `glow`.
- Sheet: `sheet.png`. Rows A000, A090, A135, A180, B090 and B180 at frames 8–92 (every 12), plus the rose.

## Base: F2 rocket (handed off in pass 216), launching the way you move

| Ticks | Phase |
|---|---|
| 0–16 | Run in the travel direction |
| 16–21 | Plant and crouch, ring fist rising |
| 21–39 | Straight up to 10 blocks; the body turns to its flight heading while rising |
| 39–51 | Pitch over into flight, level at 12 |
| 58–78 | Steer: 40° right turn |

## The two body styles

- **A, hips lead and the head looks.**
  - On the ground the body turns toward travel, up to 70°.
  - The head keeps your look, up to 75° of yaw, within the 57° neck pitch rule.
  - Moving more than 90° off the look, you backpedal on the ground (body yaw 0.35 × the back angle). You then fly
    back-first (BACKFLY): leaning back, ring arm reaching the way you go, still facing your look.
- **B, the whole body turns.** The body runs and flies along the travel direction, with the head straight.
- At 0–90° the two are nearly the same. The difference shows from 112° to 248°, where A stays facing you and B turns
  round.

## Steering ("feel control")

- Once level, every take turns right 40° over 20 ticks.
- The bank is a roll about the travel direction of up to 35°, following the turn rate (smoothstep derivative), so the
  top of the body tips into the turn.
- The ring arm reaches toward the inside of the turn while banking. The ring glow rises to 12 in the turn.
- In game: bank = 35° × (yaw rate / peak rate), clamped. The body yaw follows travel each tick, so the player can steer
  freely with the mouse or keys.

## Open for J

1. A or B, or A in front and B behind?
2. Is a 35° bank right, or more?
3. Should a turn also lift the free arm?
4. Should the take-off rise be shorter, so it feels more responsive? F2 is 18 ticks straight up.
