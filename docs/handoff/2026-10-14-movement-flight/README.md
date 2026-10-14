# Hand-off: movement and flight (J's picks, 2026-10-14)

From the lead Blender chat, for the game chat that builds movement and flight. Everything in this folder is J's pick
unless it says "Ring Lab option". Pose data: per tick, per part `rot` (xRot, yRot, zRot in radians) and `offset_px`
from the vanilla pivot. The ring is on the **right** arm. Shins are extra parts that pivot at the knee, 6 px below the hip.
If the vanilla model has no shins, use thigh + knee as one leg bend.
Blender sources are in `docs/blender/blender_updates/` (pass numbers below). J's .blend files are in
`C:\Users\Josh\Documents\LanternLive\`.

Treat KEEP as final, IMPROVE as the next thing to iterate, and DROP as safe to remove in J's Ring Lab reports.

## 1. Sprint run: S1 + S4 combined (pass 227, `poses/sprint_run2_poses.json`)

- Poses: the ring fist is held out in front and glowing (S1). When a lantern is in the off hand, the free hand carries
  it by the handle, a little higher and out in front (S4).
  - The lantern is gripped, not hanging free: it tilts and wobbles against the motion. Use a stiff, damped pendulum
    capped at about 22°.
  - With no lantern in hand, the free arm pumps as in S1 (pass 214, take S1).
- **Ring Lab option:** the carry height. J hasn't picked yet:
  - S5a: carry arm 43° forward
  - S5b: carry arm 57° forward
- Speed: drive the stride by **distance travelled**, not as a fixed clip.
  - Cycle rate = speed ÷ stride length. The data is a 12-tick stride at 0.28 blocks a tick, so stride length = 3.36 blocks.
  - Faster movement turns the legs over faster with no foot sliding. The cycle slows into a stand when you stop.
  - Blend walk to S1/S5 when sprinting starts, and back when it stops.

## 2. Takeoff: F2 rocket, in the direction you move (pass 216, `poses/flight_takeoff_poses.json`, take F2)

- Animation as F2: plant, ring fist straight up, shoot up standing, then pitch over into level flight about 12 blocks up.
- J: launch in the direction the player is **moving**, not the direction they face. Use the horizontal velocity if it
  is over about 0.05 blocks a tick; otherwise use facing.
- Head fix (J, F3): the neck bends at most about 57° back from the body. In the old data, flat flyers folded the head
  back into the chest. Rule: `headX = max(headX, bodyX - 1.0 rad)`.
  - Check `FlightPoses` too: the glide sets `head.xRot` toward -1.1 to -π/2 relative to a body laid flat. Make sure it
    reads as looking ahead, not tucked in.

## 3. Ground flight with the running barrier (pass 228, `poses/ground_flight_poses.json`)

**Start.** Sprinting on the ground, double-tap space to start a low flight forward, in the direction of movement.

**Height.** Skim with the player's origin 0.5 block above the surface, which leaves about 1 block of clearance.

**1-block steps.** The ring keeps you on top of any 1-block step you run into:
- Look ahead about 1.6 blocks along the movement and target `surface + 0.5`.
- Follow it with a critically damped spring: `vz += (target - z) * 0.35 - vz * 0.75` per tick.

**2-block or taller walls** (J: 2–3 high; no preference above that, so the same at any height) are a barrier collision.
The barrier is an invisible dome around you while you run:
- **Size:** radius **3.5 blocks**, a little smaller than the 4.5-block flying dome (`HeldConstructs.DOME_RADIUS`). The
  player can still reinforce the flying dome and see it as now.
- **Impact:** the dome shows **only where it touches the wall**. The construct texture is fully visible within 0.4
  block of the wall face and gone by 1.6 blocks. The front flattens on the wall in a dome-shaped crater.
- **Sparks:** about 48 construct sparks burst out of the crater rim along the wall, under gravity, shrinking out over
  10–18 ticks.
- **Imprint:** the flattened patch is left on the wall as a construct imprint (an ellipse on the face, kept on the
  wall). It fades over 5 s (100 ticks), starting 20 ticks after impact.
- **Re-forming:** the dome springs back to round in 4 ticks, then goes invisible again.
- **Halt.** J: "brought to a halt in the same block where my barrier made the impact, as a quick animation". Ease out
  with `y = hit - depth * (1 - (1 - w)^2)`. **Ring Lab option H1/H2/H3** (J hasn't picked):

  | Option | Stop ticks | Crater depth | Where you stop |
  |---|---|---|---|
  | H1 hard stop | 3 | 0.5 blocks | about where the dome touched |
  | H2 cushion | 6 | 1.4 blocks | 1.4 blocks past first touch |
  | H3 into the block | 8 | 2.5 blocks | 1 block off the wall |

- **Pose:** brace on impact (body comes up, ring arm punches forward), then settle to a hover over about 10 ticks.
- **Texture:** the construct texture in the ring's corps colour. The Blender preview used X3D1
  (`construct_ripples_green_x3d1_emerald.png`, frame 0 copied here as `assets/dome_x3d1_f0.png`).
- **Pose data per tick:** `dome_alpha` and `dome_squash` (in blocks). `hit_tick` and `stop_ticks` are per take.

## 4. Flight trail T4 + sonic boom (pass 218, `assets/`)

**Trail (T4):** a thin light ribbon off the ring hand, wind streaks above 0.8 blocks a tick, and a ring of light at
1.1 blocks a tick.

**Trail light.** Use `assets/flight_trail_light.png`:
- 64 × 1024, 16 frames of 64 × 64, scrolling seamlessly along the trail.
- It's construct green, so `CorpsTint` recolours it. `flight_trail_light_white.png` is a white version for a renderer
  that multiplies by the corps colour itself.
- J: the light belongs to the lantern corps and the ring: "a texture made out of light".

**Who sees it.** J: "I should be able to see the line but it's more for other players based on how fast it is."
- Other players see the full ribbon. Width, length and alpha scale with speed: 0 at 0.3 blocks a tick, full at 1.5.
- In first person, draw it fainter, at about 35% alpha, and not across the view.

**Sonic boom**, once each time you go into fast flight:
- **Trigger:** `FastFlight`'s glide speed crosses **1.1 blocks a tick**. Top speed is 1.62 (flying speed 0.08 × 2,
  drag 0.91). Re-arm below 0.9 so it doesn't repeat.
- **Visual:** `assets/sonic_boom_ring.png`, 8 frames of 64 × 64, 0.4 s at 1 frame every tick and a half. Draw it at the
  player, facing along the velocity, growing from 0 to about 6 blocks across. It also replaces the T4 speed ring at
  that moment.
- **Sound for nearby players:** `assets/sonic_boom.ogg` (1.6 s: double N-wave crack, low thump, rumble tail). Audible
  to about 64 blocks.
- **Sound for the flyer:** `assets/sonic_boom_close.ogg` (0.9 s: a fast whoosh into a tight crack).
- Register both in `sounds.json` (only `lasso_hum` is there now), with subtitles.

**Screen shake.**
- **Flyer, first person:** "extremely fast". 6 ticks of high-frequency camera jitter, about 25–30 shakes a second
  (sample per frame, not per tick). Start at ±1.2° yaw/pitch, decaying to 0, with a 4–6° field-of-view kick that springs
  back.
- **Nearby players:** amplitude `(1 - d/24)` within 24 blocks, about 10 ticks, lower frequency (about 12 shakes a second).
- Add a Ring Lab slider for shake strength (0–100%, default 100%).

The assets are generated by `tools/flight_fx_textures.py OUTDIR`.
