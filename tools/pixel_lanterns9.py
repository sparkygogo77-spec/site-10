"""Pass 609: J's four 608 leads refined, 3 variations each, with the drip colour changed up across the takes.

J circled 608 D1b2 hex, D1b3 tall, D1b5 caged, D1b6 squat; next round "Refine the four"; drip colour "be creative,
change it up". Every take keeps the molten vault (glass between fluted pillars, see-through glass with the G3-flare
core, sculpted port, drips from the roof and eaves) and its lead's one big idea; each variation is built differently.

Drip styles (each take's facts line names its style):
  gold     polished gold, as in 608
  glow     bright green light leaking out (emissive, saturated)
  cool     gold at the top cooling to green as it runs down
  emerald  dark emerald with gold flecks
  jade     milky jade with a soft inner glow
"""
import math
import numpy as np
from pixel_lanterns6 import G, grid, circle, ngon, glass, band, stepped, rod, ring_xz, EMPTY, SMOKE, GOLD, GOLD_DK, SILVER
import pixel_lanterns6 as P6
import pixel_lanterns7 as P7
from pixel_lanterns7 import hollow, core, fin, bowl, studs, knuckled_arch, sculpted_port

DRIP = 12
P6.PAL[DRIP] = (214, 170, 80)
P6.KIND[DRIP] = 1
STYLE = {"name": "gold", "z": (5.0, 21.0)}

# keep P6's originals once: a module reload (607's builder reloads its voxel module) must not wrap the patch in itself
_face_colour = getattr(P6, "_orig_face_colour", P6.face_colour)
_glow_weight = getattr(P6, "_orig_glow_weight", P6.glow_weight)
P6._orig_face_colour, P6._orig_glow_weight = _face_colour, _glow_weight


def _drip_colour(n, c, h):
    st, (zlo, zhi) = STYLE["name"], STYLE["z"]
    t = float(np.clip((zhi - c[2]) / max(zhi - zlo, 1e-6), 0, 1))        # 0 at the roof, 1 at the bottom of the run
    gold = P6.gold_colour(P6.GOLD, n, c, h)
    if st == "gold":
        return gold, 1
    if st == "glow":
        return np.array([34, 236, 96.0]) * (0.9 + 0.1 * h / 255), 3
    if st == "cool":
        green = np.array([30, 196, 92.0])
        w = min(1.0, t * 1.6)
        return gold * (1 - w) + green * w, 1 if w < 0.5 else 3
    if st == "emerald":
        if h < 34:
            return np.array([246, 206, 96.0]), 1                          # gold flecks
        return np.array([10, 74, 42.0]) * (0.85 + 0.3 * max(0.0, n[2])), 1
    if st == "jade":
        return np.array([88, 178, 128.0]) * (0.9 + 0.15 * h / 255), 3
    return gold, 1


def face_colour(pid, i, j, k, n, c):
    if pid == DRIP:
        h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
        return _drip_colour(n, c, h)
    return _face_colour(pid, i, j, k, n, c)


def glow_weight(pid, i, j, k, c, pz, span):
    if pid == DRIP:
        st, (zlo, zhi) = STYLE["name"], STYLE["z"]
        t = float(np.clip((zhi - c[2]) / max(zhi - zlo, 1e-6), 0, 1))
        return {"glow": 1.7, "cool": 1.3 * min(1.0, t * 1.6) ** 2, "jade": 0.45}.get(st, 0.0)
    return _glow_weight(pid, i, j, k, c, pz, span)


P6.face_colour = face_colour
P6.glow_weight = glow_weight


def drips(part, X, Y, Z, d, ztop, n, seed, zmin, width=1.0):
    """Drips from the roof down the glass skin: a stream ending in a bead (P7's, in the DRIP part, any width)."""
    rng = np.random.default_rng(seed)
    skin = (d > 0) & (d <= G * 1.5)
    ang = np.degrees(np.arctan2(Y, X))
    rad = np.maximum(np.hypot(X, Y), 1)
    for _ in range(n):
        a = rng.uniform(-180, 180)
        if abs(((a + 90) + 180) % 360 - 180) < 35:
            continue                                                   # keep the port clear
        zb = ztop - rng.uniform(1.5, ztop - zmin)
        da = np.abs((ang - a + 180) % 360 - 180) * np.pi / 180 * rad
        part[skin & (da < G * 0.6 * width) & (Z <= ztop) & (Z > zb)] = DRIP
        part[skin & (da < G * 1.1 * width) & (Z <= zb + 0.5) & (Z > zb - 0.25)] = DRIP


def vault(X, Y, Z, n=4, s=4.6, z0=5.0, z1=21.0, seed=91, n_drips=16, drip_w=1.0, roof=None, pillar_r=0.9,
          base_extra=0.0, edge_drips=4, edge_len=1.0, rnd=1.4, eave_g=1.9, pillars=True):
    """608's molten vault (pixel_lanterns8.molten_vault) with DRIP drips and no handle; returns what the takes add to."""
    part = np.zeros(X.shape, np.int8)
    STYLE["z"] = (z0 + 1.0, z1 + 1.5)
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = s * (1 - 0.1 * np.sin(np.pi * H) ** 1.5) + 0.35 * np.exp(-((H - 0.5) / 0.12) ** 2)
    sec = ngon(X, Y, n, size, rnd=rnd if n == 4 else 0.0)
    glass(part, X, Y, Z, sec, z0, z1, seed=seed, craze=2.6, lines=4)
    hollow(part, sec)
    sh = lambda g: ngon(X, Y, n, s + g, rnd=rnd if n == 4 else 0.0)
    stepped(part, X, Y, Z, sh, z0, [(1.0, 0.5, GOLD_DK, None), (1.5 + base_extra, 0.75, GOLD, "zig"),
                                     (1.9 + base_extra, 0.5, GOLD, None), (1.4 + base_extra, 0.75, GOLD_DK, None),
                                     (2.2 + base_extra, 0.75, GOLD, "line")], down=True)
    zt = stepped(part, X, Y, Z, sh, z1, [(1.0, 0.5, GOLD_DK, None), (1.6, 0.75, GOLD, "dots"), (eave_g, 0.5, GOLD, None)])
    zr = zt
    for k, (g, h) in enumerate(roof or ((1.6, 0.75), (0.9, 0.75), (0.2, 0.75), (-0.6, 0.75), (-1.5, 0.75))):
        band(part, X, Y, Z, sh(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK, "line" if k == 1 else None)
        zt += h
    R_c = s / math.cos(math.pi / n) * 0.9
    corners = []
    for k in range(n):
        a = -math.pi / 2 + math.pi / n + k * 2 * math.pi / n
        cx, cy = R_c * math.cos(a), R_c * math.sin(a)
        corners.append((cx, cy, a))
        if not pillars:
            continue
        q = np.hypot(X - cx, Y - cy)
        pil = (q <= pillar_r) & (Z > z0 - 0.5) & (Z <= z1 + 0.5)
        part[pil] = GOLD
        ang = np.arctan2(Y - cy, X - cx)
        part[pil & (q > pillar_r - 0.3) & (np.round(ang / (math.pi / 4)) % 2 == 0)] = GOLD_DK
        for zc in (z0 + 0.6, z1 - 0.6, (z0 + z1) / 2):
            part[(q <= pillar_r + 0.25) & (np.abs(Z - zc) <= 0.3)] = GOLD
    drips(part, X, Y, Z, sec, z1 - 0.1, n_drips, seed=seed * 10, zmin=z0 + 2.0, width=drip_w)
    eave = s + eave_g
    rng = np.random.default_rng(seed + 5)
    for k in range(n):
        a = -math.pi / 2 + k * 2 * math.pi / n
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in np.linspace(-0.7, 0.7, edge_drips):
            px, py = ux * eave + tx * t * eave * math.tan(math.pi / n), uy * eave + ty * t * eave * math.tan(math.pi / n)
            ln = rng.uniform(0.8, 2.4) * edge_len
            part[(np.hypot(X - px, Y - py) <= 0.25 * drip_w) & (Z > zr - ln) & (Z <= zr + 0.5)] = DRIP
            studs(part, X, Y, Z, [(px, py, zr - ln - 0.1)], r=0.35 * drip_w, pid=DRIP)
    core(part, 0, 0, (z0 + z1) / 2, 2.8)
    pz = (z0 + z1) / 2
    sculpted_port(part, X, Y, Z, pz)
    return dict(part=part, pz=pz, sec=sec, zt=zt, zr=zr, sh=sh, corners=corners, z0=z0, z1=z1, s=s, n=n)


def finial(part, X, Y, Z, zt, ball=1.0, spike=1.5):
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 2 * ball) & (np.hypot(r, Z - zt - ball) <= ball)] = GOLD
    part[(Z > zt + 2 * ball) & (Z <= zt + 2 * ball + spike) & (r <= 0.3)] = SILVER
    return zt + 2 * ball + spike


def hang_ring(part, X, Y, Z, z, R=1.0):
    ring_xz(part, X, Y, Z, z + R, R, 0.3, GOLD, axis="y")


# ------------------------------------------------------------------ D1b2 hex x3
HEX_ROOF = ((1.6, 0.75), (0.9, 0.75), (0.2, 0.75), (-0.6, 0.75), (-1.5, 0.75), (-2.3, 0.5))


def d1b2a_onion(X, Y, Z):
    """Hex with an onion dome: the roof swells out, then narrows to a finial; green light leaks down as the drips."""
    STYLE["name"] = "glow"
    v = vault(X, Y, Z, n=6, s=4.8, seed=921, n_drips=18, edge_drips=3, roof=((1.6, 0.75), (0.9, 0.5)))
    part, zt = v["part"], v["zt"]
    for k in range(12):                                                  # onion: radius swells then tapers
        h = k / 11
        g = 0.4 + 1.6 * math.sin(math.pi * min(1, h * 1.4)) * (1 - h) - 3.0 * h
        band(part, X, Y, Z, v["sh"](g), zt, zt + 0.5, GOLD if k % 3 else GOLD_DK, "dots" if k == 4 else None)
        zt += 0.5
    hang_ring(part, X, Y, Z, finial(part, X, Y, Z, zt, ball=0.7, spike=1.0))
    return part, v["pz"]


def d1b2b_lancet(X, Y, Z):
    """Hex with a gold lancet arch over each panel and a double belt; the drips run gold and cool to green."""
    STYLE["name"] = "cool"
    v = vault(X, Y, Z, n=6, s=4.8, seed=922, n_drips=16, edge_drips=3, roof=HEX_ROOF)
    part, z0, z1, s = v["part"], v["z0"], v["z1"], v["s"]
    ang = np.arctan2(Y, X)
    for k in range(6):                                                   # pointed arch on each panel's skin
        a = -math.pi / 2 + k * math.pi / 3
        if k == 0:
            continue                                                     # the port's panel stays clear
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        u = X * tx + Y * ty
        w = s * math.tan(math.pi / 6) * 0.8
        top = z1 - 1.0 - np.sqrt(np.clip(w * w - u * u, 0, None)) * 0.0
        spring = z1 - 4.0
        arch = spring + (w - np.abs(u)) * 1.4
        on = (np.abs(X * ux + Y * uy - (s + 0.2)) <= 0.35) & (np.abs(u) <= w)
        part[on & (np.abs(Z - arch) <= 0.35) & (Z <= top + 2)] = GOLD
        part[on & (np.abs(np.abs(u) - w) <= 0.3) & (Z > z0 + 1.0) & (Z <= spring)] = GOLD
    for zc in (z0 + 4.0, z0 + 4.8):
        part[(np.abs(Z - zc) <= 0.25) & (v["sec"] > -G) & (v["sec"] <= 0.55) & (np.abs(X) > 2.8)] = GOLD_DK
    knuckled_arch(part, X, Y, Z, v["zt"] - 0.5, 2.8, 3.6)
    return part, v["pz"]


def d1b2c_skirt(X, Y, Z):
    """Hex on a wide flared skirt with buttress fins between the back pillars; dark emerald drips with gold flecks."""
    STYLE["name"] = "emerald"
    v = vault(X, Y, Z, n=6, s=4.6, seed=923, n_drips=20, drip_w=1.2, edge_drips=4, roof=HEX_ROOF, base_extra=0.8)
    part, z0 = v["part"], v["z0"]
    sk = lambda g: ngon(X, Y, 6, 4.6 + g)
    for k, (g, h) in enumerate(((3.6, 0.5), (4.2, 0.5), (4.8, 0.75))):  # flared skirt under the base
        band(part, X, Y, Z, sk(g), z0 - 3.25 - 0.5 * k - h, z0 - 3.25 - 0.5 * k, GOLD if k % 2 == 0 else GOLD_DK)
    for cx, cy, a in v["corners"]:
        if math.sin(a) < -0.2:
            continue                                                     # front corners stay clear
        ux, uy = math.cos(a), math.sin(a)
        fin(part, X, Y, Z, [(cx, cy, z0 - 1.0), (cx, cy, z0 + 7.0)],
            [(cx + ux * 2.4, cy + uy * 2.4, z0 - 1.0), (cx + ux * 0.6, cy + uy * 0.6, z0 + 8.0)], th=0.28, n=10)
    hang_ring(part, X, Y, Z, finial(part, X, Y, Z, v["zt"], ball=0.8, spike=0.8))
    return part, v["pz"]


# ------------------------------------------------------------------ D1b3 tall x3
TALL = dict(s=3.9, z0=4.5, z1=24.0, n_drips=18, edge_len=1.3)


def crown(part, X, Y, Z, zt, n=8, r0=2.0, h=1.6, alt=0.6):
    for k in range(n):
        a = k * 2 * math.pi / n
        rod(part, X, Y, Z, [(r0 * math.cos(a), r0 * math.sin(a), zt), ((r0 + 0.5) * math.cos(a), (r0 + 0.5) * math.sin(a),
                                                                          zt + h + alt * (k % 2))], 0.3)
    part[(Z > zt) & (Z <= zt + 2.0) & (np.hypot(X, Y) <= 0.8)] = GOLD_DK


def d1b3a_belted(X, Y, Z):
    """Tall vault split by a wide engraved gold belt at mid height, a taller spiked crown; milky jade drips."""
    STYLE["name"] = "jade"
    v = vault(X, Y, Z, seed=931, roof=((1.6, 0.75), (0.8, 0.5), (1.2, 0.5), (0.2, 0.75), (-0.6, 0.75), (-1.4, 0.5)), **TALL)
    part, zm = v["part"], (v["z0"] + v["z1"]) / 2 + 3.5
    band(part, X, Y, Z, v["sh"](1.0), zm - 0.75, zm + 0.75, GOLD, "zig")
    part[(v["sh"](0.2) <= 0) & (np.abs(Z - zm) <= 0.75) & (part == GOLD) & (np.hypot(X, Y) < 3.0)] = EMPTY
    crown(part, X, Y, Z, v["zt"], n=10, h=2.2, alt=0.9)
    hang_ring(part, X, Y, Z, v["zt"] + 3.4)
    return part, v["pz"]


def d1b3b_spire(X, Y, Z):
    """Tall vault under a stepped spire that narrows to a point; bright green light leaking down as drips."""
    STYLE["name"] = "glow"
    v = vault(X, Y, Z, seed=932, roof=((1.6, 0.75), (0.8, 0.5)), **TALL)
    part, zt = v["part"], v["zt"]
    for k in range(10):
        band(part, X, Y, Z, v["sh"](0.6 - 0.48 * k), zt, zt + 0.5, GOLD if k % 2 == 0 else GOLD_DK, "dots" if k == 2 else None)
        zt += 0.5
    r = np.hypot(X, Y)
    part[(Z > zt) & (Z <= zt + 2.5) & (r <= 0.45 * (1 - (Z - zt) / 2.6))] = GOLD
    for cx, cy, a in v["corners"]:                                       # pinnacles at the roof's corners
        px, py = cx * 1.25, cy * 1.25
        part[(np.hypot(X - px, Y - py) <= 0.45 * np.clip(1 - (Z - v["zr"]) / 2.5, 0, 1)) & (Z > v["zr"]) & (Z <= v["zr"] + 2.5)] = GOLD
    hang_ring(part, X, Y, Z, zt + 2.0, R=0.8)
    return part, v["pz"]


def d1b3c_twin(X, Y, Z):
    """Two stacked glass chambers in one tall vault, a gold floor between them, a spiked crown; polished gold drips."""
    STYLE["name"] = "gold"
    v = vault(X, Y, Z, seed=933, roof=((1.6, 0.75), (0.8, 0.5), (1.2, 0.5), (0.2, 0.75), (-0.6, 0.75), (-1.4, 0.5)), **TALL)
    part, z0, z1 = v["part"], v["z0"], v["z1"]
    zm = z0 + (z1 - z0) * 0.62
    stepped(part, X, Y, Z, v["sh"], zm - 0.6, [(0.4, 0.5, GOLD_DK, None), (1.4, 0.75, GOLD, "dots"), (0.4, 0.5, GOLD_DK, None)])
    part[(v["sh"](-0.8) <= 0) & (np.abs(Z - (zm + 0.5)) <= 1.0) & np.isin(part, [GOLD, GOLD_DK, P6.GOLD_ENG])] = EMPTY
    core(part, 0, 0, zm + 3.4, 1.6)
    crown(part, X, Y, Z, v["zt"])
    hang_ring(part, X, Y, Z, v["zt"] + 3.0)
    return part, v["pz"]


# ------------------------------------------------------------------ D1b5 caged x3
def cage_bars(part, X, Y, Z, z0, z1, off=5.9, ts=(-2.2, -0.9, 0.9, 2.2), r=0.3, pid=GOLD, catch=True):
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in ts:
            if k == 0 and abs(t) < 1.5:
                continue
            px, py = ux * off + tx * t, uy * off + ty * t
            part[(np.hypot(X - px, Y - py) <= r) & (Z > z0) & (Z <= z1)] = pid
            if catch:
                studs(part, X, Y, Z, [(px, py, z0 + 5 + 3 * ((k + int(t * 10)) % 3))], r=0.42, pid=DRIP)


def d1b5a_lattice(X, Y, Z):
    """The cage as a diagonal lattice of gold bars crossing a pixel off the glass; drips cool from gold to green."""
    STYLE["name"] = "cool"
    v = vault(X, Y, Z, seed=951, n_drips=12, pillar_r=1.0)
    part, z0, z1 = v["part"], v["z0"], v["z1"]
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        u = X * tx + Y * ty
        w = (X * ux + Y * uy) - 5.9
        on = (np.abs(w) <= 0.3) & (np.abs(u) <= 3.0) & (Z > z0) & (Z <= z1)
        if k == 0:
            on &= ~((np.abs(u) < 2.9) & (np.abs(Z - v["pz"]) < 3.0))
        diag = (np.abs(((u + Z) % 3.0) - 1.5) <= 0.3) | (np.abs(((u - Z) % 3.0) - 1.5) <= 0.3)
        part[on & diag] = GOLD
    knuckled_arch(part, X, Y, Z, v["zt"] - 0.5, 2.8, 3.6, y=-0.5)
    knuckled_arch(part, X, Y, Z, v["zt"] - 0.5, 2.8, 3.6, y=0.5)
    return part, v["pz"]


def d1b5b_domed(X, Y, Z):
    """Cage bars that carry on up and arch over the roof to meet at a crown ring; green light drips."""
    STYLE["name"] = "glow"
    v = vault(X, Y, Z, seed=952, n_drips=14, pillar_r=1.0)
    part, z0, z1, zt = v["part"], v["z0"], v["z1"], v["zt"]
    cage_bars(part, X, Y, Z, z0, z1 + 1.8)
    for k in range(4):                                                   # arches over the roof
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in (-2.2, 2.2):
            p0 = (ux * 5.9 + tx * t, uy * 5.9 + ty * t, z1 + 1.8)
            pts = [p0] + [(p0[0] * (1 - f), p0[1] * (1 - f), z1 + 1.8 + (zt + 2.0 - z1 - 1.8) * math.sin(f * math.pi / 2))
                          for f in np.linspace(0.1, 0.85, 8)]
            rod(part, X, Y, Z, pts, 0.3)
    ring_xz(part, X, Y, Z, zt + 2.0, 1.2, 0.35, GOLD, axis="z")
    hang_ring(part, X, Y, Z, zt + 2.3, R=1.0)
    return part, v["pz"]


def d1b5c_heavy(X, Y, Z):
    """A heavier cage: thick square bars with rivets at every crossing of two cage belts; dark emerald drips, gold flecks."""
    STYLE["name"] = "emerald"
    v = vault(X, Y, Z, seed=953, n_drips=14, pillar_r=1.1, drip_w=1.2)
    part, z0, z1 = v["part"], v["z0"], v["z1"]
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in (-2.3, -0.8, 0.8, 2.3):
            if k == 0 and abs(t) < 1.5:
                continue
            px, py = ux * 6.0 + tx * t, uy * 6.0 + ty * t
            part[(np.maximum(np.abs(X - px), np.abs(Y - py)) <= 0.4) & (Z > z0) & (Z <= z1)] = GOLD
            for zc in (z0 + 4.0, z1 - 4.0):
                studs(part, X, Y, Z, [(px + ux * 0.5, py + uy * 0.5, zc)], r=0.45, pid=SILVER)
        for zc in (z0 + 4.0, z1 - 4.0):
            on = (np.abs(X * ux + Y * uy - 6.0) <= 0.35) & (np.abs(X * tx + Y * ty) <= 2.7) & (np.abs(Z - zc) <= 0.35)
            if k == 0:
                on &= np.abs(X) > 2.8
            part[on] = GOLD_DK
    knuckled_arch(part, X, Y, Z, v["zt"] - 0.5, 2.8, 3.6, n_knuckle=9, r=0.38)
    return part, v["pz"]


# ------------------------------------------------------------------ D1b6 squat x3
SQUAT = dict(s=5.6, z0=6.0, z1=17.0, n_drips=18, edge_drips=5, edge_len=1.25, base_extra=0.4)
SQUAT_ROOF = ((2.4, 0.5), (1.8, 0.75), (0.9, 0.75), (0.0, 0.75), (-1.0, 0.75), (-2.0, 0.75), (-3.0, 0.5))


def d1b6a_claw(X, Y, Z):
    """Squat vault on four curled claw feet; polished gold drips."""
    STYLE["name"] = "gold"
    v = vault(X, Y, Z, seed=961, roof=SQUAT_ROOF, **SQUAT)
    part = v["part"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            ux, uy = sx / math.sqrt(2), sy / math.sqrt(2)
            pts = [(sx * 5.0, sy * 5.0, 2.5), (sx * 5.8, sy * 5.8, 1.6), (sx * 6.6, sy * 6.6, 0.6), (sx * 7.3, sy * 7.3, 0.4)]
            rod(part, X, Y, Z, pts, 0.6)
            for dt in (-0.7, 0.0, 0.7):                                  # three toes
                tx, ty = -uy * dt, ux * dt
                studs(part, X, Y, Z, [(sx * 7.5 + tx, sy * 7.5 + ty, 0.35)], r=0.4)
    hang_ring(part, X, Y, Z, finial(part, X, Y, Z, v["zt"], ball=0.8, spike=0.6))
    return part, v["pz"]


def d1b6b_pagoda(X, Y, Z):
    """Squat pagoda: two stacked dripping eaves roofs with a short glass drum between; drips cool from gold to green."""
    STYLE["name"] = "cool"
    v = vault(X, Y, Z, seed=962, roof=((2.4, 0.5), (1.8, 0.75), (0.9, 0.5)), **SQUAT)
    part, zt = v["part"], v["zt"]
    drum = ngon(X, Y, 4, 2.6, rnd=1.0)
    part[(drum <= 0) & (drum > -0.5) & (Z > zt) & (Z <= zt + 2.0)] = GOLD_DK
    part[(drum <= 0) & (drum > -0.5) & (Z > zt + 0.5) & (Z <= zt + 1.5) & (np.abs(X) < 1.2)] = P6.PLATE
    zt += 2.0
    sh2 = lambda g: ngon(X, Y, 4, 2.8 + g, rnd=1.2)
    for k, (g, h) in enumerate(((2.6, 0.5), (1.8, 0.5), (0.9, 0.5), (0.0, 0.5), (-0.9, 0.5), (-1.7, 0.5))):
        band(part, X, Y, Z, sh2(g), zt, zt + h, GOLD if k % 2 == 0 else GOLD_DK)
        zt += h
    rng = np.random.default_rng(9621)
    for k in range(4):                                                   # drips off the upper eaves
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        tx, ty = -uy, ux
        for t in (-0.6, 0.0, 0.6):
            px, py = ux * 5.2 + tx * t * 5.2, uy * 5.2 + ty * t * 5.2
            ln = rng.uniform(0.6, 1.6)
            z_e = zt - 3.0
            part[(np.hypot(X - px, Y - py) <= 0.25) & (Z > z_e - ln) & (Z <= z_e + 0.5)] = DRIP
            studs(part, X, Y, Z, [(px, py, z_e - ln - 0.1)], r=0.35, pid=DRIP)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = np.hypot(X - sx * 5.6, Y - sy * 5.6)
            part[(q <= 1.0) & (Z > 0.5) & (Z <= 2.4)] = GOLD
            part[(q <= 1.3) & (Z > 0.0) & (Z <= 0.5)] = GOLD_DK
    hang_ring(part, X, Y, Z, finial(part, X, Y, Z, zt, ball=0.6, spike=0.6), R=0.8)
    return part, v["pz"]


def d1b6c_fringe(X, Y, Z):
    """Squat vault with wide flat eaves hung with a fringe of beaded drips all round, short feet; milky jade drips."""
    STYLE["name"] = "jade"
    v = vault(X, Y, Z, seed=963, roof=((3.2, 0.5), (2.4, 0.5), (1.2, 0.75), (0.2, 0.75), (-1.0, 0.75), (-2.2, 0.75)),
              eave_g=2.6, edge_drips=8, edge_len=0.9, **{k: v_ for k, v_ in SQUAT.items() if k not in ("edge_drips", "edge_len")})
    part = v["part"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = np.hypot(X - sx * 5.6, Y - sy * 5.6)
            part[(q <= 1.1) & (Z > 0.0) & (Z <= 2.4)] = GOLD
            part[(q <= 1.4) & (Z > 2.0) & (Z <= 2.4)] = GOLD_DK
    knuckled_arch(part, X, Y, Z, v["zt"] - 0.5, 3.2, 3.0, n_knuckle=7)
    return part, v["pz"]


DESIGNS = {"D1b2a": ("Hex: onion dome", d1b2a_onion, "glow"), "D1b2b": ("Hex: lancet arches", d1b2b_lancet, "cool"),
           "D1b2c": ("Hex: flared skirt", d1b2c_skirt, "emerald"),
           "D1b3a": ("Tall: belted", d1b3a_belted, "jade"), "D1b3b": ("Tall: spire", d1b3b_spire, "glow"),
           "D1b3c": ("Tall: twin chamber", d1b3c_twin, "gold"),
           "D1b5a": ("Caged: lattice", d1b5a_lattice, "cool"), "D1b5b": ("Caged: domed", d1b5b_domed, "glow"),
           "D1b5c": ("Caged: heavy bars", d1b5c_heavy, "emerald"),
           "D1b6a": ("Squat: claw feet", d1b6a_claw, "gold"), "D1b6b": ("Squat: pagoda", d1b6b_pagoda, "cool"),
           "D1b6c": ("Squat: fringe", d1b6c_fringe, "jade")}
DRIP_NAMES = {"gold": "polished gold", "glow": "bright green light", "cool": "gold cooling to green",
              "emerald": "dark emerald with gold flecks", "jade": "milky jade with a soft glow"}


def build(code):
    X, Y, Z = grid()
    STYLE["name"] = DESIGNS[code][2]
    return DESIGNS[code][1](X, Y, Z)


def quads(part, pz):
    return P7.quads(part, pz)        # STYLE stays set from build() until the next build


model_boxes = P7.model_boxes
