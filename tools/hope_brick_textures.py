"""Textures for the corps aerial drops (corps/HopeDrop.java and corps/FearNuke.java).

Hope Bricks: what a Blue Lantern drop sets into. J (2026-10-12): "i like polished deepslate bricks
and nether bricks and the bricks we have for the dome look good (it can be denser bricks by like
1.25x". So it's the dome's construct-brick layout with 5 courses where the dome has 4, cut from a
dark polished blue stone (deepslate's polish, nether brick's deep bevelled edges and tight dark
mortar) with the construct bricks' pale light veins faintly running through each face. Every texel
is shaded from the surface it stands for (light from the top left), no random speckle. 80x80.

Also the Fear Nuke's Dread: yellow HUD hearts (9x9) and the effect's icon (18x18).

Run from the repo root: python3 tools/hope_brick_textures.py
"""
import math
import os

from PIL import Image

BLOCK = "src/main/resources/assets/lanternring/textures/block"
HEART = "src/main/resources/assets/lanternring/textures/gui/sprites/hud/heart"
EFFECT = "src/main/resources/assets/lanternring/textures/mob_effect"

N = 80
ROWS = 5          # the dome's bricks have 4 courses a block: 1.25x denser
ROW = N // ROWS   # 16
BRICK = 40        # two bricks a course, every other course offset by half a brick
MORTAR = 2

MORTAR_C = (10, 16, 34)
DEEP = (20, 38, 78)
FACE = (40, 82, 150)
LIGHT = (92, 150, 222)
VEIN = (176, 224, 255)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def stone(t):
    """Brick colour for a lighting value t in [-1, 1]."""
    return mix(FACE, LIGHT, t) if t >= 0 else mix(FACE, DEEP, -t)


def h(*v):
    """A smooth repeatable hash in [0, 1) for one brick, so each brick gets its own slight tone."""
    x = math.sin(sum(c * (12.9898 + 7.233 * i) for i, c in enumerate(v))) * 43758.5453
    return x - math.floor(x)


def vein(u, v, seed):
    """A faint light vein across a brick face (u, v in brick-local 0..1), like the dome bricks' light lines."""
    a = 0.35 + 0.3 * h(seed, 1)
    b = 0.2 + 0.6 * h(seed, 2)
    c = 0.15 + 0.2 * h(seed, 3)
    y = b + c * math.sin((u * a * 2 + h(seed, 4)) * math.pi * 2)
    d = abs(v - y)
    return max(0.0, 1.0 - d * 9.0) * (0.55 + 0.45 * math.sin(u * 7 + seed))


def bricks():
    img = Image.new("RGBA", (N, N))
    px = img.load()
    for y in range(N):
        row = y // ROW
        ly = y % ROW
        shift = (BRICK // 2) * (row % 2)
        for x in range(N):
            bx = (x + shift) % N
            col = bx // BRICK
            lx = bx % BRICK
            if ly < MORTAR or lx < MORTAR:
                px[x, y] = MORTAR_C + (255,)
                continue
            w, hh = BRICK - MORTAR, ROW - MORTAR
            u, v = (lx - MORTAR) / (w - 1), (ly - MORTAR) / (hh - 1)
            seed = row * 7 + col * 3 + 1
            # Nether-brick bevel: a bright top/left lip, a deep bottom/right edge.
            t = 0.0
            if ly - MORTAR == 0 or lx - MORTAR == 0:
                t = 0.85
            elif ly - MORTAR == 1 or lx - MORTAR == 1:
                t = 0.35
            elif ly == ROW - 1 or lx == BRICK - 1:
                t = -0.9
            elif ly == ROW - 2 or lx == BRICK - 2:
                t = -0.45
            else:
                # Polished face: a soft diagonal sheen and a per-brick tone.
                t = 0.18 * math.cos((u * 0.8 + v) * math.pi) - 0.12 + 0.22 * (h(seed) - 0.5)
            c = stone(t)
            g = vein(u, v, seed)
            if 0 < u < 1 and 0 < v < 1 and g > 0:
                c = mix(c, VEIN, g * 0.45)
            px[x, y] = c + (255,)
    return img


HEART_SHAPE = [
    ".##...##.",
    "#ww#.#ww#",
    "#wyy#yyy#",
    "#yyyyyyy#",
    "#yyyyyyo#",
    ".#yyyyo#.",
    "..#yyo#..",
    "...#o#...",
    "....#....",
]
OUTLINE = (40, 26, 4)
HEART_C = {"w": (255, 250, 200), "y": (255, 210, 26), "o": (196, 130, 0)}


def heart(half=False, blinking=False):
    img = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    for y, line in enumerate(HEART_SHAPE):
        for x, ch in enumerate(line):
            if ch == ".":
                continue
            if half and x > 4 and ch != "#":
                continue
            if half and x > 4:
                # The right half's outline goes with it, except where the left half meets it.
                continue
            c = OUTLINE if ch == "#" else HEART_C[ch]
            if blinking and ch == "#":
                c = (255, 255, 255)
            img.putpixel((x, y), c + (255,))
    return img


def dread_icon():
    """The Dread effect's icon: a yellow heart cracked with black."""
    img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    big = heart().resize((18, 18), Image.NEAREST)
    img.paste(big, (0, 0), big)
    for x, y in [(9, 3), (8, 5), (9, 6), (10, 8), (9, 10), (8, 12)]:
        img.putpixel((x, y), (30, 18, 2, 255))
        img.putpixel((x + 1 if x < 17 else x, y), (30, 18, 2, 255))
    return img


def main():
    os.makedirs(BLOCK, exist_ok=True)
    os.makedirs(HEART, exist_ok=True)
    os.makedirs(EFFECT, exist_ok=True)
    bricks().save(os.path.join(BLOCK, "hope_bricks.png"))
    for half in (False, True):
        for blink in (False, True):
            name = "dread_" + ("half" if half else "full") + ("_blinking" if blink else "") + ".png"
            heart(half, blink).save(os.path.join(HEART, name))
    dread_icon().save(os.path.join(EFFECT, "dread.png"))


if __name__ == "__main__":
    main()
