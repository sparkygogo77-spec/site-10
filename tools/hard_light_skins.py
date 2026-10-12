"""Paints the Blue Lantern's hard light construct skins from J's concept sheets (2026-10-12):
python tools/hard_light_skins.py <assets_dir>

Writes textures/entity/blue_construct.png (the Blue villager while it's still a construct, the
64x64 layout of BlueVillagerModel at 4x) and textures/entity/hope_golem.png (the Hope Golem, the
vanilla iron golem's 128x128 layout at 4x).

The look, from the sheets: faceted crystal plates in blue (each face split into flat facets,
lit from the top left, with lighter facet edges), a bright chiselled rim round every face, the Blue
Lantern emblem glowing on the chest, two glowing eyes, banded joints on the limbs. Plates are
mostly opaque (about 75%) so it reads as hard light, not clear glass; rims, emblem and eyes are
fully opaque. Everything is painted bright: the renderer draws it emissive (glow isn't additive).
"""
import math, os, random, sys
from PIL import Image

S = 4  # image pixels per texel

DEEP = (8, 46, 140)
MID = (34, 128, 232)
HI = (120, 210, 255)
RIM = (95, 215, 255)
CORE = (228, 250, 255)
DARK = (6, 24, 80)

PLATE_A, EDGE_A = 192, 222


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(t):
    """Deep blue in the shadows to pale cyan in the highlights."""
    t = max(0.0, min(1.0, t))
    return mix(DEEP, MID, t / 0.6) if t < 0.6 else mix(MID, HI, (t - 0.6) / 0.4)


class Face:
    def __init__(self, u, v, w, h, kind, light):
        self.u, self.v, self.w, self.h = u, v, w, h  # texels
        self.kind = kind    # front, back, side, top, bottom
        self.light = light  # base brightness 0..1 (tops brighter, bottoms darker)
        self.emblem = None  # (cx, cy, r) texels
        self.eyes = []      # (cx, cy) texels
        self.ridge = False  # a bright line down the middle from the top (head front)
        self.smooth = False # no facets: a face, painted later by villager_faces.py
        self.bands = []     # texel rows with a dark groove and bright lip (joints)


def box(u, v, dx, dy, dz, light=0.5):
    """The six faces of a ModelPart box at texOffs (u, v), dx wide, dy tall and dz deep."""
    return {
        "top": Face(u + dz, v, dx, dz, "top", light + 0.18),
        "bottom": Face(u + dz + dx, v, dx, dz, "bottom", light - 0.2),
        "right": Face(u, v + dz, dz, dy, "side", light - 0.06),
        "front": Face(u + dz, v + dz, dx, dy, "front", light),
        "left": Face(u + dz + dx, v + dz, dz, dy, "side", light - 0.06),
        "back": Face(u + 2 * dz + dx, v + dz, dx, dy, "back", light - 0.1),
    }


def emblem(cx, cy, r, x, y):
    """The Blue Lantern emblem from the sheets: an outer ring, an inner ring round a dark core,
    and a barred post above and below joining them. Returns brightness 0..1 of the lines or None."""
    dx, dy = (x - cx) / r, (y - cy) / r
    d = math.hypot(dx, dy)
    if d > 1.25:
        return None
    if d > 1.0:
        return ("halo", (1.25 - d) / 0.25)
    if d > 0.8:
        return ("line", 1 - abs(d - 0.9) / 0.1)
    if 0.34 < d < 0.54:
        return ("line", 1 - abs(d - 0.44) / 0.1)
    if d <= 0.34:
        return ("core", d / 0.34)
    ay = abs(dy)
    if abs(dx) < 0.11 and 0.5 < ay < 0.84:
        return ("line", 1.0)
    if 0.6 < ay < 0.72 and abs(dx) < 0.36:
        return ("line", 1.0)
    return ("disc", d)


def paint(img, face, seed):
    """Fills one face: Voronoi facets, facet edges, banded joints, emblem, eyes and the rim."""
    px = img.load()
    rnd = random.Random(seed)
    x0, y0, w, h = face.u * S, face.v * S, face.w * S, face.h * S
    if w <= 0 or h <= 0:
        return
    n = max(2, round(w * h / (S * S * 12)))
    seeds = [(rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(-0.16, 0.16)) for _ in range(n)]
    for y in range(h):
        for x in range(w):
            # The nearest two facet seeds: the facet's shade, and how close the edge between them is.
            best = second = 1e9
            off = 0.0
            for sx, sy, o in seeds:
                dd = (sx - x - 0.5) ** 2 + (sy - y - 0.5) ** 2
                if dd < best:
                    second, best, off = best, dd, o
                elif dd < second:
                    second = dd
            edge = math.sqrt(second) - math.sqrt(best)
            if face.smooth:
                off, edge = 0.06, 9.0
            sheen = 0.18 * (1 - (x / w + y / h) / 2)  # light from the top left
            t = face.light + off + sheen
            col, a = ramp(t), PLATE_A
            if edge < 1.0:
                col, a = mix(col, HI, 0.4), EDGE_A
            ty = y / S
            for b in face.bands:
                if b - 0.5 <= ty < b + 0.25:
                    col, a = mix(DARK, DEEP, 0.4), 230
                elif b + 0.25 <= ty < b + 0.75:
                    col, a = mix(RIM, CORE, 0.3), 255
            if face.ridge and abs(x + 0.5 - w / 2) < S * 0.5 and ty < face.h * 0.45:
                col, a = mix(RIM, CORE, 0.6 - ty / face.h), 255
            if face.emblem:
                e = emblem(*face.emblem, (x + 0.5) / S, (y + 0.5) / S)
                if e:
                    kind, v = e
                    if kind == "halo":
                        col, a = mix(col, RIM, v * 0.7), max(a, 220)
                    elif kind == "line":
                        col, a = mix(RIM, CORE, 0.4 + 0.6 * v), 255
                    elif kind == "core":
                        col, a = mix((40, 150, 255), DARK, v * 0.8), 255
                    else:
                        col, a = mix((10, 40, 120), DARK, v), 245
            for ex, ey in face.eyes:
                d = math.hypot((x + 0.5) / S - ex, (y + 0.5) / S - ey)
                if d < 0.55:
                    col, a = CORE, 255
                elif d < 1.05:
                    col, a = mix(CORE, RIM, (d - 0.55) / 0.5), 255
                elif d < 1.4:
                    col, a = mix(col, RIM, (1.4 - d) / 0.35 * 0.8), 255
            # The chiselled rim: a half-texel bright frame, a pale line inside it, then a soft bevel.
            r = min(x, y, w - 1 - x, h - 1 - y)
            if face.smooth and face.w <= 2:
                r = min(r, 9) if r else 0  # the nose: only a thin rim, so it reads as a nose
                if r >= 1:
                    r = 9
            if r == 0:
                col, a = mix(RIM, CORE, 0.2), 255
            elif r == 1:
                col, a = mix(CORE, RIM, 0.15), 255
            elif r < S:
                col, a = mix(col, RIM, 0.35 if r == 2 else 0.15), max(a, EDGE_A)
            px[x0 + x, y0 + y] = col + (a,)


def paint_all(size, faces, path):
    img = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    for i, f in enumerate(faces):
        paint(img, f, 1000 + i)
    img.save(path)
    print("wrote", path)


def villager():
    # The face stays a villager's (brow, eyes, mouth and nose; tools/villager_faces.py paints them
    # and the expressions), so the head front and nose are smooth hard light, not facets.
    head = box(0, 0, 8, 10, 8, 0.55)
    head["front"].smooth = True
    nose = box(24, 0, 2, 4, 2, 0.5)
    for f in nose.values():
        f.smooth = True
    body = box(0, 20, 8, 12, 4, 0.5)
    body["front"].emblem = (4.0, 4.0, 2.9)
    body["back"].bands = [6, 9]
    arms = [box(24, 20, 4, 12, 4, 0.48), box(40, 20, 4, 12, 4, 0.48)]
    legs = [box(0, 36, 4, 12, 4, 0.42), box(16, 36, 4, 12, 4, 0.42)]
    for part in arms + legs:
        for k in ("front", "back", "right", "left"):
            part[k].bands = [5, 10]
    faces = []
    for part in [head, nose, body] + arms + legs:
        faces += part.values()
    return faces


def golem():
    head = box(0, 0, 8, 10, 8, 0.55)
    head["front"].eyes = [(2.0, 4.4), (6.0, 4.4)]
    head["front"].ridge = True
    nose = box(24, 0, 2, 4, 2, 0.5)
    body = box(0, 40, 18, 12, 11, 0.52)
    body["front"].emblem = (9.0, 5.2, 4.2)
    waist = box(0, 70, 9, 5, 6, 0.4)
    for k in ("front", "back", "right", "left"):
        waist[k].bands = [1.2, 3.2]
    arms = [box(60, 21, 4, 30, 6, 0.48), box(60, 58, 4, 30, 6, 0.48)]
    for a in arms:
        for k in ("front", "back", "right", "left"):
            a[k].bands = [9, 19]
    legs = [box(37, 0, 6, 16, 5, 0.42), box(60, 0, 6, 16, 5, 0.42)]
    for l in legs:
        for k in ("front", "back", "right", "left"):
            l[k].bands = [7]
    faces = []
    for part in [head, nose, body, waist] + arms + legs:
        faces += part.values()
    return faces


if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "textures", "entity")
    paint_all(64, villager(), os.path.join(out, "blue_construct.png"))
    paint_all(128, golem(), os.path.join(out, "hope_golem.png"))
