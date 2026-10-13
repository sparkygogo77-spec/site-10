"""The Dark Lantern on Minecraft's pixel grid, in several versions for J to pick from (his references:
a rounded-triangle body pinched at the waist, dark glass in horizontal ribs, a green glowing core
showing through cracks, gold wire wrapped round it, a gold cap, a triangular gold handle, a round
gold port on the front and a triangular gold base).

    python tools/pixel_dark_lantern.py <out dir>

Writes dark_<v>.npz per version (quads, col (srgb), kind 0 stone / 1 metal / 2 glow, units 1/16 block,
x right, y back (front faces -y), z up), the format the Lantern Live scene loads.
Cubes are 0.5 units (32 per block); each cube face is one colour.
"""
import math, os, sys
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
G = 0.5
GLASS, RIB, CORE, GOLD, GOLD_DARK, PORT, PORT_IN = 1, 2, 3, 4, 5, 6, 7


def tri_sdf(x, y, r):
    """Signed distance to an upright equilateral triangle of 'radius' r (flat side toward -y)."""
    k = math.sqrt(3)
    px = np.abs(x) - r
    py = y + r / k
    swap = px + k * py > 0
    nx = np.where(swap, (px - k * py) / 2, px)
    ny = np.where(swap, (-k * px - py) / 2, py)
    nx = nx - np.clip(nx, -2 * r, 0)
    return -np.hypot(nx, ny) * np.sign(ny)


def rounded_tri(x, y, size, round_):
    return tri_sdf(x, y, size - round_) - round_


def hashv(*a):
    h = np.zeros_like(a[0], dtype=np.uint64) + np.uint64(1469598103934665603)
    for v in a:
        h = (h ^ (np.floor(v * 4).astype(np.int64).astype(np.uint64))) * np.uint64(1099511628211)
    return ((h >> np.uint64(20)) & np.uint64(0xFFFF)).astype(float) / 65535.0


def build(p):
    """p: the version's measurements. Returns part grid and the cube centres."""
    xs = np.arange(-8, 8, G) + G / 2
    zs = np.arange(0, 30, G) + G / 2
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
    part = np.zeros(X.shape, np.int8)
    y0 = p["body"][0]; y1 = p["body"][1]
    h = (Z - y0) / (y1 - y0)
    # the body: a rounded triangle, pinched at the waist, ribbed in horizontal bands
    waist = 1 - p["pinch"] * np.exp(-((h - p["waist_at"]) / 0.32) ** 2)
    size = p["size"] * waist
    rib = ((np.floor((Z - y0) / p["rib"]) % 2) == 0) * p["rib_depth"]
    d = rounded_tri(X, Y + p["shift"], size + rib, p["round"])
    inside = (Z > y0) & (Z <= y1)
    part[inside & (d <= 0)] = GLASS
    part[inside & (d <= 0) & (d > -0.6) & (rib > 0)] = RIB
    # the green core showing through: an irregular glowing band in the grooves, front and back
    band = np.abs(X + 0.9 * np.sin(Z * 0.7)) < p["core_w"] * (0.7 + 0.6 * hashv(Z * 0.5, X * 0.0))
    crack = hashv(X, Z) > p["crack_keep"]
    core = inside & (d <= 0) & (d > -0.6) & (rib == 0) & band
    part[core] = CORE
    part[inside & (d <= 0) & (d > -0.6) & (rib == 0) & crack & (np.abs(X) < size * 0.8)] = CORE
    # the gold base: a triangular stepped plinth, and the cap: a stepped triangle with a neck
    for z0, z1, s in p["base"]:
        sel = (Z > z0) & (Z <= z1) & (rounded_tri(X, Y + p["shift"], s, 1.0) <= 0)
        part[sel] = np.where((Z[sel] - z0) < G * 1.01, GOLD_DARK, GOLD)
    for z0, z1, s in p["cap"]:
        sel = (Z > z0) & (Z <= z1) & (rounded_tri(X, Y + p["shift"], s, 1.0) <= 0)
        part[sel] = GOLD
    nz0, nz1, nr = p["neck"]
    part[(Z > nz0) & (Z <= nz1) & (np.hypot(X, Y) <= nr)] = GOLD_DARK
    # the triangular handle: a loop in the x-z plane, two rods meeting in a flat top bar
    hz0, hz1, hw, ht = p["handle"]
    t = (Z - hz0) / (hz1 - hz0)
    edge = np.abs(np.abs(X) - hw * (1 - t * 0.55))
    hand = (Z > hz0) & (Z <= hz1) & (edge < ht) & (np.abs(Y) < ht)
    top = (Z > hz1 - ht * 2) & (Z <= hz1) & (np.abs(X) <= hw * 0.45 + ht) & (np.abs(Y) < ht)
    part[hand | top] = GOLD
    # gold wire: tilted rings round the body, a cube out from the glass
    for (zc, tilt, phase) in p["rings"]:
        zr = zc + tilt * np.sin(np.arctan2(Y, X) + phase)
        dd = rounded_tri(X, Y + p["shift"], size + p["rib_depth"] + 0.75, p["round"])
        part[(np.abs(Z - zr) < 0.45) & (np.abs(dd) < 0.45) & (part == 0)] = GOLD
    # gold veins on the glass
    if p["veins"]:
        v = (np.abs(np.sin(X * 1.3 + Z * 0.45) + np.sin(Z * 0.9 - X * 0.6) * 0.8) < 0.07)
        part[inside & (part == GLASS) & v & (d > -0.6)] = GOLD
    # the port: a round gold boss on the front face, a darker inset square
    pz, pr = p["port"]
    hp = (pz - y0) / (y1 - y0)
    sp = p["size"] * (1 - p["pinch"] * math.exp(-((hp - p["waist_at"]) / 0.32) ** 2))
    py = -((sp - p["round"]) / math.sqrt(3) + p["round"] + p["rib_depth"])   # the front flat face there
    rr = np.hypot(X, Z - pz)
    boss = (rr <= pr) & (Y >= py - 1.0) & (Y <= py + 0.5)
    part[boss] = PORT
    part[boss & (np.maximum(np.abs(X), np.abs(Z - pz)) <= pr * 0.45) & (Y < py)] = PORT_IN
    part[boss & (rr > pr - 0.55) & (Y < py - 0.5)] = GOLD_DARK
    return xs, zs, part


COLOURS = {
    GLASS: ((16, 30, 33), 1), RIB: ((44, 70, 72), 1), CORE: ((70, 255, 120), 2),
    GOLD: ((214, 172, 82), 1), GOLD_DARK: ((150, 112, 50), 1), PORT: ((222, 186, 104), 1),
    PORT_IN: ((70, 52, 26), 1),
}
SHADE = {(0, 0, 1): 1.12, (0, 0, -1): 0.6, (1, 0, 0): 0.92, (-1, 0, 0): 0.92, (0, 1, 0): 0.8, (0, -1, 0): 1.0}


def quads(xs, zs, part):
    occ = part > 0
    out_q, out_c, out_k = [], [], []
    S = occ.shape
    idx = np.argwhere(occ)
    for i, j, k in idx:
        c = np.array([xs[i], xs[j], zs[k]])
        pid = int(part[i, j, k])
        base, kind = COLOURS[pid]
        h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
        jitter = 0.9 + 0.2 * (h / 255)
        for n, sh in SHADE.items():
            ni, nj, nk = i + n[0], j + n[1], k + n[2]
            if 0 <= ni < S[0] and 0 <= nj < S[1] and 0 <= nk < S[2] and occ[ni, nj, nk]:
                continue
            nv = np.array(n, float)
            a = np.array([0, 1, 0.]) if abs(n[0]) else np.array([1, 0, 0.])
            b = np.cross(nv, a)
            f0 = c + nv * G / 2
            corners = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(corners[1] - corners[0], corners[2] - corners[0]), nv) < 0:
                corners = corners[::-1]
            col = tuple(min(255, ch * (1.0 if kind == 2 else sh * jitter)) for ch in base)
            out_q.append(corners); out_c.append(col); out_k.append(kind)
    return np.asarray(out_q, np.float32), np.asarray(out_c, np.float32), np.asarray(out_k, np.int8)


BASE = dict(body=(4.0, 19.0), size=6.4, round=1.6, shift=0.0, pinch=0.2, waist_at=0.5, rib=1.0, rib_depth=0.5,
            core_w=1.6, crack_keep=0.985, base=[(0.0, 2.0, 7.6), (2.0, 4.0, 6.9)],
            cap=[(19.0, 20.5, 7.2), (20.5, 21.5, 5.6)], neck=(21.5, 23.0, 1.6), handle=(23.0, 29.5, 5.0, 0.55),
            rings=[(8.0, 1.6, 0.0), (10.5, 1.4, 1.9)], veins=False, port=(10.0, 2.6))
VERSIONS = {
    "d1": dict(BASE),                                                     # faithful to the references
    "d2": dict(BASE, pinch=0.3, size=6.8, core_w=2.6, rings=[(9.0, 1.0, 0.0)],      # chunky hourglass,
               base=[(0.0, 2.5, 8.0), (2.5, 4.0, 7.2)], cap=[(19.0, 21.0, 7.6), (21.0, 22.0, 6.0)]),  # wide core
    "d3": dict(BASE, pinch=0.12, size=5.9, rib=0.5, veins=True, rings=[],           # sleek, fine ribs,
               handle=(23.0, 28.5, 4.2, 0.5), crack_keep=0.97),                    # gold veins
    "d4": dict(BASE, crack_keep=0.93, core_w=2.0, rings=[(7.0, 1.6, 0.0), (10.0, 1.6, 1.2), (13.0, 1.6, 2.4)]),
}
for name, p in VERSIONS.items():
    p = dict(p)
    xs, zs, part = build(p)
    q, c, k = quads(xs, zs, part)
    np.savez_compressed(os.path.join(OUT, f"dark_{name}.npz"), quads=q, col=c, kind=k)
    print(name, len(q), "faces")
