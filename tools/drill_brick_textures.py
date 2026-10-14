"""Lays the corps' construct brick on J's Blast drills (D1-D3, round-2 pick 2026-10-14):

    python tools/drill_brick_textures.py src/main/resources/assets/lanternring

Every face of each glass_hardlight_* cube in blast_drill_d<n>.bbmodel is filled with the brick
(textures/block/construct_brick[_<corps>].png, first frame shrunk to 16 px a block), box-projected
by the cube's position so neighbouring cubes join up. glow_* and dark_core are left as they are.
Writes blast_drill_d<n>.png and a _<corps> copy for each corps (the rest recoloured as
tools/corps_textures.py does). Safe to run again: the brick faces are always repainted.
"""
import colorsys, json, sys
from PIL import Image

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
STYLE = {"red": (358, 1.15, 0.95), "yellow": (50, 1.1, 1.05), "violet": (282, 1.05, 1.0),
         "blue": (205, 1.0, 1.0), "orange": (25, 1.15, 1.0)}


def recolour(im, corps):
    hue, sat, val = STYLE[corps]
    im = im.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            deg = h * 360
            if s < 0.18 or not (70 <= deg <= 190):
                continue
            nh = ((hue + (deg - 140) * 0.25) % 360) / 360
            nr, ng, nb = colorsys.hsv_to_rgb(nh, min(1, s * sat), min(1, v * val))
            px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
    return im


def brick(corps):
    im = Image.open(f"{A}/textures/block/construct_brick{'' if corps == 'green' else '_' + corps}.png").convert("RGBA")
    w = im.width
    return im.crop((0, 0, w, w)).resize((16, 16), Image.BOX)


# For each face: which model axes run along the texture's u and v, and in which direction.
AXES = {"north": ((0, -1), (1, -1)), "south": ((0, 1), (1, -1)), "east": ((2, -1), (1, -1)),
        "west": ((2, 1), (1, -1)), "up": ((0, 1), (2, 1)), "down": ((0, 1), (2, -1))}


def paint(tex, bb, b):
    px = tex.load()
    bp = b.load()
    sx = tex.width / bb["resolution"]["width"]
    sy = tex.height / bb["resolution"]["height"]
    for el in bb["elements"]:
        if not el["name"].startswith("glass_hardlight"):
            continue
        lo = [min(el["from"][i], el["to"][i]) for i in range(3)]
        hi = [max(el["from"][i], el["to"][i]) for i in range(3)]
        for face, f in el["faces"].items():
            if face not in AXES or "uv" not in f:
                continue
            u0, v0, u1, v1 = f["uv"]
            x0, x1 = sorted((round(u0 * sx), round(u1 * sx)))
            y0, y1 = sorted((round(v0 * sy), round(v1 * sy)))
            (au, du), (av, dv) = AXES[face]
            for y in range(y0, y1):
                for x in range(x0, x1):
                    tu = (x - x0 + 0.5) / max(1, x1 - x0)
                    tv = (y - y0 + 0.5) / max(1, y1 - y0)
                    pu = lo[au] + (hi[au] - lo[au]) * (tu if du > 0 else 1 - tu)
                    pv = lo[av] + (hi[av] - lo[av]) * (tv if dv > 0 else 1 - tv)
                    px[x, y] = bp[int(pu) % 16, int(-pv if av == 1 else pv) % 16]


for d in ("d1", "d2", "d3"):
    with open(f"{A}/bbmodel/blast_drill_{d}.bbmodel") as fh:
        bb = json.load(fh)
    green = Image.open(f"{A}/textures/entity/bb/blast_drill_{d}.png").convert("RGBA")
    for corps in ["green"] + list(STYLE):
        tex = green.copy() if corps == "green" else recolour(green, corps)
        paint(tex, bb, brick(corps))
        out = f"{A}/textures/entity/bb/blast_drill_{d}{'' if corps == 'green' else '_' + corps}.png"
        tex.save(out)
        print("wrote", out)
