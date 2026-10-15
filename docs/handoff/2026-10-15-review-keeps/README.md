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
