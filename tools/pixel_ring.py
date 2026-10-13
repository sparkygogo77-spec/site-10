"""Better Power Ring models (J: "I need a better lantern ring model"), on the pixel grid like the lanterns,
64 pixels per block (G = 0.25 model pixels). Original emblems, three options:
  a forged: heavy bevelled band, hexagonal bezel, a raised flame sigil inside a lit rim
  b crown:  the band splits into claw prongs gripping a glowing round gem with a cut starburst
  c sleek:  wide flat band with a glowing channel all the way round, an oval face with a ring of light

    python tools/pixel_ring.py OUTDIR -> OUTDIR/ring_<v>.npz (quads, col, kind)
The finger runs along y; the face looks up (+z). Kinds: 0 dark, 1 metal, 4 green light, 6 bright light.
"""
import os, sys
import numpy as np

G = 0.25
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
A = np.arange(-6, 6, G) + G / 2
X, Y, Z = np.meshgrid(A, np.arange(-3, 3, G) + G / 2, np.arange(-6, 6.5, G) + G / 2, indexing="ij")
EMPTY, BAND, BEZEL, GEM, LIT, DARK, PRONG = range(7)
R_IN = 2.6           # finger hole radius


def band(width, thick, bevel=True):
    r = np.hypot(X, Z)
    inside = (r >= R_IN) & (r <= R_IN + thick) & (np.abs(Y) <= width / 2)
    if bevel:   # round the outer edges
        inside &= (r - R_IN - thick + 0.4) < (width / 2 - np.abs(Y)) * 1.2 + 0.2
    return inside


def build(v):
    part = np.zeros(X.shape, np.int8)
    r = np.hypot(X, Z)
    if v == "a":
        part[band(2.6, 1.0)] = BAND
        top = Z - (R_IN + 0.7)
        hexd = np.maximum(np.abs(X) * 0.866 + np.abs(Y) * 0.5, np.abs(Y))
        bezel = (hexd <= 2.9) & (top >= 0) & (top <= 1.6)
        part[bezel] = BEZEL
        part[(hexd <= 2.3) & (top > 1.0) & (top <= 1.6)] = DARK                   # recessed face
        part[(hexd > 2.3) & (hexd <= 2.6) & (top > 1.2) & (top <= 1.8)] = LIT     # lit rim
        # A raised flame sigil: a teardrop pointing along +y.
        u, w = X, Y + 0.3
        flame = (np.hypot(u, w + 0.5) <= 1.5) | ((w > -0.5) & (np.abs(u) <= 1.5 * np.clip(1 - (w + 0.5) / 2.4, 0, 1) ** 1.3) & (w < 1.9))
        part[flame & (top > 1.4) & (top <= 2.1) & (hexd <= 2.3)] = GEM
        part[(np.hypot(u, w + 0.4) <= 0.45) & (top > 1.4) & (top <= 2.3)] = LIT   # white-hot heart
    elif v == "b":
        part[band(1.6, 0.7)] = BAND
        top = Z - (R_IN + 0.5)
        part[(np.hypot(X, Y) <= 2.0) & (top >= 0) & (top <= 0.6)] = BEZEL         # seat
        gem = np.hypot(np.hypot(X, Y) * 1.0, (top - 1.4) * 1.25) <= 1.7
        part[gem & (top > 0.4)] = GEM
        ang = np.arctan2(Y, X)
        star = (np.cos(ang * 8) > 0.82) & (np.hypot(X, Y) < 1.5) & (top > 2.2)
        part[gem & star] = LIT
        part[gem & (np.hypot(X, Y) < 0.5) & (top > 2.4)] = LIT
        for a in np.radians([45, 135, 225, 315]):                                  # four claw prongs
            cx, cy = 1.75 * np.cos(a), 1.75 * np.sin(a)
            pr = (np.hypot(X - cx, Y - cy) <= 0.38) & (top >= 0) & (top <= 2.0)
            tip = (np.hypot(X - cx * 0.85, Y - cy * 0.85) <= 0.32) & (top > 2.0) & (top <= 2.4)
            part[pr | tip] = PRONG
        # Shoulders sweeping up from the band to the seat.
        sh = (np.abs(Y) <= 0.8) & (np.abs(X) <= 2.4) & (top < 0) & (top > -0.9) & (r > R_IN + 0.6)
        part[sh & (part == EMPTY)] = BAND
    else:
        part[band(3.4, 0.8, bevel=False)] = BAND
        chan = (r > R_IN + 0.55) & (r <= R_IN + 0.8) & (np.abs(Y) <= 0.35)
        part[chan] = LIT                                                           # glowing channel
        top = Z - (R_IN + 0.6)
        oval = (X / 2.6) ** 2 + (Y / 1.9) ** 2
        part[(oval <= 1) & (top >= 0) & (top <= 0.8)] = BEZEL
        ring = (oval > 0.42) & (oval <= 0.7) & (top > 0.5) & (top <= 1.0)
        part[ring] = GEM
        notch = (np.cos(np.arctan2(Y / 1.9, X / 2.6) * 12) > 0.6) & (oval > 0.72) & (oval <= 0.88) & (top > 0.5) & (top <= 0.9)
        part[notch] = LIT
        part[(oval <= 0.15) & (top > 0.5) & (top <= 1.1)] = LIT
        part[(oval > 0.15) & (oval <= 0.42) & (top > 0.6) & (top <= 0.8)] = DARK
    return part


COL = {
    "a": {BAND: ((62, 72, 66), 1), BEZEL: ((84, 96, 88), 1), GEM: ((40, 210, 80), 4), LIT: ((210, 255, 200), 6),
          DARK: ((10, 22, 14), 0), PRONG: ((84, 96, 88), 1)},
    "b": {BAND: ((190, 196, 200), 1), BEZEL: ((150, 156, 160), 1), GEM: ((30, 200, 70), 4), LIT: ((200, 255, 190), 6),
          DARK: ((10, 22, 14), 0), PRONG: ((210, 214, 218), 1)},
    "c": {BAND: ((22, 26, 24), 1), BEZEL: ((36, 42, 38), 1), GEM: ((50, 230, 90), 4), LIT: ((190, 255, 180), 6),
          DARK: ((8, 14, 10), 0), PRONG: ((36, 42, 38), 1)},
}


def quads(part, v):
    occ = part > 0
    S = occ.shape
    Q, C, K = [], [], []
    for i, j, k in np.argwhere(occ):
        pid = int(part[i, j, k])
        c = np.array([X[i, j, k], Y[i, j, k], Z[i, j, k]])
        base, kind = COL[v][pid]
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a, b, cc = i + n[0], j + n[1], k + n[2]
            if 0 <= a < S[0] and 0 <= b < S[1] and 0 <= cc < S[2] and occ[a, b, cc]:
                continue
            nv = np.array(n, float)
            col = np.array(base, float)
            # Metal: brighter where the face looks outward from the finger, darker inside the hole.
            if kind == 1:
                out = np.dot(nv, np.array([c[0], 0, c[2]]) / (np.hypot(c[0], c[2]) + 1e-6))
                col *= 0.75 + 0.45 * max(0.0, out) + (0.15 if n[2] > 0 else 0)
            ax = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            bx = np.cross(nv, ax)
            f0 = c + nv * G / 2
            cs = [f0 + (ax * sa + bx * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


if __name__ == "__main__":
    for v in "abc":
        q, c, k = quads(build(v), v)
        np.savez_compressed(os.path.join(OUT, f"ring_{v}.npz"), quads=q, col=c, kind=k)
        print(v, len(q), "faces", np.bincount(k, minlength=7))
