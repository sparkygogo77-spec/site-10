"""A nicer Blast Drill (J, 2026-10-13: "I would also like a nicer drill model"), in hard light on the pixel
grid like the lanterns (G = 0.25 model px, 64 per block). Three options:
  d1 auger:   a cone wound with a two-start helical flute; the blade edges glow, the core stays dark jade
  d2 tiered:  stacked crowns of teeth getting smaller toward the tip, a ring of light in each gap
  d3 crystal: a faceted hexagonal spike with spiral grooves cut into it full of light, shards round its base
Each sits on a hexagonal collar with a lit slot (where it meets the ring's beam).

    python tools/pixel_blast_drill.py OUTDIR -> OUTDIR/drill_<v>.npz (quads, col, kind, glow)
z is along the drill (tip at the top); kinds: 0 dark, 1 structure, 4 glow, 6 bright edge.
"""
import math, os, sys
import numpy as np

G = 0.25
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
AX = np.arange(-10, 10, G) + G / 2
AZ = np.arange(0, 40, G) + G / 2
X, Y, Z = np.meshgrid(AX, AX, AZ, indexing="ij")
R = np.hypot(X, Y)
TH = np.arctan2(Y, X)
EMPTY, CORE, BODY, LIGHTP, EDGE, GLOW = range(6)
PAL = {CORE: ((10, 46, 28), 1), BODY: ((24, 120, 66), 4), LIGHTP: ((70, 196, 118), 4),
       EDGE: ((205, 255, 215), 6), GLOW: ((40, 230, 96), 4)}


def collar(part, top=5.0):
    """A hexagonal collar at the base with a glowing slot round it."""
    hexr = np.maximum.reduce([np.abs(X * math.cos(a) + Y * math.sin(a)) for a in (0, math.pi / 3, 2 * math.pi / 3)])
    c = (hexr < 8.6) & (Z < top)
    part[c] = CORE
    slot = c & (np.abs(Z - top * 0.55) < 0.6) & (hexr > 7.7)
    part[slot] = GLOW
    rim = c & (Z > top - 0.6) & (hexr > 7.9)
    part[rim] = EDGE
    return part


def d1():
    part = np.zeros(X.shape, np.int8)
    zt = (Z - 5) / 33.0
    Rz = 8.2 * np.clip(1 - zt, 0, 1) ** 0.9
    inside = (Z >= 5) & (R < Rz)
    part[inside & (R < np.maximum(0.38 * Rz, 0.6))] = CORE
    phase = ((TH / (2 * math.pi)) * 2 + Z / 11.0) % 1
    blade = inside & (phase < 0.24)
    part[blade] = BODY
    part[blade & (phase < 0.05)] = LIGHTP                         # the leading face catches light
    part[blade & (R > Rz - 0.75)] = EDGE                          # the cutting edge glows
    part[(Z >= 5) & (Z < 38.5) & (R < 0.55)] = GLOW               # the light running up the core
    part[(Z >= 37) & (R < 0.8)] = EDGE                            # the tip
    return collar(part)


def d2():
    part = np.zeros(X.shape, np.int8)
    tiers = [(5, 6.5, 8.4), (11.5, 6, 7.0), (17.5, 5.5, 5.6), (23, 5, 4.3), (28, 4.5, 3.0)]
    for i, (z0, h, rad) in enumerate(tiers):
        zz = (Z - z0) / h
        inz = (zz >= 0) & (zz < 1)
        taper = rad * (1 - 0.35 * zz)
        teeth = (((TH / (2 * math.pi)) * (8 + i * 0) + i * 0.5 + zz * 0.35) % 1) < 0.62
        body = inz & (R < taper) & (teeth | (R < taper * 0.72))
        part[body] = BODY
        part[body & (R > taper - 0.6)] = LIGHTP
        part[inz & teeth & (zz > 0.85) & (R > taper * 0.6) & (R < taper)] = EDGE
        gap = (Z >= z0 + h - 0.5) & (Z < z0 + h) & (R < taper * 0.7)
        part[gap] = GLOW                                          # a ring of light between the tiers
    part[(Z >= 5) & (Z < 34) & (R < 1.2)] = CORE
    spike = (Z >= 32.5) & (R < np.clip((37.5 - Z) * 0.32, 0, 2))
    part[spike] = EDGE
    return collar(part)


def d3():
    part = np.zeros(X.shape, np.int8)
    zt = (Z - 5) / 33.0
    hexr = np.maximum.reduce([np.abs(X * math.cos(a) + Y * math.sin(a)) for a in (0, math.pi / 3, 2 * math.pi / 3)])
    Rz = 7.2 * np.clip(1 - zt, 0, 1) ** 1.1
    body = (Z >= 5) & (hexr < Rz)
    part[body] = BODY
    # facet shading: the faces turned to the light are paler
    face = (np.floor((TH + math.pi / 6) / (math.pi / 3)) % 6).astype(int)
    part[body & np.isin(face, (1, 2))] = LIGHTP
    groove = body & (((TH / (2 * math.pi)) * 3 + Z / 9.0) % 1 < 0.07) & (hexr > Rz - 1.0)
    part[groove] = GLOW
    part[groove & (hexr > Rz - 0.5)] = EDGE
    part[body & (hexr < Rz * 0.45)] = CORE
    # shards orbiting the base
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        cx, cy = 7.0 * math.cos(a), 7.0 * math.sin(a)
        d = np.hypot(X - cx, Y - cy)
        shard = (Z >= 5) & (Z < 5 + 7 - k % 2 * 2) & (d < np.clip((12 - k % 2 * 2 - Z) * 0.22, 0, 1.2))
        part[shard] = LIGHTP
        part[shard & (Z > 9.5 - k % 2 * 2)] = EDGE
    return collar(part)


def quads(part):
    """Every exposed voxel face as a quad, vectorized."""
    occ = part > 0
    P = np.pad(occ, 1)
    Q, C, K = [], [], []
    for axis in range(3):
        for sgn in (1, -1):
            sh = np.roll(P, -sgn, axis=axis)[1:-1, 1:-1, 1:-1]
            expo = occ & ~sh
            idx = np.argwhere(expo)
            if not len(idx):
                continue
            ctr = np.stack([AX[idx[:, 0]], AX[idx[:, 1]], AZ[idx[:, 2]]], 1)
            n = np.zeros(3); n[axis] = sgn
            a = np.zeros(3); a[(axis + 1) % 3] = 1
            b = np.cross(n, a)
            f0 = ctr + n * G / 2
            cs = np.stack([f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))], 1)
            pid = part[idx[:, 0], idx[:, 1], idx[:, 2]]
            base = np.array([PAL[p][0] for p in pid], float)
            kind = np.array([PAL[p][1] for p in pid], np.int8)
            # simple light: tops and the lit side brighter, undersides darker
            shade = 1.0 + 0.18 * n[2] + 0.08 * (n[0] - n[1])
            col = np.clip(base * np.where(kind[:, None] == 6, 1.0, shade), 0, 255)
            Q.append(cs); C.append(col); K.append(kind)
    q = np.concatenate(Q).astype(np.float32); c = np.concatenate(C).astype(np.float32); k = np.concatenate(K)
    glow = np.where(k == 6, 1.0, np.where(k == 4, 0.6, 0.0)).astype(np.float32)
    return q, c, k, glow


if __name__ == "__main__":
    for v, fn in (("d1", d1), ("d2", d2), ("d3", d3)):
        q, c, k, g = quads(fn())
        np.savez_compressed(os.path.join(OUT, f"drill_{v}.npz"), quads=q, col=c, kind=k, glow=g)
        print(v, len(q), "faces", np.bincount(k, minlength=7))
