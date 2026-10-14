# Build order: everything J has picked, in one jar, plus a Ring Lab you can navigate (2026-10-14)

**From:** Blender designer chat (passes 400–499), on J's instruction:

> "build it all, fix up ring lab too the system should have been worked on to make the options easier to navigate now"

**For:** the mc project chat. This is a **BUILD**, not a review.

**Base:** main at jar **2.1.646** (19.9 MB). **Budget:** under 30 MB. The estimated addition is 1–3 MB of pose
data, code and ring models.

**One jar, one note.** Merge everything below to main so a single build carries it all. Write `latest.json` as
"Bundle: soft landing, double-jump take-off, arm lead, big slam, flying flurry, absorb blast, zigzag beams, square ring
picks, new Ring Lab". Report the final jar size.

The rule for takes J hasn't picked yet: ship **J's pick as the default**, and the other takes as **Ring Lab options**,
so he can choose in game. Every option label shows its take code and pass (e.g. "S2b spring, pass 403").

---

## 1. Movement and flight (Blender designer chat)

### 1a. Double-jump take-off: pass 403 (J: S1 snap "great", running dart R3 "most accurate")

Source: `docs/blender/review/403_takeoff_small2/README.md`. Poses: `poses/403_*.json` (per tick: parts, pos, glow,
cam_shake, event).

- **Second jump:** a jump pressed while airborne from the first jump. Horizontal speed at that moment decides the
  version: under 0.15 blocks a tick is standing, at or over is running.
- **Standing (default S1):**
  - puff to **3.2 blocks** in **3 ticks** (ease-out);
  - a construct burst ring under the feet (radius 0.3 → 2.6 over 10 ticks, 28 pixels);
  - a subtle shake (0.5° pitch / 0.3° yaw, alternating, over 4 ticks);
  - a hero hover with a 0.07-block bob over 1.5 s.
  - Ring Lab options: **S2a** and **S2b**, critically damped springs that rise faster than the snap and settle at
    3.2, never above it.
- **Running: R3 dart.**
  - Flat flight at **5 blocks, 6 ticks** after the second jump, along the horizontal velocity only.
  - Speed 0.3 → 0.95 blocks a tick through the arc, easing to a 0.7 cruise.
  - Burst ring radius 1.8, trailing back.
  - Free arm default **A2** (body pitch − 0.3 rad); options **A1** (flush along the side) and **A3** (forward and out).
- **Never drags (J asked).**
  - Standing: the take-off owns 3 ticks, and the hover ends on any movement input.
  - Running: the arc owns 6 ticks, but steering input still rotates its velocity.
  - After that it is normal flight.

### 1b. Double-tap soft landing: L2, PICKED (J: "L2 for the ease landing")

Pose: `poses/403_L2.json`.

- **Trigger:** double tap space while flying within about 5 blocks of the ground.
- **The landing:**
  1. an 8-tick eased descent (smoothstep) from the flight height onto the feet, speed easing 0.8 → 0.3 blocks a tick;
  2. the first jump plays backwards onto the feet (3 ticks);
  3. touchdown, with a construct cushion ring (radius 1.4);
  4. a 12-tick run-out (0.3 → 0.06 blocks a tick, legs running forwards), easing to a stand.
- Any flight input during the descent cancels it back into flight.

### 1c. The ring arm leads where you fly: pass 404 (J: "arm leading the body by like .08s")

Source: `docs/blender/review/404_arm_lead/README.md`. Poses: `poses/404_arm_lead_D1-D3.json`.

- **Ring arm**, every tick in all flight (cruise, take-off arc, landing): xRot = −(90° + climb of the current movement
  direction), yRot = (current heading − body heading). It points flat ahead when level, not up past the head.
- **Body:** follows the movement direction from **1.6 ticks (0.08 s) ago**. Keep a 2-tick history and interpolate.
- **Default D1** (pure lead). Options: **D2** (the arm overshoots by 25% of the turn rate) and **D3** (plus a bank of up
  to 35° into turns).
- Pose only: it never changes where the player goes.

---

## 2. Combat (Chat C, passes 500–599). Specs are in each review README

| Item | J's pick | Source | Default / options |
|---|---|---|---|
| Big flight slam | **S3 M3**: 7×7 crater, mobs launched the tick after touchdown, crater lit 6 ticks longer, 0.7 s lock | `docs/blender/review/510_flight_slam4/` | Triggered from free flight when pitch ≥ 40° down, speed ≥ 20 b/s and height ≤ trigger height. Default **H5** (5 blocks); options H6 and H3. The animation fits the remaining fall (2–4 ticks). |
| Flying flurry | **F2** jab, cross, spinning backfist | `docs/blender/review/509_flying_flurry/` | In flight the target is carried 1.7 blocks ahead, nudged with each punch. The backfist launches it at 2.4 blocks a tick along the hit angle (gravity 0.03, drag 0.99): it craters what it hits first, or after 50 blocks with no hit it regains control. Automatic, no option needed. |
| Absorb and return blast | **R4b**: held at the ring, turning to green and growing to 1.8× as it charges | `docs/blender/review/503_combat_round4/` (R4) | Hold left click: the shot is sucked into the ring and held while held. Release: a green blast 2× the size at 1.5 blocks a tick (1.5× the incoming), 3 trailing bolts, ring flare. Options R4a (cage) and R4c (swallowed). |
| Omega beams zigzag | **zigzag** ("zigzag is it, shorter streaks, turn more often, random angles") | `docs/blender/review/506_omega_beams5/` | Default **Z2** (corners every 0.22–0.4 blocks, route spread 0.35 × distance, 2–4 waypoints); options Z1 and Z3. Head speed 1.3 blocks a tick, new seed per shot. Later rounds 511–514 are still waiting on J; don't build those. |

## 3. Square emblem ring: P03, N01, N04 PICKED ("the glowing looks great")

- **Source:** `docs/blender/blender_updates/596_square_ring_r2.update.py`. Its grid function (around line 192)
  returns the occupancy, colour and glow grids per take, on the same grid as the game ring.
- **Export:** export P03, N01 and N04 with `tools/ring_bbmodel.py`, the same way the other worn rings were made. The
  lit parts are glow cubes.
- **Ring Lab:** add them to Ring Lab → Ring model. Default **P03** (deep frame, banded stone, faceted proud gem).
- **Lighting:** they light up as in 595/596: the gem table first, then the inlays.

---

## 4. Ring Lab: make it easy to navigate (J's request, twice now)

2.1.646 added tabs and back/forward arrows. Finish the job:

1. **Categories as tabs:**
   - Movement (sprint, take-off, landing, ground flight)
   - Flight (trail, arm lead, effects)
   - Combat (slam, flurry, absorb, dash, hammer)
   - Beams
   - Constructs (looks, textures, walls)
   - Ring (model, hand, glow)
   - Lantern and charge
   - Corps
   - Effects / particles
   - Updates

   Every existing option moves into one of them; nothing is left in a long flat list.
2. **One row per feature,** with **◀ value ▶** cycling. The value shows the take code, a short name and the pass, e.g.
   "◀ S1 snap · pass 403 ▶". No separate button per take.
3. **J's picks are marked** (★) and are the defaults. Add a **"Reset to J's picks"** button per tab and for everything.
4. **Search box** at the top: typing filters the rows across all tabs, e.g. "landing" shows every landing option.
5. **Keyboard:**
   - **Tab / Shift+Tab** change tab;
   - **Up / Down** move between rows;
   - **Left / Right** cycle the value;
   - **Enter** previews where a preview exists.

   Works on a 60% keyboard (no numpad needed).
6. **Superseded options are hidden** (OLD in `docs/blender/DESIGNS.md`) behind a "Show old takes" toggle, so the list
   only holds what's current.
7. **Copy report** groups by tab and lists `feature: value (★ if J's pick)`, so J's KEEP / IMPROVE / DROP pastes map
   straight back.
8. Remember the last tab and row between openings.

## 5. Testing and reporting

- **Game tests:** add client game-test screenshots for:
  - the standing take-off (S1) at its hover;
  - the R3 arc at tick 6;
  - L2 at touchdown;
  - the slam crater (H5);
  - the Ring Lab on two tabs, plus with search text typed.
- **Pull request:** one pull request into main. Update `latest.json`.
- **Report back to J:** the jar version and size, and what each new Ring Lab tab holds.
- **Gaps:** if anything can't be built as specified, say which item and why, and ship the rest.
