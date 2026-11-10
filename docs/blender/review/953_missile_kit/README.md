# Pass 953: construct missile kit, a barrage from above, five explosions

J, 2026-11-09: "I want a missile set built that will rain in from above and some explosion animations modeled for me";
"do the missiles in a single pass here, different detail portions and let me mix and match ... so i can mix match
compare contrast and decide which pieces look how and which to refine and build another 3 variations of given my
choices".

**Open:** `C:\Users\Josh\Documents\LanternLive\constructs\953_missile_kit.blend`, camera `1 Mix - side`, frames 1-140.
**Script:** `docs/blender/blender_updates/953_missile_kit.update.py`.

## Mix and match

Properties editor > Scene tab > Custom Properties. One slider per portion; the mix missile, all 14 barrage missiles and
every impact follow them.

| Slider | Options |
|---|---|
| nose | 1 = N1 Ogive, 2 = N2 Sharp cone, 3 = N3 Blunt dome, 4 = N4 Seeker eye, 5 = N5 Penetrator spike |
| body | 1 = B1 Banded tube, 2 = B2 Conduit and panels, 3 = B3 Two-stage, 4 = B4 Carrier box |
| fins | 1 = F1 Cruise wings, 2 = F2 Delta fins, 3 = F3 Grid fins, 4 = F4 Canards and tail, 5 = F5 Strakes only |
| engine | 1 = G1 Bell nozzle, 2 = G2 Air-breather, 3 = G3 Four nozzles, 4 = G4 Petal tail |
| trail | 1 = T1 Solid beam, 2 = T2 Pixel smoke, 3 = T3 Corkscrew, 4 = T4 Jagged lightning |
| explosion | 1 = E1 Ground burst, 2 = E2 Airburst and embers, 3 = E3 Penetrator plume, 4 = E4 Cluster carpet, 5 = E5 Lightning scorch |
| missile_size | barrage missile size: 1 = real (6 blocks long, half a block across), default 2 |

That is 5 x 4 x 5 x 4 x 4 = 1,600 missiles, times 5 explosions.

## The options

- **N1**: rounded ogive, dark base band, yellow-green stripe
- **N2**: long sharp cone, dark heat tip
- **N3**: short blunt radar dome
- **N4**: dark collar, glowing glass seeker dome
- **N5**: thin dark rod with a bright point, for digging in
- **B1**: plain tube, two dark bands, one stripe
- **B2**: panel rings, a conduit along the top, two hatches
- **B3**: fat booster stage, taper, slim front
- **B4**: square carrier with door seams (pairs with E4)
- **F1**: long straight mid wings with tipped ends + four small tail fins
- **F2**: four big delta fins at the tail
- **F3**: four lattice grid fins on stubs
- **F4**: small canards up front + four trapezoid tail fins
- **F5**: four low strakes and a ring (ballistic)
- **G1**: flared bell with a glowing core
- **G2**: belly intake scoop, boat tail, small nozzle
- **G3**: four small bells
- **G4**: tapered tail with four petals
- **T1**: straight tapering beam, darker core
- **T2**: pixel puffs growing and darkening behind
- **T3**: double corkscrew
- **T4**: jagged bolt
- **E1**: instant scorch, dome to 6 blocks in 3 ticks, shock ring to 12, 12 debris pixels
- **E2**: bursts 9 blocks up: ball to 5, flat ring to 10, 22 embers drifting down for 34 ticks
- **E3**: small entry, then 6 ticks later a 20-block plume, ring, debris
- **E4**: nine small bursts walking across 8 blocks, 1.5 ticks apart
- **E5**: four bolts flicker twice, low dome, ring to 10, wide scorch

## Cameras

`1 Mix - side`, `2 Mix - three-quarter`; `3 N1 Ogive - shelf` ... `24 T4 Jagged lightning - shelf` (one per option, on
a shelf with its name; fins and engines sit on a plain B1 body); `25 E1 Ground burst - shelf` ... `29 E5 Lightning
scorch - shelf` (go off at frames 10 and 80); `30 Barrage - wide`, `31 Barrage - ground level`, `32 Barrage - from above`.

## Check

- Sliders tested headless: four different mixes rendered, parts swap on the mix and in the barrage.
- Explosions: no wind-up; the scorch mark is there on the contact tick; emission 1.0 (saturated, not mint).
- Missiles fly 60 blocks a second (3 a tick), 30 ticks from first sight to impact.
- E2 bursts 9 blocks up; in this file the missile still flies to the ground first (the game would stop it at 9).

## For the game (not built yet)

Nothing here is in the jar. Next round after J's picks: 3 variations of each portion he keeps.
