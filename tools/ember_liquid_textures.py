"""The Red Lantern's Deluge liquid: python tools/ember_liquid_textures.py <assets_dir>

Animated ripple strips (still and flowing) in light greys that the game tints blood red
(LanternRingClient.EMBER_LIQUID_TINT). Nearly opaque, so the liquid reads thick, like molten red
wax, instead of see-through water or flat lava.
"""
import math, os, sys
from PIL import Image

A = sys.argv[1]
OUT = os.path.join(A, "textures", "block")
FRAMES = 32
ALPHA = 232


def ripple(size, frame, flow):
    im = Image.new("RGBA", (size, size))
    px = im.load()
    t = frame / FRAMES * 2 * math.pi
    for y in range(size):
        for x in range(size):
            u, v = x / size * 2 * math.pi, y / size * 2 * math.pi
            if flow:
                # Bands sliding down the face, wobbling side to side.
                h = math.sin(2 * v - t + 0.8 * math.sin(u + t)) * 0.6 + math.sin(3 * u + v - t) * 0.4
            else:
                # Slow interfering swells; every term tiles in x, y and time.
                h = (math.sin(u + 2 * v + t) + math.sin(2 * u - v - t) + math.sin(3 * u + 3 * v + 2 * t) * 0.5) / 2.5
            k = 0.62 + 0.38 * (h * 0.5 + 0.5) ** 2
            c = int(255 * k)
            px[x, y] = (c, int(c * 0.97), int(c * 0.97), ALPHA)
    return im


for name, size, flow in (("ember_still", 16, False), ("ember_flow", 32, True)):
    strip = Image.new("RGBA", (size, size * FRAMES))
    for f in range(FRAMES):
        strip.paste(ripple(size, f, flow), (0, f * size))
    strip.save(os.path.join(OUT, name + ".png"))
    with open(os.path.join(OUT, name + ".png.mcmeta"), "w") as fh:
        fh.write('{\n\t"animation": {\n\t\t"frametime": 2,\n\t\t"interpolate": true\n\t}\n}\n')
