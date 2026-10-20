# Blender review inbox

The Blender chat appends one entry per delivery, newest at the top. The mc project chat (Minecraft threads) reads this
file, reviews each entry and builds from the hand-off it points to once J has picked.

Entry format:

```
## <date> pass <NNN>: <title>   [status: WAITING | PICKED | HANDED OFF | SENT]
- What: one or two lines on what was built and why (J's words in quotes).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\<area>\<file>.blend (camera to start on)
- Review folder: docs/blender/review/<NNN>_<name>/ (README.md, contact sheet, poses JSON)
- For the game: docs/handoff/<folder>/ (only once J has picked)
- J's picks / open questions
```

## 2026-10-20 pass v2.0112: Grizzly, Yellow Lantern enderman and blue great white, refined   [status: PICKED IMPROVE G2a G2b G2c E2a E2b E2c (J: smaller mobs with proper animations: polar bear 2.5x with long sloth-like arms, a ~7-block lantern-carrier enderman with lava/water constructs, teleport animation variations, an Orange Lantern enderman praying hugging its lantern; shark smaller too) -> next pass]
- What: J: "I want grizzly refined, shark and the other i named as well" (the round 4 Titan creatures; the Titan is shelved, so these stand alone). G2a-c grizzly swipe / charge / rearing roar, E2a-c Lantern Enderman block carrier / scream lunge / kneels to charge, S2a-c great white breach / banking hunt / ledge lunge. Legs and fins checked: no crossing, no floor clipping, real contact. Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\grizzly_enderman_shark.blend (Cam <code> per take, frames 1-120)
- Review folder: docs/blender/review/v2.0112_grizzly_enderman_shark/
## 2026-10-20 pass v2.0116: Creatures round 2: polar bear, Lantern endermen and sharks at mob size, animated   [status: WAITING (render started on J's PC 2026-10-19 23:08; take grid + rating questions still to do: docs/handoff/retired/2026-10-20-creatures-refine.md)]
- What: J's v2.0112 notes: smaller mobs with proper animations. PB1-PB6 5-block sloth-armed polar bear (idle, walk, swipe, rear, hurt, death); YE1-YE9 7-block Yellow Lantern enderman with lava/water constructs (idle, 3 teleports, lantern slam, lava throw, water cast, hurt, death); OE1-OE3 Orange Lantern enderman prayers; SK1 great whites 22/14/10/6, SK2 four shark types, SK3-SK7 10-block great white clips. IK-planted feet, every frame checked. Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\creatures_r2.blend (Cam <code> per take, frames 1-60)
- Review folder: docs/blender/review/v2.0116_creatures_r2/
## 2026-10-20 pass v2.0115: Dread Warren round 8: more entrances on what the game already makes, textured, a modern shaft   [status: WAITING]
- What: J: "all three are good, more scenarios like this, perfect utilization of existing generations ... modern looking shafts ... the cave would need texturing". W1a8a-b textured mine and ravine, W1a8c modern shaft, W1a9a dungeon cracked into ours, W1a9b dripstone cave. Built on J's PC. Last pass of the Warren look chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r8.blend (Cam <code> <name> per take)
- Review folder: docs/blender/review/v2.0115_dread_warren_r8/

## 2026-10-20 pass v2.0114: Dread Warren round 7: natural entrances one at a time, ending in the mineshaft design   [status: PICKED KEEP W1a7a W1a7b W1a7c (J: "all three are good") -> v2.0115 more scenarios; steps 1-4 shown in chat]
- What: J on W1a5a: "try to make it look natural ... random", "3 new versions, one by one". Steps shown in chat: W1a5a1 hillside cave, W1a5a2 cliff crack, W1a5a3a-c, W1a5a4a-c (old mine leading in), then J: "natural mineshafts that have the additional portion of ours attached to it" -> W1a7a-c (whole mineshaft with our section, ravine through a mineshaft, inside where it becomes ours). Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r7.blend (Cam <code> <name> per take)
- Review folder: docs/blender/review/v2.0114_dread_warren_r7/

## 2026-10-20 pass v2.0113: Dread Warren round 6: mineshaft, river bank, winding hall and the scream again   [status: PICKED W1a5a IMPROVE (-> v2.0114, one at a time); the rest unrated]
- What: J rated v2.0111 (KEEP W1b6 "Great idea", W3c1b3b). 21 takes: 3 new versions of W1a5, W1a6, W1b5, W3c1a1a, W3c1a1b, W3c1a3b, W3c1b3a. W1b4 and W3c1b1a fixed in place in v2.0111 (rev 2). Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r6.blend (Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0113_dread_warren_r6/

## 2026-10-20 pass v2.0111: Dread Warren round 5: entrances hidden in the world, galleries from inside, Lights out again   [status: PICKED (18 of 33 rated): KEEP W1b6 W3c1b3b; IMPROVE W1b4 W3c1b1a (-> rev 2), W1a5 W1a6 W1b5 W3c1a1a W3c1a1b W3c1a3b W3c1b3a (-> v2.0113); DROP 7; W3c3 and 3 others unrated]
- What: J rated v2.0109 ("these were all scrappable" for the entrances/halls), then "Hidden in the world" and "Yes, from inside". 33 takes: W1a4-6 entrances from eye height, W1b4-6 galleries from inside (both calm-then-danger clips), W3c1a1a-W3c1b3c and W3c3a1a-W3c3c2c Lights out (3 new versions of each IMPROVE, less yellow). Also v2.0109 W2d2a3 rev 2. Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r5.blend (Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0111_dread_warren_r5/

## 2026-10-20 pass v2.0109: Dread Warren round 4: improves and the caves again, webs only in danger   [status: PICKED (31 of 39 rated): KEEP W2d2b1 W3c1c1 W3c1c2 W3c3c1; IMPROVE W2d2a3 (-> rev 2) W3c1a1-a3 W3c1b1 W3c1b3 W3c3a1-a3 W3c3c2 (-> v2.0111); DROP 18; unrated W1b3 W1c1-c3 W2a3c1-c3 W2d2a1]
- What: J: "IMPROVEs + caves". 39 takes: W1a1-3 disguised entrances, W1b1-3 Weave Gallery, W1c1-3 Hatchery (all CALM / DANGER pairs: "I would prefer you only see the webs once youre in danger"), W2a3c1-3 Broodling mane, W2d2a1-W2d2c3 Phantom wire, W3c1a1-W3c1c3 and W3c3a1-W3c3c3 Lights out (the lair's construct spider instead of the cut Matron), W4ba1-3 deep funnel hollow (pairs). Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r4.blend (Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0109_dread_warren_r4/

## 2026-10-20 pass v2.0108: Dread Warren round 3: three new versions of every improve take   [status: PICKED KEEP W2a1c W2a3a W2a3b W2d1a-c; IMPROVE W2a3c W2d2a-c W3a2c W3a3a W3c1a-c W3c3a W3c3c W4ba; DROP 12; unrated W2a1a W2a1b W2a2c]
- What: J: "Hand off + improve all" (v2.0107: Hunter + Weaver handed off). 33 takes: W2a1a-W2a3c Broodlings, W2d1a-W2d2c Phantom, W3a2a-W3a3c Matron, W3c1a-c and W3c3a-c Lights out, W4ba-c funnel hollow, W4ca-c crevice. All turntables. Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r3.blend (Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0108_dread_warren_r3/
- For the game: docs/handoff/2026-10-19-dread-warren-spiders/ (Broodlings W2a1c W2a3a W2a3b, Phantom W2d1a-c)
- Next: 12 IMPROVE for the next modeller chat (this chat retired: docs/handoff/retired/2026-10-19-dread-warren-look.md)

## 2026-10-19 pass v2.0107: Dread Warren round 2: creatures in every pose, new spider caves   [status: PICKED KEEP W2b1-3 W2c1-3; IMPROVE W2a1-3 W2d1 W2d2 W3a2 W3a3 W3c1 W3c3 W4b W4c; DROP W2d3 W3c2 W4a; W3a1 unrated]
- What: J on v2.0106: "creatures and new cave try, i want to see them in various positions ... remove the columns from the big caves ... burrows and terrain more complex and maybe spider favored". W2a1-W2d3 four spiders x three builds x five poses; W3a1-3 Matron x three abdomens x four poses; W3c1-3 Lights out moments; W4a-c new caves (burrow warren, funnel hollow, crevice). All turntables. Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r2.blend (Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0107_dread_warren_r2/
- For the game: docs/handoff/2026-10-19-dread-warren-spiders/ (Hunter W2b1-3, Weaver W2c1-3)

## 2026-10-19 pass v2.0106: Dread Warren look: cave, fear spiders, the Matron   [status: PICKED IMPROVE W2a W2b W2c W2d W3a W3c; DROP W1a-W1d, W3b (-> v2.0107)]
- What: J: "Dread Warren build", then "Look first (Blender) ★". W1a Maw, W1b Weave Gallery, W1c Hatchery, W1d four corps counters (any corps can enter); W2a Broodlings, W2b Hunter, W2c Weaver on a drop thread, W2d Dread Phantom; W3a the Matron, W3b Brood Heart arena, W3c Lights out. Walls and drops only (ceiling walking on hold for the Stormie's Spiders test). Built on J's PC.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\trials\dread_warren.blend (Cam W1b Weave Gallery; Cam <code> <name> per take), frame 60
- Review folder: docs/blender/review/v2.0106_dread_warren/

## 2026-10-19 pass v2.0105: Fresh lanterns: 12 new designs (green)   [status: WAITING]
- What: J dropped all 12 of v2.0103 ("Didnt like all 12"), asked for "New stuff", picked "Fresh lantern designs": F1 classic battery, F2 pagoda, F3 storm lantern, F4 faceted gem, F5 crescent moon, F6 obelisk, F7 hanging bell, F8 pierced star lamp, F9 chalice, F10 clockwork, F11 lighthouse, F12 seed pod. Voxels tools/pixel_lanterns16.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\fresh_lanterns.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0105_fresh_lanterns/

## 2026-10-19 pass v2.0104: Ring models round 1: 12 wild worn rings, hero mesh + voxel twin (12)   [status: WAITING]
- What: J: "new ring models refined as good of a model I can currently get in blender 12 variations (past ones have all been weak)"; picked hero + voxel twin per take, "Wilder" lineup. Subdivided bands, modelled settings, refractive gems with flare cores, layered metal, original lantern mark inlays. Built on J's PC by the PC rings chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\ring_models.blend (Cam W1 hero; Cam Wn turntable / Cam Wn - first person per take), frames 1-120
- Takes: W1 orrery, W2 shard burst, W3 talon clasp, W4 reliquary shrine, W5 forged meteor, W6 aperture eye, W7 mobius ribbon, W8 broken halo, W9 lantern crown, W10 thorn vine, W11 knuckle plate, W12 spire.
- Review folder: docs/blender/review/v2.0104_ring_models/

## 2026-10-19 pass v2.0103: Reliquary round 4: the designs developed (12, green)   [status: DROPPED (J: "Didnt like all 12")]
- What: J on v2.0102: "ports are bigger slightly better on the small ones but it shouldnt have been the main focus of the new round"; picked "Develop the designs", all green. Two new directions for each 612 pick: R2d winged, R2e four arms; R4d gilded cage, R4e claw stand; R4f crowned gyro, R4g held gyro; R1d tiered pedestal, R1e fully gilded; R6d turning frame, R6e ring cage; R2f cathedral, R2g halo. Voxels tools/pixel_lanterns15.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\reliquary_round4.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0103_reliquary_round4/

## 2026-10-19 pass v2.0102: Reliquary round 3: big lit port, near-black crimson (12)   [status: WAITING]
- What: J after v2.0101: "next pass" with the lit port BIGGER on every take, KEEPs too (R2a, R4a, R4b; IMPROVE R1c, R6c, R2b), red near-black crimson. Port 2.25x (v2.0101: 1.5x), raised 1 px, hot ring; 1 green + 1 crimson of each. Voxels tools/pixel_lanterns14.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\reliquary_round3.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0102_reliquary_round3/

## 2026-10-19 pass v2.0101: Reliquary round 2: lit port, dark metallic crimson (12)   [status: WAITING]
- What: from J's 612 picks (KEEP R2a, R4a, R4b; IMPROVE R1c, R6c, R2b: "Cant see the port on any of these, maybe want darker red ... near metallic like the dark lantern"). Port 1.5x, raised and lit on every take; two of each, 1 green, 2 near-black metallic crimson. First pass in J's v2 numbering. Voxels tools/pixel_lanterns13.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\reliquary_round2.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/v2.0101_reliquary_round2/

## 2026-10-19 pass 612: Reliquary round: more gold, rings that move, creative twins (12)   [status: PICKED R2a, R4a, R4b (rated in chat; IMPROVE R1c, R2b, R6c: port not visible on any, darker near-metallic red -> v2.0101)]
- What: J rated 610/611 in chat; picked "Reliquary round": 3 each from 611 Q1 (detailed), 610 N2 ("a more detailed gold portion"), 611 Q4 ("make the rings actually move"), 611 Q6 ("creative i guess"). R4 rings, R6a beam and R6b carousel really move (separate models). Voxels tools/pixel_lanterns12.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\reliquary_round.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/612_reliquary_round/

## 2026-10-19 pass 611: Relic lanterns: 610 shrine and reliquary taken further (12, green)   [status: PICKED Q1, Q4, Q6, S4 (reliquary round -> 612)]
- What: J on 610: build on "Relics"; "More detail", "Bigger glow", "Mix the ideas", "Smaller port"; all green; 12 takes. S1-S6 shrines (detailed, overgrown, crystal crown, halo rings, ruin, two storeys), Q1-Q6 reliquaries (detailed, rooted, crystal, floating, split sleeve, twin balance). 819-2,511 boxes. Voxels tools/pixel_lanterns11.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\relic_lanterns.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/611_relic_lanterns/

## 2026-10-19 pass 610: Original lanterns: relics, alien tech, living (green + one corps each)   [status: PICKED N2g, N2r, N1o, N3b, N5y (rated in chat; reliquary -> 611, 612)]
- What: J: "make me original lanterns now"; mixed bag of ancient relics, alien tech, living/organic; green + one corps; 12 takes; anything goes. N1 shrine (+orange), N2 reliquary (+red), N3 orbital (+blue), N4 split shell (+violet), N5 geode (+yellow), N6 root heart (+indigo). 770-2,234 boxes. Voxels tools/pixel_lanterns10.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\original_lanterns.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Review folder: docs/blender/review/610_original_lanterns/

## 2026-10-19 pass 609: Molten vaults: your four leads refined (608 D1b2, D1b3, D1b5, D1b6)   [status: PICKED D1b3a, D1b5a, D1b5b, D1b6a, D1b6b, D1b6c (rated in chat; fringe: no drips)]
- What: J circled 608 D1b2/D1b3/D1b5/D1b6 and picked "Refine the four": 3 variations each (12 takes). Drip colour "be creative, change it up": gold, bright green light, gold cooling to green, dark emerald with gold flecks, milky jade (named per take). 1,093-2,350 boxes each. Voxels tools/pixel_lanterns9.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\molten_leads.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Takes: D1b2a onion dome, D1b2b lancet arches, D1b2c flared skirt; D1b3a belted, D1b3b spire, D1b3c twin chamber; D1b5a lattice, D1b5b domed, D1b5c heavy bars; D1b6a claw feet, D1b6b pagoda, D1b6c fringe.
- Review folder: docs/blender/review/609_molten_leads/

## 2026-10-19 pass 608: Molten vault: six variations (607 D1b)   [status: PICKED D1b2, D1b3, D1b5, D1b6 (J circled them -> 609)]
- What: J on 607 D1b: "this one is a keeper, i need more variation". Six takes keeping D1b's vault, pillars, drips and core, each changing one big thing. Also fixes "at a certain angle the lantern is transparent (every single model)": the material was blended (no depth), now dithered; 607 rebuilt with the fix (rev 2). Voxels tools/pixel_lanterns8.py.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\molten_vaults.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Takes: D1b1 heavy pour, D1b2 hex, D1b3 tall, D1b4 overflowing bowl, D1b5 caged, D1b6 squat.
- Review folder: docs/blender/review/608_molten_vaults/

## 2026-10-19 pass 607: Pixel lanterns round 2: more complex (606 D1, D6, D5)   [status: PICKED D1b keeper (-> 608; rev 2 fixes transparency)]
- What: J on 606 D1 Vault, D6 Armillary, D5 Crystal: "make these more complex" (comic reference for mood only). 3 takes each: layered frames, fins, gold drips, glowing bowls, sculpted ports, see-through glass with a G3-flare core. 838-1,907 boxes each. Voxels tools/pixel_lanterns7.py. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\pixel_lanterns2.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Takes: D1a cathedral, D1b molten, D1c bastion; D6a orrery, D6b cradle, D6c molten; D5a faberge, D5b winged, D5c molten.
- Review folder: docs/blender/review/607_pixel_lanterns2/

## 2026-10-18 pass 865: Ring glow in first person: round 3 (864 G3a, G3b, G3c variations)   [status: WAITING]
- What: J rated 864 G3a/G3b/G3c IMPROVE (no note) and picked "3 variations of each" (decision manager). Nine orbit-pixel takes on 864's rig; G1/G2 dropped. The primed Shift glow (handover Q24) waits on this pick. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\ring_glow3.blend (Cam G3a1 - first person, frame 75; third person per take), frames 1-120 (charge 1-60, hold 60-90, Bridge 90-120)
- Takes: G3a1 drifting radii, G3a2 darting, G3a3 wandering loops, G3b1 comet tails, G3b2 spiral in, G3b3 stretching tails, G3c1 three planes, G3c2 precessing, G3c3 atom with a heart.
- Review folder: docs/blender/review/865_ring_glow3/

## 2026-10-18 pass 606: New pixel lanterns with polished gold   [status: PICKED D1, D5, D6 (more complex -> 607)]
- What: J dropped 604/605 (smooth): "do new lanterns, the depth of the dark lantern is just the level of complexity and pixelated design, but of course i was expecting a more polished version of the gold on them". Six new designs on the Dark Lantern's 0.25 px grid with its glass; polished gold (lit lips, specular column, deep undersides, engraved bands). Voxels from tools/pixel_lanterns6.py (Blockbench-ready). Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\pixel_lanterns.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Takes: D1 vault, D2 bell, D3 gourd, D4 hex classic, D5 crystal, D6 armillary.
- Review folder: docs/blender/review/606_pixel_lanterns/

## 2026-10-18 pass 605: Proper Red Lantern models   [status: DROPPED (J: too smooth; replaced by 606)]
- What: J picked a "604-style pass" for J:red_lantern: smooth crimson glass, finishes mixed by part (gold, black steel, obsidian), new silhouettes, the claw mark on a raised lens (6 takes). Built on J's PC by the PC chat; runs 604's builder.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\red\red_lantern_proper.blend (Cam all; Cam <code> <name> per take), frames 1-120
- Takes: R1 Y cradle, R2 ruby pinch, R3 steel cage, R4 clutched heart, R5 rage spire, R6 blood lamp.
- Review folder: docs/blender/review/605_red_lantern_proper/

## 2026-10-18 pass 604: Proper lantern models from the dark lantern   [status: DROPPED (J: too smooth; replaced by 606)]
- What: J asked for "proper lantern models" from J:dark_lantern and picked smooth glass, a richer gold frame and new silhouettes (6 takes). Row A refines the jar's pinched column, row B tries new shapes; each turns while the charge fills. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\dark_lantern_proper.blend (Cam all; Cam <code> <name> per take), frames 1-120 (idle to 20, fill 20-80, hold)
- Takes: A1 pinched column, A2 hex pinch, A3 gold cage, B1 tower, B2 orb, B3 hourglass prism.
- Review folder: docs/blender/review/604_lantern_models_proper/

## 2026-10-18 pass 864: Ring glow in first person: round 2 (860 G1, G2, G3 variations)   [status: PICKED G3a, G3b, G3c (3 each -> 865)]
- What: J rated 860 G1, G2, G3 IMPROVE (no note) and dropped G4-G6: 3 new takes of each. Every take now reads on the ring's back sides (what the first-person eye sees) and the green is capped so it stays saturated. Built on J's PC by the PC chat.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\ring_glow2.blend (Cam G1a - first person, frame 75; third person per take), frames 1-120 (charge 1-60, hold 60-90, Bridge 90-120)
- Takes: G1a breathing face, G1b dark core, G1c fills from the centre, G2a two lines meet, G2b double rim, G2c dashed rim, G3a erratic orbit, G3b trailing pixels, G3c tilted orbits.
- Review folder: docs/blender/review/864_ring_glow2/

## 2026-10-19 pass 410: Primed flight lance, three new builds (409 P1 variations)   [status: WAITING]
- What: J rated 409 P1 IMPROVE with no note: "3 new variations". P1a nested hex rings + braid, P1b crystal facets + peeling shards, P1c twin crossed blades + streaks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\movement\flight_barrier2.blend (Cam P1a chase; Cam <take> side; Cam <take> fp; frames 1-120)
- Also 409 P3 changed in place (rev 4): bricks and textures for J's note "need better constructs and textures".
- Review folder: docs/blender/review/410_flight_lance/

## 2026-10-18 pass 863: Fear-consumed mobs: Yellow construct armour and tools   [status: WAITING]
- What: J: "things consumed by fear need better light construct armor and tools nearly like mine" (brief docs/handoff/2026-10-16-fear-consumed-gear/).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\suit\fear_gear.blend (Cam lineup still; Cam <code> per take), frames 1-80
- Takes: armour A1 Scale Reaver (Y1), A2 Storm-split (Y2), A3 Hollow Dread (Y3), A4 Fear Knight (mix); swords S1-S3, axes X1-X3, picks P1-P3, bows B1-B3 across Y1-Y3; LINEUP still. Zombie villager rig, walks in and strikes or draws once.
- For the game (mc chat, after J picks): equip fear-consumed mobs with the picks as construct layers; they drop nothing.
- Review folder: docs/blender/review/863_fear_gear/

## 2026-10-16 pass 862: First-person tools: round 6 variations   [status: WAITING]
- What: J's later 852 ratings (23:58): no-note IMPROVEs S4b1, H1b1, H2a1, H2a2, C1d1 get 3 variations each.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\fp_tools6.blend (Cam S4b11 first person; Cam <take> side), frames 1-85
- Takes: S4b11-13 lunges, H1b11-13 charged smashes, H2a11-13 telescoping hafts, H2a21-23 chained heads, C1d11-13 dash thrusts (prime measured at 20 degrees).
- Review folder: docs/blender/review/862_fp_tools6/

## 2026-10-16 pass 861: First-person tools: round 5 variations (+ 852 noted takes rev 2)   [status: WAITING]
- What: J's 852 ratings (22:27-22:44): no-note IMPROVEs get 3 variations; S3a3 "could be used for another weapon maybe".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\fp_tools5.blend (Cam P1b21 first person; Cam <take> side), frames 1-117
- Takes: P1b21-23, S2b31-33, S2c21-23, S3c11-13; W1 axe, W2 maul, W3 glaive doing the S3a3 move. Every pick lands on the crosshair centre.
- 852 changed in place (rev 2): P1c2, P1c3 mine at the crosshair centre; S2a2 flat blade turned 90 degrees; S2a3 much faster bite and drag.
- Review folder: docs/blender/review/861_fp_tools5/

## 2026-10-15 pass 860: Ring glow in first person: replacements for the light rays   [status: WAITING]
- What: J on the in-game glow: "these light rays from blender are not it", "that glow is also the light coming off from deluge, our light physics are bad"; he picked "New designs to pick".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\ring_glow.blend (Cam G1 - first person, frame 75; third person per take), frames 1-120 (charge 1-60, hold 60-90, Bridge 90-120)
- Takes: G1 face glow = charge, G2 rim line, G3 orbit pixels, G4 face meter, G5 pulse on use only, G6 knuckle light. Nothing on the arm, no panes, no shafts.
- Review folder: docs/blender/review/860_ring_glow/

## 2026-10-15 pass 409: Flight barrier and trail: fast vs primed   [status: WAITING]
- What: J: "the barrier when im flying and primed as well as the trail should look better or different from the fast flying activation". F = new fast-flight barrier; P1 hex lance + twin helix, P2 hex ram shield + afterimage rings, P3 comet nose + pixel tail (each flies 2 s as F, then primes).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\movement\flight_barrier.blend (Cam P1 chase; Cam <take> side; frames 1-120)
- 2026-10-19: P3 rev 4 (brick nose and tail, J: "need better constructs and textures"); P1 variations are pass 410.
- Review folder: docs/blender/review/409_flight_barrier/

## 2026-10-15 pass 859: Sword dash combos: 10 more (+ 844 A1c 45-degree hold, rev 2)   [status: WAITING]
- What: J's picks in chat (DECISIONS.md) and his notes in NEXT-ROUNDS.md.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\dash_combos.blend (Cam C1e1 first person; Cam <take> side; frames 1-81)
- Takes: C1e1-10: cross, cross, 0.7 s prime held 20 degrees off the mob, 12-block dash into a different finish each.
- Review folder: docs/blender/review/859_dash_combos/

## 2026-10-15 pass 858: Compact mech: new textures, more detail (821 MS note)   [status: WAITING]
- What: J's picks in chat (DECISIONS.md) and his notes in NEXT-ROUNDS.md.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\mech_compact.blend (Cam MS1 (Cam row MS), frames 1-130)
- Takes: MS1 Workhorse (W1, villager), MS2 Crawler (V1 crystal, zombie), MS3 Treadline tracked (R2 K1, villager); 0.6 size, detailed panels, pistons, vents.
- Review folder: docs/blender/review/858_mech_compact/

## 2026-10-15 pass 857: Catapult: forms the way it launches (822 S1 note)   [status: WAITING]
- What: J's picks in chat (DECISIONS.md) and his notes in NEXT-ROUNDS.md.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\snap_launcher2.blend (Cam S1a; Cam <take> top; frames 1-80)
- Takes: S1a arc drawn back from the landing, S1b arm sweeps down its throw leaving rails, S1c launch rail rises from the ground; nothing streams from the ring.
- Review folder: docs/blender/review/857_snap_launcher2/

## 2026-10-15 pass 856: Worn ring round 4 (831 notes)   [status: WAITING]
- What: J's picks in chat (DECISIONS.md) and his notes in NEXT-ROUNDS.md.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\worn_ring4.blend (Cam W2d2 ... - first person; third and first person per take; frames 1-120)
- Takes: W2d2 arm glow you can see forming; W2f1 carousel, W2f2 comet, W2f3 helix motes; W5a (reference) + W5a1-4 fist back 50/55/60/65; W5b1-3 settle from 75 to 65/60/55.
- Review folder: docs/blender/review/856_worn_ring4/

## 2026-10-15 pass 704: ripple packing for 702 X5Ea / X5Eb / X5Na (1 grid, 2 honeycomb, 3 interference)   [status: WAITING]
- What: J's 702 IMPROVEs with no note (20:56), three variations each, keeping his X5E note (ripples packed onto big surfaces). Each keeps its 702 colour and grading. 703's ripple takes are renamed X5Pa-c.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\skin_variations3.blend (Cam <code> close), frames 1-160
- Review folder: docs/blender/review/704_ripple_packing/ (README.md); spec specs/704.json
- J's picks / open questions: KEEP / IMPROVE / DROP per take.

## 2026-10-15 pass 855: Suits: C8b purples, circuit blues, hex plate variations (603 notes)   [status: WAITING]
- What: J's 19:14-19:21 ratings (his notes quoted in the review README).
- **C8b material (J asked):** a procedural carbon weave made in Blender's shader, no image: diagonal stripes mixed with a checker (a carbon-fibre twill), near-black violet to dark violet, glossy with a full clear coat, a fine grid of thin glowing violet lines, 92% opaque, solid glowing violet seams and visor.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\suit\corps_suits5.blend (Cam row P / row T1 / row T2, frames 1-60)
- Takes: C8b (reference); C8bP1 royal, C8bP2 plum, C8bP3 ultraviolet; T1a-c darker plates with brighter blue traces; T2a-c real hexagons (flat / domed / flickering cells).
- Review folder: docs/blender/review/855_corps_suits5/

## 2026-10-15 pass 854: Enemies: scarier E1 round (845 notes)   [status: WAITING]
- What: J's 19:14-19:21 ratings (his notes quoted in the review README).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\enemies3.blend (Cam E1a1 (Cam row E1a/E1b/E1c), frames 1-130)
- Takes: E1a1 curtain, E1a2 bell, E1a3 scale cocoon (veil hides a light that brightens with the reveal); E1b1 mask totem, E1b2 stalk crowd, E1b3 mosaic face; E1c1 creeping, E1c2 skitter, E1c3 unfolding stalkers that move across the bay.
- Review folder: docs/blender/review/854_enemies3/

## 2026-10-15 pass 853: Pickaxe rework: 3D pick, block breaking, running crater swing (844 P1a note)   [status: WAITING]
- What: J's 19:14-19:21 ratings (his notes quoted in the review README).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\pickaxe_rework.blend (Cam P1a1 first person; Cam <take> side; frames 1-93)
- Takes: P1a1 faceted crescent, P1a2 laminated, P1a3 shell-and-core (blocks crack, then drop physical chunks, light particles); R1-R3 running through a wall, 8 blocks per swing in a small dome crater, cracking before breaking.
- Review folder: docs/blender/review/853_pickaxe_rework/

## 2026-10-15 pass 852: First-person tools: round 4 variations (+ C1a dash combos C1d1-3)   [RATED 22:56; noted takes rev 2 in place; variations in 861; 23:58 IMPROVEs in 862]
- What: J's 19:14-19:21 ratings (his notes quoted in the review README).
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\fp_tools4.blend (Cam C1d1 first person; Cam <take> side; frames 1-87)
- Takes: P1b, P1c, S2a, S2b, S2c, S3a, S3c, S4b, V1a, V1b 1-3; H1b1-3 (keep H1b); H2a1-3 hitting a mob past the crosshair; C1d1-3 cross, cross, 0.7 s prime at 20 degrees, 12-block dash strike (39). Swords heavier and slower with a charge; mobs react on contact.
- Review folder: docs/blender/review/852_fp_tools4/

## 2026-10-15 pass 844 rev 2: first-person tools, J's noted takes changed in place   [status: WAITING]
- A1a, A1b axe edge faces the cut; C1a arms pulled in, slower cross up right; C1b sword turns in the hand, heavier; C1c slower with a charge, carries further left, the mob reacts; C2b beam-edge forming with sparks, deeper emerald blade; C2c, H1a, H2b heavier hand work; S4a arm turns with the sword; S4c snaps back quickly.
- Waiting on J: the unclear parts of C1a ("another 10 10") and A1c ("weld at about a , Q").
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\fp_tools3.blend (Cam <take>), frames 1-105

## 2026-10-15 pass 851: Mech suits: MCb and MCc variations (+ 843 MAa hammer and villager pilot, rev 2)   [status: WAITING]
- What: J's 18:00 ratings: no-note IMPROVEs get "3 new variations each".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\mech_suits3.blend (Cam MCb1 (Cam row MCb / MCc), frames 1-130)
- Takes: MCb1 Hover Tank, MCb2 Jump Jet, MCb3 Orbit Juggernaut; MCc1 Anvil Breaker, MCc2 Ram Breaker, MCc3 Earthshaker.
- Review folder: docs/blender/review/851_mech_suits3/

## 2026-10-15 pass 850: Bows and shields: round 3 variations (+ 842 H2b fixed in place, rev 2)   [status: WAITING]
- What: J's 18:00 ratings: no-note IMPROVEs get "3 new variations each".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\bows_shields3.blend (Cam B1a1 close, frames 1-70)
- Takes: B1a1-3, B3a1-3, B3b1-3, B3c1-3, H2a1-3, H2c1-3, H3b1-3 (21); no shield touches the arms on any frame.
- Review folder: docs/blender/review/850_bows_shields3/

## 2026-10-15 pass 849: Flying mounts: round 3 variations   [status: WAITING]
- What: J's 18:00 ratings: no-note IMPROVEs get "3 new variations each".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\flying_mounts3.blend (Cam F1a1 (Cam row per group), frames 1-120)
- Takes: F1a1-3, F1c1-3, F2c1-3, F3a1-3, F3b1-3, F3c1-3 (18).
- Review folder: docs/blender/review/849_flying_mounts3/

## 2026-10-15 pass 848: Ring beam: T1a variations   [status: WAITING]
- What: J's 18:00 ratings: no-note IMPROVEs get "3 new variations each".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\ring_beam5.blend (Cam T1a1 close, frames 1-70)
- Takes: T1a1 twin prisms + corner streak waves, T1a2 breathing prism + hex spark hoops, T1a3 flared ratchet prism + orbiting spark rings.
- Review folder: docs/blender/review/848_ring_beam5/

## 2026-10-15 pass 847: Laser: L3a and L3b variations   [status: WAITING]
- What: J's 18:00 ratings: no-note IMPROVEs get "3 new variations each".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\laser4.blend (Cam L3a1 close (eye / side per take), frames 1-60)
- Takes: L3a1 tumbling cubes, L3a2 bead bursts, L3a3 orbit beads; L3b1 hose bulge, L3b2 shock rings, L3b3 throb.
- Review folder: docs/blender/review/847_laser4/

## 2026-10-15 pass 846: Warden armour: R1b and R1h variations   [status: WAITING]
- What: J's 18:00 ratings: no-note IMPROVEs get "3 new variations each".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\warden_armour2.blend (Cam row R1b / Cam row R1h, frames 1-160)
- Takes: R1b1 lamellar, R1b2 loose tiles, R1b3 exo-frame; R1h1 bastion, R1h2 hunched carapace, R1h3 spiked heavy.
- Review folder: docs/blender/review/846_warden_armour2/

## 2026-10-15 pass 703: BRD bricks (carved / brushed alloy / dark gunmetal) and X5E packed ripples X5Pa grid / X5Pb interference / X5Pc rain   [status: WAITING]
- What: J's 701 re-rating at 18:47: BRD more brick detail or metallic bricks with the lines still glowing; X5E ripples packed onto big surfaces. X1 and X3 dropped, so X1a-c and X3a-c are out of spec 702.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\skin_variations2.blend (Cam <code> close), frames 1-160
- Review folder: docs/blender/review/703_skin_bricks_ripples/ (README.md); spec specs/703.json
- J's picks / open questions: KEEP / IMPROVE / DROP per take.

## 2026-10-15 pass 702: skin workshop variations, a deeper / b brighter / c finer for 10 textures   [status: WAITING]
- What: J's 701 IMPROVEs with no note (R2K1, T1, T2, T6, T7, X1, X3, X3D1, X5E, X5N), three labelled variations each,
  same 8 s close tour. KEEPs BRD, BRJR, BRN, T9 are in the review-keeps hand-off; LANTERNS, RINGS, T3, T5 dropped.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\skin_variations.blend (Cam <code><a|b|c> close)
- Review folder: docs/blender/review/702_skin_variations/ (README.md); spec specs/702.json
- J's picks / open questions: KEEP / IMPROVE / DROP per variation.

## 2026-10-15 pass 845: Enemies: E1 variations (812 IMPROVE)   [RATED 19:40; redone in 854]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\enemies2.blend (Cam E1a; Cam <take> close; Cam all), frames 1-130
- Takes: E1a Veil Wisp (shroud splits, gaze beam pins), E1b Mask Swarm (masks circle the head), E1c Stilt Stalker (neck slides in, fear pool).
- Review folder: docs/blender/review/845_enemies2/

## 2026-10-15 pass 844: First-person tools: variations (803 IMPROVEs, 3 each)   [RATED 19:20; noted takes rev 2 in place; variations in 852; P1a rework in 853; S3b KEEP]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\fp_tools3.blend (Cam A1a first person; Cam <take> side), frames 1-77
- Takes: A1, C1, C2, H1, H2, P1, S2, S3, S4, V1 a/b/c (30). Forming: a pixel stream, b extrude, c lock-in; ring on the punching face.
- Review folder: docs/blender/review/844_fp_tools3/

## 2026-10-15 pass 843: Mech suits: MA and MC variations (821 IMPROVEs, 3 each)   [RATED 18:00; MAa hammer + villager in place (rev 2); MCb, MCc variations in 851]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\mech_suits2.blend (Cam MAa (Cam row MA / Cam row MC), frames 1-130)
- Takes: MAa Plated Titan, MAb Exo Frame, MAc Dome Titan; MCa Siege Ape, MCb Rocket Juggernaut, MCc Breaker (each forms, moves, attacks and finishes its own way).
- Review folder: docs/blender/review/843_mech_suits2/

## 2026-10-15 pass 842: Bows and shields: B1-B3, H2, H3 variations (823 IMPROVEs, 3 each)   [RATED 18:00; variations in 850; H2b fixed in place (rev 2)]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\bows_shields2.blend (Cam B1a close (Cam all for the row), frames 1-66)
- Takes: B1a-c compound (swept / machined plate / sliced riser), B2a-c Olympic (bending / laminated / faceted limbs), B3a-c hunting (plate / truss / cube riser, two shots); H2a-c tower (curved brick / riot wall / telescoping), H3a-c dome (geodesic cap / planted dome wall / twin shells).
- Review folder: docs/blender/review/842_bows_shields2/

## 2026-10-15 pass 841: Flying mounts: F1-F3 variations (824 IMPROVEs, 3 each)   [RATED 18:00; variations in 849]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\flying_mounts2.blend (Cam F1a (Cam row F1/F2/F3), frames 1-120)
- Takes: F1a winged horse, F1b hoop horse on a light road, F1c comet horse; F2a round wyrmling, F2b serpent hatchling, F2c blocky glider; F3a ghast snug shell, F3b lattice cage, F3c brick strata (all at the real ghast size).
- Review folder: docs/blender/review/841_flying_mounts2/

## 2026-10-15 pass 840: Ring beam: T1 variations (830 T1, 3 takes)   [RATED 18:00; T1b, T1c KEEP; T1a variations in 848]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\ring_beam4.blend (Cam T1a close (close / side / shoulder per take), frames 1-70)
- Takes: T1a hex prism + spark rings, T1b hex collars + trailing sparks, T1c hex screw + impact fountain.
- Review folder: docs/blender/review/840_ring_beam4/

## 2026-10-15 pass 839: Laser: L0 and L3 variations (834 IMPROVEs, 3 each)   [RATED 18:00; L3a, L3b variations in 847]
- What: J on the no-note IMPROVEs: "3 new variations each", labelled, he picks.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\laser3.blend (Cam L0a close (eye / side cameras per take), frames 1-60)
- Takes: L0 (as before, reference); L0a twisted ribbon, L0b ladder helix, L0c spiral bolts; L3a bead train, L3b heartbeat, L3c bolt volley.
- Review folder: docs/blender/review/839_laser3/

## 2026-10-15 pass 838: Warden construct armour (replaces 828 R1, R2, R4)   [RATED 18:00; R4b KEEP; R1b, R1h variations in 846]
- Open `C:\Users\Josh\Documents\LanternLive\constructs\warden_armour.blend`, Cam row plates / Cam row shells, frames 1-160.
- Plate armour standing off 1.5 px: R1b hex, R2b bricks, R4b weave, R1h hex heavy. Shell right outside the skin: R1c, R2c, R4c.
- Review folder `docs/blender/review/838_warden_armour/`.

## 2026-10-15 pass 701: skin workshop close-ups, animated (593 re-shot)   [status: WAITING]
- What: J: "these i need to see animated on the site and closer up for each thing". Same scene as 593, new cameras:
  one 8 s close tour per texture (wall, dome, particles, suit) and each particle wall up close. 593 superseded on the site.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\skin_workshop_close.blend (Cam <code> close)
- Review folder: docs/blender/review/701_skin_workshop_close/ (README.md); spec specs/701.json
- J's picks / open questions: KEEP / IMPROVE / DROP per texture.

## 2026-10-15 pass 407: standing take-off, S2a settling at 2.2   [HANDED OFF: S2a KEEP; docs/handoff/2026-10-15-movement-keeps/ section 4]
- What: J on 403 S2a "Maybe settles at 2.2" / "Just 2.2": the fast spring now settles at 2.2 blocks; S1 and S2b (3.2) alongside.
- Open in Blender: `movement\takeoff_s2a.blend` (Cam S2a side, frames 1-45)
- Review folder: `docs/blender/review/407_takeoff_s2a/`; spec `specs/407.json`
- Also: R3A3 dropped; 404/405 KEEPs handed off (`docs/handoff/2026-10-15-movement-keeps/`).

## 2026-10-15 pass 837: Eye beam chain round 3   [PICKED: R4 KEEP (2026-10-15 review)]
- What: E1 and E3 looks on the omega physics (erratic in 3D, K1 snap), head speed = k x distance to the target (R1-R4). J: "E1 and E3 for the eye chain but we made physics for how it should behave before, the lines should be much more erratic and not limited to a certain axis or rotation at all, they also move a little too fast it should move more proportional to how far its target is".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\eye_beam_chain3.blend (Cam R1 top)
- Review folder: docs/blender/review/837_eye_beam_chain3/ (README.md)
- J's picks / open questions: KEEP / IMPROVE / DROP per take; which k.

## 2026-10-15 pass 836: Laser round 2   [status: HANDED OFF]
- What: three new takes each for L0 (the game's twin helix, made crisp), L1, L2 and L3. J: "L1 -3 need more variations, l0 can be improved laser".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\laser2.blend (Cam H1 close)
- Review folder: docs/blender/review/836_laser2/ (README.md)
- For the game: docs/handoff/2026-10-15-laser-test-picks/ (H3, N1, N2, N3, P1, C1, C2, C3 as Ring Lab options to test)
- J's picks / open questions: KEEP / IMPROVE / DROP per take; L4 from 834 still unrated.

## 2026-10-15 pass 603: corps suits round 4 (C8b new textures, fixed suit-up, corps-coloured reveal, C5c gauntlets, N1-N3)   [RATED 19:40; C8b purples, T1 blues, T2 variations in 855]
- What: J kept C8b's shape. It is shown in four new textures (T1 circuit, T2 hex plate, T3 scale mail, T4 pinstripe
  alloy). Every suit now forms under the rising light (the 827 C8 materials skipped it), with the reveal band and
  ring flare in the corps colour, not green. C5c is the brick Warden with thick gauntlet hands. New designs from C8b:
  N1 Heavy, N2 Spine, N3 Warlord.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\suit\corps_suits4.blend (Cam row R4; Cam <key>), play for the suit-up
- Review folder: docs/blender/review/603_corps_suits4/ (README.md); spec specs/603.json
- J's picks / open questions: KEEP / IMPROVE / DROP per take; C8b's texture.
- Owner: suits belong to the 800-899 chat (J: hand suits to 800 chat); that chat continues from this pass.

## 2026-10-15 pass 835: Ultimate dome round 2   [status: HANDED OFF]
- What: see the README. J: "the construct of the dome also builds behind the blocks a little too laggy".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\constructs\ultimate_dome2.blend (Cam D1 wide)
- Review folder: docs/blender/review/835_ultimate_dome2/ (README.md)
- For the game: docs/handoff/2026-10-15-keep-ultimate-dome/ (J: "D1 for the dome")
- J's picks / open questions: KEEP / IMPROVE / DROP per take.

## 2026-10-15 pass 834: A new laser   [PICKED: L1, L2 KEEP; L0, L3 variations in 839 (2026-10-15 review)]
- What: see the README. J: "we absolutely need a better laser than the one that shoots right now".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\laser.blend (Cam L1 close)
- Review folder: docs/blender/review/834_laser/ (README.md)
- J's picks / open questions: KEEP / IMPROVE / DROP per take.

## 2026-10-15 pass 833: Eye beam chain round 2   [status: WAITING]
- What: see the README. J: "the lines shouldnt go around corners so predictably either otherwise the one on the right is the best looking, we need better textures for the omega beams i dont think i saw them much in game last time".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\eye_beam_chain2.blend (Cam E1 top)
- Review folder: docs/blender/review/833_eye_beam_chain2/ (README.md)
- J's picks / open questions: KEEP / IMPROVE / DROP per take.

## 2026-10-15 pass 832: Icon rings round 3   [status: WAITING]
- What: see the README. J: "R19f 11b only not completely boring ring faces".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\icon_rings3.blend (Cam row game)
- Review folder: docs/blender/review/832_icon_rings3/ (README.md)
- J's picks / open questions: KEEP / IMPROVE / DROP per take.

## 2026-10-15 pass 831: Worn ring round 3   [RATED; redone in 856]
- What: ring on the fist's punching face as in the jar; W4b's 135° rise with the back of the hand up and the fist bent
  back 45/75/105° so you see the ring while rising (W5a-c); new W2 effects instead of rays and smoke: halo, pixel motes,
  orbit motes (W2d-f). "MC FOV" dial for the first-person cameras. J: "W4b Rise 135 deg is good ... the hand should be
  turned more ... the light rays look bad too and the smoke".
- Open in Blender: C:\Users\Josh\Documents\LanternLive\combat\worn_ring3.blend (Cam W5b rise, fist back 75 - first person)
- Review folder: docs/blender/review/831_worn_ring3/ (README.md, sheet.png)
- J's picks / open questions: one W2 effect, one fist bend, the MC FOV number.


## 2026-10-15 pass 830: ring beam round 3   [PICKED: T2, T3, T4, T5, T6 KEEP; T1 variations in 840 (2026-10-15 review)]
- What: O4's spinning rims + O3's sparks, J's construct textures flowing along the sheath, and the glow drawn the way the
  game would (one camera-facing additive strip). T1-T6.
- Open in Blender: `combat\ring_beam3.blend` (Cam T5 close)
- Review folder: `docs/blender/review/830_ring_beam3/`; spec `specs/830.json`

## 2026-10-15 pass 829: eye beam chain (corner hunter through every target)   [WAITING]
- What: Z1 picked; "the pattern should continue from there and go through each target to the last, if it hits a player
  it does not continue through them". C1 four mobs, C2 stops at a player, C3 loop of five + glow.
- Open in Blender: `combat\eye_beam_chain.blend` (Cam C1 top)
- Review folder: `docs/blender/review/829_eye_beam_chain/`; spec `specs/829.json`

## 2026-10-15 pass 828: construct animals (pig, warden)   [PICKED: P2, P3 KEEP; R1, R2, R4 redone in 838]
- What: "stretch the textures over some animals too, just the construct textures and i want more example designs over a
  warden and pig". Pigs P1-P7, wardens R1-R6 (incl. a pulsing chest heart and two-tone designs).
- Open in Blender: `constructs\construct_animals.blend` (Cam row wardens)
- Review folder: `docs/blender/review/828_construct_animals/`; spec `specs/828.json`

## 2026-10-15 pass 827: corps suits round 3   [WAITING]
- What: C8 without the cape in three new shader materials (plated alloy, carbon weave, faceted crystal) with original
  helmets (sharp cowl, robot faceplate, visor and crest); C6b hex with gauntlets on both hands, no shoulder shield; C5b
  brick with C8's shoulders and no collar rings; C1b with C4's shoulders.
- Open in Blender: `suit\corps_suits3.blend` (Cam row R3)
- Review folder: `docs/blender/review/827_corps_suits3/`; spec `specs/827.json`
- J on 817: KEEP C4, C3, C2 and the hex suits.

## 2026-10-15 pass 826: the ultimate dome   [WAITING]
- What: from X2's oath: look up, a B1 beam to the sky for 2.5 s, then a construct dome that forms from the top (the
  bottom a little after) over 10 s and lasts 2.5 minutes. U1 radius 150, U2 radius 75, U3 ribs first.
- Open in Blender: `constructs\ultimate_dome.blend` (Cam U1 wide)
- Review folder: `docs/blender/review/826_ultimate_dome/`; spec `specs/826.json`
- Also 816 round 2: X4 now a light wave to 80 blocks (X4, X4b ground, X4c double); first person 120 deg with a
  crosshair; X1 wrist turn with a bracelet ring.

## 2026-10-15 pass 825: icon rings round 2   [PICKED: R19f KEEP; IMPROVE I1b, N1, R19e (2026-10-15 review)]
- What: "ripple should cover the key, get rid of 12, make 13 extend the ripple to the black sides, no black on the ring,
  delete 14 and revise design of face on R19d, then give me 7 more rings". I1b, I3b, R19e, R19f, N1-N7.
- Open in Blender: `lanterns\icon_rings2.blend` (Cam row game)
- Review folder: `docs/blender/review/825_icon_rings2/`; spec `specs/825.json`

## 2026-10-15 pass 824: flying mounts (horse, baby dragon, ghast)   [RATED; F1-F3 variations in 841; F4 still to do (2026-10-15 review)]
- What: "horse is the only flying construct i want right now ... a flying baby dragon to ride on and also a ghast
  construct (it needs to fit the real model)". F1 flying horse, F2 baby dragon, F3 ghast at real size over the real model,
  F4 harnessed ghast with four seats.
- Open in Blender: `constructs\flying_mounts.blend` (Cam F2)
- Review folder: `docs/blender/review/824_flying_mounts/`; spec `specs/824.json`

## 2026-10-15 pass 823: modern bows and bigger shields   [RATED; B1-B3, H2, H3 variations in 842 (2026-10-15 review)]
- What: "VERY in depth bow and arrow models, think modern day" and "the shield is too small". B1 compound, B2 Olympic
  recurve, B3 hunting compound, each shooting like a real bow (side-on, draw to the jaw, release, arrow to a target at
  18 blocks); H1 big hex, H2 tower, H3 dome wall. The rest of 808 is scrapped; the game's spear stays.
- Open in Blender: `combat\bows_shields.blend` (Cam B1 close)
- Review folder: `docs/blender/review/823_bows_shields/`; spec `specs/823.json`

## 2026-10-15 pass 822: snap launcher (catapult + ram boat)   [RATED; S1 redone in 857]
- What: the construct builds in one direction to the block the mob is about to step on, the mob snaps in, and letting
  go of right click launches it. S1 catapult cradle, S2 ram boat, S3 gold catapult.
- Open in Blender: `constructs\snap_launcher.blend` (Cam S1)
- Review folder: `docs/blender/review/822_snap_launcher/`; spec `specs/822.json`

## 2026-10-15 pass 821: construct mech suits   [RATED; MA, MC in 843; MS in 858]
- What: "mech suit needs a few design iterations as a big robotic suit, do one other size and a few animations for it,
  this may be a feature i can give to a villager or any kind of mob". MA Titan frame, MB Strider, MC Juggernaut, MS
  Compact (0.6 size); pilots: player, villager, zombie. Form, board, walk, punch, stomp.
- Open in Blender: `constructs\mech_suits.blend` (Cam MA)
- Review folder: `docs/blender/review/821_mech_suits/`; spec `specs/821.json`

## 2026-10-15 pass 820: zig-zag eye beams in the B1 look   [PICKED: Z1, chain in 829]
- What: "omega beams are the zig zag eye beams not this". Twin eye beams turning hard corners, built from B1 (core +
  sheath + rims): Z1 corner hunter, Z2 zig-zag, Z3 split, Z4 + glow.
- Open in Blender: `combat\eye_beams.blend` (Cam Z1 side)
- Review folder: `docs/blender/review/820_eye_beams/`; spec `specs/820.json`
- J's picks recorded: 807 KEEP L3 Core swirl; 806/819 are the ring beam; 808 scrapped (the game's spear stays; bow and
  shield redone in 823); 810 G3 + G4 combine into 822; the game's bubble needs physics/controls fixed (mc chat).

## 2026-10-15 pass 819: omega beam B1 family   [PICKED: O4 rims, O3 sparks; round 3 in 830]
- What: "B1 wins this one make more designs based off this, give it particles around it or some kind of glowing beam".
  O0 B1, O1 orbiting motes, O2 glow beam, O3 shedding sparks, O4 spinning rims, O5 all of it.
- Open in Blender: `combat\omega_beams2.blend` (Cam O5 close)
- Review folder: `docs/blender/review/819_omega_beams2/` (README.md, sheet.png)
- J on 806: KEEP B1 ("B1 wins this one").

## 2026-10-15 pass 818: worn ring round 2   [WAITING]
- What: W2 with a faint texture forming up the arm, plus W2a light rays, W2b smoke, W2c both. W3 scrapped ("the arm never
  goes up like that"); W4a/b/c rise only while holding space in flight, arm at 120/135/150 deg, looking down; first
  person shows the arm low in the frame and pointing up, with the top of the ring pulling you.
- Open in Blender: `combat\worn_ring2.blend` (Cam W2c rays and smoke - third person)
- Review folder: `docs/blender/review/818_worn_ring2/` (README.md, sheet.png)

## 2026-10-15 pass 817: corps suits round 2   [WAITING]
- What: "for these neon weave suits remove the chest band and give the hex suits the same treatment with all the lines on
  the chest and arms and hands, leave the legs, then give me several new designs". Row W: weave Knights, no chest band.
  Row H: hex suits with the Knight's chest, arms and hands, A1 legs. Row N: eight new designs C1-C8.
- Open in Blender: `suit\corps_suits2.blend` (Cam row N; Cam row W, Cam row H)
- Review folder: `docs/blender/review/817_corps_suits2/` (README.md, sheet.png)

## 2026-10-15 pass 816: ring-hand gestures round 2 (replaces 814)   [RATED; IMPROVE X1 (2026-10-15 review)]
- What: "the X4 ring the camera names need another description ... these animations were also subpar". Boards and
  collections say what each take is for; descriptive camera names; hands placed exactly (solver); wind-up, overshoot,
  settle; first person reframed; the ring is a darker green, at most 2.4 glow. X1 Cast, X2 Oath, X3 Focus, X4 Put the ring on.
- Open in Blender: `combat\ring_gestures2.blend` (Cam X4 Put the ring on - third person)
- Review folder: `docs/blender/review/816_ring_gestures2/` (README.md, sheet.png, gestures2_poses.json)
- J on 815: KEEP F1 construct shatter and F3 outline flash ("the outline flash is good the construct break is good").

## 2026-10-15 pass 815: hit effects   [PICKED: F1, F3 KEEP]
- What: construct shatter (F1), knockback shockwave (F2), outline flash (F3), all three (F4).
- Open in Blender: `combat\hit_effects.blend` (Cam F4)
- Review folder: `docs/blender/review/815_hit_effects/` (README.md, sheet.png)

## 2026-10-15 pass 814: ring-hand gestures   [OLD: redone as 816]
- What: X1 point to cast, X2 fist-raise oath, X3 ring to forehead, X4 power-up as the ring goes on; 1st + 3rd person.
- Open in Blender: `combat\ring_gestures.blend` (Cam X1)
- Review folder: `docs/blender/review/814_ring_gestures/` (README.md, sheet.png, gestures_poses.json)

## 2026-10-15 pass 813: corps suits   [WAITING]
- What: "the armour designs in Red, Yellow, Violet, Blue and Orange textures": A1 Plates (H1), A2++ Heavy (BR1), A4 Knight (W1) per corps, from the texture library.
- Open in Blender: `suit\corps_suits.blend` (Cam row Red)
- Review folder: `docs/blender/review/813_corps_suits/` (README.md, sheet.png)

## 2026-10-15 pass 812: enemies   [RATED; E2, E3 DROP; E1 variations in 845]
- What: original Dread Wisp (fear), Ember Brute (rage), Leech Mite (parasite); idle, attack and death each.
- Open in Blender: `combat\enemies.blend` (Cam E1)
- Review folder: `docs/blender/review/812_enemies/` (README.md, sheet.png)

## 2026-10-15 pass 811: lantern shrine   [WAITING]
- What: S1 charging altar, S2 lantern tower, S3 pillar ring; the glow climbs each build as the charge rises.
- Open in Blender: `lanterns\lantern_shrine.blend` (Cam S1)
- Review folder: `docs/blender/review/811_lantern_shrine/` (README.md, sheet.png)

## 2026-10-15 pass 810: big constructs   [WAITING]
- What: G1 giant fist, G2 cage bubble, G3 catapult, G4 battering ram, G5 mech suit, forming pixel by pixel.
- Open in Blender: `constructs\big_constructs.blend` (Cam G1)
- Review folder: `docs/blender/review/810_big_constructs/` (README.md, sheet.png)

## 2026-10-15 pass 809: construct mounts   [OLD: horse kept as the flyer, redone in 824]
- What: V1 jet, V2 motorbike, V3 horse, V4 dragon in J's textures (H1, W1, BR1, X3D1).
- Open in Blender: `constructs\construct_vehicles.blend` (Cam V4)
- Review folder: `docs/blender/review/809_construct_vehicles/` (README.md, sheet.png)

## 2026-10-15 pass 808: construct weapons   [SCRAPPED: bow + shield redone in 823]
- What: K1 bow, K2 shield, K3 spear, K4 whip, K5 chain, K6 gauntlet: each forms from the ring, then acts on a dummy.
- Open in Blender: `combat\construct_weapons.blend` (Cam K1)
- Review folder: `docs/blender/review/808_construct_weapons/` (README.md, sheet.png, weapons_poses.json)

## 2026-10-15 pass 807: finished lantern charge   [PICKED: L3 KEEP]
- What: "the glow from the lantern charge should be much better by now": L1 port spread, L2 band climb, L3 core swirl on G3b timing.
- Open in Blender: `lanterns\charge_final.blend` (Cam L1 close, Rendered view)
- Review folder: `docs/blender/review/807_charge_final/` (README.md, sheet.png)

## 2026-10-15 pass 806: solid omega beams   [PICKED: B1, more in 819]
- What: "the omega beams are very particle-y and hard to see": B1 core + sheath, B2 pulsing rings, B3 twin braid + sparks, all geometry.
- Open in Blender: `combat\omega_beams.blend` (Cam B1 side)
- Review folder: `docs/blender/review/806_omega_beams/` (README.md, sheet.png)

## 2026-10-15 pass 805: worn ring   [WAITING]
- What: "the ring should stay on when wearing it": W1 idle, W2 charge pulse up the arm, W3 equip power-up; 1st + 3rd person.
- Open in Blender: `combat\worn_ring.blend` (Cam W3 third person)
- Review folder: `docs/blender/review/805_worn_ring/` (README.md, sheet.png)

## 2026-10-15 pass 804: ring matching the hotbar icon   [OLD: J's notes into 825]
- What: "why dont i have a ring that looks accurately like the one in my item bar": I1–I4 icon heads on R19d's band, or icons N1–N3 showing R19d.
- Open in Blender: `lanterns\ring_icon_match.blend` (Cam row game)
- Review folder: `docs/blender/review/804_ring_icon_match/` (README.md, sheet.png, icon_r19d_n1-3.png, icons_preview.png)

## 2026-10-14 pass 803: first-person tools round 2, edge leads, combos, construct hammer   [RATED; S1 DROP; IMPROVEs redone as variations in 844]
- What: J's notes on 802 (axe angle, flat hammer, pickaxe use, S2 diagonal with the edge, thrust back-then-forward,
  shovel, combos). The tool now turns about its length every tick so its edge/point/face leads the motion; arms reach;
  the hammer is a solid construct hammer. S1, S2, S3, S4, C1, C2 sword; P1, A1, V1, O1; H1, H2 hammer.
- Open in Blender: `combat\fp_tools2.blend` (Cam C1, play; Cam <take> / Cam <take> side)
- Review folder: `docs/blender/review/803_fp_tools2/` (README.md, sheet.png, fp_tools2_poses.json)

## 2026-10-15 pass 521: grab and throw, construct hand (G1 reach and fling, G2 overhead whip, G3 spin throw)   [WAITING]
- What: a construct hand forms from the ring, reaches 6 blocks on a tether, grabs, and throws the mob along the
  crosshair (12 deg off the mob line) into a wall: 3x3 crater on the D0 timing, mob stuck in the hole.
- Open in Blender: `LanternLive\combat\grab_throw.blend` (start on "01 Reach and fling - 3rd person")
- Review folder: docs/blender/review/521_grab_throw/ (README.md, sheet.png, grab_throw_poses.json)
- J's picks: G1 / G2 / G3.

## 2026-10-15 pass 602: lantern set-down, kneel and place (D1 deliberate, D2 quick, D3 seal)   [WAITING]
- What: the missing set-down (J picked "Kneel and place"): carry by the handle, kneel, lower until the base touches,
  it rights itself, let go, stand. D3 rests the ring hand over it and lights it. 3rd person, side and 1st person cameras.
- Open in Blender: `LanternLive\lanterns\lantern_set_down.blend` (start on "01 Set down deliberate - 3rd person")
- Review folder: docs/blender/review/602_lantern_set_down/ (README.md, sheet.png, lantern_set_down_poses.json)
- J's picks: D1 / D2 / D3.

## 2026-10-15 pass 520: first-person versions of the moves, vanilla and bigger   [WAITING]
- What: first-person arms for the moves that had none (catalogue 519): flurry F2, flying flurry, big slam S3, primed
  slams P1/P2, slide U1, take-off F2, double jump S1 and running A2, sprint with the lantern S5a, ring arm leading D1.
  Each move comes in two styles (vanilla size, and 1.3x bigger and closer). The camera rides the eyes of the 3rd-person take.
- Open in Blender: `LanternLive\first_person_moves.blend` (cameras "NN <move> - vanilla" / "NN <move> - bigger")
- Review folder: docs/blender/review/520_first_person_moves/ (README.md, sheet.png, first_person_moves_poses.json in
  RingFirstPerson terms: fist, elbow, back of hand, view space)
- J's picks: vanilla or bigger; KEEP / IMPROVE / DROP per move.

## 2026-10-14 pass 519: animation catalogue, every picked animation in 3rd and 1st person   [WAITING: J's report]
- What: all picked/in-game animations (movement, lantern, combat; 36 takes) replayed from their poses JSON, each with a
  3rd-person follow camera and a 1st-person eye camera (arms + ring + lantern only, as Minecraft draws it). Ring-arm
  visibility from the eyes is measured per take: most movement and flurry/slam takes have no first person (0-2%).
- Open in Blender: `LanternLive\animation_catalogue.blend` (cameras "Cam <id> 3p" / "Cam <id> fp", "Cam overview")
- Review folder: docs/blender/review/519_animation_catalogue/ (README.md table, sheet.png, fp_visibility.json)
- Lantern true size: 16 px tall with handle (6.2 px wide). In game it is drawn far bigger when set down (J: "Lantern too big").
- J's picks: report per take (3p OK / fp needed / mismatch); then first-person versions for the 0% takes.

## 2026-10-14 pass 802: first-person construct tool animations (sword x4, pickaxe, axe, shovel, hoe, hammer x2)   [OLD: J's notes -> 803]
- What: J wants the first-person tool animations reworked; the tool forms pixel by pixel from the ring, then swings.
  Sword S1 fast slash, S2 heavy chop, S3 sweep pair, S4 thrust; P1 pickaxe, A1 axe, V1 shovel, O1 hoe, H1 hammer
  overhead, H2 hammer from the side. Ring stays on the right hand. Per-tick poses in the JSON.
- Open in Blender: `combat\fp_tools.blend` (Cam S1, play; Cam <take> / Cam <take> side)
- Review folder: `docs/blender/review/802_fp_tools/` (README.md, sheet.png, fp_tools_poses.json)
- Game side (sent separately): tools go into the hotbar as items instead of being forced; a ring slot for the right
  hand; the back-hand fist hits.

## 2026-10-14 pass 801: four rings into the game (R19d; R12b, R12c, R16a without icons)   [HANDED OFF]
- What: J: "put r19d in game remove the icon on r16a just do no icons" and "put these two in as well" (R12c, R12b).
  Then "remove the crowns and send them to be put in game": R12b/R12c now plain. Blockbench models exported straight
  from the Blender builds (tools/ring_voxels_bbmodel.py), 276-410 cubes each.
- Open in Blender: `lanterns\rings_in_game.blend` (Cam row game)
- For the game: `docs/handoff/2026-10-14-rings-in-game/` (README.md, assets/bbmodel, assets/textures, preview.png)

## 2026-10-14 pass 601: lantern charge in 6 seconds   [WAITING]
- What: J "a much shorter charge animation now maybe 6 seconds". L1c retimed to 120 ticks; C6a fill 4 s / overcharge
  1 s / let-go 0.5 s, C6b 4.5/0.6/0.4, C6c 3.3/1.5/0.75.
- Open in Blender: C:\Users\Josh\Documents\LanternLive\lanterns\lantern_charge6.blend (Cam C6a, frames 1-120)
- Review folder: docs/blender/review/601_lantern_charge6/

## 2026-10-14 pass 518: primed slams (shift / crouch), instant craters, rebuild by left click, slide trench   [PICKED: P1, U1 KEEP; IMPROVE P2 (2026-10-15 review)]
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

## 2026-10-14 pass 598: classic-shaped ring, diamond-shiny, four original marks   [SCRAPPED by J 2026-10-15]
- What: J asked for "a classic green lantern ring ... shiny ... like diamond surface". The published ring and emblem
  are not copied; J chose new original marks (Lantern, Flame, Oath star, Rising chevrons), each light-cut or gold inlay,
  with N04's light lines. Also: 597 rebuilt with the ripple centred on the face (J).
- Open in Blender: `lanterns\classic_ring.blend` (Cam C01 Lantern light-cut, play); `lanterns\square_ring_tex.blend`
- Review folder: `docs/blender/review/598_classic_ring/` (README.md, sheet.png)

## 2026-10-14 pass 597: square emblem ring wearing our animated textures   [SCRAPPED by J 2026-10-15]
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

## 2026-10-14 pass 515: super-speed flight on left click   [PICKED: S2, S3 KEEP (2026-10-15 review)]
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

## 2026-10-14 pass 505: dash strike round 5 (faster, arms drop after)   [PICKED: R3a-3 KEEP (2026-10-15 review)]
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

## 2026-10-14 pass 502: combat poses round 4 (P1 punches, P2 blast, P4 beam loops, P5 wall, P6 slam)   [PICKED: P1b, P1c, P2b, P5a KEEP; IMPROVE P1a, P2a (2026-10-15 review)]
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
## 2026-10-15 pass 406: ring arm lead on the upright slow-flight body   [WAITING]
- What: 404's arm rule (D1, D3) on the upright 20° slow-flight body, so J can judge the arm on the body the game uses
  when flying slowly (the "arm above the head" in 404 was the flat sprint glide). U1 pure lead, U3 lead + bank.
- Open in Blender: `C:\Users\Josh\Documents\LanternLive\arm_lead_upright.blend` (Cam U1, frames 1-130)
- Spec `specs/406.json` (no review folder).

## 2026-10-14 pass 405: double-tap landing, tighter and faster   [HANDED OFF: L4 KEEP at 0.3 blocks of carry; L2/L5/L6 DROP; docs/handoff/2026-10-15-movement-keeps/]
- What: J tested L2 in game: it couldn't be triggered while moving forward, and it carried a few blocks. Now: brake on
  the tap and drop straight in. L4 0.8 blocks/0.30 s, L5 0.4/0.25 s, L6 0/0.20 s (L2 was 8.1/0.60 s). No run-out. Game
  fix: sneak and the double tap work in flight while moving.
- Open in Blender: `LanternLive\movement\land_tight.blend` (Cam L5 close, frames 14-32)
- Review folder: `docs/blender/review/405_land_tight/`; the bundle build order is updated.

## 2026-10-14 pass 404: ring arm leads where you fly (0.08 s)   [HANDED OFF: D1 default, D3 option; D2 DROP; docs/handoff/2026-10-15-movement-keeps/]
- What: the ring arm points along the movement direction (flat ahead when level, not up past the head; raised in a
  climb, lowered in a dive, swung into turns) and the body follows 0.08 s (1.6 ticks) later. D1 pure lead, D2 lead +
  anticipation, D3 lead + 35 degree bank. J: "arm leading the body by like .08s". J also picked L2 (pass 403 landing).
- Open in Blender: `LanternLive\movement\arm_lead.blend` (Cam D1, Cam D1 close)
- Review folder: `docs/blender/review/404_arm_lead/`
- Open: D1/D2/D3; free arm A1/A2/A3; standing S1/S2a/S2b.

## 2026-10-14 pass 403: double-jump take-off round 2 + double-tap soft landing   [OLD: R3A3 dropped ("Drop it"); S2a redone at 2.2 in 407]
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
## 2026-10-14 pass 305: smoke rays with more detail   [PICKED: D2 KEEP (2026-10-15 review)]
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
