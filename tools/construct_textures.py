"""Construct block textures (wall centre, wall rim, dome brick): python tools/construct_textures.py <size> <out_dir>"""
import math, random, sys, os
from PIL import Image, ImageFilter
N = int(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
random.seed(11)
k = N / 16.0

# Seamless Voronoi edge distance (in pixels), for branching energy veins.
cells = [(random.uniform(0, N), random.uniform(0, N)) for _ in range(7)]
fine = [(random.uniform(0, N), random.uniform(0, N)) for _ in range(18)]
def edge(x, y, pts):
    ds = sorted(math.hypot(x - px - ox, y - py - oy) for px, py in pts for ox in (-N, 0, N) for oy in (-N, 0, N))
    return ds[1] - ds[0]

def noise(seed):
    rnd = random.Random(seed)
    small = Image.new("L", (max(2, N // 4), max(2, N // 4)))
    small.putdata([rnd.randint(0, 255) for _ in range(small.width * small.height)])
    return small.resize((N, N), Image.BICUBIC).load()

def construct(rim):
    im = Image.new("RGBA", (N, N)); p = im.load()
    nz = noise(5)
    for y in range(N):
        for x in range(N):
            e = edge(x + 0.5, y + 0.5, cells)
            e2 = edge(x + 0.5, y + 0.5, fine)
            core = max(0.0, 1 - e / (0.9 * k))           # thin bright vein
            glow = max(0.0, 1 - e / (3.2 * k)) ** 2      # soft halo around veins
            faint = max(0.0, 1 - e2 / (0.7 * k)) * 0.35  # finer secondary web
            n = nz[x, y] / 255.0
            if rim:
                base = (14 + 10 * n, 62 + 22 * n, 38 + 12 * n, 125)
                v = min(1.0, core + 0.3 * glow + 0.6 * faint)
                top = (140, 255, 170, 235)
            else:
                base = (6 + 6 * n, 34 + 14 * n, 22 + 8 * n, 88)
                v = min(1.0, 0.55 * core + 0.3 * glow + 0.6 * faint)
                top = (50, 170, 100, 165)
            p[x, y] = tuple(int(base[i] + (top[i] - base[i]) * v) for i in range(4))
    if False:
        width = max(1.0, 1.0 * k)
        for y in range(N):
            for x in range(N):
                d = min(x, y, N - 1 - x, N - 1 - y) + 0.5
                g = max(0.0, 1 - d / (2.6 * width)) ** 1.5    # glowing border with falloff
                if g <= 0: continue
                r, gg, b, a = p[x, y]
                hot = (205, 255, 215, 255)
                p[x, y] = tuple(int(c + (h - c) * g) for c, h in zip((r, gg, b, a), hot))
    return im

def bricks():
    im = Image.new("RGBA", (N, N)); p = im.load()
    nz = noise(9)
    bh = N // 4                 # 4 courses per block, like nether bricks
    bw = N // 2
    m = max(1, round(k))        # mortar thickness
    for y in range(N):
        row = y // bh
        for x in range(N):
            ly = y % bh
            lx = (x + (0 if row % 2 == 0 else bw // 2)) % bw
            n = nz[x, y] / 255.0
            if ly >= bh - m or lx >= bw - m:
                v = 0.6 + 0.4 * n
                p[x, y] = (int(4 + 6 * v), int(24 + 12 * v), int(16 + 8 * v), 255)   # dark jade mortar
                continue
            # bright core, darker edges, light bevel on top-left, shade bottom-right
            cx = 1 - abs((lx + 0.5) - (bw - m) / 2) / ((bw - m) / 2)
            cy = 1 - abs((ly + 0.5) - (bh - m) / 2) / ((bh - m) / 2)
            g = 0.35 + 0.65 * (cx * cy) ** 0.6
            if ly < m: g += 0.18
            if lx < m: g += 0.1
            if ly >= bh - 2 * m: g -= 0.15
            g += (n - 0.5) * 0.18
            g = max(0.0, min(1.0, g))
            p[x, y] = (int(20 + 125 * g), int(95 + 160 * g), int(40 + 100 * g), 255)
    return im

construct(False).save(f"{OUT}/construct_inner.png")
construct(True).save(f"{OUT}/construct_rim.png")
bricks().save(f"{OUT}/construct_brick.png")
