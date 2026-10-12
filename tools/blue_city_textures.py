"""Textures for the Blue Lantern sky city's own blocks (Skystone and the Hope Lamp).

Skystone is the End city's purpur idea in sky colours: pale pearl-blue stone in big bevelled
tiles. Like the Classic battery (plans/lantern-style.md), every texel is shaded from the surface it
stands for (light from the top left, a soft sheen, darker bevels below and right), with no random
speckle. 32x32, so the bevels stay crisp next to vanilla blocks.

Run from the repo root: python3 tools/blue_city_textures.py
"""
import math
import os

from PIL import Image

OUT = "src/main/resources/assets/lanternring/textures/block"
N = 32

# Pearl-blue stone, lit to shadow, and the deep blue of the mortar lines.
LIGHT = (214, 232, 250)
FACE = (148, 182, 226)
SHADE = (88, 120, 176)
MORTAR = (42, 58, 104)
GLOW_CORE = (250, 253, 255)
GLOW_EDGE = (84, 170, 255)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def stone(t):
    """Stone colour for a lighting value t in [-1, 1] (-1 deep shadow, 0 face, 1 highlight)."""
    return mix(FACE, LIGHT, t) if t >= 0 else mix(FACE, SHADE, -t)


def tile(px, py, x0, y0, w, h, bevel=2):
    """Lighting of one bevelled tile at texel (px, py): a raised slab, lit from the top left."""
    lx, ly = px - x0, py - y0
    # Mitred corners: the nearest edge wins, the lit edges on a tie.
    edges = [(ly, 0.9), (lx, 0.7), (h - 1 - ly, -0.85), (w - 1 - lx, -0.6)]
    near, light = min(edges, key=lambda e: e[0])
    if near < bevel:
        return light
    # The face: a gentle top-to-bottom fall-off and a soft diagonal sheen.
    u, v = (lx + 0.5) / w, (ly + 0.5) / h
    sheen = math.exp(-((u + v - 0.75) ** 2) / 0.04) * 0.35
    return 0.15 - v * 0.35 + sheen


def tiled(cells):
    """A texture of tiles separated by one-texel mortar lines; cells is a list of (x, y, w, h)."""
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            col = MORTAR
            for (x0, y0, w, h) in cells:
                if x0 <= px < x0 + w - 1 and y0 <= py < y0 + h - 1:
                    col = stone(tile(px, py, x0, y0, w - 1, h - 1))
                    break
            img.putpixel((px, py), col + (255,))
    return img


def bricks():
    # Two big square tiles over a row of two offset half-height bricks: End city purpur rhythm.
    cells = [(0, 0, 16, 16), (16, 0, 16, 16), (-8, 16, 16, 16), (8, 16, 16, 16), (24, 16, 16, 16)]
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            col = MORTAR
            for (x0, y0, w, h) in cells:
                if x0 <= px < x0 + w - 1 and y0 <= py < y0 + h - 1:
                    cx0, cw = max(x0, 0), min(x0 + w - 1, N) - max(x0, 0)
                    # Bricks cut by the texture edge wrap round, so shade them as one brick.
                    if x0 < 0 or x0 + w > N:
                        cx0, cw = x0, w - 1
                    col = stone(tile(px, py, cx0, y0, cw, h - 1))
                    break
            img.putpixel((px, py), col + (255,))
    return img


def tiles():
    # A floor of four tiles with a small inset square where their corners meet.
    img = tiled([(0, 0, 16, 16), (16, 0, 16, 16), (0, 16, 16, 16), (16, 16, 16, 16)])
    for py in range(13, 19):
        for px in range(13, 19):
            edge = px in (13, 18) or py in (13, 18)
            img.putpixel((px, py), (MORTAR if edge else mix(GLOW_EDGE, GLOW_CORE, 0.35)) + (255,))
    return img


def pillar_side():
    # Four rounded flutes running up the pillar, each shaded like a half cylinder.
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            if px in (0, N - 1):
                col = MORTAR
            else:
                u = ((px - 1) % 8 + 0.5) / 8  # across one flute
                if (px - 1) % 8 == 7:
                    col = mix(MORTAR, SHADE, 0.5)
                else:
                    t = math.cos((u - 0.3) * math.pi) * 0.9 - 0.25
                    col = stone(t)
            img.putpixel((px, py), col + (255,))
    return img


def pillar_top():
    # Round end grain: rings of stone round a lit centre, cut round inside a square frame.
    img = Image.new("RGBA", (N, N))
    c = (N - 1) / 2
    for py in range(N):
        for px in range(N):
            r = math.hypot(px - c, py - c)
            if px in (0, N - 1) or py in (0, N - 1):
                col = MORTAR
            elif r > 14.5:
                col = stone(tile(px, py, 1, 1, N - 2, N - 2))
            elif r > 13.5:
                col = MORTAR
            else:
                ring = math.cos(r / 13.5 * math.pi * 3) * 0.2
                lit = -((px - c) + (py - c)) / (2 * 13.5) * 0.5
                col = stone(0.25 + ring + lit)
            img.putpixel((px, py), col + (255,))
    return img


def hope_lamp():
    # A Skystone frame round a glowing pane: white-hot middle fading to Blue Lantern blue,
    # crossed by four slim mullions like the city's End rods seen end on.
    img = Image.new("RGBA", (N, N))
    c = (N - 1) / 2
    for py in range(N):
        for px in range(N):
            if px < 5 or py < 5 or px >= N - 5 or py >= N - 5:
                if px == 0 or py == 0 or px == N - 1 or py == N - 1:
                    col = MORTAR
                elif px == 4 or py == 4 or px == N - 5 or py == N - 5:
                    col = mix(MORTAR, GLOW_EDGE, 0.4)
                else:
                    col = stone(tile(px, py, 1, 1, N - 2, N - 2, bevel=1) * 0.8)
            else:
                d = math.hypot(px - c, py - c) / (c - 5)
                col = mix(GLOW_CORE, GLOW_EDGE, d ** 1.4)
                if px in (15, 16) or py in (15, 16):
                    col = mix(col, (200, 230, 255), 0.5)
            img.putpixel((px, py), col + (255,))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {
        "skystone_bricks": bricks(),
        "skystone_tiles": tiles(),
        "skystone_pillar": pillar_side(),
        "skystone_pillar_top": pillar_top(),
        "hope_lamp": hope_lamp(),
    }
    for name, img in out.items():
        img.save(os.path.join(OUT, name + ".png"))
        print("wrote", name)


if __name__ == "__main__":
    main()
