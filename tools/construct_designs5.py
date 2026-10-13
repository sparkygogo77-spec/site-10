"""Construct designs, round five (J, 2026-10-13): "W1 neon from afar looks like how I'd want every face of my
constructs to look, but still somehow translucent / see-through and a dark good colour; the details in it
aren't favourable" + "generate me more super elaborate design texture flows".

So every design here keeps W1 neon's far look (dark neon green, big soft mottled patches, the fine detail
only just there) and is translucent, with an elaborate flow moving slowly through it. Same machinery and
tests as construct_designs4.py.

    python tools/construct_designs5.py OUTDIR

Speeds (J: "make the speed what you think is optimal"): 24 frames at frametime 4 (4.8 s loop) for things that
shimmer in place, 32 frames at frametime 5 (8 s loop, half a block a second) for things that glide.
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
D3, CD = D4.D3, D4.CD
N, B, TAU = D4.N, D4.B, D4.TAU
xx, yy, CLOUD = D4.xx, D4.yy, D4.CLOUD
smooth, blur, moving_field, voronoi, wrapd, field = D4.smooth, D4.blur, D4.moving_field, D4.voronoi, D4.wrapd, D3.field

W1 = D4.tone_fn("W1")
MOTTLE = field(1, 5, 1.6, 501)                      # the big soft patches W1 neon has from afar


def far_look(detail, t, drift=None, k=0.4, alpha=(150, 30)):
    """Dark, mottled, translucent: big soft patches + the detail at reduced strength."""
    mott = MOTTLE if drift is None else moving_field(1, 5, 1.6, 501, t, 0, drift=drift)
    v = 0.37 + 0.09 * mott + k * detail
    a = alpha[0] + alpha[1] * np.clip(detail * 2, 0, 1) + 10 * mott
    return v, a


def weave_detail(t, p=16):
    v, _ = W1(t)
    return (v - (0.36 + 0.05 * CLOUD)) / 0.32        # W1's threads alone, 0..1


DESIGNS = {}


def design(key, name, nf=24, ft=4):
    def deco(fn):
        DESIGNS[key] = (name, fn, nf, ft)
        return fn
    return deco


@design("V1", "W1 neon, far look: threads barely there, patches gliding", 32, 5)
def _(t):
    return far_look(weave_detail(t) * 0.8, t, drift=(1, 0), k=0.32)


@design("V2", "light currents: ribbons of flow with pulses running through", 32, 5)
def _(t):
    psi = moving_field(1, 4, 1.7, 511, t, 0, drift=(1, 1))
    warp = moving_field(2, 6, 1.5, 512, t, 0, drift=(0, 1))
    c = np.abs(((psi * 2.6 + 0.35 * warp) % 1) - 0.5)
    ribbon = smooth(0.12, 0.03, c)
    phi = field(1, 3, 1.8, 513)
    pulse = 0.5 + 0.5 * np.cos(TAU * (phi * 2 - 2 * t))
    return far_look(ribbon * (0.35 + 0.65 * pulse ** 3), t, k=0.45)


@design("V3", "interlace: sinuous bands weaving over and under", 32, 5)
def _(t):
    det = np.zeros((N, N))
    for k, (fx, amp, ph, w) in enumerate(((2, 22, 0.0, 7), (3, 16, 0.4, 6), (2, 26, 0.7, 7))):
        yc = (np.arange(0, N, 64)[:, None, None] + 32 * k
              + amp * np.sin(TAU * (fx * xx[None] / N + ph + t)))
        d = np.min(np.abs(((yy[None] - yc + N / 2) % N) - N / 2), axis=0)
        band = smooth(w, w - 2.5, d)
        edge = smooth(w + 1.5, w, d) - band
        over = (np.floor(xx / 32 + k * 0.5) % 2 == 0)
        det = np.where(over, np.maximum(det * (1 - band), band * 0.8 + edge * 0.4), np.maximum(det, band * 0.55))
    return far_look(det, t, k=0.42)


@design("V4", "filigree: spiral curls turning slowly in every block", 24, 4)
def _(t):
    lx, ly = (xx % 32) - 15.5, (yy % 32) - 15.5
    r = np.hypot(lx, ly) + 1e-3
    th = np.arctan2(ly, lx)
    cell = (np.floor(xx / 32) + np.floor(yy / 32)) % 2 * 2 - 1     # neighbours turn opposite ways
    s = (np.log(r) * 2.2 + cell * th / TAU * 2 - t) % 1
    arm = smooth(0.2, 0.05, np.abs(s - 0.5) - 0.25 + 0.25) * smooth(16, 12, r) * smooth(1.5, 4, r)
    arm = np.clip(arm, 0, 1)
    return far_look(arm, t, k=0.4)


@design("V5", "damascus: folded layers rippling like forged steel", 32, 5)
def _(t):
    w = moving_field(1, 4, 1.7, 521, t, 0, drift=(0, 1))
    w2 = field(2, 8, 1.4, 522)
    layers = 0.5 + 0.5 * np.sin(TAU * (yy / N * 10 + 1.6 * w + 0.4 * w2))
    det = smooth(0.75, 0.95, layers) + 0.35 * smooth(0.45, 0.6, layers) * (1 - smooth(0.6, 0.75, layers))
    return far_look(det, t, k=0.38)


@design("V6", "nebula weave: W1 threads with clouds of light drifting through", 32, 5)
def _(t):
    neb = moving_field(1, 6, 1.5, 531, t, 0, drift=(1, 0))
    glow = np.clip((neb - 0.4) / 1.6, 0, 1) ** 1.5
    return far_look(weave_detail(t) * 0.6 + glow * 0.75, t, k=0.4)


@design("V7", "veins: faint glowing seams with light seeping along them", 24, 4)
def _(t):
    r = np.random.default_rng(541)
    pts = r.uniform(0, N, (34, 2))
    cell, d1, d2 = voronoi(pts)
    seam = smooth(1.8, 0.5, d2 - d1)
    run = 0.5 + 0.5 * np.cos(TAU * (d1 / 40 - t))
    return far_look(seam * (0.45 + 0.55 * run ** 2) + 0.15 * np.exp(-(d2 - d1) / 5), t, k=0.45)


@design("V8", "aurora weave: soft curtains of light sweeping over W1's threads", 32, 5)
def _(t):
    w = moving_field(1, 4, 1.8, 551, t, 0, drift=(1, 0))
    bands = (0.5 + 0.5 * np.sin(TAU * (yy / 64 * 2 + 0.4 * w))) ** 3
    return far_look(weave_detail(t) * 0.55 + bands * 0.6, t, k=0.4)


@design("V9", "constellation weave: tiny stars glinting in W1's threads", 24, 4)
def _(t, _c={}):
    if "p" not in _c:
        r = np.random.default_rng(561)
        _c["p"] = (r.uniform(0, N, 60), r.uniform(0, N, 60), r.uniform(0, 1, 60), r.integers(1, 3, 60))
    star = np.zeros((N, N))
    for x, y, ph, k in zip(*_c["p"]):
        b = max(0.0, math.sin(TAU * (k * t + ph))) ** 6
        star += b * np.exp(-(np.hypot(wrapd(xx, x), wrapd(yy, y)) / 1.4) ** 2)
    return far_look(weave_detail(t) * 0.6 + np.clip(star, 0, 1), t, k=0.45)


@design("V10", "tidal glass: wide slow swells of light under a calm skin", 32, 5)
def _(t):
    s1 = moving_field(1, 3, 2.0, 571, t, 0, drift=(1, 0))
    s2 = moving_field(1, 3, 2.0, 572, t, 0, drift=(0, 1))
    swell = np.clip((s1 + s2) / 3 + 0.3, 0, 1) ** 2
    ripple = 0.5 + 0.5 * np.sin(TAU * (s1 * 3 + s2 * 2))
    return far_look(swell * 0.6 + ripple * 0.12, t, k=0.45)


PALS = ["neon", "emerald"]


if __name__ == "__main__":
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    tests, items = {}, []
    for key, (name, fn, nf, ft) in DESIGNS.items():
        if only and key not in only:
            continue
        frames = [fn(f / nf) for f in range(nf)]
        for pal in PALS:
            vname = f"{key}_{pal}"
            rgba = [np.concatenate([D4.colour(v, pal), np.clip(a, 0, 255)[..., None]], -1) for v, a in frames]
            strip = np.concatenate(rgba, 0).clip(0, 255).astype(np.uint8)
            Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{vname}.png"), optimize=True)
            bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(nf)]
            bg[0].save(os.path.join(OUT, f"face_{vname}.gif"), save_all=True, append_images=bg[1:], duration=ft * 50, loop=0)
            tests[vname] = D4.test(strip, nf)
            items.append({"key": vname, "design": key, "palette": pal, "frames": nf, "frametime": ft, "section": pal,
                          "note": name, "name": name, "jelly": False})
        print(key, "done", flush=True)
    json.dump({"items": items}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
