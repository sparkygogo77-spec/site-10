"""Green Lantern construct blocks as crystal jade, one texture per block face (J's direction: each face
stands alone, no blending across blocks): python tools/construct_jade_texture.py <out_dir> [px]

Writes six faces at px x px (default 64, 64 per block), the same jade with the outline on 0-4 sides:
- jade_plain.png:  the surface, crystal jade. A handful of flat crystal planes (a wrapped Voronoi
  split), each its own shade of green with a slight gradient so it reads as a facet catching light;
  glowing cracks where planes meet (some strong, some faint, some missing); a few hair-line inner
  fractures; three or four bright sparks inside; a soft bevel so blocks read as stacked stones.
- jade_edge.png:   the same with a bright outline down its left side: the construct's outer edge.
- jade_corner.png: outlines down the left and along the top: a corner of the construct.
- jade_strip.png, jade_three.png, jade_frame.png: left and right; left, top and right; all four.
The outline is the brightest thing on the block, brighter than any crack, as J asked. Rotating the
edge and corner faces puts the outline on whichever side a block needs.
"""
import math, os, random, sys
import numpy as np
from PIL import Image

OUT = sys.argv[1]
PX = int(sys.argv[2]) if len(sys.argv) > 2 else 64
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(2814)
S = PX / 64.0                                   # scale for sizes given at 64 px

yy, xx = np.mgrid[0:PX, 0:PX].astype(float) + 0.5
nrng = np.random.default_rng(2814)
# Anything that does not wrap round the face (planes, cracks, sparks) fades out toward its edges,
# so where two blocks meet only the wrapping clouds and grain touch: no lines that fail to match.
_e = np.minimum(np.minimum(xx, yy), np.minimum(PX - xx, PX - yy)) / (0.18 * PX)
edgefade = np.clip(_e, 0, 1) ** 2 * (3 - 2 * np.clip(_e, 0, 1))


def vnoise(cell):
    """Smooth value noise with blobs about `cell` pixels across, 0..1, wrapping at the face's edges."""
    g = max(2, int(round(PX / cell)))
    v = nrng.random((g, g))
    fx, fy = xx / PX * g, yy / PX * g
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    x0 %= g; y0 %= g; x1 = (x0 + 1) % g; y1 = (y0 + 1) % g
    a = v[y0, x0] * (1 - tx) + v[y0, x1] * tx
    b = v[y1, x0] * (1 - tx) + v[y1, x1] * tx
    return a * (1 - ty) + b * ty


def fbm(cells, weights):
    return sum(vnoise(c * S) * w for c, w in zip(cells, weights)) / sum(weights)


# cracks wander: the crystal planes are split on gently warped coordinates
wx = (fbm((16, 6), (1, 0.5)) - 0.5) * 7 * S
wy = (fbm((16, 6), (1, 0.5)) - 0.5) * 7 * S
XW, YW = xx + wx, yy + wy

# ---- crystal planes: a Voronoi split of the face ------------------------------------------------
cells = [(rnd.uniform(0, PX), rnd.uniform(0, PX)) for _ in range(8)]
d = np.stack([np.hypot(XW - cx, YW - cy) for cx, cy in cells])
order = np.argsort(d, axis=0)
near, second = order[0], order[1]
d0 = np.take_along_axis(d, order[:1], 0)[0]
d1 = np.take_along_axis(d, order[1:2], 0)[0]
border = (d1 - d0) / 2                           # distance to the line between the two nearest cells

col = np.zeros((PX, PX, 3))
for i, (cx, cy) in enumerate(cells):
    m = near == i
    base = np.array([rnd.uniform(8, 26), rnd.uniform(78, 150), rnd.uniform(38, 70)])
    ang = rnd.uniform(0, 2 * math.pi)
    g = ((xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)) / PX      # facet gradient
    shade = 1 + 0.55 * g + rnd.uniform(-0.08, 0.08)
    col[m] = base * shade[m][:, None]

# the planes are only a hint inside the stone, and none at the edges
JADE = np.array([16.0, 112.0, 54.0])
col = JADE + (col - JADE) * (0.45 * edgefade)[..., None]
# depth: the middle of each plane slightly brighter, as if lit from inside the stone
col *= (1 + edgefade * (-0.12 + 0.2 * np.clip(d1 - d0, 0, 18 * S) / (18 * S)))[..., None]

# ---- stone-like detail, down to single pixels ----------------------------------------------------
# cloudy mottling, as in real jade: darker and lighter clouds, the hue drifting between a cool
# blue-green and a warmer leaf green
cloud = fbm((32, 14, 6), (1, 0.6, 0.35))
hue = fbm((40, 18), (1, 0.5))
col *= (0.72 + 0.56 * cloud)[..., None]
col += np.stack([(hue - 0.5) * 22, (hue - 0.5) * 10, (0.5 - hue) * 26], -1)
# fibrous grain: faint parallel veins running through the stone, bent by the warp
fib = np.sin((xx * 0.55 + yy * 0.83 + wx * 2.2) / (1.3 * S)) * fbm((10,), (1,))
col *= (1 + 0.10 * fib)[..., None]
# grain: every pixel a touch lighter or darker, like the grain of stone
grain = nrng.normal(0, 1, (PX, PX))
col *= (1 + 0.075 * grain)[..., None]
# mineral flecks: pale specks and dark inclusions, one or two pixels
# clustered, not sprinkled evenly: thick in some patches, almost none in others
fleck = nrng.random((PX, PX)) * (0.55 + 0.9 * fbm((12,), (1,)))
col[fleck > 0.985] = col[fleck > 0.985] * 0.6 + np.array([110, 190, 130.0]) * 0.4
inclusion = fleck < 0.012
col[inclusion] *= 0.42
# pits: a dark pixel with a lit pixel just below it, as if the stone were chipped
pit = nrng.random((PX, PX)) < 0.012
col[pit] *= 0.5
below = np.roll(pit, 1, axis=0)
col[below & ~pit] = col[below & ~pit] * 1.28 + 6

# ---- glowing cracks where planes meet --------------------------------------------------------------
CRACK = np.array([150, 255, 175.0])
strength = {}
for i in range(len(cells)):
    for j in range(i + 1, len(cells)):
        r = rnd.random()
        strength[(i, j)] = 0.0 if r < 0.25 else rnd.uniform(0.35, 1.0)
a, b = np.minimum(near, second), np.maximum(near, second)
st = np.vectorize(lambda p, q: strength[(p, q)])(a, b)
w = np.exp(-(border / (0.9 * S)) ** 2) * st * 0.45 * edgefade   # the crack: soft, deep in the stone
halo = np.exp(-(border / (3.5 * S)) ** 2) * st * 0.22 * edgefade   # its glow in the jade around it
# translucency: the jade is see-through, cloudier in patches, the cracks solid light
alpha = 0.40 + 0.30 * cloud ** 1.5
alpha = np.clip(alpha + 0.35 * w + 0.25 * halo, 0, 1)
col = col + (CRACK - col) * np.clip(w + halo, 0, 1)[..., None]

# ---- hair-line fractures inside the planes ---------------------------------------------------------
for _ in range(5):
    x0, y0 = rnd.uniform(0, PX), rnd.uniform(0, PX)
    ang = rnd.uniform(0, math.pi)
    ln = rnd.uniform(8, 20) * S
    t = np.clip((xx - x0) * math.cos(ang) + (yy - y0) * math.sin(ang), 0, ln)
    px_, py_ = x0 + t * math.cos(ang), y0 + t * math.sin(ang)
    dist = np.hypot(xx - px_, yy - py_)
    col = col + (np.array([90, 210, 120.0]) - col) * (np.exp(-(dist / (0.6 * S)) ** 2) * 0.3 * edgefade)[..., None]

# ---- sparks: bright points of light inside the stone ----------------------------------------------
for _ in range(2):
    sx, sy = rnd.uniform(0.3 * PX, 0.7 * PX), rnd.uniform(0.3 * PX, 0.7 * PX)
    r = np.hypot(xx - sx, yy - sy)
    star = np.exp(-(r / (0.9 * S)) ** 2) + 0.35 * np.exp(-(r / (3.0 * S)) ** 2)
    # four short rays
    star += 0.5 * np.exp(-(np.abs(xx - sx) / (0.45 * S)) ** 2) * np.exp(-(np.abs(yy - sy) / (3.5 * S)) ** 2)
    star += 0.5 * np.exp(-(np.abs(yy - sy) / (0.45 * S)) ** 2) * np.exp(-(np.abs(xx - sx) / (3.5 * S)) ** 2)
    col = col + (np.array([200, 255, 215.0]) - col) * np.clip(star * 0.6, 0, 1)[..., None]
    alpha = np.maximum(alpha, np.clip(star * 0.7, 0, 1))

plain = np.clip(col, 0, 255)
# flecks and chips are solid grit inside the stone
alpha = np.where(inclusion | pit | (fleck > 0.985), np.maximum(alpha, 0.7), alpha)
plain_alpha = alpha

# ---- the outline: the construct's own edge, brighter than anything else on it ---------------------
EDGE_CORE = np.array([228, 255, 232.0])
EDGE_GLOW = np.array([90, 255, 130.0])


def outline(img, dist, a):
    """Adds the bright edge line along pixels `dist` from the outer side."""
    core = (dist < 2 * S).astype(float)
    glow = np.exp(-((dist - 2 * S).clip(0) / (3.2 * S)) ** 1.5) * (1 - core)
    img = img + (EDGE_GLOW - img) * (glow * 0.85)[..., None]
    img = img + (EDGE_CORE - img) * core[..., None]
    return img, np.maximum(a, np.clip(core + glow * 0.9, 0, 1))


# Every way a face's sides can lie on the construct's outer edge, up to turning the face:
# none, one, two meeting (corner), two opposite (strip), three, all four (a lone block's face).
SIDES = {"L": xx - 0.5, "R": PX - xx - 0.5, "T": yy - 0.5, "B": PX - yy - 0.5}
KINDS = {"plain": "", "edge": "L", "corner": "LT", "strip": "LR", "three": "LTR", "frame": "LTRB"}
for name, sides in KINDS.items():
    img, a = plain.copy(), plain_alpha.copy()
    for sd in sides:
        img, a = outline(img, SIDES[sd], a)
    rgba = np.concatenate([np.clip(img, 0, 255), (a * 255)[..., None]], -1)
    Image.fromarray(rgba.astype(np.uint8), "RGBA").save(os.path.join(OUT, "jade_" + name + ".png"))
print("wrote", ", ".join("jade_" + k for k in KINDS), "at", PX, "px to", OUT)
