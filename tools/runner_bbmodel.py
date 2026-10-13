"""Exports the Dread Runner (tools/pixel_dread_runner.py) for the game: one Blockbench model per body part
(bbmodel/dread_runner_<part>.bbmodel + textures/entity/bb/dread_runner_<part>.png), each with its joint at
the origin, and bbmodel/dread_runner_rig.json with every joint's pivot (model pixels, Blockbench axes),
its parent, and the 12-frame sprint (degrees per joint per frame, the same stride Blender plays). The game
thread draws the parts down the chain, turning each about its joint. Run tools/bbmodel_json.py afterwards
only if block models are wanted (they aren't needed for an entity).

    python tools/runner_bbmodel.py src/main/resources/assets/lanternring [variant a|b|c]
"""
import base64, io, json, math, os, sys, uuid
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
VAR = sys.argv[2] if len(sys.argv) > 2 else "a"
import pixel_dread_runner as RN  # noqa: E402

RN.V.update(RN.VARIANTS[VAR])
G = RN.G
DENSITY = int(round(1 / G))
CLEAR = (0, 0, 0, 0)
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
exec(_src[_src.index("def _texel("):_src.index("AXES = {")])


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


def to_bb(x, y, z):          # ours: x right, y forward, z up -> Blockbench: x, y up, z
    return (-x, z, y)


FACE_N = {"north": (0, -1, 0), "south": (0, 1, 0), "east": (-1, 0, 0), "west": (1, 0, 0), "up": (0, 0, 1), "down": (0, 0, -1)}


def export_part(n, name, pivot):
    lo = np.array([-12, -9, -2.0]); hi = np.array([12, 9, 48.0])
    xs = np.arange(lo[0], hi[0], G) + G / 2
    ys = np.arange(lo[1], hi[1], G) + G / 2
    zs = np.arange(lo[2], hi[2], G) + G / 2
    P = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1)
    d, tag = RN.shape(name, P)
    occ = d < 0
    px, py, pz = pivot
    model = Model(f"dread_runner_{name}", density=DENSITY)

    def painter():
        def paint(face, w, h, frm=None, to=None):
            raise NotImplementedError
        return paint

    for b_, (i, j, k, i2, j2, k2) in enumerate(boxes(occ)):
        x0, x1 = xs[i] - G / 2 - px, xs[i2] + G / 2 - px
        y0, y1 = ys[j] - G / 2 - py, ys[j2] + G / 2 - py
        z0, z1 = zs[k] - G / 2 - pz, zs[k2] + G / 2 - pz
        a, b = to_bb(x1, y0, z0), to_bb(x0, y1, z1)
        frm = [round(min(a[c], b[c]), 4) for c in range(3)]
        to = [round(max(a[c], b[c]), 4) for c in range(3)]

        def paint(face, w, h, frm=frm, to=to):
            nb = FACE_N[face]
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    X, Y, Z = _texel(frm, to, face, u, v, w, h)
                    q = np.array([-X + px, Z + py, Y + pz]) - np.array(nb) * G / 2
                    ii = int(np.clip(np.floor((q[0] - xs[0] + G / 2) / G), 0, len(xs) - 1))
                    jj = int(np.clip(np.floor((q[1] - ys[0] + G / 2) / G), 0, len(ys) - 1))
                    kk = int(np.clip(np.floor((q[2] - zs[0] + G / 2) / G), 0, len(zs) - 1))
                    col, kind = RN.colour(name, int(tag[ii, jj, kk]), -d[ii, jj, kk], np.array([xs[ii], ys[jj], zs[kk]]), np.array(nb, float))
                    row.append(tuple(int(round(min(255, max(0, c_)))) for c_ in col) + (255,))
                rows.append(row)
            return rows
        # Eyes and bright edges glow in game: cubes named glow* are drawn full-bright.
        model.cube(f"body_{b_}", frm, to, paint)
    model.write()
    return len(model.cubes)


def rig():
    STRIDE = 12
    frames = []
    for f in range(STRIDE):
        p = 2 * math.pi * f / STRIDE
        s = math.sin(p)
        frames.append({
            "torso": [-38 + 4 * math.sin(2 * p), 0, 6 * s],
            "head": [34 + 5 * math.sin(2 * p + 1.2), 0, -5 * s],
            "thigh_l": [34 + 48 * s, 0, 0], "thigh_r": [34 - 48 * s, 0, 0],
            "shin_l": [-20 - 70 * (0.5 + 0.5 * math.cos(p + 0.9)), 0, 0],
            "shin_r": [-20 - 70 * (0.5 - 0.5 * math.cos(p + 0.9)), 0, 0],
            "arm_l": [20 - 50 * s, -18, 0], "arm_r": [20 + 50 * s, 18, 0],
            "fore_l": [45 + 30 * max(0.0, s), 0, 0], "fore_r": [45 + 30 * max(0.0, -s), 0, 0],
            "bob": 0.6 * 1.6 * abs(s),
        })
    return {
        "variant": VAR,
        "note": "Angles are degrees about the joint, X/Y/Z in the generator's frame (x right, y forward, z up); "
                "convert with to_bb (x,y,z)->(-x,z,y) like the parts. 12 frames = one stride, 0.5 s.",
        "parts": [{"name": nm, "parent": par, "pivot_bb": list(to_bb(*pv))} for nm, par, pv in RN.PARTS],
        "stride_seconds": 0.5,
        "frames": frames,
    }


if __name__ == "__main__":
    total = 0
    for n, (name, parent, pivot) in enumerate(RN.PARTS):
        c = export_part(n, name, pivot)
        total += c
        print(name, c, "cubes")
    os.makedirs(f"{A}/bbmodel", exist_ok=True)
    json.dump(rig(), open(f"{A}/bbmodel/dread_runner_rig.json", "w"), indent=1)
    print("total", total, "cubes; rig written")
