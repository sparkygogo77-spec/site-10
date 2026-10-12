"""The Dark Lantern, second design, at the Blue Lantern's level: every cube is one texture pixel
(0.25 units, 64 per block), so steps, cracks and the port are drawn pixel by pixel.

J's direction:
- no stacked slabs: the surface steps in and out by exactly one pixel, in bands two pixels tall; the
  raised bands are dark jade that lights up green, the sunken bands near-black glass
- the waist matters: the rounded-triangle body pinches in hard
- tiny gold trace cracks that never move; when the lantern is lit they glow green
- references: a gold stepped cap with a nozzle, an inverted triangle handle on a hinge, a round
  gold port on the front (grooved ring, square plate, centre hole, two screws), thin gold wires
  wrapped round the body, a triangular gold base

    python tools/pixel_dark_lantern2.py <out dir>

Writes dark2_<version>_<unlit|lit>.npz (quads, col srgb, kind 0 matte / 1 metal / 2 glow), units 1/16
block, x right, y back (front faces -y), z up.
"""
import math, os, sys
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
G = 0.25
EMPTY, GLASS, JADE, GOLD, GOLD_DK, BRASS_DK, HOLE, SILVER, WIRE = range(9)


def tri_sdf(x, y, r):
    k = math.sqrt(3)
    px = np.abs(x) - r
    py = y + r / k
    swap = px + k * py > 0
    nx = np.where(swap, (px - k * py) / 2, px)
    ny = np.where(swap, (-k * px - py) / 2, py)
    nx = nx - np.clip(nx, -2 * r, 0)
    return -np.hypot(nx, ny) * np.sign(ny)


def rtri(x, y, size, rnd):
    """A rounded triangle, flat side toward -y (the front); `size` ~ centre to corner."""
    return tri_sdf(x, y, size - rnd) - rnd


def front_y(size, rnd):
    return -((size - rnd) / math.sqrt(3) + rnd)


def build(p):
    xs = np.arange(-9, 9, G) + G / 2
    zs = np.arange(0, 30, G) + G / 2
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
    part = np.zeros(X.shape, np.int8)
    z0, z1 = p["body"]
    h = np.clip((Z - z0) / (z1 - z0), 0, 1)
    # the waist: a deep pinch, and shoulders that round off into the cap and base
    size = p["size"] * (1 - p["pinch"] * np.exp(-((h - p["waist_at"]) / p["waist_w"]) ** 2))
    size = size * (1 - 0.10 * np.clip((np.abs(h - 0.5) - 0.42) / 0.08, 0, 1) ** 2)
    band = (np.floor((Z - z0) / (2 * G)) % 2) == 0           # raised bands: two pixels tall, every other
    rnd = p["round"]
    d_in = rtri(X, Y, size, rnd)
    d_out = rtri(X, Y, size + G, rnd)
    body = (Z > z0) & (Z <= z1)
    part[body & (d_in <= 0)] = GLASS
    part[body & band & (d_out <= 0) & (d_in > 0)] = JADE
    part[body & band & (d_in <= 0) & (d_in > -G)] = JADE
    # base: a triangular gold plinth in two steps with a dark seam between
    for a, b, grow, pid in ((0.0, 1.0, 1.6, GOLD), (1.0, 1.25, 1.2, GOLD_DK), (1.25, z0, 1.1, GOLD)):
        sel = (Z > a) & (Z <= b) & (rtri(X, Y, p["size"] + grow, rnd + 0.4) <= 0)
        part[sel] = pid
    # cap: a collar, a step, a low dome, then the nozzle with a silver tip
    c = z1
    for a, b, grow, pid in ((0.0, 0.75, 1.2, GOLD), (0.75, 1.0, 0.9, GOLD_DK), (1.0, 1.75, 0.6, GOLD)):
        sel = (Z > c + a) & (Z <= c + b) & (rtri(X, Y, p["size"] + grow, rnd + 0.4) <= 0)
        part[sel] = pid
    dome_h = 1.25
    t = np.clip((Z - (c + 1.75)) / dome_h, 0, 1)
    dome = (Z > c + 1.75) & (Z <= c + 1.75 + dome_h) & (rtri(X, Y, (p["size"] + 0.2) * np.sqrt(1 - t ** 2) + 0.3, rnd) <= 0)
    part[dome] = GOLD
    nz = c + 1.75 + dome_h
    r = np.hypot(X, Y)
    part[(Z > nz) & (Z <= nz + 1.0) & (r <= 1.0)] = GOLD_DK
    part[(Z > nz + 1.0) & (Z <= nz + 1.5) & (r <= 0.75)] = SILVER
    # handle: an inverted rounded triangle loop standing in the x-z plane on a hinge ring
    hz = nz + 1.5
    hh = p["handle"]
    hcz = hz + hh * 0.62
    dh = rtri(X, -(Z - hcz), hh, 1.2)
    loop = (np.abs(dh) <= 0.3) & (np.abs(Y) <= 0.3) & (Z > hz + 0.6)
    part[loop] = GOLD
    hinge = (np.abs(np.hypot(Y, Z - (hz + 0.35)) - 0.45) <= 0.15) & (np.abs(X) <= 0.6)
    part[hinge] = GOLD_DK
    # thin gold wires wrapped round the body, one pixel off the bands, tilting as they go round
    for zc, tilt, ph in p["wires"]:
        ang = np.arctan2(Y, X)
        zw = zc + tilt * np.sin(ang + ph)
        hw = np.clip((zw - z0) / (z1 - z0), 0, 1)
        sw = p["size"] * (1 - p["pinch"] * np.exp(-((hw - p["waist_at"]) / p["waist_w"]) ** 2))
        dw = rtri(X, Y, sw + 2 * G, rnd)
        part[(np.abs(Z - zw) <= G * 0.75) & (np.abs(dw) <= G * 0.6) & (part == EMPTY)] = WIRE
    # the port: a round boss on the front face
    pz, pr = p["port"]
    hp = (pz - z0) / (z1 - z0)
    sp = p["size"] * (1 - p["pinch"] * math.exp(-((hp - p["waist_at"]) / p["waist_w"]) ** 2))
    fy = front_y(sp + G, rnd)
    rr = np.hypot(X, Z - pz)
    boss = (rr <= pr) & (Y >= fy - 1.0) & (Y <= fy + 1.0)
    part[boss] = GOLD
    groove = boss & (rr > pr * 0.62) & (Y < fy - 0.5) & ((np.floor(rr / G) % 2) == 0)
    part[groove] = GOLD_DK
    part[boss & (Y < fy - 0.5) & (rr > pr - G)] = GOLD_DK
    plate = boss & (np.maximum(np.abs(X), np.abs(Z - pz)) <= pr * 0.42)
    part[plate & (Y < fy - 0.25)] = 0
    part[plate & (Y >= fy - 0.25) & (Y < fy)] = BRASS_DK
    part[(rr <= 0.4) & (Y >= fy - 0.25) & (Y < fy + 0.25) & boss] = HOLE
    for sx in (-1, 1):
        sc = np.hypot(X - sx * pr * 0.3, Z - pz - pr * 0.3 * sx) <= 0.2
        part[sc & plate & (Y >= fy - 0.25) & (Y < fy)] = SILVER
    return xs, zs, part, z0, z1


# ---- trace cracks: thin lines along the borders of a 3D Voronoi, kept in patches -------------------
CR_PTS = np.random.default_rng(91).uniform([-8, -8, 0], [8, 8, 22], (70, 3))
KEEP = np.random.default_rng(92).random((70, 70)) < 0.42


def crack_at(c):
    d = np.linalg.norm(CR_PTS - c, axis=1)
    i, j = np.argsort(d)[:2]
    border = (d[j] - d[i]) / 2
    return border < 0.11 and KEEP[min(i, j), max(i, j)]


PAL = {
    GLASS: ((10, 20, 21), 0), JADE: ((24, 78, 52), 0), GOLD: ((212, 168, 78), 1), GOLD_DK: ((140, 102, 44), 1),
    BRASS_DK: ((96, 70, 32), 1), HOLE: ((14, 10, 6), 0), SILVER: ((196, 200, 206), 1), WIRE: ((200, 156, 70), 1),
}
LIGHT = np.array([-0.45, -0.75, 0.6]); LIGHT /= np.linalg.norm(LIGHT)


def pixel_quads(xs, zs, part, z0, z1, lit):
    occ = part > 0
    S = occ.shape
    Q, C, K = [], [], []
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    for i, j, k in np.argwhere(occ):
        pid = int(part[i, j, k])
        c = np.array([xs[i], xs[j], zs[k]])
        for n in dirs:
            ni, nj, nk = i + n[0], j + n[1], k + n[2]
            if 0 <= ni < S[0] and 0 <= nj < S[1] and 0 <= nk < S[2] and occ[ni, nj, nk]:
                continue
            nv = np.array(n, float)
            col, kind = PAL[pid]
            col = np.array(col, float)
            shade = 0.62 + 0.5 * max(0.0, float(nv @ LIGHT))
            h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
            body = pid in (GLASS, JADE)
            if body and crack_at(c + nv * G / 2) and nv[2] == 0:
                # a gold trace in the glass; when lit, it glows green
                col, kind = (np.array([90, 255, 140.0]), 2) if lit else (np.array([186, 146, 66.0]), 1)
            elif pid == JADE:
                col = col * (0.9 + 0.2 * h / 255)
                if n[2] > 0:
                    col = col * 1.35        # the lit upper lip of each raised band
                if lit and n[2] == 0:
                    # lit: the band glows from inside, brightest mid-band, dimmer toward its edges
                    col, kind = np.array([40, 200, 96.0]) * (0.75 + 0.25 * h / 255), 2
            elif pid == GLASS:
                col = col * (0.85 + 0.3 * h / 255)
                if lit and n[2] == 0:
                    col = np.array([12, 46, 28.0])
            elif pid in (GOLD, WIRE, GOLD_DK):
                col = col * (0.92 + 0.16 * h / 255)
            if kind != 2:
                col = col * shade
            a = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            b = np.cross(nv, a)
            f0 = c + nv * G / 2
            cs = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


BASE = dict(body=(1.75, 18.0), size=6.2, round=1.9, pinch=0.3, waist_at=0.46, waist_w=0.26,
            handle=4.2, wires=[(7.6, 1.2, 0.3), (9.4, 1.1, 2.4)], port=(8.6, 2.3))
VERSIONS = {
    "e1": dict(BASE),                                                  # the reference proportions
    "e2": dict(BASE, pinch=0.38, waist_w=0.22, size=6.4),              # a harder, narrower waist
    "e3": dict(BASE, body=(1.75, 19.5), size=5.8, pinch=0.28, wires=[(8.4, 1.4, 0.3)], port=(9.4, 2.1)),  # tall, slim
}
if __name__ == "__main__":
    for name, p in VERSIONS.items():
        xs, zs, part, z0, z1 = build(p)
        for lit in (False, True):
            q, c, k = pixel_quads(xs, zs, part, z0, z1, lit)
            np.savez_compressed(os.path.join(OUT, f"dark2_{name}_{'lit' if lit else 'unlit'}.npz"), quads=q, col=c, kind=k)
            print(name, "lit" if lit else "unlit", len(q), "faces")
