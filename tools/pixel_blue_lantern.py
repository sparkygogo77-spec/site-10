"""The Blue Lantern built straight on Minecraft's pixel grid from measurements of J's sheet: cubes on
a grid (0.5 = 32 per block, 0.25 = 64 per block) and every cube face painted as pixel art at 4
pixels per unit (64 per block), the emblem glass at 8 (128 per block). The emblem is authored pixel
by pixel, not shrunk from a picture.

Used by tools/blender/pixel_lantern.py (renders it beside the sheet) and tools/pixel_lantern_bbmodel.py
(writes the Blockbench model the mod draws). Call build(grid) first.

Units are the mod's (1 = 1/16 block), x right, y back (the front faces -y), z up. Measured from the
sheet's front and side views at 12 px per unit: body 13.3 wide and 13.6 tall on a 4.6 tall stepped
foot, windows a 5.5 octagon frame round a 4.75 domed glass, bronze collar 4.35 round, stone handle
loop to 26.7.
"""
import math, os, sys
import numpy as np

G = 0.5                                   # cube size (set by build)
T = 0.25                                  # one texture pixel: 64 per block
TG = 0.125                                # the emblem glass's pixels: 128 per block

# ---- dimensions ------------------------------------------------------------------------------------
HX, HZ, CZ = 6.65, 6.8, 11.4              # body half width/depth, half height, centre height
CH = 1.9                                  # chamfer
FR_OUT, GL = 5.5, 4.75                    # window frame outer half size, glass half size
FR_UP = 0.5                               # how far the frame stands proud
DOME = 0.9                                # how far the glass domes out past the face
EMB_PX = 17.5                             # emblem radius in texture pixels (4.4 units, measured)
TOP = CZ + HZ                             # 18.2


def octn(s, t):
    return np.maximum(np.maximum(np.abs(s), np.abs(t)), (np.abs(s) + np.abs(t)) / math.sqrt(2))


# body planes (normal, offset) about the body centre: inside where n.q <= d for all
PLANES = []
for ax in range(3):
    for sg in (-1, 1):
        n = np.zeros(3)
        n[ax] = sg
        PLANES.append((n, HZ if ax == 2 else HX))
for a, b in ((0, 1), (0, 2), (1, 2)):
    for sa in (-1, 1):
        for sb in (-1, 1):
            n = np.zeros(3)
            n[a], n[b] = sa, sb
            ha = HZ if a == 2 else HX
            hb = HZ if b == 2 else HX
            PLANES.append((n / math.sqrt(2), (ha + hb - CH) / math.sqrt(2)))
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            PLANES.append((np.array([sx, sy, sz]) / math.sqrt(3), (HX + HX + HZ - 1.5 * CH) / math.sqrt(3)))
PN = np.array([p[0] for p in PLANES])
PD = np.array([p[1] for p in PLANES])

# ---- the cube grid ---------------------------------------------------------------------------------
STONE, FRAME, EMBLEM, LENS, PORT, HOLLOW, BRONZE, CAPTOP, HANDLE, FOOT = range(1, 11)
GLOWING = (EMBLEM, LENS)
SIDES = [("front", 1, -1), ("back", 1, 1), ("right", 0, 1), ("left", 0, -1)]   # (name, axis, sign)


def build(grid=0.5):
    """Fills the cube grid at ``grid`` units per cube: sets xs, zs (cube centres), part (what each
    cube is, 0 empty) and occ (filled) as module globals."""
    global G, xs, zs, part, occ
    G = grid
    xs = np.arange(-8.5, 8.5, G) + G / 2
    zs = np.arange(-0.0, 27.5, G) + G / 2
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
    P = np.stack([X, Y, Z - CZ], -1)
    part = np.zeros(X.shape, np.int8)          # 0 empty

    body = np.all(P @ PN.T <= PD + 1e-6, axis=-1)
    part[body] = STONE

    # the four windows: a raised octagonal frame, glass sunk inside it and domed outward
    for name, ax, sg in SIDES:
        depth = P[..., ax] * sg - HX            # height above the face plane
        s = P[..., 1 - ax] if ax == 0 else P[..., 0]
        t = P[..., 2]
        r = octn(s, t)
        frame = (r >= GL) & (r < FR_OUT) & (depth > 0) & (depth <= FR_UP)
        part[frame] = FRAME
        # sink the face under the glass, then dome the glass out
        sunk = (r < GL) & (depth > -G) & (depth <= 0)
        part[sunk] = 0
        dome_h = DOME * np.sqrt(np.clip(1 - (r / GL) ** 2, 0, 1))
        glass = (r < GL) & (depth > -G) & (depth <= dome_h - G * 0.5 + 1e-6)
        part[glass] = EMBLEM if ax == 1 else LENS
        if ax == 0:
            rr = np.hypot(s, t)
            port = (rr >= 1.5) & (rr < 2.3) & (depth > -G) & (depth <= DOME)
            part[port] = PORT
            part[(rr < 1.5) & (depth > -G) & (depth <= DOME)] = 0
            part[(rr < 1.5) & (depth > -G) & (depth <= 0.25)] = HOLLOW
            part[(rr < 1.4) & (depth > -G) & (depth <= 0)] = HOLLOW

    # the cap: a stone step, the bronze collar, its crowned top
    rr = np.hypot(X, Y)
    part[(rr < 4.4) & (Z > TOP - 0.5) & (Z <= TOP + 1.0)] = STONE
    part[(rr < 4.35) & (Z > TOP + 1.0) & (Z <= TOP + 2.5)] = BRONZE
    part[(rr < 3.4) & (Z > TOP + 2.0) & (Z <= TOP + 2.5)] = CAPTOP

    # the foot: a notched slab, a chamfered step, an octagonal neck
    slab = (np.abs(X) <= 5.5) & (np.abs(Y) <= 5.5) & (Z <= 2.3)
    for a, b in ((X, Y), (Y, X)):
        slab &= ~((np.abs(np.abs(a) - 4.25) < 0.3) & (np.abs(b) > 5.0) & (Z <= 1.8))
    part[slab] = FOOT
    step = (np.abs(X) <= 4.7) & (np.abs(Y) <= 4.7) & (np.abs(X) + np.abs(Y) <= 8.4) & (Z > 2.3) & (Z <= 4.0)
    part[step] = FOOT
    part[(octn(X, Y) <= 4.05) & (Z > 4.0) & (Z <= 4.7)] = FOOT

    # the handle: posts, stepped corners, top bar (1 wide across, 1.5 deep)
    hd = np.abs(Y) <= 0.75
    part[hd & (np.abs(X) > 4.5) & (np.abs(X) <= 5.5) & (Z > TOP) & (Z <= 24.7)] = HANDLE
    part[hd & (np.abs(X) > 3.5) & (np.abs(X) <= 4.5) & (Z > 24.7) & (Z <= 25.7)] = HANDLE
    part[hd & (np.abs(X) <= 3.5) & (Z > 25.7) & (Z <= 26.7)] = HANDLE
    occ = part > 0



def occupied(p):
    """Whether the cube holding model point p is filled."""
    i = int(math.floor((p[0] - xs[0]) / G + 0.5))
    j = int(math.floor((p[1] - xs[0]) / G + 0.5))
    k = int(math.floor((p[2] - zs[0]) / G + 0.5))
    S = occ.shape
    return 0 <= i < S[0] and 0 <= j < S[1] and 0 <= k < S[2] and bool(occ[i, j, k])


def shade_pixel(pid, q, n):
    """The finished pixel at model point q on a face with outward normal n of a cube of part pid:
    texel() plus pixel ambient occlusion where a cube sits beside it above the face.
    Returns (srgb colour, kind 0 stone / 1 metal / 2 glow)."""
    col, kind = texel(pid, q, n, None)
    if kind == 2:
        return col, kind
    n = np.asarray(n, float)
    ao = 0
    for e in np.eye(3):
        if abs(np.dot(e, n)) > 0.5:
            continue
        c = float(np.dot(q, e))
        lo = c - (math.floor(c / G) * G)
        side = -1 if lo < T * 1.01 else 1 if G - lo < T * 1.01 else 0
        if side and occupied(np.asarray(q) + n * G * 0.5 + e * side * G * 0.5):
            ao += 1
    if ao:
        col = tuple(cc * (0.78 if ao == 1 else 0.66) for cc in col)
    return col, kind


# ---- pixel art -------------------------------------------------------------------------------------
def hashf(*a):
    h = 2166136261
    for v in a:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return (h & 0xFFFF) / 0xFFFF


STONE_PAL = [(34, 48, 72), (52, 72, 102), (68, 92, 128), (88, 114, 150), (118, 142, 174)]
BRONZE_PAL = [(78, 44, 18), (122, 76, 36), (160, 104, 52), (198, 142, 78), (232, 190, 124)]


def stone_tone(q, base=2):
    """A worn stone pixel: mostly the base tone, a few 2x2 clumps a step lighter or darker."""
    u = [math.floor(c / (T * 2)) for c in q]
    h = hashf(*u, 7)
    h2 = hashf(*[math.floor(c / T) for c in q], 3)
    k = base + (1 if h > 0.88 else -1 if h < 0.1 else 0) + (1 if h2 > 0.975 else -1 if h2 < 0.02 else 0)
    return STONE_PAL[max(0, min(4, k))]


def body_facet(q):
    """For a point on the body: (active plane index, distance to the facet's nearest edge)."""
    c = PN @ q - PD
    i = int(np.argmax(c))
    others = [(c[i] - c[j]) / (np.linalg.norm(PN[i] - PN[j]) + 1e-9) for j in range(len(PN)) if j != i
              and np.dot(PN[i], PN[j]) > 0.3]
    return i, (min(others) if others else 9)


def emblem_px(u, v):
    """The Blue Lantern emblem as pixel art, proportions measured off J's sheet (fractions of its
    radius R): outer ring 0.89-1.0, a C arc each side 0.62-0.78 reaching 55 degrees up and down,
    a short bar top and bottom (half width 0.28, 0.67-0.8) on a stem (0.49-0.67) down to an inner
    ring 0.39-0.5, and the glowing disc inside it. u, v are pixels from the centre (pixel centres
    at half-integers, so it is exactly symmetric). Returns 'line', 'disc', 'field' or None."""
    R = EMB_PX
    r = math.hypot(u, v) / R
    a = math.degrees(math.atan2(abs(v), abs(u)))
    x, y = abs(u) / R, abs(v) / R
    if r >= 1.0:
        return None
    if r >= 0.886:
        return "line"
    if r < 0.375:
        return "disc"
    if r < 0.5:
        return "line"
    if 0.622 <= r < 0.783 and a <= 55:
        return "line"
    if x < 0.286 and 0.668 <= y < 0.8:
        return "line"
    if x < 0.058 and 0.49 <= y < 0.668:
        return "line"
    return "field"


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def crown_px(u, v):
    if abs(u) <= 4.5 and -3.5 <= v <= 0:
        return True
    return any(abs(u - cx) <= (3.5 - v) * 0.42 for cx in (-4, 0, 4)) and 0 < v <= 3.5


def texel(pid, q, n, vox):
    """(srgb colour, kind 0 stone / 1 metal / 2 glow) for the texture pixel centred at q on a face
    with outward normal n of the cube at index vox."""
    x, y, z = q
    up = n[2] > 0.5
    if pid in (STONE, FRAME, HANDLE, FOOT):
        if pid == FOOT and abs(z) < 1e-6 and n[2] < -0.5 and math.hypot(x, y) < 4.8:
            r = math.hypot(x, y)       # the bronze plate underneath, turned rings and four emblems
            for ring in (4.6, 3.8, 3.3, 2.2, 1.2):
                if abs(r - ring) < T * 0.6:
                    return BRONZE_PAL[0], 1
            for a in range(4):
                if math.hypot(x - 2.9 * math.cos(a * math.pi / 2), y - 2.9 * math.sin(a * math.pi / 2)) < 0.5:
                    return STONE_PAL[3], 0
            return BRONZE_PAL[2], 1
        if pid == FOOT and n[1] > 0.5 and abs(x) < 1.6 and 2.6 < z < 3.7:
            # the nameplate on the back of the step, two engraved lines
            if abs(x) < 1.2 and (abs(z - 2.95) < T * 0.6 or abs(z - 3.35) < T * 0.6):
                return BRONZE_PAL[0], 1
            return BRONZE_PAL[3], 1
        base = 3 if up else (1 if n[2] < -0.5 else 2)
        col = stone_tone(q, base)
        if pid == STONE:
            qb = np.array([x, y, z - CZ])
            if np.all(PN @ qb <= PD + G):
                i, d = body_facet(qb)
                # each facet framed as on the sheet: a worn pale edge, a dark cut line, a light catch
                if d < T:
                    col = STONE_PAL[4]
                elif d < 2 * T and d >= T * 1.5:
                    col = STONE_PAL[0]
                elif 2 * T <= d < 3 * T:
                    col = STONE_PAL[3]
        axis = np.array([0.0, 1.0, 0.0]) if abs(y) > abs(x) else np.array([1.0, 0.0, 0.0])
        if pid in (STONE, FRAME) and abs(np.dot(n, axis)) > 0.5 and abs(z - CZ) < FR_OUT + 0.5:
            s_ = x if axis[0] == 0 else y
            k = float(octn(np.array(s_), np.array(z - CZ)))
            if k < FR_OUT + T:
                # inner lip in shadow, the frame's face, a lit bevel, a dark cut line round it
                if k < GL + T:
                    return STONE_PAL[0], 0
                if k < GL + 2 * T:
                    return STONE_PAL[4], 0
                if k < FR_OUT - T:
                    return stone_tone(q, 3), 0
                if k < FR_OUT:
                    return STONE_PAL[4], 0
                return STONE_PAL[0], 0
        if pid == FRAME:
            # the raised octagonal frame: lit face, pale top edges, shadowed sides
            axis = np.array([0.0, 1.0, 0.0]) if abs(y) > abs(x) else np.array([1.0, 0.0, 0.0])
            if abs(np.dot(n, axis)) > 0.5:
                col = STONE_PAL[3] if hashf(*[math.floor(c / T) for c in q]) > 0.08 else STONE_PAL[4]
            elif up:
                col = STONE_PAL[4]
            else:
                col = STONE_PAL[1]
        if pid == HANDLE:
            # bevelled edges: the outermost pixel row of every face catches the light
            lo = [abs(((c + 1000) % G)) for c in q]
            if any(min(l, G - l) < T * 0.6 for l, nn in zip(lo, n) if abs(nn) < 0.5):
                col = STONE_PAL[3] if up or n[2] > -0.5 else STONE_PAL[1]
        return col, 0
    if pid == EMBLEM:
        # each pixel takes the average of 4 x 4 samples inside it, so the curves get one soft
        # in-between tone at their edges (hand-drawn pixel art's anti-aliasing) instead of stairs
        s0 = x if y < 0 else -x
        t0 = z - CZ
        acc = np.zeros(3)
        for i in range(4):
            for j in range(4):
                ss = s0 + (i - 1.5) / 4 * TG
                tt = t0 + (j - 1.5) / 4 * TG
                u, v = ss / T, tt / T
                m = emblem_px(u, v)
                r = math.hypot(u, v) / EMB_PX
                if m == "line":
                    c = mix((214, 242, 255), (176, 224, 250), r)
                elif m == "disc":
                    c = mix((200, 250, 255), (64, 196, 240), (r / 0.375) ** 1.5)
                elif m == "field":
                    c = mix((60, 140, 220), (40, 104, 190), r)
                else:
                    k = float(octn(np.array(ss), np.array(tt))) / GL
                    c = mix((30, 84, 184), (12, 40, 120), (k - 0.85) / 0.15)
                acc += np.array(c) ** 2.2
        return tuple((acc / 16) ** (1 / 2.2)), 2
    if pid == LENS:
        s, t = y, z - CZ
        k = float(octn(np.array(s), np.array(t))) / GL
        if k < 0.5:
            return mix((176, 228, 255), (96, 184, 250), k / 0.5), 2
        return mix((70, 150, 240), (14, 46, 140), (k - 0.5) / 0.5), 2
    if pid == PORT:
        rr_ = math.hypot(y, z - CZ)
        if n[0] * (1 if x > 0 else -1) > 0.5:
            # the ring's face: a lit outer lip, a turned groove, a pale inner lip
            if rr_ > 2.3 - T:
                return BRONZE_PAL[2], 1
            if rr_ < 1.5 + T:
                return BRONZE_PAL[4], 1
            return BRONZE_PAL[3], 1
        return BRONZE_PAL[1], 1
    if pid == HOLLOW:
        # the cup inside the port: dark bronze, darkest at its middle
        rr_ = math.hypot(y, z - CZ)
        return mix(BRONZE_PAL[1], (40, 22, 10), 1 - rr_ / 1.5), 1
    if pid == BRONZE:
        if up:
            return BRONZE_PAL[3], 1
        if n[2] < -0.5:
            return BRONZE_PAL[0], 1
        # a turned collar in bands: a dark foot, mid body, a bright band, a lit rim
        band = z - (TOP + 1.0)
        tone = 0 if band < T else 1 if band < 3 * T else 2 if band < 4 * T else 3 if band < 5 * T else 4
        # read as round: a step lighter where the collar turns toward the light (front left),
        # a step darker round the back
        r_ = math.hypot(x, y) or 1
        lit_ = (-0.45 * x - 0.9 * y) / r_
        tone += 1 if lit_ > 0.55 else -1 if lit_ < -0.35 else 0
        return BRONZE_PAL[max(0, min(4, tone))], 1
    if pid == CAPTOP:
        r = math.hypot(x, y)
        if not up:
            return BRONZE_PAL[2], 1
        if r > 3.1:
            return BRONZE_PAL[4], 1
        if r > 2.85:
            return BRONZE_PAL[1], 1
        if r > 2.4:
            return stone_tone(q, 2), 0
        if r > 2.0:
            return BRONZE_PAL[3], 1
        if r > 1.8:
            return BRONZE_PAL[0], 1
        u, v = x / T, -y / T
        if crown_px(u, v):
            return BRONZE_PAL[4], 1
        return stone_tone(q, 1), 0
    return (255, 0, 255), 0




# ---- faces at pixel resolution --------------------------------------------------------------------
def pixel_quads():
    """Every visible cube face cut into its texture pixels: (quads [4 corners each], colours (srgb),
    kinds 0 stone / 1 metal / 2 glow), for rendering. Call build() first."""

    DIRS = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
            ((0, 1, 0), (0, 0, 1), (1, 0, 0)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
            ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (0, 1, 0), (1, 0, 0))]
    quads, qcol, qkind = [], [], []
    idx = np.argwhere(occ)
    S = occ.shape
    for i, j, k in idx:
        c = np.array([xs[i], xs[j], zs[k]])
        pid = int(part[i, j, k])
        for n, a, b in DIRS:
            ni, nj, nk = i + n[0], j + n[1], k + n[2]
            if 0 <= ni < S[0] and 0 <= nj < S[1] and 0 <= nk < S[2] and occ[ni, nj, nk]:
                continue
            n_, a_, b_ = np.array(n, float), np.array(a, float), np.array(b, float)
            f0 = c + n_ * G / 2
            Tp = TG if pid == EMBLEM else T
            Kp = int(round(G / Tp))
            for ta in range(Kp):
                for tb in range(Kp):
                    oa = -G / 2 + (ta + 0.5) * Tp
                    ob = -G / 2 + (tb + 0.5) * Tp
                    q = f0 + a_ * oa + b_ * ob
                    col, kind = texel(pid, q, n_, (i, j, k))
                    # pixel ambient occlusion: darken a pixel where a cube sits beside it above the face
                    ao = 0
                    for e, oo in ((a_, oa), (b_, ob)):
                        side = np.sign(oo)
                        if abs(oo) > G / 2 - Tp * 1.01:
                            m = np.array([i, j, k]) + n_.astype(int) + (e * side).astype(int)
                            if all(0 <= m[w] < S[w] for w in range(3)) and occ[tuple(m)]:
                                ao += 1
                    if kind != 2 and ao:
                        col = tuple(cc * (0.78 if ao == 1 else 0.66) for cc in col)
                    corners = [q + (a_ * sa + b_ * sb) * Tp / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                    if np.dot(np.cross(corners[1] - corners[0], corners[2] - corners[0]), n_) < 0:
                        corners = corners[::-1]
                    quads.append(corners)
                    qcol.append(col)
                    qkind.append(kind)

    return quads, qcol, qkind
