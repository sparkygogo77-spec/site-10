"""Particle-barrier surfaces for the game (J, 2026-10-13): "T5 T1 T2 T3 T6 T7 T9 should go in game". The Blender
shell shaders from tools/blender_edits/rage_battery_shell_blends.py, turned into seamless looping strips in the
usual format (256 px = 4 x 4 blocks, frames stacked, translucent): a faint green shell, a sprinkle of construct
pixels twinkling on it, and the T layer moving over it in more than one direction.

    python tools/construct_designs9.py OUTDIR  -> face_<T>_neon.png/.gif, tests.json, set.json
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
field, warp, stars, wrapd, smooth, moving_field = D6.field, D6.warp, D6.stars, D6.wrapd, D6.smooth, D4.moving_field
NF, FT = 32, 5
U, V = xx / N, yy / N                       # 0..1 across the 4-block tile


def wave(coord, k, turns, sharp):
    """Soft band, k whole bands across the tile, moving `turns` whole cycles a loop (so it tiles and loops)."""
    return lambda t: (0.5 + 0.5 * np.cos(TAU * (k * coord - turns * t))) ** sharp


def pixels(t, seed=901):
    """Construct pixels on the shell: little 2 x 2 squares twinkling."""
    r = np.random.default_rng(seed)
    px, py = r.integers(0, N // 4, 220) * 4, r.integers(0, N // 4, 220) * 4
    ph, k = r.uniform(0, 1, 260), r.integers(1, 3, 260)
    out = np.zeros((N, N))
    for x, y, p, kk in zip(px, py, ph, k):
        out[y:y + 3, x:x + 3] = max(out[y, x], 0.35 + 0.65 * max(0.0, math.sin(TAU * (kk * t + p))))
    return out


def radial(t, k, turns, sharp):
    r = np.hypot(wrapd(xx, N / 2), wrapd(yy, N / 2)) / N         # one centre per tile (per 4 blocks)
    return (0.5 + 0.5 * np.cos(TAU * (k * r * 2 - turns * t))) ** sharp


def veins(t, seed, drift, width):
    f = moving_field(1, 5, 1.7, seed, t, 0, drift=drift)
    return smooth(width, 0.0, np.abs(f) / 3.0)


def light_clouds(t):
    f = moving_field(1, 4, 1.9, 911, t, 0, drift=(1, 1))
    return smooth(0.6, 1.6, f)


DARK, LIGHT = "dark", "light"
DESIGNS = {
    "T1": ("bands x3: wide soft dark bands three ways",
           lambda t: [(np.maximum.reduce([wave(U, 2, 1, 3)(t), wave(V, 2, -1, 3)(t), wave(U + V, 1, 1, 3)(t)]), DARK, 0.42)]),
    "T2": ("warped bands: dark bands bent by slow noise",
           lambda t: [(wave(U + 0.5 * V + 0.06 * moving_field(1, 3, 2.0, 921, t, 0, drift=(0, 1)), 2, 1, 4)(t), DARK, 0.45)]),
    "T3": ("radial bands: soft dark rings breathing outward", lambda t: [(radial(t, 2, 1, 3.5), DARK, 0.45)]),
    "T5": ("radial glow: a soft ring of light expanding", lambda t: [(radial(t, 1, 1, 12), LIGHT, 0.4)]),
    "T6": ("light clouds: patches of light drifting", lambda t: [(light_clouds(t), LIGHT, 0.35)]),
    "T7": ("soft veins: two layers drifting opposite ways",
           lambda t: [(np.maximum(veins(t, 931, (1, 0), 0.3), veins(t, 932, (-1, 1), 0.25)), DARK, 0.5)]),
    "T9": ("bands + veins: crossing soft bands with faint veins",
           lambda t: [(np.maximum(wave(U + V, 1, 1, 3)(t), wave(V - U, 1, -1, 3)(t)), DARK, 0.36),
                      (veins(t, 941, (0, 1), 0.22), DARK, 0.3)]),
}
SHELL = np.array([30, 230, 90.0]); DARKC = np.array([0, 26, 9.0]); LIGHTC = np.array([140, 255, 180.0])


def frame(key, t):
    rgb = np.zeros((N, N, 3)) + SHELL * 0.55
    a = np.full((N, N), 70.0)                                  # the faint shell
    for fac, kind, op in DESIGNS[key][1](t):
        fac = np.clip(fac, 0, 1)[..., None]
        if kind == DARK:
            rgb = rgb * (1 - fac * op * 1.6).clip(0, 1) + DARKC * fac * op
            a = a + fac[..., 0] * op * 120
        else:
            rgb = rgb * (1 - fac * op) + LIGHTC * fac * op * 1.5
            a = a + fac[..., 0] * op * 160
    px = pixels(t)[..., None]
    rgb = rgb * (1 - px) + np.array([90, 255, 140.0]) * px
    a = np.maximum(a, px[..., 0] * 235)
    return np.concatenate([rgb.clip(0, 255), np.clip(a, 0, 252)[..., None]], -1)     # never fully opaque


if __name__ == "__main__":
    tests, items = {}, []
    for key, (name, _) in DESIGNS.items():
        frames = [frame(key, f / NF) for f in range(NF)]
        strip = np.concatenate(frames, 0).astype(np.uint8)
        vname = f"{key}_neon"
        Image.fromarray(strip, "RGBA").save(os.path.join(OUT, f"face_{vname}.png"), optimize=True)
        bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(NF)]
        bg[0].save(os.path.join(OUT, f"face_{vname}.gif"), save_all=True, append_images=bg[1:], duration=FT * 50, loop=0)
        tests[vname] = D4.test(strip, NF)
        items.append({"key": vname, "design": key, "palette": "neon", "frames": NF, "frametime": FT, "section": "neon",
                      "note": name.split(":")[0], "name": name.split(":")[0], "jelly": False})
        print(key, "done", flush=True)
    json.dump({"items": items}, open(os.path.join(OUT, "set.json"), "w"), indent=1)
    json.dump(tests, open(os.path.join(OUT, "tests.json"), "w"), indent=1)
    bad = {k: v for k, v in tests.items() if not v["pass"]}
    print(len(tests), "strips,", len(tests) - len(bad), "pass")
    for k, v in bad.items():
        print("  FAIL", k, v)
