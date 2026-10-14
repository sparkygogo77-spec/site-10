# Lantern Ring: every design in one place (2026-10-14)

This is the single catalogue of the Blender designs: what each is, its status, the `.blend` J opens in
`C:\Users\Josh\Documents\LanternLive\`, and the script that rebuilds it (`docs/blender/blender_updates/<pass>.update.py`).

**Status key:**
- **IN JAR**: in a built jar (version given)
- **SENT**: briefed to the mc project chat, waiting on a jar
- **HANDED OFF**: J picked it and the brief is written
- **WAITING**: built and waiting for J's pick
- **OLD**: superseded

J's style rules are in the `lantern-ring-design` skill. The game hand-off briefs are in `docs/handoff/`.

## Lanterns and charging

| Design | Status | .blend | Pass / source |
|---|---|---|---|
| Square emblem ring round 2: P01–P04 (J's picks T01, T14, T17, T20 refined) + N01–N16, flecked stone, bevelled gold | PICKED: P03, N01, N04 (glow) | `lanterns\square_ring_r2.blend` | 596 |
| Ring picks R12, R16, R19, R25 refined: a as picked, b detail, c band swap, d big face + halo, e diamond pass | PICKED: R19d, R12b, R12c, R16a without icon | `lanterns\ring_picks_800.blend` | 800 |
| Rings in game: R19d, R12b, R12c, R16a (no icon), Blockbench models | HANDED OFF | `lanterns\rings_in_game.blend` | 801, `docs/handoff/2026-10-14-rings-in-game/` |
| 25 original rings made of W1/H1 (Q01–Q05 square picks, R06–R25 new), steady bright glow | PICKED: R12, R16, R19, R25 | `lanterns\rings25.blend` | 599 |
| Classic-shaped ring, diamond-shiny, original marks M1–M4 (light-cut / gold inlay) | WAITING | `lanterns\classic_ring.blend` | 598 |
| Square emblem ring with our animated textures (X5 ripple, X3D1, W1, H1) on P01–P04 | WAITING | `lanterns\square_ring_tex.blend` | 597 |
| Square emblem ring, 20 takes | OLD: T01, T14, T17, T20 picked | `lanterns\square_ring20.blend` | 595 |
| Dark Lantern (glassy ribs, gold cracks, port) | IN JAR (L1) | `lantern_models.blend` | `tools/pixel_dark_lantern4.py`, 21–35 |
| Lantern charge G3 (seated ring, 12 s to full, overcharge, slow fade) | approved direction | `charge_g3b.blend` | 62–75 |
| Red battery: B2 body, C1 arched handle, smooth crimson | IN JAR (2.1.641) + Red toggle | `red_battery_final.blend` | 100, `docs/handoff/2026-10-13-red-battery-final/` |
| Kneel and lean round 4: K3c kneel pick-up, L1c–L1e, L2c | HANDED OFF: K3c + L1c | `kneel_lean4.blend` | 213, `docs/handoff/2026-10-14-lantern-charge/` |
| Charge light running down the lantern (port to base, saturated) | HANDED OFF | `kneel_lean4.blend` | 213 |
| Charging at the lantern: C1 oath kneel, C2 raised, C3 both knees | WAITING | `lantern_charge.blend` | 219 |
| Hanging charge (Dark Lantern on a hook, pendulum): H1 press, H2 punch, H3 steadied | WAITING | `hanging_charge.blend` | 220 |
| Earlier kneel/lean rounds | OLD | `kneel_lean.blend`, `kneel2.blend`, `kneel_lean3.blend` | 203, 208, 212 |

## Movement and flight

| Design | Status | .blend | Pass / source |
|---|---|---|---|
| Sprint S1 + S4 combined, lantern carried higher (S5a 43° / S5b 57°) | HANDED OFF (S5a/S5b as Ring Lab options) | `sprint_run2.blend` | 227, `docs/handoff/2026-10-14-movement-flight/` |
| Sprint S1–S4 (ring forward, power pump, launch dash, lantern carry) | OLD (S1 + S4 picked) | `sprint_run.blend` | 214 |
| Flight takeoff: F1 leap, F2 rocket, F3 glide off (level at 12 blocks) | HANDED OFF: F2, launching in the direction of movement | `flight_takeoff.blend` | 216 |
| Ground flight: skim, ride over steps, invisible 3.5-block dome craters on 2+ high walls; H1/H2/H3 stops | HANDED OFF (H as Ring Lab options) | `ground_flight.blend` | 228 |
| Flight air poses (7 × arm style A/B), landings L1 run-out, L2 hover, L3 hero + construct pad | WAITING | `flight_air.blend` | 217 |
| Flight effects T1–T5 | HANDED OFF: T4 + light trail + sonic boom | `flight_fx.blend` | 218, `tools/flight_fx_textures.py` |
| Super jump (takes, landings, air, ribbon, rise, X3 motion) | super jump chat's own picks | `super_jump*.blend` | 81–91, `docs/handoff/2026-10-13-super-jump-*.md` |
| Power landing: D0 stop dead, A1–A3 dissolve slide, B1–B3 plough slide (left foot, 5 blocks max, thresholds 8/15/25 b/s) | HANDED OFF: A3 dissolve default, B2 plough Ring Lab option | `power_slide.blend` | 400, `docs/handoff/2026-10-14-power-landing/` |
| Directional take-off: F2 in 16 directions × A (hips lead, head looks) / B (whole body turns), banked steering | OLD (J wants a very small take-off; see 402) | `takeoff_dirs.blend` | 401 |
| Double-jump take-off: standing puff to a 3.2-block hero hover (S1–S3), running arc flat at 5 blocks in 6 ticks (R1–R3) | OLD (J: S1 "great", R3 dart; refined in 403) | `takeoff_small.blend` | 402 |
| Double-jump take-off round 2 (S1 faster, S2a/S2b no-overshoot springs, R3 dart arm A1–A3) + double-tap soft landing L1–L3 | WAITING | `movement\\takeoff_small2.blend` | 403 |
| Ring arm leads the flight direction by 0.08 s, body follows (D1 pure, D2 anticipation, D3 + bank) | WAITING | `movement\\arm_lead.blend` | 404 |
| Head-pitch rule: neck at most 57° back from the body | in every flight/combat pass | — | 216–226 |

## Combat and powers

| Design | Status | .blend | Pass / source |
|---|---|---|---|
| Combat poses P1–P6 (punch, blast, shield, beam, wall, slam) | WAITING (pick sheet: review/500) | `combat_poses.blend` | 221 |
| Combat combos K1–K5 | WAITING | `combat_round2.blend` | 222 |
| Combat round 3 R1–R5 (grab-throw, hammer, dash afterimages, parry, flurry) | WAITING | `combat_round3.blend` | 226 |
| Flight slams S1–S3 (dive out of flight, crater 3×3 / 5×5 / 7×7 on D0 rules, mobs knocked up and out) | WAITING | `flight_slam.blend` | 500 |
| Omega beams: O1–O3, Q1–Q3 (routing), E1–E5 starts | SENT (E1–E4 as Ring Lab options) | `omega_beams*.blend` | 223–225, `docs/handoff/2026-10-14-omega-beams.md` |
| Blast drills D1–D3, brick texture | IN JAR (2.1.641) | `drills_textured.blend` | 211 |
| Construct tools rounds 1–2 (green and blue) | see the handoff | `construct_tools*.blend` | 204, 207, 950 |
| Hope sanctuary A6 | IN JAR (2.1.641) | `hope_sanctuary2.blend` | 210 |
| Green Deluge W3 (hard-light liquid) | IN JAR (2.1.641) | `deluge_water.blend` | 206, `tools/hardlight_liquid_textures.py` |
| Lantern suit round 3 (5×5 shell × accent, eye band, forms feet first, ring flare) | WAITING | `lantern_suit3.blend` | 215 |
| Green suits in W1 neon: V1–V5 | OLD: V3 Plates picked, carried into 591 | `suit\suit_w1.blend` | 590 |
| Suit armour A1 Plates, A2 Heavy, A3 Lamellar, A4 Knight, A5 Titan × W1/H1/BR1 emerald/BR1 jade/X3D1, one animated texture each | OLD: carried into 592 | `suit\suit_armour.blend` | 591 |
| Suit armour round 2: A1–A5 plus intricate A1+–A5+ (ridges, glowing seams, rivets, collar, buckle), one animated texture each | OLD: A2+ Heavy in W1/H1/BR1 picked, carried into 594 | `suit\suit_armour2.blend` | 592 |
| Suit armour round 3: A2++ Heavy enhanced, N1–N15 new designs, R1–R5 segmented full sets with open helmets | WAITING | `suit\suit_armour3.blend` | 594 |
| Squad armour, corps metals | other chats' work | `squad_armour.blend`, `corps_metals.blend` | 201, 93–99 |
| Red towers (C1–C3, D1–D3, F1–F3) | OLD (J: "unsatisfactory regardless of the material") | `red_tower*.blend` | 202, 93–99, 300–303 |
| Red Lantern spheres S1–S3 with rage smoke | OLD ("wasted space") | `red_sphere.blend` | 350 |
| Red sky citadels P1–P3 (decks, beacon beam) | OLD: P3 Halo ring picked as the base | `red_citadel.blend` | 351 |
| Red Lantern halo islands H1–H9 (lanterns on top, prison cells under the deck, mob fields, rage smoke) | WAITING | `red_halo9.blend` | 352, `docs/handoff/2026-10-14-red-sphere-pass350.md` |

## Construct textures

| Design | Status | Source |
|---|---|---|
| Particle walls W1–W5 (curtain, lattice, swarm, rising, shards) | WAITING (`particle_walls.blend`) | 700, `tools/blender_edits/particle_walls.py` |
| R2 K1 dark-jade fragments (default construct look, bull/army skin) | IN JAR | `tools/construct_designs*.py` |
| BR1 bricks (jade, emerald, lime, neon, blue) | IN JAR | rounds 4–5 |
| H1 neon hex: the hex for every colour (crimson and yellow too, all formats) | texture library (super jump chat) | `texture_library.zip` |
| W1 weave, D1 sparks, X1, X3, X5 | picks | rounds 5–6 |
| X3D1 emerald glass aura (also the dome texture) | SENT | `tools/construct_designs10.py`, `docs/handoff/2026-10-14-x3d1-glass-aura.md` |
| Barrier surfaces T1–T9 | IN JAR (2.1.641) | `tools/construct_designs9.py` |
| Corps looks (Red R1/R2, Yellow Y1–Y3, Violet V1/V3, Blue B1–B3) | see the handoff | `docs/handoff/2026-10-13-corps-looks/` |
| Skin workshop: 16 green picks + 7 barrier surfaces on suit, wall, dome and particles; particle walls; rings; lanterns | WAITING | `constructs\skin_workshop.blend` | 593 |
| Smoke + long light rays: L1–L4 ray styles, D1–D3 detailed (D3 pixel smoke) | WAITING (`smoke_long_rays.blend`, `smoke_rays_detail.blend`) | 92, 94, 304, 305 |
| Flight trail light + sonic boom ring | HANDED OFF | `tools/flight_fx_textures.py` |

## J's open picks

- S5a or S5b: carry height
- H1, H2 or H3: ground flight wall stop
- Picks not yet made:
  - double-jump take-off (403): S1/S2a/S2b, arm A1–A3 (soft landing: J picked L2)
  - ring-arm lead (404): D1/D2/D3
  - smoke rays: L1–L4 ray style, D3 pixel smoke or wisps
  - C1–C3 (charging at the lantern)
  - H1–H3 (hanging charge)
  - flight air poses and landings
  - suit round 3
  - combat P, K and R
  - Red Lantern halo island H1–H9
