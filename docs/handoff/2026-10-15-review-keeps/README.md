# Build order: J's KEEPs from the review site, 2026-10-15

For the mc project chat. J rated these KEEP on https://lantern-review-j.vercel.app (full table: `docs/blender/review/RATINGS.md`).
Each pass's review folder has the exact numbers, poses and materials; the update script rebuilds the take in Blender.
Build the KEEPs as Ring Lab options (the first KEEP of a pass as the default unless the line says otherwise), never
overwriting J's saved Ring Lab choices. Name the pass in each commit subject ("pass 837") so the review site's
"In the game" panel finds it. Already in the jar: 407 (see `docs/handoff/2026-10-15-movement-keeps/` section 4).

## Pass 837: Eye beam chain round 3
- Review folder: `docs/blender/review/837_eye_beam_chain3/`; script `docs/blender/blender_updates/837_eye_beam_chain3.update.py`
- **R4** E3 look, k 0.45: faster: 0.45 x distance; pulse glow + sparks; hits 24/31/43/57
- Dropped: R1, R2, R3

## Pass 834: A new laser
- Review folder: `docs/blender/review/834_laser/`; script `docs/blender/blender_updates/834_laser.update.py`
- **L1** hard-light lance: thin core, streak glow flowing to the target, haze, flares at ring and hit
- **L2** construct lance: core, your hex construct texture flowing on the glow, haze, flares
- Not yet (IMPROVE, a new round first): L0, L3
- Dropped: L4

## Pass 830: Ring beam round 3
- Review folder: `docs/blender/review/830_ring_beam3/`; script `docs/blender/blender_updates/830_ring_beam3.update.py`
- **T2** brick flow + sparks: brick flow + sparks
- **T3** weave flow, thicker rims: weave flow, thicker rims
- **T4** ripple flow + game glow: ripple flow + game glow
- **T5** hex flow + sparks + game glow: hex flow + sparks + game glow
- **T6** double helix + R2 flow + sparks: double helix + R2 flow + sparks
- Not yet (IMPROVE, a new round first): T1

## Pass 828: Construct animals: pig and warden
- Review folder: `docs/blender/review/828_construct_animals/`; script `docs/blender/blender_updates/828_construct_animals.update.py`
- **P2** pig H1 hex: pig H1 hex
- **P3** pig W1 weave: pig W1 weave
- Not yet (IMPROVE, a new round first): R1, R2, R4
- Dropped: P1, P4, P5, P6, P7, R3, R5, R6

## Pass 518: Primed slams, instant craters, rebuild by left click, slide trench
- Review folder: `docs/blender/review/518_primed_slam/`; script `docs/blender/blender_updates/518_primed_slam.update.py`
- **P1** Primed flight slam (shift): locked at tick 18, lands tick 30, 7x7 crater opens at once, lining 3 s, rebuild ripple from your look at tick 70
- **U1** Unprimed slide: lands tick 30, slides 5 blocks on one knee, trench 3 wide x 6 long, lining one block out all round for 2 s
- Not yet (IMPROVE, a new round first): P2

## Pass 515: Super-speed flight on left click
- Review folder: `docs/blender/review/515_super_speed/`; script `docs/blender/blender_updates/515_super_speed.update.py`
- **S2** Tap burst: tap: straight to 60 b/s with a sonic boom ring + 16 pixels, holds 2 s, eases back
- **S3** Ramp then dive into the slam: S1 ramp, climb to 16 blocks, hard dive; slam trigger height max(5, 3 x fall per tick) -> S3 M3 slam, 7x7 crater, 0.7 s lock
- Dropped: S1

## Pass 505: Dash strike round 5: faster, arms drop after
- Review folder: `docs/blender/review/505_dash_strike5/`; script `docs/blender/blender_updates/505_dash_strike5.update.py`
- **R3a-3** Dash strike R3a-3, flying ring fist: 3-tick dash (27 b/s), dash starts frame 11, punch lands as it ends
- Dropped: R3a-4, R3a-6, R3c-4, R3c-6

## Pass 502: Combat poses round 4 (punches, blast, beam loops, wall, slam)
- Review folder: `docs/blender/review/502_combat_poses4/`; script `docs/blender/blender_updates/502_combat_poses4.update.py`
- **P1b** Step-in jab: 0.45-block step in; 40-tick seamless loop
- **P1c** Hook: hook punch; 40-tick seamless loop
- **P2b** Blast, free hand 25%: follows recoil 25%; 40-tick seamless loop
- **P5a** Wall, free arm relaxed: only the ring arm sweeps up; 40-tick seamless loop
- Not yet (IMPROVE, a new round first): P1a, P2a
- Dropped: P2c, P4a, P4b, P4c, P5b, P5c, P6a, P6b, P6c

## Pass 305: Smoke rays with more detail
- Review folder: `docs/blender/review/305_smoke_rays_detail/`; script `docs/blender/blender_updates/305_smoke_rays_detail.update.py`
- **D2** Shafts+: L2 shafts with the detail
- Dropped: D1, D3, D3c

# Added 2026-10-15 09:35 (J's later KEEPs)

## Pass 602: Lantern set-down
- Review folder `docs/blender/review/602_*`; **D1** and **D2** KEEP (D1 default, D2 option); D3 gets a new round first.

## Pass 701: Texture close-ups (construct looks)
- **BRE, H1, HW, W1** KEEP as construct looks in the Ring Lab; BRJ gets a red test first; BRL, H2, W1E dropped.

## Pass 519: Animation catalogue
- J confirmed in-game animations A3, B2, D1, D3, K3c, K3cR, P1, S5a (KEEP). Already in the game: no change unless they differ from the jar.

# Added 2026-10-15 18:20 (J's KEEPs from the 17:48 renders)

## Pass 701: Skin workshop close-ups, animated
- **BRJR** BR1 bricks in red
- **BRN** BR1 neon bricks
- **T9** T9 barrier

## Pass 838: Warden construct armour
- **R4b** W1 weave plate armour

## Pass 840: Ring beam: T1 variations
- **T1b** hex collars + trailing sparks
- **T1c** hex screw + impact fountain

# Added 2026-10-15 19:20

## Pass 844: First-person tools: variations
- **S3b** Sword: stepping wide sweep pair

(701 BRD moved back to IMPROVE: not in the build order.)

# Status 2026-10-15 22:00 (mc build chat): PR #339, branch claude/review-keeps-2, waiting on J to merge

Built and screenshot-tested in the game, not yet in the jar until #339 is merged:
- **840 T1b, T1c**: Ring Lab > Beam look, "T1b hex collars + trailing sparks", "T1c hex screw + impact fountain".
- **701 BRE, BRN**: Construct look "BR1 bricks emerald / neon". **BRJR**: Red constructs "BRJR BR1 bricks in red"
  (`tools/br1_red_strip.py`). H1, HW, W1 and T9 were already in.
- **838 R4b**: new row Construct warden (R4b default; "Hard-light warden" keeps the old look). Real warden under W1 weave
  plates, forming feet first in 1 s (`WardenArmourModel`, test `WardenArmourTest`).
- **844 S3b**: construct sword in first person on the 844 rig: extrudes from the ring fist behind a scan plate, rests
  upright, each swing is the sweep pair; the backswing hits again 5 ticks after a landed hit (`SwordSwing`,
  `SwordSweeps`, test `SwordSwingTest`). Seen at the game's 70 degree hand FOV, so the wide sweeps leave the screen
  sooner than in the 120 degree Blender camera.
- The 602 and 844 Blender scripts run headless here (bpy 5.0 in a Python 3.11 venv via uv; 602 needs
  `kl_assets/dark_lantern*.glb` from `docs/blender/models/`, 844 the `construct_*_green.bbmodel` files).

Still open: **602 D1/D2 set-down**: not built yet. Question for J: what should play it in game (placing the lantern
block from your hand is the guess)?

# Added 2026-10-15 22:56

## Pass 703: BRD bricks and X5E ripples (3 each)
- **BRDa** BRD neon bricks - carved
- **BRDb** BRD neon bricks - brushed alloy
- **BRDc** BRD neon bricks - dark gunmetal

## Pass 852: First-person tools: round 4 variations
- **P1b3** Pickaxe: strike, lever back, rip a chunk out
- **S2a1** Sword: heavy shoulder diagonal after a held charge
- **S2b1** Sword: reverse diagonal from high over the left shoulder
- **S2b2** Sword: reverse diagonal, step in, wrist turns flat to edge
- **S2c1** Sword: slow heavy X, a charge before each cut
- **S3a1** Sword: high sweep pair after a charge, stepping
- **S3a2** Sword: higher sweep pair, blade rolls over between
- **S3c2** Sword: three sweeps at three heights, high to low
- **S3c3** Sword: three wide sweeps, a step on each


# Added 2026-10-16 01:30

## Pass 856: Worn ring round 4
- **W5a4** rise, fist back 65
- **W5b1** rise, fist back 75 to 65

