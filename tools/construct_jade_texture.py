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

# ---- crystal planes: a Voronoi split of the face ------------------------------------------------
cells = [(rnd.uniform(0, PX), rnd.uniform(0, PX)) for _ in range(8)]
d = np.stack([np.hypot(xx - cx, yy - cy) for cx, cy in cells])
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

# depth: the middle of each plane slightly brighter, as if lit from inside the stone
col *= (0.82 + 0.3 * np.clip(d1 - d0, 0, 18 * S)[..., None] / (18 * S))

# ---- glowing cracks where planes meet --------------------------------------------------------------
CRACK = np.array([150, 255, 175.0])
strength = {}
for i in range(len(cells)):
    for j in range(i + 1, len(cells)):
        r = rnd.random()
        strength[(i, j)] = 0.0 if r < 0.25 else rnd.uniform(0.35, 1.0)
a, b = np.minimum(near, second), np.maximum(near, second)
st = np.vectorize(lambda p, q: strength[(p, q)])(a, b)
w = np.exp(-(border / (0.7 * S)) ** 2) * st                 # the crack line itself
halo = np.exp(-(border / (2.6 * S)) ** 2) * st * 0.35      # its glow in the jade around it
col = col + (CRACK - col) * np.clip(w + halo, 0, 1)[..., None]

# ---- hair-line fractures inside the planes ---------------------------------------------------------
for _ in range(5):
    x0, y0 = rnd.uniform(0, PX), rnd.uniform(0, PX)
    ang = rnd.uniform(0, math.pi)
    ln = rnd.uniform(8, 20) * S
    t = np.clip((xx - x0) * math.cos(ang) + (yy - y0) * math.sin(ang), 0, ln)
    px_, py_ = x0 + t * math.cos(ang), y0 + t * math.sin(ang)
    dist = np.hypot(xx - px_, yy - py_)
    col = col + (np.array([90, 210, 120.0]) - col) * (np.exp(-(dist / (0.5 * S)) ** 2) * 0.55)[..., None]

# ---- sparks: bright points of light inside the stone ----------------------------------------------
for _ in range(4):
    sx, sy = rnd.uniform(6, PX - 6), rnd.uniform(6, PX - 6)
    r = np.hypot(xx - sx, yy - sy)
    star = np.exp(-(r / (0.9 * S)) ** 2) + 0.35 * np.exp(-(r / (3.0 * S)) ** 2)
    # four short rays
    star += 0.5 * np.exp(-(np.abs(xx - sx) / (0.45 * S)) ** 2) * np.exp(-(np.abs(yy - sy) / (3.5 * S)) ** 2)
    star += 0.5 * np.exp(-(np.abs(yy - sy) / (0.45 * S)) ** 2) * np.exp(-(np.abs(xx - sx) / (3.5 * S)) ** 2)
    col = col + (np.array([225, 255, 230.0]) - col) * np.clip(star, 0, 1)[..., None]

# ---- a soft bevel: lit top and left rim, shadowed bottom and right ---------------------------------
e = 2 * S
lit = np.exp(-xx / e) + np.exp(-yy / e)
dark = np.exp(-(PX - xx) / e) + np.exp(-(PX - yy) / e)
col = col * (1 + 0.25 * np.clip(lit, 0, 1) - 0.35 * np.clip(dark, 0, 1))[..., None]
plain = np.clip(col, 0, 255)

# ---- the outline: the construct's own edge, brighter than anything else on it ---------------------
EDGE_CORE = np.array([228, 255, 232.0])
EDGE_GLOW = np.array([90, 255, 130.0])


def outline(img, dist):
    """Adds the bright edge line along pixels `dist` from the outer side."""
    core = (dist < 2 * S).astype(float)
    glow = np.exp(-((dist - 2 * S).clip(0) / (3.2 * S)) ** 1.5) * (1 - core)
    img = img + (EDGE_GLOW - img) * (glow * 0.85)[..., None]
    img = img + (EDGE_CORE - img) * core[..., None]
    return img


# Every way a face's sides can lie on the construct's outer edge, up to turning the face:
# none, one, two meeting (corner), two opposite (strip), three, all four (a lone block's face).
SIDES = {"L": xx - 0.5, "R": PX - xx - 0.5, "T": yy - 0.5, "B": PX - yy - 0.5}
KINDS = {"plain": "", "edge": "L", "corner": "LT", "strip": "LR", "three": "LTR", "frame": "LTRB"}
for name, sides in KINDS.items():
    img = plain.copy()
    for sd in sides:
        img = outline(img, SIDES[sd])
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(OUT, "jade_" + name + ".png"))
print("wrote", ", ".join("jade_" + k for k in KINDS), "at", PX, "px to", OUT)
