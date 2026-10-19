"""Pass 611: the 610 relics (N1 shrine, N2 reliquary) taken further, 12 green takes.

J on 610: build on "Relics"; change "More detail", "Bigger glow", "Mix the ideas", "Smaller port"; "All green"; "12
total". So six shrines and six reliquaries: one detailed take of each, and the rest crossing the relic with 610's other
ideas (roots, crystals, floating rings, a split shell) or with a ruin / second storey. Every take: denser carving and
studs, light leaking out of the frame (glowing windows, seams, cracks), a bigger flaring core, a small port that sits
into the design. Voxels on the Dark Lantern grid; bronze with verdigris, gold, black steel, bark, crystal.
"""
import math
import numpy as np
from pixel_lanterns6 import G, grid, circle, ngon, glass, band, stepped, rod, ring_xz, EMPTY, GOLD, GOLD_DK, GOLD_ENG, SILVER
import pixel_lanterns6 as P6
import pixel_lanterns7 as P7
from pixel_lanterns7 import hollow, core, studs, coarsen_glass, CORE
import pixel_lanterns10 as P10
from pixel_lanterns10 import BRONZE, STEEL, OBSID, BARK, CRYS, tilted_ring

P10.STYLE["hue"] = None                                   # all green
_gw = getattr(P6, "_p11_base_glow", P6.glow_weight)        # keep the base once: reloads must not compound the 1.5
P6._p11_base_glow = _gw


def glow_weight(pid, i, j, k, c, pz, span):
    return _gw(pid, i, j, k, c, pz, span) * 1.5            # "Bigger glow"


P6.glow_weight = glow_weight


def small_port(part, X, Y, Z, pz, pr=1.5):
    return P6.port(part, X, Y, Z, pz, pr=pr)


# ------------------------------------------------------------------ add-ons that cross the relic with 610's other ideas
def roots(part, X, Y, Z, n, base_r, top_z, hug, seed, r=0.42, buds=True, avoid_front=True):
    """Roots climb from the ground round a body of radius hug(z), twisting, with glowing buds."""
    rng = np.random.default_rng(seed)
    for k in range(n):
        a0 = k * 2 * math.pi / n + rng.uniform(-0.25, 0.25)
        pts = []
        for i in range(24):
            t = i / 23
            zz = 0.3 + (top_z - 0.3) * t
            rad = max(hug(zz) + 0.45, base_r * (1 - t) ** 2.2 + (hug(zz) + 0.45) * (1 - (1 - t) ** 2.2))
            a = a0 + 1.1 * t
            if avoid_front and abs(((a % (2 * math.pi)) - 1.5 * math.pi)) < 0.4:
                a += 0.55
            pts.append((rad * math.cos(a), rad * math.sin(a), zz))
        rod(part, X, Y, Z, pts, r, BARK)
        if buds:
            for i in (6, 12, 18):
                if rng.random() < 0.75:
                    studs(part, X, Y, Z, [pts[i]], r=0.42, pid=CORE)


def crystals(part, X, Y, Z, spots, seed):
    """Crystal prisms (shell only) bursting out at (x, y, z, tilt, azimuth, length, radius)."""
    P = np.stack([X, Y, Z], -1)
    for (x, y, z, tilt, az, L, rad) in spots:
        t, a = math.radians(tilt), math.radians(az)
        d = np.array([math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t)])
        q = P - np.array([x, y, z])
        along = q @ d
        lo = np.array([x, y, z]) - rad - 0.5
        perp = np.linalg.norm(q - along[..., None] * d, axis=-1)
        rr = rad * np.clip((L - along) / (L * 0.3), 0, 1)
        inside = (along > -0.5) & (along < L) & (perp <= rr)
        part[inside & (perp > rr - 0.5)] = CRYS
        part[inside & (perp <= rr - 0.5)] = CORE if rad > 1.1 else CRYS


def halo_rings(part, X, Y, Z, cz, rings):
    for R, r, tilt, turn, pid in rings:
        tilted_ring(part, X, Y, Z, cz, R, r, tilt, turn, pid)


# ------------------------------------------------------------------ shrine family
def shrine(X, Y, Z, seed, storeys=1, dome_windows=True, broken=False, dome=True, column_spiral=True):
    part = np.zeros(X.shape, np.int8)
    sq = lambda g: ngon(X, Y, 4, 4.4 + g, rnd=0.6)
    z = 0.0
    for g, h, eng in ((2.8, 0.5, None), (2.6, 0.5, "dots"), (2.0, 0.75, "zig"), (1.4, 0.75, None), (0.9, 0.75, "dots")):
        band(part, X, Y, Z, sq(g), z, z + h, BRONZE, eng)
        z += h
    for sx in (-1, 1):                                                     # studs along the top step's edge
        for t in np.linspace(-4.2, 4.2, 7):
            studs(part, X, Y, Z, [(t, sx * 5.3, z - 0.1), (sx * 5.3, t, z - 0.1)], r=0.3, pid=GOLD)
    z0 = z
    zt = z
    for s_ in range(storeys):
        h = 11.0 if storeys == 1 else 7.5
        s = 3.4 if s_ == 0 else 2.6
        z1 = zt + h
        sec = ngon(X, Y, 4, s, rnd=0.8)
        glass(part, X, Y, Z, sec, zt, z1, seed=seed + s_, craze=2.6, lines=3)
        hollow(part, sec)
        c = s + 0.6
        for sx in (-1, 1):
            for sy in (-1, 1):
                if broken and s_ == 0 and sx == 1 and sy == -1:
                    part[(np.hypot(X - c, Y + c) <= 0.95) & (Z > zt) & (Z <= zt + 4.5)] = BRONZE    # a broken column
                    studs(part, X, Y, Z, [(c + 1.6, -c - 1.2, 0.6 + z0 - 2.0), (c + 2.4, -c + 0.4, z0 - 2.4)], r=0.7, pid=BRONZE)
                    continue
                cx, cy = sx * c, sy * c
                q = np.hypot(X - cx, Y - cy)
                col = (q <= 0.95) & (Z > zt) & (Z <= z1)
                part[col] = BRONZE
                ang = np.arctan2(Y - cy, X - cx)
                if column_spiral:                                          # spiral fluting
                    fl = np.round((ang + (Z - zt) * 0.35) / (math.pi / 5)) % 2 == 0
                else:
                    fl = np.round(ang / (math.pi / 5)) % 2 == 0
                part[col & (q > 0.65) & fl & (Z > zt + 0.8) & (Z <= z1 - 0.8)] = GOLD_ENG
                for zc, w in ((zt + 0.3, 1.35), (z1 - 0.3, 1.35), (z1 - 0.9, 1.15)):
                    part[(np.maximum(np.abs(X - cx), np.abs(Y - cy)) <= w) & (np.abs(Z - zc) <= 0.3)] = BRONZE
        sq2 = lambda g, s=s: ngon(X, Y, 4, s + 1.0 + g, rnd=0.6)
        band(part, X, Y, Z, sq2(1.6), z1, z1 + 0.75, BRONZE, "zig")
        band(part, X, Y, Z, sq2(2.0), z1 + 0.75, z1 + 1.25, GOLD)
        for sx in (-1, 1):                                                 # frieze studs
            for t in np.linspace(-(s + 2.2), s + 2.2, 6):
                studs(part, X, Y, Z, [(t, sx * (s + 3.1), z1 + 0.4), (sx * (s + 3.1), t, z1 + 0.4)], r=0.28, pid=GOLD)
        zt = z1 + 1.25
    if not dome:
        return part, (z0 + z0 + 11.0) / 2, zt
    dz = zt
    R = 5.0 if storeys == 1 else 4.0
    for k in range(10):
        rr = R * math.cos(math.asin(min(1.0, k / 10)))
        band(part, X, Y, Z, circle(X, Y, rr), zt, zt + 0.5, BRONZE if k % 3 else GOLD_DK)
        zt += 0.5
    ang = np.arctan2(Y, X)
    rib = (np.round(ang / (math.pi / 6)) % 2 == 0) & (np.abs(((ang / (math.pi / 6)) % 1) - 0.5) < 0.12)
    part[rib & (np.hypot(np.hypot(X, Y), (Z - dz) * 1.0) <= R + 0.35) & (np.hypot(np.hypot(X, Y), Z - dz) > R - 0.2) & (Z > dz)] = GOLD
    if dome_windows:                                                       # glowing windows round the dome
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            wx, wy = (R - 0.3) * math.cos(a) * 0.88, (R - 0.3) * math.sin(a) * 0.88
            studs(part, X, Y, Z, [(wx, wy, dz + 1.4)], r=0.55, pid=CORE)
    if broken:                                                             # cracked dome: light pours out
        crack = (np.abs(np.arctan2(Y, X) - 0.6) < 0.35) & (Z > dz) & (np.hypot(np.hypot(X, Y), Z - dz) <= R + 0.4)
        part[crack & np.isin(part, [BRONZE, GOLD_DK, GOLD])] = EMPTY
        part[crack & (np.hypot(np.hypot(X, Y), Z - dz) <= R - 0.4) & (np.hypot(np.hypot(X, Y), Z - dz) > R - 1.0)] = CORE
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.6) & (np.hypot(r, (Z - zt - 0.8) * 1.1) <= 0.9)] = GOLD
    part[(Z > zt + 1.6) & (Z <= zt + 2.6) & (r <= 0.3)] = GOLD
    studs(part, X, Y, Z, [(0, 0, zt + 2.9)], r=0.5, pid=CORE)
    pz = z0 + 5.5
    return part, pz, zt


def s1_detailed(X, Y, Z):
    part, pz, zt = shrine(X, Y, Z, 111)
    core(part, 0, 0, pz, 2.6)
    small_port(part, X, Y, Z, pz)
    return part, pz


def s2_overgrown(X, Y, Z):
    part, pz, zt = shrine(X, Y, Z, 112)
    roots(part, X, Y, Z, 6, 6.8, zt + 1.0, lambda z: 4.6 if z < 15.0 else max(0.5, 5.0 * math.sqrt(max(0.0, 1 - ((z - 15.0) / 5.2) ** 2))),
          seed=112)
    core(part, 0, 0, pz, 2.6)
    small_port(part, X, Y, Z, pz)
    return part, pz


def s3_crystal(X, Y, Z):
    part, pz, zt = shrine(X, Y, Z, 113, dome_windows=False)
    crystals(part, X, Y, Z, [(0.0, 0.0, zt - 2.0, 0, 0, 7.5, 1.5), (1.6, 0.8, zt - 3.0, 35, 20, 5.0, 0.9),
                              (-1.4, 1.0, zt - 3.0, 38, 150, 4.5, 0.8), (0.5, -1.6, zt - 3.2, 30, 260, 4.0, 0.7),
                              (4.8, 4.8, 3.0, 50, 45, 4.0, 0.8), (-4.8, 4.6, 3.0, 48, 135, 3.5, 0.7),
                              (5.0, -4.6, 3.0, 52, -45, 3.0, 0.6)], seed=113)
    core(part, 0, 0, pz, 2.6)
    small_port(part, X, Y, Z, pz)
    return part, pz


def s4_halo(X, Y, Z):
    part, pz, zt = shrine(X, Y, Z, 114)
    halo_rings(part, X, Y, Z, zt - 2.0, [(6.6, 0.35, 12, 0, BRONZE), (7.4, 0.3, -18, 60, GOLD)])
    for a in range(0, 360, 90):
        ar = math.radians(a + 45)
        studs(part, X, Y, Z, [(6.6 * math.cos(ar), 6.6 * math.sin(ar), zt - 2.0 + 6.6 * math.sin(math.radians(12)) * math.sin(ar))],
              r=0.5, pid=CORE)
    core(part, 0, 0, pz, 2.6)
    small_port(part, X, Y, Z, pz)
    return part, pz


def s5_ruin(X, Y, Z):
    part, pz, zt = shrine(X, Y, Z, 115, broken=True)
    rng = np.random.default_rng(115)
    for _ in range(9):                                                     # rubble with light in the cracks
        a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(5.8, 7.0)
        studs(part, X, Y, Z, [(rr * math.cos(a), rr * math.sin(a), 0.4)], r=rng.uniform(0.4, 0.8), pid=BRONZE)
    core(part, 0, 0, pz, 3.0)
    small_port(part, X, Y, Z, pz)
    return part, pz


def s6_two_storey(X, Y, Z):
    part, pz, zt = shrine(X, Y, Z, 116, storeys=2)
    for sx in (-1, 1):                                                     # little lanterns hang off the first floor's corners
        for sy in (-1, 1):
            hx, hy, hz = sx * 6.0, sy * 6.0, 13.5
            part[(np.hypot(X - hx, Y - hy) <= 0.2) & (Z > hz) & (Z <= hz + 1.6)] = GOLD
            studs(part, X, Y, Z, [(hx, hy, hz - 0.3)], r=0.55, pid=CORE)
            part[(np.maximum(np.abs(X - hx), np.abs(Y - hy)) <= 0.6) & (np.abs(Z - (hz + 0.5)) <= 0.2)] = BRONZE
    core(part, 0, 0, pz - 1.0, 2.4)
    core(part, 0, 0, pz + 7.5, 1.8)
    small_port(part, X, Y, Z, pz - 1.0)
    return part, pz - 1.0


# ------------------------------------------------------------------ reliquary family
Z0R, Z1R = 4.0, 20.0


def amph_r(h):
    return 1.6 + 3.2 * math.exp(-((h - 0.38) / 0.24) ** 2) + 0.9 * math.exp(-((h - 0.97) / 0.06) ** 2)


def reliquary(X, Y, Z, seed, arms=True, sleeve=False, float_gap=0.0, foot=True, lid=True):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = Z0R + float_gap, Z1R + float_gap
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.6 + 3.2 * np.exp(-((H - 0.38) / 0.24) ** 2) + 0.9 * np.exp(-((H - 0.97) / 0.06) ** 2)
    sec = circle(X, Y, size)
    glass(part, X, Y, Z, sec, z0, z1, seed=seed, bulge_h=0.15, craze=2.6, lines=3)
    hollow(part, sec)
    for hh, eng in ((0.18, "dots"), (0.38, "zig"), (0.6, "dots"), (0.85, None)):   # gold filigree bands round the body
        zz = z0 + (z1 - z0) * hh
        band(part, X, Y, Z, circle(X, Y, amph_r(hh) + 0.45), zz - 0.35, zz + 0.35, GOLD, eng)
        part[(circle(X, Y, amph_r(hh) - 0.5) <= 0) & (np.abs(Z - zz) <= 0.35) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
    if foot:
        cf = lambda g: circle(X, Y, 1.6 + g)
        stepped(part, X, Y, Z, cf, Z0R, [(0.4, 0.5, GOLD, None), (1.4, 0.75, BRONZE, "dots"), (2.6, 0.75, BRONZE, None),
                                          (3.4, 0.5, GOLD_DK, None), (3.9, 0.75, BRONZE, "zig")], down=True)
        for k in range(8):
            a = k * math.pi / 4
            studs(part, X, Y, Z, [(5.3 * math.cos(a), 5.3 * math.sin(a), 0.5)], r=0.35, pid=GOLD)
    if arms:
        for sx in (-1, 1):
            pts = []
            for i in range(14):
                t = i / 13
                zz = 1.2 + (z1 - 2.5 - 1.2) * t
                hh = (zz - z0) / (z1 - z0)
                rr = amph_r(max(0.0, min(1.0, hh))) + 0.9 + 0.8 * math.sin(math.pi * t)
                pts.append((sx * rr, 0.0, zz))
            rod(part, X, Y, Z, pts, 0.55, BRONZE)
            for i in range(2, 13, 2):                                       # engraved knuckles along the arm
                studs(part, X, Y, Z, [pts[i]], r=0.65, pid=GOLD_DK)
            studs(part, X, Y, Z, [(sx * 2.2, 0.0, z1 - 2.4)], r=0.85, pid=GOLD)
    if sleeve:                                                             # bronze sleeve split in four, pulled apart, light seams
        for k in range(4):
            a = math.radians(45 + 90 * k)
            ox, oy = 0.8 * math.cos(a), 0.8 * math.sin(a)
            Xs, Ys = X - ox, Y - oy
            rr = np.hypot(Xs, Ys)
            hh = np.clip((Z - z0) / (z1 - z0), 0, 1)
            s_r = 1.6 + 3.2 * np.exp(-((hh - 0.38) / 0.24) ** 2) + 0.75
            angd = np.abs((np.arctan2(Ys, Xs) - a + math.pi) % (2 * math.pi) - math.pi)
            shell = (rr <= s_r + 0.35) & (rr > s_r) & (angd < math.pi / 4 - 0.15) & (Z > z0 + 2.0) & (Z <= z0 + (z1 - z0) * 0.66)
            part[shell] = BRONZE
            part[shell & (np.abs(angd - (math.pi / 4 - 0.2)) < 0.05)] = CORE
    zt = z1
    if lid:
        zt = stepped(part, X, Y, Z, lambda g: circle(X, Y, 2.4 + g), z1, [(0.3, 0.5, GOLD, "dots"), (-0.2, 0.75, GOLD, None),
                                                                          (-1.0, 0.5, GOLD_DK, None)])
        for sx in (-1, 1):
            pts = [(sx * 0.6, 0.0, zt), (sx * 1.6, 0.0, zt + 1.4), (sx * 2.0, 0.0, zt + 3.0), (sx * 1.6, 0.0, zt + 4.2)]
            rod(part, X, Y, Z, pts, 0.4, GOLD)
            studs(part, X, Y, Z, [pts[-1]], r=0.45, pid=CORE)
        studs(part, X, Y, Z, [(0, 0, zt + 0.6)], r=0.9, pid=GOLD)
    pz = z0 + (z1 - z0) * 0.38
    return part, pz, zt


def q1_detailed(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 121)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def q2_rooted(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 122, arms=False)
    roots(part, X, Y, Z, 5, 6.0, Z1R - 1.0, lambda z: amph_r(min(1.0, max(0.0, (z - Z0R) / (Z1R - Z0R)))) if z > Z0R else 2.0, seed=122)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def q3_crystal(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 123, lid=False)
    crystals(part, X, Y, Z, [(0.0, 0.0, Z1R - 0.5, 0, 0, 6.0, 1.3), (0.6, 0.4, Z1R, 28, 30, 3.5, 0.6),
                              (-0.6, 0.3, Z1R, 30, 160, 3.0, 0.6), (3.8, 1.5, 0.5, 45, 20, 3.5, 0.7),
                              (-3.6, 1.8, 0.5, 48, 160, 3.0, 0.6), (1.0, 3.9, 0.5, 40, 80, 2.8, 0.6)], seed=123)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def q4_floating(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 124, arms=False, float_gap=2.0)
    halo_rings(part, X, Y, Z, pz, [(6.0, 0.35, 0, 0, BRONZE), (6.8, 0.3, 60, 30, GOLD), (7.5, 0.3, -55, -40, BRONZE)])
    r = np.hypot(X, Y)
    part[(Z > 4.6) & (Z <= 5.1) & (r <= 2.4) & (r > 1.6)] = CORE            # light pooling under the floating body
    for sx in (-1, 1):                                                     # the hands hover by the neck
        studs(part, X, Y, Z, [(sx * 3.0, 0.0, Z1R + 2.0 - 2.4)], r=0.85, pid=GOLD)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def q5_split(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 125, arms=False, sleeve=True)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def q6_twin(X, Y, Z):
    """Two smaller amphorae on a bronze yoke, a balance; the port on the yoke's centre post."""
    part = np.zeros(X.shape, np.int8)
    for sx, seed in ((-1, 126), (1, 127)):
        cx = sx * 4.4
        z0, z1 = 7.0, 18.0
        H = np.clip((Z - z0) / (z1 - z0), 0, 1)
        size = 1.0 + 2.1 * np.exp(-((H - 0.4) / 0.25) ** 2) + 0.6 * np.exp(-((H - 0.96) / 0.06) ** 2)
        sec = np.hypot(X - cx, Y) - size
        glass(part, X - cx, Y, Z, sec, z0, z1, seed=seed, bulge_h=0.15, craze=2.6, lines=2)
        hollow(part, sec)
        band(part, X, Y, Z, np.hypot(X - cx, Y) - 3.4, z0 + 4.0, z0 + 4.6, GOLD, "zig")
        part[(np.hypot(X - cx, Y) <= 2.5) & (np.abs(Z - (z0 + 4.3)) <= 0.3) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
        band(part, X, Y, Z, np.hypot(X - cx, Y) - 1.6, z0 - 0.75, z0, GOLD_DK)
        band(part, X, Y, Z, np.hypot(X - cx, Y) - 1.5, z1, z1 + 0.6, GOLD)
        studs(part, X, Y, Z, [(cx, 0, z1 + 1.2)], r=0.6, pid=CORE)
        core(part, cx, 0, z0 + 4.4, 1.6)
        rod(part, X, Y, Z, [(cx, 0, z0 - 0.75), (cx, 0, z0 - 2.0)], 0.35, BRONZE)
    rod(part, X, Y, Z, [(-4.4, 0, 5.0), (0, 0, 6.0), (4.4, 0, 5.0)], 0.5, BRONZE)       # the yoke
    rod(part, X, Y, Z, [(0, 0, 0.8), (0, 0, 13.0)], 0.6, BRONZE)                         # centre post
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.4 + g), 1.6, [(0.6, 0.5, GOLD, None), (2.0, 0.75, BRONZE, "dots"),
                                                                 (3.0, 0.5, GOLD_DK, None)], down=True)
    studs(part, X, Y, Z, [(0, 0, 13.6)], r=0.9, pid=GOLD)
    ring_xz(part, X, Y, Z, 15.4, 1.0, 0.33, GOLD, axis="y")
    pz = 9.5
    part[(np.maximum(np.abs(X), np.abs(Z - pz)) <= 1.4) & (Y > -1.2) & (Y <= 0.2)] = BRONZE  # a plate for the port
    small_port(part, X, Y, Z, pz, pr=1.3)
    return coarsen_glass(part), pz


DESIGNS = {"S1": ("Shrine: detailed", s1_detailed), "S2": ("Shrine: overgrown", s2_overgrown),
           "S3": ("Shrine: crystal crown", s3_crystal), "S4": ("Shrine: halo rings", s4_halo),
           "S5": ("Shrine: ruin", s5_ruin), "S6": ("Shrine: two storeys", s6_two_storey),
           "Q1": ("Reliquary: detailed", q1_detailed), "Q2": ("Reliquary: rooted", q2_rooted),
           "Q3": ("Reliquary: crystal", q3_crystal), "Q4": ("Reliquary: floating", q4_floating),
           "Q5": ("Reliquary: split sleeve", q5_split), "Q6": ("Reliquary: twin balance", q6_twin)}


def build(code):
    X, Y, Z = grid()
    P10.STYLE["hue"] = None
    return DESIGNS[code][1](X, Y, Z)


quads = P7.quads
model_boxes = P7.model_boxes
