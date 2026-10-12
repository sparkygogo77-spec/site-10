"""Construct block textures (hard-light centre and rim, Wall brick): python tools/construct_textures.py <size> <out_dir>

Hard light is milky, see-through jade covered in fine crackle, like old glazed jade: a few big
cracks and a web of hair-line ones. The centre blocks' cracks only shimmer. Rim blocks light up
toward two edges (top and left of each face): the cracks get brighter and wider the closer they
are to those edges, as if light leaks in from the seam. The blockstate turns each block at random,
so the lit edges land on different sides from block to block. Bricks are dark jade blocks with the
same fine crackle, a little see-through, held together by glowing mortar. Everything tiles every N pixels.
"""
import math, random, sys, os
from PIL import Image
N = int(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
k = N / 16.0


def noise(seed, cells=4):
    """Smooth noise in 0..1 that tiles every N pixels, with blobs about `cells` 16th-of-a-block wide."""
    rnd = random.Random(seed)
    g = max(2, round(16 / cells))
    vals = [[rnd.random() for _ in range(g)] for _ in range(g)]
    def smooth(t): return t * t * (3 - 2 * t)
    out = [[0.0] * N for _ in range(N)]
    for y in range(N):
        fy = y / N * g; y0 = int(fy); ty = smooth(fy - y0)
        for x in range(N):
            fx = x / N * g; x0 = int(fx); tx = smooth(fx - x0)
            a = vals[y0 % g][x0 % g]; b = vals[y0 % g][(x0 + 1) % g]
            c = vals[(y0 + 1) % g][x0 % g]; d = vals[(y0 + 1) % g][(x0 + 1) % g]
            out[y][x] = (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty
    return out


def fbm(seed):
    layers = [(noise(seed, 8), 0.5), (noise(seed + 1, 4), 0.3), (noise(seed + 2, 2), 0.2)]
    return [[sum(l[y][x] * w for l, w in layers) for x in range(N)] for y in range(N)]


def crack_field(seed, cells, warp, keep):
    """Per pixel: (distance to the nearest crack, how strong that crack is) for a warped Voronoi
    crackle that wraps every N pixels. Each crack (a pair of neighbouring cells) gets its own
    strength, and about 1 - keep of them are missing, so the pattern never reads as tidy cells."""
    rnd = random.Random(seed)
    base = [(rnd.uniform(0, N), rnd.uniform(0, N)) for _ in range(cells)]
    pts = [(px + ox * N, py + oy * N, i) for i, (px, py) in enumerate(base) for ox in (-1, 0, 1) for oy in (-1, 0, 1)]
    wx, wy = noise(seed + 50, 4), noise(seed + 60, 4)
    strength = {}
    out = [[(99.0, 0.0)] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            sx = x + 0.5 + (wx[y][x] - 0.5) * warp
            sy = y + 0.5 + (wy[y][x] - 0.5) * warp
            best = sorted(((sx - px) ** 2 + (sy - py) ** 2, px, py, i) for px, py, i in pts)[:2]
            (d0, ax, ay, ai), (d1, bx, by, bi) = best
            key = (min(ai, bi), max(ai, bi))
            if key not in strength:
                r = random.Random(seed * 7919 + key[0] * 131 + key[1])
                strength[key] = r.uniform(0.45, 1.0) if r.random() < keep else 0.0
            # Distance to the bisector between the two nearest points: the crack line.
            mx, my = (ax + bx) / 2, (ay + by) / 2
            nx, ny = bx - ax, by - ay
            ln = math.hypot(nx, ny) or 1
            out[y][x] = (abs((sx - mx) * nx + (sy - my) * ny) / ln, strength[key])
    return out


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


BIG = crack_field(11, 6, 1.6 * k, 0.9)     # a few long cracks
MID = crack_field(17, 22, 1.0 * k, 0.6)     # branching cracks between them
FINE = crack_field(23, 70, 0.6 * k, 0.5) # the hair-line crackle
FINE_MASK = noise(31, 3)                  # fine crackle fades in and out across the face
CLOUD = fbm(41)                           # milky clouds inside the jade
PX = N / 128.0                            # one pixel at the 128px design size


def line(field, x, y, width):
    d, s = field[y][x]
    return s * max(0.0, min(1.0, (width - d) / (0.35 * PX) + 0.5))


def crack_strength(x, y):
    """0..1: how much of a crack this pixel is (1 on a big crack, less on hair-lines)."""
    big = line(BIG, x, y, 1.0 * PX)
    mid = 0.75 * line(MID, x, y, 0.8 * PX)
    fine = 0.6 * line(FINE, x, y, 0.72 * PX) * (0.3 + 0.7 * FINE_MASK[y][x])
    return max(big, mid, fine)


def crack_dist(x, y):
    """Distance to the nearest visible big or medium crack, for halos."""
    db, sb = BIG[y][x]; dm, sm = MID[y][x]
    return min(db if sb else 99.0, dm * 1.3 if sm else 99.0)


def hard_light(rim):
    im = Image.new("RGBA", (N, N)); p = im.load()
    # The fill is a rich, fairly solid green so the panel centres read as jade, not dark glass.
    deep, milky = (22, 120, 66, 178), (78, 196, 126, 206)
    lit = (120, 236, 166, 228)   # the fill colour right at a lit edge
    crack_dim, crack_hot = (150, 235, 185, 215), (235, 255, 238, 252)
    for y in range(N):
        for x in range(N):
            c = mix(deep, milky, (CLOUD[y][x] - 0.25) * 1.6)
            if rim:
                # Glow rises toward the top and left edges of each face, easing in over most of the
                # face so the bright edge blends into the fill instead of stopping short.
                d = min(x + 0.5, y + 0.5)
                t = max(0.0, 1 - d / (0.85 * N))
                glow = t * t * (3 - 2 * t)
                c = mix(c, lit, 0.65 * glow)
            else:
                glow = 0.0
            s = crack_strength(x, y)
            shade = max(0.0, 1 - crack_dist(x, y) / (2.5 * PX)) * (1 - glow)
            c = mix(c, (10, 70, 38, c[3] + 15), 0.25 * shade * (1 - s))
            # Near the lit edges, cracks widen into a soft halo.
            halo = max(0.0, 1 - crack_dist(x, y) / (3 * PX + 9 * PX * glow)) ** 2
            c = mix(c, (120, 245, 170, 215), halo * glow)
            if s > 0:
                line = mix(crack_dim, crack_hot, glow * 1.1)
                # A dark shadow line beside each crack gives it depth, then the bright crack itself.
                c = mix(c, line, s * (0.7 + 0.3 * glow))
            if rim:
                # The seam itself: a thin bright line right at the lit edges.
                e = max(0.0, 1 - min(x, y) / (4 * PX)) ** 2
                c = mix(c, crack_hot, 0.6 * e)
            p[x, y] = c
    return im


BRICK_ALPHA = 185   # bricks are about 72% opaque: a solid barrier you can just see through


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
            n = nz[y][x]
            if ly >= bh - m or lx >= bw - m:
                # Glowing mortar: hard light holding the bricks together.
                v = 0.75 + 0.25 * n
                p[x, y] = (int(110 * v), int(255 * v), int(150 * v), 240)
                continue
            iw, ih = bw - m, bh - m
            g = 0.52 + tone[(row, col)] + (grain[y][x] - 0.5) * 0.1 + (CLOUD[y][x] - 0.5) * 0.25
            if ly < m: g += 0.28                     # lit top bevel
            elif lx < m: g += 0.16                   # lit left bevel
            elif ly >= ih - m: g -= 0.2              # shaded bottom
            elif lx >= iw - m: g -= 0.12             # shaded right
            # Mortar light bleeding onto the brick edges, and into the crackle near them.
            edge = min(lx, ly, iw - 1 - lx, ih - 1 - ly)
            bleed = max(0.0, 1 - edge / (1.5 * k)) * 0.12
            g = max(0.0, min(1.0, g))
            c = (int(10 + 70 * g + 60 * bleed), int(55 + 140 * g + 90 * bleed), int(30 + 70 * g + 60 * bleed), BRICK_ALPHA)
            s = crack_strength(x, y) * (0.5 + 3 * bleed)
            p[x, y] = mix(c, (130, 235, 170, BRICK_ALPHA + 25), s * 0.7)
    return im


hard_light(False).save(f"{OUT}/construct_inner.png")
hard_light(True).save(f"{OUT}/construct_rim.png")
bricks().save(f"{OUT}/construct_brick.png")
