"""The Red Lantern's Deluge liquid: python tools/ember_liquid_textures.py <assets_dir>

Molten blood-lava, painted in full colour (the game tint is white): plates of dark, cooling crust
that drift slowly, split by thin glowing veins that run from deep red to a hot orange-white core
and pulse as they go. The flowing strip is the same crust stretched and sliding down the face.

Fully opaque, so the game draws it in the solid layer like lava, and Complementary (patched by
ShaderPackPatcher as ID 10070) shades it with its own lava code: the veins glow, the crust stays
dark. Every frame tiles, and the animation loops.
"""
import math, os, random, sys
from PIL import Image

A = sys.argv[1]
OUT = os.path.join(A, "textures", "block")
FRAMES = 32
TAU = 2 * math.pi

CRUST_DARK = (22, 2, 4)
CRUST = (58, 6, 9)
GLOW = (150, 8, 12)
HOT = (236, 34, 20)
CORE = (255, 140, 80)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def ramp(h):
    """Heat 0..1 to colour: crust, then deep red glow, hot red, and a pale core."""
    stops = ((0.0, CRUST_DARK), (0.25, CRUST), (0.6, GLOW), (0.88, HOT), (1.0, CORE))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if h <= t1:
            return lerp(c0, c1, (h - t0) / (t1 - t0))
    return CORE


def points(seed, cells):
    rnd = random.Random(seed)
    pts = []
    for cy in range(cells):
        for cx in range(cells):
            pts.append((cx + rnd.random(), cy + rnd.random(), rnd.random() * TAU, 0.18 + rnd.random() * 0.17, rnd.random()))
    return pts


def wobble(u, v, t):
    """A small tileable warp, so the cell edges wander instead of running straight."""
    return (0.16 * math.sin(TAU * v * 2 + t) + 0.07 * math.sin(TAU * (u + v) * 3 - t),
            0.16 * math.sin(TAU * u * 2 - t) + 0.07 * math.sin(TAU * (u - v) * 3 + t))


def frame(size, f, flow, pts, cells):
    im = Image.new("RGBA", (size, size))
    px = im.load()
    t = f / FRAMES * TAU
    for y in range(size):
        for x in range(size):
            u, v = (x + 0.5) / size, (y + 0.5) / size
            if flow:
                v = (v - f / FRAMES) % 1.0  # the crust slides down the face, one tile per loop
            wu, wv = wobble(u, v, t if not flow else 0)
            pu, pv = (u + wu / cells) * cells, (v + wv / cells) * cells
            if flow:
                pv *= 0.5  # cells stretched along the flow
            d1 = d2 = 9.0
            hot = 0.0
            for (cx, cy, ph, r, melt) in pts:
                # Each plate drifts round a little loop over the animation.
                qx = cx + (0 if flow else r * math.cos(t + ph))
                qy = cy + (0 if flow else r * math.sin(t + ph))
                ny = cells * (0.5 if flow else 1)
                if flow:
                    qy *= 0.5
                dx = (pu - qx + cells / 2) % cells - cells / 2
                dy = (pv - qy + ny / 2) % ny - ny / 2
                d = math.sqrt(dx * dx + dy * dy)
                if d < d1:
                    d1, d2, hot = d, d1, melt
                elif d < d2:
                    d2 = d
            edge = d2 - d1
            vein = max(0.0, 1 - edge / 0.2) ** 1.4
            # The veins pulse, a slow wave of heat travelling across the surface.
            pulse = 0.82 + 0.18 * math.sin(t * 2 + TAU * (u * 2 + v))
            # Crust: darker in the middle of a plate, faint warmth toward its edge, and grain.
            grain = 0.5 + 0.5 * math.sin(TAU * (u * 7 + v * 5)) * math.sin(TAU * (u * 4 - v * 6))
            crust = 0.04 + 0.14 * max(0.0, 1 - edge / 0.55) ** 2 + 0.05 * grain
            # Some plates are thin and still half molten: they glow a dull red through the crust.
            if hot > 0.6:
                crust += (hot - 0.6) * 1.1 * (0.6 + 0.4 * math.sin(t + TAU * (u - v) * 2))
            heat = min(1.0, crust + vein * pulse)
            c = ramp(heat)
            px[x, y] = (int(c[0]), int(c[1]), int(c[2]), 255)
    return im


for name, size, flow, cells, seed in (("ember_still", 32, False, 2, 7), ("ember_flow", 32, True, 2, 11)):
    pts = points(seed, cells)
    strip = Image.new("RGBA", (size, size * FRAMES))
    for f in range(FRAMES):
        strip.paste(frame(size, f, flow, pts, cells), (0, f * size))
    strip.save(os.path.join(OUT, name + ".png"))
    with open(os.path.join(OUT, name + ".png.mcmeta"), "w") as fh:
        fh.write('{\n\t"animation": {\n\t\t"frametime": 3,\n\t\t"interpolate": true\n\t}\n}\n')
