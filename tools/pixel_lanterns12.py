"""Pass 612: the reliquary round, 12 takes, with parts that really move.

J's ratings (in chat, 2026-10-19): 611 Q1 detailed IMPROVE, Q4 floating IMPROVE "make the rings actually move", Q6 twin
balance IMPROVE "creative i guess"; 610 N2g IMPROVE "Looks good for the core maybe a more detailed gold portion", N2r
IMPROVE; every shrine and the other ideas dropped except S4. He picked "Reliquary round": 3 variations each of
  R1 (611 Q1 detailed)  R2 (610 N2 + more detailed gold)  R4 (611 Q4 floating, rings that move)  R6 (611 Q6 twin, creative)
Moving parts are separate voxel models: MOVING[code] lists them with a pivot, a fixed tilt and a spin the builder drives
(the same split a Blockbench export makes: one bone per moving part).
"""
import math
import numpy as np
from pixel_lanterns6 import G, grid, circle, ngon, glass, band, stepped, rod, ring_xz, EMPTY, GOLD, GOLD_DK, GOLD_ENG, SILVER
import pixel_lanterns6 as P6
import pixel_lanterns7 as P7
from pixel_lanterns7 import hollow, core, studs, coarsen_glass, CORE
import pixel_lanterns10 as P10
from pixel_lanterns10 import BRONZE, STEEL, OBSID, BARK, CRYS, tilted_ring
import pixel_lanterns11 as P11
from pixel_lanterns11 import reliquary, small_port, amph_r, Z0R, Z1R

MID = 16.0                                               # moving parts are built centred on (0, 0, MID), then moved to their pivot


# ------------------------------------------------------------------ more detailed gold
def gold_net(part, X, Y, Z, z_lo, z_hi, rad_of_z, cell=2.2, off=0.45):
    """A pierced gold lattice standing just off the glass between z_lo and z_hi (diamonds, studs at the crossings)."""
    rr = np.hypot(X, Y)
    zz = np.clip(Z, z_lo, z_hi)
    want = np.vectorize(rad_of_z)(zz) + off
    skin = (np.abs(rr - want) <= 0.32) & (Z > z_lo) & (Z <= z_hi)
    u = np.arctan2(Y, X) * want
    a = ((u + Z) % cell) - cell / 2
    b = ((u - Z) % cell) - cell / 2
    lat = (np.abs(a) < 0.3) | (np.abs(b) < 0.3)
    front = (np.abs(X) < 2.6) & (Y < 0) & (np.abs(Z - (Z0R + (Z1R - Z0R) * 0.38)) < 2.6)
    part[skin & lat & ~front] = GOLD
    part[skin & (np.abs(a) < 0.3) & (np.abs(b) < 0.3) & ~front] = GOLD_DK


def gold_wire(part, X, Y, Z, pts, r_wire=0.25, wrap=0.75, turns=6):
    """A gold wire spiralling round a polyline (e.g. round an arm)."""
    pts = np.array(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    total = seg.sum()
    out = []
    n = 60
    for i in range(n + 1):
        s = total * i / n
        k = min(np.searchsorted(np.cumsum(seg), s), len(seg) - 1)
        s0 = s - (np.cumsum(seg)[k] - seg[k])
        p = pts[k] + (pts[k + 1] - pts[k]) * (s0 / max(seg[k], 1e-6))
        d = (pts[k + 1] - pts[k]) / max(seg[k], 1e-6)
        a = np.cross(d, [0, 1, 0]) if abs(d[1]) < 0.9 else np.cross(d, [1, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(d, a)
        t = 2 * math.pi * turns * i / n
        out.append(tuple(p + (a * math.cos(t) + b * math.sin(t)) * wrap))
    rod(part, X, Y, Z, out, r_wire, GOLD)


def gem_crown(part, X, Y, Z, zt, n=8, r0=2.2, h=1.6):
    band(part, X, Y, Z, circle(X, Y, r0 + 0.3), zt, zt + 0.75, GOLD, "dots")
    part[(circle(X, Y, r0 - 0.4) <= 0) & (Z > zt) & (Z <= zt + 0.75) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
    for k in range(n):
        a = k * 2 * math.pi / n
        rod(part, X, Y, Z, [(r0 * math.cos(a), r0 * math.sin(a), zt + 0.75), (r0 * math.cos(a), r0 * math.sin(a), zt + 0.75 + h * (1 if k % 2 else 0.6))], 0.32)
        studs(part, X, Y, Z, [(r0 * math.cos(a), r0 * math.sin(a), zt + 0.9 + h * (1 if k % 2 else 0.6))], r=0.4, pid=CORE if k % 2 else GOLD_DK)


def claw_feet(part, X, Y, Z, n=3, r0=3.6):
    for k in range(n):
        a = math.radians(90 + k * 360 / n)
        c, s = math.cos(a), math.sin(a)
        rod(part, X, Y, Z, [(r0 * c, r0 * s, 1.6), ((r0 + 1.2) * c, (r0 + 1.2) * s, 0.8), ((r0 + 2.0) * c, (r0 + 2.0) * s, 0.35)], 0.45, GOLD)
        for dt in (-0.55, 0.0, 0.55):
            studs(part, X, Y, Z, [((r0 + 2.2) * c - s * dt, (r0 + 2.2) * s + c * dt, 0.3)], r=0.32, pid=GOLD_DK)


def arms_pts(sx, z0=Z0R, z1=Z1R):
    pts = []
    for i in range(14):
        t = i / 13
        zz = 1.2 + (z1 - 2.5 - 1.2) * t
        hh = (zz - z0) / (z1 - z0)
        rr = amph_r(max(0.0, min(1.0, hh))) + 0.9 + 0.8 * math.sin(math.pi * t)
        pts.append((sx * rr, 0.0, zz))
    return pts


def body_r(z):
    return amph_r(max(0.0, min(1.0, (z - Z0R) / (Z1R - Z0R))))


# ------------------------------------------------------------------ R1: 611 Q1 detailed, three ways
def r1a_gilded_net(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 1201)
    gold_net(part, X, Y, Z, Z0R + 9.0, Z1R - 1.2, body_r)                    # pierced gold over the shoulders and neck
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def r1b_crowned(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 1202, lid=False)
    gem_crown(part, X, Y, Z, Z1R, n=10, r0=2.4, h=2.0)
    for sx in (-1, 1):                                                        # gold chains from the crown to the hands
        pts = [(sx * 2.4, 0.0, Z1R + 0.4)] + [(sx * (2.4 + 0.4 * math.sin(math.pi * t)), 0.6 * math.sin(math.pi * t), Z1R + 0.4 - 2.0 * t) for t in np.linspace(0.1, 1, 7)]
        for p in pts:
            studs(part, X, Y, Z, [p], r=0.28, pid=GOLD)
        gold_wire(part, X, Y, Z, arms_pts(sx)[2:12], wrap=0.7, turns=7)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def r1c_gold_foot(X, Y, Z):
    part, pz, zt = reliquary(X, Y, Z, 1203)
    zl = Z0R + (Z1R - Z0R) * 0.22                                           # the lower body plated in engraved gold
    hh = np.clip((Z - Z0R) / (Z1R - Z0R), 0, 1)
    rr = np.hypot(X, Y)
    want = 1.6 + 3.2 * np.exp(-((hh - 0.38) / 0.24) ** 2) + 0.35
    plate = (np.abs(rr - want) <= 0.35) & (Z > Z0R) & (Z <= zl)
    part[plate] = GOLD
    ang = np.arctan2(Y, X)
    part[plate & (np.abs(((ang * 6 / math.pi) % 1) - 0.5) < 0.1)] = GOLD_ENG
    claw_feet(part, X, Y, Z, n=4, r0=3.4)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ R2: 610 N2 + "a more detailed gold portion"
def _n2(X, Y, Z):
    part, pz = P10.n2_reliquary(X, Y, Z)
    return part, pz


def r2a_gold_arms(X, Y, Z):
    part, pz = _n2(X, Y, Z)
    for sx in (-1, 1):
        pts = arms_pts(sx)
        rod(part, X, Y, Z, pts, 0.6, GOLD)                                    # the arms gilded, wire-wrapped
        gold_wire(part, X, Y, Z, pts[1:13], wrap=0.75, turns=8)
        for i in (3, 6, 9):
            studs(part, X, Y, Z, [pts[i]], r=0.75, pid=GOLD_DK)
        hx = sx * 2.2                                                         # hands with four fingers round the neck
        for f in range(4):
            a = math.radians(-60 + f * 40)
            rod(part, X, Y, Z, [(hx, 0, Z1R - 2.4), (hx - sx * 0.8 * math.cos(a), 0.9 * math.sin(a), Z1R - 2.0 + 0.2 * f)], 0.28, GOLD)
    return part, pz


def r2b_gold_arms_red(X, Y, Z):
    return r2a_gold_arms(X, Y, Z)


def r2c_gold_shoulders(X, Y, Z):
    part, pz = _n2(X, Y, Z)
    gold_net(part, X, Y, Z, Z0R + 8.5, Z1R - 1.4, body_r, cell=1.8)
    gem_crown(part, X, Y, Z, Z1R + 1.75, n=8, r0=1.8, h=1.2)
    claw_feet(part, X, Y, Z, n=3, r0=3.2)
    return part, pz


# ------------------------------------------------------------------ R4: floating, the rings really move
def _floating(X, Y, Z, seed):
    part, pz, zt = reliquary(X, Y, Z, seed, arms=False, float_gap=2.0)
    r = np.hypot(X, Y)
    part[(Z > 4.6) & (Z <= 5.1) & (r <= 2.4) & (r > 1.6)] = CORE
    for sx in (-1, 1):
        studs(part, X, Y, Z, [(sx * 3.0, 0.0, Z1R + 2.0 - 2.4)], r=0.85, pid=GOLD)
    core(part, 0, 0, pz, 2.9)
    small_port(part, X, Y, Z, pz)
    return coarsen_glass(part), pz


def ring_part(R, r, pid, nodes=6, node_pid=CORE, upright=False, satellites=False):
    """A flat ring (in XY, centred on (0, 0, MID)) with nodes, so its spin reads."""
    X, Y, Z = grid()
    part = np.zeros(X.shape, np.int8)
    if not satellites:
        part[np.hypot(np.hypot(X, Y) - R, Z - MID) <= r] = pid
    for k in range(nodes):
        a = k * 2 * math.pi / nodes
        studs(part, X, Y, Z, [(R * math.cos(a), R * math.sin(a), MID)], r=0.55 if not satellites else 0.7,
              pid=node_pid if k % 2 == 0 else GOLD)
    return part


def r4a_three_rings(X, Y, Z):
    return _floating(X, Y, Z, 1241)


def r4b_gyroscope(X, Y, Z):
    return _floating(X, Y, Z, 1242)


def r4c_satellites(X, Y, Z):
    return _floating(X, Y, Z, 1243)


# ------------------------------------------------------------------ R6: twin balance, creative (and moving)
def small_amphora(part, X, Y, Z, cx, cy, z0, z1, seed, scale=1.0):
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = (1.0 + 2.1 * np.exp(-((H - 0.4) / 0.25) ** 2) + 0.6 * np.exp(-((H - 0.96) / 0.06) ** 2)) * scale
    sec = np.hypot(X - cx, Y - cy) - size
    glass(part, X - cx, Y - cy, Z, sec, z0, z1, seed=seed, bulge_h=0.15, craze=2.6, lines=2)
    hollow(part, sec)
    zm = z0 + (z1 - z0) * 0.4
    band(part, X, Y, Z, np.hypot(X - cx, Y - cy) - 3.3 * scale, zm - 0.3, zm + 0.3, GOLD, "zig")
    part[(np.hypot(X - cx, Y - cy) <= 2.4 * scale) & (np.abs(Z - zm) <= 0.3) & np.isin(part, [GOLD, GOLD_ENG])] = EMPTY
    band(part, X, Y, Z, np.hypot(X - cx, Y - cy) - 1.5 * scale, z0 - 0.6, z0, GOLD_DK)
    band(part, X, Y, Z, np.hypot(X - cx, Y - cy) - 1.4 * scale, z1, z1 + 0.5, GOLD)
    studs(part, X, Y, Z, [(cx, cy, z1 + 1.0)], r=0.55, pid=CORE)
    core(part, cx, cy, zm, 1.5 * scale)


def r6a_scales(X, Y, Z):
    """A true balance: a tall post, the beam rocks (moving part) with two amphorae hanging from it."""
    part = np.zeros(X.shape, np.int8)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.4 + g), 1.6, [(0.6, 0.5, GOLD, None), (2.0, 0.75, BRONZE, "dots"),
                                                                 (3.0, 0.5, GOLD_DK, None)], down=True)
    rod(part, X, Y, Z, [(0, 0, 1.6), (0, 0, 24.5)], 0.6, BRONZE)
    studs(part, X, Y, Z, [(0, 0, 25.4)], r=1.0, pid=GOLD)
    part[(np.maximum(np.abs(X), np.abs(Z - 12.0)) <= 1.5) & (Y > -1.3) & (Y <= 0.2)] = BRONZE
    pz = 12.0
    small_port(part, X, Y, Z, pz, pr=1.3)
    return part, pz


def r6a_beam(X, Y, Z):
    """The moving beam, built round the pivot at MID: beam, chains, two hanging amphorae."""
    part = np.zeros(X.shape, np.int8)
    rod(part, X, Y, Z, [(-6.2, 0, MID), (6.2, 0, MID)], 0.45, GOLD)
    studs(part, X, Y, Z, [(0, 0, MID)], r=0.8, pid=GOLD_DK)
    for sx, seed in ((-1, 1261), (1, 1262)):
        cx = sx * 5.6
        for t in np.linspace(0, 1, 7):
            studs(part, X, Y, Z, [(cx, 0, MID - 0.6 - 2.4 * t)], r=0.25, pid=GOLD)
        small_amphora(part, X, Y, Z, cx, 0.0, MID - 12.5, MID - 3.4, seed, scale=0.8)
    return coarsen_glass(part)


def r6b_carousel(X, Y, Z):
    """Three small amphorae on a turning three-armed stand (moving part), a gold canopy above."""
    part = np.zeros(X.shape, np.int8)
    stepped(part, X, Y, Z, lambda g: circle(X, Y, 1.4 + g), 1.6, [(0.6, 0.5, GOLD, None), (2.4, 0.75, BRONZE, "zig"),
                                                                 (3.4, 0.5, GOLD_DK, None)], down=True)
    rod(part, X, Y, Z, [(0, 0, 1.6), (0, 0, 22.0)], 0.6, BRONZE)
    for k in range(6):                                                         # canopy
        band(part, X, Y, Z, circle(X, Y, 6.5 - k * 1.0), 22.0 + k * 0.5, 22.5 + k * 0.5, GOLD if k % 2 == 0 else GOLD_DK)
    studs(part, X, Y, Z, [(0, 0, 25.6)], r=0.7, pid=CORE)
    pz = 7.0
    part[(np.maximum(np.abs(X), np.abs(Z - pz)) <= 1.5) & (Y > -1.3) & (Y <= 0.2)] = BRONZE
    small_port(part, X, Y, Z, pz, pr=1.3)
    return part, pz


def r6b_arms(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    for k in range(3):
        a = math.radians(90 + k * 120)
        cx, cy = 5.4 * math.cos(a), 5.4 * math.sin(a)
        rod(part, X, Y, Z, [(0.8 * math.cos(a), 0.8 * math.sin(a), MID - 4.5), (cx, cy, MID - 4.5)], 0.4, GOLD)
        small_amphora(part, X, Y, Z, cx, cy, MID - 3.8, MID + 4.4, 1263 + k, scale=0.65)
    band(part, X, Y, Z, circle(X, Y, 1.2), MID - 5.0, MID - 4.0, GOLD_DK)
    return coarsen_glass(part)


def r6c_hourglass(X, Y, Z):
    """Two amphorae mouth to mouth (one upside down) in a bronze frame: an hourglass reliquary."""
    part = np.zeros(X.shape, np.int8)
    small_amphora(part, X, Y, Z, 0.0, 0.0, 3.0, 12.4, 1264, scale=1.15)
    Zf = 26.0 - Z                                                              # the top one, mirrored in Z
    tmp = np.zeros(X.shape, np.int8)
    small_amphora(tmp, X, Y, Zf, 0.0, 0.0, 3.0, 12.4, 1265, scale=1.15)
    part[tmp > 0] = tmp[tmp > 0]
    band(part, X, Y, Z, circle(X, Y, 1.9), 12.4, 13.6, GOLD, "dots")         # the waist where they meet
    for k in range(4):                                                         # frame posts
        a = math.radians(45 + 90 * k)
        cx, cy = 4.8 * math.cos(a), 4.8 * math.sin(a)
        rod(part, X, Y, Z, [(cx, cy, 1.0), (cx, cy, 25.0)], 0.45, BRONZE)
        studs(part, X, Y, Z, [(cx, cy, 25.4), (cx, cy, 0.8)], r=0.6, pid=GOLD)
    for zc in (0.5, 25.3):
        band(part, X, Y, Z, ngon(X, Y, 4, 5.0, rnd=1.0, turn=45), zc - 0.4, zc + 0.4, BRONZE, "zig")
    ring_xz(part, X, Y, Z, 27.2, 1.0, 0.33, GOLD, axis="y")
    pz = 7.8
    small_port(part, X, Y, Z, pz, pr=1.4)
    return coarsen_glass(part), pz


DESIGNS = {"R1a": ("Reliquary: gilded net", r1a_gilded_net, "g"), "R1b": ("Reliquary: gem crown", r1b_crowned, "g"),
           "R1c": ("Reliquary: gold foot", r1c_gold_foot, "g"),
           "R2a": ("N2: gold arms", r2a_gold_arms, "g"), "R2b": ("N2: gold arms, red", r2b_gold_arms_red, "r"),
           "R2c": ("N2: gold shoulders", r2c_gold_shoulders, "g"),
           "R4a": ("Floating: three spinning rings", r4a_three_rings, "g"), "R4b": ("Floating: gyroscope", r4b_gyroscope, "g"),
           "R4c": ("Floating: satellites", r4c_satellites, "g"),
           "R6a": ("Twin: rocking scales", r6a_scales, "g"), "R6b": ("Twin: carousel of three", r6b_carousel, "g"),
           "R6c": ("Twin: hourglass", r6c_hourglass, "g")}

# moving parts: (name, builder, pivot (x, y, z) px, fixed tilt (rx, ry, rz) deg, spin axis 0/1/2, driver expression)
PZ4 = Z0R + 2.0 + (Z1R - Z0R) * 0.38
MOVING = {
    "R4a": [("ring A", lambda: ring_part(6.0, 0.4, BRONZE), (0, 0, PZ4), (12, 0, 0), 2, "frame * 0.11"),
            ("ring B", lambda: ring_part(6.9, 0.35, GOLD, nodes=8), (0, 0, PZ4), (64, 0, 30), 2, "frame * -0.07"),
            ("ring C", lambda: ring_part(7.7, 0.32, BRONZE, nodes=4), (0, 0, PZ4), (-55, 0, -40), 2, "frame * 0.05")],
    "R4b": [("gimbal outer", lambda: ring_part(7.6, 0.4, BRONZE, nodes=4), (0, 0, PZ4), (90, 0, 0), 0, "frame * 0.04"),
            ("gimbal middle", lambda: ring_part(6.8, 0.36, GOLD, nodes=4), (0, 0, PZ4), (90, 0, 90), 1, "frame * 0.06"),
            ("gimbal inner", lambda: ring_part(6.0, 0.34, BRONZE, nodes=6), (0, 0, PZ4), (0, 0, 0), 2, "frame * 0.09")],
    "R4c": [("wide ring", lambda: ring_part(7.4, 0.45, GOLD, nodes=8, node_pid=GOLD_DK), (0, 0, PZ4), (8, 0, 0), 2, "frame * 0.03"),
            ("satellites", lambda: ring_part(5.6, 0.0, GOLD, nodes=5, satellites=True), (0, 0, PZ4), (-20, 0, 0), 2, "frame * -0.12")],
    "R6a": [("beam", lambda: r6a_beam(*grid()), (0, 0, 24.0), (0, 0, 0), 1, "0.16 * sin(frame * 0.07)")],
    "R6b": [("carousel", lambda: r6b_arms(*grid()), (0, 0, 16.0), (0, 0, 0), 2, "frame * 0.035")],
}


def build(code):
    X, Y, Z = grid()
    P10.STYLE["hue"] = P10.CORPS[DESIGNS[code][2]][1]
    return DESIGNS[code][1](X, Y, Z)


quads = P7.quads
model_boxes = P7.model_boxes
