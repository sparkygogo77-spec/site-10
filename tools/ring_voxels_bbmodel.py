"""Exports a ring from a Blender ring pass (800+) as a worn-ring Blockbench model for the game, in the layout
tools/ring_bbmodel.py uses (RingModels.Placement, 16 units = 1 skin pixel, one voxel = one unit; x across the finger,
y out of the fist with the face up, z along the finger; the band reaching DROP units down into the fist).

The ring is rebuilt from the pass script itself, so the model is exactly what J picked in Blender:

    python3 tools/ring_voxels_bbmodel.py docs/blender/blender_updates/800_ring_picks.update.py LLDIR R19d OUTDIR ring_r19d
    (add "noicon" as a 6th argument to leave the mark off the face, e.g. R16a for J)

Needs bpy (the pass script builds its scene first). Writes OUTDIR/bbmodel/<name>.bbmodel and
OUTDIR/textures/entity/bb/<name>.png. Lit parts (the stone, the lines of light, the textured band) are "glow" cubes,
which the game draws full-bright in the corps colour; metal and gold are "body" cubes. Each textured part is painted
with frame 0 of its strip (W1 / H1 / X5), shaded as in Blender; the game texture is static.
"""
import io, os, sys, math, base64, json, uuid
import numpy as np
import bpy
from PIL import Image

SRC, LL, CODE, OUT, NAME = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["LL_NO_RENDER"] = "1"
g = {"bpy": bpy, "np": np, "FOLDER": LL, "__name__": "__ll__"}
exec(compile(open(SRC).read(), SRC, "exec"), g)
t = dict(next(x for x in g["TAKES"] if x["code"] == CODE))
if len(sys.argv) > 6 and sys.argv[6] == "noicon":
    _mm = g["mark_mask"]
    g["mark_mask"] = lambda key: np.zeros((15, 15), bool) if key == "NONE" else _mm(key)
    t["mark"] = "NONE"
rng = np.random.default_rng(1)
build = g["build_ring"] if t["builder"] == "square" else g["build_classic"]
K, C, GL, DI, (x0, y0, zf, fw) = build(t, rng)
METAL, GOLD, GEM, CORE, DARK, BANDTEX = range(6)
if t.get("band_tex"):
    K[K == METAL] = BANDTEX
NX, NY, NZ = K.shape


def strip0(key):
    im = Image.open(os.path.join(LL, "suit_tex", key + "_strip.png")).convert("RGB")
    w = im.width
    return np.asarray(im.crop((0, 0, w, w)), float) / 255.0


TEX = {GEM: strip0(g["TEXES"][t["gem"]][0])}
if t.get("band_tex"):
    TEX[BANDTEX] = strip0(g["TEXES"][t["band_tex"]][0])
cx, cy = x0 + fw / 2, y0 + fw / 2


def voxel_rgb(i, j, k):
    kind = int(K[i, j, k]); lin = C[i, j, k]
    if kind in TEX:
        tex = TEX[kind]; n = tex.shape[0]
        u = ((i + 0.5 - cx) / fw + 0.5) % 1.0; v = ((j + 0.5 - cy) / fw + 0.5) % 1.0
        tc = tex[int((1 - v) * n) % n, int(u * n) % n] ** 2.2          # to linear
        shade = np.clip(lin * 3.2, 0, 1)
        lin = tc * (0.15 + 0.85 * shade)
    srgb = np.clip(lin, 0, 1) ** (1 / 2.2)
    return tuple(int(c * 255) for c in srgb) + (255,)


# ---- the Blockbench model (Model class from tools/blockbench_models.py)
A = OUT
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
DROP = -8.0
zc = 18.0                                   # the band's centre height in the pass builder
xc_, yc_ = NX / 2, NY / 2


def boxes(mask):
    m = mask.copy(); out = []; S = m.shape
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


occ = K >= 0
# hidden voxels (all six neighbours filled) can join any box: fill them into every kind's mask as "don't care"
pad = np.zeros((NX + 2, NY + 2, NZ + 2), bool); pad[1:-1, 1:-1, 1:-1] = occ
hidden = occ.copy()
for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
    hidden &= pad[1 + dx:NX + 1 + dx, 1 + dy:NY + 1 + dy, 1 + dz:NZ + 1 + dz]
model = Model(NAME, density=1)
n = 0
used = np.zeros_like(occ)
for kind in (METAL, GOLD, BANDTEX, GEM, DARK, CORE):
    mask = (K == kind) & ~used
    if not mask.any():
        continue
    glow = kind in (GEM, CORE, BANDTEX)
    for (i, j, k, i2, j2, k2) in boxes(mask):
        used[i:i2 + 1, j:j2 + 1, k:k2 + 1] = True
        # pass grid: x along the finger, y across, z up  ->  bb: x = across (y), y = up (z), z = along (x)
        frm = [j - yc_, k - zc + DROP, i - xc_]
        to = [j2 + 1 - yc_, k2 + 1 - zc + DROP, i2 + 1 - xc_]

        def paint(face, w, h, b=(i, j, k, i2, j2, k2)):
            I, J, Kz, I2, J2, K2 = b
            rows = []
            for yy in range(h):
                row = []
                for xx in range(w):
                    # pick the voxel behind this texel on that face (orientation approximate; the patterns are symmetric)
                    if face == "up":
                        vi, vj, vk = I + min(yy, I2 - I), J + min(xx, J2 - J), K2
                    elif face == "down":
                        vi, vj, vk = I + min(yy, I2 - I), J + min(xx, J2 - J), Kz
                    elif face in ("north", "south"):
                        vi, vj, vk = (I if face == "north" else I2), J + min(xx, J2 - J), K2 - min(yy, K2 - Kz)
                    else:
                        vi, vj, vk = I + min(xx, I2 - I), (J if face == "west" else J2), K2 - min(yy, K2 - Kz)
                    row.append(voxel_rgb(vi, vj, vk) if K[vi, vj, vk] >= 0 else (0, 0, 0, 0))
                rows.append(row)
            return rows
        model.cube(f"{'glow' if glow else 'body'}_{n}", frm, to, paint)
        n += 1
model.write()
top = max(c["to"][1] for c in model.cubes)
print(NAME, len(model.cubes), "cubes; face top", top, "units =", round(top / 16, 3), "skin px")
