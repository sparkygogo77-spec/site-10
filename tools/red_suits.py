"""Red Lantern suits for the sanctuary's residents (J's picks from the design drafts, 2026-10-12):
P1 Rage Raider (pillager), W1 Caged Heart (warden), C1 Rage Suit (blue cat), G1 Blood Iron (golem).

Each suit is painted over the vanilla texture, so the mob keeps its own face and shape. Run it with
the vanilla textures unpacked from the game jar Loom extracts, e.g.

    unzip -o .gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-clientOnly-*/26.3/*.jar \
        'assets/minecraft/textures/entity/*' -d /tmp/vanilla
    python3 tools/red_suits.py /tmp/vanilla/assets/minecraft/textures/entity

The cloth is shaded from the vanilla pixel's own brightness (smooth ramps, no added noise), as in
the lantern style guide.
"""
import os
import sys

from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets", "lanternring",
                   "textures", "entity", "red_lantern")

CRIMSON = ((70, 6, 14), (200, 30, 40))
BLACK = ((16, 12, 14), (62, 50, 54))
GLOW = (255, 70, 56)
HOT = (255, 196, 186)


def lum(p):
    return (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255


def ramp(p, pal, lo=0.15, hi=0.75):
    """The pixel's brightness, stretched from lo..hi onto the palette's dark..light."""
    t = min(1.0, max(0.0, (lum(p) - lo) / (hi - lo)))
    a, b = pal
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (p[3],)


def paint(im, box, pal, **kw):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = im.getpixel((x, y))
            if p[3]:
                im.putpixel((x, y), ramp(p, pal, **kw))


def put(im, x, y, c):
    im.putpixel((x, y), c + (255,) if len(c) == 3 else c)


def emblem(im, cx, cy):
    """The corps emblem, 4x4: a black ring round a bright red centre."""
    for dy in range(4):
        for dx in range(4):
            corner = dx in (0, 3) and dy in (0, 3)
            if corner:
                continue
            inner = dx in (1, 2) and dy in (1, 2)
            put(im, cx + dx, cy + dy, HOT if inner and (dx, dy) == (1, 1) else GLOW if inner else BLACK[0])


def reds_for_greens(im, box):
    """Turns coloured eye pixels (green, gold) red."""
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = im.getpixel((x, y))
            if a and (g > r + 15 or (r > 200 and g > 180 and b < 170)):
                put(im, x, y, GLOW)


def pillager(src):
    im = Image.open(os.path.join(src, "illager", "pillager.png")).convert("RGBA")
    # Head: a red headband all the way round, red eyes.
    for x in range(0, 32):
        put(im, x, 9, CRIMSON[1])
    reds_for_greens(im, (8, 8, 16, 18))
    # Body: black, with a crimson chest plate and the emblem.
    paint(im, (16, 20, 44, 38), BLACK)
    paint(im, (23, 27, 29, 38), CRIMSON)
    emblem(im, 24, 29)
    # The coat over the legs: black, with a red hem.
    paint(im, (0, 38, 28, 64), BLACK)
    for x in range(0, 28):
        if im.getpixel((x, 63))[3]:
            put(im, x, 63, CRIMSON[0])
    # Arms: black sleeves, red shoulders; the hands stay.
    paint(im, (40, 46, 56, 60), BLACK)
    paint(im, (40, 46, 56, 53), CRIMSON)
    # Legs: black with red knee guards.
    paint(im, (0, 22, 16, 38), BLACK)
    paint(im, (4, 30, 8, 33), CRIMSON)
    paint(im, (12, 30, 16, 33), CRIMSON)
    return im


def warden(src):
    im = Image.open(os.path.join(src, "warden", "warden.png")).convert("RGBA")
    # Its glowing teal tendrils and markings turn red.
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = im.getpixel((x, y))
            if a and b > r + 20 and g > r + 20:
                v = max(g, b)
                im.putpixel((x, y), (min(255, int(v * 1.25)), int(v * 0.12), int(v * 0.16), a))
    # The Caged Heart: black bands across the chest, open round the heart (16..23, 18..27).
    for row in range(14, 32, 3):
        for x in range(11, 29):
            if 15 <= x <= 24 and 17 <= row <= 28:
                continue
            put(im, x, row, BLACK[0])
    # The window's frame in red.
    for x in range(15, 25):
        for y in (17, 28):
            put(im, x, y, CRIMSON[1])
    for y in range(17, 29):
        for x in (15, 24):
            put(im, x, y, CRIMSON[1])
    return im


def cat(src):
    im = Image.open(os.path.join(src, "cat", "cat_british_shorthair.png")).convert("RGBA")
    reds_for_greens(im, (0, 0, 20, 13))
    # The suit: the body and legs in crimson, a darker stripe down the back, the emblem on each side.
    paint(im, (20, 0, 40, 22), CRIMSON)
    paint(im, (36, 6, 40, 22), ((50, 4, 10), (140, 20, 30)))
    emblem(im, 21, 12)
    emblem(im, 31, 12)
    # Legs: red, the paws stay blue.
    paint(im, (40, 0, 48, 7), CRIMSON)
    paint(im, (8, 13, 16, 20), CRIMSON)
    # The ring on its tail: the tip's last row glows.
    for x in range(0, 8):
        for y in (22, 23):
            if im.getpixel((x, y))[3]:
                put(im, x, y, GLOW)
    return im


def golem(src):
    im = Image.open(os.path.join(src, "iron_golem", "iron_golem.png")).convert("RGBA")
    w, h = im.size
    # No vines: green turns back to iron.
    for y in range(h):
        for x in range(w):
            r, g, b, a = im.getpixel((x, y))
            if a and g > r + 12 and g > b + 12:
                v = int(lum((r, g, b, a)) * 255 * 1.15)
                im.putpixel((x, y), (v, v - 4, v - 8, a))
    reds_for_greens(im, (0, 0, 32, 18))
    # Crimson shoulder plates over the top of the body and arms.
    paint(im, (0, 40, 40, 51), CRIMSON)
    paint(im, (60, 21, 80, 33), CRIMSON)
    paint(im, (60, 58, 80, 70), CRIMSON)
    # Crimson gauntlets on the forearms.
    paint(im, (60, 45, 80, 57), CRIMSON)
    paint(im, (60, 82, 80, 94), CRIMSON)
    # A Red Lantern battery set in its chest (body front is 11..29, 51..63).
    for y in range(53, 62):
        for x in range(16, 24):
            edge = x in (16, 23) or y in (53, 61)
            core = 18 <= x <= 21 and 55 <= y <= 59
            put(im, x, y, BLACK[0] if edge else HOT if core and 19 <= x <= 20 and 56 <= y <= 58 else GLOW if core else CRIMSON[0])
    return im


def main():
    src = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("rage_raider", pillager), ("caged_heart_warden", warden), ("rage_cat", cat), ("blood_iron_golem", golem)):
        fn(src).save(os.path.join(OUT, name + ".png"))
        print("wrote", name)


if __name__ == "__main__":
    main()
