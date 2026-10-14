# Pass 500: flight slams (Chat C, combat) — WAITING

**Script:** `docs/blender/blender_updates/500_flight_slam.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\flight_slam.blend` (Cam S1, frames 14–60)
**Files here:** `sheet.png` (contact sheet, every 8 frames from frame 14), `flight_slam_poses.json`

## What J asked for

First combat build: slam landings. J picked: **slams out of flight** (not from a jump or standing), **show all three
crater sizes**, and nearby mobs **knocked up and out**.

## The three takes

Each take: flat flight at 20 blocks per second (b/s), pitch over into a head-down dive with the ring fist leading,
swing the legs under in the last 4 ticks, slam (one knee down, ring fist into the ground), hold to tick 20, stand by
tick 34. Touchdown at tick 34 in every take, so they line up. 20 ticks a second.

| Take | Dive from | Dive ticks | Crater | Shockwave radius | Pulse ticks | Knock (out, up) blocks/tick | Mobs |
|---|---|---|---|---|---|---|---|
| S1 small | 6 blocks | 8 | 3×3 (exactly D0) | 3 | 8 | 0.55, 0.45 | 4 |
| S2 medium | 12 blocks | 12 | 5×5 | 5 | 10 | 0.75, 0.55 | 5 |
| S3 big | 20 blocks | 16 | 7×7 | 7 | 12 | 0.95, 0.65 | 6 |

## Rules (D0 from pass 400, scaled out ring by ring)

- The block you land on turns construct for 0.8 s, holds you and fades back. It is **not** removed.
- Every other crater block is ring `d = round(distance)`: it lights up at tick `d - 1` and is gone (construct pixels)
  at tick `4 + 2d`. Only the top layer goes. Pixels drift outward.
- Ground pulse: a construct ring growing to the shockwave radius over the pulse ticks, fading.
- A slam always stops dead, whatever the speed: no slide.
- Dive: the ring sheds a few construct pixels every 2 ticks; ring glow climbs 7 → 16 in the dive, 18 at impact.
- Mobs: hit when the pulse ring reaches them. Launch = direction away from you × out × `max(0.25, 1 - d/(R+1.5))`,
  plus up × `(0.55 + 0.45 × that factor)`. Then vanilla-style gravity 0.08/tick and drag 0.98. A red hurt flash for
  10 ticks. Exact per-mob hit ticks and launch velocities are in the JSON.

## Open questions for J

1. Which size: S1, S2 or S3 — or scale with dive height (S1 under 8 blocks, S2 to 16, S3 above)?
2. After a big slam you stand on the one kept block in a pit (the D0 rule). Keep that, or let the landing block go too
   so you land in the crater?
3. Knock strength: right, harder or softer?
