"""The ring wearer's aura: python tools/aura_texture.py <assets_dir>

A 64x64 tileable texture of rising flame streaks in greys (tinted to the corps' colour in game). The
aura is drawn additively, so black is clear and bright streaks glow; it scrolls upward over time.
"""
import math, os, random, sys
from PIL import Image

ASSETS = sys.argv[1]
random.seed(7)
W = H = 64
im = Image.new("RGBA", (W, H))
px = im.load()
# A few streak columns, each with its own phase, so the glow licks upward unevenly.
cols = [(random.uniform(0, W), random.uniform(1.5, 3.5), random.uniform(0, 2 * math.pi), random.choice((1, 2))) for _ in range(14)]
for y in range(H):
    for x in range(W):
        v = 0.06  # a faint base glow so the whole silhouette reads
        for cx, width, phase, waves in cols:
            dx = min(abs(x - cx), W - abs(x - cx))
            streak = math.exp(-(dx / width) ** 2)
            v += 0.6 * streak * (0.5 + 0.5 * math.sin(2 * math.pi * waves * y / H + phase))
        v = max(0.0, min(1.0, v))
        c = round(255 * v)
        px[x, y] = (c, c, c, 255)
out = os.path.join(ASSETS, "textures", "entity", "ring_aura.png")
im.save(out)
print("wrote", out)
