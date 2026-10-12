"""The screen overlay while charging at a lantern: python tools/lantern_glare_textures.py <assets_dir>

  <assets_dir>/textures/misc/lantern_vignette.png  256x256 black, see-through in the middle and
                                                   solid at the edges: the dark around the lantern.
  <assets_dir>/textures/misc/lantern_glare.png     128x128 white glow fading out from the middle,
                                                   premultiplied, added onto the screen in the
                                                   lantern's colour.
"""
import math, os, sys
from PIL import Image

OUT = os.path.join(sys.argv[1], "textures/misc")
os.makedirs(OUT, exist_ok=True)


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


N = 256
img = Image.new("RGBA", (N, N))
px = img.load()
for y in range(N):
    for x in range(N):
        r = math.hypot(x + 0.5 - N / 2, y + 0.5 - N / 2) / (N / 2)
        # Clear around the lantern, then a long soft falloff into full dark by the edge.
        px[x, y] = (0, 0, 0, int(255 * smooth((r - 0.12) / 0.86)))
img.save(os.path.join(OUT, "lantern_vignette.png"))

N = 128
img = Image.new("RGBA", (N, N))
px = img.load()
for y in range(N):
    for x in range(N):
        r = math.hypot(x + 0.5 - N / 2, y + 0.5 - N / 2) / (N / 2)
        # A hot core with a wide halo, like light bleeding into the eye.
        a = 0.85 * max(0.0, 1 - r) ** 3 + 0.15 * max(0.0, 1 - r) ** 1.2
        # Premultiplied (colour = alpha), so the game can add it onto the screen as light.
        v = int(255 * min(1.0, a))
        px[x, y] = (v, v, v, v)
img.save(os.path.join(OUT, "lantern_glare.png"))
