"""Construct designs, round six (J, 2026-10-13): detailed animated versions of five reference looks,
"not too slow, if not almost near still, but never static":
  X1 cosmic dust     - a web of glowing filaments through dark space, stars twinkling, the haze drifting
  X2 solid energy    - cells of hard light, bright knots where the edges meet, pulses running along the edges
  X3 power aura      - wispy strands of power flowing over each other in slow currents
  X4 brushed metal   - fine diagonal brushed streaks with a sheen sliding across
  X5 quantum ripple  - concentric rings breathing out from a bright core, fine dust in the gaps

Same format as rounds 4 and 5: 256 px strips (4 x 4 blocks at 64 px a block), seamless, looping, translucent.
Every design moves slowly all the time: 32 frames at frametime 5 = an 8 s loop.

    python tools/construct_designs6.py OUTDIR   -> face_<X>_<pal>.png/.gif, tests.json, set.json
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs4.py", os.path.join(OUT, "_r4")]
sys.path.insert(0, HERE)
import construct_designs4 as D4  # noqa: E402
sys.argv = _argv
D3 = D4.D3
CD = D3.CD
N, TAU = D4.N, D4.TAU
xx, yy = D4.xx, D4.yy
smooth, blur, moving_field, voronoi, wrapd, field = D4.smooth, D4.blur, D4.moving_field, D4.voronoi, D4.wrapd, D3.field
K, KX, KY = CD.K, CD.KX, CD.KY
NF, FT = 32, 5


def ridged(f, sharp=6.0):
    """Thin bright ridges where a noise crosses zero."""
    return np.exp(-(f * sharp) ** 2)


def stars(seed, count, t, size=0.9, twinkle=True):
    r = np.random.default_rng(seed)
    px, py = r.uniform(0, N, count), r.uniform(0, N, count)
    ph, k, b = r.uniform(0, 1, count), r.integers(1, 3, count), r.uniform(0.3, 1.0, count)
    out = np.zeros((N, N))
    for x, y, p, kk, bb in zip(px, py, ph, k, b):
        w = bb * ((0.55 + 0.45 * math.sin(TAU * (kk * t + p))) if twinkle else 1.0)
        out += w * np.exp(-(np.hypot(wrapd(xx, x), wrapd(yy, y)) / size) ** 2)
    return np.clip(out, 0, 1.4)


def warp(f, dx, dy):
    """Sample a periodic image at (x+dx, y+dy) with wrap (bilinear)."""
    x = (xx + dx) % N; y = (yy + dy) % N
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    x1, y1 = (x0 + 1) % N, (y0 + 1) % N
    return (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x1] * fx * (1 - fy)
            + f[y1, x0] * (1 - fx) * fy + f[y1, x1] * fx * fy)


def finish(v, base=0.08, a0=36, a1=215):
    """Brightness -> (tone, alpha): dark space stays see-through, the light is solid."""
    v = np.clip(v, 0, 1.25)
    tone = base + (1 - base) * np.clip(v, 0, 1) ** 0.85
    a = a0 + a1 * np.clip(v, 0, 1) ** 0.7
    return tone, a


DESIGNS = {}


def design(key, name):
    def deco(fn):
        DESIGNS[key] = (name, fn)
        return fn
    return deco


def sway(t, amp, seed):
    """A gentle periodic displacement: every point circles a little once a loop (never still, never fast)."""
    p = field(1, 4, 2.0, seed) * math.pi
    return amp * np.cos(TAU * t + p), amp * np.sin(TAU * t + p)


@design("X1", "cosmic dust: a web of glowing filaments through dark space, twinkling stars")
def _(t, _c={}):
    if "f" not in _c:
        _c["f"] = (field(2, 10, 1.5, 601), field(5, 22, 1.3, 602), field(1, 4, 2.0, 603))
    f1, f2, f3 = _c["f"]
    dx, dy = sway(t, 3.0, 604)
    a, b = warp(f1, dx, dy), warp(f2, dx * 1.6, -dy * 1.6)
    web = ridged(a, 4.2) ** 1.8
    branch = ridged(b, 3.4) ** 2 * smooth(0.05, 0.6, ridged(a, 0.9))
    halo = blur(web + 0.6 * branch, 5.0) * 0.9
    knots = smooth(0.75, 1.0, web * (0.4 + ridged(b, 1.2)))
    haze = np.clip(warp(f3, dy * 2, dx * 2) * 0.12 + 0.1, 0, 1)
    v = 0.6 * web + 0.4 * branch + 0.35 * halo + 0.8 * knots + haze
    return finish(v * 0.75 + 1.2 * stars(611, 160, t, 1.0))


@design("X2", "solid energy: hard-light cells, bright knots at the joins, pulses running along the edges")
def _(t, _c={}):
    if "p" not in _c:
        r = np.random.default_rng(621)
        pts = []
        while len(pts) < 26:                           # evenly spread seeds, so no two cells collapse into a blob
            p = r.uniform(0, N, 2)
            if all(math.hypot(wrapd(p[0], q[0]), wrapd(p[1], q[1])) > 34 for q in pts):
                pts.append(p)
        _c["p"] = (np.array(pts), r.uniform(0, TAU, 26), r.uniform(2, 5, 26))
    base, ph, rad = _c["p"]
    pts = [(x + 0.6 * rr * math.cos(TAU * t + p), y + 0.6 * rr * math.sin(TAU * t + p)) for (x, y), p, rr in zip(base, ph, rad)]
    cell, d1, d2 = voronoi(pts)
    edge = d2 - d1
    line = np.exp(-edge / 1.1) + 0.35 * np.exp(-edge / 5.0)
    # the joins: where the third-nearest seed is also close
    d = np.sort(np.stack([np.hypot(wrapd(xx, px), wrapd(yy, py)) for px, py in pts]), 0)
    knot = np.exp(-((d[2] - d[0]) / 6.0) ** 2)
    knot = knot ** 3 * 1.4 + 0.15 * np.exp(-((d[2] - d[0]) / 10.0) ** 2)
    run = 0.5 + 0.5 * np.cos(TAU * (d1 / 34.0 - t + cell * 0.37))
    small = voronoi([((x * 2.3 + 40) % N, (y * 1.7 + 90) % N) for x, y in base])[1:]
    fine = np.exp(-(small[1] - small[0]) / 0.9) * 0.22
    v = line * (0.55 + 0.45 * run ** 2) + knot + fine + 0.05 * np.exp(-d1 / 30)
    return finish(v)


@design("X3", "power aura: wispy strands of power flowing over each other in slow currents")
def _(t, _c={}):
    if "f" not in _c:
        _c["f"] = (field(2, 7, 1.5, 633), field(3, 11, 1.4, 634), field(1, 3, 2.0, 635))
    f1, f2, f3 = _c["f"]
    dx, dy = sway(t, 4.0, 631)
    s1 = warp(f1, dx, dy)
    s2 = warp(f2, -dy * 1.3, dx * 1.3)
    strands = ridged(s1, 4.5) ** 1.6 * 0.75 + ridged(s2, 6.0) ** 2 * 0.5
    glow = blur(strands, 4.0) * 1.1
    cloud = np.clip(warp(f3, dx * 3, dy * 3) * 0.18 + 0.22, 0, 1) * smooth(0.0, 0.5, glow + 0.2)
    v = strands + 0.55 * glow + 0.35 * cloud + 0.6 * stars(636, 50, t, 0.8)
    return finish(v * 0.85)


@design("X4", "brushed metal: fine diagonal streaks with a soft sheen sliding across")
def _(t, _c={}):
    if "s" not in _c:
        r = np.random.default_rng(641)
        # anisotropic spectrum: energy only where k is nearly perpendicular to the (1,1) diagonal -> streaks along it
        along = np.abs(KX + KY) / math.sqrt(2)
        across = np.abs(KX - KY) / math.sqrt(2)
        amp = np.where((across >= 6) & (across <= 120) & (along <= 1.5), np.maximum(across, 1) ** -0.6, 0.0)
        f = np.real(np.fft.ifft2(amp * np.exp(1j * r.uniform(0, TAU, K.shape))))
        _c["s"] = (f - f.mean()) / f.std()
    s = _c["s"]
    u = (xx - yy) / N                                  # across the streaks
    w = (xx + yy) / N                                  # along them
    sheen = np.exp(-((((u - t) % 1) - 0.5) / 0.16) ** 2) * (0.7 + 0.3 * np.cos(TAU * (w + t)))
    sheen2 = 0.45 * np.exp(-((((u * 2 - t * 2 + 0.3) % 1) - 0.5) / 0.08) ** 2)
    v = 0.28 + 0.1 * s + (0.55 + 0.25 * s) * (sheen + sheen2)
    return finish(v, base=0.1, a0=70, a1=170)


@design("X5", "quantum ripple: concentric rings breathing out from a bright core, fine dust between")
def _(t):
    cx, cy = N / 2, N / 2
    dx, dy = wrapd(xx, cx), wrapd(yy, cy)
    r = np.hypot(dx, dy)
    wob = sway(t, 0.6, 651)[0]
    rings = (0.5 + 0.5 * np.cos(TAU * (r / 6.0 - t) + wob)) ** 5
    fade = np.exp(-r / 120.0)
    core = np.exp(-(r / 9.0) ** 2) * (1.0 + 0.15 * math.sin(TAU * t)) + 0.4 * np.exp(-r / 30.0)
    v = rings * (0.3 + 0.9 * fade) + core + 0.5 * stars(652, 70, t, 0.6)
    return finish(v)


PALS = ["neon", "emerald"]

if __name__ == "__main__":
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    tests, items = {}, []
    for key, (name, fn) in DESIGNS.items():
        if only and key not in only:
            continue
        frames = [fn(f / NF) for f in range(NF)]
        for pal in PALS:
            vname = f"{key}_{pal}"
            rgba = [np.concatenate([D4.colour(v, pal), np.clip(a, 0, 255)[..., None]], -1) for v, a in frames]
            strip = np.concatenate(rgba, 0).clip(0, 255).astype(np.uint8)
            Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{vname}.png"), optimize=True)
            bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(NF)]
            bg[0].save(os.path.join(OUT, f"face_{vname}.gif"), save_all=True, append_images=bg[1:], duration=FT * 50, loop=0)
            tests[vname] = D4.test(strip, NF)
            items.append({"key": vname, "design": key, "palette": pal, "frames": NF, "frametime": FT, "section": pal,
                          "note": name.split(":")[0], "name": name.split(":")[0], "jelly": False})
        print(key, "done", flush=True)
    json.dump({"items": items}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
