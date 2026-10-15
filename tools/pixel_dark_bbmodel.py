"""Writes the pixel-grid Dark Lantern (tools/pixel_dark_lantern4.py) as the Blockbench model the mod
draws: assets/lanternring/bbmodel/dark_lantern.bbmodel and textures/entity/bb/dark_lantern.png, the
model the held, placed and dropped Dark Lantern use. Neighbouring cubes of the same part merge into
as few boxes as possible; every box face is painted pixel by pixel with the same colours Blender
shows (face_colour), 4 texture pixels per unit = one per model pixel. Nothing is full-bright: the
lantern is dark at rest, as J wants. Run tools/bbmodel_json.py afterwards.

    python tools/pixel_dark_bbmodel.py src/main/resources/assets/lanternring [version, default l1]
"""
import math, os, sys
import numpy as np
import base64, io, json, uuid
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
VER = sys.argv[2] if len(sys.argv) > 2 else "l1"
_argv, sys.argv = sys.argv, ["pixel_dark_lantern4.py", "/tmp/dark_unused"]
import pixel_dark_lantern4 as D
sys.argv = _argv

DENSITY = 4
CLEAR = (0, 0, 0, 0)
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
exec(_src[_src.index("def _texel("):_src.index("AXES = {")])

p = D.VERSIONS[VER]
xs, zs, part, pz = D.build(p)
G = D.G
ZSHIFT = 0.75   # the model's foot starts 0.75 up; stand it on the block's floor


def boxes(mask):
    m = mask.copy()
    out = []
    S = m.shape
    for k in range(S[2]):
        for j in range(S[1]):
            for i in range(S[0]):
                if not m[i, j, k]:
                    continue
                i2 = i
                while i2 + 1 < S[0] and m[i2 + 1, j, k]:
                    i2 += 1
                j2 = j
                while j2 + 1 < S[1] and m[i:i2 + 1, j2 + 1, k].all():
                    j2 += 1
                k2 = k
                while k2 + 1 < S[2] and m[i:i2 + 1, j:j2 + 1, k2 + 1].all():
                    k2 += 1
                m[i:i2 + 1, j:j2 + 1, k:k2 + 1] = False
                out.append((i, j, k, i2, j2, k2))
    return out


def to_bb(x, y, z):
    return (-x, z, y)


FACE_N = {"north": (0, -1, 0), "south": (0, 1, 0), "east": (-1, 0, 0), "west": (1, 0, 0), "up": (0, 0, 1), "down": (0, 0, -1)}
x0g, z0g = xs[0] - G / 2, zs[0] - G / 2


def painter(pid, frm, to):
    def paint(face, w, h):
        n = FACE_N[face]
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2      # back inside the cube this face belongs to
                i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                c = np.array([xs[i], xs[j], zs[k]])
                col, kind = D.face_colour(pid, i, j, k, n, c, p)
                row.append(tuple(int(round(min(255, max(0, v_)))) for v_ in col) + (255,))
            rows.append(row)
        return rows
    return paint


model = Model("dark_lantern", density=DENSITY)
count = 0


def any_painter(frm, to):
    def paint(face, w, h):
        n = FACE_N[face]
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2
                i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                c = np.array([xs[i], xs[j], zs[k]])
                col, kind = D.face_colour(int(part[i, j, k]), i, j, k, n, c, p)
                row.append(tuple(int(round(min(255, max(0, v_)))) for v_ in col) + (255,))
            rows.append(row)
        return rows
    return paint


# Performance (J: 140 -> 70 fps): every box costs the same to draw however big, so the whole lantern
# is merged as one shape, not part by part; each texel still takes its own part's colour.
for n_, (i, j, k, i2, j2, k2) in enumerate(boxes(part > 0)):
    x0, x1 = xs[i] - G / 2, xs[i2] + G / 2
    y0, y1 = xs[j] - G / 2, xs[j2] + G / 2
    z0, z1 = zs[k] - G / 2 - ZSHIFT, zs[k2] + G / 2 - ZSHIFT
    a, b = to_bb(x1, y0, z0), to_bb(x0, y1, z1)
    frm = [round(min(a[c], b[c]), 4) for c in range(3)]
    to = [round(max(a[c], b[c]), 4) for c in range(3)]
    model.cube(f"body_{n_}", frm, to, any_painter(frm, to))
    count += 1


# G3 R4, J's pick from the Blender thread (docs/handoff/2026-10-13-constructs-and-lantern/lantern/):
# the charge light baked into frames of a separate glow model (dark_lantern_glow) the mod cross-fades.
#  - CHARGE frames dark_lantern_glow_c0..c15 run through the 12 s charge (u = 0..1 of it): the light
#    spreads out from the port over the first 3 s in the lantern's own greens, the ball behind the
#    port grows in brightness (not reach) with the charge, the gold cracks fill from the centre
#    outwards (a gold flash as the light runs through them, then a dim gold) reaching the edges at
#    85% and swallowed by the green from 95%, and the glass fades to near-black emerald at the ends.
#  - dark_lantern_glow_climax: the 140% overcharge, a very bright saturated green, never white.
#  - dark_lantern_glow_flash: the let-go flash, a pulse on the core, drawn on top.
#  - SWIRL frames (a smaller model, dark_lantern_swirl, only the middle band): the strands of the
#    spinning ball, one third of a turn over SWIRL frames; the mod plays them from accumulated time
#    (0.5 + 4.5 x charge rad/s) so it only ever turns one way.
# Round 4 (J on L1c, docs/handoff/2026-10-14-lantern-charge): "my lantern should be much brighter than this... it's
# just using the sphere, I want the light running further down the model". The charge frames now follow the hand-off's
# fill rule (fill_light): the glass lights from the top down to the base as the charge rises, with a bright band at
# the lit front; only the dark glass lights, the gold stays metal. 24 frames so the band steps down smoothly.
CHARGE_FRAMES = 24
SWIRL_FRAMES = 8
STATE = {"u": 0.0, "c": 0.0, "mode": "charge", "phase": 0.0}
z0b, z1b = p["body"]


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# The lantern's own greens; yellow mixed into the hot flow; the hottest burn yellow-green, never white.
RAMP = [(0.0, (1, 12, 8)), (0.18, (3, 50, 32)), (0.36, (8, 118, 66)), (0.56, (24, 196, 84)), (0.76, (64, 255, 92)),
        (0.9, (100, 255, 84)), (1.0, (120, 255, 80))]


def ramp(v):
    v = max(0.0, min(1.0, v))
    for (p0, c0), (p1, c1) in zip(RAMP, RAMP[1:]):
        if v <= p1:
            f = (v - p0) / (p1 - p0)
            return np.array([c0[i] + (c1[i] - c0[i]) * f for i in range(3)])
    return np.array(RAMP[-1][1], float)


def end_fade(z, c):
    """1 in the middle of the glass, down to near-black emerald at the very top and bottom (exp falloff)."""
    d_px = min(z - z0b, z1b - z) / G
    return 1.0 - math.exp(-max(0.0, d_px) / (4.4 + 1.6 * c))


def charge_light(pid, cc, gw, hv, i, j, k):  # noqa: C901
    """(r, g, b) of a glass pixel at this frame's charge."""
    u, c, mode = STATE["u"], STATE["c"], STATE["mode"]
    x, y, z = cc
    spread = 1.0 if mode != "charge" else smooth(u * 4.0)        # out from the port over the first 3 of 12 s
    dz = z - pz
    rad = math.hypot(x, y)
    front = math.sqrt(x * x + (y - FRONT_Y) ** 2 + dz * dz)             # from the port, on the front
    reach = 2.0 + 15.0 * spread
    mask = max(0.0, min(1.0, (reach - front) / 3.0))
    ends = end_fade(z, c)
    if mode == "flash":
        core = math.exp(-((math.sqrt(dz * dz + 0.3 * rad * rad)) / 3.2) ** 2)
        L = 1.1 * core * ends
        return ramp(0.55 + 0.4 * L) * min(1.0, L)
    ball = math.exp(-((math.sqrt(dz * dz + 0.25 * rad * rad)) / 4.2) ** 2)
    cg = min(c, 1.4)
    glass = (0.35 + 0.65 * gw) * (0.42 + 0.58 * min(cg, 1.0) + 0.35 * max(0.0, cg - 1.0))
    L = (glass + 1.25 * ball * cg) * ends * mask
    if pid == D.VEIN:
        # gold cracks: dark lines first; the light runs through them centre-out as one gold flash, then
        # they hold a dim gold; the green swallows them from about 95%
        fz = min(1.0, abs(dz) / ((z1b - z0b) / 2))
        front_ = min(cg, 1.0) / 0.85
        if fz > front_:
            gold = np.zeros(3)
        else:
            run = math.exp(-((front_ - fz) / 0.07) ** 2)
            gold = (np.array([120, 88, 26.0]) * (0.6 + 0.4 * (hv / 255)) + np.array([200, 150, 40.0]) * run) * ends
        swallow = smooth((cg - 0.95) / 0.2)
        green = ramp(L * 0.8) * min(1.0, L * L * 0.7)
        return gold * (1 - swallow) + green * swallow
    if pid == D.RIB and p.get("glassy") and D.on_streak(cc, p) and (k // 2) % 2 == 0:
        return np.zeros(3)                                        # the stitches stay darkest green
    # yellow mixed into the green flow: some pixels lean yellow as they get hot
    yellow = 0.15 * (hv / 255) * smooth((L - 0.8) / 0.6)
    col = ramp(L * 0.72 + 0.08 * hv / 255) * min(1.0, 0.25 + 0.75 * L)
    col = col + np.array([90, 20, -20.0]) * yellow * min(1.0, L)
    if cg > 1.0:
        # the climax: a very bright saturated green
        col = col * (1 + 0.5 * (cg - 1.0)) + np.array([0, 60, 0.0]) * (cg - 1.0) * min(1.0, L)
    return col


LIME = np.array([150, 255, 120.0])        # the light lime the hottest light leans toward, never white
SATURATED = np.array([40, 255, 80.0])     # the saturated corps green (Blender's emission 0.2, 1.0, 0.3)


def fill_light(pid, cc, gw, hv, i, j, k):
    """(r, g, b) of a glass pixel by the hand-off's fill rule, at this frame's charge c (1.4 for the climax).

    h runs from 0 at the base to 1 at the handle's top. The lit front is at h = 1.05 - 1.15 c; everything above it is
    lit, and a band about 7% of the height wide runs along it at 3x. Only dark texels light: full glow up to 0.05
    brightness, 15% by 0.35, so the gold frame stays metal. About 5x emission in the saturated corps colour (14x washed
    out to white), shown here as brightness that saturates, leaning toward light lime only in the band. Nothing glows at
    charge 0."""
    c, mode = STATE["c"], STATE["mode"]
    if mode == "flash":
        return charge_light(pid, cc, gw, hv, i, j, k)
    if c <= 0.0:
        return np.zeros(3)
    h = (cc[2] - Z_LO) / (Z_HI - Z_LO)
    # J (2026-10-14, 3b): glow sooner. The rule's front started above the handle, so the glass stayed dark for the
    # first 3-4 s; it now starts at the glass's top and still reaches past the base at full charge.
    d = h - (GLASS_TOP + 0.05 - (GLASS_TOP + 0.15) * c)
    lit = max(0.0, min(1.0, (d + 0.06) / 0.12))
    band = max(0.0, 3.0 * (1.0 - abs(d) / 0.07))
    col, _ = D.face_colour(pid, i, j, k, STATE["n"], cc, p)
    lin = (np.clip(col, 0, 255) / 255.0) ** 2.2
    bw = float(lin @ np.array([0.2126, 0.7152, 0.0722]))
    w = max(0.15, min(1.0, 1.0 + (bw - 0.05) / 0.30 * (0.15 - 1.0)))
    e = 5.0 * min(c, 1.4) * w * (lit + band)
    bright = 1.0 - math.exp(-e / 2.2)
    hot = smooth((e - 5.0) / 8.0)
    return (SATURATED * (1 - 0.6 * hot) + LIME * 0.6 * hot) * bright


def l3_light(pid, cc, gw, hv, i, j, k):
    """J's KEEP L3 core swirl (pass 807; J 2026-10-15: "it's not supposed to light the whole thing"): the fill rule's
    light only stays strong in the band round the core, where the strands wind; the rest of the glass stays dark
    (15%), and the gold cracks flash as the light reaches them, then hold a dim gold instead of going green."""
    c, mode = STATE["c"], STATE["mode"]
    if mode == "flash" or c <= 0.0:
        return fill_light(pid, cc, gw, hv, i, j, k)
    x, y, z = cc
    dz = z - pz
    cg = min(c, 1.4)
    band = (2.2 + 1.8 * min(cg, 1.0)) * G * 1.6
    core = math.exp(-abs(dz / band) ** 3)
    base = fill_light(pid, cc, gw, hv, i, j, k)
    if pid == D.VEIN:
        fz = min(1.0, abs(dz) / ((z1b - z0b) / 2))
        front_ = min(cg, 1.0) / 0.85
        if fz > front_:
            return base * 0.15
        run = math.exp(-((front_ - fz) / 0.07) ** 2)
        gold = (np.array([120, 88, 26.0]) * (0.6 + 0.4 * (hv / 255)) + np.array([200, 150, 40.0]) * run) * end_fade(z, cg)
        return np.maximum(gold, base * (0.15 + 0.85 * core))
    # The strands round the heart (still; the swirl frames turn on top), bright in the saturated corps green.
    ang = math.atan2(y, x)
    strand = 3.0 * ((math.sin(3 * ang + 0.55 * dz) + 1) / 2) ** 3
    lit = core * min(1.0, 0.45 + 0.35 * strand) * min(1.0, 0.25 + 0.75 * cg)
    return np.maximum(base * (0.15 + 0.85 * core), SATURATED * lit + LIME * 0.25 * lit * max(0.0, cg - 1.0))


def swirl_light(pid, cc, gw):
    """The spinning ball's strands in the middle band (+-(2.2 + 1.8 c) px; baked at c = 0.75).

    J's KEEP L3 core swirl (pass 807, docs/handoff/2026-10-15-keeps-charge-hits): strand phase 3 angle + 0.55 dz + 2 spin
    (the mod turns the frames at twice the spin), weight ((sin + 1) / 2)^3 x 3: the strands three times as strong."""
    x, y, z = cc
    dz = z - pz
    ang = math.atan2(y, x)
    band = (2.2 + 1.8 * 0.75) * G
    inband = math.exp(-abs(dz / band) ** 3)
    ph = STATE["phase"]
    strand = 3.0 * ((math.sin(3 * ang + 0.55 * dz - ph) + 1) / 2) ** 3
    noise = 0.5 + 0.5 * math.sin(5 * ang - 2.3 * dz + 2 * ph) * math.cos(2 * ang + 1.7 * dz - ph)
    L = inband * (0.25 + gw) * (0.9 * strand + 0.5 * noise * strand)
    return ramp(0.5 + 0.45 * L) * min(1.0, 1.6 * L)


FRONT_Y = float(np.min([xs[j_] for j_ in range(len(xs)) if (part[:, j_, :] > 0).any()]))
# The whole lantern's height, base to handle top, for the fill rule's h.
_zs_on = [zs[k_] for k_ in range(len(zs)) if (part[:, :, k_] > 0).any()]
Z_LO, Z_HI = float(min(_zs_on)) - G / 2, float(max(_zs_on)) + G / 2
GLASS_TOP = (z1b - Z_LO) / (Z_HI - Z_LO)


def glow_painter_for(fn):
    def factory(frm, to):
        def paint(face, w, h):
            n = FACE_N[face]
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    X, Y, Z = _texel(frm, to, face, u, v, w, h)
                    q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2
                    i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                    c = np.array([xs[i], xs[j], zs[k]])
                    pid = int(part[i, j, k])
                    gw = D.glow_weight(pid, i, j, k, c, p, pz) if pid else 0.0
                    hv = ((i * 2654435761) ^ (j * 40503) ^ (k * 2246822519)) & 255
                    STATE["n"] = n
                    col = fn(pid, c, gw, hv, i, j, k)
                    rgb = tuple(int(round(min(255, max(0, v_)))) for v_ in col)
                    row.append(rgb + (min(255, int(max(rgb) * 1.4)),))     # see-through where dark (shader packs)
                rows.append(row)
            return rows
        return paint
    return factory


def save_quantized(img, path):
    """256-colour palette PNG (with alpha) to keep the jar small."""
    q = img.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    q.save(path, optimize=True)


def glass_boxes(mask, name, fn, first_only=False):
    m = Model(name, density=DENSITY)
    for n_, (i, j, k, i2, j2, k2) in enumerate(boxes(mask)):
        x0, x1 = xs[i] - G / 2, xs[i2] + G / 2
        y0, y1 = xs[j] - G / 2, xs[j2] + G / 2
        za, zb = zs[k] - G / 2 - ZSHIFT, zs[k2] + G / 2 - ZSHIFT
        a, b = to_bb(x1, y0, za), to_bb(x0, y1, zb)
        frm = [round(min(a[c], b[c]), 4) for c in range(3)]
        to = [round(max(a[c], b[c]), 4) for c in range(3)]
        m.cube(f"glow_{n_}", frm, to, glow_painter_for(fn)(frm, to), inflate=0.02)
    return m


glowable = np.isin(part, [D.SMOKE, D.RIB, D.PLATE, D.VEIN, D.SOCKET])
glow_model = glass_boxes(glowable, "dark_lantern_glow", l3_light)
TEX = f"{A}/textures/entity/bb"
for old in os.listdir(TEX):
    if old.startswith("dark_lantern_glow_") or old.startswith("dark_lantern_swirl"):
        os.remove(os.path.join(TEX, old))
STATE.update(mode="charge", u=0.0, c=0.0)
glow_model.write()        # the base texture (dark_lantern_glow.png) is the unlit first frame
save_quantized(Image.open(f"{TEX}/dark_lantern_glow.png").convert("RGBA"), f"{TEX}/dark_lantern_glow.png")
for f in range(CHARGE_FRAMES):
    u = f / (CHARGE_FRAMES - 1)
    STATE.update(mode="charge", u=u, c=smooth(u))
    save_quantized(glow_model.texture(), f"{TEX}/dark_lantern_glow_c{f}.png")
STATE.update(mode="climax", u=1.0, c=1.4)
save_quantized(glow_model.texture(), f"{TEX}/dark_lantern_glow_climax.png")
STATE.update(mode="flash", u=1.0, c=1.4)
save_quantized(glow_model.texture(), f"{TEX}/dark_lantern_glow_flash.png")
print("glow model:", len(glow_model.cubes), "boxes,", CHARGE_FRAMES, "charge frames + climax + flash")

band = (np.abs(zs - pz) <= 2.4)[None, None, :]
swirl_model = glass_boxes(glowable & band, "dark_lantern_swirl", lambda pid, c, gw, hv, i, j, k: swirl_light(pid, c, gw))
STATE["phase"] = 0.0
swirl_model.write()
os.remove(f"{TEX}/dark_lantern_swirl.png")
for f in range(SWIRL_FRAMES):
    STATE["phase"] = f / SWIRL_FRAMES * 2 * math.pi           # strands repeat every third of a turn (3 ang)
    save_quantized(swirl_model.texture(), f"{TEX}/dark_lantern_swirl_{f}.png")
print("swirl model:", len(swirl_model.cubes), "boxes,", SWIRL_FRAMES, "frames")

# R4's polished gold: a LabPBR specular map (dark_lantern_s.png), so a shader pack (Complementary)
# reflects the lantern's green in the gold frame. No emissive gold. Red = smoothness, green = 231
# (gold) / 230 (iron) for metals or the reflectance of glass, alpha 255 = no emission.
SPEC = {D.GOLD: (215, 231), D.GOLD_DK: (190, 231), D.EMBLEM: (220, 231), D.VEIN: (170, 231), D.SILVER: (200, 230),
        D.SILVER_DK: (170, 230), D.SMOKE: (225, 10), D.RIB: (225, 10), D.PLATE: (215, 10), D.SOCKET: (200, 10),
        D.HOLE: (40, 4), D.BRONZE_PLUG: (160, 231)}


def spec_painter(frm, to):
    def paint(face, w, h):
        n = FACE_N[face]
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                X, Y, Z = _texel(frm, to, face, u, v, w, h)
                q = np.array([-X, Z, Y + ZSHIFT]) - np.array(n) * G / 2
                i = int(np.floor((q[0] - x0g) / G)); j = int(np.floor((q[1] - x0g) / G)); k = int(np.floor((q[2] - z0g) / G))
                sm, f0 = SPEC.get(int(part[i, j, k]), (100, 10))
                row.append((sm, f0, 0, 255))
            rows.append(row)
        return rows
    return paint


spec = Model("dark_lantern_s", density=DENSITY)
for n_, (i, j, k, i2, j2, k2) in enumerate(boxes(part > 0)):
    x0, x1 = xs[i] - G / 2, xs[i2] + G / 2
    y0, y1 = xs[j] - G / 2, xs[j2] + G / 2
    za, zb = zs[k] - G / 2 - ZSHIFT, zs[k2] + G / 2 - ZSHIFT
    a, b = to_bb(x1, y0, za), to_bb(x0, y1, zb)
    frm = [round(min(a[c], b[c]), 4) for c in range(3)]
    to = [round(max(a[c], b[c]), 4) for c in range(3)]
    spec.cube(f"body_{n_}", frm, to, spec_painter(frm, to))
spec.pack()
spec.texture().save(f"{TEX}/dark_lantern_s.png", optimize=True)
print(f"{count} boxes from {int((part > 0).sum()):,} cubes")
model.write()
