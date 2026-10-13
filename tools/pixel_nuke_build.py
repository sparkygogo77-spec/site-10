"""The Fear Nuke built in the ring hand (J: "it should spend its time being constructed in the arm"): a fat
yellow hard-light bomb made of separate plates, so Blender (and later the game) can fly each plate in and
lock it into place. 32 pixels per block (G = 0.5 model pixels). x is the bomb's long axis.

    python tools/pixel_nuke_build.py OUTDIR -> OUTDIR/nuke_build.npz
Parts: plates (8 around x 5 along), a nose cap, 4 tail fins and a tail ring; for part n: q<n> (faces, in the
part's frame), c<n>, k<n>, pivot<n> (where it locks in), order<n> (build order 0..1).
Kinds: 0 dark core, 4 amber hard light, 6 bright seam.
"""
import os, sys
import numpy as np

G = 0.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
X = np.arange(-10, 10, G) + G / 2
YZ = np.arange(-7, 7, G) + G / 2
PX, PY, PZ = np.meshgrid(X, YZ, YZ, indexing="ij")
LEN, RAD = 7.0, 5.0                       # half length, radius


def parts():
    r = np.hypot(PY, PZ)
    ang = np.arctan2(PZ, PY)
    body = (PX / LEN) ** 2 + (r / RAD) ** 2 <= 1.0
    shell = body & ((PX / (LEN - 1.2)) ** 2 + (r / (RAD - 1.2)) ** 2 > 1.0)
    core = body & ~shell
    lab = np.full(PX.shape, -1, np.int32)
    order = {}
    seam = np.zeros(PX.shape, bool)
    for i in range(8):                     # around
        a0 = -np.pi + i * np.pi / 4
        for j in range(5):                 # along, from the tail (-x) to just behind the nose
            x0, x1 = -LEN + j * 2.4, -LEN + (j + 1) * 2.4
            m = shell & (ang >= a0) & (ang < a0 + np.pi / 4) & (PX >= x0) & (PX < x1)
            n = i * 5 + j
            lab[m] = n
            order[n] = (j + (i % 2) * 0.5) / 5.5
            seam |= m & ((np.abs(ang - a0) < 0.12) | (PX - x0 < G))
    nose = shell & (PX >= -LEN + 5 * 2.4)
    lab[nose] = 40; order[40] = 0.95
    lab[core] = 41; order[41] = 0.0       # the dark core is there from the start
    k = 42
    for f in range(4):                     # tail fins
        a = f * np.pi / 2 + np.pi / 4
        u = PY * np.cos(a) + PZ * np.sin(a)
        v = -PY * np.sin(a) + PZ * np.cos(a)
        fin = (np.abs(v) <= 0.3) & (u > 2.0) & (u < 6.5) & (PX < -LEN + 3.5) & (PX > -LEN - 2.0)
        lab[fin & (lab < 0)] = k; order[k] = 0.85 + 0.02 * f; k += 1
    ring = (r > 5.4) & (r < 6.4) & (PX < -LEN - 0.8) & (PX > -LEN - 2.0)
    lab[ring & (lab < 0)] = k; order[k] = 0.92
    return lab, order, seam, core


def faces(mask, colour_of):
    S = mask.shape
    Q, C, K = [], [], []
    for i, j, k in np.argwhere(mask):
        c = np.array([X[i], YZ[j], YZ[k]])
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a, b, cc = i + n[0], j + n[1], k + n[2]
            if 0 <= a < S[0] and 0 <= b < S[1] and 0 <= cc < S[2] and mask[a, b, cc]:
                continue
            col, kind = colour_of(i, j, k, n)
            nv = np.array(n, float)
            ax = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            bx = np.cross(nv, ax)
            f0 = c + nv * G / 2
            cs = [f0 + (ax * sa + bx * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(col); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


if __name__ == "__main__":
    lab, order, seam, core = parts()
    out = {}
    ids = sorted(order)
    for n_, pid in enumerate(ids):
        m = lab == pid
        pts = np.stack([PX[m], PY[m], PZ[m]], -1)
        piv = pts.mean(0)

        def col(i, j, k, n, pid=pid):
            if pid == 41:
                return np.array([60, 36, 0.0]), 0
            if seam[i, j, k]:
                return np.array([255, 230, 120.0]), 6
            return np.array([226, 160, 22.0]) * (0.8 if n[2] < 0 else 1.0), 4
        q, c, k = faces(m, col)
        out[f"q{n_}"], out[f"c{n_}"], out[f"k{n_}"] = q - piv, c, k
        out[f"pivot{n_}"] = piv.astype(np.float32)
        out[f"order{n_}"] = np.float32(order[pid])
    out["count"] = np.int32(len(ids))
    np.savez_compressed(os.path.join(OUT, "nuke_build.npz"), **out)
    print(len(ids), "parts", sum(len(out[f"q{i}"]) for i in range(len(ids))), "faces")
