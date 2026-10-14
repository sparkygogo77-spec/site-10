# Pass 514: omega beams round 8 — fiery lines, same physics to the hit, speed-scaled chase, under water (Chat C) — WAITING

J on 513: "the lines need some work as well as once the initial bands go it starts to track a little closer and no
longer in the way that the lines initially moved which it will need to obey the movement physics of totally, though if
something is running the lasers should get LONGER in length the scale should slide up to 1.4 and high end chase someone
at about 95% of their speed when fast flying" + (reference of the beams under water) "it should leave an air bubble
trail underwater but not too dense but give me a few variations".

**Open:** `C:\Users\Josh\Documents\LanternLive\combat\omega_fire.blend`, Cam L2 (or `Cam <take> wide` / `Cam <take> target`),
frames 1–80. **Script:** `docs/blender/blender_updates/514_omega_fire.update.py`. **Files:** `sheet.png`, `omega_fire_poses.json`.

## Physics (for the game)
- **Same switchbacks from the eyes to the hit**: P3, sides 0.8–3.2 blocks, 55–72° off the line, swinging mostly
  sideways. 513's tighter closing-in phase is gone. The last side goes straight in once the target is within one long
  side (as in 511).
- Each side aims where the target **will be** (lead = distance / (0.45 × head speed), max 2 s).
- If the target pulled away during a side, the next side takes the lower half of the band (55–63°): same look, keeps gaining.
- **Running targets lengthen the sides**: scale = 1 + 0.4 × min(1, target speed / 1.5 blocks a tick) → **×1.4 at 30 b/s**.
- **Head speed** = max(2.2, 0.95 × target speed / 0.45) blocks a tick, so the line closes at **95% of a fast target's
  speed** (0.45 = the headway of a P3 switchback). A fast flyer that keeps flying straight stays ahead; it is caught when
  it turns (F1: flying 30 b/s, caught in its banking turn at tick 60). The chase gives up after 5 s and burns away.

## Look (from J's references)
- Thin white-hot-red core (255, 107, 82), radius 0.02 blocks, in a tight deep red glow (255, 13, 5), radius 0.07,
  fading to its edges, with bloom. Never washed to white.
- **L1** core + glow + 3 embers a tick flaking off the whole line (8-tick life).
- **L2** L1 + flickering hot spots running along the line (noise, ~0.5 blocks, moving 0.4 blocks a tick, brightness ×0.55–1.8).
- **L3** L2 + a pulsing flare at each corner as it is laid, 6 embers a tick.

## Under water (L2 look)
- **W1** sparse bead: 1 bubble a tick (0.05–0.1 blocks), rising 0.06 b/tick, wobbling, growing ×1.4, popping at the surface.
- **W2** thin boiling sleeve: 4 small bubbles a tick hugging the line, 7-tick life.
- **W3** W1 + a steam puff at every new corner, growing ×2.2 as it rises.

| Take | Target | Speed | Side scale | Head speed | Hit |
|---|---|---|---|---|---|
| L1–L3 | galloping horse | 13 b/s | ×1.19 | 2.2 b/tick | ticks 37–52 |
| F1 | fast flyer, banking turn at tick 40–62 | 30 b/s | ×1.4 | 3.17 b/tick | tick 60 |
| W1–W3 | swimmer | 6 b/s | ×1.1 | 2.2 b/tick | ticks 32–34 |
