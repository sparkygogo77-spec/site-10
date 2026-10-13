"""Construct designs, round three (J, 2026-10-12): keep O1 G2 W1 H1 D1, bring back the bricks with P1/P2 as
inspiration, show them all in different green colour combinations and with different fill animations, a
negative G2 (dark lines, brights turned dark) as see-through jelly, and more new designs.

    python tools/construct_designs3.py OUTDIR

Every design is drawn once as a tone map (0..1) plus alpha by tools/construct_designs.py's functions, then
coloured with a palette and given a fill animation, so all variants share exactly the same shapes:
    face_<design>_<palette>.png        24-frame strip, 256 px = 4 x 4 blocks, its own motion
    face_<design>_fill<k>.png          the same in jade with fill animation k
    face_<design>_jelly.png            see-through jelly alpha (thin in the middle of each block, firm rim)
Also: tests.json (seam, loop and motion checks for every strip) and set.json (what to show in Blender).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs.py", os.path.join(OUT, "_r2")]
sys.path.insert(0, HERE)
import construct_designs as CD  # noqa: E402
sys.argv = _argv

N, F, B, TAU = CD.N, CD.F, CD.B, CD.TAU
xx, yy, CLOUD = CD.xx, CD.yy, CD.CLOUD
smooth, blur, field, moving_field, voronoi, wrapd = CD.smooth, CD.blur, CD.field, CD.moving_field, CD.voronoi, CD.wrapd

# designs return rgba(ramp(v), a); with a grey ramp the red channel IS the tone v
CD.ramp = lambda v, *a, **k: np.repeat((np.clip(v, 0, 1) * 255)[..., None], 3, -1)
ramp = CD.ramp
rgba = CD.rgba

PALETTES = {   # deep, mid, light, highlight
    "jade":    [(4, 48, 26), (18, 128, 62), (92, 214, 132), (205, 255, 222)],
    "emerald": [(2, 28, 14), (8, 100, 52), (38, 196, 106), (168, 255, 198)],
    "mint":    [(36, 104, 76), (96, 186, 142), (168, 234, 194), (236, 255, 242)],
    "lime":    [(8, 38, 10), (38, 98, 24), (150, 222, 40), (232, 255, 140)],
    "teal":    [(2, 44, 44), (10, 118, 98), (60, 210, 170), (190, 255, 236)],
    "neon":    [(0, 14, 5), (4, 58, 20), (40, 255, 92), (205, 255, 214)],
}
STOPS = (0, 0.45, 0.8, 1.0)


def colour(v, pal):
    c = [np.array(x, float) for x in PALETTES[pal]]
    v = np.clip(v, 0, 1)[..., None]
    out = np.zeros(v.shape[:-1] + (3,))
    for i in range(3):
        a, b = STOPS[i], STOPS[i + 1]
        u = np.clip((v - a) / (b - a), 0, 1)
        out = np.where((v >= a) & (v <= b), c[i] + (c[i + 1] - c[i]) * u, out)
    return out


# ---- bricks (J: "bring back my bricks", P1 and P2 as inspiration) --------------------------------------------
def brick_layout(courses, per_row, seed, split=0.0):
    """Brick ids for one tile: `courses` per block, `per_row` bricks per course per block, staggered; with
    `split`, some bricks are cut into smaller plates (P2's dense panels)."""
    r = np.random.default_rng(seed)
    bh, bw = B // courses, B // per_row
    row = (yy // bh).astype(int)
    shift = np.where(row % 2 == 1, bw // 2, 0)
    sx = (xx + shift) % N
    col = (sx // bw).astype(int)
    ids = row * 1000 + col
    lx, ly = sx % bw, yy % bh
    if split:
        cut = r.random((N // bh + 1, N // bw + 1)) < split
        vert = r.random((N // bh + 1, N // bw + 1)) < 0.5
        c = cut[row, col]; v = vert[row, col]
        half = np.where(v, lx >= bw // 2, ly >= bh // 2)
        ids = np.where(c, ids * 2 + half, ids * 2)
    return ids, lx, ly, bw, bh


def bricks(t, courses, per_row, seed, split, mortar=2, rivets=False, inset=False):
    ids, lx, ly, bw, bh = brick_layout(courses, per_row, seed, split)
    r = np.random.default_rng(seed + 1)
    tone = r.uniform(-0.09, 0.09, ids.max() + 1)
    seam = (np.roll(ids, 1, 0) != ids) | (np.roll(ids, 1, 1) != ids)
    for k in range(1, mortar):
        seam |= np.roll(seam, 1, 0) | np.roll(seam, 1, 1)
    lip = (np.roll(seam, 1, 0) | np.roll(seam, 1, 1)) & ~seam
    shade = (np.roll(seam, -1, 0) | np.roll(seam, -1, 1)) & ~seam & ~lip
    v = 0.48 + tone[ids] + 0.05 * CLOUD
    v = np.where(lip, v + 0.2, v)
    v = np.where(shade, v - 0.09, v)
    if inset:      # a sunken panel in the middle of each brick (P1's plates)
        e = np.minimum(np.minimum(lx, bw - 1 - lx), np.minimum(ly, bh - 1 - ly))
        ring = (e >= 3) & (e < 4)
        v = np.where(ring, v - 0.12, v)
        v = np.where(e >= 4, v - 0.04, v)
    # glowing mortar: hard light holding the bricks together, a pulse travelling along it
    wave = 0.5 + 0.5 * np.cos(TAU * ((xx + yy) / N - t))
    v = np.where(seam, 0.78 + 0.2 * wave, v)
    if rivets:
        rv = np.zeros((N, N), bool)
        for cx in (3, bw - 4):
            for cy in (2, bh - 3):
                rv |= (lx == cx) & (ly == cy)
        v = np.where(rv & ~seam, 0.97, v)
    # P1's glint sweeping across
    d = ((xx + yy) - t * 2 * N) % (2 * N)
    g = np.exp(-((np.minimum(d, 2 * N - d)) / 14) ** 2)
    v = v + (1 - v) * g * 0.45 * ~seam
    a = np.where(seam, 235, 200.0)
    return rgba(ramp(v), a)


EXTRA = {}


def extra(key, name, ft=2):
    def deco(fn):
        EXTRA[key] = (name, ft, fn)
        return fn
    return deco


extra("BR1", "bricks, glowing mortar, glint")(lambda t: bricks(t, 4, 2, 201, 0.0))
extra("BR2", "bricks cut into plates (P2), rivets")(lambda t: bricks(t, 4, 2, 202, 0.55, mortar=1, rivets=True))
extra("BR3", "big blocks with sunken panels (P1)")(lambda t: bricks(t, 2, 1, 203, 0.0, inset=True, rivets=True))


@extra("N1", "jelly bubbles rising", 2)
def _(t, _c={}):
    if "p" not in _c:
        r = np.random.default_rng(301)
        _c["p"] = (r.uniform(0, N, 40), r.uniform(0, N, 40), r.uniform(3, 9, 40), r.integers(1, 3, 40))
    v = 0.42 + 0.06 * CLOUD
    for x, y, rad, sp in zip(*_c["p"]):
        cy = (y - t * N * sp) % N
        d = np.hypot(wrapd(xx, x), wrapd(yy, cy))
        rim = np.exp(-((d - rad) / 0.9) ** 2)
        spec = np.exp(-(np.hypot(wrapd(xx, x - rad * 0.4), wrapd(yy, cy - rad * 0.4)) / (rad * 0.25)) ** 2)
        v = v + 0.35 * rim + 0.4 * spec + 0.06 * (d < rad)
    return rgba(ramp(v), 175 + 50 * np.clip(v - 0.45, 0, 1))


@extra("N2", "drops: rings spreading on jelly", 2)
def _(t, _c={}):
    if "p" not in _c:
        r = np.random.default_rng(302)
        _c["p"] = (r.uniform(0, N, 12), r.uniform(0, N, 12), r.uniform(0, 1, 12))
    v = 0.42 + 0.06 * CLOUD
    for x, y, ph in zip(*_c["p"]):
        age = (t + ph) % 1
        d = np.hypot(wrapd(xx, x), wrapd(yy, y))
        for k in range(3):
            rr = age * 70 - k * 9
            if rr > 0:
                v = v + 0.32 * (1 - age) * np.exp(-((d - rr) / 1.6) ** 2)
    return rgba(ramp(v), 185 + 40 * np.clip(v - 0.45, 0, 1))


@extra("N3", "scales, shimmering", 3)
def _(t):
    s = 16
    row = np.floor(yy / (s / 2))
    cx = (np.floor((xx + (row % 2) * s / 2) / s) * s + s / 2 - (row % 2) * s / 2)
    cy = row * (s / 2)
    d = np.hypot(xx - cx, yy - cy)
    edge = smooth(s * 0.62, s * 0.55, d) * (1 - smooth(s * 0.55, s * 0.5, d))
    shim = 0.5 + 0.5 * np.sin(TAU * (cx / N + 2 * cy / N - t))
    v = 0.36 + 0.05 * CLOUD + 0.22 * (1 - d / s) * shim + 0.3 * edge
    return rgba(ramp(v), 195 + 30 * edge)


@extra("N4", "constellation: stars joined by threads", 2)
def _(t, _c={}):
    from PIL import ImageDraw
    if "p" not in _c:
        r = np.random.default_rng(304)
        pts = r.uniform(0, N, (34, 2))
        pairs = []
        for i, (x, y) in enumerate(pts):
            d = [(math.hypot(min(abs(x - a), N - abs(x - a)), min(abs(y - b), N - abs(y - b))), j) for j, (a, b) in enumerate(pts) if j != i]
            for _, j in sorted(d)[:2]:
                pairs.append((i, j))
        _c["p"] = (pts, pairs, r.uniform(0, 1, 34))
    pts, pairs, ph = _c["p"]
    img = Image.new("L", (N * 3, N * 3)); dr = ImageDraw.Draw(img)
    for i, j in pairs:
        (x0, y0), (x1, y1) = pts[i], pts[j]
        if abs(x1 - x0) > N / 2: x1 -= N * np.sign(x1 - x0)
        if abs(y1 - y0) > N / 2: y1 -= N * np.sign(y1 - y0)
        for ox in (0, N, 2 * N):
            for oy in (0, N, 2 * N):
                dr.line([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy)], fill=200, width=1)
    m = np.asarray(img).astype(float)[N:2 * N, N:2 * N] / 255
    star = np.zeros((N, N))
    for (x, y), p in zip(pts, ph):
        b = 0.5 + 0.5 * math.sin(TAU * (t * 2 + p))
        star += b * np.exp(-(np.hypot(wrapd(xx, x), wrapd(yy, y)) / 2.6) ** 2)
    run = 0.35 + 0.65 * (0.5 + 0.5 * np.cos(TAU * ((xx + 2 * yy) / N - t))) ** 3   # light running along the threads
    v = 0.36 + 0.05 * CLOUD + 0.45 * m * run + 0.6 * np.clip(star, 0, 1)
    return rgba(ramp(v), 190 + 50 * np.clip(star + m, 0, 1))


@extra("N5", "aurora bands drifting", 3)
def _(t):
    w = moving_field(1, 4, 1.8, 305, t, 1)
    bands = 0.5 + 0.5 * np.sin(TAU * (yy / 64 * 2 + 0.35 * w))
    v = 0.36 + 0.05 * CLOUD + 0.35 * bands ** 3
    return rgba(ramp(v), 180 + 50 * bands ** 3)


@extra("N6", "truss struts, light running along", 2)
def _(t):
    p = 32
    a = (xx + yy) % p; b = (xx - yy) % p
    line = np.maximum(smooth(2.2, 0.8, np.minimum(a, p - a)), smooth(2.2, 0.8, np.minimum(b, p - b)))
    run = 0.5 + 0.5 * np.cos(TAU * ((xx + yy) / N * 2 - 2 * t))
    v = 0.38 + 0.05 * CLOUD + line * (0.25 + 0.45 * run ** 4)
    return rgba(ramp(v), 190 + 45 * line)


# ---- tone maps ---------------------------------------------------------------------------------------------
def frames_of(key):
    for k, name, ft, fn in CD.DESIGNS:
        if k == key:
            return name, ft, [fn(f / F) for f in range(F)]
    name, ft, fn = EXTRA[key]
    return name, ft, [fn(f / F) for f in range(F)]


def tone(fr):
    return fr[..., 0] / 255.0, fr[..., 3]


# ---- fill animations: how the pattern fills each block (on top of the design's own motion) ---------------------
lx, ly = xx % B, yy % B
rad = np.hypot(lx - (B - 1) / 2, ly - (B - 1) / 2) / (B * 0.71)
DISS = blur(np.random.default_rng(7).random((N, N)), 1.2)
DISS = (DISS.argsort(None).argsort().reshape(N, N)) / (N * N)     # evenly spread 0..1
FILLS = {
    "fill1": "rises up each block, then drains",
    "fill2": "blooms out from each block's centre",
    "fill3": "dissolves in and out, sparkling edge",
    "fill4": "row by row, like a printer",
    "fill5": "breathes, the whole pattern pulses",
    "fill6": "shine sweeps across",
}


def fill_mask(kind, t):
    """(m, edge): how lit the pattern is (0..1) and a bright front."""
    level = 2 * t if t < 0.5 else 2 - 2 * t                 # 0 -> 1 -> 0 over the loop
    if kind == "fill1":
        h = 1 - ly / (B - 1)                                 # 0 at the bottom of a block, 1 at the top
        m = smooth(level + 0.04, level - 0.04, h)
        return m, np.exp(-((h - level) / 0.025) ** 2) * (0.05 < level < 0.97)
    if kind == "fill2":
        m = smooth(level + 0.04, level - 0.04, rad)
        return m, np.exp(-((rad - level) / 0.03) ** 2) * (0.05 < level < 0.97)
    if kind == "fill3":
        m = smooth(level + 0.02, level - 0.02, DISS)
        return m, np.exp(-((DISS - level) / 0.012) ** 2) * (0.03 < level < 0.98)
    if kind == "fill4":
        rows = np.floor(ly / 4) / 16
        on = rows < level * 1.02
        cur = (np.abs(rows - np.floor(level * 16) / 16) < 1e-6) & (lx / B < (level * 16) % 1)
        return np.where(on | cur, 1.0, 0.0), cur * 1.0
    if kind == "fill5":
        return np.full((N, N), 0.55 + 0.45 * math.sin(TAU * t)), np.zeros((N, N))
    if kind == "fill6":
        d = ((xx - yy) - t * N) % N                           # wraps with the tile
        g = np.exp(-((np.minimum(d, N - d)) / 10) ** 2)
        return np.ones((N, N)), g
    raise KeyError(kind)


def apply_fill(v, a, kind, t):
    m, edge = fill_mask(kind, t)
    base_v, base_a = 0.36 + 0.05 * CLOUD, 150.0
    v2 = base_v + (v - base_v) * (0.15 + 0.85 * m) + 0.55 * edge
    a2 = base_a + (a - base_a) * (0.3 + 0.7 * m) + 60 * edge
    return v2, a2


def jelly(v, a):
    """See-through jelly: thin in the middle of each block, a firm bright rim, glossy top-left."""
    e = np.minimum(np.minimum(lx, B - 1 - lx), np.minimum(ly, B - 1 - ly))
    rim = np.exp(-e / 4.0)
    gloss = np.exp(-(((lx - 14) / 10) ** 2 + ((ly - 12) / 6) ** 2))
    a2 = np.clip(a * 0.45 + 150 * rim + 50 * gloss, 0, 245)
    v2 = v + 0.18 * rim + 0.3 * gloss
    return v2, a2


def negative(v):
    """G2 flipped: the bright web turns into dark lines and the dark jade turns bright."""
    return np.clip(1.22 - v, 0, 1)


# ---- tests ---------------------------------------------------------------------------------------------------
def test(strip):
    f = strip.astype(float)
    fr = f.reshape(F, N, N, 4)
    steps = [np.abs(fr[i + 1] - fr[i]).mean() for i in range(F - 1)]
    wrap = np.abs(fr[0] - fr[-1]).mean()
    step = float(np.mean(steps))
    # the tile's wrap edge must look like any other edge inside it: compare it with the block edges at 64,
    # 128 and 192 (where per-block patterns put their lines too) and with the average neighbour step
    col_in = max(np.abs(np.diff(fr, axis=2)).mean(), max(np.abs(fr[:, :, k] - fr[:, :, k - 1]).mean() for k in (64, 128, 192)))
    col_seam = np.abs(fr[:, :, 0] - fr[:, :, -1]).mean()
    row_in = max(np.abs(np.diff(fr, axis=1)).mean(), max(np.abs(fr[:, k] - fr[:, k - 1]).mean() for k in (64, 128, 192)))
    row_seam = np.abs(fr[:, 0] - fr[:, -1]).mean()
    res = {"motion": round(step, 2), "loop_jump": float(round(wrap / max(step, 0.3), 2)),
           "seam_x": float(round(col_seam / max(col_in, 0.3), 2)), "seam_y": float(round(row_seam / max(row_in, 0.3), 2)),
           "alpha_min": int(fr[..., 3].min()), "alpha_mean": int(fr[..., 3].mean())}
    res["pass"] = bool(res["motion"] > 0.15 and res["loop_jump"] < 2.5 and res["seam_x"] < 2.5 and res["seam_y"] < 2.5)
    return res


def save(name, vs, as_, pal, ft):
    frames = [np.concatenate([colour(v, pal), np.clip(a, 0, 255)[..., None]], -1) for v, a in zip(vs, as_)]
    strip = np.concatenate(frames, 0).clip(0, 255).astype(np.uint8)
    Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{name}.png"), optimize=True)
    bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB")
          for i in range(F)]
    bg[0].save(os.path.join(OUT, f"face_{name}.gif"), save_all=True, append_images=bg[1:], duration=ft * 50, loop=0)
    return test(strip)


if __name__ == "__main__":
    KEEP = ["O1", "G2", "W1", "H1", "D1", "BR1"]
    NEW = ["G2N", "BR2", "BR3", "N1", "N2", "N3", "N4", "N5", "N6"]
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    tests, sets = {}, {"palettes": [], "fills": [], "new": [], "jelly": []}
    names = {}
    for key in KEEP + ["G2N"] + NEW[1:]:
        if only and key not in only:
            continue
        src = "G2" if key == "G2N" else key
        name, ft, frs = frames_of(src)
        vs, as_ = zip(*[tone(fr) for fr in frs])
        if key == "G2N":
            name = "G2 negative: dark lines, brights turned dark"
            vs = [negative(v) for v in vs]
        names[key] = name
        if key in KEEP:
            for pal in PALETTES:
                tests[f"{key}_{pal}"] = save(f"{key}_{pal}", vs, as_, pal, ft)
                sets["palettes"].append(f"{key}_{pal}")
            for fk in FILLS:
                fv, fa = zip(*[apply_fill(v, a, fk, f / F) for f, (v, a) in enumerate(zip(vs, as_))])
                tests[f"{key}_{fk}"] = save(f"{key}_{fk}", fv, fa, "jade", ft)
                sets["fills"].append(f"{key}_{fk}")
        else:
            tests[f"{key}_jade"] = save(f"{key}_jade", vs, as_, "jade", ft)
            sets["new"].append(f"{key}_jade")
        if key in ("G2N", "G2", "N1", "N2", "O1", "BR1"):
            jv, ja = zip(*[jelly(v, a) for v, a in zip(vs, as_)])
            pal = "jade"
            tests[f"{key}_jelly"] = save(f"{key}_jelly", jv, ja, pal, ft)
            sets["jelly"].append(f"{key}_jelly")
        print(key, "done", flush=True)
    json.dump({"names": names, "palettes": list(PALETTES), "fills": FILLS, "sets": sets}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
