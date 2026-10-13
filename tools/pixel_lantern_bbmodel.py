"""Writes the pixel-grid Blue Lantern (tools/pixel_blue_lantern.py) as the Blockbench model the mod
draws: assets/lanternring/bbmodel/blue_lantern.bbmodel and textures/entity/bb/blue_lantern.png.
Neighbouring cubes of the same part are merged into as few boxes as possible, and every box face is
painted from the pixel art at 8 texture pixels per unit (128 per block; outside the emblem glass
each 64-per-block pixel is simply 2 x 2 of them). Glass boxes are named glow_* so they draw
full-bright. Run tools/bbmodel_json.py afterwards for the placed block and item models.

    python tools/pixel_lantern_bbmodel.py src/main/resources/assets/lanternring [--grid 0.5]
"""
import base64, io, json, math, os, sys, uuid
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_blue_lantern as L

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
GRID = float(sys.argv[sys.argv.index("--grid") + 1]) if "--grid" in sys.argv else 0.5
DENSITY = 8
ONLY = None
CLEAR = (0, 0, 0, 0)

# blockbench_models.py's Model (box-UV packing and the .bbmodel writer) and its _texel mapping,
# taken from its source so this does not run that whole generator
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
exec(_src[_src.index("def _texel("):_src.index("AXES = {")])

L.build(GRID)
G = L.G
part, occ, xs, zs = L.part, L.occ, L.xs, L.zs


def boxes(mask):
    """Greedy 3-D merge: grow each box along x, then y, then z while every cube is in ``mask``."""
    m = mask.copy()
    out = []
    S = m.shape
    for k in range(S[2]):
        for j in range(S[1]):
            for i in range(S[0]):
                if not m[i, j, k]:
                    continue
                i2 = i
                while i2 + 1 < S[0] and m[i2 + 1, j, k]:
                    i2 += 1
                j2 = j
                while j2 + 1 < S[1] and m[i:i2 + 1, j2 + 1, k].all():
                    j2 += 1
                k2 = k
                while k2 + 1 < S[2] and m[i:i2 + 1, j:j2 + 1, k2 + 1].all():
                    k2 += 1
                m[i:i2 + 1, j:j2 + 1, k:k2 + 1] = False
                out.append((i, j, k, i2, j2, k2))
    return out


# model (x right, y back, z up) -> Blockbench (X, Y up, Z; front faces north = -Z)
def to_bb(x, y, z):
    return (-x, z, y)


FACE_N = {"north": (0, -1, 0), "south": (0, 1, 0), "east": (-1, 0, 0), "west": (1, 0, 0), "up": (0, 0, 1), "down": (0, 0, -1)}
SNAP = L.T


def painter(pid, frm, to):
    fine = pid == L.EMBLEM

    def paint(face, w, h):
        n = np.array(FACE_N[face], float)
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y])
                if not fine:   # 64-per-block pixels: every 2 x 2 texture pixels share one colour
                    for a in range(3):
                        if abs(n[a]) < 0.5:
                            q[a] = (math.floor(q[a] / SNAP) + 0.5) * SNAP
                col, kind = L.shade_pixel(pid, q, n)
                row.append(tuple(int(round(min(255, max(0, c)))) for c in col) + (255,))
            rows.append(row)
        return rows
    return paint


model = Model("blue_lantern", density=DENSITY)
names = {L.STONE: "stone", L.FRAME: "frame", L.EMBLEM: "glow_emblem", L.LENS: "glow_lens", L.PORT: "port",
         L.HOLLOW: "port_cup", L.BRONZE: "collar", L.CAPTOP: "cap_top", L.HANDLE: "handle", L.FOOT: "foot"}
count = 0
for pid, nm in names.items():
    for n_, (i, j, k, i2, j2, k2) in enumerate(boxes(part == pid)):
        x0, x1 = xs[i] - G / 2, xs[i2] + G / 2
        y0, y1 = xs[j] - G / 2, xs[j2] + G / 2
        z0, z1 = zs[k] - G / 2, zs[k2] + G / 2
        a, b = to_bb(x1, y0, z0), to_bb(x0, y1, z1)
        frm = [round(min(a[c], b[c]), 4) for c in range(3)]
        to = [round(max(a[c], b[c]), 4) for c in range(3)]
        model.cube(f"{nm}_{n_}", frm, to, painter(pid, frm, to))
        count += 1
print(f"{count} boxes from {int(occ.sum()):,} cubes")
model.write()
