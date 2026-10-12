"""Construct block textures (hard-light centre and rim, Wall brick): python tools/construct_textures.py <size> <out_dir>

Hard light is clear emerald glass crossed by a glowing hexagon lattice, so a curved Dome of many
blocks reads as one energy shield. Bricks are dark jade blocks held together by glowing mortar.
"""
import math, random, sys, os
from PIL import Image
N = int(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
k = N / 16.0


def noise(seed, cells=4):
    rnd = random.Random(seed)
    small = Image.new("L", (max(2, N // cells), max(2, N // cells)))
    small.putdata([rnd.randint(0, 255) for _ in range(small.width * small.height)])
    return small.resize((N, N), Image.BICUBIC).load()


# Hexagon lattice that tiles every N pixels: points a*(N/2, 0) + b*(N/4, N/2).
LATTICE = [(a * N / 2 + b * N / 4, b * N / 2) for a in range(-3, 4) for b in range(-3, 4)]


def hex_edge(x, y):
    """Distance in pixels from (x, y) to the nearest hexagon edge."""
    ds = sorted((x - px) ** 2 + (y - py) ** 2 for px, py in LATTICE)
    d0, d1 = math.sqrt(ds[0]), math.sqrt(ds[1])
    return (d1 - d0) / 2


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


def hard_light(rim):
    im = Image.new("RGBA", (N, N)); p = im.load()
    nz = noise(5)
    if rim:
        glass, line, hot = (24, 120, 70, 95), (110, 255, 160, 200), (215, 255, 225, 245)
    else:
        glass, line, hot = (14, 90, 55, 52), (70, 220, 130, 150), (170, 255, 200, 200)
    for y in range(N):
        for x in range(N):
            e = hex_edge(x + 0.5, y + 0.5)
            n = nz[x, y] / 255.0
            c = mix(glass, (glass[0] + 12, glass[1] + 30, glass[2] + 18, glass[3] + 10), n)  # faint shimmer
            halo = max(0.0, 1 - e / (2.2 * k)) ** 2
            c = mix(c, line, 0.55 * halo)
            if e < 0.35 * k + 0.2:
                c = mix(line, hot, 0.5 if rim else 0.2)                                      # the lattice line itself
            p[x, y] = c
    # A few lattice joints flare brighter, like charge running through the shield.
    rnd = random.Random(21 if rim else 7)
    for _ in range(3):
        px, py = rnd.choice([pt for pt in LATTICE if 0 <= pt[0] < N and 0 <= pt[1] < N])
        r = rnd.choice([N / 6, N / 3])
        for y in range(N):
            for x in range(N):
                d = math.hypot(x + 0.5 - (px + r) % N, y + 0.5 - py % N)
                if hex_edge(x + 0.5, y + 0.5) < 0.35 * k + 0.2 and d < 1.6 * k:
                    p[x, y] = hot
    if rim:
        # Glowing border so the shell's outer edge reads as a bright band.
        for y in range(N):
            for x in range(N):
                d = min(x, y, N - 1 - x, N - 1 - y) + 0.5
                g = max(0.0, 1 - d / (1.2 * k)) ** 1.5
                if g > 0:
                    p[x, y] = mix(p[x, y], hot, g)
    return im


def bricks():
    im = Image.new("RGBA", (N, N)); p = im.load()
    nz = noise(9)
    grain = noise(13, 1)
    bh = N // 4                 # 4 courses per block
    bw = N // 2
    m = max(1, round(k))        # mortar thickness
    rnd = random.Random(3)
    tone = {(r, c): rnd.uniform(-0.12, 0.12) for r in range(4) for c in range(3)}
    for y in range(N):
        row = y // bh
        shift = 0 if row % 2 == 0 else bw // 2
        for x in range(N):
            ly = y % bh
            sx = x + shift
            lx = sx % bw
            col = (sx // bw) % 2
            n = nz[x, y] / 255.0
            if ly >= bh - m or lx >= bw - m:
                # Glowing mortar: hard light holding the bricks together.
                v = 0.75 + 0.25 * n
                p[x, y] = (int(110 * v), int(255 * v), int(150 * v), 255)
                continue
            iw, ih = bw - m, bh - m
            g = 0.52 + tone[(row, col)] + (grain[x, y] / 255.0 - 0.5) * 0.1
            if ly < m: g += 0.28                     # lit top bevel
            elif lx < m: g += 0.16                   # lit left bevel
            elif ly >= ih - m: g -= 0.2              # shaded bottom
            elif lx >= iw - m: g -= 0.12             # shaded right
            # Mortar light bleeding onto the brick edges.
            edge = min(lx, ly, iw - 1 - lx, ih - 1 - ly)
            bleed = max(0.0, 1 - edge / (1.5 * k)) * 0.12
            g = max(0.0, min(1.0, g))
            p[x, y] = (int(10 + 70 * g + 60 * bleed), int(55 + 140 * g + 90 * bleed), int(30 + 70 * g + 60 * bleed), 255)
    return im


hard_light(False).save(f"{OUT}/construct_inner.png")
hard_light(True).save(f"{OUT}/construct_rim.png")
bricks().save(f"{OUT}/construct_brick.png")
