"""Construct face designs, round two (J, 2026-10-12: "why do the designs all look so similar? ... I need tons
of variety, take time with the designs"; his references: comic hard light with panel lines, plating and rim
light; glassy movie constructs with soft inner light). Every design here is built a different way, not the
ripple streaks again. Each is a whole animated face (cloudy or flat jade + its detail), 256 px = 4 x 4 blocks,
tiling, 24 frames that loop:

    python tools/construct_designs.py OUTDIR

Writes face_<id>.png (24 frames stacked, 256 x 6144), face_<id>.gif, still_<id>.png (frame 0) and designs.json.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
N, F = 256, 24
B = 64                                   # px per block
yy, xx = np.mgrid[0:N, 0:N].astype(float)
kx = np.fft.fftfreq(N, 1.0 / N)
KX, KY = np.meshgrid(kx, kx, indexing="xy")
K = np.hypot(KX, KY)
TAU = 2 * np.pi

DEEP = np.array([4, 48, 26.0]); MID = np.array([18, 128, 62.0]); LIGHT = np.array([92, 214, 132.0])
HI = np.array([205, 255, 222.0]); DARK = np.array([6, 34, 20.0])


def ramp(v, stops=((0, DEEP), (0.45, MID), (0.8, LIGHT), (1.0, HI))):
    v = np.clip(v, 0, 1)[..., None]
    out = np.zeros(v.shape[:-1] + (3,))
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        u = np.clip((v - a) / (b - a), 0, 1)
        m = (v >= a) & (v <= b)
        out = np.where(m, ca + (cb - ca) * u, out)
    return out


def field(kmin, kmax, beta, seed):
    r = np.random.default_rng(seed)
    amp = np.where((K >= kmin) & (K <= kmax), np.maximum(K, 1e-9) ** -beta, 0.0)
    spec = amp * np.exp(1j * r.uniform(0, TAU, K.shape))
    f = np.real(np.fft.ifft2(spec))
    return (f - f.mean()) / (f.std() + 1e-9)


def moving_field(kmin, kmax, beta, seed, t, turns=1, drift=(0, 0)):
    """A periodic noise whose components turn `turns` times a loop (it churns) and shifts by drift loops."""
    r = np.random.default_rng(seed)
    amp = np.where((K >= kmin) & (K <= kmax), np.maximum(K, 1e-9) ** -beta, 0.0)
    phi = r.uniform(0, TAU, K.shape)
    spin = r.choice([-1, 1], K.shape) * turns
    ph = phi + TAU * spin * t - TAU * (KX * drift[0] + KY * drift[1]) * t
    f = np.real(np.fft.ifft2(amp * np.exp(1j * ph)))
    return (f - f.mean()) / (f.std() + 1e-9)


def blur(img, r):
    """Wrapping gaussian blur of a 2D float array."""
    g = np.exp(-(K * r * TAU / N) ** 2 / 2)
    return np.real(np.fft.ifft2(np.fft.fft2(img) * g))


def wrapd(a, b):
    d = np.abs(a - b) % N
    return np.minimum(d, N - d)


def voronoi(pts):
    d = np.stack([np.hypot(wrapd(xx, px), wrapd(yy, py)) for px, py in pts])
    o = np.argsort(d, 0)
    d1 = np.take_along_axis(d, o[:1], 0)[0]
    d2 = np.take_along_axis(d, o[1:2], 0)[0]
    return o[0], d1, d2


def rgba(rgb, a):
    return np.concatenate([np.clip(rgb, 0, 255), np.clip(a, 0, 255)[..., None]], -1)


def smooth(e0, e1, x):
    u = np.clip((x - e0) / (e1 - e0), 0, 1)
    return u * u * (3 - 2 * u)


CLOUD = field(1, 14, 1.3, 5)            # a gentle cloudiness most designs sit on
DESIGNS = []


def design(key, name, frametime=2):
    def deco(fn):
        DESIGNS.append((key, name, frametime, fn))
        return fn
    return deco


# ---- 1. Plating: armour plates with bevelled seams and rivets; a glint sweeps across ---------------------
def plates(seed, min_size=8, depth=3):
    r = np.random.default_rng(seed)
    ids = np.zeros((N, N), int); n = [0]
    rects = []

    def split(x0, y0, x1, y1, d):
        w, h = x1 - x0, y1 - y0
        if d == 0 or (w < 2 * min_size and h < 2 * min_size) or (d < depth and r.random() < 0.25):
            ids[y0:y1, x0:x1] = n[0]; rects.append((x0, y0, x1, y1)); n[0] += 1
            return
        if (w >= h and w >= 2 * min_size) or h < 2 * min_size:
            c = x0 + int(r.integers(min_size, w - min_size + 1) // 4 * 4)
            split(x0, y0, c, y1, d - 1); split(c, y0, x1, y1, d - 1)
        else:
            c = y0 + int(r.integers(min_size, h - min_size + 1) // 4 * 4)
            split(x0, y0, x1, c, d - 1); split(x0, c, x1, y1, d - 1)
    for bx in range(0, N, B):
        for by in range(0, N, B):
            split(bx, by, bx + B, by + B, depth)
    return ids, rects, r


def plating_face(seed, min_size, depth, rivets, t, glint=True, tone=0.12):
    ids, rects, r = plates(seed, min_size, depth)
    shade = r.uniform(-tone, tone, len(rects))
    v = 0.5 + shade[ids] + 0.04 * CLOUD
    up = np.roll(ids, 1, 0) != ids; left = np.roll(ids, 1, 1) != ids
    down = np.roll(ids, -1, 0) != ids; right = np.roll(ids, -1, 1) != ids
    seam = up | left
    hl = (np.roll(seam, 1, 0) | np.roll(seam, 1, 1)) & ~seam      # the lit lip just inside each seam
    sh = (down | right) & ~seam
    v = np.where(hl, v + 0.22, v); v = np.where(sh, v - 0.1, v)
    rgb = ramp(v); a = np.full((N, N), 215.0)
    rgb = np.where(seam[..., None], DARK, rgb)
    if rivets:
        rr = np.random.default_rng(seed + 9)
        for (x0, y0, x1, y1) in rects:
            if (x1 - x0) >= 12 and (y1 - y0) >= 12 and rr.random() < 0.6:
                for cx, cy in ((x0 + 3, y0 + 3), (x1 - 4, y0 + 3), (x0 + 3, y1 - 4), (x1 - 4, y1 - 4)):
                    rgb[cy, cx] = HI; rgb[cy + 1, cx + 1] = DEEP
    if glint:
        d = ((xx + yy) - t * 2 * N) % (2 * N)
        g = np.exp(-((np.minimum(d, 2 * N - d)) / 14) ** 2)
        rgb = rgb + (HI - rgb) * (g * 0.55)[..., None]
    return rgba(rgb, a)


@design("P1", "plating, big plates, glint")
def _(t):
    return plating_face(11, 16, 2, True, t)


@design("P2", "plating, dense panels")
def _(t):
    return plating_face(23, 8, 4, False, t, tone=0.08)


# ---- 2. Mech: plates with vents and insets; the vents breathe ----------------------------------------------
@design("M1", "mech panels, glowing vents", 3)
def _(t):
    base = plating_face(31, 16, 2, True, t, glint=False, tone=0.07)
    rgb, a = base[..., :3].copy(), base[..., 3].copy()
    r = np.random.default_rng(32)
    pulse = 0.5 + 0.5 * math.sin(TAU * t)
    for bx in range(0, N, B):
        for by in range(0, N, B):
            if r.random() < 0.7:          # a vent: rows of slots
                x0 = bx + int(r.integers(6, 28)); y0 = by + int(r.integers(8, 36))
                for k in range(int(r.integers(3, 6))):
                    y = y0 + k * 4
                    rgb[y:y + 2, x0:x0 + 22] = DEEP + (HI - DEEP) * (0.35 + 0.65 * pulse * (0.6 + 0.4 * ((k % 2) == 0)))
            if r.random() < 0.5:          # an inset square with a light in it
                x0 = bx + int(r.integers(30, 46)); y0 = by + int(r.integers(30, 46))
                rgb[y0:y0 + 12, x0:x0 + 12] = DEEP
                rgb[y0 + 1:y0 + 11, x0 + 1:x0 + 11] = MID * 0.8
                rgb[y0 + 4:y0 + 8, x0 + 4:x0 + 8] = LIGHT + (HI - LIGHT) * (1 - pulse)
    return rgba(rgb, a)


# ---- 3. Cel: comic flat shading, three tones, clean edges, slowly shifting -----------------------------------
def cel(t, levels=(0.35, 0.62), outline=True, seed=41):
    v = moving_field(1, 6, 1.6, seed, t, 1)
    v = 0.5 + 0.22 * v
    b = np.digitize(v, levels)
    tones = np.array([0.32, 0.55, 0.8])
    out = ramp(tones[b])
    if outline:
        edge = (np.roll(b, 1, 0) != b) | (np.roll(b, 1, 1) != b)
        out = np.where(edge[..., None], LIGHT + (HI - LIGHT) * 0.6, out)
    return rgba(out, np.full((N, N), 205.0))


@design("C1", "comic cel tones, bright band lines", 3)
def _(t):
    return cel(t)


@design("C2", "comic cel, two tones, no lines (minimal)", 3)
def _(t):
    return cel(t, levels=(0.5,), outline=False, seed=43)


# ---- 4. Glass: clear and smooth, soft highlights sliding over it (the film's glassy constructs) -------------
@design("G1", "glass, soft sliding highlights (minimal)", 3)
def _(t):
    # long soft diagonal sheens drifting across clear jade, like light on a glass block
    rr = np.random.default_rng(51)
    amp = np.where((np.abs(KX - KY) <= 1) & (np.abs(KX) >= 1) & (np.abs(KX) <= 6), 1.0 / (np.abs(KX) + 0.5), 0.0)
    ph = rr.uniform(0, TAU, K.shape) - TAU * (KX + KY) * 0.5 * t
    f = np.real(np.fft.ifft2(amp * np.exp(1j * ph)))
    f = (f - f.mean()) / (f.std() + 1e-9)
    sheen = smooth(0.9, 1.9, f) * (0.7 + 0.3 * smooth(-1, 1, CLOUD))
    v = 0.42 + 0.07 * CLOUD + 0.5 * sheen
    return rgba(ramp(v), 140 + 90 * sheen)


@design("G2", "glass, deep with a bright caustic web", 3)
def _(t):
    # caustics: thin bright lines where two drifting waves cross zero
    w1 = moving_field(2, 7, 1.5, 61, t, 1)
    w2 = moving_field(2, 7, 1.5, 62, t, 1)
    web = np.maximum(np.exp(-(w1 / 0.09) ** 2), np.exp(-(w2 / 0.09) ** 2) * 0.7)
    web = np.clip(blur(web, 0.6) * 1.3, 0, 1)
    v = 0.36 + 0.06 * CLOUD + 0.55 * web
    return rgba(ramp(v), 160 + 80 * web)


# ---- 5. Facets: crystal shards; a light turns and each facet flashes as it faces it ------------------------
def facets(t, n, seed, edge_w=1.4):
    r = np.random.default_rng(seed)
    pts = r.uniform(0, N, (n, 2))
    nrm = r.normal(0, 1, (n, 3)); nrm[:, 2] = np.abs(nrm[:, 2]) * 2.2
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    cell, d1, d2 = voronoi(pts)
    a = TAU * t
    L = np.array([math.cos(a) * 0.7, math.sin(a) * 0.7, 0.7]); L /= np.linalg.norm(L)
    lit = nrm @ L
    v = 0.25 + 0.65 * (lit[cell] ** 3)
    edge = smooth(edge_w + 1, edge_w, d2 - d1)
    v = v + 0.35 * edge
    return rgba(ramp(v), 195 + 40 * edge)


@design("F1", "crystal facets, turning light", 3)
def _(t):
    return facets(t, 44, 71)


@design("F2", "big shards", 3)
def _(t):
    return facets(t, 14, 72, 1.8)


# ---- 6. Hex: a faint honeycomb, a ring of light pulses out across it --------------------------------------
@design("H1", "hex shield cells, pulse ring", 2)
def _(t):
    # staggered rows 32 px apart, 32 px across: nearly regular hexagons that tile the 4 x 4 blocks
    sx, rows = 32, 8
    sy = N / rows
    pts = [(i * sx + (sx / 2 if j % 2 else 0), j * sy) for i in range(N // sx) for j in range(rows)]
    cell, d1, d2 = voronoi(pts)
    line = smooth(2.2, 0.6, d2 - d1)
    rad = np.hypot(wrapd(xx, 128), wrapd(yy, 128))
    R = 182.0
    ring = (t * R)
    pulse = np.exp(-((rad - ring) / 10) ** 2) * math.sin(math.pi * t)
    cellglow = np.exp(-((rad - ring) / 28) ** 2) * math.sin(math.pi * t) * 0.18
    v = 0.42 + 0.05 * CLOUD + line * (0.18 + 0.7 * pulse) + cellglow
    return rgba(ramp(v), 190 + 50 * line)


# ---- 7. Circuit: thin traces with pads; light runs along them ---------------------------------------------
@design("T1", "circuit traces, running light", 2)
def _(t, _cache={}):
    if "tr" not in _cache:
        r = np.random.default_rng(81)
        trs = []
        for _ in range(46):
            x, y = int(r.integers(0, 32)) * 8, int(r.integers(0, 32)) * 8
            d = int(r.integers(0, 4)); path = [(x, y)]
            for _ in range(int(r.integers(4, 12))):
                if r.random() < 0.35:
                    d = (d + (1 if r.random() < 0.5 else 3)) % 4
                dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][d]
                for _ in range(8):
                    x, y = (x + dx) % N, (y + dy) % N
                    path.append((x, y))
            trs.append(path)
        _cache["tr"] = trs
    v = 0.44 + 0.05 * CLOUD
    rgb = ramp(v); a = np.full((N, N), 200.0)
    for k, path in enumerate(_cache["tr"]):
        L = len(path); ph = (k * 0.37) % 1
        for s, (x, y) in enumerate(path):
            u = ((s / L) - (t * 2 + ph)) % 1
            glow = math.exp(-(min(u, 1 - u) / 0.07) ** 2)
            c = DEEP * 0.4 + (HI - DEEP * 0.4) * (0.4 + 0.6 * glow)
            rgb[y, x] = c
        for (x, y) in (path[0], path[-1]):
            rgb[(y - 1) % N:(y + 2), (x - 1) % N:(x + 2)] = LIGHT
    return rgba(rgb, a)


# ---- 8. Scan: plain jade with fine scanlines and a bright band sweeping up (a hologram) --------------------
@design("S1", "hologram scan band (minimal)", 2)
def _(t):
    v = 0.48 + 0.05 * CLOUD - 0.06 * ((yy % 4) < 1)
    d = (yy + t * N) % N
    band = np.exp(-((np.minimum(d, N - d)) / 9) ** 2)
    trail = np.exp(-(((yy + t * N) % N) / 40)) * 0.25
    v = v + 0.55 * band + trail
    return rgba(ramp(v), 185 + 60 * band)


# ---- 9. Arcs: lightning crackles across now and then (Kyle Rayner's energy) --------------------------------
def bolt(r, x0, y0, x1, y1, rough, depth):
    pts = [(x0, y0), (x1, y1)]
    for _ in range(depth):
        new = []
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            mx, my = (ax + bx) / 2, (ay + by) / 2
            L = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / (L + 1e-6), (bx - ax) / (L + 1e-6)
            o = r.normal(0, rough * L)
            new += [(ax, ay), (mx + nx * o, my + ny * o)]
        new.append(pts[-1]); pts = new
    return pts


@design("E1", "energy arcs crackling", 1)
def _(t, _cache={}):
    if "arcs" not in _cache:
        r = np.random.default_rng(91)
        arcs = []
        for k in range(14):
            x0, y0 = r.uniform(0, N, 2); ang = r.uniform(0, TAU); L = r.uniform(30, 90)
            pts = bolt(r, x0, y0, x0 + math.cos(ang) * L, y0 + math.sin(ang) * L, 0.22, 5)
            arcs.append((pts, int(r.integers(0, F)), int(r.integers(2, 5))))
        _cache["arcs"] = arcs
    f = int(round(t * F)) % F
    img = Image.new("L", (N * 3, N * 3), 0); dr = ImageDraw.Draw(img)
    for pts, start, life in _cache["arcs"]:
        age = (f - start) % F
        if age < life:
            s = 255 if age == 0 else int(255 * (1 - age / life))
            for ox in (0, N, 2 * N):
                for oy in (0, N, 2 * N):
                    dr.line([(x + ox, y + oy) for x, y in pts], fill=s, width=1)
    m = np.asarray(img).astype(float)[N:2 * N, N:2 * N] / 255
    glow = np.clip(blur(m, 2.5) * 4, 0, 1)
    v = 0.4 + 0.06 * CLOUD + 0.25 * glow + 0.6 * m
    return rgba(ramp(v), 195 + 55 * np.maximum(m, glow * 0.5))


# ---- 10. Core: every block glows at its edges and is deep inside; the light breathes ------------------------
@design("B1", "block glow, bright edges, breathing (minimal)", 3)
def _(t):
    lx, ly = xx % B, yy % B
    d = np.minimum(np.minimum(lx, B - 1 - lx), np.minimum(ly, B - 1 - ly))
    breathe = 0.85 + 0.15 * math.sin(TAU * t)
    v = 0.3 + 0.04 * CLOUD + 0.6 * np.exp(-d / 7) * breathe
    return rgba(ramp(v), 170 + 70 * np.exp(-d / 7))


# ---- 11. Motes: smooth jade with sparks drifting up through it, twinkling ---------------------------------
@design("D1", "sparks drifting up (minimal)", 2)
def _(t, _cache={}):
    if "p" not in _cache:
        r = np.random.default_rng(101)
        _cache["p"] = (r.uniform(0, N, 70), r.uniform(0, N, 70), r.integers(1, 3, 70), r.uniform(0, 1, 70), r.integers(1, 4, 70))
    px, py, sp, ph, tw = _cache["p"]
    m = np.zeros((N, N))
    for x, y, s, p, w in zip(px, py, sp, ph, tw):
        yy_ = (y - t * N * s) % N
        b = 0.5 + 0.5 * math.sin(TAU * (w * t + p))
        xi, yi = int(x) % N, int(yy_) % N
        m[yi, xi] += b
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m[(yi + dy) % N, (xi + dx) % N] += b * 0.45
    glow = np.clip(blur(m, 1.6) * 6, 0, 1)
    v = 0.44 + 0.06 * CLOUD + 0.2 * glow + 0.5 * np.clip(m, 0, 1)
    return rgba(ramp(v), 195 + 50 * np.clip(m, 0, 1))


# ---- 12. Flow: long soft streaks rising up the faces, like light pouring (the statue's flowing energy) -----
@design("L1", "rising light streaks", 2)
def _(t):
    def streaks(seed, speed, sharp):
        rr = np.random.default_rng(seed)
        amp = np.where((np.abs(KX) >= 3) & (np.abs(KX) <= 24) & (np.abs(KY) <= 3), 1.0 / (np.abs(KX) + 1), 0.0)
        ph = rr.uniform(0, TAU, K.shape) + TAU * KY * speed * t
        f = np.real(np.fft.ifft2(amp * np.exp(1j * ph)))
        f = (f - f.mean()) / (f.std() + 1e-9)
        return smooth(sharp, sharp + 1.2, f)
    s = 0.7 * streaks(111, 1, 0.8) + 0.5 * streaks(112, 2, 1.2)
    v = 0.4 + 0.05 * CLOUD + 0.45 * s
    return rgba(ramp(v), 185 + 55 * np.clip(s, 0, 1))


# ---- 13. Topo: contour lines of a slowly churning field, like a map of the light ---------------------------
@design("O1", "contour lines, churning", 3)
def _(t):
    f = moving_field(1, 6, 1.5, 121, t, 1)
    c = np.abs(((f * 3) % 1) - 0.5)
    line = smooth(0.08, 0.02, c)
    v = 0.4 + 0.06 * CLOUD + 0.4 * line
    return rgba(ramp(v), 190 + 50 * line)


# ---- 14. Weave: a fine cross-hatched energy weave with a slow shimmer (woven hard light) ------------------
@design("W1", "woven light, shimmering", 3)
def _(t):
    u = np.sin(TAU * (xx + yy) / 16); w = np.sin(TAU * (xx - yy) / 16)
    over = ((np.floor((xx + yy) / 16) + np.floor((xx - yy) / 16)) % 2) == 0
    thread = np.where(over, np.abs(u), np.abs(w))
    shimmer = 0.5 + 0.5 * np.sin(TAU * ((xx + 2 * yy) / N + t))
    v = 0.36 + 0.05 * CLOUD + 0.32 * thread * (0.6 + 0.4 * shimmer)
    return rgba(ramp(v), 195 + 30 * thread)


# ---- 15. Fractured: dark crack lines that branch, light seeping out of them (cracked hard light) ----------
@design("X1", "fractured, light seeping through cracks", 3)
def _(t):
    r = np.random.default_rng(131)
    pts = r.uniform(0, N, (26, 2))
    cell, d1, d2 = voronoi(pts)
    crack = smooth(1.6, 0.4, d2 - d1)
    seep = np.exp(-(d2 - d1) / 6)
    pulse = 0.6 + 0.4 * math.sin(TAU * t)
    base = 0.36 + 0.05 * CLOUD + 0.06 * (cell % 3)
    v = base + 0.35 * seep * pulse
    rgb = ramp(v)
    rgb = np.where(crack[..., None] > 0.5, HI * (0.75 + 0.25 * pulse), rgb)
    return rgba(rgb, 200 + 40 * crack)


# ---- references J kept --------------------------------------------------------------------------------------
@design("K5", "J kept: R1 lines in K5 shadow haze (reference)", 3)
def _(t, _cache={}):
    return None


@design("K1", "J's pick: R2 small fragments in K1 dark jade (reference)", 2)
def _(t, _cache={}):
    return None


def reference(path, f):
    strip = np.asarray(Image.open(path).convert("RGBA")).astype(float)
    return strip[f * N:(f + 1) * N]


if __name__ == "__main__":
    ref_dir = sys.argv[2] if len(sys.argv) > 2 else None
    info = []
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    for key, name, ft, fn in DESIGNS:
        if only and key not in only:
            continue
        frames = []
        for f in range(F):
            fr = fn(f / F)
            if fr is None:
                if not ref_dir:
                    break
                lines = reference(os.path.join(ref_dir, {"K5": "lines_R1_K5.png", "K1": "lines_R2_K1.png"}[key]), f)
                base = np.asarray(Image.open(os.path.join(ref_dir, "face_R1_W.png")).convert("RGBA")).astype(float)
                # rebuild the jade underneath (face_* has W lines baked in): use the cloudy jade instead
                v = 0.5 + 0.06 * CLOUD
                under = rgba(ramp(v * 0.95), np.full((N, N), 208.0))
                ta = lines[..., 3:4] / 255
                fr = np.concatenate([lines[..., :3] * ta + under[..., :3] * (1 - ta), under[..., 3:]], -1)
            frames.append(fr)
        if len(frames) < F:
            continue
        strip = np.concatenate(frames, 0).clip(0, 255).astype(np.uint8)
        Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{key}.png"), optimize=True)
        Image.fromarray(strip[:N], "RGBA").save(os.path.join(OUT, f"still_{key}.png"))
        bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)),
                                    Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(F)]
        bg[0].save(os.path.join(OUT, f"face_{key}.gif"), save_all=True, append_images=bg[1:], duration=ft * 50, loop=0)
        info.append({"key": key, "label": f"{key}  {name}", "frametime": ft})
        print(key, "done", flush=True)
    json.dump(info, open(os.path.join(OUT, "designs.json"), "w"), indent=1)
