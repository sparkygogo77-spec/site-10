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

## 2026-10-14 pass 510: big slam S3 M3 picked, triggered from free flight   [WAITING]
- What: J picked S3 M3 and wants free flight with the slam starting only on a nose-dive at speed near the ground.
  Trigger: pitch >= 40 deg, speed >= 1.0 b/tick, height <= H (H6 / H5 / H3; 4 / 3 / 2 ticks of animation).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\flight_slam4.blend (Cam S3 H5, frames 1-60)
- Review folder: docs/blender/review/510_flight_slam4/
- J's picks: trigger height.

## 2026-10-14 pass 509: flying flurry, backfist into a crater or 50 blocks then regain   [WAITING]
- What: J picked F2 (507: jab-cross-spinning backfist) and wants it in flight: the target is carried along the punches,
  the backfist launches it at the hit angle; it craters where it hits the ground (A1 20 deg, A3 60 deg) or, after 50
  blocks with no hit, regains control and lands (A2).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\flying_flurry.blend (Cam A1, frames 1-100)
- Review folder: docs/blender/review/509_flying_flurry/

## 2026-10-14 pass 508: flight slams, 0.7 s lock picked, mobs launched on contact   [S3 M3 PICKED -> 510]
- What: J picked L2 ("locked .7s") and wants mobs launched "instantly or almost" on contact, not when the pulse reaches
  them. M1 instant, M2 almost (1 tick per 3 blocks), M3 instant with the crater lit 6 ticks longer. S2 and S3.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\flight_slam3.blend (Cam S2 M1, frames 14-64)
- Review folder: docs/blender/review/508_flight_slam3/
- J's picks: M1 / M2 / M3.

## 2026-10-14 pass 507: flurry round 5, short mixed strings that send them flying   [F2 PICKED -> 509]
- What: J "mixed short burst combo string that sends them flying". F1 jab-hook-uppercut, F2 jab-cross-spinning
  backfist, F3 body hook-cross-point-blank blast; hits at ticks 6/11/18, the third launches the target 8-12 blocks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\flurry5.blend (Cam F1, frames 1-60)
- Review folder: docs/blender/review/507_flurry5/
- J's picks: F1 / F2 / F3.

## 2026-10-14 pass 506: omega beams round 5, irregular zigzag with random routes   [WAITING]
- What: J picked zigzag (504 a): "shorter streaks ... turn more often ... all kinds of directions randomly ... hit from
  unpredictable angles every time". Lightning-like zigzag (corners every Z1 0.35-0.6 / Z2 0.22-0.4 blocks, kicks keep
  turning), wandering routes with a random approach side, heads 1.3 blocks a tick. Z3 = Z2 with a wilder route.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_beams5.blend (Cam O1-Z2, frames 1-140)
- Review folder: docs/blender/review/506_omega_beams5/
- J's picks: Z1 / Z2 / Z3.

## 2026-10-14 pass 505: dash strike round 5 (faster, arms drop after)   [WAITING]
- What: J on 503 "R3a is better but the animation should maybe be way faster ... R3c ... the end animation of the hand
  coming up is unnecessary". R3a with a 6/4/3-tick dash, R3c with 6/4; no guard after the punch. J also: "R4b is good
  too" -> R4b (absorb, turns green and charges) PICKED.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\dash_strike5.blend (Cam R3a-4, frames 1-40)
- Review folder: docs/blender/review/505_dash_strike5/
- J's picks: dash speed. Flurry (R5) is open: J "needs less repetitive punching", not sure how yet.

## 2026-10-14 pass 504: omega beams round 4 (one writhing pair, slow walk, faster burn, chaining barrage)   [a zigzag PICKED -> 506]
- What: from J's notes on 223. One pair of parallel lasers per use, never straight: the 4.5-block tail always shows 3-4
  moving bends (a zigzag / b snake / c hooks). O1 slow walk while firing; O2 hover brake KEPT; incinerate in 0.5 s;
  O3 barrage: calm, 0.6 s charge, the same pair threads all six targets, movement back once it leaves the eyes.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_beams4.blend (Cam O1a, frames 1-120)
- Review folder: docs/blender/review/504_omega_beams4/
- J's picks: bend style a/b/c. Supersedes the beam look in docs/handoff/2026-10-14-omega-beams.md once picked.

## 2026-10-14 pass 503: combat round 3 refined (R2 hammer, R3 dash, R4 absorb, R5 flurry)   [R4b PICKED; R3 -> 505]
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

## 2026-10-14 pass 501: flight slam tiers S2 + S3, locked on touchdown   [L2 0.7 s PICKED -> 508]
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
