# Blender review inbox

The Blender chat appends one entry per delivery, newest at the top. The mc project chat (Minecraft threads) reads this
file, reviews each entry and builds from the hand-off it points to once J has picked.

Entry format:

```
## <date> pass <NNN>: <title>   [status: WAITING | PICKED | HANDED OFF | SENT]
- What: one or two lines on what was built and why (J's words in quotes).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\<file>.blend (camera to start on)
- Review folder: docs/blender/review/<NNN>_<name>/ (README.md, contact sheet, poses JSON)
- For the game: docs/handoff/<folder>/ (only once J has picked)
- J's picks / open questions
```

## 2026-10-14 pass 504: omega beams round 4 (one writhing pair, slow walk, faster burn, chaining barrage)   [WAITING]
- What: from J's notes on 223. One pair of parallel lasers per use, never straight: the 4.5-block tail always shows 3-4
  moving bends (a zigzag / b snake / c hooks). O1 slow walk while firing; O2 hover brake KEPT; incinerate in 0.5 s;
  O3 barrage: calm, 0.6 s charge, the same pair threads all six targets, movement back once it leaves the eyes.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_beams4.blend (Cam O1a, frames 1-120)
- Review folder: docs/blender/review/504_omega_beams4/
- J's picks: bend style a/b/c. Supersedes the beam look in docs/handoff/2026-10-14-omega-beams.md once picked.

## 2026-10-14 pass 503: combat round 3 refined (R2 hammer, R3 dash, R4 absorb, R5 flurry)   [WAITING]
- What: from J's notes on 226. R2 ring-only hammer forming from any angle into a 3x3 crater; R3 dash kept, one-handed;
  R4 hold-to-absorb (left click held) then a blast 2x the size and 1.5x the speed; R5 real accelerating punches with
  construct fists. R1 parked until blocks can be encased in our own textures.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\combat_round4.blend (Cam R4b, frames 1-80)
- Review folder: docs/blender/review/503_combat_round4/
- J's picks: one of each a/b/c.

## 2026-10-14 pass 502: combat poses round 4 (P1 punches, P2 blast, P4 beam loops, P5 wall, P6 slam)   [WAITING]
- What: from J's notes on 221. P1 real punches (cross / step-in jab / hook); P2 kept, free hand moves 0/25/50% of the ring
  hand; P3 DROPPED (game shield stays); P4 shaking beam loop with the free hand stabilising + helix / pulse rings / pixel
  stream beams; P5 ring arm only; P6 slam with no wind-up (5/7/10 ticks).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\combat_poses4.blend (Cam P1a; "fp" cameras for first person)
- Review folder: docs/blender/review/502_combat_poses4/
- J's picks: one of each a/b/c.

## 2026-10-14 pass 501: flight slam tiers S2 + S3, locked on touchdown   [WAITING]
- What: J keeps the medium and big slams as two tiers; "it should lock me in place briefly where i touched down for the
  slam since this isnt the slide". Lock L1 0.4 s / L2 0.7 s / L3 1.0 s per tier; the landing block stays construct for
  the lock, then a pixel ring pops and you stand up free in 8 ticks. S1 dropped.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\flight_slam2.blend (Cam S2 L2, frames 14-64)
- Review folder: docs/blender/review/501_flight_slam_lock/
- Open: lock length (same per tier?); can input cancel the stand-up.

## 2026-10-14 pass 500: flight slams, crater S1 3x3 / S2 5x5 / S3 7x7   [WAITING]
- What: Chat C (combat, passes 500–599). Dive out of flight ring-fist first, slam with one knee down; the D0 crater
  rules from pass 400 scaled out ring by ring (landing block stays); mobs knocked up and out by the shockwave.
- Open in Blender: `flight_slam.blend` (Cam S1, frames 14–60)
- Review folder: `docs/blender/review/500_flight_slam/` (README.md, sheet.png, flight_slam_poses.json)
- Open: which size (or scale with dive height); keep the landing block after big slams; knock strength.

## 2026-10-14 pass 700: particle walls W1-W5 as their own file   [WAITING]
- What: the five particle walls (W1 curtain, W2 lattice, W3 swarm, W4 rising, W5 shards) never reached J's folder, so
  they are rebuilt unchanged in a standalone scene (Chat E).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\particle_walls.blend (Cam W1, frames 60-200)
- Review folder: docs/blender/review/700_particle_walls/
- J's picks: W1-W5 keep / improve / drop

## 2026-10-14 pass 600: lanterns, charging, suit pick sheet   [WAITING]
- What: no new design; C1-C3 (219), H1-H3 (220) and suit round 3 (215) rendered as sheets so J can pick (Chat D).
- Open in Blender: lantern_charge.blend (Cam C1), hanging_charge.blend (Cam H1), lantern_suit3.blend (Cam grid)
- Review folder: docs/blender/review/600_lantern_pick_sheet/
- J's picks: C, H and suit shell x accent

## 2026-10-14 pass 500: combat pick sheet   [WAITING]
- What: no new design; P1-P6 (221), K1-K5 (222), R1-R5 (226) rendered as sheets so J can pick (Chat C).
- Open in Blender: combat_poses.blend (Cam P1), combat_round2.blend (Cam K1), combat_round3.blend (Cam R1)
- Review folder: docs/blender/review/500_combat_pick_sheet/
- J's picks: keep / improve / drop per take; round 4 follows in 501+
## 2026-10-14 pass 402: double-jump take-off, small and quick   [WAITING]
- What: standing double jump: a construct burst ring and a subtle shake, then a puff up to a 3.2-block hero hover
  (S1 snap, S2 spring, S3 float). Running double jump: flat flight at 5 blocks in 6 ticks, only the way you were running
  (R1 arc, R2 high arc, R3 dart; R1 also shown running right and back). Free flight after both. Replaces 401.
- Open in Blender: `takeoff_small.blend` (Cam S1, Cam R1 side; frames 8-50)
- Review folder: `docs/blender/review/402_takeoff_small/` (README.md, sheet.png, takeoff_small_poses.json)
- Open: S1/S2/S3; R1/R2/R3; shake on the running arc too?

## 2026-10-14 pass 401: directional take-off, 16 directions x 2 body styles   [OLD: replaced by 402]
- What: F2 rocket launching the way you move, for every 22.5 degrees of movement relative to the look. A: hips lead,
  head keeps the look, back-first flight beyond 90 degrees. B: the whole body turns. Each banks 35 degrees into a 40
  degree right turn once level. J: "look natural while leaving me feel control in the direction i want to go".
- Open in Blender: `takeoff_dirs.blend` (Cam A rose, then Cam A180 / Cam B180)
- Review folder: `docs/blender/review/401_takeoff_dirs/` (README.md, sheet.png, takeoff_dirs_poses.json)
- J: "maybe the take off should be a very small animation"; a standing double jump puffs you up 3+ blocks, a running one arcs
  you flat at 5 blocks, then free flight. See pass 402.

## 2026-10-14 pass 400: power landing, stop dead or one-foot slide   [HANDED OFF]
- What: under the threshold you stop dead (D0, squat, the 3×3 under you turns construct and dissolves). Above it you
  land on the left foot and skid at most 5 blocks while the construct clears the path: A1–A3 dissolve it to pixels,
  B1–B3 plough the blocks aside. J: "a strong one foot stop".
- Open in Blender: `power_slide.blend` (Cam A2, frames 16–40)
- Review folder: `docs/blender/review/400_power_slide/` (README.md, sheet.png, power_slide_poses.json)
- For the game: `docs/handoff/2026-10-14-power-landing/`
- J picked: A3 dissolve (default, slides above 25 b/s), B2 plough as a Ring Lab option (above 15 b/s), D0 under the
  threshold. "optimize the ring lab selection methods too".

## 2026-10-14 passes 350–352: Red Lantern sky island (Chat B)   [WAITING]
- What: J dropped the Red towers ("unsatisfactory regardless of the material") for "an entire red lantern structure"
  for flyers and ground creatures, with "a rage field flowing like heavy smoke" onto the ground. 350 floating spheres
  (dropped: "wasted space"), 351 platform citadels with a beacon beam (J picked P3 Halo ring), 352 nine islands on P3
  with "room for a lot of red lanterns on top", enraged mob fields below and red prison cells under the main deck.
- Open in Blender: `red_halo9.blend` (Cam all, then Cam H1–H9); also `red_citadel.blend`, `red_sphere.blend`. Packed
  copies with textures: project files `blender/red-lantern/` (keep `texture_library/` beside them).
- Review: renders `red-towers/352_red_halo_*.png` (project files), notes `docs/handoff/2026-10-14-red-sphere-pass350.md`.
- For the game: nothing yet (no hand-off until J picks).
- Open: which island (H5 lantern field, H9 great lantern, H7 arena, or H5 round H9); next pass adds real detail.
## 2026-10-14 pass 305: smoke rays with more detail   [WAITING]
- What: 304's long rays with a block-grid ground, a figure for scale, dust motes in the light, and D3 pixel smoke puffs
  ("as detailed as the Cowork chats").
- Open in Blender: `smoke_rays_detail.blend` (Cam D1). Project files: `blender/smoke-rays/` with its `texture_library`.
- Review folder: `docs/blender/review/305_smoke_rays_detail/`
- Open: pixel smoke (D3) or soft wisps; ray style from 304.

## 2026-10-14 pass 304: smoke long rays, refined   [WAITING]
- What: J's "long rays" pick (every side glows, glow fades over 4 blocks, beams from every side) in four ray styles.
- Open in Blender: `smoke_long_rays.blend` (Cam L3). Project files: `blender/smoke-rays/` with its `texture_library`.
- Review folder: `docs/blender/review/304_smoke_long_rays/`
- Open: L1 as picked, L2 shafts, L3 streaks (recommended) or L4 breathing.

## 2026-10-14 pass 228: ground flight with the running barrier   [HANDED OFF]
- What: skim flight, riding over 1-block steps; the invisible 3.5-block dome craters on 2+ high walls and halts you.
- Open in Blender: `ground_flight.blend` (Cam H2)
- For the game: `docs/handoff/2026-10-14-movement-flight/`
- Open: H1 / H2 / H3 stop, as Ring Lab options.

## 2026-10-14 pass 227: sprint S1 + S4   [HANDED OFF]
- What: ring forward while running, with the lantern carried a little higher.
- Open in Blender: `sprint_run2.blend` (Cam S5a)
- For the game: `docs/handoff/2026-10-14-movement-flight/`
- Open: S5a or S5b, as Ring Lab options.

## 2026-10-14 pass 213 update: knees back; charge light down the lantern   [HANDED OFF]
- What: K3c kneels on one knee (no splits); the charge light runs from the port to the base.
- Open in Blender: `kneel_lean4.blend` (Cam L1c)
- For the game: `docs/handoff/2026-10-14-lantern-charge/`

## 2026-10-14 passes 216–226: neck limit   [fix]
- What: flat flyers look ahead instead of folding the head into the chest (J on F3). All of those .blend files were
  re-sent.
