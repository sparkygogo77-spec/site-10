"""Pass v2.0105 voxels: fresh lanterns, 12 new designs in green (PC chat, 2026-10-19).

J dropped all 12 of v2.0103 ("Didnt like all 12") and asked for "New stuff", then picked "Fresh lantern designs": a
round of new silhouettes that are not reliquaries, still voxel pixel art with polished gold (606-612 rules: complex,
layered, a see-through glass with the G3-flare core, the lit port kept at the v2.0102 size).
  F1 classic battery    F2 pagoda             F3 storm lantern      F4 faceted gem
  F5 crescent moon      F6 obelisk            F7 hanging bell       F8 pierced star lamp
  F9 chalice            F10 clockwork         F11 lighthouse        F12 seed pod
"""
import math
import numpy as np
import pixel_lanterns6 as P6
from pixel_lanterns6 import G, grid, circle, ngon, glass, band, stepped, rod, ring_xz, EMPTY, GOLD, GOLD_DK, GOLD_ENG, SILVER
from pixel_lanterns7 import hollow, core, studs, coarsen_glass, fin, CORE
import pixel_lanterns10 as P10
from pixel_lanterns10 import BRONZE, tilted_ring, sphere_glass
import pixel_lanterns13 as P13
import pixel_lanterns14 as P14                          # the 2.25x lit port, raised, hot ring

STYLE = P13.STYLE
_w = P13._with_port


def _body(part, X, Y, Z, sec, z0, z1, seed, lines=3):
    glass(part, X, Y, Z, sec, z0, z1, seed=seed, bulge_h=0.15, craze=2.6, lines=lines)
    hollow(part, sec)


def _base(part, X, Y, Z, z, r0=1.6, wide=3.6):
    """A stepped gold and bronze foot under z, with studs round the bottom."""
    stepped(part, X, Y, Z, lambda g: circle(X, Y, r0 + g), z,
            [(0.4, 0.5, GOLD, None), (wide * 0.45, 0.75, BRONZE, "dots"), (wide * 0.8, 0.5, GOLD_DK, None), (wide, 0.75, BRONZE, "zig")],
            down=True)


def _half_ring(part, X, Y, Z, cz, R, r, pid=GOLD, upper=True):
    tmp = np.zeros(X.shape, np.int8)
    ring_xz(tmp, X, Y, Z, cz, R, r, pid, axis="y", turn=90)       # upright, in the YZ plane: a bail over the top
    keep = (tmp > 0) & ((Z >= cz) if upper else (Z <= cz))
    part[keep] = tmp[keep]


# ------------------------------------------------------------------ F1 classic battery lantern
def f1_classic(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 5.0, 18.0
    _body(part, X, Y, Z, ngon(X, Y, 8, 3.4, rnd=0.6, turn=22.5), z0, z1, 1601)
    _base(part, X, Y, Z, z0, r0=2.6, wide=2.2)
    for k in range(8):                                   # gold bars over the glass
        a = math.radians(22.5 + 45 * k)
        if abs(math.degrees(a) - 270) < 30:
            continue
        rod(part, X, Y, Z, [(3.7 * math.cos(a), 3.7 * math.sin(a), z0), (3.7 * math.cos(a), 3.7 * math.sin(a), z1)], 0.3, GOLD)
    for zz, eng in ((z0 + 0.4, "dots"), ((z0 + z1) / 2, "zig"), (z1 - 0.4, "dots")):
        band(part, X, Y, Z, circle(X, Y, 3.95), zz - 0.35, zz + 0.35, GOLD, eng)
        part[(circle(X, Y, 3.3) <= 0) & (np.abs(Z - zz) <= 0.35) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
    zt = stepped(part, X, Y, Z, lambda g: circle(X, Y, 2.6 + g), z1, [(1.4, 0.5, GOLD, "dots"), (0.8, 0.75, BRONZE, None),
                                                                      (0.0, 0.5, GOLD_DK, None), (-0.8, 0.75, GOLD, "zig")])
    for k in range(6):                                   # vent slots round the cap
        a = math.radians(30 + 60 * k)
        studs(part, X, Y, Z, [(2.3 * math.cos(a), 2.3 * math.sin(a), zt - 1.0)], r=0.35, pid=CORE)
    _half_ring(part, X, Y, Z, zt, 2.6, 0.38)
    studs(part, X, Y, Z, [(0, 0, zt + 2.7)], r=0.6, pid=GOLD_DK)
    pz = (z0 + z1) / 2
    core(part, 0, 0, pz, 2.6)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F2 pagoda
def f2_pagoda(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    _base(part, X, Y, Z, 3.0, r0=2.4, wide=2.6)
    z = 3.0
    for k, (s, h) in enumerate(((3.0, 6.0), (2.4, 4.0), (1.8, 3.0))):     # three glass storeys, shrinking
        _body(part, X, Y, Z, ngon(X, Y, 4, s, rnd=0.3, turn=45), z, z + h, 1602 + k, lines=2)
        for sx in (-1, 1):
            for sy in (-1, 1):
                rod(part, X, Y, Z, [(sx * s * 0.72, sy * s * 0.72, z), (sx * s * 0.72, sy * s * 0.72, z + h)], 0.32, BRONZE)
        z += h
        roof = s + 2.0                                   # a flared gold roof with upturned corners
        band(part, X, Y, Z, ngon(X, Y, 4, roof, rnd=0.4, turn=45), z, z + 0.5, GOLD, "zig")
        band(part, X, Y, Z, ngon(X, Y, 4, roof - 0.9, rnd=0.4, turn=45), z + 0.5, z + 1.0, GOLD_DK)
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = roof * 0.72
                rod(part, X, Y, Z, [(sx * c * 0.8, sy * c * 0.8, z + 0.3), (sx * c * 1.05, sy * c * 1.05, z + 1.3)], 0.3, GOLD)
                studs(part, X, Y, Z, [(sx * c * 1.05, sy * c * 1.05, z + 1.5)], r=0.38, pid=CORE)
        z += 1.0
    rod(part, X, Y, Z, [(0, 0, z), (0, 0, z + 3.5)], 0.35, GOLD)        # spire with rings
    for zz in (z + 0.8, z + 1.8, z + 2.8):
        band(part, X, Y, Z, circle(X, Y, 0.8), zz - 0.2, zz + 0.2, GOLD_DK)
    studs(part, X, Y, Z, [(0, 0, z + 3.8)], r=0.55, pid=CORE)
    pz = 6.0
    core(part, 0, 0, pz, 2.0)
    core(part, 0, 0, 11.0, 1.4)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F3 storm lantern
def f3_storm(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 6.0, 17.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.9 + 2.3 * np.sin(math.pi * H) ** 0.8
    _body(part, X, Y, Z, circle(X, Y, size), z0, z1, 1603)
    band(part, X, Y, Z, circle(X, Y, 3.8), 2.4, z0, BRONZE, "dots")       # the fuel tank
    band(part, X, Y, Z, circle(X, Y, 4.1), z0 - 0.5, z0, GOLD, "zig")
    band(part, X, Y, Z, circle(X, Y, 3.4), 1.6, 2.4, GOLD_DK)
    for k in range(6):                                   # a bowed gold guard cage
        a = math.radians(30 + 60 * k)
        pts = [((2.6 + 2.5 * math.sin(math.pi * t) ** 0.8) * math.cos(a), (2.6 + 2.5 * math.sin(math.pi * t) ** 0.8) * math.sin(a),
                z0 + (z1 - z0) * t) for t in np.linspace(0, 1, 9)]
        rod(part, X, Y, Z, pts, 0.3, GOLD)
    zt = stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.8 + g), z1, [(0.8, 0.5, GOLD, None), (0.2, 1.2, BRONZE, "dots"),
                                                                      (1.0, 0.4, GOLD_DK, None), (0.0, 0.9, GOLD, "zig")])
    _half_ring(part, X, Y, Z, z0 + 1.0, 4.9, 0.32, upper=True)         # the wire bail from the tank over the top
    studs(part, X, Y, Z, [(0, 0, zt + 0.4)], r=0.5, pid=CORE)
    pz = z0 + (z1 - z0) * 0.5
    core(part, 0, 0, pz, 2.4)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F4 faceted gem
def f4_gem(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 5.0, 21.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    s = 1.4 + 3.4 * np.clip(1 - np.abs(H - 0.42) * 1.9, 0, 1)
    _body(part, X, Y, Z, ngon(X, Y, 8, s, rnd=0.0, turn=22.5), z0, z1, 1604)
    _base(part, X, Y, Z, z0, r0=1.6, wide=3.2)
    for k in range(4):                                   # four gold claws gripping the gem
        a = math.radians(45 + 90 * k)
        c, sn = math.cos(a), math.sin(a)
        pts = [(1.8 * c, 1.8 * sn, z0), (4.4 * c, 4.4 * sn, z0 + 4.0), (5.0 * c, 5.0 * sn, z0 + 6.7), (4.0 * c, 4.0 * sn, z0 + 9.0)]
        rod(part, X, Y, Z, pts, 0.5, GOLD)
        studs(part, X, Y, Z, [pts[2]], r=0.6, pid=GOLD_DK)
        studs(part, X, Y, Z, [pts[3]], r=0.45, pid=CORE)
    band(part, X, Y, Z, ngon(X, Y, 8, 4.95, turn=22.5), z0 + 6.4, z0 + 7.0, GOLD, "dots")   # the girdle
    part[(ngon(X, Y, 8, 4.2, turn=22.5) <= 0) & (Z > z0 + 6.4) & (Z <= z0 + 7.0) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.3 + g), z1, [(0.3, 0.5, GOLD, None), (-0.3, 0.75, GOLD_DK, None)])
    studs(part, X, Y, Z, [(0, 0, z1 + 1.8)], r=0.65, pid=CORE)
    pz = z0 + (z1 - z0) * 0.42
    core(part, 0, 0, pz, 2.8)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F5 crescent moon
def f5_moon(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    cz, R = 14.5, 5.0
    sphere_glass(part, X, Y, Z, cz, R, 1605)
    tmp = np.zeros(X.shape, np.int8)                     # a heavy gold crescent wrapping the left of the globe
    tilted_ring(tmp, X, Y, Z, cz, R + 0.9, 1.0, 90, 0, GOLD)
    keep = (tmp > 0) & (X < -0.6)
    part[keep] = GOLD
    rr = np.hypot(np.hypot(X, Y), Z - cz)
    part[keep & (np.abs(((np.arctan2(Z - cz, X) * 10 / math.pi) % 1) - 0.5) < 0.12)] = GOLD_ENG
    for t in (-0.8, 0.8):                                # the crescent's horns, tipped with gems
        studs(part, X, Y, Z, [(-0.6, 0.0, cz + t * (R + 0.9))], r=0.7, pid=CORE)
    tilted_ring(part, X, Y, Z, cz, R + 0.5, 0.32, 0, 0, GOLD_DK)          # an equator band
    rod(part, X, Y, Z, [(0, 0, 1.6), (0, 0, cz - R)], 0.6, BRONZE)        # stand
    for zz in (4.0, 7.0):
        band(part, X, Y, Z, circle(X, Y, 1.1), zz - 0.3, zz + 0.3, GOLD, "dots")
    _base(part, X, Y, Z, 1.6, r0=1.2, wide=3.4)
    band(part, X, Y, Z, circle(X, Y, 2.4), cz - R - 0.5, cz - R + 0.4, GOLD, "zig")
    studs(part, X, Y, Z, [(0, 0, cz + R + 0.8)], r=0.6, pid=GOLD)
    core(part, 0, 0, cz, 3.0)
    return coarsen_glass(part), cz


# ------------------------------------------------------------------ F6 obelisk
def f6_obelisk(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.0, 23.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    s = 3.3 - 1.5 * H
    _body(part, X, Y, Z, ngon(X, Y, 4, s, rnd=0.0, turn=45), z0, z1, 1606, lines=4)
    for sx in (-1, 1):                                   # gold edges
        for sy in (-1, 1):
            rod(part, X, Y, Z, [(sx * 2.33, sy * 2.33, z0), (sx * 1.27, sy * 1.27, z1)], 0.34, GOLD)
    for k, zz in enumerate(np.linspace(z0 + 2.0, z1 - 2.0, 5)):            # gold bands, alternating engraving
        hh = (zz - z0) / (z1 - z0)
        band(part, X, Y, Z, ngon(X, Y, 4, 3.3 - 1.5 * hh + 0.35, turn=45), zz - 0.3, zz + 0.3, GOLD, "zig" if k % 2 else "dots")
        part[(ngon(X, Y, 4, 3.3 - 1.5 * hh - 0.4, turn=45) <= 0) & (np.abs(Z - zz) <= 0.3) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
    for k in range(4):                                   # the gold pyramidion
        band(part, X, Y, Z, ngon(X, Y, 4, 1.9 - k * 0.5, turn=45), z1 + k * 0.6, z1 + (k + 1) * 0.6, GOLD if k % 2 == 0 else GOLD_DK)
    studs(part, X, Y, Z, [(0, 0, z1 + 2.8)], r=0.5, pid=CORE)
    stepped(part, X, Y, Z, lambda g: ngon(X, Y, 4, 3.0 + g, turn=45), z0, [(0.6, 0.6, GOLD, "dots"), (1.4, 1.0, BRONZE, None),
                                                                         (2.2, 0.6, GOLD_DK, "zig")], down=True)
    pz = 9.5
    core(part, 0, 0, pz, 2.2)
    core(part, 0, 0, 16.0, 1.4)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F7 hanging bell lantern on a bracket
def f7_hanging(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    stepped(part, X, Y, Z, lambda g: circle(X + 6.5, Y, 1.0 + g), 1.6, [(0.5, 0.5, GOLD, None), (1.4, 0.75, BRONZE, "dots"),
                                                                       (2.2, 0.5, GOLD_DK, None)], down=True)
    rod(part, X, Y, Z, [(-6.5, 0, 1.6), (-6.5, 0, 28.5)], 0.55, BRONZE)    # post and bracket arm
    rod(part, X, Y, Z, [(-6.5, 0, 27.5), (0, 0, 27.5)], 0.45, GOLD)
    rod(part, X, Y, Z, [(-6.5, 0, 23.5), (-3.2, 0, 27.3)], 0.3, GOLD)     # a brace with a scroll
    ring_xz(part, X, Y, Z, 24.6, 1.1, 0.25, GOLD, axis="y")
    studs(part, X, Y, Z, [(-6.5, 0, 29.0), (0.4, 0, 27.5)], r=0.6, pid=GOLD_DK)
    for t in np.linspace(0, 1, 6):                       # chain links
        studs(part, X, Y, Z, [(0, 0, 27.0 - 2.4 * t)], r=0.3, pid=GOLD)
    z0, z1 = 11.0, 23.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.4 + 3.0 * (1 - H) ** 0.7                    # a bell: wide mouth at the bottom
    _body(part, X, Y, Z, circle(X, Y, size), z0, z1, 1607)
    band(part, X, Y, Z, circle(X, Y, 4.8), z0 - 0.6, z0, GOLD, "zig")      # the mouth rim
    part[(circle(X, Y, 3.6) <= 0) & (Z > z0 - 0.6) & (Z <= z0)] = EMPTY
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.4 + g), z1, [(0.3, 0.5, GOLD, "dots"), (-0.3, 0.5, GOLD_DK, None)])
    rod(part, X, Y, Z, [(0, 0, z0 + 0.5), (0, 0, z0 - 3.0)], 0.3, GOLD)    # a clapper drop under the mouth
    studs(part, X, Y, Z, [(0, 0, z0 - 3.3)], r=0.7, pid=CORE)
    pz = z0 + 3.5
    core(part, 0, 0, pz, 2.4)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F8 pierced star lamp
def f8_star_lamp(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.5, 19.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.8 + 2.6 * np.sin(math.pi * H) ** 0.6
    _body(part, X, Y, Z, circle(X, Y, size), z0, z1, 1608)
    rr = np.hypot(X, Y)
    want = 1.8 + 2.6 * np.sin(math.pi * H) ** 0.6 + 0.45
    skin = (np.abs(rr - want) <= 0.3) & (Z > z0 + 0.3) & (Z <= z1 - 0.3)
    u = np.arctan2(Y, X) * want
    cell = 1.6
    a = (u % cell) - cell / 2
    b = ((Z - z0) % cell) - cell / 2
    star = (np.abs(a) + np.abs(b) < 0.55) | ((np.abs(a) < 0.16) & (np.abs(b) < 0.62)) | ((np.abs(b) < 0.16) & (np.abs(a) < 0.62))
    part[skin & ~star] = GOLD                            # a pierced gold shell: the light shines out through stars
    part[skin & ~star & (np.abs(np.abs(a) + np.abs(b) - 0.75) < 0.12)] = GOLD_ENG
    _base(part, X, Y, Z, z0, r0=1.4, wide=3.0)
    for k in range(6):                                   # an onion dome on top, ribbed
        band(part, X, Y, Z, circle(X, Y, 2.6 - k * 0.45), z1 + k * 0.5, z1 + (k + 1) * 0.5, GOLD if k % 2 == 0 else GOLD_DK)
    rod(part, X, Y, Z, [(0, 0, z1 + 3.0), (0, 0, z1 + 5.5)], 0.25, GOLD)
    band(part, X, Y, Z, circle(X, Y, 0.6), z1 + 4.0, z1 + 4.4, GOLD_DK)
    studs(part, X, Y, Z, [(0, 0, z1 + 5.8)], r=0.45, pid=CORE)
    pz = z0 + (z1 - z0) * 0.5
    core(part, 0, 0, pz, 2.8)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F9 chalice
def f9_chalice(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 12.0, 21.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.2 + 3.6 * H ** 0.6
    _body(part, X, Y, Z, circle(X, Y, size), z0, z1, 1609)
    band(part, X, Y, Z, circle(X, Y, 5.2), z1 - 0.6, z1, GOLD, "dots")     # gold rim and lip
    part[(circle(X, Y, 4.2) <= 0) & (Z > z1 - 0.6) & (Z <= z1)] = EMPTY
    for k in range(6):                                   # gold ribs up the cup
        a = math.radians(30 + 60 * k)
        if abs(math.degrees(a) - 270) < 40:
            continue
        pts = [((1.2 + 3.6 * t ** 0.6 + 0.3) * math.cos(a), (1.2 + 3.6 * t ** 0.6 + 0.3) * math.sin(a), z0 + (z1 - z0) * t)
               for t in np.linspace(0.05, 1, 8)]
        rod(part, X, Y, Z, pts, 0.28, GOLD)
    rod(part, X, Y, Z, [(0, 0, 3.0), (0, 0, z0 + 0.5)], 0.7, GOLD)        # the stem with knots
    for zz, r in ((5.5, 1.4), (8.5, 1.8), (10.8, 1.2)):
        band(part, X, Y, Z, circle(X, Y, r), zz - 0.45, zz + 0.45, GOLD_DK if r > 1.5 else GOLD, "zig" if r > 1.5 else None)
    for k in range(4):
        a = math.radians(90 * k)
        studs(part, X, Y, Z, [(1.9 * math.cos(a), 1.9 * math.sin(a), 8.5)], r=0.45, pid=CORE)
    _base(part, X, Y, Z, 3.0, r0=1.4, wide=3.4)
    pz = z0 + 4.5
    core(part, 0, 0, pz, 2.6)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F10 clockwork
def _gear(part, X, Y, Z, x0, cy, cz, R, teeth, pid=GOLD):
    """An upright gear in the plane x = x0 (facing out to the side)."""
    rr = np.hypot(Y - cy, Z - cz)
    ang = np.arctan2(Z - cz, Y - cy)
    tooth = np.cos(teeth * ang) > 0.1
    slab = np.abs(X - x0) <= 0.3
    part[slab & ((rr <= R) | ((rr <= R + 0.5) & tooth)) & (rr > R * 0.45)] = pid
    part[slab & (rr <= R * 0.3)] = GOLD_DK
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        rod(part, X, Y, Z, [(x0, cy, cz), (x0, cy + R * 0.5 * math.cos(a), cz + R * 0.5 * math.sin(a))], 0.22, pid)


def f10_clockwork(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 5.0, 19.0
    _body(part, X, Y, Z, circle(X, Y, 3.4), z0, z1, 1610)
    _base(part, X, Y, Z, z0, r0=2.6, wide=2.2)
    for zz in (z0 + 0.4, z1 - 0.4):
        band(part, X, Y, Z, circle(X, Y, 3.9), zz - 0.4, zz + 0.4, GOLD, "zig")
        part[(circle(X, Y, 3.2) <= 0) & (np.abs(Z - zz) <= 0.4)] = EMPTY
    for sx in (-1, 1):                                   # meshing gears on both sides
        _gear(part, X, Y, Z, sx * 3.9, 0.0, 15.0, 2.4, 10, GOLD)
        _gear(part, X, Y, Z, sx * 3.9, 1.6, 9.6, 1.6, 7, BRONZE)
        _gear(part, X, Y, Z, sx * 3.9, -1.4, 7.2, 1.1, 6, GOLD)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 2.4 + g), z1, [(1.4, 0.5, GOLD, None), (0.6, 0.75, BRONZE, "dots"),
                                                                 (-0.4, 0.5, GOLD_DK, None)])
    ring_xz(part, X, Y, Z, z1 + 3.2, 1.2, 0.35, GOLD, axis="y")          # winding key on top
    rod(part, X, Y, Z, [(0, 0, z1 + 1.75), (0, 0, z1 + 2.0)], 0.4, GOLD)
    pz = (z0 + z1) / 2 - 1.0
    core(part, 0, 0, pz, 2.6)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F11 lighthouse
def f11_lighthouse(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    zt = 17.0
    H = np.clip(Z / zt, 0, 1)
    tower = (circle(X, Y, 3.6 - 1.1 * H) <= 0) & (Z > 1.0) & (Z <= zt)
    stripe = (np.floor((Z - 1.0) / 2.5) % 2) == 0
    part[tower & stripe] = BRONZE
    part[tower & ~stripe] = GOLD
    part[tower & (circle(X, Y, 3.6 - 1.1 * H - 0.5) <= 0)] = EMPTY
    for zz in (5.0, 10.0, 14.5):                         # lit windows up the tower
        for a in (0, 120, 240):
            ar = math.radians(a + 30)
            hh = zz / zt
            rr = 3.6 - 1.1 * hh
            studs(part, X, Y, Z, [(rr * math.cos(ar), rr * math.sin(ar), zz)], r=0.45, pid=CORE)
    band(part, X, Y, Z, circle(X, Y, 3.8), zt, zt + 0.5, GOLD, "dots")    # the gallery and its rail
    for k in range(12):
        a = k * math.pi / 6
        rod(part, X, Y, Z, [(3.5 * math.cos(a), 3.5 * math.sin(a), zt + 0.5), (3.5 * math.cos(a), 3.5 * math.sin(a), zt + 1.6)], 0.18, GOLD_DK)
    ring_xz(part, X, Y, Z, zt + 1.6, 3.5, 0.2, GOLD)
    z0, z1 = zt + 0.5, zt + 6.0
    _body(part, X, Y, Z, circle(X, Y, 2.3), z0, z1, 1611, lines=2)       # the lantern room
    for k in range(6):
        a = math.radians(30 + 60 * k)
        rod(part, X, Y, Z, [(2.4 * math.cos(a), 2.4 * math.sin(a), z0), (2.4 * math.cos(a), 2.4 * math.sin(a), z1)], 0.2, GOLD)
    for k in range(5):
        band(part, X, Y, Z, circle(X, Y, 2.7 - k * 0.55), z1 + k * 0.45, z1 + (k + 1) * 0.45, GOLD if k % 2 == 0 else GOLD_DK)
    studs(part, X, Y, Z, [(0, 0, z1 + 2.6)], r=0.45, pid=CORE)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 3.6 + g), 1.0, [(0.4, 0.5, GOLD_DK, None), (1.0, 0.5, BRONZE, "zig")], down=True)
    core(part, 0, 0, (z0 + z1) / 2, 1.6)
    pz = 8.0                                             # the port on the tower, a beacon door
    core(part, 0, 0, pz, 1.8)
    part[(circle(X, Y, 3.0 - 1.1 * (pz / zt) - 0.5) <= 0) & (np.abs(Z - pz) < 2.0) & (part == EMPTY)] = EMPTY
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ F12 seed pod
def f12_seed_pod(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 6.0, 21.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 0.8 + 3.6 * np.sin(math.pi * H ** 0.85) ** 0.75
    _body(part, X, Y, Z, circle(X, Y, size), z0, z1, 1612)
    for k in range(6):                                   # six gold petals curling up round the pod, open at the front
        a = math.radians(30 + 60 * k)
        if abs(math.degrees(a) - 270) < 40:
            continue
        c, s = math.cos(a), math.sin(a)
        spine = [((0.8 + 4.6 * math.sin(math.pi * t ** 0.85) ** 0.75 + 0.6 * t) * c,
                  (0.8 + 4.6 * math.sin(math.pi * t ** 0.85) ** 0.75 + 0.6 * t) * s, z0 + (z1 - z0) * 0.8 * t)
                 for t in np.linspace(0.02, 1, 10)]
        side = [(p[0] - s * 0.9 * math.sin(math.pi * i / 9), p[1] + c * 0.9 * math.sin(math.pi * i / 9), p[2]) for i, p in enumerate(spine)]
        fin(part, X, Y, Z, spine, side, th=0.25, pid=GOLD)
        rod(part, X, Y, Z, spine, 0.3, GOLD_DK)
        studs(part, X, Y, Z, [spine[-1]], r=0.45, pid=CORE)
    rod(part, X, Y, Z, [(0, 0, 1.6), (0, 0, z0 + 0.5)], 0.6, BRONZE)     # stem
    for k in range(3):                                   # root feet
        a = math.radians(90 + 120 * k)
        rod(part, X, Y, Z, [(0, 0, 2.4), (2.2 * math.cos(a), 2.2 * math.sin(a), 1.2), (3.6 * math.cos(a), 3.6 * math.sin(a), 0.3)], 0.45, GOLD)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 0.6 + g), z1, [(0.3, 0.5, GOLD, None)])
    rod(part, X, Y, Z, [(0, 0, z1 + 0.5), (0.6, 0, z1 + 2.0), (0.2, 0, z1 + 3.2)], 0.25, GOLD)   # a curled tip
    studs(part, X, Y, Z, [(0.2, 0, z1 + 3.4)], r=0.45, pid=CORE)
    pz = z0 + (z1 - z0) * 0.42
    core(part, 0, 0, pz, 2.8)
    return coarsen_glass(part), pz


DESIGNS = {"F1": ("Classic battery lantern", _w(f1_classic, pr=1.3), "g"),
           "F2": ("Pagoda", _w(f2_pagoda, pr=1.1), "g"),
           "F3": ("Storm lantern", _w(f3_storm, pr=1.2), "g"),
           "F4": ("Faceted gem", _w(f4_gem, pr=1.3), "g"),
           "F5": ("Crescent moon", _w(f5_moon, pr=1.3), "g"),
           "F6": ("Obelisk", _w(f6_obelisk, pr=1.1), "g"),
           "F7": ("Hanging bell", _w(f7_hanging, pr=1.1), "g"),
           "F8": ("Pierced star lamp", _w(f8_star_lamp, pr=1.2), "g"),
           "F9": ("Chalice", _w(f9_chalice, pr=1.2), "g"),
           "F10": ("Clockwork", _w(f10_clockwork, pr=1.2), "g"),
           "F11": ("Lighthouse", _w(f11_lighthouse, pr=1.0), "g"),
           "F12": ("Seed pod", _w(f12_seed_pod, pr=1.3), "g")}

MOVING = {}
MID = P13.MID


def build(code):
    X, Y, Z = grid()
    P10.STYLE["hue"] = P10.CORPS[DESIGNS[code][2]][1]
    STYLE["dark"] = False
    return DESIGNS[code][1](X, Y, Z)


quads = P13.quads
model_boxes = P13.model_boxes
