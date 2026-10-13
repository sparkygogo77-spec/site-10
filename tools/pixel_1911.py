"""A 1911-style pistol for the lanternring:pistol_1911 item (J), on the pixel grid like the lanterns.
32 pixels per block (G = 0.5 model pixels). Three finishes as options:
  blued: blued steel with walnut grips; steel: stainless with black grips; construct: yellow hard light.

    python tools/pixel_1911.py OUTDIR  -> OUTDIR/pistol_1911_<finish>.npz  (quads, col, kind)
x runs along the barrel (muzzle at +x), y across, z up. Kinds: 0 matte, 1 metal, 4 hard light, 6 bright edge.
"""
import os, sys
import numpy as np

G = 0.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
X = np.arange(-8, 8, G) + G / 2
Y = np.arange(-1.5, 1.5, G) + G / 2
Z = np.arange(-8.5, 3, G) + G / 2
PX, PY, PZ = np.meshgrid(X, Y, Z, indexing="ij")

EMPTY, SLIDE, FRAME, GRIP, BARREL, SMALL, SIGHT, HOLE, MAG = range(9)


def box(x0, x1, y0, y1, z0, z1):
    return (PX >= x0) & (PX < x1) & (PY >= y0) & (PY < y1) & (PZ >= z0) & (PZ < z1)


def build():
    part = np.zeros(PX.shape, np.int8)
    # Slide: long, flat-sided, with a slight top round-off, the muzzle end and rear cocking serrations.
    part[box(-5.5, 6.0, -0.75, 0.75, 0.0, 2.0)] = SLIDE
    part[box(-5.5, 6.0, -0.75, 0.75, 1.5, 2.0) & (np.abs(PY) > 0.5)] = EMPTY      # rounded top edges
    part[box(-5.0, -3.0, 0.5, 0.75, 0.5, 1.5) & (np.floor(PX / G) % 2 == 0)] = EMPTY   # serrations
    part[box(-5.0, -3.0, -0.75, -0.5, 0.5, 1.5) & (np.floor(PX / G) % 2 == 0)] = EMPTY
    part[box(0.5, 2.5, 0.5, 0.75, 1.0, 2.0)] = EMPTY                                # ejection port
    # Barrel bushing and the bore at the muzzle.
    part[box(6.0, 6.5, -0.5, 0.5, 0.0, 1.5)] = BARREL
    part[box(6.0, 6.5, -0.25, 0.25, 0.5, 1.0)] = HOLE
    # Sights.
    part[box(5.0, 5.5, -0.25, 0.25, 2.0, 2.5)] = SIGHT
    part[box(-5.5, -4.5, -0.5, 0.5, 2.0, 2.5)] = SIGHT
    part[box(-5.5, -4.5, -0.25, 0.25, 2.0, 2.5)] = EMPTY                            # rear notch
    # Frame: dust cover under the slide, trigger guard, the grip frame.
    part[box(-5.0, 4.5, -0.5, 0.5, -1.0, 0.0)] = FRAME
    part[box(-1.0, 1.5, -0.5, 0.5, -2.75, -1.0) & ~box(-0.5, 1.0, -0.5, 0.5, -2.25, -1.0)] = FRAME   # guard
    part[box(-0.25, 0.25, -0.25, 0.25, -2.0, -1.0)] = SMALL                            # trigger
    # The grip, raked back, with walnut panels and the mainspring housing.
    for k, z in enumerate(np.arange(-7.5, -1.0, G)):          # a full-length grip
        back = -5.0 + 0.32 * (z + 1.0)          # raked back toward the bottom
        part[box(back, back + 3.5, -0.5, 0.5, z, z + G)] = FRAME
        part[box(back + 0.5, back + 3.0, -0.75, 0.75, z, z + G) & (np.abs(PY) > 0.5)] = GRIP
    part[box(-7.1, -3.4, -0.5, 0.5, -8.0, -7.5)] = MAG                               # magazine base
    # Hammer, grip safety tang, slide stop, thumb safety.
    part[box(-6.5, -5.5, -0.25, 0.25, 0.5, 2.0)] = SMALL
    part[box(-6.5, -5.0, -0.5, 0.5, -1.5, -0.5)] = FRAME
    part[box(1.5, 2.5, 0.5, 0.75, -0.5, 0.0)] = SMALL
    part[box(-4.5, -3.5, 0.5, 0.75, -0.5, 0.0)] = SMALL
    return part


FINISH = {
    "blued": {SLIDE: ((44, 46, 54), 1), FRAME: ((40, 42, 50), 1), GRIP: ((112, 62, 30), 0), BARREL: ((70, 72, 80), 1),
              SMALL: ((30, 30, 36), 1), SIGHT: ((24, 24, 28), 0), HOLE: ((6, 6, 8), 0), MAG: ((30, 30, 36), 1)},
    "steel": {SLIDE: ((176, 178, 184), 1), FRAME: ((168, 170, 176), 1), GRIP: ((28, 28, 30), 0), BARREL: ((196, 198, 204), 1),
              SMALL: ((120, 122, 128), 1), SIGHT: ((40, 40, 44), 0), HOLE: ((6, 6, 8), 0), MAG: ((110, 112, 118), 1)},
    "construct": {SLIDE: ((236, 172, 28), 4), FRAME: ((220, 150, 20), 4), GRIP: ((150, 96, 10), 4), BARREL: ((255, 226, 96), 6),
                  SMALL: ((255, 226, 96), 6), SIGHT: ((255, 240, 160), 6), HOLE: ((40, 24, 0), 0), MAG: ((255, 214, 70), 6)},
}


def quads(part, finish):
    occ = (part > 0) & (part != HOLE) | (part == HOLE)
    S = occ.shape
    Q, C, K = [], [], []
    for i, j, k in np.argwhere(occ):
        pid = int(part[i, j, k])
        c = np.array([X[i], Y[j], Z[k]])
        base, kind = FINISH[finish][pid]
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a, b, cc = i + n[0], j + n[1], k + n[2]
            if 0 <= a < S[0] and 0 <= b < S[1] and 0 <= cc < S[2] and occ[a, b, cc]:
                continue
            col = np.array(base, float)
            if pid == GRIP and (i + k) % 2 == 0:
                col *= 0.78                                    # checkering
            if n[2] > 0:
                col *= 1.12                                    # tops catch the light
            elif n[2] < 0:
                col *= 0.7
            if finish == "construct" and kind == 4 and (n[2] > 0 or abs(c[1]) > 0.6 and (k % 3 == 0)):
                col, kind_ = np.array([255, 214, 70.0]), 6
            else:
                kind_ = kind
            nv = np.array(n, float)
            ax = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            bx = np.cross(nv, ax)
            f0 = c + nv * G / 2
            cs = [f0 + (ax * sa + bx * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind_)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


if __name__ == "__main__":
    part = build()
    for f in FINISH:
        q, c, k = quads(part, f)
        np.savez_compressed(os.path.join(OUT, f"pistol_1911_{f}.npz"), quads=q, col=c, kind=k)
        print(f, len(q), "faces")
