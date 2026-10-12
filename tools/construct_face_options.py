"""Several construct face styles at once, so J can pick (he asked for options every time we make
faces): python tools/construct_face_options.py <out_dir> [px]

Each style is written with every outline variant the construct needs (see construct_jade_texture.py):
<style>_plain/edge/corner/strip/three/frame.png, RGBA (alpha = how see-through). Every pattern
here wraps round the face, so blocks side by side join without a seam. The four follow J's
reference panels; all share a fine pebbled grain:
  A  constellation - a fine web of cracks with star points where they meet
  B  swirl         - streams of light curling through the jade
  C  crystal cells - glowing seams round crystal cells, stars at the corners
  D  hexagons      - a honeycomb of glowing seams over pebbled cells
  B1, B2 threads   - J's pick after round one: random broken lines in every direction (sparse, dense)
(J dropped C and D; their code stays for reference. Round two writes A, B1 and B2.)
"""
import math, os, sys
import numpy as np
from PIL import Image

OUT = sys.argv[1]
PX = int(sys.argv[2]) if len(sys.argv) > 2 else 128
os.makedirs(OUT, exist_ok=True)
S = PX / 64.0
yy, xx = np.mgrid[0:PX, 0:PX].astype(float) + 0.5


def vnoise(cell, rng):
    g = max(2, int(round(PX / cell)))
    v = rng.random((g, g))
    fx, fy = xx / PX * g, yy / PX * g
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    x0 %= g; y0 %= g; x1 = (x0 + 1) % g; y1 = (y0 + 1) % g
    a = v[y0, x0] * (1 - tx) + v[y0, x1] * tx
    b = v[y1, x0] * (1 - tx) + v[y1, x1] * tx
    return a * (1 - ty) + b * ty


def fbm(rng, cells, weights):
    return sum(vnoise(c * S, rng) * w for c, w in zip(cells, weights)) / sum(weights)


def mixc(col, target, k):
    return col + (np.asarray(target, float) - col) * np.clip(k, 0, 1)[..., None]


def grain(col, rng, amount):
    return col * (1 + amount * rng.normal(0, 1, (PX, PX)))[..., None]


def wrapped_voronoi(rng, n):
    """Nearest and second-nearest distances to n points, wrapping round the face (so it tiles)."""
    pts = rng.random((n, 2)) * PX
    ds = []
    for ox in (-PX, 0, PX):
        for oy in (-PX, 0, PX):
            for px_, py_ in pts:
                ds.append(np.hypot(xx - (px_ + ox), yy - (py_ + oy)))
    ds = np.stack(ds)
    idx = np.argsort(ds, axis=0)
    d0 = np.take_along_axis(ds, idx[:1], 0)[0]
    d1 = np.take_along_axis(ds, idx[1:2], 0)[0]
    return d0, d1, idx[0] % n


def vor(points):
    """Nearest three distances and the nearest point's index for points that wrap round the face."""
    ds = []
    for ox in (-PX, 0, PX):
        for oy in (-PX, 0, PX):
            for px_, py_ in points:
                ds.append(np.hypot(xx - (px_ + ox), yy - (py_ + oy)))
    ds = np.stack(ds)
    idx = np.argsort(ds, axis=0)[:3]
    d = np.take_along_axis(ds, idx, 0)
    return d[0], d[1], d[2], idx[0] % len(points)


def jvor(rng, g):
    """A jittered-grid Voronoi with g x g cells that wraps; cheap for many small cells."""
    jit = rng.random((g, g, 2))
    cs = PX / g
    ix, iy = np.floor(xx / cs).astype(int), np.floor(yy / cs).astype(int)
    d0 = np.full((PX, PX), 1e9); d1 = d0.copy(); ident = np.zeros((PX, PX), int)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = ix + ox, iy + oy
            j = jit[cy % g, cx % g]
            d = np.hypot(xx - (cx + j[..., 0]) * cs, yy - (cy + j[..., 1]) * cs)
            closer = d < d0
            d1 = np.where(closer, d0, np.minimum(d1, d))
            ident = np.where(closer, (cy % g) * g + (cx % g), ident)
            d0 = np.where(closer, d, d0)
    return d0, d1, ident, cs


def pebbles(col, rng, g=30, depth=0.3):
    """The fine pebbled grain all of J's references share: tiny rounded cells, lit in the middle."""
    d0, d1, ident, cs = jvor(rng, g)
    rim = np.clip(((d1 - d0) / 2) / (cs * 0.32), 0, 1)
    tone = rng.uniform(0.85, 1.15, g * g)[ident]
    return col * ((1 - depth) + depth * (0.55 + 0.45 * rim) * tone)[..., None]


def star(col, alpha, x, y, size):
    r = np.hypot(xx - x, yy - y)
    k = np.exp(-(r / (0.8 * size * S)) ** 2) + 0.3 * np.exp(-(r / (2.6 * size * S)) ** 2)
    k += 0.45 * np.exp(-(np.abs(xx - x) / (0.4 * S)) ** 2) * np.exp(-(np.abs(yy - y) / (3.2 * size * S)) ** 2)
    k += 0.45 * np.exp(-(np.abs(yy - y) / (0.4 * S)) ** 2) * np.exp(-(np.abs(xx - x) / (3.2 * size * S)) ** 2)
    return mixc(col, (225, 255, 230), k), np.maximum(alpha, np.clip(k, 0, 1))


BASE = np.array([20, 148, 64.0])
LINE = (150, 255, 175)


# ---- A: constellation cracks: a fine crack web with stars where cracks meet -------------------------
def style_a():
    rng = np.random.default_rng(5)
    cloud = fbm(rng, (40, 16), (1, 0.5))
    col = np.zeros((PX, PX, 3)) + BASE * 0.9
    col *= (0.7 + 0.5 * cloud)[..., None]
    col = pebbles(col, rng, 34, 0.35)
    alpha = 0.42 + 0.2 * cloud
    pts = rng.random((7, 2)) * PX
    d0, d1, d2, _ = vor(pts)
    big = np.exp(-(((d1 - d0) / 2) / (0.45 * S)) ** 2) * (fbm(rng, (14,), (1,)) > 0.32)
    f0, f1, _, _ = jvor(rng, 9)
    fine = np.exp(-(((f1 - f0) / 2) / (0.35 * S)) ** 2) * (fbm(rng, (10,), (1,)) > 0.5) * 0.45
    k = np.clip(big * 0.8 + fine, 0, 1)
    col = mixc(col, LINE, k)
    alpha = np.maximum(alpha, k * 0.8)
    junction = (d2 - d0) < 1.6 * S
    ys, xs_ = np.nonzero(junction)
    for i in range(0, len(xs_), max(1, len(xs_) // 6))[:6]:
        col, alpha = star(col, alpha, xs_[i] + 0.5, ys[i] + 0.5, 1.0)
    return grain(col, rng, 0.03), alpha


# ---- B: swirling flow: streams of light curling through the jade -----------------------------------
def style_b():
    rng = np.random.default_rng(11)
    cloud = fbm(rng, (36, 14), (1, 0.5))
    col = np.zeros((PX, PX, 3)) + np.array([24, 150, 66.0])
    col *= (0.7 + 0.45 * cloud)[..., None]
    col = pebbles(col, rng, 30, 0.25)
    alpha = 0.4 + 0.2 * cloud
    # a field bent twice on itself; its contour lines become the swirling streams
    w1 = fbm(rng, (48, 20), (1, 0.5))
    w2 = fbm(rng, (48, 20), (1, 0.5))
    # a slow wave across the face, bent by two wrapping fields: smooth curling bands
    f = (xx + yy) / PX + 0.55 * np.sin(2 * math.pi * (w1 * 1.5 + yy / PX)) + 0.45 * np.cos(2 * math.pi * (w2 * 1.5 + xx / PX))
    stream = np.sin(2 * math.pi * f * 2.0)
    lines = np.exp(-(stream / 0.32) ** 2)
    lines += 0.45 * np.exp(-(np.sin(2 * math.pi * f * 4.0) / 0.22) ** 2)
    k = lines * (0.35 + 0.65 * fbm(rng, (18,), (1,)))
    col = mixc(col, LINE, k * 0.85)
    alpha = np.maximum(alpha, k * 0.7)
    for _ in range(3):
        col, alpha = star(col, alpha, rng.uniform(10, PX - 10), rng.uniform(10, PX - 10), 0.7)
    return grain(col, rng, 0.03), alpha


# ---- B1, B2: random threads: wandering lines in every direction, broken and uneven -----------------
def threads(seed, layers, width, keep, dim):
    rng = np.random.default_rng(seed)
    cloud = fbm(rng, (36, 14), (1, 0.5))
    col = np.zeros((PX, PX, 3)) + np.array([22, 146, 64.0])
    col *= (0.7 + 0.45 * cloud)[..., None]
    col = pebbles(col, rng, 30, 0.25)
    alpha = 0.4 + 0.2 * cloud
    for i in range(layers):
        # each layer: the contour of its own wrapping field (a wiggly line going wherever it goes),
        # cut into pieces by a second field, at its own brightness
        cell = rng.uniform(18, 46)
        f = fbm(rng, (cell, cell / 2.3), (1, 0.45))
        line = np.exp(-((f - 0.5) / (width * rng.uniform(0.6, 1.4))) ** 2)
        cut = fbm(rng, (rng.uniform(10, 24),), (1,))
        piece = np.clip((cut - (1 - keep)) / 0.08, 0, 1)
        k = line * piece * rng.uniform(dim, 1.0)
        col = mixc(col, LINE, k * 0.85)
        alpha = np.maximum(alpha, k * 0.7)
    for _ in range(2):
        col, alpha = star(col, alpha, rng.uniform(10, PX - 10), rng.uniform(10, PX - 10), 0.6)
    return grain(col, rng, 0.03), alpha


def style_b1():
    return threads(101, 6, 0.016, 0.45, 0.35)


def style_b2():
    return threads(202, 12, 0.011, 0.6, 0.2)


# ---- C: crystal cells: glowing seams round crystal cells, stars at the corners ----------------------
def style_c():
    rng = np.random.default_rng(23)
    pts = rng.random((9, 2)) * PX
    d0, d1, d2, cell = vor(pts)
    col = np.zeros((PX, PX, 3)) + BASE
    col *= rng.uniform(0.75, 1.15, 9)[cell][..., None]
    col *= (0.8 + 0.35 * fbm(rng, (24, 10), (1, 0.5)))[..., None]
    col = pebbles(col, rng, 32, 0.35)
    border = (d1 - d0) / 2
    seam = np.exp(-(border / (0.7 * S)) ** 2)
    halo = np.exp(-(border / (3.2 * S)) ** 2) * 0.3
    col = mixc(col, LINE, seam * 0.9 + halo)
    alpha = np.clip(0.45 + 0.1 * fbm(rng, (30,), (1,)) + 0.45 * seam + 0.2 * halo, 0, 1)
    corner = (d2 - d0) < 1.2 * S
    ys, xs_ = np.nonzero(corner)
    seen = []
    for x, y in zip(xs_, ys):
        if all(math.hypot(x - a, y - b) > 10 * S for a, b in seen):
            seen.append((x, y))
            col, alpha = star(col, alpha, x + 0.5, y + 0.5, 0.8)
    return grain(col, rng, 0.03), alpha


# ---- D: hexagons: a honeycomb of glowing seams, pebbled cells, stars at the joints -------------------
def style_d():
    rng = np.random.default_rng(37)
    n = 4                                       # 4 x 4 hexagons per block face, wrapping
    cs = PX / n
    pts = [((i + 0.5 * (j % 2)) * cs, (j + 0.5) * cs) for j in range(n) for i in range(n)]
    d0, d1, d2, cell = vor(pts)
    col = np.zeros((PX, PX, 3)) + BASE
    col *= (0.78 + 0.35 * fbm(rng, (30, 12), (1, 0.5)))[..., None]
    col = pebbles(col, rng, 40, 0.4)
    border = (d1 - d0) / 2
    seam = np.exp(-(border / (0.8 * S)) ** 2)
    halo = np.exp(-(border / (2.6 * S)) ** 2) * 0.3
    col = mixc(col, LINE, seam * 0.85 + halo)
    alpha = np.clip(0.42 + 0.48 * seam + 0.2 * halo, 0, 1)
    joint = (d2 - d0) < 0.9 * S
    ys, xs_ = np.nonzero(joint)
    seen = []
    for x, y in zip(xs_, ys):
        if all(math.hypot(x - a, y - b) > 6 * S for a, b in seen):
            seen.append((x, y))
            if rng.random() < 0.35:
                col, alpha = star(col, alpha, x + 0.5, y + 0.5, 0.6)
    return grain(col, rng, 0.03), alpha


# ---- outlines, the same for every style --------------------------------------------------------------
EDGE_CORE = np.array([228, 255, 232.0])
EDGE_GLOW = np.array([90, 255, 130.0])
SIDES = {"L": xx - 0.5, "R": PX - xx - 0.5, "T": yy - 0.5, "B": PX - yy - 0.5}
KINDS = {"plain": "", "edge": "L", "corner": "LT", "strip": "LR", "three": "LTR", "frame": "LTRB"}


def outline(img, a, dist):
    core = (dist < 2 * S).astype(float)
    glow = np.exp(-((dist - 2 * S).clip(0) / (3.2 * S)) ** 1.5) * (1 - core)
    img = mixc(img, EDGE_GLOW, glow * 0.85)
    img = mixc(img, EDGE_CORE, core)
    return img, np.maximum(a, np.clip(core + glow * 0.9, 0, 1))


for name, fn in (("A", style_a), ("B1", style_b1), ("B2", style_b2)):
    base, base_a = fn()
    for kind, sides in KINDS.items():
        img, a = np.clip(base, 0, 255), base_a.copy()
        for sd in sides:
            img, a = outline(img, a, SIDES[sd])
        rgba = np.concatenate([np.clip(img, 0, 255), (np.clip(a, 0, 1) * 255)[..., None]], -1)
        Image.fromarray(rgba.astype(np.uint8), "RGBA").save(os.path.join(OUT, f"{name}_{kind}.png"))
print("wrote styles A, B1, B2 at", PX, "px to", OUT)
