"""The ring wearer's aura: python tools/aura_texture.py <assets_dir>

Two textures, both in greys (tinted to the corps' colour in game) and drawn additively, so black is
clear (alpha follows brightness too, for the see-through look used under shader packs):
- ring_aura.png: a faint sheen of soft diagonal bands, dark to pale, that slides over the body like
  an enchantment glint (it tiles; the game scrolls it).
- ring_aura_edge.png: in the player skin's layout, a bright line round the edge of every face of
  every body part, so each part's outer line is the brightest thing on it.
"""
import math, os, sys
from PIL import Image

ASSETS = sys.argv[1]
OUT = os.path.join(ASSETS, "textures", "entity")

W = H = 64
sheen = Image.new("RGBA", (W, H))
px = sheen.load()
for y in range(H):
    for x in range(W):
        # Two crossing diagonal waves, like the enchantment glint, only softer.
        a = 0.5 + 0.5 * math.sin(2 * math.pi * (x + y) / W)
        b = 0.5 + 0.5 * math.sin(2 * math.pi * (2 * x - y) / W + 1.3)
        v = 0.03 + 0.17 * a ** 3 + 0.07 * b ** 4
        c = round(255 * min(1, v))
        px[x, y] = (c, c, c, c)
sheen.save(os.path.join(OUT, "ring_aura.png"))

# Four texels per skin pixel, so the line is a quarter of a pixel wide however narrow the part.
S = 4
edge = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
ex = edge.load()


def rect(u, v, w, h):
    u, v, w, h = u * S, v * S, w * S, h * S
    for i in range(w):
        for j in range(h):
            d = min(i, j, w - 1 - i, h - 1 - j)
            c = 255 if d == 0 else 90 if d == 1 else 0
            if c > ex[u + i, v + j][0]:
                ex[u + i, v + j] = (c, c, c, c)


def box(u, v, w, h, d):
    """A cube's six faces in the standard box UV layout."""
    rect(u + d, v, w, d)              # top
    rect(u + d + w, v, w, d)          # bottom
    rect(u, v + d, d, h)              # right side
    rect(u + d, v + d, w, h)          # front
    rect(u + d + w, v + d, d, h)      # left side
    rect(u + 2 * d + w, v + d, w, h)  # back


box(0, 0, 8, 8, 8)       # head
box(16, 16, 8, 12, 4)    # body
box(0, 16, 4, 12, 4)     # right leg
box(16, 48, 4, 12, 4)    # left leg
for w in (4, 3):         # arms, wide and slim skins
    box(40, 16, w, 12, 4)
    box(32, 48, w, 12, 4)
edge.save(os.path.join(OUT, "ring_aura_edge.png"))
print("wrote ring_aura.png and ring_aura_edge.png")
