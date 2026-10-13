"""Puts J's construct texture picks from the Blender rounds (2026-10-13) into the game:
python tools/construct_picks.py <assets_dir> [--dissolve-only]

Runs tools/construct_designs4.py for the picked designs (round-4 palettes: darker, five stops,
smoothstep blend) and writes each strip as textures/block/construct_ripples_<design>_<palette>.png,
256 px wide (4 x 4 blocks at 64 px a block), 24 or 32 frames, with an interpolated .mcmeta at
frametime 4 (J: slow and smooth). FlowConstructModel slices any construct_ripples sprite over 4
blocks by world position; the Ring Lab's construct rows pick which strip each kind of construct shows.
Strips are quantized to 256 colours (FASTOCTREE, no dither) to keep the jar under 30 MB.

Also writes textures/entity/construct_dissolve.png, J's round-3 "fill3" dissolve for a construct going
away (DismissFx): 16 frames of one 64 px block face stacked vertically. Each pixel goes in its own
random order (construct_designs3.DISS) and a bright sparkling front runs where it is just going.
The texture is white and grey; DismissFx tints it with the corps colour.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMETIME = 4
# (design, palette): J's picks (construct-texture-picks.md)
PICKS = [
    ("BR1", "jade"), ("BR1", "emerald"), ("BR1", "lime"), ("BR1", "neon"), ("BR1", "forest"),   # green Walls
    ("H1", "neon"), ("D1", "neon"), ("W1", "emerald"), ("W1", "neon"),                       # green constructs
    ("BR1", "blue"), ("H1", "blue"),                                                         # Blue Lantern
    ("G2Ng", "yellow"), ("G2Ng", "amber"), ("N3", "yellow"), ("N3", "amber"),                # Yellow Lantern
]
MCMETA = '{\n\t"animation": {\n\t\t"frametime": %d,\n\t\t"interpolate": true\n\t}\n}\n' % FRAMETIME


def quantized(path):
    im = Image.open(path).convert("RGBA")
    return im.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)


def strips(assets, tmp):
    keys = sorted({d for d, _ in PICKS})
    env = dict(os.environ, ONLY=",".join(keys))
    subprocess.run([sys.executable, os.path.join(HERE, "construct_designs4.py"), tmp], env=env, check=True)
    folder = os.path.join(assets, "textures", "block")
    for design, pal in PICKS:
        name = f"construct_ripples_{design.lower()}_{pal}"
        out = os.path.join(folder, name + ".png")
        quantized(os.path.join(tmp, f"face_{design}_{pal}.png")).save(out, optimize=True)
        with open(out + ".mcmeta", "w") as f:
            f.write(MCMETA)
        print("wrote", out, os.path.getsize(out) // 1024, "KB")


def dissolve(assets, tmp):
    argv, sys.argv = sys.argv, ["construct_designs3.py", os.path.join(tmp, "_r3")]
    sys.path.insert(0, HERE)
    import construct_designs3 as D3  # noqa: E402
    sys.argv = argv
    B, frames = 64, 16
    # one block's worth of the dissolve order, spread evenly over 0..1 again
    d = D3.DISS[:B, :B]
    d = d.argsort(None).argsort().reshape(B, B) / (B * B)
    y, x = np.mgrid[0:B, 0:B]
    edge = np.minimum(np.minimum(x, B - 1 - x), np.minimum(y, B - 1 - y))
    rim = np.exp(-edge / 3.0)                                   # a firm bright rim like the constructs'
    cloud = D3.CLOUD[:B, :B]
    out = np.zeros((frames * B, B, 4), np.uint8)
    for k in range(frames):
        level = 1 - k / (frames - 1)                            # 1: all there, 0: gone
        m = D3.smooth(level + 0.02, level - 0.02, d)
        front = np.exp(-((d - level) / 0.025) ** 2) * (0.02 < level < 0.99)
        v = np.clip(0.3 + 0.08 * cloud + 0.25 * rim, 0, 1) * m           # dark like the picks; the front pops
        v = np.clip(v + front, 0, 1)
        a = np.clip((150 + 90 * rim) * m + 255 * front, 0, 255)
        grey = (v * 255).astype(np.uint8)
        out[k * B:(k + 1) * B, :, 0] = grey
        out[k * B:(k + 1) * B, :, 1] = grey
        out[k * B:(k + 1) * B, :, 2] = grey
        out[k * B:(k + 1) * B, :, 3] = a.astype(np.uint8)
    path = os.path.join(assets, "textures", "entity", "construct_dissolve.png")
    Image.fromarray(out, "RGBA").save(path, optimize=True)
    print("wrote", path)


if __name__ == "__main__":
    assets = sys.argv[1]
    with tempfile.TemporaryDirectory() as tmp:
        dissolve(assets, tmp)
        if "--dissolve-only" not in sys.argv:
            strips(assets, tmp)
