"""The swirl of light around the hand while the Beam charges: python tools/charge_glow_texture.py <assets_dir>

  <assets_dir>/textures/entity/charge_swirl.png  64x64 tileable green streaks on black. It is drawn
                                                 additively (like a charged creeper), so black is
                                                 see-through and bright green glows.
"""
import math, os, sys
from PIL import Image

OUT = sys.argv[1]
N = 64
img = Image.new("RGB", (N, N))
px = img.load()
for y in range(N):
    for x in range(N):
        # Two sets of diagonal bands that tile, plus a finer wobble, so scrolling looks like swirling light.
        a = math.sin(2 * math.pi * (x + y) / N * 2)
        b = math.sin(2 * math.pi * (x - 2 * y) / N * 3 + 1.3)
        c = math.sin(2 * math.pi * (3 * x + y) / N + 0.4 * math.sin(2 * math.pi * y / N * 2))
        v = max(0.0, 0.55 * a + 0.35 * b + 0.3 * c)
        v = min(1.0, v ** 1.6)
        hot = v ** 3
        px[x, y] = (int(40 * v + 180 * hot), int(255 * v), int(70 * v + 150 * hot))
os.makedirs(os.path.join(OUT, "textures/entity"), exist_ok=True)
img.save(os.path.join(OUT, "textures/entity/charge_swirl.png"))
