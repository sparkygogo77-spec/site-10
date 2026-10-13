"""Yellow hard-light construct weapons the Fear Nuke's gas hands to feared mobs (J): an AK-style rifle and a
crossbow, on the pixel grid (32 per block, G = 0.5 model pixels). x runs to the muzzle, z up.

    python tools/pixel_construct_weapons.py OUTDIR -> OUTDIR/construct_rifle.npz, construct_crossbow.npz
Kinds: 0 dark core, 4 amber hard light, 6 bright edge.
"""
import os, sys
import numpy as np

G = 0.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def grid(x0, x1, y0, y1, z0, z1):
    X = np.arange(x0, x1, G) + G / 2
    Y = np.arange(y0, y1, G) + G / 2
    Z = np.arange(z0, z1, G) + G / 2
    return X, Y, Z, np.meshgrid(X, Y, Z, indexing="ij")


def rifle():
    X, Y, Z, (PX, PY, PZ) = grid(-14, 16, -1.5, 1.5, -8, 4)
    occ = np.zeros(PX.shape, bool)
    B = lambda x0, x1, y0, y1, z0, z1: (PX >= x0) & (PX < x1) & (PY >= y0) & (PY < y1) & (PZ >= z0) & (PZ < z1)
    occ |= B(-4, 6, -0.75, 0.75, -1.0, 1.5)                       # receiver
    occ |= B(-4, 4, -0.5, 0.5, 1.5, 2.0)                           # dust cover
    occ |= B(6, 15, -0.25, 0.25, 0.0, 0.5)                         # barrel
    occ |= B(6, 11, -0.25, 0.25, 0.75, 1.25)                       # gas tube
    occ |= B(6, 10, -0.75, 0.75, -0.5, 1.0)                        # handguard
    occ |= B(13, 13.5, -0.25, 0.25, 0.5, 2.0)                      # front sight
    occ |= B(14.5, 15.5, -0.5, 0.5, -0.25, 0.75)                   # muzzle brake
    # Stock: from the back of the receiver, dropping slightly.
    for x in np.arange(-13, -4, G):
        drop = (-4 - x) * 0.12
        occ |= B(x, x + G, -0.5, 0.5, -1.5 - drop, 1.0 - drop * 0.4)
    # Pistol grip, raked back.
    for z in np.arange(-5, -1, G):
        back = -2.5 + 0.35 * (z + 1)
        occ |= B(back, back + 1.5, -0.5, 0.5, z, z + G)
    # The curved magazine.
    for z in np.arange(-7.5, -1, G):
        t = (-1 - z) / 6.5
        x0 = 1.0 + 3.0 * t ** 1.5
        occ |= B(x0, x0 + 2.0, -0.5, 0.5, z, z + G)
    occ |= B(-0.5, 0.0, -0.25, 0.25, -2.0, -1.0)                   # trigger
    return X, Y, Z, occ


def crossbow():
    X, Y, Z, (PX, PY, PZ) = grid(-12, 10, -9, 9, -5, 3)
    occ = np.zeros(PX.shape, bool)
    B = lambda x0, x1, y0, y1, z0, z1: (PX >= x0) & (PX < x1) & (PY >= y0) & (PY < y1) & (PZ >= z0) & (PZ < z1)
    occ |= B(-6, 8, -0.75, 0.75, -0.5, 0.5)                        # tiller
    occ |= B(-11, -6, -0.5, 0.5, -1.5, 0.5)                        # stock
    occ |= B(-4, -2.5, -0.5, 0.5, -4, -0.5)                        # grip
    # Limbs: bowed forward toward the tips.
    for y in np.arange(-8.5, 8.5, G):
        bow = 6.5 - 0.06 * y * y
        occ |= B(bow, bow + 1.0, y, y + G, -0.25, 0.25)
    # String from the tips back to the nut.
    for y in np.arange(-8.0, 8.0, G):
        sx = 2.3 + 2.4 * abs(y) / 8.0
        occ |= B(sx, sx + G, y, y + G, 0.5, 1.0)
    occ |= B(-1, 9.5, -0.25, 0.25, 0.5, 1.0)                       # the bolt
    occ |= B(9.5, 10.0, -0.5, 0.5, 0.25, 1.25)                     # bolt head
    return X, Y, Z, occ


def quads(X, Y, Z, occ):
    S = occ.shape
    Q, C, K = [], [], []
    for i, j, k in np.argwhere(occ):
        c = np.array([X[i], Y[j], Z[k]])
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a, b, cc = i + n[0], j + n[1], k + n[2]
            if 0 <= a < S[0] and 0 <= b < S[1] and 0 <= cc < S[2] and occ[a, b, cc]:
                continue
            # Hard light: bright where an edge or a top catches it, amber faces, a darker core seam.
            edge = sum(1 for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))
                       if not (0 <= i + d[0] < S[0] and 0 <= k + d[2] < S[2] and occ[i + d[0], j, k + d[2]]))
            # Take 2: calmer. Bright only on the top edges, clean panel seams instead of speckle.
            if n[2] > 0 and edge >= 1:
                col, kind = np.array([255, 214, 80.0]), 6
            elif i % 10 == 0 and n[2] == 0:
                col, kind = np.array([120, 74, 6.0]), 0
            else:
                col, kind = np.array([196, 128, 14.0]) * (0.8 if n[2] < 0 else 1.0), 4
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
    for name, fn in (("construct_rifle", rifle), ("construct_crossbow", crossbow)):
        q, c, k = quads(*fn())
        np.savez_compressed(os.path.join(OUT, name + ".npz"), quads=q, col=c, kind=k)
        print(name, len(q), "faces")
