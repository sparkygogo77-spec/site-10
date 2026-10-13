"""Writes the pixel-grid Dark Lantern (tools/pixel_dark_lantern4.py) as the Blockbench model the mod
draws: assets/lanternring/bbmodel/dark_lantern.bbmodel and textures/entity/bb/dark_lantern.png, the
model the held, placed and dropped Dark Lantern use. Neighbouring cubes of the same part merge into
as few boxes as possible; every box face is painted pixel by pixel with the same colours Blender
shows (face_colour), 4 texture pixels per unit = one per model pixel. Nothing is full-bright: the
lantern is dark at rest, as J wants. Run tools/bbmodel_json.py afterwards.

    python tools/pixel_dark_bbmodel.py src/main/resources/assets/lanternring [version, default l1]
"""
import math, os, sys
import numpy as np
import base64, io, json, uuid
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
VER = sys.argv[2] if len(sys.argv) > 2 else "l1"
_argv, sys.argv = sys.argv, ["pixel_dark_lantern4.py", "/tmp/dark_unused"]
import pixel_dark_lantern4 as D
sys.argv = _argv

DENSITY = 4
CLEAR = (0, 0, 0, 0)
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
exec(_src[_src.index("def _texel("):_src.index("AXES = {")])

p = D.VERSIONS[VER]
xs, zs, part, pz = D.build(p)
G = D.G
ZSHIFT = 0.75   # the model's foot starts 0.75 up; stand it on the block's floor


def boxes(mask):
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


def to_bb(x, y, z):
    return (-x, z, y)


FACE_N = {"north": (0, -1, 0), "south": (0, 1, 0), "east": (-1, 0, 0), "west": (1, 0, 0), "up": (0, 0, 1), "down": (0, 0, -1)}
x0g, z0g = xs[0] - G / 2, zs[0] - G / 2


def painter(pid, frm, to):
    def paint(face, w, h):
        n = FACE_N[face]
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2      # back inside the cube this face belongs to
                i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                c = np.array([xs[i], xs[j], zs[k]])
                col, kind = D.face_colour(pid, i, j, k, n, c, p)
                row.append(tuple(int(round(min(255, max(0, v_)))) for v_ in col) + (255,))
            rows.append(row)
        return rows
    return paint


model = Model("dark_lantern", density=DENSITY)
count = 0


def any_painter(frm, to):
    def paint(face, w, h):
        n = FACE_N[face]
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2
                i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                c = np.array([xs[i], xs[j], zs[k]])
                col, kind = D.face_colour(int(part[i, j, k]), i, j, k, n, c, p)
                row.append(tuple(int(round(min(255, max(0, v_)))) for v_ in col) + (255,))
            rows.append(row)
        return rows
    return paint


# Performance (J: 140 -> 70 fps): every box costs the same to draw however big, so the whole lantern
# is merged as one shape, not part by part; each texel still takes its own part's colour.
for n_, (i, j, k, i2, j2, k2) in enumerate(boxes(part > 0)):
    x0, x1 = xs[i] - G / 2, xs[i2] + G / 2
    y0, y1 = xs[j] - G / 2, xs[j2] + G / 2
    z0, z1 = zs[k] - G / 2 - ZSHIFT, zs[k2] + G / 2 - ZSHIFT
    a, b = to_bb(x1, y0, z0), to_bb(x0, y1, z1)
    frm = [round(min(a[c], b[c]), 4) for c in range(3)]
    to = [round(max(a[c], b[c]), 4) for c in range(3)]
    model.cube(f"body_{n_}", frm, to, any_painter(frm, to))
    count += 1


# the charge light (J): a ball of light at the bulge, light swirling round the centre, flares running
# out of it up and down. Baked from the same field as Blender's charge material into FRAMES looping
# textures of a separate glow model (dark_lantern_glow); the mod cross-fades them while it charges.
FRAMES = 12
PERIOD = 2.5                     # seconds per loop: the swirl turns once, the flares leave twice
FRAME = [0]


def light_at(q, gw, t):
    x, y, z = q
    dz = z - pz
    ang = math.atan2(y, x)
    rad = math.hypot(x, y)
    w = 2 * math.pi / PERIOD
    ball = math.exp(-((math.sqrt(dz * dz + 0.25 * rad * rad)) / 8.5) ** 2)
    swirl = ((math.sin(3 * ang + 0.55 * dz + w * t) + 1) / 2) ** 3
    brk = 0.5 + 0.5 * math.sin(1.3 * ang + 0.35 * z + w * t) * math.cos(0.9 * ang - 0.25 * z)
    flare = ((math.sin(0.9 * abs(dz) - 2 * w * t) + 1) / 2) ** 6 * brk ** 2 * math.exp(-abs(dz) / 8.5)
    light = 1.2 * ball + (0.45 * swirl + 1.3 * flare) * (0.2 + ball)
    return light * (0.35 + gw)


RAMP = [(0.0, (0, 26, 8)), (0.2, (0, 90, 20)), (0.42, (5, 190, 46)), (0.62, (46, 255, 76)), (0.8, (150, 255, 90)),
        (1.0, (255, 255, 140))]


def ramp(v):
    v = max(0.0, min(1.0, v))
    for (p0, c0), (p1, c1) in zip(RAMP, RAMP[1:]):
        if v <= p1:
            f = (v - p0) / (p1 - p0)
            return [c0[i] + (c1[i] - c0[i]) * f for i in range(3)]
    return list(RAMP[-1][1])


def glow_painter(frm, to):
    def paint(face, w, h):
        n = FACE_N[face]
        t = FRAME[0] / FRAMES * PERIOD
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2
                i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                c = np.array([xs[i], xs[j], zs[k]])
                pid = int(part[i, j, k])
                gw = D.glow_weight(pid, i, j, k, c, p, pz) if pid else 0.0
                hv = ((i * 2654435761) ^ (j * 40503) ^ (k * 2246822519)) & 255
                L = light_at(c, gw, t)
                col = np.array(ramp(L * 0.85 + 0.15 * hv / 255)) * min(1.0, (L * L) * 0.55)
                rgb = tuple(int(round(min(255, max(0, v_)))) for v_ in col)
                row.append(rgb + (min(255, int(max(rgb) * 1.4)),))     # see-through where dark (shader packs)
            rows.append(row)
        return rows
    return paint


glow_model = Model("dark_lantern_glow", density=DENSITY)
glowable = np.isin(part, [D.SMOKE, D.RIB, D.PLATE, D.VEIN, D.SOCKET])
for n_, (i, j, k, i2, j2, k2) in enumerate(boxes(glowable)):
    x0, x1 = xs[i] - G / 2, xs[i2] + G / 2
    y0, y1 = xs[j] - G / 2, xs[j2] + G / 2
    z0, z1 = zs[k] - G / 2 - ZSHIFT, zs[k2] + G / 2 - ZSHIFT
    a, b = to_bb(x1, y0, z0), to_bb(x0, y1, z1)
    frm = [round(min(a[c], b[c]), 4) for c in range(3)]
    to = [round(max(a[c], b[c]), 4) for c in range(3)]
    glow_model.cube(f"glow_{n_}", frm, to, glow_painter(frm, to), inflate=0.02)
FRAME[0] = 0
glow_model.write()
for f in range(1, FRAMES):
    FRAME[0] = f
    glow_model.texture().save(f"{A}/textures/entity/bb/dark_lantern_glow_{f}.png", optimize=True)
print("glow model:", len(glow_model.cubes), "boxes,", FRAMES, "frames")
print(f"{count} boxes from {int((part > 0).sum()):,} cubes")
model.write()
