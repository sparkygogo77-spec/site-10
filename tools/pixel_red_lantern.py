"""The Red Lantern on Minecraft's pixel grid: three versions for J to pick from.

Same method as the Dark Lantern (pixel_dark_lantern4.py): a 0.25-unit voxel grid (one cube = one
texture pixel, 64 per block), shapes from signed distances, every detail placed pixel by pixel.
Identity kept from the reference sheet (#18): a tall copper cylinder with dark red veined glass,
copper bands top and bottom, the round Red Lantern Corps emblem port on the front and a ring handle.

- r1 "refined": the sheet's lantern, cleaned up. Round barrel of glass split into panels by six copper
  struts, riveted bands, a stepped foot, a grilled cap, two rods tied to the emblem housing, a ring.
- r2 "rage": meaner. Octagonal glass that widens toward the shoulders, copper jaws biting the glass
  top and bottom (fangs), a spiked crown, claw feet, a spiked bezel round a bigger emblem, and the
  glass shattered into shards with hot cracks.
- r3 "bleeding": a different glass. Smooth bulged glass with blood running down inside it from the
  top collar in drip lines that end in drops, a glowing heart behind the emblem, an open copper cage
  of four bowed bars, blood spilling over the foot, and a double ring.

    python tools/pixel_red_lantern.py <out dir>

Writes red_<version>.npz with quads (N,4,3), col (N,3 srgb 0-255), kind (N: 0 matte, 1 metal,
3 glinting fleck, 4 glass body, 5 vein) and glow (N, 0..1). Units 1/16 block, x right, y back
(front faces -y), z up.
"""
import math, os, sys
import numpy as np

G = 0.25
LIGHT = np.array([-0.45, -0.75, 0.6]); LIGHT /= np.linalg.norm(LIGHT)

# ---- palette (srgb) ---------------------------------------------------------------------------
COPPER = (196, 104, 56)
COPPER_DK = (112, 52, 26)
COPPER_HI = (236, 160, 104)
RUST = (92, 40, 22)
BRONZE = (150, 96, 50)
GLASS = (58, 6, 10)
GLASS_LT = (84, 10, 16)
VEIN = (186, 18, 22)
VEIN_HOT = (232, 52, 30)
SIGIL = (226, 28, 30)
FIELD = (22, 5, 5)
HOLE = (12, 6, 5)
BLOOD = (128, 6, 12)

# the Red Lantern emblem inside its ring, 14 x 16 pixels, top row first: a lantern with a handle,
# a domed cap, a hollow body round a blood drop, and a stem that drips through the ring
GLYPH = """
......##......
.....#..#.....
......##......
...########...
..##########..
..##......##..
..##..##..##..
..##.####.##..
..##.####.##..
..##..##..##..
..##......##..
..##########..
...########...
......##......
......##......
......##......
"""
GLYPH = np.array([[ch == "#" for ch in row] for row in GLYPH.strip().splitlines()])


# ---- noise ------------------------------------------------------------------------------------
def vnoise(P, seed, n=32):
    """Smooth 3D value noise in -1..1 (trilinear over a random lattice, smoothstep weights)."""
    lat = np.random.default_rng(seed).uniform(-1, 1, (n, n, n))
    g = np.floor(P).astype(int)
    f = P - g
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (np.where(dx, f[..., 0], 1 - f[..., 0]) * np.where(dy, f[..., 1], 1 - f[..., 1])
                     * np.where(dz, f[..., 2], 1 - f[..., 2]))
                out = out + w * lat[(g[..., 0] + dx) % n, (g[..., 1] + dy) % n, (g[..., 2] + dz) % n]
    return out


def fbm(P, seed, octaves=3):
    s, a, t = 1.0, 1.0, 0
    for o in range(octaves):
        t = t + a * vnoise(P * s, seed + o)
        s *= 2.03; a *= 0.5
    return t / (2 - 2 ** (1 - octaves))


def vor3(P, cell, seed):
    """Distance to the nearest border of a jittered 3D cell grid, and each point's cell id."""
    jit = np.random.default_rng(seed).random((32, 32, 32, 3))
    g = np.floor(P / cell).astype(int)
    d0 = np.full(P.shape[:-1], 1e9); d1 = d0.copy(); ident = np.zeros(P.shape[:-1], int)
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            for oz in (-1, 0, 1):
                c = g + np.array([ox, oy, oz])
                j = jit[c[..., 0] % 32, c[..., 1] % 32, c[..., 2] % 32]
                d = np.linalg.norm(P - (c + j) * cell, axis=-1)
                closer = d < d0
                d1 = np.where(closer, d0, np.minimum(d1, d))
                ident = np.where(closer, (c[..., 0] % 32) * 1024 + (c[..., 1] % 32) * 32 + c[..., 2] % 32, ident)
                d0 = np.where(closer, d, d0)
    return (d1 - d0) / 2, ident


# ---- the canvas: a colour, kind and glow per voxel ------------------------------------------------
class Canvas:
    def __init__(self, half=9.0, top=31.0):
        self.xs = np.arange(-half, half, G) + G / 2
        self.zs = np.arange(0, top, G) + G / 2
        self.X, self.Y, self.Z = np.meshgrid(self.xs, self.xs, self.zs, indexing="ij")
        self.occ = np.zeros(self.X.shape, bool)
        self.col = np.zeros(self.X.shape + (3,), np.float32)
        self.kind = np.zeros(self.X.shape, np.int8)
        self.glow = np.zeros(self.X.shape, np.float32)
        i, j, k = np.indices(self.X.shape)
        self.hash = (((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 1023) / 1023.0
        self.metal = np.zeros(self.X.shape, bool)

    def put(self, m, col, kind, glow=0.0, jitter=0.12):
        col = np.asarray(col, np.float32)
        self.occ[m] = True
        self.col[m] = col * (1 - jitter / 2 + jitter * self.hash[m])[:, None]
        self.kind[m] = kind
        self.glow[m] = glow if np.isscalar(glow) else glow[m]
        self.metal[m] = kind in (1, 3)

    def clear(self, m):
        self.occ[m] = False

    def recolour(self, m, col, kind=None, glow=None, jitter=0.12):
        m = m & self.occ
        self.col[m] = np.asarray(col, np.float32) * (1 - jitter / 2 + jitter * self.hash[m])[:, None]
        if kind is not None:
            self.kind[m] = kind
            self.metal[m] = kind in (1, 3)
        if glow is not None:
            self.glow[m] = glow if np.isscalar(glow) else glow[m]

    def quads(self):
        occ = self.occ
        pad = np.pad(occ, 1)
        Q, C, K, W = [], [], [], []
        for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            nb = pad[1 + n[0]:pad.shape[0] - 1 + n[0], 1 + n[1]:pad.shape[1] - 1 + n[1], 1 + n[2]:pad.shape[2] - 1 + n[2]]
            idx = np.argwhere(occ & ~nb)
            i, j, k = idx.T
            c = np.stack([self.xs[i], self.xs[j], self.zs[k]], -1)
            nv = np.array(n, float)
            a = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            b = np.cross(nv, a)
            f0 = c + nv * G / 2
            cs = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1][0] - cs[0][0], cs[2][0] - cs[0][0]), nv) < 0:
                cs = cs[::-1]
            Q.append(np.stack(cs, 1))
            col = self.col[i, j, k].astype(float)
            shade = 0.62 + 0.5 * max(0.0, float(nv @ LIGHT))
            met = self.metal[i, j, k]
            if n[2] > 0:
                col = np.where(met[:, None], col * 1.22, col * 1.08)      # lit upper lips
            elif n[2] < 0:
                col = np.where(met[:, None], col * 0.72, col)
            C.append(np.clip(col * shade, 0, 255))
            K.append(self.kind[i, j, k])
            W.append(self.glow[i, j, k])
        return (np.concatenate(Q).astype(np.float32), np.concatenate(C).astype(np.float32),
                np.concatenate(K).astype(np.int8), np.concatenate(W).astype(np.float32))


# ---- shapes -----------------------------------------------------------------------------------
def radial(cv, p):
    """The cross-section distance measure: a circle, or an octagon with flat front (apothem)."""
    X, Y = cv.X, cv.Y
    if p.get("octagon"):
        ax, ay = np.abs(X), np.abs(Y)
        return np.maximum(np.maximum(ax, ay), (ax + ay) / math.sqrt(2))
    return np.hypot(X, Y)


def ang_front(cv):
    """Angle round the body, 0 at the front (-y), positive toward +x."""
    return np.arctan2(cv.X, -cv.Y)


def wrapd(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def copper(cv, m, p, kind=1, dark=False, glints=0.0):
    """Copper with rust spots and the odd glinting fleck."""
    base = COPPER_DK if dark else COPPER
    cv.put(m, base, kind)
    if p.get("rust", 0) > 0:
        P = np.stack([cv.X, cv.Y, cv.Z], -1) * 0.9
        rust = (fbm(P, p["seed"] + 7, 2) > 1 - p["rust"]) & m
        cv.recolour(rust, RUST, 0)
    if glints:
        cv.recolour(m & (cv.hash < glints), COPPER_HI, 3)


def ring_band(cv, p, z0, z1, R, dark=False, rivets=0, rivet_phase=0.0):
    """A copper band round the body at radius R (or octagon apothem), with an upper highlight row
    and rivets a pixel proud."""
    r = radial(cv, p)
    m = (cv.Z > z0) & (cv.Z <= z1) & (r <= R)
    copper(cv, m, p, dark=dark)
    edge = m & (r > R - G) & ((cv.Z > z1 - G) | (cv.Z <= z0 + G))
    cv.recolour(edge & (cv.Z > z1 - G), COPPER_HI, 1)
    cv.recolour(edge & (cv.Z <= z0 + G), COPPER_DK, 1)
    if rivets:
        zc = (z0 + z1) / 2
        a = ang_front(cv)
        for i in range(rivets):
            t = rivet_phase + 2 * np.pi * i / rivets
            ad = np.abs(wrapd(a - t)) * R
            rv = (ad < 0.3) & (np.abs(cv.Z - zc) < 0.3) & (r > R) & (r <= R + G)
            cv.put(rv, COPPER_HI, 3 if i % 3 == 0 else 1)


def handle_ring(cv, zc, Rm, rt, col=COPPER, square=False, yoff=0.0):
    """A ring loop standing in the x-z plane (front view shows the full ring)."""
    d = np.hypot(cv.X, cv.Z - zc) - Rm
    if square:
        m = (np.abs(d) <= rt) & (np.abs(cv.Y - yoff) <= rt)
    else:
        m = np.hypot(d, cv.Y - yoff) <= rt
    cv.put(m, col, 1)
    # highlight the outer upper rim, shade the inner
    cv.recolour(m & (d > rt * 0.4) & (cv.Z > zc), COPPER_HI, 1)
    cv.recolour(m & (d < -rt * 0.4), COPPER_DK, 1)
    return m


def emblem(cv, p, pz, fy):
    """The Red Lantern Corps emblem port on the front. `fy` is the glass's front y at pz. The face
    plane (the bezel's front) stands `port_out` in front of the glass. Laid out in pixels:
    the field is a disc of radius 8.6 px, the symbol ring 8.6..10.6, the copper bezel out to Rh."""
    X, Y, Z = cv.X, cv.Y, cv.Z
    s = p.get("port_scale", 1.0)
    rpx = np.hypot(X, Z - pz) / G / s
    ye = round((fy - p["port_out"]) / G) * G           # the face plane, on the grid
    back = fy + 1.5
    Rh = p.get("bezel_px", 13.5)
    house = (rpx <= Rh) & (Y >= ye) & (Y <= back)
    copper(cv, house, p, dark=True)
    # the bezel: a pixel proud, knurled on its inner edge, bevelled at its rim
    bez = (rpx <= Rh) & (rpx > 10.6) & (Y >= ye - G) & (Y < ye)
    cv.put(bez, COPPER, 1)
    cv.recolour(bez & (rpx > Rh - 1) & (Z > pz), COPPER_HI, 1)
    knurl = bez & (rpx <= 11.8) & ((np.floor((np.arctan2(X, Z - pz) + np.pi) / (2 * np.pi) * 40) % 2) == 0)
    cv.recolour(knurl, COPPER_DK, 1)
    # rivets on the diagonals
    for k in range(p.get("bezel_rivets", 4)):
        t = np.pi / 4 + k * 2 * np.pi / p.get("bezel_rivets", 4)
        rx, rz = math.sin(t) * (Rh - 1.4) * G * s, math.cos(t) * (Rh - 1.4) * G * s
        rv = (np.hypot(X - rx, Z - pz - rz) <= 0.3) & (Y >= ye - 2 * G) & (Y < ye - G)
        cv.put(rv, COPPER_HI, 3)
    # spikes round the bezel (r2): little triangles pointing out
    for k in range(p.get("bezel_spikes", 0)):
        t = 2 * np.pi * (k + 0.5) / p["bezel_spikes"]
        u = (X * math.sin(t) + (Z - pz) * math.cos(t)) / G / s - Rh       # outward from the rim
        v = np.abs(X * math.cos(t) - (Z - pz) * math.sin(t)) / G / s       # sideways
        sp = (u > -1) & (u <= p["spike_len"]) & (v <= (p["spike_len"] - u) * 0.55) & (Y >= ye - G) & (Y <= back)
        cv.put(sp, COPPER, 1)
        cv.recolour(sp & (u > p["spike_len"] - 2), COPPER_HI, 1)
    # the field: recessed a pixel, near black with a faint red lens behind
    field = (rpx < 8.6) & (Y >= ye) & (Y <= back)
    cv.put(field, FIELD, 0, jitter=0.2)
    cv.clear((rpx < 8.6) & (Y >= ye) & (Y < ye + G))
    lens = (rpx < 8.6) & (Y >= ye + G) & (Y < ye + 2 * G)
    cv.recolour(lens & (rpx > 7.2), (60, 6, 8), 4, glow=0.35)
    # the symbol ring and the lantern glyph, flush with the face plane, blazing red
    ring = (rpx >= 8.6) & (rpx <= 10.6) & (Y >= ye) & (Y < ye + 2 * G)
    cv.put(ring, SIGIL, 5, glow=1.0, jitter=0.08)
    col_i = np.floor(X / (G * s)).astype(int) + 7
    row_i = 7 - np.floor((Z - pz) / (G * s)).astype(int)
    ok = (col_i >= 0) & (col_i < 14) & (row_i >= 0) & (row_i < 16)
    gl = np.zeros(X.shape, bool)
    gl[ok] = GLYPH[row_i[ok], col_i[ok]]
    sym = gl & (rpx < 8.6) & (Y >= ye) & (Y < ye + 2 * G)
    cv.put(sym, SIGIL, 5, glow=1.0, jitter=0.08)
    # the drop inside the lantern burns hotter
    hot = sym & (np.abs(X) < 1.0 * G * s + 1e-6) & (np.abs(Z - pz) < 1.6 * G * s)
    cv.recolour(hot, VEIN_HOT, 5, glow=1.0, jitter=0.05)
    # blood drips under the ring, running down the bezel
    for dx, ln in p.get("emblem_drips", ((-3, 3), (0, 5), (2, 2))):
        x0 = (dx + 0.5) * G * s
        zt = pz - 10.6 * G * s
        dr = (np.abs(X - x0) < G * 0.6 * s) & (Z <= zt) & (Z > zt - ln * G) & (Y >= ye - 2 * G) & (Y < ye)
        tip = (np.abs(X - x0) < G * 1.1 * s) & (Z <= zt - (ln - 1) * G) & (Z > zt - (ln + 1) * G) & (Y >= ye - 2 * G) & (Y < ye) \
            & (np.abs(X - x0) + np.abs(Z - (zt - ln * G)) < G * 1.4)
        cv.put(dr | tip, BLOOD, 5, glow=0.55, jitter=0.1)
    return ye


# ---- the glass --------------------------------------------------------------------------------
def glass_fill(cv, p, m, shell, pz, z0, z1):
    """Fill the glass and paint its veins on the outer shell (one pixel deep). Glow weight is
    strongest round the emblem's height and eases toward the bands."""
    X, Y, Z = cv.X, cv.Y, cv.Z
    zmid = p.get("heart_z", pz)
    span = (z1 - z0) * p.get("glow_span", 0.45)
    g = 0.35 + 0.65 * np.exp(-((Z - zmid) / span) ** 2)
    cv.put(m, GLASS, 4, glow=g * 0.55, jitter=0.25)
    P = np.stack([X, Y, Z], -1)
    style = p["veins"]
    if style == "marble":
        # ridged noise: meandering, branching blood veins, thick main runs and fine capillaries
        n1 = fbm(P * 0.42 + np.array([0, 0, 0.0]), p["seed"], 3)
        n2 = fbm(P * 0.9 + 13.0, p["seed"] + 20, 2)
        main = shell & (np.abs(n1) < 0.045)
        fine = shell & (np.abs(n2) < 0.035) & ~main
        cloud = shell & (fbm(P * 0.3 + 5, p["seed"] + 40, 2) > 0.25)
        cv.recolour(cloud, GLASS_LT, 4, glow=g * 0.75, jitter=0.25)
        cv.recolour(fine, (130, 12, 18), 5, glow=g * 0.6, jitter=0.2)
        cv.recolour(main, VEIN, 5, glow=g * (0.8 + 0.2 * cv.hash), jitter=0.15)
        cv.recolour(main & (cv.hash < 0.06), VEIN_HOT, 3, glow=g)
    elif style == "shards":
        # shattered glass: each shard a slightly different red, hot cracks between them
        border, ident = vor3(P, p["shard"], p["seed"])
        tone = (ident * 2654435761 % 1000) / 1000.0
        dark = shell & (tone < 0.35)
        lite = shell & (tone > 0.75)
        cv.recolour(dark, (40, 4, 8), 4, glow=g * 0.4, jitter=0.2)
        cv.recolour(lite, (96, 12, 18), 4, glow=g * 0.75, jitter=0.2)
        # proud shards: a few stand a pixel out
        crack = shell & (border < G * 0.32)
        cv.recolour(crack, VEIN, 5, glow=g * (0.75 + 0.25 * cv.hash), jitter=0.15)
        cv.recolour(crack & (cv.hash < 0.05), VEIN_HOT, 3, glow=g)
        return tone, border
    elif style == "bleed":
        # blood running down inside the glass from the top collar: wavering drip lines, thick at the
        # top and thinning, each ending in a drop; capillaries branch off them
        a = ang_front(cv)
        R = p["size"]
        rng = np.random.default_rng(p["seed"])
        n = p.get("drips", 22)
        veins = np.zeros(X.shape, bool)
        drops = np.zeros(X.shape, bool)
        wob = fbm(np.stack([X * 0.2, Y * 0.2, Z * 0.35], -1), p["seed"] + 3, 2)
        for i in range(n):
            a0 = 2 * np.pi * (i + rng.uniform(-0.3, 0.3)) / n
            zend = z1 - rng.uniform(0.25, 0.85) * (z1 - z0)
            t = np.clip((z1 - Z) / max(z1 - zend, 1e-3), 0, 1)                   # 0 at top .. 1 at end
            path = a0 + wob * 0.18 + 0.05 * np.sin(Z * 0.9 + i)
            dist = np.abs(wrapd(a - path)) * R / G                                # pixels
            width = 1.4 - 0.9 * t                                                 # pixels, half width
            veins |= shell & (dist < width) & (Z <= z1) & (Z >= zend)
            drops |= shell & (np.hypot(dist, (Z - (zend - 0.15)) / G) < 1.3)
        n2 = fbm(P * 0.85 + 7.0, p["seed"] + 30, 2)
        caps = shell & (np.abs(n2) < 0.03) & (Z > z0 + (z1 - z0) * 0.35)
        cv.recolour(caps, (120, 10, 16), 5, glow=g * 0.55, jitter=0.2)
        cv.recolour(veins, VEIN, 5, glow=np.maximum(g, 0.5) * (0.8 + 0.2 * cv.hash), jitter=0.12)
        cv.recolour(drops, VEIN_HOT, 5, glow=np.maximum(g, 0.6), jitter=0.08)
        cv.recolour(veins & (cv.hash < 0.04), VEIN_HOT, 3, glow=g)
        # the heart: glass round the emblem a shade brighter, the glow pooled there
        heart = shell & (np.hypot(X, (Z - zmid) * 0.8) < 4.2) & ~veins & ~drops & ~caps
        cv.recolour(heart, (78, 8, 14), 4, glow=g * 0.85, jitter=0.25)


# ---- r1: refined -------------------------------------------------------------------------------
def build_r1(p):
    cv = Canvas()
    X, Y, Z = cv.X, cv.Y, cv.Z
    r = radial(cv, p)
    a = ang_front(cv)
    z0, z1 = p["glass"]
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    R = p["size"] + p["bulge"] * np.sin(np.pi * H) ** 1.5 - p["neck"] * np.clip((H - 0.8) / 0.2, 0, 1) ** 2
    pz = p["port_z"]
    body = (Z > z0) & (Z <= z1) & (r <= R)
    shell = body & (r > R - G)
    glass_fill(cv, p, body, shell, pz, z0, z1)
    # panels: six copper struts, a pixel proud, standing over the glass; none across the emblem
    for k in range(6):
        t = np.pi / 6 + k * np.pi / 3
        ad = np.abs(wrapd(a - t)) * R
        st = (ad < 0.3) & (Z > z0) & (Z <= z1) & (r <= R + G) & (r > R - G)
        copper(cv, st, p)
        cv.recolour(st & (wrapd(a - t) < -0.12 / np.maximum(R, 1)), COPPER_HI, 1)
    # the foot: three steps, the lowest widest, rust on the steps
    for lo, hi, rad, dark in ((0.0, 0.75, p["size"] + 1.5, True), (0.75, 1.5, p["size"] + 1.1, False),
                              (1.5, 2.25, p["size"] + 0.8, True)):
        m = (Z > lo) & (Z <= hi) & (r <= rad)
        copper(cv, m, p, dark=dark)
        cv.recolour(m & (Z > hi - G) & (r > rad - G), COPPER_HI, 1)
    ring_band(cv, p, 2.25, z0, p["size"] + 0.7, rivets=12, rivet_phase=np.pi / 12)
    # cap: the upper band, a shoulder that rounds in, the grille plate
    Rt = float(p["size"] - p["neck"])
    ring_band(cv, p, z1, z1 + 1.5, Rt + 0.75, rivets=12, rivet_phase=np.pi / 12)
    zs = z1 + 1.5
    t = np.clip((Z - zs) / 1.75, 0, 1)
    sh = (Z > zs) & (Z <= zs + 1.75) & (r <= (Rt + 0.4) * np.sqrt(np.clip(1 - 0.55 * t ** 2, 0, 1)))
    copper(cv, sh, p)
    zt = zs + 1.75
    plate = (Z > zt) & (Z <= zt + 0.5) & (r <= Rt * 0.72)
    copper(cv, plate, p, dark=True)
    # the grille: a ring of dark slots round a raised boss
    slots = plate & (r > Rt * 0.42) & (r < Rt * 0.66) & ((np.floor((np.arctan2(Y, X) + np.pi) / (2 * np.pi) * 24) % 2) == 0) & (Z > zt + 0.25)
    cv.put(slots, HOLE, 0)
    boss = (Z > zt + 0.5) & (Z <= zt + 1.0) & (r <= Rt * 0.36)
    copper(cv, boss, p)
    cv.recolour(boss & (r > Rt * 0.36 - G), COPPER_HI, 1)
    # the ring handle on a knuckle
    kn = (Z > zt + 1.0) & (Z <= zt + 1.75) & (np.hypot(X, Y) <= 0.6)
    cv.put(kn, COPPER_DK, 1)
    Rm = p["ring_r"]
    handle_ring(cv, zt + 1.6 + Rm, Rm, 0.42)
    # the emblem port and the two rods tied to its housing
    fy = -float(p["size"] + p["bulge"] * math.sin(math.pi * (pz - z0) / (z1 - z0)) ** 1.5)
    ye = emblem(cv, p, pz, fy)
    for dz in (-p["rod_gap"], p["rod_gap"]):
        zr = pz + dz
        Hr = (zr - z0) / (z1 - z0)
        Rr = p["size"] + p["bulge"] * math.sin(math.pi * Hr) ** 1.5 + 0.35
        rod = (np.abs(Z - zr) <= 0.25) & (np.abs(r - Rr) <= 0.25) & ~cv.occ
        copper(cv, rod, p)
    return cv


# ---- r2: rage ----------------------------------------------------------------------------------
def build_r2(p):
    cv = Canvas()
    X, Y, Z = cv.X, cv.Y, cv.Z
    r = radial(cv, p)                  # octagon apothem
    a = ang_front(cv)
    z0, z1 = p["glass"]
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    # narrow at the foot, widening to hard shoulders, then cut in
    R = p["size"] - p["taper"] * (1 - H) ** 1.4 - 1.6 * np.clip((H - 0.88) / 0.12, 0, 1) ** 2
    pz = p["port_z"]
    body = (Z > z0) & (Z <= z1) & (r <= R)
    shell = body & (r > R - G)
    tone, border = glass_fill(cv, p, body, shell, pz, z0, z1)
    # some shards stand a pixel proud
    _, ident = vor3(np.stack([X, Y, Z], -1), p["shard"], p["seed"])
    proud = (Z > z0) & (Z <= z1) & (r > R) & (r <= R + G) & ((ident * 2654435761 % 1000) < 280) & (border > G * 0.32)
    cv.put(proud & ~cv.occ, (78, 9, 14), 4, glow=0.5, jitter=0.25)
    # octagon edges: thin dark copper ribs on the eight corners
    ce = np.abs(wrapd((a - np.pi / 8) * 4)) / 4 * R
    rib = (ce < 0.3) & (Z > z0) & (Z <= z1) & (r <= R + G) & (r > R - 2 * G)
    copper(cv, rib, p, dark=True)
    # the jaws: fangs hanging from the top band and rising from the bottom band over the glass
    for k in range(16):
        t = 2 * np.pi * k / 16
        if abs(wrapd(np.array(t))) < 0.5:
            continue                                             # clear of the emblem
        ad = np.abs(wrapd(a - t)) * R / G                        # pixels sideways
        top = k % 2 == 0
        ln = p["fang"] * (1.0 if top else 0.7) * (1.0 if k % 4 in (0, 1) else 0.75)
        if top:
            u = (z1 - Z) / G
        else:
            u = (Z - z0) / G
        f = (u >= 0) & (u < ln) & (ad <= 2.2 * (1 - u / ln)) & (r <= R + G) & (r > R - G)
        copper(cv, f, p)
        cv.recolour(f & (ad < 0.8), COPPER_HI, 1)
    # the foot: a wide octagon with four claws reaching out at the diagonals
    Rb = p["size"] - p["taper"]
    for lo, hi, rad, dark in ((0.0, 0.75, Rb + 1.6, True), (0.75, 1.75, Rb + 1.0, False)):
        m = (Z > lo) & (Z <= hi) & (r <= rad)
        copper(cv, m, p, dark=dark)
        cv.recolour(m & (Z > hi - G) & (r > rad - G), COPPER_HI, 1)
    for k in range(4):
        t = np.pi / 4 + k * np.pi / 2
        ux, uy = math.sin(t), -math.cos(t)
        along = X * ux + Y * uy
        side = np.abs(-X * uy + Y * ux)
        claw = (along > Rb) & (along < Rb + 3.2) & (side <= 0.9 * (1 - (along - Rb) / 3.4)) & (Z > 0) \
            & (Z <= 2.0 - 0.45 * (along - Rb))
        copper(cv, claw, p)
        cv.recolour(claw & (Z > 1.4 - 0.45 * (along - Rb)), COPPER_HI, 1)
    ring_band(cv, p, 1.75, z0, Rb + 0.6, dark=True, rivets=8, rivet_phase=np.pi / 8)
    # top band and the spiked crown
    Rt = float(p["size"] - 1.6)
    ring_band(cv, p, z1, z1 + 1.25, float(p["size"]) + 0.5, rivets=8, rivet_phase=np.pi / 8)
    zc = z1 + 1.25
    crown = (Z > zc) & (Z <= zc + 0.75) & (r <= Rt + 0.6)
    copper(cv, crown, p, dark=True)
    for k in range(8):
        t = np.pi / 8 + k * np.pi / 4
        cx, cy = math.sin(t) * (Rt + 0.1), -math.cos(t) * (Rt + 0.1)
        hgt = p["spike"] * (1.0 if k % 2 == 0 else 0.7)
        u = np.clip((Z - (zc + 0.75)) / hgt, 0, 1)
        sp = (Z > zc + 0.75) & (Z <= zc + 0.75 + hgt) & (np.hypot(X - cx, Y - cy) <= 0.75 * (1 - u) + 0.13)
        copper(cv, sp, p)
        cv.recolour(sp & (u > 0.55), COPPER_HI, 1)
    # a stepped dome inside the crown, then the ring on a thick knuckle
    zd = zc + 0.75
    for i, rad in enumerate((Rt * 0.8, Rt * 0.6, Rt * 0.38)):
        m = (Z > zd + i * 0.5) & (Z <= zd + (i + 1) * 0.5) & (np.hypot(X, Y) <= rad)
        copper(cv, m, p, dark=(i % 2 == 0))
    zk = zd + 1.5
    kn = (Z > zk) & (Z <= zk + 0.75) & (np.maximum(np.abs(X), np.abs(Y)) <= 0.75)
    cv.put(kn, COPPER_DK, 1)
    Rm = p["ring_r"]
    handle_ring(cv, zk + 0.5 + Rm, Rm, 0.5, square=True)
    # three small spikes on the ring's crown
    for t in (-0.6, 0.0, 0.6):
        cx, cz = math.sin(t) * (Rm + 0.5), zk + 0.5 + Rm + math.cos(t) * (Rm + 0.5)
        ux, uz = math.sin(t), math.cos(t)
        along = (X - cx) * ux + (Z - cz) * uz
        side = np.abs((X - cx) * uz - (Z - cz) * ux)
        sp = (along >= 0) & (along < 1.25) & (side <= 0.4 * (1 - along / 1.25) + 0.1) & (np.abs(Y) <= 0.25)
        cv.put(sp, COPPER_HI, 1)
    # the emblem: bigger, spiked bezel; the glass front is flat at y = -R (octagon)
    Hp = (pz - z0) / (z1 - z0)
    fy = -float(p["size"] - p["taper"] * (1 - Hp) ** 1.4)
    emblem(cv, p, pz, fy)
    return cv


# ---- r3: bleeding -----------------------------------------------------------------------------
def build_r3(p):
    cv = Canvas()
    X, Y, Z = cv.X, cv.Y, cv.Z
    r = radial(cv, p)
    a = ang_front(cv)
    z0, z1 = p["glass"]
    H = np.clip((Z - z0) / (z1 - z0), 0, 1)
    def Rof(h):
        return p["size"] + p["bulge"] * np.sin(np.pi * h) - 0.5 * np.clip((h - 0.85) / 0.15, 0, 1) ** 2 \
            - 0.5 * np.clip((0.15 - h) / 0.15, 0, 1) ** 2
    R = Rof(H)
    pz = p["port_z"]
    body = (Z > z0) & (Z <= z1) & (r <= R)
    shell = body & (r > R - G)
    glass_fill(cv, p, body, shell, pz, z0, z1)
    # the open cage: four bowed copper bars at the diagonals, standing a pixel off the glass
    for k in range(4):
        t = np.pi / 4 + k * np.pi / 2
        ad = np.abs(wrapd(a - t)) * (R + 0.5)
        bar = (ad < 0.375) & (Z > z0) & (Z <= z1) & (r > R + 0.25) & (r <= R + 0.75)
        copper(cv, bar, p)
        cv.recolour(bar & (r > R + 0.5), COPPER_HI, 1)
        # little lugs where the bar meets the glass, every few pixels
        lug = (ad < 0.25) & (r > R) & (r <= R + 0.25) & (np.abs(((Z - z0) % 3.0) - 1.5) < 0.26) & (Z > z0) & (Z <= z1)
        cv.put(lug, COPPER_DK, 1)
    # foot: a round stepped base with blood spilling over its lip
    Rb = p["size"] + 0.6
    for lo, hi, rad, dark in ((0.0, 0.5, Rb + 0.9, True), (0.5, 1.25, Rb + 0.6, False),
                              (1.25, 1.75, Rb + 0.25, True), (1.75, z0, Rb, False)):
        m = (Z > lo) & (Z <= hi) & (r <= rad)
        copper(cv, m, p, dark=dark)
        cv.recolour(m & (Z > hi - G) & (r > rad - G), COPPER_HI, 1)
    # the collar bands: a fat torus-like roll top and bottom
    for zc in (z0, z1):
        Rc = float(Rof(0.0 if zc == z0 else 1.0)) + 0.5
        roll = np.hypot(r - Rc, Z - zc) <= 0.6
        copper(cv, roll, p)
        cv.recolour(roll & (Z > zc + 0.25), COPPER_HI, 1)
    # blood pooled on the foot and running over its edges
    rng = np.random.default_rng(p["seed"] + 9)
    pool = (Z > z0 - 0.25) & (Z <= z0) & (r <= Rb + 0.25) & (r > Rof(0.0) + 1.0) \
        & (fbm(np.stack([X * 0.4, Y * 0.4, Z * 0], -1), p["seed"] + 4, 2) > 0.05)
    cv.put(pool & ~cv.occ, BLOOD, 5, glow=0.4)
    for i in range(13):
        t = 2 * np.pi * (i + rng.uniform(-0.3, 0.3)) / 13
        if abs(wrapd(np.array(t))) < 0.35:
            continue
        ln = rng.integers(3, 8) * G
        ad = np.abs(wrapd(a - t)) * (Rb + 0.25) / G
        rr = Rb + 0.25 + G * (Z < 1.25) * 1 + G * (Z < 0.5)
        dr = (ad < 0.7) & (Z <= z0) & (Z > z0 - ln) & (r > rr - G) & (r <= rr + G * 0.5) & ~cv.occ
        drop = (ad < 1.3) & (np.abs(Z - (z0 - ln)) < G * 0.6) & (r > rr - G) & (r <= rr + G * 0.5) & ~cv.occ
        cv.put(dr | drop, BLOOD, 5, glow=0.4)
    # the cap: a tall dome stepped in, a ring of vent holes, a finial knuckle
    zt = z1 + 0.6
    Rt = float(Rof(1.0))
    for i, (h, rad) in enumerate(((0.75, Rt + 0.2), (0.5, Rt - 0.3), (0.75, Rt - 0.9), (0.5, Rt - 1.7), (0.5, Rt - 2.5))):
        m = (Z > zt) & (Z <= zt + h) & (r <= rad)
        copper(cv, m, p, dark=(i % 2 == 1))
        cv.recolour(m & (Z > zt + h - G) & (r > rad - G), COPPER_HI, 1)
        if i == 2:
            vent = m & (np.abs(r - (rad - 0.12)) < 0.2) & ((np.floor((np.arctan2(Y, X) + np.pi) / (2 * np.pi) * 16) % 2) == 0) \
                & (np.abs(Z - (zt + h / 2)) < 0.26)
            cv.put(vent, HOLE, 0)
        zt += h
    kn = (Z > zt) & (Z <= zt + 0.75) & (np.hypot(X, Y) <= 0.7)
    cv.put(kn, COPPER_DK, 1)
    # a double ring: the main loop and a thinner ring threaded through it at right angles
    Rm = p["ring_r"]
    zc = zt + 0.5 + Rm
    handle_ring(cv, zc, Rm, 0.42)
    d2 = np.hypot(cv.Y, cv.Z - (zt + 0.5 + 0.9)) - 1.1
    small = (np.hypot(d2, cv.X) <= 0.28)
    cv.put(small & ~cv.occ, BRONZE, 1)
    # the emblem
    Hp = (pz - z0) / (z1 - z0)
    fy = -float(Rof(Hp))
    emblem(cv, p, pz, fy)
    return cv


BASE = dict(seed=11, rust=0.12, port_out=1.0, bezel_px=13.5)
VERSIONS = {
    "r1": (build_r1, dict(BASE, glass=(4.0, 17.5), size=5.4, bulge=0.45, neck=0.5, port_z=10.75, rod_gap=3.75,
                          ring_r=2.4, veins="marble")),
    "r2": (build_r2, dict(BASE, glass=(3.5, 18.0), size=5.9, taper=1.4, port_z=11.0, port_scale=1.0,
                          bezel_px=14.0, bezel_spikes=8, spike_len=3.0, bezel_rivets=0, shard=1.6, fang=7,
                          spike=2.5, ring_r=2.2, veins="shards", seed=23, rust=0.18,
                          emblem_drips=((-4, 2), (-1, 6), (1, 3), (3, 4)))),
    "r3": (build_r3, dict(BASE, glass=(3.0, 18.0), size=5.1, bulge=0.9, port_z=10.5, ring_r=2.5,
                          veins="bleed", drips=20, seed=5, rust=0.08, glow_span=0.32, port_out=1.25)),
}

if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[2:] or list(VERSIONS)
    for name in only:
        fn, p = VERSIONS[name]
        cv = fn(p)
        q, c, k, w = cv.quads()
        lo, hi = q.reshape(-1, 3).min(0), q.reshape(-1, 3).max(0)
        np.savez_compressed(os.path.join(OUT, f"red_{name}.npz"), quads=q, col=c, kind=k, glow=w)
        print(name, len(q), "faces", np.bincount(k, minlength=6), "bounds", lo.round(2), hi.round(2))
