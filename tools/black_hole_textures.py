"""The Black Hole's texture (client/BlackHoleFx), one 512x256 sheet so the whole hole is a
single translucent mesh the game sorts back to front:

  rows 0-127          the accretion disk: streaky hot gas, white-hot at its inner edge (top)
                      through jade to dark green at its outer edge; brightness is in alpha.
  (0,128) 64x64       a soft round dot, for the streaks of matter spiralling in.
  (64,128) 32x64      a thin bright line across v, for the photon ring round the core.
  (96,128) 16x16      plain black, for the core and the shadow round it.

Usage: python tools/black_hole_textures.py src/main/resources/assets/lanternring
"""
import math
import os
import random
import sys

from PIL import Image


def smooth_noise(width, octaves, seed):
    """1D periodic value noise over width samples, summed over octaves."""
    rnd = random.Random(seed)
    out = [0.0] * width
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = 4 * 2 ** o
        knots = [rnd.random() for _ in range(cells)]
        for x in range(width):
            t = x / width * cells
            i = int(t)
            f = t - i
            f = f * f * (3 - 2 * f)
            a, b = knots[i % cells], knots[(i + 1) % cells]
            out[x] += amp * (a + (b - a) * f)
        total += amp
        amp *= 0.55
    return [v / total for v in out]


def lerp(a, b, t):
    return a + (b - a) * t


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return tuple(lerp(c0[i], c1[i], f) for i in range(3))
    return stops[-1][1]


W, H = 512, 256


def disk(img):
    """Rows 0-127, full width: u runs round the disk (tiles seamlessly), v inner edge to outer edge."""
    w, h = W, 128
    px = img.load()
    # Each few rows get their own streak pattern, sheared a little so the gas looks like it spirals.
    bands = [smooth_noise(w, 5, 1000 + y // 4) for y in range(h + 4)]
    fine = [smooth_noise(w, 4, 5000 + y) for y in range(h)]
    clumps = smooth_noise(w, 3, 77)
    stops = [
        (0.0, (255, 255, 255)),
        (0.12, (220, 255, 228)),
        (0.35, (110, 255, 150)),
        (0.65, (40, 210, 90)),
        (1.0, (10, 120, 45)),
    ]
    for y in range(h):
        v = y / (h - 1)
        # Bright just off the inner edge, dimming outward; a soft fade at both edges.
        profile = (1 - v) ** 1.3 * min(1.0, v / 0.05) * min(1.0, (1 - v) / 0.1)
        shear = int(v * w * 0.18)
        for x in range(w):
            xs = (x + shear) % w
            n = 0.6 * bands[y][xs] + 0.4 * fine[y][xs]
            streak = 0.2 + 2.4 * max(0.0, n - 0.3) ** 1.2
            clump = 0.5 + 1.0 * clumps[(x + shear * 2) % w] ** 1.5
            b = max(0.0, min(1.0, profile * streak * clump))
            col = ramp(stops, v * 0.8 + (1 - b) * 0.2)
            px[x, y] = tuple(int(c) for c in col) + (int(255 * b ** 0.7),)


def glow(img, x0=0, y0=128, s=64):
    """A soft round dot, white, its strength in alpha."""
    px = img.load()
    for y in range(s):
        for x in range(s):
            d = math.hypot(x - (s - 1) / 2, y - (s - 1) / 2) / (s / 2)
            b = min(1.0, max(0.0, math.exp(-(d * 2.2) ** 2) * 1.1 - 0.02))
            px[x0 + x, y0 + y] = (255, 255, 255, int(255 * b))


def ring(img, x0=64, y0=128, w=32, h=64):
    """A thin bright line across v, white at its heart going jade at its edges."""
    px = img.load()
    for y in range(h):
        d = (y / (h - 1) - 0.5) * 2
        b = min(1.0, math.exp(-(d * 3.2) ** 2) + 0.3 * math.exp(-(d * 1.3) ** 2))
        col = (int(lerp(90, 255, b ** 2)), 255, int(lerp(140, 245, b ** 2)), int(255 * b))
        for x in range(w):
            px[x0 + x, y0 + y] = col


def black(img, x0=96, y0=128, s=16):
    px = img.load()
    for y in range(s):
        for x in range(s):
            px[x0 + x, y0 + y] = (0, 0, 0, 255)


def main(assets):
    out = os.path.join(assets, "textures", "entity")
    os.makedirs(out, exist_ok=True)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    disk(img)
    glow(img)
    ring(img)
    black(img)
    img.save(os.path.join(out, "black_hole.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring")
