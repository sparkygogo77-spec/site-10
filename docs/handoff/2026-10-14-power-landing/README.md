# Hand-off: power landing (pass 400), J's picks 2026-10-14

**From:** Blender designer chat (passes 400–499).
**For:** the mc project chat (game code).
**Source:**
- Script: `docs/blender/blender_updates/400_power_slide.update.py`
- Review: `docs/blender/review/400_power_slide/`
- Open in Blender: `C:\Users\Josh\Documents\LanternLive\power_slide.blend`, Cams D0, A3, B2

## What J asked for and picked

> "a power landing that either stops you dead or if you are moving above a certain limit create a slide animation ...
> a construct texture animation clearing the blocks i slide to until i come to a halt and the animation for the slide
> should be a strong one foot stop"

J's in-game shots: today the landing crater forms, then the physics slides him far away across the snow. **The slide
must replace that run-out.**

> "A3 dissolve and i also want to see a plough option in the ring lab optimize the ring lab selection methods too, make
> the dissolve the 25 28 threshold, B2 for plough"

| Ring Lab option | Take | Slides above | Demo speed | Slide | Trench |
|---|---|---|---|---|---|
| **Dissolve (default)** | A3 | **25 b/s** | 28 b/s | 5.0 blocks in 7 ticks | 3 wide |
| **Plough** | B2 | **15 b/s** | 18 b/s | 3.2 blocks in 7 ticks | 3 wide |
| below the threshold (either option) | D0 | — | 5 b/s | none: stop dead | 3×3 crater |

b/s = blocks per second, horizontal speed at touchdown. 20 ticks a second.

## Rules

- **Slide length** = `min(5, 5 × speed / 28)` blocks.
- **Slide time** `n` = `round(2 × length / speed × 20)` ticks (7 at both picked speeds).
- **Deceleration:** constant. Forward at tick `k` after touchdown = `length × (1 - (1 - k/n)²)`.
- **Direction:** the slide runs along the horizontal velocity at touchdown. The trench follows that direction (in Blender it
  is straight ahead).
- **Trench:** blocks from the touchdown block to the block before the halt block. The **halt block stays**, so you stop on
  solid ground. Width is 3 at 15 b/s and up (1 below), centred on the player.
- **Which blocks:** only the top layer the feet slide over. Respect claims and unbreakable blocks (bedrock, etc.); an
  unbreakable block in the path ends the slide there.

### D0 stop dead (under the threshold)

- Two-foot squat in 3 ticks, ring fist to the ground; hold to tick 20; stand by tick 34.
- The block you land on turns construct for 0.8 s, holds you, and fades back. **It is not removed.**
- The 8 around it light up (ticks -1 to 1) and dissolve to pixels (ticks 6 to 8, sorted by distance).
- Ground pulse: a construct ring growing to radius 3 over 8 ticks, fading.

### A3 dissolve (default)

- Each path block lights up in construct texture when the planted left foot is 1.6 blocks from it. It breaks into about
  10 construct pixels when the foot reaches it; the side columns go a tick later.
- Pixels fly up 0.08–0.24 blocks a tick, drift with you, take gravity of 0.02 a tick², shrink out over 12–22 ticks,
  and fade.
- A construct pad (0.55 × 1.1 blocks, about 85% opaque) under the left foot keeps you level over the trench. It fades
  over 11 ticks after the halt.
- The exact lit and cleared ticks per block are in `poses/A3_dissolve.json` under `cells`.

### B2 plough (Ring Lab option)

- A construct bow-wave blade (a shallow V pointing forward, 3.3 wide, curling up at the top) rides 0.65 blocks ahead of
  the left foot.
- Each block it reaches turns construct and is thrown aside:
  - sideways 0.24–0.32 blocks a tick (the centre column alternates left and right);
  - forward 8–16% of your speed;
  - up 0.24–0.3 a tick;
  - gravity 0.045 a tick², tumbling.
- Thrown blocks land square on the surface beside the trench and dissolve to pixels 12 ticks later. They do **not**
  drop as items.
- At the halt the blade pushes on 0.25 blocks a tick and fades over 9 ticks.

## Player animation (all three)

Use `poses/*.json`: per tick, per part `rot` (xRot, yRot, zRot in radians) and `offset_px` from the vanilla pivot. Ring
on the right hand; the **left foot plants**.

Slide timeline, by tick after touchdown:

| Ticks | Pose |
|---|---|
| 0–2 | REACH → IMPACT (absorb: torso sinks 1.5 px, planted knee 0.95 rad) |
| 2 to n | IMPACT → SKID: lean back, left leg braced forward, right knee trailing low, ring arm thrown back and out, free arm forward |
| n to n+4 | SKID → HALT: rock forward onto the planted knee |
| next 10 | hold |
| next 14 | → stand |

Ring glow: 18 at impact, 16 through the skid, easing to 7.

## The construct look

- Use the existing default construct texture (R2 K1 dark-jade fragments) on the blocks and pixels, in the ring's corps
  colour (`CorpsTint`).
- The Blender preview is a procedural stand-in, about 25% darker than the first draft; J likes dark jade lines between
  the fragments.
- Pixels and the pad stay see-through (at most 95% opaque).

## Ring Lab (J: "optimize the ring lab selection methods too")

- Add **Landing → Slide: Dissolve | Plough** (default Dissolve).
- J wants the Ring Lab's picking made easier; how is up to you. Suggestions:
  - one row per feature with ◀ ▶ cycling instead of separate buttons;
  - group rows by power (Landing, Flight, Sprint, Constructs…);
  - show the pass and take name (e.g. "A3 dissolve, pass 400") next to each choice;
  - keep "Copy report" listing every current pick, so J can paste KEEP / IMPROVE / DROP back.

## Assets

`assets/sheet_400.png` is the contact sheet. No new textures: everything uses the construct texture already in the jar.
