"""Blue Lantern villagers redesigned (J, 2026-10-12: "villagers should just be in blue suits and look
the same, just blue translucent textured skin with a glow and flowing light element over them"):
python tools/blue_villager_light.py <assets_dir>

Run after blue_villager_skin.py and villager_faces.py. In textures/entity/ it:
- turns the villager skin (head, nose, hands) of blue_villager.png and its _focus, _fierce and
  _blink faces into translucent blue hard light skin: shaded by the old skin's brightness, with a
  faint vein texture, about 80% opaque. The brow and mouth turn deep navy, the eyes stay white with
  glowing blue pupils, so the expressions still read.
- adds that skin, bright, to blue_villager_glow.png (drawn emissive over the body) so it glows.
- writes blue_villager_flow_00..15.png: soft bands of light that flow up the whole body, with a
  few twinkles, one frame per 1/16 of the loop (BlueVillagerRenderer steps through them).
"""
import math, os, random, sys
from PIL import Image

S = 4
SKIN_A = 205

DEEP = (18, 66, 168)
LIGHT = (128, 212, 255)
NAVY = (10, 30, 92)
PUPIL = (60, 190, 255)
FLOW = (190, 240, 255)

# The model's boxes: texOffs u, v, size dx, dy, dz, and the body height (texels from the top of
# the head) of the box's top. Used to know how high on the body each texture pixel sits.
BOXES = [
    (0, 0, 8, 10, 8, 0),     # head
    (24, 0, 2, 4, 2, 6),     # nose
    (0, 20, 8, 12, 4, 10),   # body
    (24, 20, 4, 12, 4, 10),  # right arm
    (40, 20, 4, 12, 4, 10),  # left arm
    (0, 36, 4, 12, 4, 22),   # right leg
    (16, 36, 4, 12, 4, 22),  # left leg
]
HEIGHT = 34


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lum(p):
    return (0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]) / 255


def veins(x, y):
    """A faint, smooth vein pattern 0..1 (bright lines where it's near 1)."""
    v = math.sin(x * 0.21 + math.sin(y * 0.13) * 2.2) * math.sin(y * 0.17 + math.sin(x * 0.11) * 2.0)
    return max(0.0, 1 - abs(v) * 6)


def is_skin(p):
    return p[3] > 0 and p[0] > p[2] + 20


def blue_skin(path):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] == 0:
                continue
            if p[:3] == (0x00, 0x96, 0x11):  # green pupils
                px[x, y] = PUPIL + (255,)
            elif not is_skin(p):
                continue
            elif lum(p) < 0.2 or p[:3] == (0x77, 0x42, 0x35):  # brow, mouth
                px[x, y] = NAVY + (255,)
            else:
                # Old skin runs about 0.38 (shadow) to 0.6 (lit); keep that shading in blue.
                t = (lum(p) - 0.36) / 0.26
                c = mix(DEEP, LIGHT, 0.25 + 0.6 * t)
                c = mix(c, (210, 245, 255), 0.45 * veins(x, y))
                px[x, y] = c + (SKIN_A,)
    im.save(path)
    return im


def skin_glow(base, glow_path):
    glow = Image.open(glow_path).convert("RGBA")
    gp, bp = glow.load(), base.load()
    for y in range(base.height):
        for x in range(base.width):
            p = bp[x, y]
            if p[3] == SKIN_A and gp[x, y][3] == 0:
                gp[x, y] = mix(p[:3], (200, 240, 255), 0.35) + (120,)
            elif p[:3] == PUPIL:
                gp[x, y] = PUPIL + (255,)
    glow.save(glow_path)


def face_rects():
    """Each face of each box: (x0, y0, w, h) in texels and a function giving body height for a texel row."""
    out = []
    for u, v, dx, dy, dz, top in BOXES:
        out.append((u + dz, v, dx, dz, lambda ty, t=top: t))                 # top
        out.append((u + dz + dx, v, dx, dz, lambda ty, t=top, h=dy: t + h))  # bottom
        for (fx, fw) in ((u, dz), (u + dz, dx), (u + dz + dx, dz), (u + 2 * dz + dx, dx)):
            out.append((fx, v + dz, fw, dy, lambda ty, t=top: t + ty))
    return out


def flow_frames(folder, frames=16):
    rnd = random.Random(4)
    twinkles = [(rnd.uniform(0, 64), rnd.uniform(0, 52), rnd.uniform(0, 1)) for _ in range(40)]
    rects = face_rects()
    for f in range(frames):
        phase = f / frames
        im = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0))
        px = im.load()
        for (fx, fy, fw, fh, height) in rects:
            for py in range(fh * S):
                for pxl in range(fw * S):
                    tx, ty = (fx * S + pxl) / S, (fy * S + py) / S
                    hy = height(py / S)
                    # Two bands per loop rise up the body; each wavers sideways a little.
                    wave = 1.0 * math.sin(tx * 0.3 + phase * 2 * math.pi)
                    d = ((HEIGHT - hy + wave) / (HEIGHT / 2) - phase * 2) % 1.0
                    d = min(d, 1 - d) * (HEIGHT / 2)  # texels from the nearest band centre
                    a = max(0.0, 1 - d / 2.2) ** 1.6
                    if a <= 0.02:
                        continue
                    col = mix(FLOW, (255, 255, 255), a * 0.5)
                    px[fx * S + pxl, fy * S + py] = col + (round(165 * a),)
        for (tx, ty, ph) in twinkles:
            b = max(0.0, math.sin((phase + ph) * 2 * math.pi))
            if b < 0.6:
                continue
            x, y = int(tx * S), int(ty * S)
            if px[x, y][3] == 0 and not any(r[0] <= tx < r[0] + r[2] and r[1] <= ty < r[1] + r[3] for r in rects):
                continue
            for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + ox < im.width and 0 <= y + oy < im.height:
                    px[x + ox, y + oy] = (235, 250, 255, round(255 * b if (ox, oy) == (0, 0) else 140 * b))
        im.save(os.path.join(folder, "blue_villager_flow_%02d.png" % f))


if __name__ == "__main__":
    folder = os.path.join(sys.argv[1], "textures", "entity")
    base = None
    for suffix in ("", "_focus", "_fierce", "_blink"):
        im = blue_skin(os.path.join(folder, "blue_villager" + suffix + ".png"))
        if suffix == "":
            base = im
    skin_glow(base, os.path.join(folder, "blue_villager_glow.png"))
    flow_frames(folder)
    print("done")
