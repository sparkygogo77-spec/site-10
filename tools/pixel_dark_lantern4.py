"""The Dark Lantern, fourth design: J's pick G2 rebuilt round the film stills' centre.

What the stills show, and what this builds (0.25 units = one pixel, 64 per block):
- the ribs run from each end toward the middle and stop; the middle is a smooth rounded bulge of
  glass, crazed all over with a fine crack network, some crackle plates standing a pixel proud
- the port sits on that bulge: a knurled stack of rings, a brass face with a square cut-out plate,
  two screws, and a small ringed hole in the middle; two thick wire loops run from it round the body
- the top: a flat rounded-triangle plate with a raised rim, two teardrop holes at the corners, a round
  boss in the middle with a post the handle hinges on
J's rules: dark at rest, the glow gathers in the centre when charging, gold flecks glint now and then.

    python tools/pixel_dark_lantern4.py <out dir>

Writes dark5_<version>.npz (quads, col, kind 0 matte / 1 metal / 3 fleck / 4 body / 5 vein, glow),
the format the Lantern Live dark materials (pass 23) read.
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_dark_lantern2 import rtri, front_y, G, LIGHT

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
EMPTY, SMOKE, RIB, PLATE, GOLD, GOLD_DK, SILVER, SILVER_DK, VEIN, HOLE, EMBLEM, SOCKET = range(12)


def profile(h, p):
    """Body size at height fraction h: ribbed ends tapering in, then the smooth bulge in the middle."""
    h = np.asarray(h, float)
    taper = p["size"] * (1 - p["pinch"] * np.clip(1 - np.abs(h - 0.5) / 0.5, 0, 1) ** 1.3)
    u = np.clip(np.abs(h - 0.5) / p["bulge_h"], 0, 1)
    bulge = p["size"] * (1 - p["pinch"]) + p["bulge"] * p["size"] * np.sqrt(np.clip(1 - u ** 2, 0, 1))
    return np.where(u < 1, np.maximum(bulge, taper), taper)


def vor3(P, cell, seed):
    """Distance to the nearest crack (a border of a jittered 3D grid of cells) and the cell's id."""
    r = np.random.default_rng(seed)
    jit = r.random((64, 64, 64, 3))
    g = np.floor(P / cell).astype(int)
    d0 = np.full(P.shape[:-1], 1e9); d1 = d0.copy(); ident = np.zeros(P.shape[:-1], int)
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            for oz in (-1, 0, 1):
                c = g + np.array([ox, oy, oz])
                j = jit[c[..., 0] % 64, c[..., 1] % 64, c[..., 2] % 64]
                d = np.linalg.norm(P - (c + j) * cell, axis=-1)
                closer = d < d0
                d1 = np.where(closer, d0, np.minimum(d1, d))
                ident = np.where(closer, (c[..., 0] % 64) * 4096 + (c[..., 1] % 64) * 64 + c[..., 2] % 64, ident)
                d0 = np.where(closer, d, d0)
    return (d1 - d0) / 2, ident


def build(p):
    xs = np.arange(-9, 9, G) + G / 2
    zs = np.arange(0, 31, G) + G / 2
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
    part = np.zeros(X.shape, np.int8)
    z0, z1 = p["body"]
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = profile(H, p)
    rnd = p["round"]
    d = rtri(X, Y, size, rnd)
    body = (Z > z0) & (Z <= z1)
    mid = np.abs(H - 0.5) < p["bulge_h"]
    part[body & (d <= 0)] = SMOKE
    # ribs: every other pixel row a pixel proud, only on the ribbed ends
    rib = (np.floor((Z - z0) / G) % 2) == 0
    ribbed = body & ~mid
    part[ribbed & rib & (d <= G * p.get("rib_depth", 1)) & (d > 0)] = RIB
    part[ribbed & rib & (d <= 0) & (d > -G)] = RIB
    # the middle: crazed glass. Fine cells; some stand a pixel proud; gold in the cracks
    P = np.stack([X, Y, Z], -1)
    border, ident = vor3(P, p["craze"], p["seed"])
    proud = (ident * 2654435761 % 1000) < 330
    shell = body & mid & (d <= 0) & (d > -G)
    part[body & mid & proud & (d <= G) & (d > 0)] = PLATE
    part[shell] = PLATE
    crack = (border < G * 0.28) & ((ident * 40503 % 100) < p.get("crack_keep", 70))
    part[body & mid & crack & (d <= G) & (d > -G) & (part > 0)] = VEIN
    # a few long gold lines down the ribbed ends, as in the close-up
    rng = np.random.default_rng(p["seed"] + 1)
    ang = np.degrees(np.arctan2(Y, X))
    for _ in range(p["lines"]):
        a0 = rng.uniform(-180, 180); slope = rng.uniform(-4, 4)
        za, zb = sorted(rng.uniform(z0, z1, 2))
        path = a0 + slope * (Z - za)
        dist = np.abs((ang - path + 180) % 360 - 180) * np.pi / 180 * np.maximum(size, 1)
        part[(dist < G * 0.5) & (Z >= za) & (Z <= zb) & ribbed & (d <= G) & (d > -G) & (part > 0)] = VEIN
    # collars: thin bands at each end of the glass
    for zc, sgn in ((z0, -1), (z1, 1)):
        s = float(profile((zc - z0) / (z1 - z0), p))
        for a, b, grow, pid in ((0.0, 0.5, 0.55, GOLD), (0.5, 0.75, 0.4, GOLD_DK)):
            lo, hi = (zc + a, zc + b) if sgn > 0 else (zc - b, zc - a)
            part[(Z > lo) & (Z <= hi) & (rtri(X, Y, s + grow, rnd + 0.3) <= 0)] = pid
    # base: a stepped foot
    sb = float(profile(0.0, p))
    for i, (grow, pid) in enumerate(((0.55, GOLD), (0.1, GOLD_DK), (-0.6, GOLD))):
        lo = z0 - 0.75 - 0.5 * (i + 1)
        part[(Z > lo) & (Z <= lo + 0.5) & (rtri(X, Y, sb + grow, rnd) <= 0)] = pid
    # top plate (from J's photo of the top): a flat plate with a smooth raised rim, sloping down to a
    # recessed field; two teardrop holes pointing into the front corners; a stepped round boss; a post
    zt = z1 + 0.75
    st = float(profile(1.0, p)) + 0.55
    outer = rtri(X, Y, st, rnd + 0.3)
    part[(Z > zt) & (Z <= zt + 0.5) & (outer <= 0)] = GOLD_DK                     # the plate
    part[(Z > zt + 0.5) & (Z <= zt + 1.0) & (outer <= 0) & (outer > -0.5)] = GOLD   # the rim
    part[(Z > zt + 0.5) & (Z <= zt + 0.75) & (outer <= -0.5) & (outer > -0.75)] = GOLD_DK   # rim's inner step
    for sx in (-1, 1):                                                              # two front corners
        cx, cy = sx * (st - rnd) * 0.5, -(st - rnd) / (2 * math.sqrt(3)) * 1.2
        ux, uy = cx / math.hypot(cx, cy), cy / math.hypot(cx, cy)                   # toward the corner
        qx, qy = X - cx, Y - cy
        along = qx * ux + qy * uy
        across = np.abs(-qx * uy + qy * ux)
        tear = (np.hypot(qx, qy) <= 0.55) | ((along > 0) & (along < 1.0) & (across < 0.55 * (1 - along)))
        part[tear & (Z > zt) & (Z <= zt + 0.5)] = HOLE
        part[tear & (Z > zt) & (Z <= zt - 0.25 + 0.25)] = HOLE
    r = np.hypot(X, Y)
    part[(Z > zt + 0.5) & (Z <= zt + 1.0) & (r <= 2.0) & (r > 1.5)] = GOLD           # the boss: outer ring
    part[(Z > zt + 1.0) & (Z <= zt + 1.25) & (r <= 1.5) & (r > 1.0)] = GOLD          # a second, higher step
    part[(Z > zt + 0.5) & (Z <= zt + 1.0) & (r <= 1.5)] = GOLD_DK
    part[(Z > zt + 1.0) & (Z <= zt + 2.0) & (r <= 0.7)] = SILVER                    # the post
    part[(Z > zt + 2.0) & (Z <= zt + 2.25) & (r <= 0.85)] = SILVER                  # its cap
    part[(Z > zt + 2.25) & (Z <= zt + 2.5) & (r <= 0.45)] = SILVER_DK
    # handle: a bent rod rising from the post, an inverted rounded triangle, hinged at the post
    zh = zt + 1.6
    hh = p["handle"]
    hc = zh + hh * 0.62
    dh = rtri(X, -(Z - hc), hh, 1.4)
    part[(np.abs(dh) <= 0.3) & (np.abs(Y) <= 0.3) & (Z > zh + 0.4)] = GOLD
    part[(np.abs(np.hypot(Y, Z - (zh + 0.4)) - 0.45) <= 0.15) & (np.abs(X) <= 0.5)] = GOLD_DK
    # the port, on the front of the bulge
    pz = z0 + (z1 - z0) * 0.5
    pr = p["port_r"]
    fy = front_y(float(profile(0.5, p)), rnd)
    rr = np.hypot(X, Z - pz)
    for rad, out_, pid in ((pr, 0.5, GOLD_DK), (pr * 0.93, 0.75, GOLD), (pr * 0.86, 1.0, GOLD_DK),
                           (pr * 0.79, 1.25, GOLD), (pr * 0.7, 1.25, GOLD)):
        part[(rr <= rad) & (Y >= fy - out_) & (Y <= fy + 1.0)] = pid
    # the face: a brass disc carrying the lantern emblem, where the ring goes. The emblem is cut into the
    # disc (a ring with a bar above and below, like the lantern logo); its socket in the middle glows
    face = (rr <= pr * 0.7) & (Y >= fy - 1.5) & (Y < fy - 1.25)
    part[face] = GOLD
    part[face & (rr > pr * 0.62)] = GOLD_DK
    er = pr * 0.46                                                                  # the emblem's size
    emb_ring = (rr <= er) & (rr > er * 0.62)
    bar = (np.abs(X) <= er * 1.05) & (np.abs(np.abs(Z - pz) - er * 1.0) <= 0.17)
    stem = (np.abs(X) <= 0.17) & (np.abs(Z - pz) > er * 0.62) & (np.abs(Z - pz) < er * 1.0)
    cut = (emb_ring | bar | stem) & (Y >= fy - 1.5) & (Y < fy - 1.25)
    part[cut] = EMBLEM
    part[(rr <= er * 0.45) & (Y >= fy - 1.5) & (Y < fy - 1.0)] = SOCKET               # the glowing socket
    for sx, sz in ((-1, 1), (1, -1)):                                                 # two screws
        part[(np.hypot(X - sx * pr * 0.52, Z - pz - sz * pr * 0.45) <= 0.2) & (Y >= fy - 1.75) & (Y < fy - 1.5)] = SILVER
    # two thick wire loops running from the port round the bulge, a little off the glass
    for dz in (-p["wire_gap"], p["wire_gap"]):
        zw = pz + dz
        sw = float(profile((zw - z0) / (z1 - z0), p))
        dw = rtri(X, Y, sw + 0.6, rnd)
        part[(np.abs(Z - zw) <= 0.3) & (np.abs(dw) <= 0.3) & (part == EMPTY)] = GOLD
    return xs, zs, part, pz


PAL = {SMOKE: (14, 40, 28), RIB: (28, 82, 52), PLATE: (22, 64, 44), GOLD: (214, 170, 80), GOLD_DK: (150, 110, 46),
       SILVER: (200, 204, 210), SILVER_DK: (110, 114, 120), VEIN: (196, 156, 70), HOLE: (10, 8, 6), EMBLEM: (40, 30, 16),
       SOCKET: (20, 70, 40)}
BRASS = {GOLD: (150, 120, 74), GOLD_DK: (88, 68, 40), VEIN: (176, 140, 66)}
KIND = {SMOKE: 4, RIB: 4, PLATE: 4, GOLD: 1, GOLD_DK: 1, SILVER: 1, SILVER_DK: 1, VEIN: 5, HOLE: 0, EMBLEM: 0, SOCKET: 4}


def quads(xs, zs, part, p, pz):
    occ = part > 0
    S = occ.shape
    Q, C, K, W = [], [], [], []
    z0, z1 = p["body"]
    for i, j, k in np.argwhere(occ):
        pid = int(part[i, j, k])
        c = np.array([xs[i], xs[j], zs[k]])
        # glow: the bulge is the heart; it fades over the ribs toward the collars
        # J: the light spreads through the whole glass, strongest at the bulge, still clear near the collars
        g = 0.3 + 0.7 * math.exp(-((c[2] - pz) / ((z1 - z0) * 0.42)) ** 2)
        gw = {VEIN: g, PLATE: g * 0.95, SMOKE: g * 0.55, RIB: g * 0.8, SOCKET: 1.4}.get(pid, 0.0)
        # uneven light inside the glass: each pixel a little brighter or dimmer, so it never goes flat
        hv = ((i * 2654435761) ^ (j * 40503) ^ (k * 2246822519)) & 1023
        if pid != SOCKET:
            gw *= 0.55 + 0.45 * hv / 1023
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            ni, nj, nk = i + n[0], j + n[1], k + n[2]
            if 0 <= ni < S[0] and 0 <= nj < S[1] and 0 <= nk < S[2] and occ[ni, nj, nk]:
                continue
            nv = np.array(n, float)
            h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
            shade = 0.62 + 0.5 * max(0.0, float(nv @ LIGHT))
            base = (BRASS.get(pid) if p.get("brass") else None) or PAL[pid]
            col = np.array(base, float) * (0.9 + 0.2 * h / 255)
            kind = KIND[pid]
            if pid in (RIB, SMOKE) and p.get("glassy"):
                # glass ribs: a bright lip on top, a dark underside, the face in between; a glossy
                # vertical streak where the light catches each face (like the film's polished ribs)
                if pid == RIB and n[2] > 0:
                    col = np.array([70, 150, 112.0])
                elif pid == RIB and n[2] < 0:
                    col = np.array([6, 18, 13.0])
                elif pid == RIB:
                    col = np.array([22, 66, 46.0]) * (0.9 + 0.2 * h / 255)
                    a_ = math.degrees(math.atan2(c[1], c[0]))
                    for streak in p.get("streaks", (-120.0, 0.0, 120.0)):
                        if abs((a_ - streak + 180) % 360 - 180) < 7:
                            col = col * 1.9 + 18
                else:
                    col = np.array([7, 20, 15.0])           # the grooves between ribs: near black
                if pid == RIB and p.get("hairline") and h < 9:
                    col, kind = np.array([190, 150, 66.0]), 5
            elif pid == RIB and n[2] > 0:
                col *= 1.3
            if pid == PLATE:
                col *= 1.1 if n[1] < 0 or n[0] != 0 else 0.95
            if pid == VEIN and h < 30:
                kind = 3
            col = col * shade
            a = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            b = np.cross(nv, a)
            f0 = c + nv * G / 2
            cs = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind); W.append(gw)
    return (np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8),
            np.asarray(W, np.float32))


G2 = dict(body=(3.0, 20.5), size=4.9, round=2.0, pinch=0.24, bulge=0.2, bulge_h=0.16, craze=1.5,
          lines=10, handle=4.6, port_r=2.3, wire_gap=1.0, seed=5)
H2 = dict(G2)
VERSIONS = {
    "k1": dict(H2, glassy=True),                                  # glassy ribs: lit lips, dark undersides, gloss
    "k2": dict(H2, glassy=True, rib_depth=2),                     # the same, ribs standing two pixels proud
    "k3": dict(H2, glassy=True, hairline=True),                   # with fine gold hairlines through the ribs
}
H_VERSIONS = {
    "h1": dict(G2, bulge=0.14),                       # a gentle bulge
    "h2": dict(G2),                                   # as in the stills
    "h3": dict(G2, bulge=0.26, bulge_h=0.19, brass=True),   # fuller, antique brass like the film
}
if __name__ == "__main__":
    for name, p in VERSIONS.items():
        xs, zs, part, pz = build(p)
        q, c, k, w = quads(xs, zs, part, p, pz)
        np.savez_compressed(os.path.join(OUT, f"dark5_{name}.npz"), quads=q, col=c, kind=k, glow=w)
        print(name, len(q), "faces", np.bincount(k, minlength=6))
