"""An original fear parasite (J wants the feel of a fear entity, not any existing character): a floating,
segmented serpent of yellow hard light. A wide fanged maw that opens, flaring mandibles, a cluster of eyes
and spines down its back; the body turns from burning yellow at the head to black-green at the tail.
Jointed (head, jaw, 12 body segments in a chain) so it can undulate. Three versions:
  a serpent: smooth body; b centipede: pairs of clawed legs on every segment; c finned: long side fins.

    python tools/pixel_fear_parasite.py OUTDIR  -> OUTDIR/fear_parasite_<v>.npz (same layout as dread_runner)
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_dread_runner import _seg, smin  # noqa: E402

G = 0.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
SEGS = 18
L = 4.0            # segment length, model pixels
Z0 = 24.0          # floats this high


def radius(i):
    return 4.2 * (1 - i / SEGS) ** 0.8 + 0.7


PARTS = [("head", -1, (0, 0, Z0)), ("jaw", 0, (0, 1.0, Z0 - 1.2))]
for i in range(SEGS):
    PARTS.append((f"seg{i}", 0 if i == 0 else 1 + i, (0, -L * i - 2.0, Z0)))


def shape(name, P, v):
    tag = np.zeros(P.shape[:-1], np.int8)
    if name == "head":
        # A wedge skull with a wide upper maw, crest horns, mandibles and a cluster of eyes.
        d, _ = _seg(P, (0, -1.5, Z0), (0, 4.5, Z0 + 0.4), 4.0, 2.6)
        d = np.maximum(d, -(P[..., 2] - (Z0 - 0.6)))                 # flat underside: the maw opens below
        for sx in (1, -1):
            h, _ = _seg(P, (1.8 * sx, 0.5, Z0 + 3.0), (3.6 * sx, -4.5, Z0 + 6.5), 0.8, 0.12)
            tag[(h < d) & (h < 0)] = 3
            d = np.minimum(d, h)
            m1, _ = _seg(P, (3.0 * sx, 3.0, Z0 - 0.4), (5.6 * sx, 6.5, Z0 - 1.0), 0.7, 0.3)
            m2, _ = _seg(P, (5.6 * sx, 6.5, Z0 - 1.0), (3.4 * sx, 9.0, Z0 - 1.4), 0.3, 0.08)
            mand = np.minimum(m1, m2)
            tag[(mand < d) & (mand < 0)] = 3
            d = np.minimum(d, mand)
            for k, (ex, ey, ez) in enumerate(((1.3, 4.6, Z0 + 1.6), (2.4, 3.2, Z0 + 2.1), (2.9, 1.6, Z0 + 2.4))):
                e = np.linalg.norm(P - np.array([ex * sx, ey, ez]), axis=-1) - (0.75 - 0.12 * k)
                tag[(e < 0.2) & (d < 0.8)] = 2
        for x in np.linspace(-2.6, 2.6, 7):                           # upper fangs
            f, _ = _seg(P, (x, 4.0 - abs(x) * 0.5, Z0 - 0.4), (x * 0.9, 4.4 - abs(x) * 0.5, Z0 - 2.6), 0.4, 0.06)
            tag[(f < d) & (f < 0)] = 3
            d = np.minimum(d, f)
        return d, tag
    if name == "jaw":
        d, _ = _seg(P, (0, 0.0, Z0 - 1.6), (0, 4.6, Z0 - 1.9), 2.6, 1.6)
        d = np.maximum(d, P[..., 2] - (Z0 - 1.2))
        for x in np.linspace(-2.0, 2.0, 5):
            f, _ = _seg(P, (x, 4.0 - abs(x) * 0.5, Z0 - 1.8), (x * 0.9, 4.3 - abs(x) * 0.5, Z0 + 0.0), 0.35, 0.06)
            tag[(f < d) & (f < 0)] = 3
            d = np.minimum(d, f)
        return d, tag
    i = int(name[3:])
    y0 = -L * i - 2.0
    r0, r1 = radius(i), radius(i + 1)
    d, _ = _seg(P, (0, y0 + 0.6, Z0), (0, y0 - L + 0.4, Z0), r0, r1)
    # A spine (two on the fins version) on every segment.
    for sx in ((0,) if v != "c" else (-0.8, 0.8)):
        sp, _ = _seg(P, (sx, y0 - L * 0.4, Z0 + r0 * 0.8), (sx * 1.6, y0 - L * 0.9, Z0 + r0 + 2.2 + (1.5 if v == "c" else 0)),
                     0.6 * r0 / 4 + 0.25, 0.06)
        tag[(sp < d) & (sp < 0)] = 1
        d = np.minimum(d, sp)
    if v == "b":
        for sx in (1, -1):
            l1, _ = _seg(P, (r0 * 0.8 * sx, y0 - L * 0.5, Z0 - r0 * 0.4), ((r0 + 2.4) * sx, y0 - L * 0.4, Z0 - r0 - 1.2), 0.45, 0.3)
            l2, _ = _seg(P, ((r0 + 2.4) * sx, y0 - L * 0.4, Z0 - r0 - 1.2), ((r0 + 1.8) * sx, y0 - L * 0.1, Z0 - r0 - 3.4), 0.3, 0.06)
            leg = np.minimum(l1, l2)
            tag[(leg < d) & (leg < 0)] = 3
            d = np.minimum(d, leg)
    if v == "c" and i < SEGS - 1:
        span = (r0 + 4.5 * (1 - i / SEGS))
        fin = np.maximum.reduce([np.abs(P[..., 2] - Z0) - 0.3, np.abs(P[..., 0]) - span,
                                 np.abs(P[..., 1] - (y0 - L / 2)) - L * 0.45,
                                 # scalloped trailing edge
                                 (np.abs(P[..., 0]) - span * (0.55 + 0.45 * np.cos((P[..., 1] - y0) * 1.3) ** 2))])
        tag[(fin < d) & (fin < 0)] = 4
        d = np.minimum(d, fin)
    return d, tag


def colour(name, tag, c, n):
    x, y, z = c
    t = 0.0 if name in ("head", "jaw") else (int(name[3:]) + 0.5) / SEGS
    if tag == 2:
        return np.array([255, 252, 214.0]), 7
    hot = np.array([244, 184, 28.0]); cold = np.array([18, 44, 20.0])
    base = hot * (1 - t ** 1.3) + cold * t ** 1.3
    if tag in (1, 3):
        tip = np.array([255, 228, 110.0]) * (1 - t) + np.array([40, 90, 30.0]) * t
        return tip, 6 if t < 0.7 else 4
    if tag == 4:
        return base * 0.75 + np.array([0, 20, 0.0]) * t, 4
    if name in ("head", "jaw") and n[2] < -0.5:
        return np.array([40, 18, 0.0]), 0                       # inside the maw
    if np.sin(y * 1.6) > 0.7:
        return base * 0.45, 0                                    # dark bands between plates
    if n[2] > 0.5:
        return np.minimum(base * 1.15 + 20, 255), 6 if t < 0.5 else 4
    return base, 4


def voxelise(name, pivot, v):
    xs = np.arange(-12, 12, G) + G / 2
    ys = np.arange(-80, 12, G) + G / 2
    zs = np.arange(Z0 - 12, Z0 + 12, G) + G / 2
    # Only the slab of y this part can reach, to keep it quick.
    if name.startswith("seg"):
        i = int(name[3:]); y0 = -L * i - 2.0
        ys = ys[(ys > y0 - L - 2) & (ys < y0 + 2)]
    else:
        ys = ys[ys > -4]
    P = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1)
    d, tag = shape(name, P, v)
    occ = d < 0
    Q, C, K = [], [], []
    S = occ.shape
    for i, j, k in np.argwhere(occ):
        c = np.array([xs[i], ys[j], zs[k]])
        for nn in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a_, b_, c_ = i + nn[0], j + nn[1], k + nn[2]
            if 0 <= a_ < S[0] and 0 <= b_ < S[1] and 0 <= c_ < S[2] and occ[a_, b_, c_]:
                continue
            nv = np.array(nn, float)
            col, kind = colour(name, int(tag[i, j, k]), c, nv)
            ax = np.array([0, 1, 0.]) if nn[0] else np.array([1, 0, 0.])
            bx = np.cross(nv, ax)
            f0 = c + nv * G / 2
            cs = [f0 + (ax * sa + bx * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(np.asarray(cs) - np.asarray(pivot, float)); C.append(np.clip(col, 0, 255)); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


if __name__ == "__main__":
    for v in "abc":
        out = {}
        total = 0
        for n, (name, parent, pivot) in enumerate(PARTS):
            q, c, k = voxelise(name, pivot, v)
            out[f"q{n}"], out[f"c{n}"], out[f"k{n}"] = q, c, k
            total += len(q)
        out["names"] = np.array([p[0] for p in PARTS])
        out["parents"] = np.array([p[1] for p in PARTS], np.int32)
        out["pivots"] = np.array([p[2] for p in PARTS], np.float32)
        np.savez_compressed(os.path.join(OUT, f"fear_parasite_{v}.npz"), **out)
        print(v, total, "faces")
