"""The Dark Lantern, third design: recreated from J's two concept renders (not the in-game sheet), on the
Blue Lantern's pixel grid (0.25 units = one pixel, 64 per block).

From the renders: a rounded-triangle body (the bottom view shows nested rounded triangles), gently
pinched at the waist, wrapped in tight thin ribs of dark smoky glass; a bright green core column glows
through the middle of each face; fine lightning-like gold veins run over the glass; thick gold
rounded-triangle collars top and bottom; two thin gold wires round the waist meeting a round port on
the front: a stack of gold rings like a lens barrel round a silver face with a square plate; on top a
silver nozzle in a gold band, a swivel loop, and a big rounded-triangle gold handle, point down.
J's rules on top: nothing glows at rest, everything green lights up with the charge; gold flecks in
the veins glint now and then.

    python tools/pixel_dark_lantern3.py <out dir>

Writes dark4_<version>.npz (quads, col, kind: 0 matte, 1 metal, 3 glinting fleck, 4 jade body lit by
the charge, 5 gold vein green while charging), the kinds the Lantern Live dark materials expect.
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_dark_lantern2 import rtri, front_y, G, LIGHT

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
EMPTY, SMOKE, RIB, CORE, GOLD, GOLD_DK, SILVER, SILVER_DK, VEIN = range(9)


def profile(h, p):
    """Body size at height fraction h: a gentle waist, the shoulders full."""
    s = p["size"] * (1 - p["pinch"] * np.exp(-((h - p["waist_at"]) / p["waist_w"]) ** 2))
    return s * (1 + p["top_flare"] * np.clip((h - 0.6) / 0.4, 0, 1) ** 2)


def build(p):
    rng = np.random.default_rng(p["seed"])
    xs = np.arange(-10, 10, G) + G / 2
    zs = np.arange(0, 32, G) + G / 2
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
    part = np.zeros(X.shape, np.int8)
    z0, z1 = p["body"]
    h = np.clip((Z - z0) / (z1 - z0), 0, 1)
    size = profile(h, p)
    rnd = p["round"]
    d = rtri(X, Y, size, rnd)
    body = (Z > z0) & (Z <= z1)
    # tight ribs: one pixel out, one pixel in, all the way up
    rib = (np.floor((Z - z0) / G) % 2) == 0
    part[body & (d <= 0)] = SMOKE
    part[body & rib & (d <= G) & (d > 0)] = RIB
    part[body & rib & (d <= 0) & (d > -G)] = RIB
    # the green core column: the middle of each flat face, where the glass shows the light inside
    ang = np.degrees(np.arctan2(Y, X))
    for face in (-90.0, 30.0, 150.0):
        da = np.abs((ang - face + 180) % 360 - 180)
        wobble = 6 * np.sin(Z * 0.9 + face)
        col = (da < p["core_w"] + wobble) & body & (d <= 0) & (d > -G) & ~rib
        part[col] = CORE
    # fine gold veins: lightning paths over the glass, each zig-zagging down at its own slant
    for _ in range(p["veins"]):
        a0 = rng.uniform(-180, 180)
        za, zb = sorted(rng.uniform(z0 + 1, z1 - 1, 2))
        if zb - za < 4:
            zb = min(z1 - 0.5, za + 4)
        slope = rng.uniform(-9, 9)
        jag = rng.uniform(4, 10)
        path = a0 + slope * (Z - za) + jag * np.sign(np.sin(Z * rng.uniform(1.2, 2.2))) * 0.5
        dist = np.abs((ang - path + 180) % 360 - 180) * np.pi / 180 * np.maximum(size, 1)
        v = (dist < G * 0.6) & (Z >= za) & (Z <= zb) & body & (d <= G) & (d > -G)
        part[v] = VEIN
    # collars: thick gold rounded-triangle bands at the top and bottom of the glass
    for zc in (z0, z1):
        hc = (zc - z0) / (z1 - z0)
        s = float(profile(np.array(hc), p))
        for a, b, grow, pid in ((-0.75, -0.5, 0.95, GOLD_DK), (-0.5, 0.5, 1.15, GOLD), (0.5, 0.75, 0.95, GOLD_DK)):
            sel = (Z > zc + a) & (Z <= zc + b) & (rtri(X, Y, s + grow, rnd + 0.3) <= 0)
            part[sel & (part == EMPTY) | sel & (part == SMOKE) | sel & (part == RIB)] = pid
    # base: below the bottom collar, nested gold rounded triangles stepping in
    zb0 = z0 - 0.75
    sb = float(profile(np.array(0.0), p))
    for i, (grow, pid) in enumerate(((0.8, GOLD), (0.2, GOLD_DK), (-0.4, GOLD), (-1.2, GOLD_DK), (-2.2, GOLD))):
        sel = (Z > zb0 - 0.5 * (i + 1)) & (Z <= zb0 - 0.5 * i) & (rtri(X, Y, sb + grow, rnd) <= 0)
        part[sel] = pid
    # top: a low gold dome ring, the silver nozzle in a gold band, the swivel loop, the handle
    zt = z1 + 0.75
    st = float(profile(np.array(1.0), p))
    t = np.clip((Z - zt) / 1.0, 0, 1)
    dome = (Z > zt) & (Z <= zt + 1.0) & (rtri(X, Y, (st + 0.3) * (1 - 0.55 * t), rnd) <= 0)
    part[dome] = GOLD
    r = np.hypot(X, Y)
    zn = zt + 1.0
    part[(Z > zn) & (Z <= zn + 1.75) & (r <= 1.2)] = SILVER
    part[(Z > zn + 0.5) & (Z <= zn + 1.0) & (r <= 1.45)] = GOLD
    part[(Z > zn + 1.75) & (Z <= zn + 2.0) & (r <= 0.9)] = SILVER_DK
    zs_ = zn + 2.0
    swivel = (np.abs(np.hypot(X, Z - (zs_ + 0.6)) - 0.55) <= 0.18) & (np.abs(Y) <= 0.2)
    part[swivel] = GOLD
    hh = p["handle"]
    hc = zs_ + 1.0 + hh * 0.5
    dh = rtri(X, -(Z - hc), hh, 1.6)          # point down, wide flat top
    part[(np.abs(dh) <= 0.3) & (np.abs(Y) <= 0.3) & (Z > zs_ + 0.9)] = GOLD
    # wires: two thin gold rings round the waist, a pixel off the ribs
    for zc, tilt, ph in p["wires"]:
        zw = zc + tilt * np.sin(np.radians(ang) + ph)
        hw = np.clip((zw - z0) / (z1 - z0), 0, 1)
        dw = rtri(X, Y, profile(hw, p) + 2 * G, rnd)
        part[(np.abs(Z - zw) <= G * 0.6) & (np.abs(dw) <= G * 0.6) & (part == EMPTY)] = GOLD
    # the port on the front face: stepped rings like a lens barrel, a silver face, a square plate
    pz, pr = p["port"]
    hp = (pz - z0) / (z1 - z0)
    fy = front_y(float(profile(np.array(hp), p)) + G, rnd)
    rr = np.hypot(X, Z - pz)
    for k, (rad, depth, pid) in enumerate(((pr, 0.5, GOLD), (pr * 0.86, 0.75, GOLD_DK), (pr * 0.74, 1.0, GOLD),
                                         (pr * 0.6, 1.0, SILVER))):
        sel = (rr <= rad) & (Y >= fy - depth) & (Y <= fy + 0.75)
        part[sel] = pid
    plate = (np.maximum(np.abs(X), np.abs(Z - pz)) <= pr * 0.32) & (Y >= fy - 1.25) & (Y < fy - 1.0)
    part[plate] = GOLD_DK
    part[(rr <= pr * 0.12) & (Y >= fy - 1.25) & (Y < fy - 0.75)] = SILVER_DK
    return xs, zs, part


PAL = {SMOKE: (16, 44, 30), RIB: (30, 88, 56), CORE: (26, 104, 58), GOLD: (214, 170, 80),
       GOLD_DK: (150, 110, 46), SILVER: (200, 204, 210), SILVER_DK: (110, 114, 120), VEIN: (190, 150, 68)}
KIND = {SMOKE: 4, RIB: 4, CORE: 4, GOLD: 1, GOLD_DK: 1, SILVER: 1, SILVER_DK: 1, VEIN: 5}


def quads(xs, zs, part):
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
            h = ((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) & 255
            shade = 0.62 + 0.5 * max(0.0, float(nv @ LIGHT))
            col = np.array(PAL[pid], float) * (0.9 + 0.2 * h / 255)
            kind = KIND[pid]
            if pid == RIB and n[2] > 0:
                col *= 1.3                        # each rib's lit upper lip
            if pid == CORE:
                col *= 1.15
            if pid == VEIN and h < 34:
                kind = 3                          # about one vein pixel in eight glints
            col = col * shade
            a = np.array([0, 1, 0.]) if n[0] else np.array([1, 0, 0.])
            b = np.cross(nv, a)
            f0 = c + nv * G / 2
            cs = [f0 + (a * sa + b * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(cs); C.append(np.clip(col, 0, 255)); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


BASE = dict(body=(3.0, 19.5), size=6.6, round=2.4, pinch=0.17, waist_at=0.45, waist_w=0.3, top_flare=0.04,
            core_w=11, veins=9, handle=5.6, wires=[(9.6, 0.5, 0.0), (11.0, 0.5, 0.0)], port=(10.3, 2.5), seed=5)
VERSIONS = {
    "f1": dict(BASE),                                                           # as in the renders
    "f2": dict(BASE, pinch=0.24, core_w=15, veins=6),                           # deeper waist, wider glow
    "f3": dict(BASE, veins=16, wires=[(8.4, 0.6, 0.0), (10.0, 0.6, 0.0), (12.4, 0.6, 0.0)], seed=9),  # more gold
}
if __name__ == "__main__":
    for name, p in VERSIONS.items():
        xs, zs, part = build(p)
        q, c, k = quads(xs, zs, part)
        np.savez_compressed(os.path.join(OUT, f"dark4_{name}.npz"), quads=q, col=c, kind=k)
        print(name, len(q), "faces", np.bincount(k, minlength=6))
