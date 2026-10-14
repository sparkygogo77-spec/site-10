# Pass 519: animation catalogue, every picked animation in third and first person

J: "some third person animations dont have 1st person and vice versa, i need them all in a blender file but ill make a
report here" -> "All picked so far".

- Open in Blender: `LanternLive\animation_catalogue.blend` (one scene, "Animation Catalogue", 171 frames at 20 fps).
- Every take is shown twice:
  - **3rd person** lane (x = lane × 14): the full player, over-the-shoulder follow camera `Cam <id> 3p`.
  - **1st person** lane (same lane, x + 1000): only the arms, ring and lantern, the way Minecraft draws first person.
    Its camera `Cam <id> fp` rides the eyes (eye height 1.62, just in front of the face, 70° vertical field of view).
- `Cam overview` looks down the 3rd-person lanes. The yellow labels mark the areas; the white labels name the takes.
- Poses replay 1:1 from the hand-off / review poses JSON (script: `blender_updates/519_animation_catalogue.update.py`).
- Effects (craters, beams, puffs, domes) are left out; they are in each take's own `.blend` (last column).
- The lantern is the Dark Lantern at its true size: 16 px (one block) tall with the handle, 6.2 px wide. L1c's fist and
  the K3c pick-up are posed for that size. In game it's drawn far bigger when set down, which is the "lantern too big"
  J saw in L1c. The in-game model needs to come down to this size; the poses are already right.

## What the first-person cameras show

"Ring arm in view" is the share of frames where any part of the ring arm is inside the eye camera's frame
(`fp_visibility.json`). 0% means the animation has **no first-person version**: from the eyes, the arms never come
into view. Those need a first-person pose designed for them, like the mod's `RingFirstPerson` aim states.

| Area | Id | Take | Ticks | Ring arm in view | Own .blend (effects) |
|---|---|---|---|---|---|
| Movement | `F2` | F2 flight take-off | 91 | 1% | `flight_takeoff.blend` |
| Movement | `S5a` | S5a sprint, lantern 43 deg | 144 | 0% | `sprint_run2.blend` |
| Movement | `S5b` | S5b sprint, lantern 57 deg | 144 | 0% | `sprint_run2.blend` |
| Movement | `H1` | H1 ground flight stop | 171 | 0% | `ground_flight.blend` |
| Movement | `H2` | H2 ground flight stop | 171 | 0% | `ground_flight.blend` |
| Movement | `H3` | H3 ground flight stop | 171 | 0% | `ground_flight.blend` |
| Movement | `S1` | S1 double jump, standing | 101 | 0% | `movement\takeoff_small2.blend` |
| Movement | `S2a` | S2a double jump, spring | 101 | 0% | `movement\takeoff_small2.blend` |
| Movement | `S2b` | S2b double jump, fastest | 101 | 0% | `movement\takeoff_small2.blend` |
| Movement | `R3A1` | R3A1 running dart, arm side | 101 | 0% | `movement\takeoff_small2.blend` |
| Movement | `R3A2` | R3A2 running dart, arm fwd | 101 | 0% | `movement\takeoff_small2.blend` |
| Movement | `R3A3` | R3A3 running dart, arm out | 101 | 0% | `movement\takeoff_small2.blend` |
| Movement | `L4` | L4 double-tap landing | 101 | 0% | `movement\land_tight.blend` |
| Movement | `L5` | L5 double-tap landing (default) | 101 | 0% | `movement\land_tight.blend` |
| Movement | `L6` | L6 double-tap landing | 101 | 0% | `movement\land_tight.blend` |
| Movement | `D1` | D1 ring arm leads | 131 | 13% | `movement\arm_lead.blend` |
| Movement | `D2` | D2 arm leads + anticipation | 131 | 19% | `movement\arm_lead.blend` |
| Movement | `D3` | D3 arm leads + bank | 131 | 13% | `movement\arm_lead.blend` |
| Movement | `D0` | D0 power landing, stop dead | 101 | 1% | `power_slide.blend` |
| Movement | `A3` | A3 power landing, dissolve | 101 | 1% | `power_slide.blend` |
| Movement | `B2` | B2 power landing, plough | 101 | 1% | `power_slide.blend` |
| Lantern | `K3c` | K3c kneel, pick the lantern up | 85 | 36% | `kneel_lean4.blend` |
| Lantern | `K3cR` | set down (K3c backwards) | 85 | 36% | `none yet` |
| Lantern | `C6a` | L1c charge in 6 s (C6a timing) | 121 | 75% | `lanterns\lantern_charge6.blend` |
| Combat | `R2a` | R2a hammer overhead | 81 | 41% | `combat\combat_round4.blend` |
| Combat | `R2b` | R2b hammer from the side | 81 | 41% | `combat\combat_round4.blend` |
| Combat | `R3a` | R3a dash strike (4-tick dash) | 81 | 12% | `combat\dash_strike5.blend` |
| Combat | `R4b` | R4b absorb and fire back | 81 | 73% | `combat\combat_round4.blend` |
| Combat | `F2f` | F2 flurry jab-cross-backfist | 61 | 2% | `combat\flurry5.blend` |
| Combat | `A1` | A1 flying flurry, crater ahead | 101 | 0% | `combat\flying_flurry.blend` |
| Combat | `A2` | A2 flying flurry, 50 blocks | 101 | 0% | `combat\flying_flurry.blend` |
| Combat | `A3f` | A3 flying flurry, crater below | 101 | 0% | `combat\flying_flurry.blend` |
| Combat | `S3H5` | S3 big slam (in game now) | 101 | 1% | `combat\flight_slam4.blend` |
| Combat | `P1` | P1 primed slam (shift) | 151 | 19% | `combat\primed_slam.blend` |
| Combat | `P2` | P2 primed super-jump slam | 151 | 21% | `combat\primed_slam.blend` |
| Combat | `U1` | U1 unprimed slide | 151 | 0% | `combat\primed_slam.blend` |
Readings:
- **No first person at all (0–2%)**:
  - movement: take-off F2, sprints S5a/S5b, ground flight H1–H3, double jump S1–S2b and R3A1–R3A3, landings L4–L6,
    power landings D0/A3/B2;
  - combat: flurry F2, flying flurries A1–A3, big slam S3, slide U1.
- **Partly in view**:
  - ring-arm lead D1–D3 (13–19%), dash R3a (12%), primed slams P1/P2 (about 20%);
  - hammer R2a/R2b (41%: you see the wind-up, not the hit);
  - K3c pick-up (36%).
- **Reads well**: absorb R4b (73%) and the L1c charge (75%), though in L1c the lantern fills the view and the fist in
  the port sits just below the frame.
- "set down" has no design yet. `K3cR` (K3c played backwards) stands in for it so the in-game set-down can be compared.

## Open for J
- Report per take: 3p OK / fp needed / mismatch with the game.
- Next pass: first-person versions for the 0% takes, starting with the ones J uses most.
