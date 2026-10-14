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

## 2026-10-14 pass 801: four rings into the game (R19d; R12b, R12c, R16a without icons)   [HANDED OFF]
- What: J: "put r19d in game remove the icon on r16a just do no icons" and "put these two in as well" (R12c, R12b).
  Then "remove the crowns and send them to be put in game": R12b/R12c now plain. Blockbench models exported straight
  from the Blender builds (tools/ring_voxels_bbmodel.py), 276-410 cubes each.
- Open in Blender: `lanterns\rings_in_game.blend` (Cam row game)
- For the game: `docs/handoff/2026-10-14-rings-in-game/` (README.md, assets/bbmodel, assets/textures, preview.png)

## 2026-10-14 pass 518: primed slams (shift / crouch), instant craters, rebuild by left click, slide trench   [WAITING]
- What: from J's in-game test. P1 flying + shift -> locked dive, 7x7 crater opens instantly, construct lining 3 s, left
  click rebuilds (ripple from look). P2 super jump + crouch on the way down -> locked, 9x9, rebuild follows the
  crosshair sweep. U1 no shift -> slide, trench spreading with you, lining one block out all round.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\primed_slam.blend (Cam P1, frames 1-150)
- Review folder: docs/blender/review/518_primed_slam/

## 2026-10-14 pass 517: omega beams round 10 (wild E2 picked, hit on contact, strike endings)   [HANDED OFF: K1 + U3 -> docs/handoff/2026-10-14-omega-beams-final/]
- What: J picked E2 wild (F2 kept). Hits on contact on any angle; no last-second straight zip; final corner into a
  strike: K1 snap / K2 coil / K3 pierce. Under water: wild at restless speed (U3 1.6x, U4 2x head speed).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_strike.blend (Cam K1 target, frames 1-130)
- Review folder: docs/blender/review/517_omega_strike/
- J's picks: K1 / K2 / K3, U3 / U4.

## 2026-10-14 pass 516: omega beams round 9, erratic and darker; W2 sleeve picked   [E2 PICKED -> 517]
## 2026-10-14 pass 800: ring picks R12, R16, R19, R25 refined, five takes each   [PICKED: R19d, R12b, R12c, R16a (no icon) -> 801]
- What: J picked R12, R16, R19, R25 from 599. Takes a (as picked), b (beading, 16 facets, gold band line), c (band
  texture swapped), d (bigger face + a second line of light), e (diamond-gloss stone, 24 facets, gold rim). Original
  designs only (J's claim of a studio commission can't be verified here, so no published emblem). New range: 800-899.
- Open in Blender: `lanterns\ring_picks_800.blend` (Cam row R12/R16/R19/R25, play)
- Review folder: `docs/blender/review/800_ring_picks/` (README.md, sheet.png)

## 2026-10-14 pass 516: omega beams round 9, erratic and darker; W2 sleeve picked   [WAITING]
- What: J: rotate on the joins, completely unpredictable paths, darker; W2 boiling sleeve, denser, lingering briefly.
  Corners roll ~half a turn; sides blend random and target (commit curve); E1 restless / E2 wild / E3 wild + bursts.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_erratic.blend (Cam E2 wide, frames 1-130)
- Review folder: docs/blender/review/516_omega_erratic/
- J's picks: E1 / E2 / E3.
## 2026-10-14 pass 599: 25 original rings made of the textures, steady bright glow   [PICKED: R12, R16, R19, R25]
- What: J: glow "stayed bright and never faded ... even brighter", "a ring made out of the hex ... neon weave", "25 at
  a time, no repeats in design". Q01-Q05 remake his square picks from W1/H1 (bands and faces); R06-R25 are twenty
  original rings (7 face shapes x 9 original marks x light-cut/gold x 4 band builds, no combination repeated).
- Open in Blender: `lanterns\rings25.blend` (Cam row 1-5, play)
- Review folder: `docs/blender/review/599_rings25/` (README.md, sheet.png)
- Note: last pass number in Chat C's 500-599 range.

## 2026-10-14 pass 598: classic-shaped ring, diamond-shiny, four original marks   [WAITING]
- What: J asked for "a classic green lantern ring ... shiny ... like diamond surface". The published ring and emblem
  are not copied; J chose new original marks (Lantern, Flame, Oath star, Rising chevrons), each light-cut or gold inlay,
  with N04's light lines. Also: 597 rebuilt with the ripple centred on the face (J).
- Open in Blender: `lanterns\classic_ring.blend` (Cam C01 Lantern light-cut, play); `lanterns\square_ring_tex.blend`
- Review folder: `docs/blender/review/598_classic_ring/` (README.md, sheet.png)

## 2026-10-14 pass 597: square emblem ring wearing our animated textures   [WAITING]
- What: J: "can you put our textures on the ring yet, like the ripple?" P01-P04 each in X5 ripple emerald/neon, X3D1
  ripples, W1 neon and H1 neon on the green, animated as the game strips, voxel shading kept on top.
- Open in Blender: `lanterns\square_ring_tex.blend` (Cam row <ring>, play)
- Review folder: `docs/blender/review/597_square_ring_tex/` (README.md, sheet.png)
- J on 596 meanwhile: P03, N01, N04 "the glowing looks great".

## 2026-10-14 pass 596: square emblem ring round 2, 4 refined picks + 16 new takes   [PICKED: P03, N01, N04]
- What: J picked T01, T14, T17, T20 and asked for "more rings, more detail and variation" (with a photo of a real
  square ring). P01-P04 refine his picks; N01-N16 grow four families from them. New detail: flecked or banded
  (malachite) stone, bevelled gold, engraved bands, rope trim, shoulder inlays, a faceted proud gem, eight spokes, gold
  and white-gold bodies. The photo's round emblem was not copied.
- Open in Blender: `lanterns\square_ring_r2.blend` (Cam P01 Faithful plus, play)
- Review folder: `docs/blender/review/596_square_ring_r2/` (README.md, sheet.png)
- Open: which take(s) go to Blockbench.

## 2026-10-14 pass 595: square emblem ring, 20 takes that light up   [OLD: T01, T14, T17, T20 picked, carried into 596]
- What: J: "extreme effort ... the square emblem ring head or face, it will have to light up ... 20 takes on the ring, no
  repeats, stay faithful to this ring". Every take keeps his concept's grey band, gold-framed square face, green top and
  bottom bars, side columns and concentric centre; bands, relief, rings, cores, corners and glow differ. The light
  spreads from the core outward from frame 20. Same 0.25 px grid as the game ring.
- Open in Blender: `lanterns\square_ring20.blend` (Cam T01 Faithful, play)
- Review folder: `docs/blender/review/595_square_ring20/` (README.md, sheet.png)
- Open: which take(s); then a Blockbench model for the game.

## 2026-10-14 pass 515: super-speed flight on left click   [WAITING]
- What: S1 hold to ramp 20->60 b/s, S2 tap burst + sonic boom, S3 ramp then a hard dive into the S3 M3 slam (trigger
  height scales with speed so the slam always gets 3 ticks). Looks: longer green trail, afterimages, ground wake.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\super_speed.blend (Cam S1, frames 1-120)
- Review folder: docs/blender/review/515_super_speed/
- J's picks: S1 or S2 activation.

## 2026-10-14 pass 514: omega beams round 8 (fiery lines, same physics to the hit, speed-scaled chase, under water)   [WAITING]
- What: J on 513: lines need work; must obey the same switchback physics all the way (no closing-in phase); running
  targets lengthen sides up to x1.4; chase a fast flyer at 95% of its speed; bubble trails under water. L1/L2/L3 fiery
  looks (embers, hot spots, corner flares), F1 fast flyer, W1/W2/W3 bubble variations.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_fire.blend (Cam L2, frames 1-80)
- Review folder: docs/blender/review/514_omega_fire/
- J's picks: L1/L2/L3 and W1/W2/W3.
## 2026-10-14 pass 594: suit armour round 3, picks enhanced, 15 new designs, R1-R5 segmented sets   [WAITING]
- What: A2++ Heavy (J's picks enhanced a little more) in W1 neon/emerald, H1, BR1 jade/emerald; N1-N15 new designs
  shown once each; R1-R5 segmented full sets with open-face helmets after J's reference ("try somethings like this").
  One animated texture per suit.
- Open in Blender: `suit\suit_armour3.blend` (Cam row E, then G1-G3, V)
- Review folder: `docs/blender/review/594_suit_armour3/` (README.md, sheet.png)
- Open: KEEP / IMPROVE / DROP per design.

## 2026-10-14 pass 593: skin workshop, every texture on suit, wall, dome and particles   [WAITING]
- What: J: "a skin workshop of all of our current textures ... construct / particle skin renders". One file, a shelf per
  group: 16 green picks and 7 barrier surfaces (each on the A1 Plates suit, a 3x2 block wall, a dome and a particle
  construct, animated as in game), the particle walls W1-W5, 11 rings, 5 lanterns.
- Open in Blender: `constructs\skin_workshop.blend` (Cam W1, play; Cam <code> for any stand)
- Review folder: `docs/blender/review/593_skin_workshop/` (README.md, sheet.png)
- Open: KEEP / IMPROVE / DROP per texture and per use (suit, wall, dome, particles).

## 2026-10-14 pass 592: suit armour round 2, intricate versions A1+ to A5+   [OLD: A2+ Heavy picked, carried into 594]
- What: J: "make more intricate designs of all of these in another row individually". Each 591 design sits next to an
  intricate version (ridges, glowing seams, rivets, collar, buckle, knuckles, trims), one animated texture per suit.
  Also fixes the white flash in the first frames (the floor caught the forming edge). Supersedes 591.
- Open in Blender: `suit\suit_armour2.blend` (Cam row A1+ Plates intricate, or Cam pair <design>)
- Review folder: `docs/blender/review/592_suit_armour2/` (README.md, sheet.png)
- Open: design, plain or intricate, and texture.

## 2026-10-14 pass 591: suit armour, 5 designs x 5 textures, one texture each, animated   [OLD: carried into 592]
- What: J liked 590's V3 Plates and wants "one single really well defined texture", bigger armour, animated. A1 Plates
  (V3), A2 Heavy, A3 Lamellar, A4 Knight, A5 Titan, each in W1, H1, BR1 emerald, BR1 jade and X3D1, playing as the
  game strips do. Replaces 590's mixed looks. Suit area (Chat D's), built in this chat.
- Open in Blender: `suit\suit_armour.blend` (Cam row A1 Plates, play 1-200)
- Review folder: `docs/blender/review/591_suit_armour/` (README.md, sheet.png)
- Open: which design and which texture.

## 2026-10-14 pass 513: glowing omega beams, random targets in view, chasing a horse   [WAITING]
- What: J picked P3 (sides now 0.8-3.2). Barrage takes only targets in a 110 deg FOV, random order. Moving targets are
  led (each side aims where the target will be). Beams are a hot core inside a glow sheath along the whole line, with
  bloom: G1 core+glow, G2 + pulses, G3 + sparks. Chase target: a galloping horse.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_glow.blend (Cam C-G1 / Cam B-G1 wide)
- Review folder: docs/blender/review/513_omega_glow/
- J's picks: G1 / G2 / G3.

## 2026-10-14 pass 512: omega beams chasing moving targets   [WAITING]
- What: J "omega beams chasing a moving target ... same physics". 511's angular pair (P2), laid tick by tick: each new
  side aims at the target's current position; within one short side it homes in. C1 runner, C2 dodger, C3 flyer.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_chase.blend (Cam C1 / C1 wide, frames 1-80)
- Review folder: docs/blender/review/512_omega_chase/
## 2026-10-14 pass 590: five Green suits, all W1 neon   [OLD: V3 Plates carried into 591]
- What: J: "we're gonna need these suits all given 5 suits using this texture". V1 full shell, V2 uniform, V3 plates,
  V4 two-tone, V5 channels; all keep the band mask, white eyes, square emblem and W1 weave. Suit area (Chat D's), built
  as 590 in this chat.
- Open in Blender: `suit\suit_w1.blend` (Cam all, frame 60)
- Review folder: `docs/blender/review/590_suit_w1/` (README.md, sheet.png)
- Open: which cut (or mix cuts).

## 2026-10-14 pass 511: omega beams round 6, long angular lines built out of the eyes   [WAITING]
- What: from J's references: straight sides with sharp switchback corners, the pair stays joined to the eyes and grows
  corner by corner, then burns away from the eye end after the hit. P1 short sides / P2 long sides / P3 sharper.
  Heads 1.8 blocks a tick; barrage lets go of the eyes at 10 blocks so you can move.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\omega_beams6.blend (Cam O1-P2, frames 1-100)
- Review folder: docs/blender/review/511_omega_beams6/
- J's picks: P1 / P2 / P3.

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

## 2026-10-14 pass 503: combat round 3 refined (R2 hammer, R3 dash, R4 absorb, R5 flurry)   [R4b PICKED; R3 -> 505; R2a overhead + R2b on walls HANDED OFF -> docs/handoff/2026-10-14-construct-hammer/]
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
## 2026-10-14 pass 405: double-tap landing, tighter and faster   [IN BUNDLE: L5 default, L4/L6 options]
- What: J tested L2 in game: it couldn't be triggered while moving forward, and it carried a few blocks. Now: brake on
  the tap and drop straight in. L4 0.8 blocks/0.30 s, L5 0.4/0.25 s, L6 0/0.20 s (L2 was 8.1/0.60 s). No run-out. Game
  fix: sneak and the double tap work in flight while moving.
- Open in Blender: `LanternLive\movement\land_tight.blend` (Cam L5 close, frames 14-32)
- Review folder: `docs/blender/review/405_land_tight/`; the bundle build order is updated.

## 2026-10-14 pass 404: ring arm leads where you fly (0.08 s)   [WAITING]
- What: the ring arm points along the movement direction (flat ahead when level, not up past the head; raised in a
  climb, lowered in a dive, swung into turns) and the body follows 0.08 s (1.6 ticks) later. D1 pure lead, D2 lead +
  anticipation, D3 lead + 35 degree bank. J: "arm leading the body by like .08s". J also picked L2 (pass 403 landing).
- Open in Blender: `LanternLive\movement\arm_lead.blend` (Cam D1, Cam D1 close)
- Review folder: `docs/blender/review/404_arm_lead/`
- Open: D1/D2/D3; free arm A1/A2/A3; standing S1/S2a/S2b.

## 2026-10-14 pass 403: double-jump take-off round 2 + double-tap soft landing   [WAITING]
- What: S1 snap kept and faster (3 ticks); S2a/S2b faster springs that never rise above the snap height; R3 dart (J's
  pick) with the free arm where a player's arm sits (A1 flush along the side, A2 slightly forward, A3 forward and out).
  New: L1-L3 soft landings (J liked R1 played backwards as "double tap space soft land"). Never drags: free flight
  after 3/6 ticks, and steering works during the arc.
- Open in Blender: `LanternLive\movement\takeoff_small2.blend` (Cam S2b side, Cam R3A1 close, Cam L1 side)
- Review folder: `docs/blender/review/403_takeoff_small2/`
- J picked: **L2** soft landing. Open: S1/S2a/S2b; arm A1/A2/A3 (now with the ring-arm lead, pass 404).

## 2026-10-14 pass 402: double-jump take-off, small and quick   [OLD: J picked S1 + R3, refined in 403]
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
