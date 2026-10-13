"""Construct designs, round four (J, 2026-10-12): his picks darker, smoother and slower ("they don't have to be
so animated", "H1 neon looks good, smooth"), G2 and O1 gliding in one direction instead of churning, BR1 in
blue too, G2 negative and N3 as Yellow Lantern textures, N2 jelly whose rings blend through each other, and
more designs grown from his picks.

    python tools/construct_designs4.py OUTDIR

Same machinery as construct_designs3.py (tone map + palette), with:
- darker palettes and a smooth (smoothstep) blend between the colour stops instead of straight lines;
- per-strip frame count and frametime: a loop now lasts 4.8-9.6 s instead of 1.2-2.4 s;
- face_<id>.png strips, face_<id>.gif, tests.json, set.json (sections and frametimes for Blender).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs3.py", os.path.join(OUT, "_r3")]
sys.path.insert(0, HERE)
import construct_designs3 as D3  # noqa: E402
sys.argv = _argv
CD = D3.CD
N, B, TAU = D3.N, D3.B, D3.TAU
xx, yy, CLOUD = D3.xx, D3.yy, D3.CLOUD
smooth, blur, moving_field, voronoi, wrapd, ramp, rgba = D3.smooth, D3.blur, D3.moving_field, D3.voronoi, D3.wrapd, D3.ramp, D3.rgba

# darker, with five stops so the blend has a soft shoulder at both ends
PALETTES = {
    "jade":    [(1, 20, 10), (6, 58, 30), (16, 112, 56), (70, 186, 112), (175, 245, 200)],
    "emerald": [(0, 12, 6), (3, 44, 22), (8, 96, 48), (34, 168, 90), (150, 240, 182)],
    "neon":    [(0, 6, 2), (1, 26, 9), (4, 70, 24), (28, 214, 80), (190, 255, 205)],
    "lime":    [(3, 16, 4), (12, 44, 10), (36, 92, 20), (124, 196, 34), (220, 250, 130)],
    "forest":  [(2, 14, 7), (8, 40, 20), (24, 84, 42), (84, 160, 92), (190, 236, 196)],
    "blue":    [(0, 6, 24), (2, 24, 72), (10, 70, 160), (60, 160, 245), (200, 236, 255)],
    "yellow":  [(20, 10, 0), (66, 38, 0), (150, 100, 4), (236, 190, 36), (255, 246, 180)],
    "amber":   [(16, 6, 0), (54, 22, 0), (128, 66, 2), (226, 146, 24), (255, 226, 150)],
}
STOPS = (0.0, 0.25, 0.5, 0.78, 1.0)


def colour(v, pal):
    c = [np.array(x, float) for x in PALETTES[pal]]
    v = np.clip(v, 0, 1)
    out = np.zeros(v.shape + (3,))
    for i in range(4):
        a, b = STOPS[i], STOPS[i + 1]
        u = np.clip((v - a) / (b - a), 0, 1)
        u = u * u * (3 - 2 * u)                       # smooth blend between the stops
        m = ((v >= a) & (v <= b))[..., None]
        out = np.where(m, c[i] + (c[i + 1] - c[i]) * u[..., None], out)
    return out


def base_of(kind):
    return {"D": 0.44 + 0.06 * CLOUD, "W": 0.36 + 0.05 * CLOUD, "N": 0.36 + 0.05 * CLOUD, "H": 0.42 + 0.05 * CLOUD}[kind]


def tone_fn(key):
    """t -> (v, a) for a design key from round two/three."""
    for k, name, ft, fn in CD.DESIGNS:
        if k == key:
            return lambda t: D3.tone(fn(t))
    name, ft, fn = D3.EXTRA[key]
    return lambda t: D3.tone(fn(t))


DESIGNS = {}


def design(key, name):
    def deco(fn):
        DESIGNS[key] = (name, fn)
        return fn
    return deco


for k in ("H1", "BR1", "D1", "W1", "N3", "N5"):
    design(k, k)(tone_fn(k))


# ---- G2 and O1 gliding: the shape slides one way instead of churning ----------------------------------------
@design("G2g", "G2 caustic web gliding diagonally")
def _(t):
    w1 = moving_field(2, 7, 1.5, 61, t, 0, drift=(1, 1))
    w2 = moving_field(2, 7, 1.5, 62, t, 0, drift=(1, 1))
    web = np.maximum(np.exp(-(w1 / 0.09) ** 2), np.exp(-(w2 / 0.09) ** 2) * 0.7)
    web = np.clip(blur(web, 0.6) * 1.3, 0, 1)
    return 0.36 + 0.06 * CLOUD + 0.55 * web, 160 + 80 * web


@design("G2s", "G2 two webs sliding past each other")
def _(t):
    w1 = moving_field(2, 7, 1.5, 61, t, 0, drift=(1, 0))
    w2 = moving_field(2, 7, 1.5, 62, t, 0, drift=(0, 1))
    web = np.maximum(np.exp(-(w1 / 0.09) ** 2), np.exp(-(w2 / 0.09) ** 2) * 0.7)
    web = np.clip(blur(web, 0.6) * 1.3, 0, 1)
    return 0.36 + 0.06 * CLOUD + 0.55 * web, 160 + 80 * web


@design("O1g", "O1 contours drifting upward")
def _(t):
    f = moving_field(1, 6, 1.5, 121, t, 0, drift=(0, 1))
    c = np.abs(((f * 3) % 1) - 0.5)
    line = smooth(0.08, 0.02, c)
    return 0.4 + 0.06 * CLOUD + 0.4 * line, 190 + 50 * line


@design("G2Ng", "G2 negative gliding (dark lines)")
def _(t):
    v, a = DESIGNS["G2g"][1](t)
    return np.clip(1.22 - v, 0, 1), a


# ---- N2 jelly v2: the rings soften into each other instead of stacking -------------------------------------
@design("N2b", "drops on jelly, rings blending through each other")
def _(t, _c={}):
    if "p" not in _c:
        r = np.random.default_rng(302)
        _c["p"] = (r.uniform(0, N, 12), r.uniform(0, N, 12), r.uniform(0, 1, 12))
    keep = np.ones((N, N))
    for x, y, ph in zip(*_c["p"]):
        age = (t + ph) % 1
        d = np.hypot(wrapd(xx, x), wrapd(yy, y))
        for k in range(3):
            rr = age * 70 - k * 11
            if rr > 0:
                ring = (1 - age) ** 1.5 * np.exp(-((d - rr) / 3.2) ** 2) * (0.8 - 0.2 * k)
                keep *= 1 - 0.85 * ring              # soft union: overlaps add up gently, never stack bright
    glow = blur(1 - keep, 1.2)
    v = 0.42 + 0.06 * CLOUD + 0.85 * glow
    return v, 175 + 50 * np.clip(glow * 2, 0, 1)


# ---- new, grown from J's picks ------------------------------------------------------------------------------
def mix_detail(key_a, key_b, kb, wb):
    fa, fb = DESIGNS[key_a][1], DESIGNS[key_b][1]

    def fn(t):
        va, aa = fa(t)
        vb, ab = fb(t)
        return va + wb * np.clip(vb - base_of(kb), 0, 1), np.maximum(aa, ab * 0.9)
    return fn


design("BRD", "BR1 bricks with D1 sparks rising through")(mix_detail("BR1", "D1", "D", 0.9))
design("HW", "H1 hex cells woven with W1")(mix_detail("H1", "W1", "W", 0.6))
design("DA", "D1 sparks over N5 aurora")(mix_detail("D1", "N5", "N", 0.7))


@design("BR4", "cobble stones, glowing mortar")
def _(t):
    r = np.random.default_rng(401)
    pts = [(bx + r.uniform(6, 58), by + r.uniform(6, 58)) for bx in range(0, N, B) for by in range(0, N, B) for _ in range(3)]
    cell, d1, d2 = voronoi(pts)
    tone = r.uniform(-0.08, 0.08, len(pts))
    gap = d2 - d1
    mortar = smooth(2.4, 1.0, gap)
    lip = smooth(5, 2.4, gap) * (1 - mortar)
    wave = 0.5 + 0.5 * np.cos(TAU * ((xx + yy) / N - t))
    v = 0.46 + tone[cell] + 0.05 * CLOUD - 0.12 * (d1 / 30) + 0.15 * lip
    v = v * (1 - mortar) + (0.78 + 0.18 * wave) * mortar
    return v, 200 + 35 * mortar


@design("H2", "hex cells breathing slowly, one by one")
def _(t):
    sx, rows = 32, 8
    sy = N / rows
    pts = [(i * sx + (sx / 2 if j % 2 else 0), j * sy) for i in range(N // sx) for j in range(rows)]
    cell, d1, d2 = voronoi(pts)
    ph = np.random.default_rng(402).uniform(0, 1, len(pts))
    breathe = 0.5 + 0.5 * np.sin(TAU * (t + ph[cell]))
    line = smooth(2.2, 0.6, d2 - d1)
    core = np.exp(-(d1 / 11) ** 2)
    v = 0.36 + 0.05 * CLOUD + 0.2 * line + 0.3 * core * breathe
    return v, 185 + 50 * line


@design("W2", "big slow weave")
def _(t):
    p = 32
    u = np.sin(TAU * (xx + yy) / p); w = np.sin(TAU * (xx - yy) / p)
    over = ((np.floor((xx + yy) / p) + np.floor((xx - yy) / p)) % 2) == 0
    thread = np.where(over, np.abs(u), np.abs(w))
    shimmer = 0.5 + 0.5 * np.sin(TAU * ((xx + yy) / N - t))
    return 0.34 + 0.05 * CLOUD + 0.34 * thread * (0.65 + 0.35 * shimmer), 195 + 30 * thread


@design("D2", "sparks in a slow green fog")
def _(t):
    v, a = DESIGNS["D1"][1](t)
    fog = moving_field(1, 5, 1.8, 403, t, 0, drift=(1, 0))
    return v - 0.1 + 0.1 * smooth(-0.5, 1.5, fog), a


# ---- what to make --------------------------------------------------------------------------------------------
# (design, palette, frames, frametime, section, note)
PLAN = [
    ("H1", "neon", 24, 4, "picks", "J: looks good, smooth"),
    ("BR1", "lime", 24, 4, "picks", "J: great"), ("BR1", "emerald", 24, 4, "picks", "J: great"),
    ("BR1", "jade", 24, 4, "picks", "J: great"), ("BR1", "neon", 24, 4, "picks", "J: great"),
    ("D1", "neon", 24, 4, "picks", "J's pick"), ("W1", "emerald", 24, 4, "picks", "J's pick"), ("W1", "neon", 24, 4, "picks", "J's pick"),
    ("G2g", "emerald", 32, 4, "glide", "G2, gliding"), ("G2g", "neon", 32, 4, "glide", "G2, gliding"),
    ("G2s", "jade", 32, 4, "glide", "G2, two webs sliding"), ("O1g", "emerald", 32, 4, "glide", "O1, drifting up"),
    ("O1g", "neon", 32, 4, "glide", "O1, drifting up"),
    ("BR1", "blue", 24, 4, "blue", "BR1 in blue"), ("H1", "blue", 24, 4, "blue", "H1 in blue"), ("BR4", "blue", 24, 4, "blue", "cobble in blue"),
    ("G2Ng", "yellow", 32, 4, "yellow", "G2 negative for Yellow"), ("G2Ng", "amber", 32, 4, "yellow", "G2 negative for Yellow"),
    ("N3", "yellow", 24, 4, "yellow", "N3 scales for Yellow"), ("N3", "amber", 24, 4, "yellow", "N3 scales for Yellow"),
    ("N2b", "jade", 24, 4, "jelly", "N2 jelly, rings blend through"), ("N2b", "neon", 24, 4, "jelly", "N2 jelly, rings blend through"),
    ("BRD", "neon", 24, 4, "new", "bricks + sparks"), ("HW", "emerald", 24, 4, "new", "hex + weave"),
    ("DA", "neon", 24, 4, "new", "sparks + aurora"), ("BR4", "emerald", 24, 4, "new", "cobble"),
    ("H2", "neon", 24, 5, "new", "hex breathing"), ("W2", "emerald", 24, 5, "new", "big weave"),
    ("D2", "forest", 32, 4, "new", "sparks in fog"), ("BR1", "forest", 24, 4, "new", "BR1 forest"),
]
JELLY = {("N2b", "jade"), ("N2b", "neon"), ("G2Ng", "yellow")}


def test(strip, nf):
    fr = strip.astype(float).reshape(nf, N, N, 4)
    steps = [np.abs(fr[i + 1] - fr[i]).mean() for i in range(nf - 1)]
    step = float(np.mean(steps)); wrap = np.abs(fr[0] - fr[-1]).mean()
    col_in = max(np.abs(np.diff(fr, axis=2)).mean(), max(np.abs(fr[:, :, k] - fr[:, :, k - 1]).mean() for k in (64, 128, 192)))
    row_in = max(np.abs(np.diff(fr, axis=1)).mean(), max(np.abs(fr[:, k] - fr[:, k - 1]).mean() for k in (64, 128, 192)))
    res = {"motion_per_frame": round(step, 2), "loop_jump": round(float(wrap / max(step, 0.3)), 2),
           "seam_x": round(float(np.abs(fr[:, :, 0] - fr[:, :, -1]).mean() / max(col_in, 0.3)), 2),
           "seam_y": round(float(np.abs(fr[:, 0] - fr[:, -1]).mean() / max(row_in, 0.3)), 2),
           "luma_mean": round(float((0.3 * fr[..., 0] + 0.59 * fr[..., 1] + 0.11 * fr[..., 2]).mean()), 1)}
    res["pass"] = bool(res["motion_per_frame"] > 0.1 and res["loop_jump"] < 2.5 and res["seam_x"] < 2.5 and res["seam_y"] < 2.5)
    return res


if __name__ == "__main__":
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    tests, items = {}, []
    cache = {}
    for key, pal, nf, ft, sec, note in PLAN:
        name = f"{key}_{pal}"
        if only and key not in only:
            continue
        if (key, nf) not in cache:
            cache[(key, nf)] = [DESIGNS[key][1](f / nf) for f in range(nf)]
        tv = cache[(key, nf)]
        variants = [(name, tv)]
        if (key, pal) in JELLY:
            variants.append((name + "_jelly", [D3.jelly(v, a) for v, a in tv]))
        for vname, frames in variants:
            rgba_frames = [np.concatenate([colour(v, pal), np.clip(a, 0, 255)[..., None]], -1) for v, a in frames]
            strip = np.concatenate(rgba_frames, 0).clip(0, 255).astype(np.uint8)
            Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{vname}.png"), optimize=True)
            bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(nf)]
            bg[0].save(os.path.join(OUT, f"face_{vname}.gif"), save_all=True, append_images=bg[1:], duration=ft * 50, loop=0)
            tests[vname] = test(strip, nf)
            items.append({"key": vname, "design": key, "palette": pal, "frames": nf, "frametime": ft, "section": sec,
                          "note": note + (" (jelly)" if vname.endswith("_jelly") else ""), "name": DESIGNS[key][0],
                          "jelly": vname.endswith("_jelly")})
        print(name, "done", flush=True)
    json.dump({"items": items}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
