"""Construct designs, round eleven (pass 703, 2026-10-15): J on the 701 skin workshop.
  BRD: "try giving this one more detail on the bricks, or make them one of our new metallic materials for the brick
        material (not the glowing lines though)"
  X5E: "we need textures where the ripples are more efficiently packed onto big texture surfaces"

  BRDC  carved bricks: BRD (BR1 bricks + D1 sparks) with far more on each brick - bevelled edges lit from the top
        left, a fine stone grain, hairline cracks, chipped corners, a few pits - the glowing mortar and sparks unchanged.
        Also writes BRDC's glow mask (mortar + sparks = 1, brick = 0) so Blender can make only the bricks metal.
  X5G   ripple grid: one ripple source per block (16 per 4 x 4 tile instead of 1), rings interlocking at the edges.
  X5I   ripple interference: seven sources per tile whose waves add up, so the whole surface is covered in a moving
        lattice of crossings, no dark gaps.
  X5R   ripple rain: 46 small ripples spawning all over the tile at different times, like rain on water.

Same format as rounds 4-6: 256 px strips (4 x 4 blocks at 64 px a block), seamless, looping, translucent.

    python tools/construct_designs11.py OUTDIR  -> <key>_strip.png (+ brdc_mask_strip.png), <key>.gif, tests.json
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
D4, D3 = D6.D4, D6.D3
N, TAU, B = D4.N, D4.TAU, D3.B
xx, yy, wrapd, blur, CLOUD = D4.xx, D4.yy, D4.wrapd, D4.blur, D3.CLOUD


# ------------------------------------------------------------------ BRDC carved bricks
def _brick_static(seed=201):
    ids, lx, ly, bw, bh = D3.brick_layout(4, 2, seed, 0.0)
    r = np.random.default_rng(seed + 1)
    nb = ids.max() + 1
    tone = r.uniform(-0.08, 0.08, nb)
    seam = (np.roll(ids, 1, 0) != ids) | (np.roll(ids, 1, 1) != ids)
    seam |= np.roll(seam, 1, 0) | np.roll(seam, 1, 1)                  # 2 px mortar, as BR1
    # distance to the mortar inside each brick (4-neighbour, a few steps)
    dist = np.where(seam, 0, 99).astype(float)
    for k in range(1, 5):
        near = np.zeros_like(seam)
        for ax, s in ((0, 1), (0, -1), (1, 1), (1, -1)):
            near |= np.roll(dist == k - 1, s, ax)
        dist = np.where((dist == 99) & near, k, dist)
    # which side of the brick the edge is on: lit from the top left, shaded bottom right
    top = np.roll(seam, 1, 0) | np.roll(np.roll(seam, 1, 0), 1, 0)
    left = np.roll(seam, 1, 1) | np.roll(np.roll(seam, 1, 1), 1, 1)
    bot = np.roll(seam, -1, 0) | np.roll(np.roll(seam, -1, 0), -1, 0)
    right = np.roll(seam, -1, 1) | np.roll(np.roll(seam, -1, 1), -1, 1)
    bevel = np.where(dist <= 2, 1.0, 0.0) * (0.26 * (top | left) - 0.2 * (bot | right))
    grain = blur(r.random((N, N)), 0.7) - 0.5
    grain2 = blur(r.random((N, N)), 2.5) - 0.5
    # hairline cracks: thin ridges of a noise field, only inside some bricks
    f = blur(r.random((N, N)), 3.0); f = (f - f.mean()) / f.std()
    crack = np.exp(-(f * 7) ** 2) * (r.random(nb) < 0.6)[ids] * (dist >= 3)
    # chipped corners: a few bricks lose a corner (darker, rough)
    chip = np.zeros((N, N))
    for b in np.where(r.random(nb) < 0.35)[0]:
        m = ids == b
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            continue
        cx, cy = (xs.min(), ys.min()) if r.random() < 0.5 else (xs.max(), ys.max())
        rr = r.uniform(2.5, 4.5)
        chip += m * (np.hypot(wrapd(xx, cx), wrapd(yy, cy)) < rr)
    pits = (r.random((N, N)) < 0.006) & ~seam
    pits = blur(pits.astype(float), 0.6) * 3
    v = 0.47 + tone[ids] + 0.04 * CLOUD + bevel + 0.11 * grain + 0.07 * grain2 - 0.3 * crack - 0.2 * np.clip(chip, 0, 1) - 0.18 * np.clip(pits, 0, 1)
    return v, seam


def brdc(t, _c={}):
    if "s" not in _c:
        _c["s"] = _brick_static()
    v, seam = _c["s"]
    wave = 0.5 + 0.5 * np.cos(TAU * ((xx + yy) / N - t))
    out = np.where(seam, 0.78 + 0.2 * wave, v)
    d = ((xx + yy) - t * 2 * N) % (2 * N)                              # BR1's glint, a little softer on the detail
    g = np.exp(-((np.minimum(d, 2 * N - d)) / 14) ** 2)
    out = out + (1 - out) * g * 0.3 * ~seam
    a = np.where(seam, 235, 205.0)
    sv, sa = D4.DESIGNS["D1"][1](t)                                    # BRD's sparks rising through
    spark = np.clip(sv - D4.base_of("D"), 0, 1)
    out = out + 0.9 * spark
    mask = np.clip(seam + spark * 3.0, 0, 1)
    return out, np.maximum(a, sa * 0.9), mask


# ------------------------------------------------------------------ X5 packed ripples
def _nearest(points, k=4):
    """Distances from every pixel to its k nearest sources (wrapped), sorted, and their indices."""
    D = np.stack([np.hypot(wrapd(xx, px), wrapd(yy, py)) for px, py in points], 0)
    idx = np.argsort(D, 0)[:k]
    return np.take_along_axis(D, idx, 0), idx


GRID = [(B / 2 + B * i, B / 2 + B * j) for i in range(4) for j in range(4)]
_G = {}


def x5g(t):
    if "d" not in _G:
        _G["d"], _G["i"] = _nearest(GRID, 4)
        _G["ph"] = np.array([((i + j) % 2) * 0.5 for i in range(4) for j in range(4)])
    d, idx = _G["d"], _G["i"]
    v = np.zeros((N, N)); keep = np.ones((N, N))
    for k in range(4):                     # soft union of the four nearest sources: rings interlock, never stack bright
        ph = _G["ph"][idx[k]]
        ring = (0.5 + 0.5 * np.cos(TAU * (d[k] / 7.0 - t - ph))) ** 4 * np.exp(-d[k] / 40.0)
        keep *= 1 - 0.85 * ring
    v = (1 - keep) * 1.4
    core = sum(np.exp(-(d[0] / 3.2) ** 2) * (1.0 + 0.15 * math.sin(TAU * (t + 0.5 * kk))) for kk in (0,)) * 0.9
    v = v + core + 0.35 * D6.stars(661, 60, t, 0.6)
    return D6.finish(v)


SRC7 = [(40, 46), (150, 22), (226, 104), (96, 128), (24, 196), (178, 176), (120, 238)]


def x5i(t, _c={}):
    if "d" not in _c:
        _c["d"] = [np.hypot(wrapd(xx, px), wrapd(yy, py)) for px, py in SRC7]
    s = np.zeros((N, N))
    for k, d in enumerate(_c["d"]):        # waves add up: a lattice of bright crossings over the whole surface
        s += np.cos(TAU * (d / 11.0 - t) + k * 0.9) / (1 + d / 90.0)
    s = s / 3.2
    v = np.clip(0.5 + 0.5 * s, 0, 1) ** 3 * 1.25
    core = sum(np.exp(-(d / 3.0) ** 2) for d in _c["d"]) * 0.8
    return D6.finish(v + core + 0.3 * D6.stars(662, 50, t, 0.6))


RAIN = np.random.default_rng(663)
DROPS = [(RAIN.uniform(0, N), RAIN.uniform(0, N), RAIN.uniform(0, 1), RAIN.uniform(26, 40)) for _ in range(46)]


def x5r(t, _c={}):
    if "d" not in _c:
        _c["d"] = [np.hypot(wrapd(xx, px), wrapd(yy, py)) for px, py, _, _ in DROPS]
    life = 0.5
    keep = np.ones((N, N)); core = np.zeros((N, N))
    for (px, py, t0, rmax), d in zip(DROPS, _c["d"]):
        age = (t - t0) % 1.0
        if age >= life:
            continue
        u = age / life
        amp = (1 - u) ** 1.4
        for lag in (0.0, 0.12, 0.24):      # a ring and two smaller trailing rings
            rr = max(0.0, u - lag) * rmax
            if rr <= 0:
                continue
            ring = np.exp(-((d - rr) / 1.9) ** 2) * amp * (1 - lag * 2.2)
            keep *= 1 - 0.9 * np.clip(ring, 0, 1)
        core += np.exp(-(d / 2.5) ** 2) * max(0.0, 1 - u * 4)
    v = (1 - keep) * 1.5 + core + 0.12 + 0.35 * D6.stars(664, 60, t, 0.6)
    return D6.finish(v)


PLAN = [("brdc_neon", brdc, "neon", 24, 4, "BRDC carved bricks"),
        ("x5g_emerald", x5g, "emerald", 32, 5, "X5G ripple grid"),
        ("x5i_emerald", x5i, "emerald", 32, 5, "X5I ripple interference"),
        ("x5r_emerald", x5r, "emerald", 32, 5, "X5R ripple rain")]

if __name__ == "__main__":
    tests = {}
    for key, fn, pal, nf, ft, name in PLAN:
        res = [fn(f / nf) for f in range(nf)]
        frames = [np.concatenate([D4.colour(r[0], pal), np.clip(r[1], 0, 255)[..., None]], -1) for r in res]
        strip = np.concatenate(frames, 0).clip(0, 255).astype(np.uint8)
        Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"{key}_strip.png"), optimize=True)
        if len(res[0]) > 2:                # the glow mask (R = 1 where the light is), same frames
            m = np.concatenate([np.repeat((r[2] * 255)[..., None], 3, -1) for r in res], 0).clip(0, 255).astype(np.uint8)
            Image.fromarray(m, "RGB").save(os.path.join(OUT, key.split("_")[0] + "_mask_strip.png"), optimize=True)
        bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)),
                                    Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(nf)]
        bg[0].save(os.path.join(OUT, f"{key}.gif"), save_all=True, append_images=bg[1:], duration=ft * 50, loop=0)
        tests[key] = D4.test(strip, nf)
        print(key, tests[key], flush=True)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
