# Pass 403: double-jump take-off round 2, plus a soft landing (Blender designer chat, 2026-10-14)

J on 402:

> "the snap to hover is great, the spring may be better on the way up but it should slow down no higher than snap goes,
> make it faster for both though but more for the speed spring goes up, Running dart seems to be the most accurate, the
> arm should be angled about where the players arm is a little more accurately than a thrown back and up arm"

> "is the animation gonna drag me or allow me to fly once im flying?"

> R1 played backwards: "its a landing? ... not bad if i wanted to double tap space soft land"

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\movement\takeoff_small2.blend`. Start on **Cam S2b side**,
  then Cam R3A1/A2/A3 close and Cam L1 side; frames 10–46.
- Script: `docs/blender/blender_updates/403_takeoff_small2.update.py`
- Poses: `takeoff_small2_poses.json` (adds `heading_deg` per tick)

## Takes

| Take | What changed |
|---|---|
| S1 snap (KEEP) | Faster: up to 3.2 blocks in **3 ticks** (was 4). |
| S2a spring | A critically damped spring: shoots up faster than the snap off the jump (2.66 one tick in) and eases into 3.2, **never above it**. |
| S2b spring, fastest | Same, harder: 2.92 one tick in, 3.19 at two; settled by tick 3. |
| R3A1 dart, arm along the side | J's pick (R3). The free arm lies flush along the body (body pitch + 0), like a player's arm at its side. |
| R3A2 dart, arm a little forward | Body pitch − 0.3 rad. |
| R3A3 dart, arm forward and out | Body pitch − 0.45 rad, splayed 0.32. |
| R3A2 090 | The same, running right of the look. |
| L1 soft landing | R1 exactly reversed. Flat at 5 blocks, double tap space: a slow tip-over, then a quicker drop onto the feet, a construct cushion ring (radius 1.4) at touchdown, a run-out of 12 ticks, and a stop. |
| L2 soft landing, eased | An 8-tick descent eased in and out: the gentlest. |
| L3 soft landing, dart reversed | A 6-tick straight ramp down, dart body line. |

All running and landing takes run their legs forwards (no moonwalk).

## Control: the animation never drags you

- **Standing:** the puff owns 3 ticks (S1) or 1.5–2 ticks plus the settle (S2). The hover then holds only until any
  movement input, and from there it's ordinary flight on the player's input.
- **Running:** the dart owns the 6 ticks of the arc, then it's free flight.
  - Steering input must still change the heading during those 6 ticks: rotate the arc's velocity with the input.
  - Every running take turns 35° right 10 ticks after the arc (`heading_deg`) to show this.
- **Landing:** double tap space while flying near the ground (within about 5 blocks) to start it. Any jump or flight
  input during the 6–8 descent ticks cancels it back into flight.

## Open for J

1. S1 or S2a / S2b?
2. Arm A1, A2 or A3?
3. Soft landing L1, L2 or L3, and how near the ground should the double tap work?
