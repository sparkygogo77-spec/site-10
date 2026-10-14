# Pass 402: double-jump take-off, small and quick (Blender designer chat, 2026-10-14)

**Replaces pass 401.** J:

> "maybe the take off should be a very small animation but it should only be in a certain direction if you are already
> running in that direction but double jumping should once you hit the second jump puff you up so youre floating at
> about 3+ blocks high with a little screen shake flight animation from standing and then you can fly with no limited
> animation, but if you are running in a direction it is a super fast double jump arcs you and has you flying flat by 5
> blocks high"

**Picks before the build:** a construct burst ring on the second jump, a hero hover (ring fist raised forward, free hand
open), 6 ticks from the second jump to flat flight when running, and a subtle shake.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\takeoff_small.blend`. Start on **Cam S1**, then Cam S2 side,
  Cam R1 and Cam R1 side; frames 8–50.
- Script: `docs/blender/blender_updates/402_takeoff_small.update.py`
- Poses: `takeoff_small_poses.json`. Per tick: parts, `pos` (right, forward, up), `glow`, `cam_shake`, and
  `event: burst`.

## Takes

| Take | What happens |
|---|---|
| S1 snap | Standing. A vanilla jump; the second jump (4 ticks in, about 1 block up) sets off the burst ring and a subtle shake, and you puff up to **3.2 blocks** in 4 ticks: a tuck, then the hero hover with a 0.07-block bob over 1.5 s. 34 ticks later he flies off forward, to show the flight isn't locked. |
| S2 spring | Same, but overshoots to 3.7 and settles at 3.2 by tick 12. |
| S3 float | Same, but a smooth 10-tick rise. |
| R1 arc | Running. A sprint jump; the second jump comes 3 ticks in. A burst ring trails back, and you are **flat at 5 blocks in 6 ticks** (ease-out), then free flight. |
| R2 high arc | Peaks around 5.9, then settles onto 5 by tick 6. |
| R3 dart | A straight ramp, already nearly flat, ring arm forward. |
| R1 090 / R1 180 | The R1 arc while running right / backwards relative to your look. It only goes the way you were already running; the body faces the run and the camera keeps your look. |

## Numbers for the game

- **Second jump:** a jump pressed while airborne from the first jump.
- **Standing or running:** under 0.15 blocks a tick of horizontal speed at the second jump gives the standing puff. At
  or over it gives the running arc, along the horizontal velocity.
- **Standing:**
  - puff to 3.2 blocks above the take-off ground;
  - burst ring radius 0.3 → 2.6 over 10 ticks, about 95% → 0;
  - 28 construct pixels flung out at 0.22–0.34 blocks a tick;
  - shake 0.5° pitch and 0.3° yaw, alternating, decaying over 4 ticks;
  - the hover holds until any movement input, then normal flight.
- **Running:**
  - flat at 5 blocks 6 ticks after the second jump;
  - speed 0.3 → 0.95 blocks a tick through the arc, easing to a 0.7 cruise over 30 ticks;
  - burst ring radius 1.8, trailing back at 0.12 blocks a tick;
  - no shake.
- **Ring glow:** 18 at the burst, 13 through the arc, 9 in the hover or cruise.

## Open for J

1. S1, S2 or S3?
2. R1, R2 or R3?
3. Should the running arc get a shake too?
