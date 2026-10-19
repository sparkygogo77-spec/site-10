"""Pass 610: original lanterns, six new designs from scratch, each in green and one other corps colour (12 takes).

J: "make me original lanterns now"; ideas: a mixed bag of ancient relics, alien tech and living/organic; colours "Green +
one corps" (each design twice); 12 takes; style "Anything goes". Nothing here starts from the Dark Lantern's pinch or
the molten vault. Kept from the house rules: voxel pixel art at the Dark Lantern's depth, see-through glass round a core
carrying the G3 flare, a ring port, solid from every angle, original marks only (no corps emblems).

  N1 Shrine          relic: weathered bronze temple, four columns, domed roof, verdigris          + orange
  N2 Reliquary       relic: glass amphora held up by two bronze arms, a horned gold lid          + red
  N3 Orbital         alien: glass sphere inside three floating steel rings, hovering base        + blue
  N4 Split shell     alien: an obsidian egg split in four and pulled apart round a glass column  + violet
  N5 Geode           living: crystal prisms erupting from a rock, gold-veined, core in the tallest + yellow
  N6 Root heart      living: roots climb from the ground and grip a glass heart, glowing buds    + indigo
"""
import colorsys, math
import numpy as np
from pixel_lanterns6 import (G, grid, circle, ngon, glass, band, stepped, rod, ring_xz, EMPTY, SMOKE, RIB, PLATE,
                             GOLD, GOLD_DK, GOLD_ENG, SILVER, VEIN, HOLE, SOCKET)
import pixel_lanterns6 as P6
import pixel_lanterns7 as P7
from pixel_lanterns7 import hollow, core, fin, studs, sculpted_port, coarsen_glass, CORE

BRONZE, STEEL, OBSID, BARK, CRYS = 13, 14, 15, 16, 17
P6.KIND.update({BRONZE: 1, STEEL: 1, OBSID: 1, BARK: 0, CRYS: 4})
P6.PAL.update({BRONZE: (150, 98, 52), STEEL: (120, 126, 136), OBSID: (14, 12, 18), BARK: (62, 40, 26), CRYS: (40, 170, 90)})

# corps colours: hue for the glass, and the core's two emission colours (linear: base, hot spots; never white)
CORPS = {"g": ("green", None, (0.02, 0.9, 0.12), (0.45, 0.92, 0.05)),
         "o": ("orange", 0.075, (1.0, 0.28, 0.0), (1.0, 0.5, 0.02)),
         "r": ("red", 0.0, (0.9, 0.02, 0.04), (1.0, 0.18, 0.02)),
         "b": ("blue", 0.6, (0.04, 0.3, 1.0), (0.1, 0.6, 1.0)),
         "v": ("violet", 0.79, (0.55, 0.04, 0.95), (0.8, 0.2, 1.0)),
         "y": ("yellow", 0.14, (1.0, 0.72, 0.0), (1.0, 0.85, 0.15)),
         "i": ("indigo", 0.7, (0.18, 0.05, 0.95), (0.35, 0.2, 1.0))}
STYLE = {"hue": None}
GLASSY = {SMOKE, RIB, PLATE, SOCKET, CORE, CRYS}

_face_colour = getattr(P6, "_orig_face_colour", P6.face_colour)
_glow_weight = getattr(P6, "_orig_glow_weight", P6.glow_weight)
P6._orig_face_colour, P6._orig_glow_weight = _face_colour, _glow_weight


def _metal(col, n, h, lip, mid_lo, mid_hi, under):
    if n[2] > 0:
        c = np.array(lip, float)
    elif n[2] < 0:
        c = np.array(under, float)
    else:
        lit = float(np.dot(np.array(n, float), P6.LIGHT))
        c = np.array(mid_lo, float) + (np.array(mid_hi, float) - np.array(mid_lo, float)) * (lit + 0.9) / 1.8
    return c * (0.94 + 0.12 * h / 255)


def face_colour(pid, i, j, k, n, c):
    h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
    if pid == BRONZE:
        if h < 12:
            return np.array([74, 150, 118.0]) * (0.85 + 0.3 * max(0.0, n[2])), 1      # verdigris
        return _metal(None, n, h, (226, 168, 96), (96, 60, 30), (182, 126, 68), (52, 32, 16)), 1
    if pid == STEEL:
        return _metal(None, n, h, (226, 232, 240), (70, 76, 86), (170, 178, 190), (34, 36, 42)), 1
    if pid == OBSID:
        return _metal(None, n, h, (70, 66, 84), (10, 9, 13), (40, 38, 50), (4, 4, 6)), 1
    if pid == BARK:
        return np.array([62, 40, 26.0]) * (0.75 + 0.45 * h / 255) * (1.15 if n[2] > 0 else 0.85 if n[2] < 0 else 1.0), 0
    if pid == CRYS:
        col = np.array([22, 110, 58.0]) * (0.8 + 0.4 * h / 255) * (1.25 if n[2] > 0 else 0.7 if n[2] < 0 else 1.0)
        kind = 4
    else:
        col, kind = _face_colour(pid, i, j, k, n, c)
    if STYLE["hue"] is not None and pid in GLASSY:
        r, g, b = (np.clip(col, 0, 255) / 255.0).tolist()
        _, s, v = colorsys.rgb_to_hsv(r, g, b)
        col = np.array(colorsys.hsv_to_rgb(STYLE["hue"], s, v)) * 255.0
    return col, kind


def glow_weight(pid, i, j, k, c, pz, span):
    if pid == CRYS:
        return 0.3 + 0.5 * math.exp(-((c[2] - pz) / (span * 0.35)) ** 2)
    if pid in (BRONZE, STEEL, OBSID, BARK):
        return 0.0
    return _glow_weight(pid, i, j, k, c, pz, span)


P6.face_colour = face_colour
P6.glow_weight = glow_weight


def tilted_ring(part, X, Y, Z, cz, R, r, tilt, turn, pid):
    """A torus of radius R round (0, 0, cz), its plane tilted by `tilt` about the axis at angle `turn` in XY."""
    t, a = math.radians(tilt), math.radians(turn)
    ca, sa = math.cos(a), math.sin(a)
    u = X * ca + Y * sa                                 # along the tilt axis
    v = -X * sa + Y * ca
    w = Z - cz
    v2, w2 = v * math.cos(t) + w * math.sin(t), -v * math.sin(t) + w * math.cos(t)
    part[np.hypot(np.hypot(u, v2) - R, w2) <= r] = pid


def sphere_glass(part, X, Y, Z, cz, R, seed):
    sec = np.hypot(np.hypot(X, Y), Z - cz) - R
    glass(part, X, Y, Z, sec, cz - R, cz + R, seed=seed, bulge_h=0.17, craze=2.6, lines=3)
    hollow(part, sec)
    return sec


# ------------------------------------------------------------------ N1 shrine (relic)
def n1_shrine(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    sq = lambda g: ngon(X, Y, 4, 4.4 + g, rnd=0.6)
    z = 0.0
    for g, h, eng in ((2.6, 0.75, None), (2.0, 0.75, "zig"), (1.4, 0.75, None), (0.9, 0.75, "dots")):   # worn steps
        band(part, X, Y, Z, sq(g), z, z + h, BRONZE, eng)
        z += h
    z0, z1 = z, z + 11.0
    sec = ngon(X, Y, 4, 3.4, rnd=0.8)
    glass(part, X, Y, Z, sec, z0, z1, seed=101, craze=2.6, lines=3)
    hollow(part, sec)
    for sx in (-1, 1):                                                     # four squat columns with capitals
        for sy in (-1, 1):
            cx, cy = sx * 4.0, sy * 4.0
            q = np.hypot(X - cx, Y - cy)
            part[(q <= 0.95) & (Z > z0) & (Z <= z1)] = BRONZE
            ang = np.arctan2(Y - cy, X - cx)
            part[(q <= 0.95) & (q > 0.65) & (Z > z0 + 0.8) & (Z <= z1 - 0.8) & (np.round(ang / (math.pi / 5)) % 2 == 0)] = GOLD_ENG
            for zc, w in ((z0 + 0.3, 1.35), (z1 - 0.3, 1.35), (z1 - 0.9, 1.15)):
                part[(np.maximum(np.abs(X - cx), np.abs(Y - cy)) <= w) & (np.abs(Z - zc) <= 0.3)] = BRONZE
    zt = z1
    band(part, X, Y, Z, sq(1.6), zt, zt + 0.75, BRONZE, "zig")             # carved architrave
    band(part, X, Y, Z, sq(1.9), zt + 0.75, zt + 1.25, BRONZE)
    zt += 1.25
    cz = zt
    for k in range(10):                                                    # dome
        rr = 5.2 * math.cos(math.asin(min(1.0, k / 10)))
        band(part, X, Y, Z, circle(X, Y, rr), zt, zt + 0.5, BRONZE if k % 4 else GOLD_DK)
        zt += 0.5
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 1.6) & (np.hypot(r, (Z - zt - 0.8) * 1.1) <= 0.9)] = GOLD
    part[(Z > zt + 1.6) & (Z <= zt + 2.6) & (r <= 0.3)] = GOLD
    studs(part, X, Y, Z, [(0, 0, zt + 2.9)], r=0.5)
    core(part, 0, 0, (z0 + z1) / 2, 2.2)
    pz = (z0 + z1) / 2
    P6.port(part, X, Y, Z, pz, pr=1.87)
    return part, pz


# ------------------------------------------------------------------ N2 reliquary (relic)
def n2_reliquary(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.0, 20.0
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = 1.6 + 3.2 * np.exp(-((H - 0.38) / 0.24) ** 2) + 0.9 * np.exp(-((H - 0.97) / 0.06) ** 2)
    sec = circle(X, Y, size)
    glass(part, X, Y, Z, sec, z0, z1, seed=102, bulge_h=0.15, craze=2.6, lines=3)
    hollow(part, sec)
    cf = lambda g: circle(X, Y, 1.6 + g)
    stepped(part, X, Y, Z, cf, z0, [(0.4, 0.5, GOLD, None), (1.4, 0.75, BRONZE, "dots"), (2.6, 0.75, BRONZE, None),
                                     (3.4, 0.5, GOLD_DK, None), (3.9, 0.75, BRONZE, "zig")], down=True)
    for sx in (-1, 1):                                                     # two arms rise from the base, hold the neck
        pts = []
        for i in range(14):
            t = i / 13
            zz = 1.2 + (z1 - 2.5 - 1.2) * t
            hh = (zz - z0) / (z1 - z0)
            rr = (1.6 + 3.2 * math.exp(-((hh - 0.38) / 0.24) ** 2)) + 0.9 + 0.8 * math.sin(math.pi * t)
            pts.append((sx * rr, 0.0, zz))
        rod(part, X, Y, Z, pts, 0.55, BRONZE)
        studs(part, X, Y, Z, [(sx * 2.2, 0.0, z1 - 2.4)], r=0.85, pid=GOLD)  # the hands round the neck
        for zc in (6.0, 11.0):
            studs(part, X, Y, Z, [(pts[int((zc - 1.2) / (z1 - 3.7) * 13)][0], 0.0, zc)], r=0.7, pid=GOLD_DK)
    zt = stepped(part, X, Y, Z, lambda g: circle(X, Y, 2.4 + g), z1, [(0.3, 0.5, GOLD, "dots"), (-0.2, 0.75, GOLD, None),
                                                                      (-1.0, 0.5, GOLD_DK, None)])
    for sx in (-1, 1):                                                     # horned crest on the lid
        pts = [(sx * 0.6, 0.0, zt), (sx * 1.6, 0.0, zt + 1.4), (sx * 2.0, 0.0, zt + 3.0), (sx * 1.6, 0.0, zt + 4.2)]
        rod(part, X, Y, Z, pts, 0.4, GOLD)
    studs(part, X, Y, Z, [(0, 0, zt + 0.6)], r=0.9, pid=GOLD)
    pz = z0 + (z1 - z0) * 0.38
    core(part, 0, 0, pz, 2.4)
    P6.port(part, X, Y, Z, pz, pr=1.95)
    return coarsen_glass(part), pz


# ------------------------------------------------------------------ N3 orbital (alien)
def n3_orbital(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    cz, R = 15.0, 4.2
    sphere_glass(part, X, Y, Z, cz, R, 103)
    tilted_ring(part, X, Y, Z, cz, 6.0, 0.4, 0, 0, STEEL)
    tilted_ring(part, X, Y, Z, cz, 6.9, 0.35, 62, 30, STEEL)
    tilted_ring(part, X, Y, Z, cz, 7.7, 0.32, -55, -40, STEEL)
    for a in range(0, 360, 60):                                            # emitter nodes on the inner ring
        ar = math.radians(a + 30)
        studs(part, X, Y, Z, [(6.0 * math.cos(ar), 6.0 * math.sin(ar), cz)], r=0.6, pid=OBSID)
    r = np.hypot(X, Y)
    part[(Z > 2.0) & (Z <= 3.0) & (r <= 4.2)] = STEEL                      # hovering base disc
    part[(Z > 3.0) & (Z <= 3.5) & (r <= 3.2) & (r > 2.6)] = CORE           # its light ring
    part[(Z > 1.0) & (Z <= 2.0) & (r <= 2.2)] = OBSID
    for k in range(3):                                                     # floating shards between base and sphere
        a = math.radians(90 + k * 120)
        studs(part, X, Y, Z, [(2.6 * math.cos(a), 2.6 * math.sin(a), 6.0 + 0.8 * k)], r=0.5, pid=STEEL)
    part[(Z > cz + R + 1.2) & (Z <= cz + R + 1.7) & (r <= 1.6) & (r > 1.0)] = STEEL   # floating crown ring
    studs(part, X, Y, Z, [(0, 0, cz + R + 2.6)], r=0.45, pid=STEEL)
    core(part, 0, 0, cz, 2.2)
    P6.port(part, X, Y, Z, cz, pr=1.70)
    return coarsen_glass(part), cz


# ------------------------------------------------------------------ N4 split shell (alien)
def n4_split(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    z0, z1 = 4.0, 22.0
    sec = circle(X, Y, 2.3)
    glass(part, X, Y, Z, sec, z0, z1, seed=104, bulge_h=0.2, craze=2.6, lines=3)
    hollow(part, sec)
    cz = (z0 + z1) / 2
    for k in range(4):                                                     # four shell quarters pulled apart
        a = math.radians(45 + 90 * k)
        ox, oy = 0.9 * math.cos(a), 0.9 * math.sin(a)
        Xs, Ys = X - ox, Y - oy
        e = np.sqrt((Xs / 5.0) ** 2 + (Ys / 5.0) ** 2 + ((Z - cz) / 9.5) ** 2)
        shell = (e <= 1.0) & (e > 0.88)
        ang = np.arctan2(Ys, Xs)
        quarter = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) < math.pi / 4 - 0.12
        part[shell & quarter & (Z > 3.0)] = OBSID
        edge = shell & quarter & (np.abs(np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) - (math.pi / 4 - 0.18)) < 0.06)
        part[edge & (Z > 3.0)] = STEEL
        part[(e <= 0.9) & (e > 0.86) & quarter & (np.abs(Z - cz) < 6.0)] = CORE   # light seam inside each quarter
    r = np.hypot(X, Y)
    part[(Z > 1.2) & (Z <= 2.2) & (r <= 3.4)] = STEEL                      # hovering caps
    part[(Z > 2.2) & (Z <= 2.6) & (r <= 2.4)] = OBSID
    part[(Z > z1 + 1.6) & (Z <= z1 + 2.4) & (r <= 2.8)] = STEEL
    part[(Z > z1 + 2.4) & (Z <= z1 + 3.4) & (r <= 0.5)] = STEEL
    studs(part, X, Y, Z, [(0, 0, z1 + 3.8)], r=0.55, pid=OBSID)
    core(part, 0, 0, cz, 1.6)
    P6.port(part, X, Y, Z, cz, pr=1.61)
    return part, cz


# ------------------------------------------------------------------ N5 geode (living crystal)
def n5_geode(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    rng = np.random.default_rng(105)
    rr = np.hypot(X, Y)
    lump = 1.0 + 0.25 * np.sin(3 * np.arctan2(Y, X)) + 0.15 * np.sin(5 * np.arctan2(Y, X) + 1)
    rock = (np.hypot(rr / (5.6 * lump), Z / 3.2) <= 1.0) & (Z > 0)
    part[rock] = OBSID
    for _ in range(26):                                                    # gold veins in the rock
        a, rad = rng.uniform(0, 2 * math.pi), rng.uniform(2.5, 5.0)
        zz = 3.0 * math.sqrt(max(0.0, 1 - (rad / 5.6) ** 2))
        studs(part, X, Y, Z, [(rad * math.cos(a), rad * math.sin(a), zz)], r=0.3, pid=GOLD)
    crystals = [(0.0, 0.0, 0.0, 17.0, 2.4)]                                 # (tilt deg, azimuth deg, base offset, length, radius)
    for k in range(7):
        crystals.append((rng.uniform(22, 48), k * 51 + rng.uniform(-12, 12), rng.uniform(1.0, 2.6), rng.uniform(6, 11),
                         rng.uniform(0.9, 1.6)))
    P = np.stack([X, Y, Z], -1)
    main_sec = None
    for idx, (tilt, az, off, L, rad) in enumerate(crystals):
        t, a = math.radians(tilt), math.radians(az)
        d = np.array([math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t)])
        b = np.array([off * math.cos(a), off * math.sin(a), 2.0])
        q = P - b
        along = q @ d
        perp = np.linalg.norm(q - along[..., None] * d, axis=-1)
        taper = np.clip((L - along) / (L * 0.28), 0, 1)                    # pointed tip over the last 28%
        rr_ = rad * taper
        inside = (along > 0) & (along < L) & (perp <= rr_)
        part[inside & (perp > rr_ - 0.55)] = CRYS
        part[inside & (perp <= rr_ - 0.55) & (part != CRYS)] = EMPTY if idx == 0 else CRYS
        if idx == 0:
            main_sec = perp - rad
    band(part, X, Y, Z, circle(X, Y, 3.2), 3.6, 4.4, GOLD, "zig")           # gold collar round the cluster
    part[(circle(X, Y, 2.4) <= 0) & (Z > 3.6) & (Z <= 4.4) & (part == GOLD)] = CRYS
    pz = 10.0
    core(part, 0, 0, pz, 1.6)
    P6.port(part, X, Y, Z, pz, pr=1.53)
    return part, pz


# ------------------------------------------------------------------ N6 root heart (living)
def n6_roots(X, Y, Z):
    part = np.zeros(X.shape, np.int8)
    cz, R = 12.5, 4.3
    sphere_glass(part, X, Y, Z, cz, R, 106)
    rng = np.random.default_rng(106)
    for k in range(5):                                                     # roots climb, twist and grip the heart
        a0 = k * 2 * math.pi / 5 + rng.uniform(-0.2, 0.2)
        if abs(math.sin(a0) + 1) < 0.08:
            a0 += 0.35                                                     # keep the port clear
        pts = []
        for i in range(22):
            t = i / 21
            zz = 0.3 + (cz + R + 3.0 - 0.3) * t
            if zz < cz - R:
                rad = 6.0 - (6.0 - (R + 0.45)) * (zz / (cz - R)) ** 0.7
            else:
                rad = (R + 0.45) * math.sqrt(max(0.0, 1 - ((zz - cz) / (R + 0.45)) ** 2)) + 0.15
            a = a0 + 0.9 * t
            if abs(((a % (2 * math.pi)) - 1.5 * math.pi)) < 0.45 and abs(zz - cz) < 2.8:
                a += 0.5                                                   # bend round the port
            pts.append((rad * math.cos(a), rad * math.sin(a), zz))
        rod(part, X, Y, Z, pts, 0.45, BARK)
        for i in (5, 11, 16):
            if rng.random() < 0.7:
                studs(part, X, Y, Z, [pts[i]], r=0.45, pid=CORE)            # glowing buds
    r = np.hypot(X, Y)
    knot = cz + R + 2.6
    studs(part, X, Y, Z, [(0, 0, knot)], r=1.2, pid=BARK)
    ring_xz(part, X, Y, Z, knot + 2.0, 1.2, 0.45, BARK, axis="y")
    part[(Z > 0) & (Z <= 0.8) & (r <= 6.6) & (r > 4.4)] = BARK             # root flare on the ground
    part[(Z > 0) & (Z <= 0.6) & (r <= 4.4)] = OBSID
    core(part, 0, 0, cz, 2.2)
    P6.port(part, X, Y, Z, cz, pr=1.70)
    return coarsen_glass(part), cz


DESIGNS_BASE = {"N1": ("Shrine", n1_shrine, "o"), "N2": ("Reliquary", n2_reliquary, "r"), "N3": ("Orbital", n3_orbital, "b"),
                "N4": ("Split shell", n4_split, "v"), "N5": ("Geode", n5_geode, "y"), "N6": ("Root heart", n6_roots, "i")}
DESIGNS = {}
for _c, (_n, _f, _corps) in DESIGNS_BASE.items():
    DESIGNS[_c + "g"] = (f"{_n}, green", _f, "g")
    DESIGNS[_c + _corps] = (f"{_n}, {CORPS[_corps][0]}", _f, _corps)


def build(code):
    X, Y, Z = grid()
    STYLE["hue"] = CORPS[DESIGNS[code][2]][1]
    return DESIGNS[code][1](X, Y, Z)


quads = P7.quads
model_boxes = P7.model_boxes
