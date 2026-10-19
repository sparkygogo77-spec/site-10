"""New pixel lanterns (pass 606): six new designs at the Dark Lantern's level of pixel detail, with polished gold.

J on pass 604 (smooth meshes, all dropped): "do new lanterns, the depth of the dark lantern is just the level of
complexity and pixelated design, but of course i was expecting a more polished version of the gold on them".

Same grid and glass as tools/pixel_dark_lantern4.py (0.25 px voxels, 64 per block): glassy ribs at the ends (lit lip,
dark underside, near-black grooves), the crazed middle with plates standing a pixel proud and gold veins in the cracks,
branching gold lightning on the ribbed halves, dark dashed stitches down the front and sides. New here:
- polished gold: every gold face is shaded as metal, not paint: a bright lip on top faces, a mid tone that follows the
  light round the body, one specular column where the light glances, deep brown undersides, and engraved lines
  (GOLD_ENG) cut into collars and bands;
- the port has an original square socket (J's square ring), no corps logo.

    from pixel_lanterns6 import DESIGNS, build, quads, box_count
    part, xs, zs, pz = build("D1")
"""
import math
import numpy as np

G = 0.25
EMPTY, SMOKE, RIB, PLATE, GOLD, GOLD_DK, GOLD_ENG, SILVER, VEIN, HOLE, SOCKET = range(11)
METAL = {GOLD, GOLD_DK, GOLD_ENG, SILVER}
LIGHT = np.array([-0.45, -0.75, 0.6]); LIGHT /= np.linalg.norm(LIGHT)
XS = np.arange(-10, 10, G) + G / 2
ZS = np.arange(0, 33, G) + G / 2


def grid():
    return np.meshgrid(XS, XS, ZS, indexing="ij")


# ------------------------------------------------------------------ 2D sections (negative inside), front = -Y
def circle(X, Y, s):
    return np.hypot(X, Y) - s


def ngon(X, Y, n, s, rnd=0.0, turn=0.0):
    """Regular n-gon with apothem s, a flat face to the front (turn=0), corners rounded by rnd."""
    d = None
    for k in range(n):
        a = math.radians(-90 + turn) + k * 2 * math.pi / n
        v = X * math.cos(a) + Y * math.sin(a)
        d = v if d is None else np.maximum(d, v)
    if rnd <= 0:
        return d - s
    inner = d - (s - rnd)                           # shrink by rnd, then grow back round: rounded corners
    return np.where(inner > 0, _poly_dist(X, Y, n, s - rnd, turn), inner) - rnd


def _poly_dist(X, Y, n, s, turn):
    """Euclidean distance outside a regular polygon (apothem s)."""
    best = np.full(X.shape, np.inf)
    R = s / math.cos(math.pi / n)
    pts = [(R * math.cos(math.radians(-90 + turn) + (k + 0.5) * 2 * math.pi / n),
            R * math.sin(math.radians(-90 + turn) + (k + 0.5) * 2 * math.pi / n)) for k in range(n)]
    for k in range(n):
        (ax, ay), (bx, by) = pts[k - 1], pts[k]
        ex, ey = bx - ax, by - ay
        t = np.clip(((X - ax) * ex + (Y - ay) * ey) / (ex * ex + ey * ey), 0, 1)
        best = np.minimum(best, np.hypot(X - ax - t * ex, Y - ay - t * ey))
    return best


def vor3(P, cell, seed):
    """Distance to the nearest crack (border of a jittered 3D cell grid) and the cell's id (as pixel_dark_lantern4)."""
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


# ------------------------------------------------------------------ the glass (the Dark Lantern's treatment, any shape)
def glass(part, X, Y, Z, d, z0, z1, seed, bulge_h=0.16, craze=2.0, lines=5, ribs=True):
    """d: the glass section's signed distance on the grid. Ribbed ends, crazed middle, gold lightning."""
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    body = (Z > z0) & (Z <= z1)
    mid = (np.abs(H - 0.5) < bulge_h) if ribs else body
    part[body & (d <= 0)] = SMOKE
    ribbed = body & ~mid
    if ribs:
        row = (np.floor((Z - z0) / G) % 2) == 0
        part[ribbed & row & (d <= G) & (d > 0)] = RIB
        part[ribbed & row & (d <= 0) & (d > -G)] = RIB
    sub = body & mid & (d <= G) & (d > -G)
    idx = np.argwhere(sub)
    if len(idx):
        P = np.stack([X[sub], Y[sub], Z[sub]], -1)
        border, ident = vor3(P, craze, seed)
        proud = (ident * 2654435761 % 1000) < 330
        dd = d[sub]
        pv = np.where((dd <= 0) | proud, PLATE, 0)
        crack = (border < G * 0.28) & ((ident * 40503 % 100) < 70) & (pv > 0)
        pv = np.where(crack, VEIN, pv)
        cur = part[sub]
        part[sub] = np.where(pv > 0, pv, cur)
    # branching gold lightning on the ribbed halves
    if ribs and lines:
        rng = np.random.default_rng(seed + 1)
        ang = np.degrees(np.arctan2(Y[:, :, 0], X[:, :, 0]))
        zb_lo, zb_hi = z0 + (z1 - z0) * (0.5 - bulge_h), z0 + (z1 - z0) * (0.5 + bulge_h)
        cracks = []

        def walk(a, z, zend, sgn, depth):
            pts, heading = [], rng.uniform(-6, 6)
            while (z - zend) * sgn < 0:
                pts.append((a, z))
                if rng.random() < 0.12:
                    heading = rng.uniform(-14, 14)
                a += heading * 0.25 + rng.normal(0, 2.0)
                z += sgn * G
                if depth < 2 and rng.random() < 0.07:
                    walk(a, z, z + sgn * rng.uniform(1.0, 3.5), sgn, depth + 1)
            cracks.append(pts)

        for half, (za, zb) in enumerate(((z0, zb_lo), (zb_hi, z1))):
            for li in range(lines):
                a0 = li * 360.0 / lines + rng.uniform(-14, 14) + half * 180.0 / lines
                if half == 0:
                    walk(a0, za + rng.uniform(0.2, 1.0), zb - rng.uniform(0.0, 1.0), 1, 0)
                else:
                    walk(a0, zb - rng.uniform(0.2, 1.0), za + rng.uniform(0.0, 1.0), -1, 0)
        rad = np.hypot(X[:, :, 0], Y[:, :, 0])
        for pts in cracks:
            for a_, z_ in pts:
                k = int(round((z_ - ZS[0]) / G))
                if not 0 <= k < len(ZS):
                    continue
                sl = ribbed[:, :, k] & (d[:, :, k] <= G) & (d[:, :, k] > -G) & (part[:, :, k] > 0)
                dist = np.abs((ang - a_ + 180) % 360 - 180) * np.pi / 180 * np.maximum(rad, 1)
                part[:, :, k][sl & (dist < G * 0.6)] = VEIN
    return H


def band(part, X, Y, Z, sec, zlo, zhi, pid, engrave=None):
    """Fill the section sec (<=0) between zlo and zhi; engrave='dots'|'zig'|'line' cuts GOLD_ENG into its outer skin."""
    m = (Z > zlo) & (Z <= zhi) & (sec <= 0)
    part[m] = pid
    if engrave:
        skin = m & (sec > -G)
        u = np.degrees(np.arctan2(Y, X)) * np.hypot(X, Y) * math.pi / 180 / G     # pixels round the body
        v = (Z - zlo) / G
        hgt = (zhi - zlo) / G
        if engrave == "dots":
            cut = (np.round(u) % 3 == 0) & (np.abs(v - hgt / 2) < 0.6)
        elif engrave == "zig":
            cut = np.abs(((u % 6) - 3) - (v - hgt / 2) * 1.5) < 0.6
        else:
            cut = np.abs(v - hgt / 2) < 0.5
        part[skin & cut] = GOLD_ENG
    return m


def stepped(part, X, Y, Z, secfn, z, steps, down=False):
    """A bevelled stack: steps = [(grow, height, pid, engrave)] built upward from z (or downward)."""
    for grow, h, pid, eng in steps:
        lo, hi = (z - h, z) if down else (z, z + h)
        band(part, X, Y, Z, secfn(grow), lo, hi, pid, eng)
        z = lo if down else hi
    return z


def port(part, X, Y, Z, pz, pr=2.6):
    """The ring port on the front: knurled rings stepping out, a gold face with an engraved ring, a square socket
    (J's square ring) with a glowing heart, two silver screws. Sits on the front of whatever is there at pz."""
    col = (np.abs(X) < pr) & (np.abs(Z - pz) < pr) & (part > 0)
    ys = np.where(col, Y, np.inf)
    fy = float(ys.min()) if np.isfinite(ys.min()) else -5.0
    rr = np.hypot(X, Z - pz)
    for rad, out_, pid in ((pr, 0.5, GOLD_DK), (pr * 0.93, 0.75, GOLD), (pr * 0.86, 1.0, GOLD_DK),
                           (pr * 0.79, 1.25, GOLD), (pr * 0.7, 1.25, GOLD)):
        part[(rr <= rad) & (Y >= fy - out_) & (Y <= fy + 1.0)] = pid
    face = (rr <= pr * 0.7) & (Y >= fy - 1.5) & (Y < fy - 1.25)
    part[face] = GOLD
    part[face & (rr > pr * 0.6) & (rr <= pr * 0.66)] = GOLD_ENG
    half = 5 * G
    sq = np.maximum(np.abs(X), np.abs(Z - pz))
    part[(sq <= half + G) & (Y >= fy - 1.5) & (Y < fy - 1.0)] = HOLE
    part[(sq <= half) & (sq > half - G) & (Y >= fy - 1.75) & (Y < fy - 1.25)] = GOLD
    part[(sq <= half - 2 * G) & (Y >= fy - 1.5) & (Y < fy - 1.0)] = SOCKET
    for sx, sz in ((-1, 1), (1, -1)):
        part[(np.hypot(X - sx * pr * 0.55, Z - pz - sz * pr * 0.42) <= 0.22) & (Y >= fy - 1.75) & (Y < fy - 1.5)] = SILVER
    return fy


def rod(part, X, Y, Z, pts, r, pid=GOLD):
    """A round rod through a polyline of (x, y, z) points."""
    P = np.stack([X, Y, Z], -1)
    for a, b in zip(pts, pts[1:]):
        a, b = np.array(a, float), np.array(b, float)
        e = b - a
        lo = np.minimum(a, b) - r - G; hi = np.maximum(a, b) + r + G
        box = (X > lo[0]) & (X < hi[0]) & (Y > lo[1]) & (Y < hi[1]) & (Z > lo[2]) & (Z < hi[2])
        Q = P[box]
        t = np.clip(((Q - a) @ e) / (e @ e), 0, 1)
        dist = np.linalg.norm(Q - a - t[:, None] * e, axis=-1)
        sel = np.zeros(X.shape, bool); sel[box] = dist <= r
        part[sel] = pid


def ring_xz(part, X, Y, Z, cz, R, r, pid=GOLD, turn=0.0, axis="z"):
    """A torus of radius R, tube r, centred (0, 0, cz); axis 'z' = horizontal ring, 'y' = upright, turned by turn deg."""
    a = math.radians(turn)
    Xr, Yr = X * math.cos(a) + Y * math.sin(a), -X * math.sin(a) + Y * math.cos(a)
    if axis == "z":
        q = np.hypot(np.hypot(Xr, Yr) - R, Z - cz)
    else:
        q = np.hypot(np.hypot(Xr, Z - cz) - R, Yr)
    part[q <= r] = pid


# ------------------------------------------------------------------ the six designs
def d1_vault(X, Y, Z):
    """Rounded-square glass column held by four fluted gold corner pillars; stepped pyramid roof with a finial."""
    part = np.zeros(X.shape, np.int8)
    z0, z1, s = 5.0, 21.0, 4.6
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = s * (1 - 0.1 * np.sin(np.pi * H) ** 1.5) + 0.35 * np.exp(-((H - 0.5) / 0.12) ** 2)
    sec = ngon(X, Y, 4, size, rnd=1.4)
    glass(part, X, Y, Z, sec, z0, z1, seed=61)
    sq = lambda g: ngon(X, Y, 4, s + g, rnd=1.4)
    stepped(part, X, Y, Z, sq, z0, [(1.0, 0.5, GOLD_DK, None), (1.5, 0.75, GOLD, "dots"), (1.9, 0.5, GOLD, None),
                                     (1.4, 0.75, GOLD_DK, None), (2.2, 0.75, GOLD, "line")], down=True)
    zt = stepped(part, X, Y, Z, sq, z1, [(1.0, 0.5, GOLD_DK, None), (1.6, 0.75, GOLD, "dots"), (1.9, 0.5, GOLD, None)])
    for k, (g, h) in enumerate(((1.6, 0.75), (0.9, 0.75), (0.2, 0.75), (-0.6, 0.75), (-1.5, 0.75), (-2.4, 0.75))):
        band(part, X, Y, Z, sq(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK, "line" if k == 1 else None)
        zt += h
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.25) & (np.hypot(r, (Z - zt - 0.6) * 1.2) <= 1.1)] = GOLD           # finial ball
    part[(Z > zt + 1.25) & (Z <= zt + 2.5) & (r <= 0.35)] = SILVER
    ring_xz(part, X, Y, Z, zt + 3.4, 1.0, 0.3, GOLD, axis="y")
    c = s * 0.83                                                                                    # corner pillars
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = np.hypot(X - sx * c, Y - sy * c)
            pil = (q <= 0.9) & (Z > z0 - 0.5) & (Z <= z1 + 0.5)
            part[pil] = GOLD
            ang = np.arctan2(Y - sy * c, X - sx * c)
            part[pil & (q > 0.6) & (np.round(ang / (math.pi / 4)) % 2 == 0)] = GOLD_DK                # flutes
            for zc in (z0 + 0.6, z1 - 0.6, (z0 + z1) / 2):
                part[(q <= 1.15) & (np.abs(Z - zc) <= 0.3)] = GOLD
    pz = (z0 + z1) / 2
    port(part, X, Y, Z, pz)
    return part, pz


def d2_bell(X, Y, Z):
    """Bell-shaped glass widening to the foot, eight polished gold ribs, a scalloped crown and a ring handle."""
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 3.5, 20.5
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 3.2 + 2.6 * (1 - H) ** 1.6 + 0.3 * np.exp(-((H - 0.45) / 0.1) ** 2)
    sec = circle(X, Y, size)
    glass(part, X, Y, Z, sec, z0, z1, seed=62, bulge_h=0.13)
    ang = np.arctan2(Y, X)
    for k in range(8):                                                                       # ribs, a pixel proud
        a = -math.pi / 2 + math.pi / 8 + k * math.pi / 4
        da = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) * np.hypot(X, Y)
        part[(da <= 0.4) & (sec > -G) & (sec <= 0.5) & (Z > z0) & (Z <= z1)] = GOLD
    cf = lambda g: circle(X, Y, 5.8 + g)
    stepped(part, X, Y, Z, cf, z0, [(0.3, 0.5, GOLD_DK, None), (0.8, 0.75, GOLD, "zig"), (1.2, 0.5, GOLD, None),
                                     (0.6, 0.5, GOLD_DK, None), (1.4, 0.75, GOLD, "line")], down=True)
    ct = lambda g: circle(X, Y, 3.2 + g)
    zt = stepped(part, X, Y, Z, ct, z1, [(0.4, 0.5, GOLD_DK, None), (1.0, 0.75, GOLD, "dots")])
    sc = (np.cos(np.arctan2(Y, X) * 8) > 0.2)                                                # scalloped rim
    part[(Z > zt) & (Z <= zt + 0.75) & (circle(X, Y, 4.2) <= 0) & (circle(X, Y, 3.4) > 0) & sc] = GOLD
    for k, (g, h) in enumerate(((0.6, 0.5), (0.0, 0.5), (-0.8, 0.5), (-1.6, 0.5), (-2.3, 0.5))):  # dome
        band(part, X, Y, Z, ct(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK)
        zt += h
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.0) & (r <= 0.5)] = SILVER
    ring_xz(part, X, Y, Z, zt + 2.6, 1.6, 0.35, GOLD, axis="y")
    pz = z0 + (z1 - z0) * 0.42
    port(part, X, Y, Z, pz, pr=2.4)
    return part, pz


def d3_gourd(X, Y, Z):
    """Two stacked glass bulbs with an engraved gold cuff at the waist, a petal crown and a tall bail."""
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.0, 22.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 2.3 + 3.0 * np.exp(-((H - 0.28) / 0.19) ** 2) + 2.2 * np.exp(-((H - 0.76) / 0.15) ** 2)
    sec = circle(X, Y, size)
    glass(part, X, Y, Z, sec, z0, z1, seed=63, bulge_h=0.12, lines=4)
    zw = z0 + (z1 - z0) * 0.53
    cw = lambda g: circle(X, Y, 3.0 + g)
    stepped(part, X, Y, Z, cw, zw - 1.5, [(0.4, 0.5, GOLD_DK, None), (0.9, 1.0, GOLD, "zig"), (1.1, 0.5, GOLD, None),
                                          (0.5, 0.5, GOLD_DK, None)])
    cf = lambda g: circle(X, Y, 2.6 + g)
    stepped(part, X, Y, Z, cf, z0, [(0.5, 0.75, GOLD, None), (1.4, 0.5, GOLD_DK, None), (2.6, 0.75, GOLD, "dots"),
                                     (3.2, 0.5, GOLD, None)], down=True)
    zt = stepped(part, X, Y, Z, cf, z1, [(0.2, 0.5, GOLD_DK, None), (0.8, 0.75, GOLD, "line")])
    ang = np.arctan2(Y, X)
    for k in range(6):                                                                       # petal crown
        a = -math.pi / 2 + k * math.pi / 3
        px, py = 2.3 * math.cos(a), 2.3 * math.sin(a)
        q = np.hypot(X - px, Y - py)
        part[(q <= 0.9 - (Z - zt) * 0.35) & (Z > zt) & (Z <= zt + 2.0)] = GOLD
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.5) & (r <= 1.2)] = GOLD_DK
    part[(Z > zt + 1.5) & (Z <= zt + 2.25) & (r <= 0.5)] = SILVER
    arch = [(4.6 * math.cos(math.pi * k / 16), 0.0, zt - 3.0 + 5.5 * math.sin(math.pi * k / 16)) for k in range(17)]
    rod(part, X, Y, Z, arch, 0.35)
    for sx in (-1, 1):
        part[(np.hypot(X - sx * 4.6, Y) <= 0.6) & (np.abs(Z - (zt - 3.0)) <= 0.4)] = GOLD_DK      # hinge bosses
    pz = z0 + (z1 - z0) * 0.28
    port(part, X, Y, Z, pz, pr=2.5)
    return part, pz


def d4_hex(X, Y, Z):
    """A classic hexagonal lantern: panels widening upward, proud gold mullions, a vented hex dome, a swing bail."""
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.5, 19.5
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 4.0 + 1.0 * H
    sec = ngon(X, Y, 6, size)
    glass(part, X, Y, Z, sec, z0, z1, seed=64, bulge_h=0.15, lines=6)
    ang = np.arctan2(Y, X)
    for k in range(6):                                                                       # mullions at the corners
        a = -math.pi / 2 + math.pi / 6 + k * math.pi / 3
        da = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) * np.hypot(X, Y)
        part[(da <= 0.45) & (sec > -G) & (sec <= 0.75) & (Z > z0) & (Z <= z1)] = GOLD
    hx = lambda g: ngon(X, Y, 6, 4.0 + g)
    stepped(part, X, Y, Z, hx, z0, [(0.4, 0.5, GOLD_DK, None), (1.0, 0.75, GOLD, "dots"), (0.6, 0.5, GOLD_DK, None),
                                     (1.4, 0.75, GOLD, None), (1.6, 0.5, GOLD_DK, None)], down=True)
    part[(np.abs(Z - (z0 + z1) / 2) <= 0.4) & (ngon(X, Y, 6, 4.5 + 0.55) <= 0) & (part != SMOKE)] = GOLD
    ht = lambda g: ngon(X, Y, 6, 5.0 + g)
    zt = stepped(part, X, Y, Z, ht, z1, [(0.4, 0.5, GOLD_DK, None), (1.0, 0.75, GOLD, "zig"), (1.3, 0.5, GOLD, None)])
    zd = zt
    for k in range(9):                                                                       # dome, vents round it
        g = 1.0 - 0.75 * k
        m = band(part, X, Y, Z, ht(g), zt, zt + 0.5, GOLD if k % 2 == 0 else GOLD_DK)
        zt += 0.5
    vent = (np.round(np.degrees(ang) / 15) % 4 == 0) & (Z > zd + 1.0) & (Z <= zd + 2.0) & (ht(-1.0) > -G * 2)
    part[vent & (part > 0)] = HOLE
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.0) & (r <= 0.9)] = GOLD
    part[(Z > zt + 1.0) & (Z <= zt + 1.5) & (r <= 1.2)] = GOLD_DK
    arch = [(5.3 * math.cos(math.pi * k / 16), 0.0, zd + 0.5 + 6.0 * math.sin(math.pi * k / 16)) for k in range(17)]
    rod(part, X, Y, Z, arch, 0.33)
    pz = z0 + (z1 - z0) * 0.5
    port(part, X, Y, Z, pz, pr=2.3)
    return part, pz


def d5_crystal(X, Y, Z):
    """A tall faceted crystal held in gold claws at both ends, a hanging hook on top."""
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 3.0, 23.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.0 + 4.4 * (1 - np.abs(2 * H - 1)) ** 0.6
    sec = ngon(X, Y, 8, size)
    glass(part, X, Y, Z, sec, z0, z1, seed=65, bulge_h=0.2, lines=4)
    cup = lambda g: ngon(X, Y, 8, 2.4 + g)
    stepped(part, X, Y, Z, cup, z0 + 2.0, [(0.0, 0.75, GOLD, "dots"), (0.6, 0.5, GOLD_DK, None), (1.4, 0.75, GOLD, None),
                                            (2.2, 0.5, GOLD_DK, None), (3.0, 0.75, GOLD, "line")], down=True)
    zt = stepped(part, X, Y, Z, cup, z1 - 2.0, [(0.0, 0.75, GOLD, "dots"), (0.6, 0.5, GOLD_DK, None)])
    for k in range(4):                                                                       # four claws each end
        a = -math.pi / 2 + math.pi / 8 + k * math.pi / 2
        for zs_, ze in ((z0 + 2.0, z0 + (z1 - z0) * 0.34), (z1 - 2.0, z1 - (z1 - z0) * 0.34)):
            pts = []
            for i in range(9):
                z = zs_ + (ze - zs_) * i / 8
                h = (z - z0) / (z1 - z0)
                rr = (1.0 + 4.4 * (1 - abs(2 * h - 1)) ** 0.6) / math.cos(math.pi / 8) + 0.35
                pts.append((rr * math.cos(a), rr * math.sin(a), z))
            rod(part, X, Y, Z, pts, 0.45)
            part[(np.hypot(X - pts[-1][0], Y - pts[-1][1]) <= 0.7) & (np.abs(Z - pts[-1][2]) <= 0.5)] = GOLD   # claw tip
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.5) & (r <= 0.8)] = GOLD_DK
    ring_xz(part, X, Y, Z, zt + 2.8, 1.3, 0.35, GOLD, axis="y")
    pz = z0 + (z1 - z0) * 0.5
    port(part, X, Y, Z, pz, pr=2.3)
    return part, pz


def d6_armillary(X, Y, Z):
    """A glass sphere inside three polished gold rings (an armillary) on a stepped pedestal."""
    part = np.zeros(X.shape, np.int8)
    cz, R = 14.0, 5.6
    sec = np.hypot(np.hypot(X, Y), Z - cz) - R
    z0, z1 = cz - R, cz + R
    glass(part, X, Y, Z, sec, z0, z1, seed=66, bulge_h=0.17, lines=4)
    ring_xz(part, X, Y, Z, cz, R + 1.3, 0.45, GOLD, axis="z")
    ring_xz(part, X, Y, Z, cz, R + 1.3, 0.4, GOLD, axis="y", turn=45)
    ring_xz(part, X, Y, Z, cz, R + 1.3, 0.4, GOLD, axis="y", turn=-45)
    for zc in (cz - R - 1.3, cz + R + 1.3):                                                  # where the rings meet
        part[(np.hypot(np.hypot(X, Y), Z - zc) <= 0.9)] = GOLD_DK
    pd = lambda g: circle(X, Y, 1.4 + g)
    zb = cz - R - 1.6
    band(part, X, Y, Z, pd(0.0), 2.5, zb, GOLD)
    band(part, X, Y, Z, pd(0.5), (2.5 + zb) / 2 - 0.4, (2.5 + zb) / 2 + 0.4, GOLD_DK, None)
    stepped(part, X, Y, Z, pd, 2.5, [(1.2, 0.5, GOLD_DK, None), (2.4, 0.75, GOLD, "zig"), (3.2, 0.5, GOLD, None),
                                      (3.8, 0.75, GOLD_DK, None), (4.4, 0.5, GOLD, "dots")], down=True)
    r = np.hypot(X, Y)
    zt = cz + R + 2.0
    part[(Z > zt) & (Z <= zt + 1.0) & (r <= 0.45)] = SILVER
    ring_xz(part, X, Y, Z, zt + 2.0, 1.1, 0.33, GOLD, axis="y")
    port(part, X, Y, Z, cz, pr=2.4)
    return part, cz


DESIGNS = {"D1": ("Vault", d1_vault), "D2": ("Bell", d2_bell), "D3": ("Gourd", d3_gourd),
           "D4": ("Hex classic", d4_hex), "D5": ("Crystal", d5_crystal), "D6": ("Armillary", d6_armillary)}


def build(code):
    X, Y, Z = grid()
    part, pz = DESIGNS[code][1](X, Y, Z)
    return part, pz


# ------------------------------------------------------------------ colours: glassy glass, polished gold
PAL = {SMOKE: (14, 40, 28), RIB: (28, 82, 52), PLATE: (22, 64, 44), VEIN: (196, 156, 70), HOLE: (10, 8, 6),
       SOCKET: (20, 70, 40), SILVER: (200, 204, 210)}
KIND = {SMOKE: 4, RIB: 4, PLATE: 4, GOLD: 1, GOLD_DK: 1, GOLD_ENG: 1, SILVER: 1, VEIN: 5, HOLE: 0, SOCKET: 4}
STREAKS = (-90.0, 30.0, 150.0)


def gold_colour(pid, n, c, h):
    """Polished gold: lit lip on top, the mid tone follows the light round the body, a specular column where the light
    glances, deep brown undersides; GOLD_DK sits in shadow, GOLD_ENG is the cut line."""
    if pid == GOLD_ENG:
        return np.array([92, 60, 22.0]) * (0.95 + 0.1 * h / 255)
    if n[2] > 0:
        col = np.array([255, 212, 104.0])
    elif n[2] < 0:
        col = np.array([84, 54, 20.0])
    else:
        lit = float(np.dot(np.array(n, float), LIGHT))                 # -0.9 .. 0.9 on side faces
        col = np.array([150, 104, 36.0]) + (np.array([238, 190, 86.0]) - np.array([150, 104, 36.0])) * (lit + 0.9) / 1.8
        az = math.degrees(math.atan2(c[1], c[0]))
        if abs((az - (-110.0) + 180) % 360 - 180) < 9:                # the specular column
            col = np.array([255, 232, 160.0])
    if pid == GOLD_DK:
        col = col * 0.66
    return col * (0.96 + 0.08 * h / 255)


def face_colour(pid, i, j, k, n, c):
    h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
    if pid in (GOLD, GOLD_DK, GOLD_ENG):
        return gold_colour(pid, n, c, h), KIND[pid]
    shade = 0.62 + 0.5 * max(0.0, float(np.array(n, float) @ LIGHT))
    col = np.array(PAL[pid], float) * (0.9 + 0.2 * h / 255)
    kind = KIND[pid]
    if pid == RIB:
        if n[2] > 0:
            col = np.array([70, 150, 112.0])
        elif n[2] < 0:
            col = np.array([6, 18, 13.0])
        else:
            col = np.array([22, 66, 46.0]) * (0.9 + 0.2 * h / 255)
            a_ = math.degrees(math.atan2(c[1], c[0]))
            if any(abs((a_ - s + 180) % 360 - 180) < 7 for s in STREAKS):
                col = np.array([6, 18, 13.0]) if (k // 2) % 2 == 0 else col * 0.55   # dark dashed stitches
    elif pid == SMOKE:
        col = np.array([7, 20, 15.0])
    elif pid == PLATE:
        col *= 1.1 if n[1] < 0 or n[0] != 0 else 0.95
    elif pid == VEIN and h < 30:
        kind = 3
    elif pid == SILVER:
        col = np.array([236, 238, 242.0]) if n[2] > 0 else col
    return col * shade, kind


def glow_weight(pid, i, j, k, c, pz, span):
    g = 0.04 + 0.96 * math.exp(-((c[2] - pz) / (span * 0.26)) ** 2) ** 1.5    # dark ends, light round the port
    gw = {VEIN: g * 0.6, PLATE: g * 0.95, SMOKE: g * 0.55, RIB: g * 0.8, SOCKET: 1.4}.get(pid, 0.0)
    hv = ((i * 2654435761) ^ (j * 40503) ^ (k * 2246822519)) & 1023
    if pid != SOCKET:
        gw *= 0.55 + 0.45 * hv / 1023
    return gw


def quads(part, pz):
    """Every exposed voxel face: corners (px), sRGB colour, kind, glow weight."""
    occ = part > 0
    S = occ.shape
    zs = [k for k in range(S[2]) if occ[:, :, k].any()]
    span = (ZS[max(zs)] - ZS[min(zs)]) if zs else 1.0
    Q, C, K, W = [], [], [], []
    pad = np.pad(occ, 1)
    for i, j, k in np.argwhere(occ):
        pid = int(part[i, j, k])
        c = np.array([XS[i], XS[j], ZS[k]])
        gw = glow_weight(pid, i, j, k, c, pz, span)
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            if pad[i + 1 + n[0], j + 1 + n[1], k + 1 + n[2]]:
                continue
            nv = np.array(n, float)
            col, kind = face_colour(pid, i, j, k, n, c)
            a = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            b = np.cross(nv, a)
            f0 = c + nv * G / 2
            cs = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind); W.append(gw)
    return (np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8), np.asarray(W, np.float32))


def box_count(part):
    """Greedy boxes per part (what a Blockbench export would hold; the jar's dark lantern is 2,118)."""
    total = 0
    for pid in np.unique(part):
        if pid == EMPTY:
            continue
        m = part == pid
        S = m.shape
        for k in range(S[2]):
            if not m[:, :, k].any():
                continue
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
                    total += 1
    return total
