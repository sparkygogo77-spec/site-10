"""Corps look kits, part one: Red (rage) and Yellow (fear) construct textures (J, 2026-10-13: "every ring will
probably have to have a different look for its textures of constructs, and its associated lantern/ring match").
Built in round six's detailed style: always moving gently, never still, translucent where it's dark.

  RED (rage)
    R1 magma     - dark crust plates split by molten cracks, the melt creeping through, embers rising
    R2 bloodfire - tongues of red fire climbing the face, hot cores, sparks
    R3 heartbeat - rage veins that throb with a heartbeat (two beats a loop), light pushed out from the core
  YELLOW (fear)
    Y1 scales    - overlapping scales like armour, a glint sweeping across them
    Y2 lightning - jagged forks of fear crackling between hard points, flickering
    Y3 dread     - dark smoke rolling over the face, yellow sparks of fear caught in it

    python tools/construct_designs7.py OUTDIR   -> face_<id>.png/.gif, tests.json, set.json
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs6.py", os.path.join(OUT, "_r6")]
sys.path.insert(0, HERE)
import construct_designs6 as D6  # noqa: E402
sys.argv = _argv
D4 = D6.D4
N, TAU, xx, yy = D6.N, D6.TAU, D6.xx, D6.yy
field, warp, ridged, stars, sway, finish, smooth, blur, voronoi, wrapd = (D6.field, D6.warp, D6.ridged, D6.stars,
    D6.sway, D6.finish, D6.smooth, D6.blur, D6.voronoi, D6.wrapd)
NF, FT = 32, 5

D4.PALETTES.update({
    "rage":    [(8, 0, 0), (40, 2, 2), (120, 8, 6), (235, 50, 24), (255, 200, 150)],
    "crimson": [(6, 0, 2), (32, 0, 6), (96, 4, 16), (210, 30, 40), (255, 170, 160)],
    "fear":    [(10, 6, 0), (48, 30, 0), (140, 96, 4), (246, 206, 40), (255, 250, 200)],
    "amberf":  [(8, 4, 0), (40, 20, 0), (120, 70, 4), (230, 160, 30), (255, 236, 170)],
})

DESIGNS = {}
SLOW = {"R2": 64}                                 # fire climbs: a 16 s loop keeps it unhurried


def design(key, name, pals):
    def deco(fn):
        DESIGNS[key] = (name, fn, pals)
        return fn
    return deco


def even_points(seed, n, gap):
    r = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        p = r.uniform(0, N, 2)
        if all(math.hypot(wrapd(p[0], q[0]), wrapd(p[1], q[1])) > gap for q in pts):
            pts.append(p)
    return np.array(pts)


def embers(seed, count, t, rise=1, size=1.0):
    """Sparks that rise `rise` tiles a loop (seamless), flickering."""
    r = np.random.default_rng(seed)
    px, py, ph = r.uniform(0, N, count), r.uniform(0, N, count), r.uniform(0, 1, count)
    out = np.zeros((N, N))
    for x, y, p in zip(px, py, ph):
        yy0 = (y - rise * N * t) % N
        x0 = x + 3 * math.sin(TAU * (t * 2 + p))
        w = 0.5 + 0.5 * math.sin(TAU * (3 * t + p))
        out += w * np.exp(-(np.hypot(wrapd(xx, x0), wrapd(yy, yy0)) / size) ** 2)
    return np.clip(out, 0, 1.3)


# ---- RED ------------------------------------------------------------------------------------------------------
@design("R1", "magma: crust plates split by molten cracks, embers rising", ("rage", "crimson"))
def _(t, _c={}):
    if "v" not in _c:
        pts = even_points(701, 22, 36)
        cell, d1, d2 = voronoi(pts)
        _c["v"] = (cell, d2 - d1, d1, field(3, 12, 1.4, 702), field(1, 4, 2.0, 703))
    cell, edge, d1, rough, big = _c["v"]
    dx, dy = sway(t, 1.5, 704)
    e = warp(edge, dx, dy)
    flow = 0.5 + 0.5 * np.cos(TAU * (warp(big, dy, dx) * 1.2 - t))       # the melt creeping along the cracks
    crack = np.exp(-e / 1.6) * (0.55 + 0.45 * flow) + 0.35 * np.exp(-e / 6.0) * flow
    crust = 0.1 + 0.06 * rough + 0.08 * np.exp(-warp(d1, dx, dy) / 40)      # plates stay dark, a little texture
    v = crust + crack * 1.1 + 0.9 * embers(705, 40, t, 1, 1.0)
    return finish(v * 0.95)


@design("R2", "bloodfire: tongues of red fire climbing the face, hot cores, sparks", ("rage", "crimson"))
def _(t):
    f1 = D4.moving_field(2, 8, 1.5, 711, t, 0, drift=(0, -1))           # climbs one tile a loop
    f2 = D4.moving_field(4, 16, 1.4, 712, t, 1, drift=(0, -1))
    g = f1 + 0.45 * f2
    tongues = ridged(g - 0.6, 2.2) * smooth(-0.2, 0.8, g)        # licks of flame round the hot patches
    cores = smooth(1.3, 2.2, g)
    wisps = ridged(f2, 3.2) * smooth(-0.4, 0.6, f1) * 0.35
    v = 0.08 + 0.55 * tongues + 0.5 * cores + wisps + 0.12 * smooth(-0.5, 1.5, g) + 0.8 * embers(713, 35, t, 2, 0.9)
    return finish(v * 0.8)


@design("R3", "heartbeat: rage veins throbbing twice a loop, light pushed out from the core", ("rage", "crimson"))
def _(t, _c={}):
    if "f" not in _c:
        _c["f"] = (field(2, 9, 1.5, 721), field(4, 18, 1.3, 722))
    f1, f2 = _c["f"]
    beat = sum(math.exp(-(((t * 2) % 1 - c) / 0.05) ** 2) * a for c, a in ((0.1, 1.0), (0.28, 0.6)))
    dx, dy = sway(t, 1.2, 723)
    veins = ridged(warp(f1, dx, dy), 4.0) ** 1.5 + 0.5 * ridged(warp(f2, -dy, dx), 5.5) ** 2
    cx, cy = N / 2, N / 2
    r = np.hypot(wrapd(xx, cx), wrapd(yy, cy))
    wave = np.exp(-((r - 160 * ((t * 2) % 1)) / 18) ** 2)               # each beat pushes a ring of light out
    v = 0.08 + veins * (0.6 + 0.6 * beat) + 0.5 * wave * veins + 0.2 * blur(veins, 3.0) + 0.25 * beat * np.exp(-r / 60)
    return finish(v)


# ---- YELLOW -----------------------------------------------------------------------------------------------------
@design("Y1", "scales: overlapping armour scales, a glint sweeping across them", ("fear", "amberf"))
def _(t, _c={}):
    if "s" not in _c:
        s = 32.0                                                         # scale size: two per block
        row = np.floor(yy / (s * 0.5))
        lx = (xx + (row % 2) * s / 2) % s - s / 2
        ly = yy % (s * 0.5)
        d = np.hypot(lx, ly - 0.0) / (s * 0.62)                          # scale centred on its top edge
        rim = smooth(0.78, 0.98, d) * (1 - smooth(0.98, 1.05, d))
        body = (1 - d) * (d < 1)
        _c["s"] = (rim, body, field(4, 14, 1.4, 731))
    rim, body, grain = _c["s"]
    u = (xx + 0.5 * yy) / N
    glint = np.exp(-((((u - t) % 1) - 0.5) / 0.09) ** 2)
    shimmer = 0.5 + 0.5 * np.cos(TAU * (grain * 0.6 + t))
    v = 0.12 + 0.25 * body * (0.6 + 0.4 * shimmer) + 0.55 * rim + 0.85 * glint * (rim + 0.4 * body)
    return finish(v * 0.9)


@design("Y2", "lightning: jagged forks crackling between hard points, flickering", ("fear", "amberf"))
def _(t, _c={}):
    if "p" not in _c:
        pts = even_points(741, 16, 48)
        cell, d1, d2 = voronoi(pts)
        jag = field(8, 40, 1.0, 742)                                      # makes the edges jagged
        _c["p"] = (pts, cell, d2 - d1, jag, field(1, 4, 2.0, 743))
    pts, cell, edge, jag, big = _c["p"]
    e = edge + 2.2 * jag
    bolt = np.exp(-np.abs(e) / 1.3)
    # each cell edge flickers on its own: a few bright flashes a loop
    ph = (cell * 0.6180339) % 1
    flick = np.clip(np.sin(TAU * (3 * t + ph)) * 1.6 - 0.4, 0, 1) ** 2
    nodes = sum(np.exp(-(np.hypot(wrapd(xx, x), wrapd(yy, y)) / 3.0) ** 2) for x, y in pts)
    glow = blur(bolt * (0.3 + flick), 3.5) * 2.6
    v = 0.08 + bolt * (0.5 + 0.9 * flick) + glow + 0.8 * nodes * (0.6 + 0.4 * math.sin(TAU * t))
    return finish(v * 0.9)


@design("Y3", "dread: dark smoke rolling over the face, yellow sparks of fear caught in it", ("fear", "amberf"))
def _(t):
    s1 = warp(field(1, 5, 1.8, 751), *sway(t, 10.0, 755))
    s2 = warp(field(3, 12, 1.4, 752), *sway(t, 5.0, 756))
    smoke = smooth(-0.6, 1.2, s1 + 0.4 * s2)
    curls = ridged(s1 + 0.4 * s2, 3.0) * 0.45
    sparks = stars(753, 70, t, 0.9) * smooth(0.0, 0.8, smoke)
    v = 0.05 + 0.2 * smoke + 1.1 * curls * (0.4 + smoke) + 1.2 * sparks + 0.7 * embers(754, 24, t, 1, 0.8)
    return finish(v)


if __name__ == "__main__":
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    tests, items = {}, []
    for key, (name, fn, pals) in DESIGNS.items():
        if only and key not in only:
            continue
        nf = SLOW.get(key, NF)
        frames = [fn(f / nf) for f in range(nf)]
        for pal in pals:
            vname = f"{key}_{pal}"
            rgba = [np.concatenate([D4.colour(v, pal), np.clip(a, 0, 255)[..., None]], -1) for v, a in frames]
            strip = np.concatenate(rgba, 0).clip(0, 255).astype(np.uint8)
            Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{vname}.png"), optimize=True)
            bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(nf)]
            bg[0].save(os.path.join(OUT, f"face_{vname}.gif"), save_all=True, append_images=bg[1:], duration=FT * 50, loop=0)
            tests[vname] = D4.test(strip, nf)
            sec = "red" if key[0] == "R" else "yellow"
            items.append({"key": vname, "design": key, "palette": pal, "frames": nf, "frametime": FT, "section": sec,
                          "note": name.split(":")[0], "name": name.split(":")[0], "jelly": False})
        print(key, "done", flush=True)
    json.dump({"items": items}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
