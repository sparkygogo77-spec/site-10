# Super jump: Ring Lab test rows for J's Blender picks

**To the coordinator, from the super jump Blender chat.**

J wants to pick the last super jump choices by playing, not in Blender. Please add them as Ring Lab rows on the super jump branch (`claude/project-thread-mt98dl`), each one with KEEP / IMPROVE / DROP like the other rows.

The Blender source is passes 81–84 on `claude/lantern-redesign-pass2` (`docs/blender/blender_updates/8x_*.update.py`). The pose data is in `docs/blender/super_jump_poses.json` and `docs/blender/super_jump_landings2_poses.json`.

## Rows to add

| Row key | Values (first = default) | Side | What it switches |
|---|---|---|---|
| `super_fall_arm` | `D1A`, `D1B`, `D1C` | client | The ring arm while falling. D1A points straight down at the ground, D1B points ahead at the landing spot, D1C points down and a little out. |
| `super_landing` | `E1`, `E2` | client | The landing pose. E1 is Take 1's three-point landing (ring foot forward, back knee down). E2 is Take 2's wide slam. In both, the ring fist is on the ground. |
| `super_wall` | `W2`, `W1`, `W3`, `OFF` | client | The small construct wall around the landing pad. W1 is 8 px thick × 8 px high (a slab). W2 is 3 px × 8 px (trapdoor thin). W3 is 1.5 px × 6 px (half a trapdoor). |
| `super_crater` | `SURFACE`, `PRIMED_ONLY` | server | `SURFACE` blasts a crater on every landing, shaped by what you land on (see below). `PRIMED_ONLY` is today's behaviour. |

The pad and wall should take their texture from the existing **Construct look** and **Wall look** rows, so J tests textures through those rows. The pad uses the construct look; the wall uses the wall look.

## Poses

Replace the placeholders in `SuperJumpPoses.java` with these. The values are model rotations in radians, as (xRot, yRot, zRot), followed by `+(x, y, z)`, which is added to the part's default position in model px. The default positions are:
- head and body at (0, 0, 0);
- arms at (∓5, 2, 0);
- legs at (∓1.9, 12, 0).

The ring arm is `rarm` and its leg is `rleg` (right-handed). For a left-handed player:
- swap the arms and the legs;
- negate yRot and zRot;
- negate the x offsets.

| Pose | head | body | ring arm | free arm | ring leg | free leg |
|---|---|---|---|---|---|---|
| A1 wind-up (full) | (-0.55, 0, 0) +(0, 5.93, -6.27) | (0.55, 0, 0) +(0, 5.93, -6.27) | (1.15, 0, 0.25) +(0, 5.63, -5.23) | (-0.75, -0.35, 0.15) +(0, 5.63, -5.23) | (-0.55, 0, 0.2) +(0, 0.16, 0) | (0.45, 0, -0.15) +(0, 0.16, 0) |
| B1 launch | (-0.4, 0, 0) +(0, 0.01, 0.6) | (-0.05, 0, 0) +(0, 0.01, 0.6) | (0.75, 0, 0.15) +(0, 0.01, 0.5) | (0.75, 0, -0.15) +(0, 0.01, 0.5) | (0.15, 0, 0.03) | (0.15, 0, -0.03) |
| C1 rising | (-0.45, 0, 0) +(0, 0.04, 0.96) | (-0.08, 0, 0) +(0, 0.04, 0.96) | (-3.05, 0, 0.05) +(0, 0.03, 0.8) | (0.35, 0, -0.12) +(0, 0.03, 0.8) | (-0.95, 0, 0.05) | (0.3, 0, -0.02) |
| D1a fall | (0.3, 0, 0) +(0, 0.37, -2.97) | (0.25, 0, 0) +(0, 0.37, -2.97) | (-0.15, 0, 0.05) +(0, 0.31, -2.47) | (-0.35, 0, -1.1) +(0, 0.31, -2.47) | (-0.45, 0, 0.08) | (0.35, 0, -0.08) |
| D1b fall | same as D1a, except: | | (-0.75, 0, 0.12) +(0, 0.31, -2.47) | | | |
| D1c fall | same as D1a, except: | | (-0.3, 0, 0.4) +(0, 0.31, -2.47) | | | |
| E1 landing | (-0.7, 0, 0) +(0, 12.29, -8.18) | (0.75, 0, 0) +(0, 12.29, -8.18) | (-0.36, 0, 0.12) +(0, 11.76, -6.82) | (1.3, 0, -0.5) +(0, 11.76, -6.82) | (-1.3, 0, 0.1) +(0, 3.7, 0) | (1, 0, -0.08) +(0, 3.7, 0) |
| E2 landing | (-0.9, 0, 0) +(0, 12.5, -9.76) | (0.95, 0, 0) +(0, 12.5, -9.76) | (-0.36, 0, -0.05) +(0, 11.66, -8.13) | (0.45, 0, -1.2) +(0, 11.66, -8.13) | (-0.8, 0, 0.5) +(0, 2.2, 0) | (0.8, 0, -0.4) +(0, 2.2, 0) |
| E3 deep landing | (-0.5, -0.2, 0) +(-1.68, 12.73, -6.57) | (0.6, 0.25, 0) +(-1.68, 12.73, -6.57) | (-0.37, 0, 0.45) +(-1.24, 12.38, -4.23) | (0.9, 0, -0.25) +(-1.55, 12.38, -6.71) | (-1.45, 0, 0.15) +(0, 5.11, 0) | (1.15, 0, -0.1) +(0, 5.11, 0) |
| F2 stand-up (E2's) | (-0.3, 0, 0) +(0, 2.18, -4.11) | (0.35, 0, 0) +(0, 2.18, -4.11) | (0.4, 0, 0.2) +(0, 2.06, -3.43) | (0.5, 0, -0.3) +(0, 2.06, -3.43) | (-0.5, 0, 0.08) | (0.35, 0, -0.05) |
| F3 stand-up (E3's) | (-0.2, 0, 0) +(0, -0.1, 1.44) | (-0.12, 0, 0) +(0, -0.1, 1.44) | (-0.3, 0, 0.1) +(0, -0.11, 1.2) | (0.2, 0, -0.15) +(0, -0.11, 1.2) | (0.05, 0, 0.06) | (0.05, 0, -0.06) |

In the landing poses the whole model also sits lower:
- E1: the legs and everything above them drop 3.7 px (already in the leg offsets above);
- E2: 2.2 px;
- E3: 5.1 px.

E1's stand-up (F1) has no halfway pose; it is an eased blend straight back to idle.

## Timing and blends (ticks)

- **Wind-up:**
  - the pose is at 35% when the jump arms;
  - it reaches 100% at full charge;
  - smoothstep easing;
  - at full charge the ring arm trembles slightly: xRot ±0.03, zRot ±0.02.
- **Launch:** 5 ticks of B1, blending in over 2.
- **Rising:**
  - blend into C1 over 3 ticks;
  - from 45% of the way up, ease both arms toward the fall arms (D1a/b/c), arriving at the apex. J: "the hand shouldn't stay up the entire way";
  - the body and legs stay in C1 until the apex.
- **Falling:** from the apex, blend into the D pose over 8 ticks.
- **Landing:**
  - blend into E over 2 ticks;
  - hold for 16 ticks;
  - stand up over 8 ticks: E → F (halfway) → idle.

## The deeper fall → E3

When you land more than 6 blocks below your take-off height (you jumped into a hole deeper than you meant):
- use E3 instead of the picked landing;
- hold for 30 ticks;
- use F3 for the stand-up;
- use the deep crater and the tall guard walls below.

## Craters by surface (`super_crater SURFACE`)

**Shape.** The crater is a stepped bowl. Each layer down has its own radius:

| Surface | Layer radii (top first) | Debris |
|---|---|---|
| grass / dirt (default) | 3.0, 1.7 | dirt chunks |
| stone and other stone-like blocks | 2.2, 1.1 | sparks + stone chips |
| sand / gravel | 3.6, 2.3 | sand spray (lots of small grains; J: "excellent") |
| water (feet in or on water) | no crater | a construct pad on the water, radius 2.2 |
| deeper fall | 4.6, 3.8, 2.8, 1.6 | dirt, stone |

**Scaling.** Scale the radii by `clamp(drop / 28, 0.7, 1.5)`, where drop is the fall height. Keep the existing rules: unbreakable blocks, containers and constructs stay. Scorch still runs afterwards.

**Timing.** Carve the crater one tick **before** touchdown: the first tick the player is within 2 blocks of the ground and falling faster than 1 block a tick. That way the player lands on the crater floor instead of hovering over it and then dropping in.

**Blasted blocks.** Throw them up and out:
- launched from where they were, starting at their distance × 0.5 ticks after touchdown;
- out 0.05–0.09 blocks a tick, up 0.12–0.26 a tick;
- falling under normal gravity;
- shrinking away over 10 ticks.

They can be falling-block-style particles, or entity displays that you clean up.

## The landing construct (client-side visuals, like `RAM_BARRIER`)

- **Pad.** Thin construct plates, 3 px thick, lie on the crater floor under the player, out to radius 1.6, following the floor's steps.
  - On water the radius is 2.2; on a deeper fall it is 2.3.
  - Each plate switches on as the impact wave reaches it: delay = distance × 0.8 ticks.
  - It flares briefly as it forms.
- **Wall.** The `super_wall` wall stands along the pad's outer edge. It rises out of the ground over 4 ticks.
- **Deeper fall: guard walls.** Instead of the low wall, a ring of guard walls rises around the pad's edge:
  - 3 px thick and 2.6 blocks high;
  - they rise over 7 ticks, overshooting 0.12 blocks before settling;
  - they hold through the landing.
- **Fading.** After the stand-up, every piece dissolves at its own random moment, using the dissolve J picked for constructs going away.
  - Normal: between stand-up + 4 and + 16 ticks.
  - Deep: between + 6 and + 20.
  - The crater stays.
- **Glow.** Low, in jade:
  - surface colour (0.07, 0.42, 0.24);
  - emission (0.06, 0.5, 0.28) at low strength;
  - about 70% opaque.

## J's landing picks (in game, 2026-10-14)

- **Landing pose: E2** (Take 2's wide slam), ring fist on the ground. Make it the default for `super_landing`.
- **Wall: W2**, thin: 3 px thick and 8 px high. Make it the default for `super_wall`.
- **Texture: BR1 emerald** bricks on the landing pad and wall. J: "looks the most construct like for bricks".
- **Coverage (pass 89/90):**
  - J wants both **P3** (the whole crater plus a one-block lip out onto the rim) and **P2** (the whole crater floor and its steps) in game. P3 is the strong landing and P2 the weaker one, for example by fall height or charge.
  - **P4** (in Blender, waiting on J's pick) sits in between: it lines the crater, and its edge rises straight up past the rim, 1/2 or 1 block above the ground, instead of spreading out onto the surrounding blocks.
- **Looks:** the landing construct takes the current construct look, mapped in world space at 4 blocks to a tile. BR1 emerald is J's favourite. The corps looks apply per corps.

## Rising arm (J's pick, pass 88: G2 + G3 together)

- **At rest, 15° forward.** With a level look, the ring arm points 15° forward of straight up (xRot ≈ -2.88), and the body leans into it slightly (body xRot +0.04).
- **It follows the aim.** While rising, the ring arm points along the player's look:
  - Elevation = clamp(75° + 0.5 × look pitch upward, 55°, 90°). A level look gives 75°, which is the 15°-forward rest.
  - Yaw: the arm's yRot = the head's yaw relative to the body.
  - The head follows the look as normal, and the body turns a third of that yaw.
  - Blend toward the aim over 3 ticks.
- **Still easing down.** From 45% of the way up, both arms still ease into the fall arm, reaching it at the apex.
- **The ring on the fist.** The ring hand wears the square emblem ring with its face out on the back of the hand, so it leads the climb. In game this is the existing RingHandLayer ring; just check that it shows from below and from the side while rising.

## In the air (J's picks, passes 85–86)

- **The ribbon trail (J picked R1, the shortest).**
  - A thin jade streak comes off the ring fist while rising only, from take-off to the apex.
  - It stays locked to the fist: emit a point every quarter tick, exactly where the ring is, so it never lags or gaps.
  - New points show at full strength at once, with no fade-in.
  - Each point lasts 2 ticks, then fades out within about 1 tick.
  - It is about 1 px wide (0.06 blocks), in the jade construct colour, at low glow.
- **Build-up to the landing.**
  - The ring's light climbs from low at the apex to bright just before touchdown, steepest over the last third of the fall. In Blender terms the curve is 20 + 150·u^2.2, where u is the fraction of the fall.
  - A soft glow round the fist grows, from about 1.5 px to 5 px radius. Its pulse speeds up from every 8 ticks to every 2, leading into the touchdown flare.

## Remove

Take these out of the landing; J dropped them:
- the rolling low wall of hard-light panes (`SuperJumpFx.groundRing`);
- any cracked-ground decal.

The quake, the bounce, the screen shake, kills and scorch all stay as they are.

## Also

- **Motes:** cut the landing motes from 30 to about 8, in dim jade.
- **Ring flare:**
  - wind-up: 40 at full charge;
  - take-off: 420 for a moment;
  - rise and fall: 30, climbing to 120 near the ground;
  - touchdown: 300, then fading;
  - these are relative light levels from Blender; use whatever matches in game.

When it's in, please build a jar. J tests in Lunar Client with the Complementary shader copy.
