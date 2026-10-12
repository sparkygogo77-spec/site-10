"""The ring wearer's aura: python tools/aura_texture.py <assets_dir>

Two textures, both in greys (tinted to the corps' colour in game) and drawn additively, so black is
clear (alpha follows brightness too, for the see-through look used under shader packs):
- ring_aura.png: a glint of thin soft streaks over a near-clear base, sliding over the body like an
  enchantment glint (it tiles; the game scrolls it). No hard edges anywhere.
- ring_aura_edge.png: in the player skin's layout, a bright line round the edge of every face of
  every body part (used by the Soul Stone's outline).
"""
import math, os, sys
from PIL import Image

ASSETS = sys.argv[1]
OUT = os.path.join(ASSETS, "textures", "entity")

W = H = 64
# The sheen is drawn over the whole skin (64x64 pixels), so four texels per skin pixel keep the
# streaks smooth even on a 4-pixel-wide arm.
SW = SH = 256
sheen = Image.new("RGBA", (SW, SH))
px = sheen.load()
P = SW / 8  # streak spacing: eight per tile, so every limb catches a couple


def streak(t, width):
    """A soft streak: 1 on its centre line, fading smoothly to 0 (no hard edge)."""
    d = abs((t % P) - P / 2) / width
    return math.exp(-d * d)


for y in range(SH):
    for x in range(SW):
        # Like the enchantment glint: a near-clear base with thin soft streaks crossing at two
        # angles, the main set brighter than the second.
        a = streak(x + 0.5 * y, P * 0.09)
        b = streak(1.7 * x - y + 13, P * 0.06)
        v = 0.02 + 0.30 * a + 0.14 * b
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
