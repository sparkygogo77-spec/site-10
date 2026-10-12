"""Paints the Blue Lantern villager's suit from J's reference sheet (2026-10-12):
python tools/blue_villager_skin.py <minecraft client jar> <assets_dir>

Writes textures/entity/blue_villager.png and blue_villager_glow.png (256x256: the 64x64 layout of
BlueVillagerModel at 4x, so the emblems and circuit lines stay sharp).

- Head and nose: the vanilla villager's, copied texel for texel (the sheet uses the plain villager head).
- Suit: dark navy, every texel shaded from the surface it stands for (brighter up the chest and
  shoulders, darkest at the feet, a little darker at each face's edges) and lit blue by the circuit
  lines near it, which is where the sheet's lighter cells come from. No random noise.
- Circuit lines and the Blue Lantern emblem (chest, both shoulders) are painted into the suit and
  again, bright, on the glow layer (glow isn't additive in 26.3, so it must be painted at full colour).
- Bare hands: the bottom row of each sleeve and the bottom of the arm are villager skin.

Layout in 64x64 units (ModelPart box UV): head (0,0) 8x10x8, nose (24,0) 2x4x2, body (0,20) 8x12x4,
right arm (24,20), left arm (40,20), right leg (0,36), left leg (16,36), all 4x12x4.
"""
import io, math, os, sys, zipfile
from PIL import Image

S = 4  # image pixels per texel
W = 64 * S

JAR, ASSETS = sys.argv[1], sys.argv[2]

skin = Image.new("RGBA", (W, W), (0, 0, 0, 0))
glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
sp, gp = skin.load(), glow.load()

# ---- head and nose from the vanilla villager -----------------------------------------------------
with zipfile.ZipFile(JAR) as z:
    vanilla = Image.open(io.BytesIO(z.read("assets/minecraft/textures/entity/villager/villager.png"))).convert("RGBA")
for (u, v, w, h) in [(0, 0, 32, 18), (24, 0, 8, 6)]:
    part = vanilla.crop((u, v, u + w, v + h)).resize((w * S, h * S), Image.NEAREST)
    skin.paste(part, (u * S, v * S))
SKIN = vanilla.getpixel((9, 16))[:3]  # a cheek texel: the villager's skin tone

# ---- colours -------------------------------------------------------------------------------------
NAVY_HI = (22, 52, 128)   # upper chest, under the glow
NAVY = (12, 26, 70)
NAVY_LO = (7, 12, 30)     # feet
LINE_CORE = (215, 240, 255)
LINE = (70, 165, 255)
LINE_EDGE = (30, 105, 235)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---- faces ---------------------------------------------------------------------------------------
class Face:
    """One face of a box: its place on the texture in texels, and where it sits on the body."""

    def __init__(self, u, v, w, h, y0, height, kind):
        self.u, self.v, self.w, self.h = u, v, w, h
        self.y0, self.height = y0, height  # body height (0 top of shoulders .. 1 feet) of its top and span
        self.kind = kind                   # front, back, side, top, bottom
        self.lines = []                    # glowing segments in texel coords ((x0, y0), (x1, y1))
        self.emblem = None                 # (cx, cy, r) in texels
        self.skin_rows = 0                 # bare-hand rows at the bottom

    def line(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.lines.append((a, b))
        return self


def box(u, v, dx, dy, dz, y0, height):
    """The six faces of a ModelPart box at texOffs (u, v)."""
    return {
        "top": Face(u + dz, v, dx, dz, y0, 0, "top"),
        "bottom": Face(u + dz + dx, v, dx, dz, y0 + height, 0, "bottom"),
        "right": Face(u, v + dz, dz, dy, y0, height, "side"),
        "front": Face(u + dz, v + dz, dx, dy, y0, height, "front"),
        "left": Face(u + dz + dx, v + dz, dz, dy, y0, height, "side"),
        "back": Face(u + 2 * dz + dx, v + dz, dx, dy, y0, height, "back"),
    }


# Body height fractions: the suit runs from the shoulders (0) to the feet (1), torso first half.
body = box(0, 20, 8, 12, 4, 0.0, 0.5)
arms = {"right": box(24, 20, 4, 12, 4, 0.0, 0.5), "left": box(40, 20, 4, 12, 4, 0.0, 0.5)}
legs = {"right": box(0, 36, 4, 12, 4, 0.5, 0.5), "left": box(16, 36, 4, 12, 4, 0.5, 0.5)}

# Chest: the emblem high on the chest, and two lines down the stomach that hook outward at the belt.
body["front"].emblem = (4.0, 3.7, 2.55)
body["front"].line((1.5, 6.3), (1.5, 9.5), (0.0, 10.6))
body["front"].line((6.5, 6.3), (6.5, 9.5), (8.0, 10.6))
body["front"].line((0.0, 11.5), (1.2, 11.5))
body["front"].line((6.8, 11.5), (8.0, 11.5))
# Back: two lines that flare out over the shoulder blades and again at the waist.
body["back"].line((0.6, 1.2), (2.4, 3.0), (2.4, 7.5), (0.6, 9.6))
body["back"].line((7.4, 1.2), (5.6, 3.0), (5.6, 7.5), (7.4, 9.6))
for side in ("right", "left"):
    body[side].line((0.8, 8.5), (3.2, 8.5))

for side, a in arms.items():
    # Emblem on the outside of the shoulder, glowing dashes round the elbow, bare hand at the cuff.
    outer = a["right"] if side == "right" else a["left"]
    outer.emblem = (2.0, 2.7, 1.75)
    for f in ("front", "back", "right", "left"):
        a[f].line((0.7, 6.5), (3.3, 6.5))
        a[f].skin_rows = 1
    a["bottom"].skin_rows = 4

for side, l in legs.items():
    m = 1 if side == "right" else -1
    c = 2.0 if side == "right" else 2.0
    out = 0.5 if side == "right" else 3.5
    inn = 2.6 if side == "right" else 1.4
    l["front"].line((c, 0.0), (c, 4.6))
    l["front"].line((out, 6.6), (out, 9.0), (inn, 9.0))
    l["front"].line((1.0, 11.4), (3.0, 11.4))
    l["back"].line((c, 1.0), (c, 5.5))
    l["back"].line((out, 8.0), (out, 10.2))
    for f in ("right", "left"):
        l[f].line((0.8, 5.5), (3.2, 5.5))
        l[f].line((1.2, 10.0), (2.8, 10.0))

ALL = list(body.values()) + [f for a in arms.values() for f in a.values()] + [f for l in legs.values() for f in l.values()]


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def emblem(face, x, y):
    """Blue Lantern emblem at texel point (x, y): returns (colour, glow alpha) or None.

    A bright ring round a deep blue disc; inside, the lantern: a small round body with a flat base
    and five short rays fanning up from it, like the sheet's chest badge."""
    cx, cy, r = face.emblem
    dx, dy = (x - cx) / r, (y - cy) / r
    d = math.hypot(dx, dy)
    if d > 1.18:
        return None
    if d > 1.0:  # soft halo
        return (mix(NAVY_HI, LINE_EDGE, (1.18 - d) / 0.18 * 0.9), 0)
    if d > 0.78:  # the outer ring
        return (mix(LINE_CORE, LINE, abs(d - 0.89) / 0.11), 255)
    # Inside: the lantern sits low in the disc.
    lx, ly = dx, dy - 0.12
    body_r = math.hypot(lx, ly)
    if body_r < 0.2:
        return ((240, 250, 255), 255)
    if body_r < 0.32:
        return (LINE, 255)
    if 0.28 < ly < 0.40 and abs(lx) < 0.34:  # flat base
        return (LINE_CORE, 255)
    if ly < -0.25 and body_r < 0.66:  # rays fanning up
        ang = math.degrees(math.atan2(lx, -ly))
        for a in (-56, -28, 0, 28, 56):
            if abs(ang - a) < 7:
                return (mix(LINE_CORE, LINE, (body_r - 0.32) / 0.34), 255)
    return (mix((16, 50, 120), (10, 30, 80), d), 0)


def shade(face, tx, ty):
    """Suit colour of the texel at (tx, ty) on this face, before glow."""
    # Height down the body: the chest is lit and the feet are in shadow.
    if face.kind in ("top", "bottom"):
        h = face.y0
    else:
        h = face.y0 + face.height * (ty + 0.5) / face.h
    base = mix(NAVY_HI, NAVY, h / 0.45) if h < 0.45 else mix(NAVY, NAVY_LO, (h - 0.45) / 0.55)
    # Faces turned from the light are darker; edges of each face a touch darker (rounded seams).
    k = {"front": 1.0, "side": 0.9, "back": 0.85, "top": 1.1, "bottom": 0.6}[face.kind]
    ex = min(tx + 0.5, face.w - tx - 0.5) / max(1, face.w / 2)
    k *= 0.86 + 0.14 * min(1, ex * 2.2)
    # Panel cells: every other texel a hair darker, as on the sheet's suit grid.
    if (tx + ty) % 2 == 1:
        k *= 0.93
    return tuple(min(255, round(c * k)) for c in base)


def paint(face):
    for py in range(face.h * S):
        for px in range(face.w * S):
            x, y = (px + 0.5) / S, (py + 0.5) / S
            tx, ty = int(x), int(y)
            X, Y = face.u * S + px, face.v * S + py
            if face.skin_rows and ty >= face.h - face.skin_rows:
                k = 0.92 if face.kind != "bottom" else 0.8
                sp[X, Y] = tuple(round(c * k) for c in SKIN) + (255,)
                continue
            col = shade(face, tx, ty)
            # Light from the nearby circuit lines and emblem, judged at the texel's middle so the
            # suit stays pixel-crisp.
            cx, cy = tx + 0.5, ty + 0.5
            near = min([seg_dist((cx, cy), a, b) for a, b in face.lines] + [99])
            if face.emblem:
                ex, ey, er = face.emblem
                near = min(near, max(0, math.hypot(cx - ex, cy - ey) - er))
            col = mix(col, LINE_EDGE, 0.55 * math.exp(-near / 0.9))
            g = None
            # The lines themselves, at full resolution: a white-hot core in a blue line.
            d = min([seg_dist((x, y), a, b) for a, b in face.lines] + [99])
            if d < 0.42:
                lc = mix(LINE_CORE, LINE, (d - 0.12) / 0.3) if d > 0.12 else LINE_CORE
                col, g = lc, lc
            if face.emblem:
                e = emblem(face, x, y)
                if e:
                    col = e[0]
                    g = e[0] if e[1] else None
            sp[X, Y] = col + (255,)
            if g:
                gp[X, Y] = g + (255,)


for f in ALL:
    paint(f)

out = os.path.join(ASSETS, "textures", "entity")
skin.save(os.path.join(out, "blue_villager.png"))
glow.save(os.path.join(out, "blue_villager_glow.png"))
print("wrote", out)
