"""The Hawk Whistle's inventory icon: a steel-blue Blue Lantern whistle on a cord, lying on a diagonal.

Drawn at 8x size from its real surface (a cylinder lit from the upper left, so every texel is shaded by
the cylinder's normal, no noise), then reduced to 16x16.

Usage: python tools/hawk_whistle_texture.py src/main/resources/assets/lanternring
"""
import math
import os
import sys

from PIL import Image

S = 8
N = 16 * S


def lit(base, shade):
    return tuple(max(0, min(255, int(c * shade))) for c in base)


def main(assets):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = img.load()
    # The whistle's axis, from the mouthpiece (lower left) to the bell end (upper right), in 16px units.
    ax, ay, bx, by = 2.5, 12.0, 12.5, 4.0
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux  # across the body
    steel = (150, 190, 225)
    band = (40, 120, 255)
    for y in range(N):
        for x in range(N):
            fx, fy = (x + 0.5) / S, (y + 0.5) / S
            t = (fx - ax) * ux + (fy - ay) * uy  # along
            s = (fx - ax) * nx + (fy - ay) * ny  # across
            # Radius: a thin mouthpiece flaring into the body, a round bell end.
            if t < -0.3 or t > length + 0.6:
                continue
            r = 1.3 if t < 2.2 else 2.2
            if t > length - 0.2:
                r = 2.2 * math.sqrt(max(0.0, 1 - ((t - (length - 0.2)) / 0.8) ** 2))
            if abs(s) > r:
                continue
            # Cylinder normal across the body; light from the upper left.
            c = s / r
            nz = math.sqrt(max(0.0, 1 - c * c))
            light = 0.6 + 0.5 * max(0.0, -c * 0.55 + nz * 0.8)
            col = steel
            # A glowing Blue Lantern band round the body, and the sound slot near the bell.
            if 5.6 < t < 6.6:
                col, light = band, 0.9 + 0.3 * nz
            elif length - 3.4 < t < length - 1.9 and -0.2 < s < 1.1:
                col, light = (25, 40, 70), 1.0
            # A crisp darker rim along the edge.
            if abs(s) > r - 0.28:
                light *= 0.62
            px[x, y] = lit(col, light) + (255,)
    # The cord: a loop through the mouthpiece end, hanging down.
    for i in range(400):
        a = i / 400 * math.pi * 1.6 + 0.9
        cx, cy = 3.4 + math.cos(a) * 2.2, 13.2 + math.sin(a) * 1.8
        for ox in range(-2, 3):
            for oy in range(-2, 3):
                X, Y = int(cx * S) + ox, int(cy * S) + oy
                if 0 <= X < N and 0 <= Y < N and px[X, Y][3] == 0:
                    px[X, Y] = (30, 60, 140, 255)
    out = img.resize((16, 16), Image.BOX)
    # Snap alpha so the icon has clean edges.
    o = out.load()
    for y in range(16):
        for x in range(16):
            r, g, b, a = o[x, y]
            o[x, y] = (r, g, b, 255) if a >= 110 else (0, 0, 0, 0)
    path = os.path.join(assets, "textures", "item", "hawk_whistle.png")
    out.save(path)
    out.resize((256, 256), Image.NEAREST).save("/tmp/hawk_whistle_preview.png")
    print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1])
