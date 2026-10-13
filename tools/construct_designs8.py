"""Corps look kits, part two: Blue (hope), Violet (love) and Orange (avarice) construct textures, in the same
detailed, always-gently-moving style as part one (construct_designs7.py).

  BLUE (hope)       B1 hope hex     - calm hexagons, soft light breathing up from their centres
                    B2 dawn         - soft rays of dawn light sweeping slowly across
                    B3 renewal      - orbs of healing light rising gently through the face
  VIOLET (love)     V1 crystal      - faceted amethyst, each facet catching the light in turn, sparkles
                    V2 bloom        - rose-curve blooms turning slowly in every block
                    V3 silk         - flowing silk ribbons with a soft sheen
  ORANGE (avarice)  O1 coins        - a hoard of packed coins, embossed rims, a glint passing over
                    O2 chains       - interlocked chain links, light running along them
                    O3 molten gold  - liquid gold rolling slowly, bright where it crests

    python tools/construct_designs8.py OUTDIR   -> face_<id>.png/.gif, tests.json, set.json
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs7.py", os.path.join(OUT, "_r7")]
sys.path.insert(0, HERE)
import construct_designs7 as D7  # noqa: E402
sys.argv = _argv
D6, D4 = D7.D6, D7.D4
N, TAU, xx, yy = D6.N, D6.TAU, D6.xx, D6.yy
field, warp, ridged, stars, sway, finish, smooth, blur, voronoi, wrapd = (D6.field, D6.warp, D6.ridged, D6.stars,
    D6.sway, D6.finish, D6.smooth, D6.blur, D6.voronoi, D6.wrapd)
embers, even_points = D7.embers, D7.even_points
NF, FT = 32, 5

D4.PALETTES.update({
    "hope":     [(0, 4, 16), (2, 20, 60), (10, 70, 160), (70, 170, 250), (210, 240, 255)],
    "sky":      [(0, 8, 14), (2, 34, 56), (12, 100, 150), (80, 200, 235), (215, 250, 255)],
    "love":     [(6, 0, 12), (30, 4, 56), (90, 20, 150), (180, 80, 250), (240, 210, 255)],
    "rose":     [(10, 0, 8), (44, 4, 40), (120, 20, 110), (230, 90, 210), (255, 215, 245)],
    "avarice":  [(10, 3, 0), (46, 16, 0), (140, 60, 2), (250, 140, 20), (255, 225, 160)],
    "gold":     [(8, 5, 0), (40, 26, 2), (120, 84, 10), (230, 180, 50), (255, 245, 200)],
})

DESIGNS = {}
SECTION = {"B": "blue", "V": "violet", "O": "orange"}


def design(key, name, pals):
    def deco(fn):
        DESIGNS[key] = (name, fn, pals)
        return fn
    return deco


def hex_lattice(cols=8, rows=10):
    """A staggered lattice that tiles the 256 px face exactly (even row count)."""
    sx, sy = N / cols, N / rows
    return np.array([((c + 0.5 * (r % 2)) * sx, r * sy) for r in range(rows) for c in range(cols)])


# ---- BLUE -----------------------------------------------------------------------------------------------------
@design("B1", "hope hex: calm hexagons, soft light breathing up from their centres", ("hope", "sky"))
def _(t, _c={}):
    if "h" not in _c:
        pts = hex_lattice(8, 10)
        cell, d1, d2 = voronoi(pts)
        _c["h"] = (cell, d1, d2 - d1, field(1, 4, 2.0, 801))
    cell, d1, edge, big = _c["h"]
    ph = (cell * 0.381966) % 1 + big * 0.15
    breathe = 0.5 + 0.5 * np.cos(TAU * (t + ph))
    core = np.exp(-(d1 / 9.0) ** 2) * breathe
    rim = np.exp(-edge / 1.0) * 0.7 + np.exp(-edge / 4.0) * 0.2
    v = 0.12 + 0.12 * breathe + rim + 0.55 * core + 0.4 * stars(802, 30, t, 0.7)
    return finish(v * 0.85)


@design("B2", "dawn: soft rays of light sweeping slowly across", ("hope", "sky"))
def _(t, _c={}):
    if "r" not in _c:
        r = np.random.default_rng(811)
        _c["r"] = [(r.integers(1, 5), r.uniform(0, 1), r.uniform(0.3, 1.0), r.choice([-1, 1])) for _ in range(9)]
        _c["f"] = field(2, 8, 1.6, 812)
    u = (2 * xx + yy) / N                                 # slanted rays (whole-number slant so it tiles)
    rays = np.zeros((N, N))
    for k, ph, a, s in _c["r"]:
        rays += a * (0.5 + 0.5 * np.cos(TAU * (k * u + ph + s * t))) ** 8
    haze = 0.5 + 0.5 * np.cos(TAU * (yy / N - t))          # light swells up the face once a loop
    v = 0.1 + 0.32 * rays * (0.6 + 0.4 * haze) + 0.08 * _c["f"] * 0.5 + 0.15 * haze + 0.35 * stars(813, 25, t, 0.7)
    return finish(v * 0.62)


@design("B3", "renewal: orbs of healing light rising gently through the face", ("hope", "sky"))
def _(t, _c={}):
    if "f" not in _c:
        _c["f"] = field(1, 5, 1.8, 821)
    dx, dy = sway(t, 5.0, 822)
    water = warp(_c["f"], dx, dy)
    orbs = embers(823, 22, t, 1, 4.5) * 0.9 + embers(824, 40, t, 2, 1.6) * 0.6
    halo = blur(orbs, 4.0) * 1.6
    v = 0.1 + 0.12 * (water * 0.5 + 0.5) + orbs + halo
    return finish(v * 0.9)


# ---- VIOLET ---------------------------------------------------------------------------------------------------
@design("V1", "crystal: faceted amethyst, each facet catching the light in turn, sparkles", ("love", "rose"))
def _(t, _c={}):
    if "c" not in _c:
        pts = even_points(831, 30, 30)
        cell, d1, d2 = voronoi(pts)
        r = np.random.default_rng(832)
        ang, ph = r.uniform(0, TAU, len(pts)), r.uniform(0, 1, len(pts))
        _c["c"] = (cell, d2 - d1, ang, ph, pts)
    cell, edge, ang, ph, pts = _c["c"]
    # each facet is a tilted plane: brightness ramps across it, and its turn to flash comes round once a loop
    px, py = pts[cell, 0], pts[cell, 1]
    gx, gy = wrapd(xx, px) * np.sign(((xx - px + N / 2) % N) - N / 2), wrapd(yy, py) * np.sign(((yy - py + N / 2) % N) - N / 2)
    tilt = (gx * np.cos(ang[cell]) + gy * np.sin(ang[cell])) / 22.0
    flash = (0.5 + 0.5 * np.cos(TAU * (t + ph[cell]))) ** 4
    facet = 0.22 + 0.16 * tilt + 0.45 * flash * (0.6 + 0.4 * tilt)
    rim = np.exp(-edge / 0.9) * (0.5 + 0.5 * flash)
    v = facet + 0.6 * rim + 1.0 * stars(833, 40, t, 0.8) * (0.4 + flash)
    return finish(v * 0.85)


@design("V2", "bloom: rose-curve blooms turning slowly in every block", ("love", "rose"))
def _(t):
    lx, ly = (xx % 64) - 31.5, (yy % 64) - 31.5
    r = np.hypot(lx, ly) + 1e-3
    th = np.arctan2(ly, lx)
    cell = (np.floor(xx / 64) + np.floor(yy / 64)) % 2 * 2 - 1           # neighbours turn opposite ways
    k = 5
    petals = np.abs(np.cos(k / 2 * (th + cell * TAU * t / k)))            # one petal's width a loop
    edge = np.exp(-((r / 27.0 - petals) / 0.07) ** 2)
    inner = np.exp(-((r / 15.0 - np.abs(np.cos(k / 2 * (th - cell * TAU * t / k + 0.3)))) / 0.09) ** 2)
    heart = np.exp(-(r / 5.0) ** 2) * (1 + 0.2 * math.sin(TAU * t))
    fill = (r / 27.0 < petals) * 0.12
    v = 0.08 + fill + 0.7 * edge + 0.45 * inner + heart + 0.3 * stars(841, 30, t, 0.7)
    return finish(v * 0.9)


@design("V3", "silk: flowing silk ribbons with a soft sheen", ("love", "rose"))
def _(t, _c={}):
    if "f" not in _c:
        _c["f"] = (field(1, 3, 2.0, 851), field(2, 6, 1.7, 852))
    f1, f2 = _c["f"]
    dx, dy = sway(t, 6.0, 853)
    w = warp(f1, dx, dy) * 1.4 + 0.5 * warp(f2, -dy, dx)
    bands = 0.5 + 0.5 * np.sin(TAU * (yy / N * 2 + w * 0.7))
    sheen = smooth(0.75, 1.0, bands) * (0.6 + 0.4 * np.cos(TAU * (xx / N + t)))
    fold = smooth(0.0, 0.25, bands) * 0.3
    v = 0.08 + fold + 0.18 * bands + 0.55 * sheen
    return finish(v * 0.7, a0=60, a1=180)


# ---- ORANGE ---------------------------------------------------------------------------------------------------
@design("O1", "coins: a hoard of packed coins, embossed rims, a glint passing over", ("avarice", "gold"))
def _(t, _c={}):
    if "h" not in _c:
        pts = hex_lattice(8, 10)
        cell, d1, d2 = voronoi(pts)
        _c["h"] = (cell, d1, field(4, 16, 1.4, 861))
    cell, d1, grain = _c["h"]
    rad = 13.5
    face = d1 < rad
    rim = np.exp(-((d1 - rad + 1.5) / 1.2) ** 2)
    inner = np.exp(-((d1 - rad * 0.62) / 0.9) ** 2) * 0.5
    stamp = np.exp(-(d1 / 4.0) ** 2) * 0.35
    u = (xx + 0.6 * yy) / N
    glint = np.exp(-((((u - t) % 1) - 0.5) / 0.07) ** 2)
    v = 0.06 + face * (0.3 + 0.05 * grain) + 0.55 * rim + inner + stamp + 0.9 * glint * (rim + 0.5 * face)
    return finish(v * 0.72)


@design("O2", "chains: interlocked chain links, light running along them", ("avarice", "gold"))
def _(t):
    s = 32.0
    def link_at(ox, oy, ax, ay):
        lx = ((xx - ox) % s) - s / 2
        ly = ((yy - oy) % s) - s / 2
        e = np.hypot(lx / ax, ly / ay)
        return np.exp(-((e - 1.0) / 0.16) ** 2), np.exp(-((e - 0.9) / 0.07) ** 2)
    h, hh = link_at(0, 0, 13.0, 6.5)                      # links lying across
    v_, vh = link_at(s / 2, s / 2, 6.5, 13.0)             # links standing up, threaded through them
    link = np.maximum(h, v_)
    hi = np.maximum(hh, vh)
    run = 0.5 + 0.5 * np.cos(TAU * ((xx + yy) / N * 2 - t))
    v = 0.06 + link * (0.45 + 0.4 * run) + 0.5 * hi * run + 0.4 * stars(871, 25, t, 0.7)
    return finish(v * 0.85)


@design("O3", "molten gold: liquid gold rolling slowly, bright where it crests", ("avarice", "gold"))
def _(t, _c={}):
    if "f" not in _c:
        _c["f"] = (field(1, 4, 1.9, 881), field(3, 10, 1.5, 882))
    f1, f2 = _c["f"]
    dx, dy = sway(t, 7.0, 883)
    g = warp(f1, dx, dy) + 0.4 * warp(f2, -dy * 1.4, dx * 1.4)
    body = smooth(-1.2, 1.4, g)
    crest = ridged(g - 0.6, 2.4) * 0.6 + smooth(1.1, 1.8, g) * 0.6
    v = 0.08 + 0.22 * body + 0.8 * crest + 0.5 * stars(884, 20, t, 0.7) * body
    return finish(v * 0.7, a0=60, a1=185)


if __name__ == "__main__":
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    tests, items = {}, []
    for key, (name, fn, pals) in DESIGNS.items():
        if only and key not in only:
            continue
        frames = [fn(f / NF) for f in range(NF)]
        for pal in pals:
            vname = f"{key}_{pal}"
            rgba = [np.concatenate([D4.colour(v, pal), np.clip(a, 0, 255)[..., None]], -1) for v, a in frames]
            strip = np.concatenate(rgba, 0).clip(0, 255).astype(np.uint8)
            Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{vname}.png"), optimize=True)
            bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(NF)]
            bg[0].save(os.path.join(OUT, f"face_{vname}.gif"), save_all=True, append_images=bg[1:], duration=FT * 50, loop=0)
            tests[vname] = D4.test(strip, NF)
            items.append({"key": vname, "design": key, "palette": pal, "frames": NF, "frametime": FT,
                          "section": SECTION[key[0]], "note": name.split(":")[0], "name": name.split(":")[0], "jelly": False})
        print(key, "done", flush=True)
    json.dump({"items": items}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
