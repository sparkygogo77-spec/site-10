"""The Red Lantern's Deluge liquid: python tools/blood_liquid_textures.py <assets_dir>

Soft, slow ripples in light greys that the game tints blood red (LanternRingClient.EMBER_LIQUID_TINT),
nearly opaque so you can't see the bottom without shaders either. Low contrast, so it reads as a thick,
smooth liquid and the per-block repeat doesn't show. With the patched Complementary the pack draws it as
its own water instead (ShaderPackPatcher, ID 32003). Every frame tiles, and the animation loops.
"""
import math, os, sys
from PIL import Image

A = sys.argv[1]
OUT = os.path.join(A, "textures", "block")
FRAMES = 32
ALPHA = 246
TAU = 2 * math.pi


def ripple(size, frame, flow):
    im = Image.new("RGBA", (size, size))
    px = im.load()
    t = frame / FRAMES * TAU
    for y in range(size):
        for x in range(size):
            u, v = x / size * TAU, y / size * TAU
            if flow:
                h = 0.6 * math.sin(v - t + 0.5 * math.sin(u)) + 0.4 * math.sin(2 * v + u - 2 * t)
            else:
                h = (math.sin(u + v + t) + math.sin(u - 2 * v - t) + 0.5 * math.sin(2 * u + v + 2 * t)) / 2.5
            k = 0.84 + 0.12 * (h * 0.5 + 0.5)
            c = int(255 * k)
            px[x, y] = (c, c, c, ALPHA)
    return im


for name, size, flow in (("blood_still", 16, False), ("blood_flow", 32, True)):
    strip = Image.new("RGBA", (size, size * FRAMES))
    for f in range(FRAMES):
        strip.paste(ripple(size, f, flow), (0, f * size))
    strip.save(os.path.join(OUT, name + ".png"))
    with open(os.path.join(OUT, name + ".png.mcmeta"), "w") as fh:
        fh.write('{\n\t"animation": {\n\t\t"frametime": 3,\n\t\t"interpolate": true\n\t}\n}\n')
