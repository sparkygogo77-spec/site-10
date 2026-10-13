"""Exports a pixel-grid ring (tools/pixel_ring.py) as a worn-ring Blockbench model, in the layout the
other worn rings use (RingModels.Placement, 16 units = 1 skin pixel): x across the finger, y out of the fist
(the face up), z along the finger, the band reaching down into the fist like ring_forged. One voxel = 1 unit.
The gem and the lit parts are "glow" cubes (full-bright in the corps colour).

    python tools/ring_bbmodel.py src/main/resources/assets/lanternring b ring_crown
"""
import base64, io, json, math, os, sys, uuid
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
VAR = sys.argv[2] if len(sys.argv) > 2 else "b"
NAME = sys.argv[3] if len(sys.argv) > 3 else "ring_crown"
_argv, sys.argv = sys.argv, ["pixel_ring.py", "/tmp"]
import pixel_ring as PR  # noqa: E402
sys.argv = _argv

CLEAR = (0, 0, 0, 0)
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
exec(_src[_src.index("def _texel("):_src.index("AXES = {")])

UNIT = 1 / PR.G          # bb units per model pixel (one voxel = one unit)
DROP = -8.0              # the band reaches this far down into the fist, like ring_forged


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


def shade(base, face, kind, centre):
    col = np.array(base, float)
    if kind == 1:            # metal: lit where it faces out of the finger, darker underneath
        n = {"up": (0, 0, 1), "down": (0, 0, -1), "east": (-1, 0, 0), "west": (1, 0, 0), "north": (0, 0, 0), "south": (0, 0, 0)}[face]
        out = np.dot(n, np.array([centre[0], 0, centre[2]]) / (math.hypot(centre[0], centre[2]) + 1e-6))
        col *= 0.75 + 0.45 * max(0.0, out) + (0.15 if face == "up" else 0) - (0.2 if face in ("north", "south") else 0)
    return tuple(int(min(255, max(0, c))) for c in col) + (255,)


if __name__ == "__main__":
    part = PR.build(VAR)
    xs = PR.A
    model = Model(NAME, density=1)
    n = 0
    for pid, (base, kind) in PR.COL[VAR].items():
        mask = part == pid
        if not mask.any():
            continue
        glow = kind in (4, 6)
        for (i, j, k, i2, j2, k2) in boxes(mask):
            x0, x1 = PR.X[i, 0, 0] - PR.G / 2, PR.X[i2, 0, 0] + PR.G / 2
            y0, y1 = PR.Y[0, j, 0] - PR.G / 2, PR.Y[0, j2, 0] + PR.G / 2
            z0, z1 = PR.Z[0, 0, k] - PR.G / 2, PR.Z[0, 0, k2] + PR.G / 2
            # ours: x across, y along the finger, z out of the fist -> bb: x, y = out, z = along
            frm = [round(x0 * UNIT, 3), round(z0 * UNIT + DROP, 3), round(y0 * UNIT, 3)]
            to = [round(x1 * UNIT, 3), round(z1 * UNIT + DROP, 3), round(y1 * UNIT, 3)]
            centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])

            def paint(face, w, h, base=base, kind=kind, centre=centre):
                c = shade(base, face, kind, centre)
                return [[c] * w for _ in range(h)]
            model.cube(f"{'glow' if glow else 'body'}_{n}", frm, to, paint)
            n += 1
    model.write()
    top = max(c["to"][1] for c in model.cubes)
    print(NAME, len(model.cubes), "cubes; face top", top, "units =", round(top / 16, 3), "skin px")
