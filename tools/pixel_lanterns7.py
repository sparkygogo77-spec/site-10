"""Pass 607: J's three 606 lanterns made more complex, 3 takes each (siblings, built differently).

J: "make these more complex" (606 D1 Vault, D6 Armillary, D5 Crystal). Mood only from a comic reference he sent (layered
silhouettes, angular fins, a glowing bowl/core, molten drips, strong highlights): no shape, emblem or corps mark copied.
New on top of tools/pixel_lanterns6.py:
- hollow see-through glass (the shell only) with an inner CORE ball the G3 flare plays on (spinning noise, breathing);
- layered frames: outer fins/blades, buttresses, tiered roofs and bases, studs and rivets;
- gold drips running down from collars over the glass ("molten"), a glowing bowl crown on some takes;
- a sculpted port (fins either side, rivets) and knuckled/sculpted handles.
Budget per take: about 2,500 Blockbench boxes (box_count), as the jar's models.
"""
import math
import numpy as np
from pixel_lanterns6 import (G, XS, ZS, grid, circle, ngon, glass, band, stepped, port, rod, ring_xz,
                             EMPTY, SMOKE, RIB, PLATE, GOLD, GOLD_DK, GOLD_ENG, SILVER, VEIN, HOLE, SOCKET)
import pixel_lanterns6 as P6

CORE = 11
P6.PAL[CORE] = (90, 255, 120)
P6.KIND[CORE] = 6


def hollow(part, d, keep=1):
    """Keep only the glass's outer skin (keep voxels thick) so the core shows through."""
    part[(part == SMOKE) & (d < -G * keep)] = EMPTY


def core(part, cx, cy, cz, r):
    X, Y, Z = grid()
    part[(np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2) <= r) & (part == EMPTY)] = CORE


def fin(part, X, Y, Z, inner, outer, th=0.3, n=14, pid=GOLD):
    """A flat angular blade between two polylines (inner edge, outer edge), sampled n times."""
    def at(poly, t):
        k = min(int(t * (len(poly) - 1)), len(poly) - 2)
        u = t * (len(poly) - 1) - k
        a, b = np.array(poly[k], float), np.array(poly[k + 1], float)
        return tuple(a + (b - a) * u)
    span = sum(np.linalg.norm(np.subtract(p, q)) for p, q in zip(inner, inner[1:]))
    n = max(n, int(span / (G * 0.8)))                # strips closer than a voxel: a solid blade, not a comb
    for i in range(n + 1):
        t = i / n
        rod(part, X, Y, Z, [at(inner, t), at(outer, t)], th, pid)


def drips(part, X, Y, Z, d, ztop, n, seed, zmin, avoid_front=True):
    """Gold drips from a collar down the glass skin: a stream a pixel wide ending in a bead."""
    rng = np.random.default_rng(seed)
    skin = (d > 0) & (d <= G * 1.5)
    ang = np.degrees(np.arctan2(Y, X))
    for _ in range(n):
        a = rng.uniform(-180, 180)
        if avoid_front and abs(((a + 90) + 180) % 360 - 180) < 35:
            continue
        length = rng.uniform(1.5, ztop - zmin)
        zb = ztop - length
        da = np.abs((ang - a + 180) % 360 - 180) * np.pi / 180 * np.maximum(np.hypot(X, Y), 1)
        stream = skin & (da < G * 0.6) & (Z <= ztop) & (Z > zb)
        part[stream & ((part == EMPTY) | (part == RIB) | (part == PLATE) | (part == VEIN))] = GOLD
        bead = skin & (da < G * 1.1) & (Z <= zb + 0.5) & (Z > zb - 0.25)
        part[bead] = GOLD


def bowl(part, X, Y, Z, cz, r, pid=GOLD):
    """An open gold bowl (a hemispherical shell, rim at cz) with a pool of core light inside."""
    q = np.sqrt(X ** 2 + Y ** 2 + (Z - cz) ** 2)
    part[(q <= r) & (q > r - 0.5) & (Z <= cz)] = pid
    part[(q <= r) & (q > r - 0.75) & (np.abs(Z - cz) <= 0.25)] = GOLD_DK                 # rim lip
    part[(q <= r - 0.5) & (Z <= cz - r * 0.45)] = CORE


def studs(part, X, Y, Z, pts, r=0.4, pid=GOLD):
    for p in pts:
        part[np.sqrt((X - p[0]) ** 2 + (Y - p[1]) ** 2 + (Z - p[2]) ** 2) <= r] = pid


def knuckled_arch(part, X, Y, Z, zbase, w, h, n_knuckle=7, r=0.33, y=0.0):
    pts = [(w * math.cos(math.pi * k / 20), y, zbase + h * math.sin(math.pi * k / 20)) for k in range(21)]
    rod(part, X, Y, Z, pts, r)
    for k in range(1, n_knuckle + 1):
        a = math.pi * k / (n_knuckle + 1)
        studs(part, X, Y, Z, [(w * math.cos(a), y, zbase + h * math.sin(a))], r=r + 0.25, pid=GOLD_DK)


def sculpted_port(part, X, Y, Z, pz, pr=2.4):
    fy = port(part, X, Y, Z, pz, pr)
    for sx in (-1, 1):                                                         # swept fins either side of the port
        fin(part, X, Y, Z, [(sx * pr * 0.9, fy - 0.6, pz + 1.2), (sx * pr * 0.9, fy - 0.6, pz - 1.2)],
            [(sx * (pr + 1.6), fy + 0.2, pz + 2.2), (sx * (pr + 1.0), fy + 0.2, pz - 1.6)], th=0.28, n=10)
    studs(part, X, Y, Z, [(0, fy - 1.0, pz + pr + 0.35), (0, fy - 1.0, pz - pr - 0.35)], r=0.4, pid=SILVER)
    return fy


# ------------------------------------------------------------------ Vault (606 D1) x3
def _vault_body(X, Y, Z, s=4.6, z0=5.0, z1=21.0, seed=71):
    part = np.zeros(X.shape, np.int8)
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = s * (1 - 0.1 * np.sin(np.pi * H) ** 1.5) + 0.35 * np.exp(-((H - 0.5) / 0.12) ** 2)
    sec = ngon(X, Y, 4, size, rnd=1.4)
    glass(part, X, Y, Z, sec, z0, z1, seed=seed, craze=2.6, lines=4)
    hollow(part, sec)
    sq = lambda g: ngon(X, Y, 4, s + g, rnd=1.4)
    return part, sec, sq, z0, z1


def _pillars(part, X, Y, Z, c, z0, z1, r=0.9):
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = np.hypot(X - sx * c, Y - sy * c)
            pil = (q <= r) & (Z > z0 - 0.5) & (Z <= z1 + 0.5)
            part[pil] = GOLD
            ang = np.arctan2(Y - sy * c, X - sx * c)
            part[pil & (q > r - 0.3) & (np.round(ang / (math.pi / 4)) % 2 == 0)] = GOLD_DK
            for zc in (z0 + 0.6, z1 - 0.6, (z0 + z1) / 2):
                part[(q <= r + 0.25) & (np.abs(Z - zc) <= 0.3)] = GOLD


def v1_cathedral(X, Y, Z):
    """Two-tier roof with corner finials, angular blades sweeping up from each corner, core inside."""
    part, sec, sq, z0, z1 = _vault_body(X, Y, Z)
    stepped(part, X, Y, Z, sq, z0, [(1.0, 0.5, GOLD_DK, None), (1.6, 0.75, GOLD, "dots"), (2.2, 0.5, GOLD, None),
                                     (1.6, 0.5, GOLD_DK, None), (2.6, 0.75, GOLD, "line")], down=True)
    zt = stepped(part, X, Y, Z, sq, z1, [(1.0, 0.5, GOLD_DK, None), (1.8, 0.75, GOLD, "zig"), (2.3, 0.5, GOLD, None)])
    for k, (g, h) in enumerate(((1.8, 0.5), (1.0, 0.5), (0.2, 0.75), (0.6, 0.5), (-0.4, 0.5), (-1.4, 0.75),
                                (-2.3, 0.5), (-3.0, 0.5))):
        band(part, X, Y, Z, sq(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK, "dots" if k == 3 else None)
        zt += h
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.5) & (np.hypot(r, (Z - zt - 0.75) * 1.1) <= 1.0)] = GOLD
    part[(Z > zt + 1.5) & (Z <= zt + 3.0) & (r <= 0.3)] = SILVER
    ring_xz(part, X, Y, Z, zt + 3.9, 1.0, 0.3, GOLD, axis="y")
    c = 4.6 * 0.83
    _pillars(part, X, Y, Z, c, z0, z1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            studs(part, X, Y, Z, [(sx * (c + 0.9), sy * (c + 0.9), z1 + 2.2)], r=0.5)            # corner finials
            part[(np.hypot(X - sx * (c + 0.9), Y - sy * (c + 0.9)) <= 0.25) & (Z > z1 + 2.2) & (Z <= z1 + 3.4)] = GOLD
            ox, oy = sx * (c + 0.5), sy * (c + 0.5)                                        # blades sweeping up and out
            fin(part, X, Y, Z, [(ox, oy, z0 + 2.0), (ox, oy, z0 + 8.0)],
                [(ox + sx * 1.6, oy + sy * 1.6, z0 + 0.8), (ox + sx * 0.9, oy + sy * 0.9, z0 + 9.5)], th=0.26, n=12)
    core(part, 0, 0, (z0 + z1) / 2, 2.8)
    pz = (z0 + z1) / 2
    sculpted_port(part, X, Y, Z, pz)
    return part, pz


def v2_molten(X, Y, Z):
    """606 D1 with gold drips running from the roof down the panels, a knuckled handle, core inside."""
    part, sec, sq, z0, z1 = _vault_body(X, Y, Z, seed=72)
    stepped(part, X, Y, Z, sq, z0, [(1.0, 0.5, GOLD_DK, None), (1.5, 0.75, GOLD, "zig"), (1.9, 0.5, GOLD, None),
                                     (1.4, 0.75, GOLD_DK, None), (2.2, 0.75, GOLD, "line")], down=True)
    zt = stepped(part, X, Y, Z, sq, z1, [(1.0, 0.5, GOLD_DK, None), (1.6, 0.75, GOLD, "dots"), (1.9, 0.5, GOLD, None)])
    zr = zt
    for k, (g, h) in enumerate(((1.6, 0.75), (0.9, 0.75), (0.2, 0.75), (-0.6, 0.75), (-1.5, 0.75))):
        band(part, X, Y, Z, sq(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK, "line" if k == 1 else None)
        zt += h
    c = 4.6 * 0.83
    _pillars(part, X, Y, Z, c, z0, z1)
    drips(part, X, Y, Z, sec, z1 - 0.1, 16, seed=720, zmin=z0 + 2.0)
    for sx in (-1, 1):                                                                       # drips off the roof edge
        for x in np.linspace(-3.5, 3.5, 4):
            part[(np.abs(X - x) <= 0.25) & (np.abs(Y - sx * 6.3) <= 0.25) & (Z > zr - 1.6) & (Z <= zr + 0.5)] = GOLD
            studs(part, X, Y, Z, [(x, sx * 6.3, zr - 1.7)], r=0.35)
    knuckled_arch(part, X, Y, Z, zt - 0.5, 2.8, 3.6)
    core(part, 0, 0, (z0 + z1) / 2, 2.8)
    pz = (z0 + z1) / 2
    sculpted_port(part, X, Y, Z, pz)
    return part, pz


def v3_bastion(X, Y, Z):
    """Wider stepped base with buttress fins on the four sides, panels split by cross mullions, a glowing bowl crown."""
    part, sec, sq, z0, z1 = _vault_body(X, Y, Z, seed=73, z0=5.5, z1=19.5)
    zb = stepped(part, X, Y, Z, sq, z0, [(1.0, 0.5, GOLD_DK, None), (1.8, 0.75, GOLD, "dots"), (2.6, 0.5, GOLD, None),
                                          (3.0, 0.75, GOLD_DK, None), (3.4, 0.75, GOLD, "zig")], down=True)
    zt = stepped(part, X, Y, Z, sq, z1, [(1.0, 0.5, GOLD_DK, None), (1.8, 0.75, GOLD, "line"), (2.4, 0.5, GOLD, None),
                                          (1.2, 0.5, GOLD_DK, None)])
    ang = np.arctan2(Y, X)
    for k in range(4):                                                     # cross mullions on each panel
        a = -math.pi / 2 + k * math.pi / 2
        da = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) * np.hypot(X, Y)
        part[(da <= 0.35) & (sec > -G) & (sec <= 0.6) & (Z > z0) & (Z <= z1) & (np.abs(Z - (z0 + z1) / 2) > 2.4)] = GOLD
    part[(np.abs(Z - (z0 + z1) / 2) <= 0.3) & (sec > -G) & (sec <= 0.6)] = GOLD
    c = 4.6 * 0.83
    _pillars(part, X, Y, Z, c, z0, z1, r=1.0)
    for k in range(4):                                                     # buttress fins on the four sides
        a = k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        if abs(uy + 1) < 1e-6:
            continue                                                       # keep the front (port) clear
        fin(part, X, Y, Z, [(ux * 5.0, uy * 5.0, zb + 0.5), (ux * 5.0, uy * 5.0, z0 + 6.0)],
            [(ux * 7.6, uy * 7.6, zb + 0.5), (ux * 5.4, uy * 5.4, z0 + 6.5)], th=0.3, n=12)
    bowl(part, X, Y, Z, zt + 2.6, 2.8)
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 0.5) & (r <= 1.0)] = GOLD_DK
    for k in range(3):                                                     # three struts carry the bowl's handle
        a = -math.pi / 2 + k * 2 * math.pi / 3 + math.pi / 3
        rod(part, X, Y, Z, [(2.6 * math.cos(a), 2.6 * math.sin(a), zt + 2.6), (0, 0, zt + 6.0)], 0.28)
    ring_xz(part, X, Y, Z, zt + 6.9, 0.9, 0.3, GOLD, axis="y")
    core(part, 0, 0, (z0 + z1) / 2, 2.8)
    pz = (z0 + z1) / 2
    sculpted_port(part, X, Y, Z, pz)
    return part, pz


# ------------------------------------------------------------------ Armillary (606 D6) x3
CZ, RS = 14.0, 5.6


def _globe(X, Y, Z, seed):
    part = np.zeros(X.shape, np.int8)
    sec = np.hypot(np.hypot(X, Y), Z - CZ) - RS
    glass(part, X, Y, Z, sec, CZ - RS, CZ + RS, seed=seed, bulge_h=0.17, craze=2.6, lines=3)
    hollow(part, sec)
    return part, sec


def _pedestal(part, X, Y, Z, top, steps):
    pd = lambda g: circle(X, Y, 1.4 + g)
    band(part, X, Y, Z, pd(0.0), 2.5, top, GOLD)
    for zc in np.linspace(3.5, top - 0.6, 3):
        band(part, X, Y, Z, pd(0.45), zc - 0.3, zc + 0.3, GOLD_DK)
    stepped(part, X, Y, Z, pd, 2.5, steps, down=True)
    return pd


def a1_orrery(X, Y, Z):
    """Four rings (a fourth tilted 30 degrees), studs where rings cross, a finned pedestal, core inside."""
    part, sec = _globe(X, Y, Z, 74)
    R = RS + 1.3
    ring_xz(part, X, Y, Z, CZ, R, 0.45, GOLD, axis="z")
    ring_xz(part, X, Y, Z, CZ, R, 0.4, GOLD, axis="y", turn=45)
    ring_xz(part, X, Y, Z, CZ, R, 0.4, GOLD, axis="y", turn=-45)
    a = math.radians(30)                                                    # tilted outer ring
    Xr, Zr = X * math.cos(a) - (Z - CZ) * math.sin(a), X * math.sin(a) + (Z - CZ) * math.cos(a)
    part[np.hypot(np.hypot(Xr, Y) - (R + 1.1), Zr) <= 0.35] = GOLD_DK
    for t in (45, 135, 225, 315):                                           # studs on the equator crossings
        studs(part, X, Y, Z, [(R * math.cos(math.radians(t)), R * math.sin(math.radians(t)), CZ)], r=0.7)
    studs(part, X, Y, Z, [(0, 0, CZ - R), (0, 0, CZ + R)], r=0.9, pid=GOLD_DK)
    pd = _pedestal(part, X, Y, Z, CZ - R - 0.3, [(1.2, 0.5, GOLD_DK, None), (2.4, 0.75, GOLD, "zig"),
                                                 (3.2, 0.5, GOLD, None), (3.8, 0.75, GOLD_DK, None), (4.4, 0.5, GOLD, "dots")])
    for k in range(4):                                                      # pedestal fins
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        fin(part, X, Y, Z, [(ux * 1.5, uy * 1.5, 2.6), (ux * 1.5, uy * 1.5, 6.5)],
            [(ux * 4.2, uy * 4.2, 2.6), (ux * 1.9, uy * 1.9, 7.2)], th=0.28, n=10)
    r = np.hypot(X, Y)
    zt = CZ + R + 0.8
    part[(Z > zt) & (Z <= zt + 1.0) & (r <= 0.45)] = SILVER
    ring_xz(part, X, Y, Z, zt + 2.0, 1.1, 0.33, GOLD, axis="y")
    core(part, 0, 0, CZ, 2.8)
    sculpted_port(part, X, Y, Z, CZ, pr=2.3)
    return part, CZ


def a2_cradle(X, Y, Z):
    """The globe held by four angular blade arms rising from the pedestal, an equator band, core inside."""
    part, sec = _globe(X, Y, Z, 75)
    R = RS + 1.0
    ring_xz(part, X, Y, Z, CZ, R, 0.5, GOLD, axis="z")
    band(part, X, Y, Z, np.hypot(X, Y) - (R + 0.2), CZ - 0.6, CZ + 0.6, GOLD, "zig")
    part[(np.hypot(X, Y) < R - 0.4) & (np.abs(Z - CZ) <= 0.6) & (part == GOLD)] = EMPTY
    for k in range(4):                                                      # four angular arms, a kink at the waist
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        inner = [(ux * 1.6, uy * 1.6, 6.0), (ux * (R - 0.2), uy * (R - 0.2), CZ - 2.0), (ux * (R - 0.6), uy * (R - 0.6), CZ + 3.5)]
        outer = [(ux * 2.6, uy * 2.6, 5.4), (ux * (R + 1.6), uy * (R + 1.6), CZ - 2.6), (ux * (R + 0.9), uy * (R + 0.9), CZ + 4.6)]
        fin(part, X, Y, Z, inner, outer, th=0.3, n=18)
        studs(part, X, Y, Z, [(ux * (R + 1.2), uy * (R + 1.2), CZ + 4.4)], r=0.55, pid=GOLD_DK)
    _pedestal(part, X, Y, Z, 6.2, [(1.4, 0.5, GOLD_DK, None), (2.6, 0.75, GOLD, "dots"), (3.4, 0.5, GOLD, None),
                                    (4.0, 0.75, GOLD_DK, None), (4.6, 0.5, GOLD, "line")])
    r = np.hypot(X, Y)
    zt = CZ + RS
    band(part, X, Y, Z, circle(X, Y, 1.6), zt - 0.4, zt + 0.4, GOLD_DK)
    part[(Z > zt + 0.4) & (Z <= zt + 1.4) & (r <= 0.45)] = SILVER
    knuckled_arch(part, X, Y, Z, zt + 1.2, 2.0, 2.6, n_knuckle=5, r=0.3)
    core(part, 0, 0, CZ, 2.8)
    sculpted_port(part, X, Y, Z, CZ, pr=2.3)
    return part, CZ


def a3_molten(X, Y, Z):
    """606 D6's rings, gold drips running down the glass from a crown that is a glowing bowl, core inside."""
    part, sec = _globe(X, Y, Z, 76)
    R = RS + 1.3
    ring_xz(part, X, Y, Z, CZ, R, 0.45, GOLD, axis="z")
    ring_xz(part, X, Y, Z, CZ, R, 0.4, GOLD, axis="y", turn=45)
    ring_xz(part, X, Y, Z, CZ, R, 0.4, GOLD, axis="y", turn=-45)
    zt = CZ + RS - 0.6
    band(part, X, Y, Z, circle(X, Y, 2.6), zt - 0.2, zt + 0.5, GOLD, "dots")
    drips(part, X, Y, Z, sec, zt, 18, seed=760, zmin=CZ - RS + 1.0)
    bowl(part, X, Y, Z, zt + 3.2, 2.6)
    part[(Z > zt + 0.5) & (Z <= zt + 0.9) & (np.hypot(X, Y) <= 1.2)] = GOLD_DK
    for k in range(3):
        a = -math.pi / 2 + k * 2 * math.pi / 3 + math.pi / 3
        rod(part, X, Y, Z, [(1.0 * math.cos(a), 1.0 * math.sin(a), zt + 0.8), (2.2 * math.cos(a), 2.2 * math.sin(a), zt + 1.6)], 0.3)
    _pedestal(part, X, Y, Z, CZ - R - 0.3, [(1.2, 0.5, GOLD_DK, None), (2.4, 0.75, GOLD, "zig"), (3.2, 0.5, GOLD, None),
                                             (3.8, 0.75, GOLD_DK, None), (4.4, 0.5, GOLD, "dots")])
    studs(part, X, Y, Z, [(0, 0, CZ - R)], r=0.9, pid=GOLD_DK)
    for k in range(8):                                                      # drips off the pedestal's top step too
        a = k * math.pi / 4 + 0.2
        studs(part, X, Y, Z, [(3.6 * math.cos(a), 3.6 * math.sin(a), 1.0)], r=0.3)
    core(part, 0, 0, CZ, 2.8)
    sculpted_port(part, X, Y, Z, CZ, pr=2.3)
    return part, CZ


# ------------------------------------------------------------------ Crystal / egg (606 D5) x3
Z0C, Z1C = 4.0, 23.0


def _egg(X, Y, Z, seed, n=8):
    part = np.zeros(X.shape, np.int8)
    H = np.clip((Z - Z0C) / (Z1C - Z0C), 0, 1)
    size = 1.0 + 4.6 * np.maximum(0, 1 - np.abs(2 * H - 1.08)) ** 0.55
    sec = ngon(X, Y, n, size)
    glass(part, X, Y, Z, sec, Z0C, Z1C, seed=seed, bulge_h=0.2, craze=2.6, lines=3)
    hollow(part, sec)
    return part, sec, size


def _egg_r(h):
    return 1.0 + 4.6 * max(0.0, 1 - abs(2 * h - 1.08)) ** 0.55


def _ribs(part, X, Y, Z, n, off=0.0, r=0.42, pid=GOLD, z_lo=0.05, z_hi=0.95):
    for k in range(n):
        a = -math.pi / 2 + math.pi / n + k * 2 * math.pi / n + off
        pts = []
        for i in range(17):
            h = z_lo + (z_hi - z_lo) * i / 16
            rr = _egg_r(h) / math.cos(math.pi / 8) + 0.3
            pts.append((rr * math.cos(a), rr * math.sin(a), Z0C + (Z1C - Z0C) * h))
        rod(part, X, Y, Z, pts, r, pid)
        yield a, pts


def _oct_base(part, X, Y, Z, z, extra=0.0):
    ob = lambda g: ngon(X, Y, 8, 2.6 + g)
    return stepped(part, X, Y, Z, ob, z, [(0.0, 0.75, GOLD, "dots"), (0.8, 0.5, GOLD_DK, None), (1.8 + extra, 0.75, GOLD, None),
                                          (2.6 + extra, 0.5, GOLD_DK, None), (3.4 + extra, 0.75, GOLD, "line"),
                                          (3.8 + extra, 0.5, GOLD, None)], down=True)


def c1_faberge(X, Y, Z):
    """Eight ribs with gem studs where the engraved bands cross them, a tiered octagon base, core inside."""
    part, sec, size = _egg(X, Y, Z, 77)
    for a, pts in _ribs(part, X, Y, Z, 8):
        for h in (0.3, 0.7):
            p = pts[int(round((h - 0.05) / 0.9 * 16))]
            studs(part, X, Y, Z, [p], r=0.65, pid=GOLD_DK)
            studs(part, X, Y, Z, [(p[0] * 1.06, p[1] * 1.06, p[2])], r=0.35, pid=SILVER)
    for h, eng in ((0.3, "zig"), (0.7, "dots")):                              # engraved bands round the egg
        z = Z0C + (Z1C - Z0C) * h
        band(part, X, Y, Z, ngon(X, Y, 8, _egg_r(h) + 0.55), z - 0.4, z + 0.4, GOLD, eng)
        part[(ngon(X, Y, 8, _egg_r(h) - 0.6) <= 0) & (np.abs(Z - z) <= 0.4) & (part == GOLD)] = EMPTY
    _oct_base(part, X, Y, Z, Z0C + 1.5)
    zt = stepped(part, X, Y, Z, lambda g: ngon(X, Y, 8, 1.6 + g), Z1C - 1.2, [(0.3, 0.5, GOLD, "dots"), (0.0, 0.5, GOLD_DK, None),
                                                                             (-0.6, 0.5, GOLD, None)])
    part[(Z > zt) & (Z <= zt + 1.2) & (np.hypot(X, Y) <= 0.6)] = GOLD_DK
    ring_xz(part, X, Y, Z, zt + 2.4, 1.3, 0.35, GOLD, axis="y")
    core(part, 0, 0, Z0C + (Z1C - Z0C) * 0.48, 2.8)
    pz = Z0C + (Z1C - Z0C) * 0.5
    sculpted_port(part, X, Y, Z, pz, pr=2.2)
    return part, pz


def c2_winged(X, Y, Z):
    """Angular blades sweep from the base up the egg's sides like folded wings, four ribs, core inside."""
    part, sec, size = _egg(X, Y, Z, 78)
    list(_ribs(part, X, Y, Z, 4, off=math.pi / 8))
    zb = _oct_base(part, X, Y, Z, Z0C + 1.5, extra=0.4)
    for k in range(4):                                                       # wings, kinked, sweeping up and out
        a = math.pi / 4 + k * math.pi / 2
        if abs(math.sin(a) + 1) < 0.3:
            continue
        ux, uy = math.cos(a), math.sin(a)
        inner = [(ux * 3.4, uy * 3.4, Z0C + 1.0), (ux * 5.6, uy * 5.6, Z0C + 7.0), (ux * 5.2, uy * 5.2, Z0C + 14.0)]
        outer = [(ux * 5.6, uy * 5.6, Z0C + 0.2), (ux * 8.0, uy * 8.0, Z0C + 6.0), (ux * 7.0, uy * 7.0, Z0C + 15.5)]
        fin(part, X, Y, Z, inner, outer, th=0.3, n=20)
        studs(part, X, Y, Z, [(ux * 6.9, uy * 6.9, Z0C + 6.2)], r=0.55, pid=GOLD_DK)
    for sx in (-1, 1):                                                       # the front pair stays low, framing the port
        fin(part, X, Y, Z, [(sx * 3.0, -2.6, Z0C + 1.0), (sx * 4.4, -3.6, Z0C + 5.0)],
            [(sx * 4.6, -4.0, Z0C + 0.4), (sx * 6.0, -4.6, Z0C + 4.4)], th=0.28, n=10)
    zt = stepped(part, X, Y, Z, lambda g: ngon(X, Y, 8, 1.6 + g), Z1C - 1.2, [(0.4, 0.5, GOLD, "zig"), (0.0, 0.5, GOLD_DK, None),
                                                                             (-0.6, 0.5, GOLD, None)])
    part[(Z > zt) & (Z <= zt + 1.2) & (np.hypot(X, Y) <= 0.6)] = GOLD_DK
    knuckled_arch(part, X, Y, Z, zt + 0.8, 1.6, 2.4, n_knuckle=4, r=0.3)
    core(part, 0, 0, Z0C + (Z1C - Z0C) * 0.48, 2.8)
    pz = Z0C + (Z1C - Z0C) * 0.5
    sculpted_port(part, X, Y, Z, pz, pr=2.2)
    return part, pz


def c3_molten(X, Y, Z):
    """606 D5's claws and ribs with gold drips from the top cup, a glowing bowl crown, core inside."""
    part, sec, size = _egg(X, Y, Z, 79)
    list(_ribs(part, X, Y, Z, 8, z_lo=0.08, z_hi=0.35))
    list(_ribs(part, X, Y, Z, 8, z_lo=0.65, z_hi=0.92))
    zc = Z1C - 2.0
    stepped(part, X, Y, Z, lambda g: ngon(X, Y, 8, 2.4 + g), zc, [(0.0, 0.75, GOLD, "dots"), (0.6, 0.5, GOLD_DK, None)])
    drips(part, X, Y, Z, sec, zc, 14, seed=790, zmin=Z0C + 4.0)
    _oct_base(part, X, Y, Z, Z0C + 1.5)
    bowl(part, X, Y, Z, zc + 3.6, 2.4)
    part[(Z > zc + 1.25) & (Z <= zc + 1.6) & (np.hypot(X, Y) <= 1.0)] = GOLD_DK
    core(part, 0, 0, Z0C + (Z1C - Z0C) * 0.48, 2.8)
    pz = Z0C + (Z1C - Z0C) * 0.5
    sculpted_port(part, X, Y, Z, pz, pr=2.2)
    return part, pz


DESIGNS = {"D1a": ("Vault: cathedral", v1_cathedral), "D1b": ("Vault: molten", v2_molten), "D1c": ("Vault: bastion", v3_bastion),
           "D6a": ("Armillary: orrery", a1_orrery), "D6b": ("Armillary: cradle", a2_cradle), "D6c": ("Armillary: molten", a3_molten),
           "D5a": ("Crystal: faberge", c1_faberge), "D5b": ("Crystal: winged", c2_winged), "D5c": ("Crystal: molten", c3_molten)}


def build(code):
    X, Y, Z = grid()
    part, pz = DESIGNS[code][1](X, Y, Z)
    if code[:2] in ("D5", "D6"):                      # curved glass on a half-pixel grid keeps them under ~2,500 boxes
        part = coarsen_glass(part)
    return part, pz


def model_boxes(part):
    """Boxes for a Blockbench export with per-texel painted faces: every occupied voxel merges, whatever its part."""
    return P6.box_count((part > 0).astype(np.int8))


def quads(part, pz):
    q, c, k, w = P6.quads(part, pz)
    # the core glows full (its flare comes from the material)
    w = np.where(k == 6, 1.0, w).astype(np.float32)
    return q, c, k, w


box_count = P6.box_count


def coarsen_glass(part):
    """Glass on a half-pixel grid (2x2x2 voxels), gold stays at a quarter pixel: a curved quarter-pixel shell splits
    into thousands of boxes. A block becomes glass (its most common glass part) when it holds glass and no gold."""
    GL = np.array([SMOKE, RIB, PLATE, VEIN])
    S = (np.array(part.shape) // 2) * 2
    p = part[:S[0], :S[1], :S[2]]
    b = p.reshape(S[0] // 2, 2, S[1] // 2, 2, S[2] // 2, 2).transpose(0, 2, 4, 1, 3, 5).reshape(S[0] // 2, S[1] // 2, S[2] // 2, 8)
    isg = np.isin(b, GL)
    opaque = (b > 0) & ~isg
    has = isg.any(-1) & ~opaque.any(-1)
    counts = np.stack([(b == g).sum(-1) for g in GL], -1)
    pick = GL[counts.argmax(-1)]
    vein = (b == VEIN).any(-1)
    pick = np.where(vein & (counts[..., 3] >= 2), VEIN, pick)
    newb = np.where(has[..., None], pick[..., None], np.where(isg, 0, b))
    out = part.copy()
    out[:S[0], :S[1], :S[2]] = newb.reshape(S[0] // 2, S[1] // 2, S[2] // 2, 2, 2, 2).transpose(0, 3, 1, 4, 2, 5).reshape(S)
    return out
