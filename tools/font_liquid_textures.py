"""Draws the animated liquids in the big batteries' basins: python tools/font_liquid_textures.py <assets_dir>

willpower_still.png: bright green light, slowly churning (the Great Power Battery).
blood_lava_still.png: thick red lantern lava with dark crust drifting over it (the Lava Font).
Each is a vertical strip of looping frames with a .mcmeta, like vanilla's lava. The pattern tiles,
so it can cover any size of basin.
"""
import json, os, sys
import numpy as np
from PIL import Image

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
SIZE, FRAMES = 32, 32
rng = np.random.default_rng(11)
G = rng.random((8, 8, FRAMES // 4))


def noise(x, y, t):
    """Tiling value noise: x, y in lattice cells over an 8x8 grid, t over FRAMES // 4 cells (loops)."""
    xi, yi, ti = np.floor(x).astype(int), np.floor(y).astype(int), int(np.floor(t))
    xf, yf, tf = x - xi, y - yi, t - ti
    u, v, w = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf), tf * tf * (3 - 2 * tf)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dt in (0, 1):
                c = G[(xi + dx) % 8, (yi + dy) % 8, (ti + dt) % G.shape[2]]
                out = out + c * (u if dx else 1 - u) * (v if dy else 1 - v) * (w if dt else 1 - w)
    return out


def field(frame):
    y, x = np.mgrid[0:SIZE, 0:SIZE] / SIZE * 8
    t = frame / FRAMES * G.shape[2]
    warp = noise(x * 1 + 1.3, y * 1, t)
    a = noise((x + warp * 3) % 8, (y + warp * 2) % 8, t) * 0.65 + noise((x * 2) % 8, (y * 2 + warp) % 8, t) * 0.35
    return a


def write(name, palette):
    strip = Image.new("RGBA", (SIZE, SIZE * FRAMES))
    for f in range(FRAMES):
        a = field(f)
        k = np.clip((a - a.min()) / max(a.max() - a.min(), 1e-6), 0, 1)
        stops = np.array(palette, float)
        idx = k * (len(stops) - 1)
        lo = np.floor(idx).astype(int).clip(0, len(stops) - 2)
        fr = (idx - lo)[..., None]
        rgb = stops[lo] * (1 - fr) + stops[lo + 1] * fr
        im = Image.fromarray(np.dstack([rgb, np.full((SIZE, SIZE), 255)]).astype(np.uint8), "RGBA")
        strip.paste(im, (0, f * SIZE))
    os.makedirs(f"{A}/textures/block", exist_ok=True)
    strip.save(f"{A}/textures/block/{name}.png")
    with open(f"{A}/textures/block/{name}.png.mcmeta", "w") as fh:
        json.dump({"animation": {"frametime": 3, "interpolate": True}}, fh, indent="\t")


write("willpower_still", [(20, 150, 60), (50, 220, 95), (120, 255, 150), (230, 255, 235)])
write("blood_lava_still", [(40, 4, 6), (120, 10, 14), (205, 30, 24), (255, 110, 60), (255, 200, 140)])
