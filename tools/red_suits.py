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
EYE = (70, 255, 90)
EYE_HOT = (210, 255, 200)


def lum(p):
    return (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255


def ramp(p, pal, lo=0.15, hi=0.75):
    """The pixel's brightness, stretched from lo..hi onto the palette's dark..light."""
    t = min(1.0, max(0.0, (lum(p) - lo) / (hi - lo)))
    a, b = pal
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (p[3],)


def paint(im, box, pal, norm=False, **kw):
    """Shades the region from the palette by each pixel's brightness. With norm, the region's own darkest
    and lightest pixels set the stretch, so dark cloth and bright iron come out equally bright."""
    x0, y0, x1, y1 = box
    if norm:
        ls = [lum(im.getpixel((x, y))) for y in range(y0, y1) for x in range(x0, x1) if im.getpixel((x, y))[3]]
        if ls:
            lo, hi = min(ls), max(ls)
            span = max(hi - lo, 0.2)
            kw = {"lo": lo - span * 0.8, "hi": lo + span}
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


def box(u, v, w, h, d):
    """A model box's faces in its texture, as (x0, y0, x1, y1)."""
    return {
        "top": (u + d, v, u + d + w, v + d),
        "bottom": (u + d + w, v, u + d + 2 * w, v + d),
        "right": (u, v + d, u + d, v + d + h),
        "front": (u + d, v + d, u + d + w, v + d + h),
        "left": (u + d + w, v + d, u + 2 * d + w, v + d + h),
        "back": (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h),
    }


SIDES = ("right", "front", "left", "back")


def bands(im, faces, rows, sides=SIDES):
    """Paints the side faces in horizontal bands: rows is [(first row, end row, palette)], counted down the face."""
    for side in sides:
        x0, y0, x1, y1 = faces[side]
        for r0, r1, pal in rows:
            paint(im, (x0, y0 + r0, x1, min(y1, y0 + r1)), pal, norm=True)


def edges(glow, faces, colour=GLOW, sides=SIDES, rows=None):
    """The glowing silhouette: a line down both edges of each side face, so every corner of the box is lit."""
    for side in sides:
        x0, y0, x1, y1 = faces[side]
        r0, r1 = (y0, y1) if rows is None else (y0 + rows[0], y0 + rows[1])
        for y in range(r0, r1):
            put(glow, x0, y, colour)
            put(glow, x1 - 1, y, colour)


def emblem_big(im, cx, cy, glow=None):
    """The Red Lantern emblem, 6x6: a ring with the lantern's flame inside."""
    rows = ["..##..", ".#..#.", "#.##.#", "#.##.#", ".#..#.", "..##.."]
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                c = HOT if (dx, dy) in ((2, 2), (3, 2)) else GLOW
                put(im, cx + dx, cy + dy, c)
                if glow is not None:
                    put(glow, cx + dx, cy + dy, c)
            elif 1 <= dx <= 4 and 1 <= dy <= 4:
                put(im, cx + dx, cy + dy, BLACK[0])


def pillager(src):
    """P1 Rage Raider, after the Red Lantern troopers: a red helmet, chest plate, shoulder pads, gloves and
    boots over a black undersuit, the emblem on the chest, and a red glowing silhouette."""
    im = Image.open(os.path.join(src, "illager", "pillager.png")).convert("RGBA")
    glow = Image.new("RGBA", im.size)
    head = box(0, 0, 8, 10, 8)
    # The helmet: everything but the face, plus a brow rim over it.
    for side in ("top", "right", "left", "back"):
        paint(im, head[side], CRIMSON, norm=True)
    fx0, fy0, fx1, fy1 = head["front"]
    paint(im, (fx0, fy0, fx1, fy0 + 3), CRIMSON, norm=True)
    for x in range(fx0, fx1):
        put(im, x, fy0 + 3, BLACK[0])
    for x, y in ((9, 14), (10, 14), (13, 14), (14, 14)):
        put(im, x, y, HOT if x in (10, 13) else GLOW)
        put(glow, x, y, HOT if x in (10, 13) else GLOW)
    # The body: a red chest plate over a black undersuit, the emblem in the middle.
    body = box(16, 20, 8, 12, 6)
    paint(im, body["top"], CRIMSON, norm=True)
    bands(im, body, [(0, 12, BLACK), (0, 7, CRIMSON)])
    emblem_big(im, body["front"][0] + 1, body["front"][1] + 1, glow)
    edges(glow, body)
    # Arms: red shoulder pads, black sleeves, red gloves.
    for u, v in ((40, 46),):
        arm = box(u, v, 4, 12, 4)
        paint(im, arm["top"], CRIMSON, norm=True)
        paint(im, arm["bottom"], CRIMSON, norm=True)
        bands(im, arm, [(0, 12, BLACK), (0, 4, CRIMSON), (9, 12, CRIMSON)])
        edges(glow, arm, sides=("right", "left"))
    # Crossed arms (the pose it holds when idle without a crossbow).
    for u, v, w, h, d in ((44, 22, 4, 8, 4), (40, 38, 8, 4, 4)):
        f = box(u, v, w, h, d)
        for side in f.values():
            paint(im, side, BLACK, norm=True)
    # The coat's skirt and belt under the chest plate: black, with a red belt line.
    paint(im, (0, 38, 28, 64), BLACK, norm=True)
    jacket = box(0, 38, 8, 20, 6)
    bands(im, jacket, [(0, 1, CRIMSON)])
    # Legs: black, with red boots.
    leg = box(0, 22, 4, 12, 4)
    paint(im, leg["bottom"], CRIMSON, norm=True)
    bands(im, leg, [(0, 12, BLACK), (7, 12, CRIMSON)])
    edges(glow, leg, sides=("right", "left"))
    return im, glow


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
    """G1 Blood Iron, now a full suit: red armour over a black undersuit from head to foot, green eyes,
    the Red Lantern emblem on the chest and a red glowing silhouette."""
    im = Image.open(os.path.join(src, "iron_golem", "iron_golem.png")).convert("RGBA")
    glow = Image.new("RGBA", im.size)
    w, h = im.size
    # No vines.
    for y in range(h):
        for x in range(w):
            r, g, b, a = im.getpixel((x, y))
            if a and g > r + 12 and g > b + 12:
                v = int(lum((r, g, b, a)) * 255 * 1.15)
                im.putpixel((x, y), (v, v - 4, v - 8, a))
    # Head: a red helmet with a black visor band across the eyes; the eyes glow green.
    head = box(0, 0, 8, 10, 8)
    for side in head.values():
        paint(im, side, CRIMSON, norm=True)
    fx0, fy0, fx1, fy1 = head["front"]
    for x in range(fx0, fx1):
        for y in range(fy0 + 4, fy0 + 7):
            put(im, x, y, BLACK[0] if y == fy0 + 4 else BLACK[1])
    for x, y in ((9, 13), (10, 13), (13, 13), (14, 13), (9, 14), (10, 14), (13, 14), (14, 14)):
        c = EYE_HOT if y == 14 and x in (9, 14) else EYE
        put(im, x, y, c)
        put(glow, x, y, c)
    paint(im, (24, 0, 32, 6), CRIMSON, norm=True)  # the nose
    # Chest: red plate, black at the sides, the emblem big in the middle.
    body = box(0, 40, 18, 12, 11)
    paint(im, body["top"], CRIMSON, norm=True)
    paint(im, body["bottom"], BLACK, norm=True)
    bands(im, body, [(0, 12, CRIMSON), (8, 12, BLACK)], sides=("front", "back"))
    bands(im, body, [(0, 12, BLACK), (0, 4, CRIMSON)], sides=("right", "left"))
    emblem_big(im, body["front"][0] + 6, body["front"][1] + 1, glow)
    edges(glow, body)
    # Waist: black with a red belt line.
    waist = box(0, 70, 9, 5, 6)
    for side in waist.values():
        paint(im, side, BLACK, norm=True)
    bands(im, waist, [(0, 1, CRIMSON)])
    # Arms: red shoulder pads, black upper arm, red gauntlets with a black cuff.
    for u, v in ((60, 21), (60, 58)):
        arm = box(u, v, 4, 30, 6)
        paint(im, arm["top"], CRIMSON, norm=True)
        paint(im, arm["bottom"], CRIMSON, norm=True)
        bands(im, arm, [(0, 30, BLACK), (0, 9, CRIMSON), (17, 30, CRIMSON), (17, 18, BLACK)])
        edges(glow, arm)
    # Legs: black thighs, red boots.
    for u, v in ((37, 0), (60, 0)):
        leg = box(u, v, 6, 16, 5)
        paint(im, leg["top"], BLACK, norm=True)
        paint(im, leg["bottom"], CRIMSON, norm=True)
        bands(im, leg, [(0, 16, BLACK), (8, 16, CRIMSON)])
        edges(glow, leg)
    return im, glow


def main():
    src = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("rage_raider", pillager), ("caged_heart_warden", warden), ("rage_cat", cat), ("blood_iron_golem", golem)):
        out = fn(src)
        im, glow = out if isinstance(out, tuple) else (out, None)
        im.save(os.path.join(OUT, name + ".png"))
        if glow is not None:
            glow.save(os.path.join(OUT, name + "_glow.png"))
        print("wrote", name)


if __name__ == "__main__":
    main()
