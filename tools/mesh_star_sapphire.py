"""The Star Sapphire lantern from J's sheet as a real mesh (see mesh_kit.py): a cut violet gem whose
facets rise to a point at their hearts like real cut stone, lit from within, held in a cage of
bevelled bronze bars with a row of rivets down each, a turned tip on top and a stepped hexagonal
foot with ribs and a nameplate. The big corner panels carry the eight-pointed star (runes behind).

    python tools/mesh_star_sapphire.py <out.json>
"""
import math, sys
import numpy as np
from PIL import Image
from mesh_kit import Model, lathe, norm

OUT = sys.argv[1] if len(sys.argv) > 1 else "violet_lantern_mesh.json"
m = Model("violet_lantern")

# The gem's rings (height, radius, angles), as in blockbench_models' Star Sapphire.
GEM_B = (3.0, 4.2, [45 * i for i in range(8)])
GEM_W = (8.2, 6.0, sorted(d + o for d in (45, 135, 225, 315) for o in (-30, 30)))
GEM_S = (13.2, 4.0, [45 * i for i in range(8)])
GEM_T = (16.2, 2.2, [45, 135, 225, 315])
APEX = np.array([0.0, 17.6, 0.0])
MARKS = {315: "star", 45: "star", 135: "runes", 225: "star"}


def rp(ring, ang):
    y, r, _ = ring
    th = math.radians(ang)
    return np.array([r * math.sin(th), y, -r * math.cos(th)])


def around(angs, a):
    lo = max([x for x in angs if x < a] or [max(angs) - 360])
    hi = min([x for x in angs if x > a] or [min(angs) + 360])
    return lo, hi


# ---- the mark texture: the eight-pointed star and the runes, in dark ink over violet light -------
def mark_img(kind, size=512):
    N = size * 2
    y, x = np.mgrid[0:N, 0:N]
    s = ((x + 0.5) / N * 2 - 1) * 2.0     # the mark fills about half the panel
    t = (1 - (y + 0.5) / N * 2) * 2.0
    r = np.hypot(s, t)
    a = np.arctan2(t, s)
    k = (a % (np.pi / 4)) / (np.pi / 4)
    long_pt = (np.round(a / (np.pi / 4)).astype(int) % 2) == 0
    tip = np.where(long_pt, 0.9, 0.68)
    f = 0.36 + (tip - 0.36) * np.abs(1 - 2 * k) ** 1.6
    glow = np.clip(1 - r * 0.45, 0, 1)[..., None] ** 1.5
    col = np.array([150, 70, 236]) * (1 - glow) + np.array([246, 226, 255]) * glow
    if kind == "star":
        ink = ((0.66 * f < r) & (r < f)) | (r < 0.11)
        halo = (r < f * 1.16) & ~ink & (r >= 0.66 * f)
        col = np.where(halo[..., None], np.array([255, 240, 255]), col)
    else:
        ink = np.zeros_like(r, bool)
        rng = np.random.default_rng(5)
        for row in range(5):
            for c in range(3):
                cx, cy = -0.34 + c * 0.34, 0.6 - row * 0.3
                kind_ = rng.integers(0, 5)
                inside = (np.abs(s - cx) < 0.12) & (np.abs(t - cy) < 0.11)
                strokes = [np.abs(s - cx) < 0.03, np.abs(t - cy) < 0.03, np.abs((s - cx) - (t - cy)) < 0.035,
                           np.abs((s - cx) + (t - cy)) < 0.035, (np.abs(t - cy - 0.08) < 0.03)]
                ink |= inside & (strokes[kind_] | strokes[(kind_ + 2) % 5])
    col = np.where(ink[..., None], np.array([60, 10, 110]), col)
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


m.texture("star", mark_img("star"))
m.texture("runes", mark_img("runes"))

# ---- the gem's facets ---------------------------------------------------------------------------
panels = []   # (name, outline points, mark or None)
skip = set()


def key(a, b):
    return tuple(sorted((tuple(np.round(a, 4)), tuple(np.round(b, 4)))))


for k in GEM_B[2]:
    lo, hi = around(GEM_W[2], k)
    wl, wh, b_, s_ = rp(GEM_W, lo), rp(GEM_W, hi), rp(GEM_B, k), rp(GEM_S, k)
    if k in MARKS:
        bl, bh, sl, sh = rp(GEM_B, k - 45), rp(GEM_B, k + 45), rp(GEM_S, k - 45), rp(GEM_S, k + 45)
        panels.append((f"panel_{k}", [bl, b_, bh, wh, sh, s_, sl, wl], MARKS[k]))
    else:
        panels.append((f"kite_{k}", [b_, wh, s_, wl], None))
for d in GEM_T[2]:
    panels.append((f"crown_{d}", [rp(GEM_S, d - 45), rp(GEM_S, d), rp(GEM_S, d + 45), rp(GEM_T, d)][::-1], None))
for c in (0, 90, 180, 270):
    panels.append((f"crown_c{c}", [rp(GEM_T, c + 45), rp(GEM_T, c - 45), rp(GEM_S, c)], None))
for d in GEM_T[2]:
    panels.append((f"apex_{d}", [rp(GEM_T, d + 90), rp(GEM_T, d), APEX], None))

DEEP = np.array([96, 34, 170]) / 255
MID = np.array([168, 92, 246]) / 255
PALE = np.array([244, 222, 255]) / 255
edges = {}
for name, pts, mark in panels:
    P = [np.asarray(p, float) for p in pts]
    c = sum(P) / len(P)
    out = norm(c - np.array([0, 9.0, 0]))
    nrm = np.zeros(3)
    for i in range(len(P)):
        nrm += np.cross(P[i] - c, P[(i + 1) % len(P)] - c)
    nrm = norm(nrm)
    if np.dot(nrm, out) < 0:
        P = P[::-1]
        nrm = -nrm
    # the facet rises to a point at its heart, like cut stone, so each half catches the light
    rise = 0.35 if len(P) > 3 else 0.18
    heart = c + rise * nrm
    R = max(np.linalg.norm(p - c) for p in P)
    if mark:
        part = m.part("glow_" + name, mark)
        up = norm(np.array([0, 1.0, 0]) - nrm * nrm[1])
        rt = np.cross(up, nrm)
        sc = 1 / (R * 1.0)

        def uv(p):
            d = p - c
            return (0.5 + np.dot(d, rt) * sc * 0.5, 0.5 + (np.dot(d, up) - 0.4) * sc * 0.5)
        h = part.v(heart, uv(heart))
        ids = [part.v(p, uv(p)) for p in P]
    else:
        part = m.part("glow_" + name, "gem")
        h = part.v(heart, (0, 0), tuple(PALE * 0.8 + MID * 0.2))
        ids = [part.v(p, (0, 0), tuple(DEEP)) for p in P]
    for i in range(len(ids)):
        part.tri.append([ids[i], ids[(i + 1) % len(ids)], h])
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        edges.setdefault(key(a, b), (a, b, []))[2].append(nrm)
# the panels' inner seams are not cage bars: only edges between two different panels get bars
bottom = [rp(GEM_B, k) for k in GEM_B[2]]

# ---- the cage: a bevelled bronze bar along every edge, with rivets -------------------------------
cage = m.part("cage", "bronze")
rivets = m.part("rivets", "bronze")


def bar(a, b, out, w=0.36, hgt=0.34, bev=0.09):
    """A bar of rounded-rectangle section swept from a to b, raised along ``out``."""
    e = norm(b - a)
    o = norm(out - e * np.dot(out, e))
    sd = np.cross(e, o)
    a2, b2 = a - e * w * 0.9, b + e * w * 0.9
    sect = [(-w, 0.0), (-w, hgt - bev), (-w + bev, hgt), (w - bev, hgt), (w, hgt - bev), (w, 0.0)]
    shades = [0.7, 0.85, 1.15, 1.15, 0.85, 0.7]
    rows = []
    for p in (a2, b2):
        rows.append([cage.v(p + sx * sd + sy * o, (0, 0), (sh,) * 3) for (sx, sy), sh in zip(sect, shades)])
    for i in range(len(sect) - 1):
        q = [rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]]
        P = [np.array(cage.p[j]) for j in q]
        fn = np.cross(P[1] - P[0], P[2] - P[0])
        mid = sum(P) / 4
        if np.dot(fn, mid - (a + b) / 2) < 0:
            q = q[::-1]
        cage.quad(*q)
    # rivet heads down the middle of the bar's top
    L = np.linalg.norm(b - a)
    n_r = max(1, int(L / 0.62))
    for i in range(n_r):
        p0 = a + e * (L * (i + 0.5) / n_r) + o * hgt
        ring = [rivets.v(p0 + 0.11 * (math.cos(2 * math.pi * j / 8) * e + math.sin(2 * math.pi * j / 8) * sd),
                         (0, 0), (1.25,) * 3) for j in range(8)]
        top = rivets.v(p0 + o * 0.09, (0, 0), (1.45,) * 3)
        for j in range(8):
            t = [ring[j], ring[(j + 1) % 8], top]
            P = [np.array(rivets.p[x]) for x in t]
            if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), o) < 0:
                t = [t[0], t[2], t[1]]
            rivets.tri.append(t)


for kk, (a, b, ns) in edges.items():
    if len(ns) < 2 and not (abs(a[1] - GEM_B[0]) < 1e-6 and abs(b[1] - GEM_B[0]) < 1e-6):
        continue
    out = norm(sum(ns)) if len(ns) else norm((a + b) / 2 - np.array([0, 9.0, 0]))
    bar(a, b, out)

lathe(m, "tip", "bronze", [(APEX[1] - 0.2, 0.8), (APEX[1] + 0.25, 0.8, "hard"), (APEX[1] + 0.25, 0.55),
                           (APEX[1] + 0.55, 0.5), (APEX[1] + 0.85, 0.22)], 16)

# ---- the foot: a stepped hexagon with ribs round its slab and a nameplate behind ------------------
H6 = 1 / math.cos(math.radians(30))
foot = [(0.0, 6.1 * H6), (1.25, 6.1 * H6), (1.4, 5.9 * H6), (1.4, 5.3 * H6), (2.3, 5.0 * H6), (2.3, 4.2 * H6),
        (3.1, 3.7 * H6)]
lathe(m, "foot", "bronze", foot, 6, phase=30, smooth=False,
      color=lambda y, r: (0.78,) * 3 if y < 1.3 else (1.0,) * 3)
ribs = m.part("foot_ribs", "bronze")
for side in range(6):
    th = math.radians(60 * side)
    nrm = np.array([math.sin(th), 0, -math.cos(th)])
    tan = np.array([math.cos(th), 0, math.sin(th)])
    for j in range(-6, 7):
        if side == 3 and abs(j) <= 3:
            continue   # the nameplate sits here
        c = nrm * 6.1 + tan * j * 0.5
        quad = [c - tan * 0.1 + [0, 0.15, 0], c + tan * 0.1 + [0, 0.15, 0], c + tan * 0.1 + [0, 1.1, 0],
                c - tan * 0.1 + [0, 1.1, 0]]
        ids = [ribs.v(p + nrm * 0.06, (0, 0), (0.6,) * 3) for p in quad]
        ribs.quad(ids[1], ids[0], ids[3], ids[2])
plate = m.part("nameplate", "bronze")
c = np.array([0, 0.65, 6.1 + 0.08])
quad = [c + [1.4, -0.4, 0], c + [-1.4, -0.4, 0], c + [-1.4, 0.4, 0], c + [1.4, 0.4, 0]]
ids = [plate.v(p, (0, 0), (1.3,) * 3) for p in quad]
plate.quad(ids[1], ids[0], ids[3], ids[2])

tris = m.save(OUT)
print(f"{OUT}: {tris} triangles, {sum(len(p.p) for p in m.parts)} vertices, {len(m.parts)} parts")
