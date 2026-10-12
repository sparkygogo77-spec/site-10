"""Textures for Hope Quartz: what the Blue Lantern bearers' hard-light buildings set into.

J (2026-10-12): the Blue bearers' buildings form as glowing blue hard light, then turn into
"high value quartz like good looking blue/white materials that embody the hard light construct
colours". So Hope Quartz is polished white crystal with an ice-blue sheen and blue light running
in its seams, cut in facets like the hard-light plating. Like Skystone (blue_city_textures.py),
every texel is shaded from the surface it stands for (light from the top left, a soft sheen,
darker bevels below and right), with no random speckle. 32x32.

Run from the repo root: python3 tools/hope_quartz_textures.py
"""
import math
import os

from PIL import Image

OUT = "src/main/resources/assets/lanternring/textures/block"
N = 32

# Polished white quartz, lit to shadow, and the blue that runs in its seams.
LIGHT = (252, 254, 255)
FACE = (226, 236, 248)
SHADE = (164, 190, 226)
SEAM = (64, 140, 242)
GLOW_CORE = (246, 252, 255)
GLOW_EDGE = (60, 160, 255)
DEEP = (22, 66, 168)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def quartz(t):
    """Quartz colour for a lighting value t in [-1, 1] (-1 deep shadow, 0 face, 1 highlight)."""
    return mix(FACE, LIGHT, t) if t >= 0 else mix(FACE, SHADE, -t)


def bevel(lx, ly, w, h, size=2):
    """Light on a bevelled slab's rim at local texel (lx, ly), or None on its face."""
    edges = [(ly, 0.85), (lx, 0.65), (h - 1 - ly, -0.8), (w - 1 - lx, -0.55)]
    near, light = min(edges, key=lambda e: e[0])
    return light if near < size else None


def sheen(u, v):
    """A soft diagonal ice-blue sheen across a polished face (u, v in 0..1)."""
    return math.exp(-((u + v - 0.8) ** 2) / 0.05)


def face_colour(u, v, base=0.1):
    col = quartz(base - v * 0.3 + sheen(u, v) * 0.6)
    # The blue sheen of hard light under the polish, strongest away from the highlight.
    return mix(col, (196, 222, 252), 0.25 * (1 - sheen(u, v)) * (0.4 + v * 0.6))


def facets(u, v):
    """Lighting of a cut-crystal face: four planes rising to a ridge cross in the middle."""
    du, dv = u - 0.5, v - 0.5
    if abs(du) > abs(dv):
        return 0.35 if du < 0 else -0.25
    return 0.5 if dv < 0 else -0.4


def hope_quartz():
    # One big polished slab cut as a shallow pyramid of four facets, a blue seam round it.
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            if px in (0, N - 1) or py in (0, N - 1):
                col = SEAM
            else:
                lx, ly = px - 1, py - 1
                b = bevel(lx, ly, N - 2, N - 2)
                if b is not None:
                    col = quartz(b)
                else:
                    u, v = (lx + 0.5) / (N - 2), (ly + 0.5) / (N - 2)
                    col = mix(face_colour(u, v), quartz(facets(u, v)), 0.35)
            img.putpixel((px, py), col + (255,))
    return img


def bricks():
    # Long thin courses of polished quartz, offset by half, with light-blue seams between.
    rows = [(0, 8, 0), (8, 8, 8), (16, 8, 0), (24, 8, 8)]
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            for (y0, h, off) in rows:
                if y0 <= py < y0 + h:
                    break
            lx = (px + off) % 16
            ly = py - y0
            if ly == h - 1 or lx == 15:
                col = SEAM
            else:
                b = bevel(lx, ly, 15, h - 1, size=1)
                col = quartz(b) if b is not None else face_colour((lx + 0.5) / 15, (ly + 0.5) / (h - 1), 0.15)
            img.putpixel((px, py), col + (255,))
    return img


def pillar_side():
    # Three wide rounded flutes with a thin glowing blue groove between them.
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            if px in (0, N - 1):
                col = SEAM
            else:
                k = (px - 1) % 10
                if k == 9 or k == 0:
                    col = mix(GLOW_EDGE, GLOW_CORE, 0.3 if k == 9 else 0.0)
                else:
                    u = (k - 0.5) / 8
                    col = quartz(math.cos((u - 0.3) * math.pi) * 0.9 - 0.3)
                    col = mix(col, (200, 224, 252), 0.15 * (1 - math.sin(u * math.pi)))
            img.putpixel((px, py), col + (255,))
    return img


def pillar_top():
    # The end of the pillar: a ring of polished quartz round a blue gem of light.
    img = Image.new("RGBA", (N, N))
    c = (N - 1) / 2
    for py in range(N):
        for px in range(N):
            r = math.hypot(px - c, py - c)
            lit = -((px - c) + (py - c)) / (2 * 14) * 0.6
            if px in (0, N - 1) or py in (0, N - 1):
                col = SEAM
            elif r > 13.5:
                col = quartz(0.1 + lit)
            elif r > 12.5:
                col = SEAM
            elif r > 5.5:
                col = quartz(0.3 + lit + math.cos((r - 5.5) / 7 * math.pi) * 0.15)
            elif r > 4.5:
                col = SEAM
            else:
                col = mix(GLOW_CORE, GLOW_EDGE, (r / 4.5) ** 1.3)
            img.putpixel((px, py), col + (255,))
    return img


def inlay():
    # Quartz with a channel of hard light set in it: a frame line and the Blue Lantern's ring in
    # the middle, joined by four short spokes. The channel glows (light_emission) white-hot to blue.
    img = Image.new("RGBA", (N, N))
    c = (N - 1) / 2
    for py in range(N):
        for px in range(N):
            r = math.hypot(px - c, py - c)
            frame = min(px, py, N - 1 - px, N - 1 - py)
            ring = abs(r - 8.5)
            spoke = (abs(px - c) < 1 and 10 < abs(py - c) < 13) or (abs(py - c) < 1 and 10 < abs(px - c) < 13)
            if frame == 0:
                col = SEAM
            elif frame == 3 or ring < 0.8 or spoke:
                # The glowing channel: a white-hot line of light.
                col = mix(GLOW_CORE, GLOW_EDGE, 0.2 + (ring if ring < 0.8 else 0) * 0.3)
            elif frame in (2, 4) or ring < 1.8 or (abs(px - c) < 2 and 9.5 < abs(py - c) < 13.5) or (abs(py - c) < 2 and 9.5 < abs(px - c) < 13.5):
                # Its blue halo in the quartz either side.
                col = GLOW_EDGE
            else:
                u, v = px / (N - 1), py / (N - 1)
                b = bevel(px - 1, py - 1, N - 2, N - 2, size=1)
                col = quartz(b) if b is not None else face_colour(u, v)
                if r < 7:
                    col = mix(col, mix(GLOW_EDGE, GLOW_CORE, 0.7), 0.25 * (1 - r / 7))
            img.putpixel((px, py), col + (255,))
    return img


def crystal():
    # See-through blue crystal, cut in four facets, with a white quartz frame. Its translucent
    # facets catch the light at different strengths, like the hard-light plating.
    img = Image.new("RGBA", (N, N))
    for py in range(N):
        for px in range(N):
            frame = min(px, py, N - 1 - px, N - 1 - py)
            if frame == 0:
                col, a = SEAM, 255
            elif frame <= 2:
                b = bevel(px - 1, py - 1, N - 2, N - 2, size=2)
                col, a = quartz(b if b is not None else 0.2), 255
            else:
                u, v = (px - 3 + 0.5) / (N - 6), (py - 3 + 0.5) / (N - 6)
                f = facets(u, v)
                col = mix((36, 112, 232), (150, 206, 255), 0.45 + f * 0.6)
                # The facet ridges catch a white line of light.
                ridge = min(abs(abs(u - 0.5) - abs(v - 0.5)) * 12, 1)
                col = mix((235, 248, 255), col, ridge)
                a = round(140 + (1 - ridge) * 80 + max(f, 0) * 25)
            img.putpixel((px, py), col + (a,))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {
        "hope_quartz": hope_quartz(),
        "hope_quartz_bricks": bricks(),
        "hope_quartz_pillar": pillar_side(),
        "hope_quartz_pillar_top": pillar_top(),
        "hope_inlay": inlay(),
        "hope_crystal": crystal(),
    }
    for name, img in out.items():
        img.save(os.path.join(OUT, name + ".png"))
        print("wrote", name)
    # A contact sheet at 8x for checking the look.
    sheet = Image.new("RGBA", (N * 8 * len(out) + 8 * (len(out) - 1), N * 8), (40, 40, 48, 255))
    for i, img in enumerate(out.values()):
        big = img.resize((N * 8, N * 8), Image.NEAREST)
        sheet.alpha_composite(big, (i * (N * 8 + 8), 0))
    os.makedirs("build", exist_ok=True)
    sheet.save("build/hope_quartz_sheet.png")


if __name__ == "__main__":
    main()
