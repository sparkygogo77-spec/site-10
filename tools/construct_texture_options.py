"""Texture options for the jade constructs (J, 2026-10-12: "do R2 and several new texture variants",
"the white smoke lines can be a better colour, maybe dark so it blends in with the jade", and the Rage
Bull in the same style). Uses the real game generator (tools/construct_jade_game.py) for the ripples,
so every option is exactly what the game would draw:

    python tools/construct_texture_options.py OUTDIR

Writes into OUTDIR:
- lines_<style>_<colour>.png   the ripple strip (24 frames, 256 px = 4 blocks) as the game uses it
- face_<style>_<colour>.png    one frame laid over the cloudy jade, 256 px (4 x 4 blocks), for Blender
- face_<...>.gif               the same, moving
- options.json                 the list, for the Blender update
Styles  R1 mixed (today) / R2 small fragments / R3 large and slow / S1 silk (long thin) / S2 grain (tiny, dense)
Colours W white (today) / K1 dark jade / K2 deep forest / K3 dark with a mint rim / K4 jade tone / K5 shadow haze
Bull    the same faces turned red (RED_*), for the Rage Bull and the Red constructs.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# the game generator's shared fields and LIC, without its file writing
src = open(os.path.join(HERE, "construct_jade_game.py"), encoding="utf-8").read()
ns = {"__name__": "jade", "OUT": OUT}
exec("import math, os, sys\nimport numpy as np\nfrom PIL import Image\n" +
     src[src.index("# ---- shared"):src.index("def ripples(")], ns)
N, FRAMES = ns["N"], ns["FRAMES"]


def intensity(layers, pulse=0.0):
    """The game's ripples() up to its colouring: line strength 0..1, [FRAMES, N, N]."""
    frames = np.zeros((FRAMES, N, N))
    for li, (grain, steps, lam, cycles, weight) in enumerate(layers):
        S = ns["lic_samples"](ns["blurred_noise"](grain, 100 + li), steps)
        s = np.arange(-steps, steps + 1)[:, None, None]
        for f in range(FRAMES):
            t = f / FRAMES
            k = 0.5 + 0.5 * np.cos(2 * np.pi * (s / lam - cycles * t))
            k = k * np.exp(-(s / steps) ** 2 * 1.2)
            v = (S * k).sum(0) / k.sum(0)
            v = (v - v.mean()) / (v.std() + 1e-9)
            frames[f] += np.clip((v - 0.25) / 1.6, 0, 1) ** 1.4 * weight
    m1, m2 = ns["field"](2, 10, 1.2, 31), ns["field"](2, 10, 1.2, 32)
    for f in range(FRAMES):
        a = 2 * np.pi * f / FRAMES
        frames[f] *= np.clip((m1 * np.cos(a) + m2 * np.sin(a) + 0.2) / 0.9, 0, 1)
        if pulse:
            frames[f] *= 1 + pulse * np.sin(2 * a * 2)
    return np.clip(frames * 1.15, 0, 1)


STYLES = {
    "R1": ("mixed sizes (today)", [(1.1, 30, 26, 2, 1.0), (2.4, 44, 40, 1, 0.8)], 3),
    "R2": ("small fragments", [(0.6, 14, 11, 3, 1.0), (0.9, 20, 15, 2, 0.85)], 2),
    "R3": ("large and slow", [(3.2, 64, 60, 1, 1.0)], 5),
    "S1": ("silk, long and thin", [(0.55, 60, 34, 2, 1.0)], 3),
    "S2": ("grain, tiny and dense", [(0.45, 8, 7, 4, 1.0), (0.7, 12, 10, 3, 0.7)], 2),
}


def soft(a, r):
    """Blur each frame a little (wrapping), for the hazier colourways."""
    out = np.empty_like(a)
    for f in range(len(a)):
        im = Image.fromarray((np.tile(a[f], (3, 3)) * 255).astype(np.uint8))
        b = np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(float) / 255
        out[f] = b[N:2 * N, N:2 * N]
    return out


def colour(a, cw):
    """Line strength -> RGBA strip for each colourway."""
    rgb = np.empty(a.shape + (3,))
    if cw == "W":            # today's: white-mint, nearly solid where strong
        for c, (lo, hi) in enumerate(((120, 225), (255, 255), (150, 232))):
            rgb[..., c] = lo + (hi - lo) * a
        alpha = a * 235
    elif cw == "K1":         # dark jade: the lines read as deeper jade, not paint
        for c, (lo, hi) in enumerate(((40, 10), (120, 66), (85, 44))):
            rgb[..., c] = lo + (hi - lo) * a
        alpha = a * 200
    elif cw == "K2":         # deep forest, nearly black green, strongest contrast
        for c, (lo, hi) in enumerate(((20, 3), (70, 30), (48, 18))):
            rgb[..., c] = lo + (hi - lo) * a
        alpha = a * 215
    elif cw == "K3":         # dark core with a thin mint rim, like a groove catching light
        rim = np.clip(soft(a, 1.3) - a * 0.9, 0, 1) * 2.2
        core = a
        for c, (dk, lt) in enumerate(((12, 175), (62, 255), (40, 205))):
            rgb[..., c] = (dk * core + lt * rim) / (core + rim + 1e-6)
        alpha = np.clip(core * 205 + rim * 150, 0, 235)
    elif cw == "K4":         # jade tone: brighter, richer jade, low contrast
        for c, (lo, hi) in enumerate(((70, 60), (175, 205), (125, 140))):
            rgb[..., c] = lo + (hi - lo) * a
        alpha = a * 170
    elif cw == "K5":         # shadow haze: soft dark smoke inside the jade
        a = soft(a, 1.6)
        rgb[..., 0], rgb[..., 1], rgb[..., 2] = 8, 42, 28
        alpha = np.clip(a * 1.3, 0, 1) * 150
    return np.concatenate([rgb, alpha[..., None]], -1)


COLOURS = {"W": "white (today)", "K1": "dark jade", "K2": "deep forest", "K3": "dark, mint rim",
           "K4": "jade tone", "K5": "shadow haze"}

# the cloudy jade under the lines: the game's plain tile, 128 px per block -> 64, tiled 4 x 4
import subprocess, tempfile
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable, os.path.join(HERE, "construct_jade_game.py"), tmp], check=True, stdout=subprocess.DEVNULL)
sheet = Image.open(os.path.join(tmp, "construct_jade.png")).convert("RGBA")
plain = sheet.crop((0, 0, 128, 128)).resize((64, 64), Image.LANCZOS)
frame_tile = sheet.crop((256, 128, 384, 256)).resize((64, 64), Image.LANCZOS)  # with its outline
base = Image.new("RGBA", (N, N))
for i in range(4):
    for j in range(4):
        base.paste(frame_tile if (i, j) == (0, 0) else plain, (i * 64, j * 64))
base_np = np.asarray(base).astype(float)


def over(top, under):
    ta = top[..., 3:4] / 255; ua = under[..., 3:4] / 255
    oa = ta + ua * (1 - ta)
    rgb = (top[..., :3] * ta + under[..., :3] * ua * (1 - ta)) / np.maximum(oa, 1e-6)
    return np.concatenate([rgb, oa * 255], -1)


def red(img):
    """Turn jade to the Red corps: keep each pixel's lightness, swap the hue (like CorpsTint)."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    lum = np.maximum(np.maximum(r, g), b)
    low = np.minimum(np.minimum(r, g), b)
    out = img.copy()
    out[..., 0] = lum
    out[..., 1] = low * 0.55
    out[..., 2] = low * 0.5
    return out


opts = []
for sk, (sname, layers, ft) in STYLES.items():
    a = intensity(layers)
    for ck, cname in COLOURS.items():
        strip = colour(a, ck)
        key = f"{sk}_{ck}"
        Image.fromarray(np.concatenate(list(strip), 0).clip(0, 255).astype(np.uint8), "RGBA").save(
            os.path.join(OUT, f"lines_{key}.png"), optimize=True)
        faces = [over(strip[f], base_np) for f in range(FRAMES)]
        variants = [(key, faces)]
        if ck in ("W", "K1", "K3") and sk in ("R1", "R2", "S1"):
            variants.append(("RED_" + key, [red(x) for x in faces]))
        for vk, fr in variants:
            ims = [Image.fromarray(x.clip(0, 255).astype(np.uint8), "RGBA") for x in fr]
            ims[0].save(os.path.join(OUT, f"face_{vk}.png"))
            bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), im).convert("RGB") for im in ims]
            bg[0].save(os.path.join(OUT, f"face_{vk}.gif"), save_all=True, append_images=bg[1:],
                       duration=ft * 50, loop=0)
            opts.append({"key": vk, "label": f"{vk}  {sname}, {cname}" + (" (red)" if vk.startswith("RED") else ""),
                         "style": sk, "colour": ck, "red": vk.startswith("RED")})
    print("style", sk, "done", flush=True)
json.dump(opts, open(os.path.join(OUT, "options.json"), "w"), indent=1)
print(len(opts), "options in", OUT)
