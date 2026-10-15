# Hand-off: J's KEEP from pass 835 (2026-10-15)

## Ultimate dome: D1 snap — KEEP, word for word: "D1 for the dome"

- Blender: `LanternLive\constructs\ultimate_dome2.blend` (Cam D1 wide / D1 look up / D1 player).
  Script: `docs/blender/blender_updates/835_ultimate_dome2.update.py` (take `D1`).
- **What it is:** the ultimate build (J on 816 X2): look up, shoot a beam to the sky for 2.5 s, and a construct dome
  forms over you in 10 s and lasts 2.5 minutes. Built at **radius 150** (J's ask "about 150 blocks in radius"; the 75
  version in 826 was not picked).
- **Timeline (20 ticks a second):**
  - 1-18 the oath: ring fist to the heart (8-13), then driven straight up (17-18); head up to the 57° limit by 24.
  - 18-68 the beam straight up to the dome's top, up in 4 ticks, held, thinned out 68-74. The look of the beam follows
    whatever ring laser J picks (834/836 are still open; the file uses 834 L1).
  - 28 apex flash where the beam hits the top.
  - 28-228 the dome forms **top-down**; 60-228 it also forms **bottom-up** from the ground; the fronts meet 70% of the
    way down at 228 (10 s).
  - 228 to 3000+228 it stands (2.5 min); then it comes apart top first over 30 ticks.
- **The front (why D1, J: 826 "builds behind the blocks a little too laggy"):** every block appears on the exact tick
  the front reaches it - no fade-in, no random delay - and one thin bright edge ring rides the front, moved every tick.
  - Top front, how far down it is (0 = top, 0.7 = the meeting line) at tick t:
    `frac = 0.7 * u^(1/1.6)`, `u = clamp((t - 28) / 200, 0, 1)`; polar angle = frac × 90°.
  - Bottom front: `frac = 1 - 0.3 * clamp((t - 60) / 168, 0, 1)`.
  - A block at polar angle θ appears at the first tick its front's frac passes θ / 90°.
  - Edge ring: emissive green (0.06, 1.0, 0.28), about 0.025 blocks thick in the file - in game a 1-block-wide
    glowing band of the construct texture is the equivalent.
- **Look:** the brick construct texture (`texture_library/green/br1`), 55% opaque, animated strip (4 ticks a frame),
  emission 0.9; edge and apex saturated green, never white.
- **For the game (sizes to weigh):** a 150-radius hemisphere is 2π·150² ≈ 141,000 blocks of surface. Building it in
  10 s is about 700 blocks a tick, so either place real construct blocks in batches per latitude band (48 bands, as in
  the file) or draw the shell client-side as one textured mesh revealed by the same `frac` (cheap) and keep the
  server-side barrier as a sphere check on entities.
