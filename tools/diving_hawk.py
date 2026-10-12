"""Writes the Blue Lantern diving hawk as a rigged Blockbench model plus its texture.

    python tools/diving_hawk.py src/main/resources/assets/lanternring

Unlike the lanterns, the hawk has bones: every part sits in a Blockbench group (body, neck, head,
three-part wings, each primary and tail feather, legs), and DivingHawkModel animates those groups
by name, so the model can be opened and reshaped in Blockbench (File > Open Model) and the flap,
glide, stoop and perch animations still work as long as the group names stay.

Built like the Classic battery (plans/lantern-style.md): the round parts (body, neck, head) are
stacked one-unit slices of a real ellipsoid, and every texel is shaded from the surface it stands
for, lit from above and in front, with no random noise. The detail comes from shape: a hooked
beak sheathed in a blue armour lance, a helm with a crest, slotted primary feathers, a fanned
banded tail, feathered legs with dark talons. Plumage is a red-tailed hawk's: dark brown back,
cream chest with soft barring, a rufous tail with a dark band. Cubes named "glow..." light up
(the armour's trim lines, the lance tip, the Blue Lantern emblem on the helm).

Coordinates are Blockbench's (+Y up, 1 unit = 1 pixel, the beak points north / -Z, feet on y=0).
"""
import base64, io, json, math, os, sys, uuid
from PIL import Image

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
NAME = "diving_hawk"
DENSITY = 2  # texture pixels per model unit
CLEAR = (0, 0, 0, 0)


def clamp(v):
    return max(0, min(255, int(round(v))))


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(clamp(a[i] + (b[i] - a[i]) * k) for i in range(3))


def norm(v):
    m = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / m for c in v)


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


L = norm((0.25, 0.8, -0.55))  # light from above, in front and a little to the side
H = norm((0.25, 0.8, -1.55))  # half-way between the light and a viewer in front


def matte(c, n):
    """Feathers: soft light from above, dark underneath, no shine."""
    d = max(0.0, dot(n, L))
    return mix(tuple(x * 0.42 for x in c), c, 0.25 + 0.75 * d)


BLUE_METAL = ((8, 20, 64), (34, 86, 196), (214, 236, 255), (90, 150, 240))


def metal(n, pal=BLUE_METAL):
    """Glossy Blue Lantern armour: deep navy underneath, a bright glint toward the light."""
    dark, base, hi, rim = pal
    d = max(0.0, dot(n, L))
    c = mix(dark, base, 0.2 + 0.8 * d)
    spec = max(0.0, dot(n, H)) ** 20
    c = mix(c, hi, spec * 0.95)
    return mix(c, rim, 0.3 * max(0.0, -n[1]) ** 2)


# ---- where a texel is -------------------------------------------------------------------------

FACE_N = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


def texel(frm, to, face, u, v, w, h):
    """The model-space point a texel stands for, following the way ModelPart lays box UV onto a
    face once the model is turned about Z into entity space (see BbRig)."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    a, b = (u + 0.5) / w, (v + 0.5) / h
    return {
        "north": (x1 - a * (x1 - x0), y1 - b * (y1 - y0), z0),
        "south": (x0 + a * (x1 - x0), y1 - b * (y1 - y0), z1),
        "east": (x1, y1 - b * (y1 - y0), z1 - a * (z1 - z0)),
        "west": (x0, y1 - b * (y1 - y0), z0 + a * (z1 - z0)),
        "up": (x1 - a * (x1 - x0), y1, z1 - b * (z1 - z0)),
        "down": (x1 - a * (x1 - x0), y0, z1 - b * (z1 - z0)),
    }[face]


def painter(fn, surface=None):
    """A face painter calling fn(p, n, face, cube) per texel; surface(p) gives the real normal of a
    round part (otherwise the flat face's own)."""
    def paint(c, face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = texel(c["frm"], c["to"], face, u, v, w, h)
                n = surface(p) if surface else FACE_N[face]
                col = fn(p, n, face, c)
                row.append(col if len(col) == 4 else col + (255,))
            rows.append(row)
        return rows
    return paint


def ellipsoid(centre, radii):
    return lambda p: norm(tuple((p[i] - centre[i]) / (radii[i] ** 2) for i in range(3)))


def rod(axis, centre, rx, ry):
    """A round bar along an axis, shaded as if its section were an ellipse rx by ry."""
    i = "xyz".index(axis)
    j, k = [m for m in range(3) if m != i]

    def n(p):
        v = [0.0, 0.0, 0.0]
        v[j] = (p[j] - centre[j]) / (rx * rx)
        v[k] = (p[k] - centre[k]) / (ry * ry)
        return norm(v)
    return n


# ---- colours ----------------------------------------------------------------------------------

BACK = (78, 52, 34)          # dark brown back and wing tops
BACK_EDGE = (150, 108, 66)   # the pale fringe on each feather
CREAM = (236, 222, 192)      # chest and wing linings
BAR = (150, 104, 66)         # soft barring on the chest and under the wings
TAWNY = (176, 120, 70)       # flanks and the side of the neck
RUFOUS = (186, 84, 40)       # the tail
TAIL_BAND = (40, 24, 18)
FLIGHT = (60, 42, 32)        # flight feathers
FLIGHT_TIP = (24, 18, 16)
YELLOW = (236, 190, 52)      # cere and feet
TALON = (22, 20, 22)
BEAK = (50, 54, 66)
LEATHER = (66, 40, 28)


def plumage(p, n, face, c):
    """Body and neck: dark back, tawny flanks, cream chest and belly with soft bars across it."""
    up = n[1]
    back = smooth(-0.1, 0.45, up)
    col = mix(CREAM, TAWNY, smooth(-0.6, 0.2, up) * 0.8)
    col = mix(col, BACK, back)
    if up < 0.2 and p[2] > -12:
        # Bars across the belly, fading out toward the flanks and the back.
        bar = 0.5 + 0.5 * math.cos(p[2] * 1.15 + abs(p[0]) * 0.25)
        col = mix(col, BAR, smooth(0.6, 1.0, bar) * 0.55 * (1 - smooth(-0.2, 0.2, up)))
    return matte(col, n)


def head_feathers(p, n, face, c):
    """Head: dark crown, pale throat, a dark streak back from the eye (the malar stripe)."""
    col = mix(CREAM, BACK, smooth(-0.3, 0.4, n[1]))
    if abs(n[0]) > 0.6 and -2.0 < p[1] - 21.0 < 0.6 and p[2] > -21:
        col = mix(col, BACK, 0.75)
    return matte(col, n)


def feather(kind):
    """A flight feather, covert or tail feather. Each cube's long axis is its length; the feather
    darkens toward its tip, with a pale fringe along its edge and bars across it."""
    def fn(p, n, face, c):
        frm, to = c["frm"], c["to"]
        size = [to[i] - frm[i] for i in range(3)]
        ax = 0 if kind in ("primary", "covert") else 2
        if kind == "secondary":
            ax = 2
        t = (p[ax] - frm[ax]) / max(size[ax], 1e-6)
        if kind == "primary" and frm[0] < 0:
            t = 1 - t  # the mirrored wing runs the other way
        across = [i for i in (0, 2) if i != ax][0]
        s = (p[across] - frm[across]) / max(size[across], 1e-6)
        edge = min(s, 1 - s)
        under = face == "down"
        if kind == "tail":
            col = RUFOUS if not under else mix(RUFOUS, CREAM, 0.55)
            if 0.74 < t < 0.88:
                col = TAIL_BAND
            elif t >= 0.95:
                col = CREAM
        elif kind == "covert":
            col = BACK if not under else CREAM
            col = mix(col, BACK_EDGE if not under else BAR, 0.6 * smooth(0.2, 0.0, edge) if not under else 0.0)
        else:
            col = FLIGHT if not under else (214, 204, 186)
            bars = 0.5 + 0.5 * math.cos(t * (18 if kind == "primary" else 14))
            col = mix(col, FLIGHT_TIP if not under else BAR, smooth(0.55, 1.0, bars) * 0.5)
            col = mix(col, FLIGHT_TIP, smooth(0.7, 1.0, t) * (0.85 if not under else 0.6))
            if not under:
                col = mix(col, BACK_EDGE, 0.45 * smooth(0.18, 0.0, edge))
        return matte(col, n)
    return fn


def flat(col):
    return lambda p, n, face, c: matte(col, n)


def shiny(col):
    pal = (tuple(x * 0.25 for x in col), col, (250, 245, 230), mix(col, (255, 255, 255), 0.3))
    return lambda p, n, face, c: metal(n, pal)


def armour(p, n, face, c):
    return metal(n)


def glow(p, n, face, c):
    """Bright, as the Blockbench glow note says: a white-hot middle fading to Blue Lantern blue."""
    frm, to = c["frm"], c["to"]
    centre = [(frm[i] + to[i]) / 2 for i in range(3)]
    half = [max((to[i] - frm[i]) / 2, 1e-6) for i in range(3)]
    d = max(abs(p[i] - centre[i]) / half[i] for i in range(3) if FACE_N[face][i] == 0)
    return mix((150, 215, 255), (90, 160, 255), d)


def eye(p, n, face, c):
    if face not in ("east", "west"):
        return matte((40, 30, 24), n)
    cy, cz = 22.5, -19.5
    r = math.hypot(p[1] - cy, p[2] - cz)
    if r < 0.45:
        return (10, 8, 8)
    if r < 0.95:
        return (230, 160, 40)
    return (40, 30, 24)


# ---- the model --------------------------------------------------------------------------------

class Bone:
    def __init__(self, name, origin, rotation=(0, 0, 0)):
        self.name, self.origin, self.rotation = name, list(origin), list(rotation)
        self.children = []  # cubes and bones, in order


cubes = []
root_bones = []
stack = []


def bone(name, origin, rotation=(0, 0, 0)):
    b = Bone(name, origin, rotation)
    (stack[-1].children if stack else root_bones).append(b)
    return b


class into:
    def __init__(self, b):
        self.b = b

    def __enter__(self):
        stack.append(self.b)
        return self.b

    def __exit__(self, *a):
        stack.pop()


def cube(name, frm, to, paint, inflate=0.0, rotation=None, origin=None):
    size = [to[i] - frm[i] for i in range(3)]
    assert all(abs(s - round(s)) < 1e-6 and s >= 0 for s in size), (name, size)
    c = dict(name=name, frm=list(frm), to=list(to), size=[int(round(s)) for s in size], paint=paint,
             inflate=inflate, rotation=rotation, origin=origin)
    cubes.append(c)
    stack[-1].children.append(c)
    return c


def half(x):
    return round(x * 2) / 2


def loaf(name, centre, radii, z0, z1, step, paint_fn, ycentre=None, scale_y=None):
    """A round part along z: one-unit (or ``step``) slices of an ellipsoid, each a wide box and a
    tall box crossed, so the section reads round from every side."""
    surf = ellipsoid(centre, radii)
    z = z0
    i = 0
    while z < z1 - 1e-6:
        zc = z + step / 2
        k = max(0.0, 1 - ((zc - centre[2]) / radii[2]) ** 2)
        s = math.sqrt(k)
        hw, hh = half(radii[0] * s + 0.2), half(radii[1] * s + 0.2)
        yc = centre[1] if ycentre is None else ycentre(zc)
        if hw >= 0.5 and hh >= 0.5:
            iw, ih = half(hw * 0.72), half(hh * 0.72)
            p = painter(paint_fn, surf)
            cube(f"{name}_{i}a", (-hw, yc - ih, z), (hw, yc + ih, z + step), p)
            if ih < hh and iw >= 0.5:
                cube(f"{name}_{i}b", (-iw, yc - hh, z), (iw, yc + hh, z + step), p)
        z += step
        i += 1


BODY_C = (0, 16, 0)
BODY_R = (7, 6.5, 14)

body = bone("body", (0, 16, 0))
with into(body):
    loaf("torso", BODY_C, BODY_R, -12, 13, 1, plumage)
    # Breastplate: blue armour over the front and underside of the chest, its edge lit blue.
    surf = ellipsoid(BODY_C, (7.6, 7.1, 14.6))
    for i, z in enumerate(range(-12, -3)):
        zc = z + 0.5
        s = math.sqrt(max(0.0, 1 - (zc / 14.6) ** 2))
        hw, hh = half(7.6 * s), round(7.1 * s)
        cube(f"plate_{i}", (-hw + 1, 16 - hh, z), (hw - 1, 16 - 1, z + 1), painter(armour, surf))
    cube("glow_plate_edge", (-5.5, 14.4, -9.5), (5.5, 15.4, -8.5), painter(glow))
    cube("glow_plate_emblem", (-1.5, 9.6, -10), (1.5, 11.6, -7), painter(glow))
    # Saddle on the back, between the wings.
    cube("saddle", (-4, 21.5, -4), (4, 23.5, 4), painter(flat(LEATHER), rod("z", (0, 21.5, 0), 4.5, 2.5)))
    cube("saddle_pommel", (-1.5, 23.5, -4), (1.5, 25.5, -2), painter(flat(LEATHER)))
    cube("saddle_trim", (-4.5, 21, 3.5), (4.5, 23, 4.5), painter(armour))
    cube("glow_saddle", (-4, 22.6, 3.6), (4, 23.6, 4.6), painter(glow))
    cube("rump", (-3.5, 16, 10), (3.5, 20, 15), painter(plumage, ellipsoid((0, 17.5, 9), (5, 4, 7))))

    neck = bone("neck", (0, 19, -10))
    with into(neck):
        loaf("neck", (0, 19.5, -12), (4.6, 4.8, 4), -15, -9, 1, plumage)
        head = bone("head", (0, 21, -15))
        with into(head):
            HC, HR = (0, 22, -18), (4, 4, 4.5)
            loaf("skull", HC, HR, -22, -13.5, 1, head_feathers)
            cube("eye_l", (3.1, 21.5, -20.5), (4.1, 23.5, -18.5), painter(eye))
            cube("eye_r", (-4.1, 21.5, -20.5), (-3.1, 23.5, -18.5), painter(eye))
            # The stern raptor brow over each eye.
            cube("brow_l", (1.5, 23.4, -21.5), (4.5, 24.4, -18.5), painter(flat(BACK)))
            cube("brow_r", (-4.5, 23.4, -21.5), (-1.5, 24.4, -18.5), painter(flat(BACK)))
            cube("cere", (-2, 21, -23), (2, 23, -21), painter(flat(YELLOW), rod("z", (0, 22, 0), 2, 1)))
            cube("beak_lower", (-1, 19.5, -25), (1, 20.5, -22), painter(flat(BEAK)))
            cube("beak_hook", (-1, 18.5, -27), (1, 20.5, -25), painter(shiny(BEAK)))
            # The armour: a blue sheath over the upper beak drawn out into a stabbing lance, a
            # helm with a crest and cheek guards, trimmed with glowing lines.
            cube("sheath", (-2, 20.5, -27), (2, 24.5, -21), painter(armour, rod("z", (0, 21.5, 0), 2.6, 3.2)))
            cube("lance", (-1.5, 20.5, -31), (1.5, 23.5, -27), painter(armour, rod("z", (0, 22, 0), 1.8, 1.8)))
            cube("lance_mid", (-1, 21, -34), (1, 23, -31), painter(armour, rod("z", (0, 22, 0), 1.2, 1.2)))
            cube("glow_lance_tip", (-0.5, 21.5, -37), (0.5, 22.5, -34), painter(glow))
            cube("glow_ridge", (-0.5, 24, -27), (0.5, 25, -21), painter(glow))
            cube("helm", (-4.5, 24, -21), (4.5, 27, -14), painter(armour, ellipsoid((0, 23, -17.5), (4.8, 4, 5))))
            cube("helm_back", (-4, 21, -15), (4, 25, -13), painter(armour, ellipsoid((0, 22, -17), (4.6, 4, 5))))
            cube("crest", (-0.5, 27, -20), (0.5, 29, -12), painter(armour))
            cube("glow_crest", (-0.5, 28.5, -19), (0.5, 29.5, -13), painter(glow))
            cube("glow_emblem", (-1, 24.5, -21.5), (1, 26.5, -20.5), painter(glow))
            cube("cheek_l", (3.5, 19.5, -21), (4.5, 21.5, -16), painter(armour))
            cube("cheek_r", (-4.5, 19.5, -21), (-3.5, 21.5, -16), painter(armour))

    # Wings, outstretched for gliding: arm, forearm and hand, each with its own coverts and flight
    # feathers. The feathers on the trailing edge alternate in length so the edge is serrated.
    def wing(side):
        sx = 1 if side == "left" else -1

        def X(a, b):
            return (min(sx * a, sx * b), max(sx * a, sx * b))

        def box(name, x0, x1, y0, y1, z0, z1, paint):
            xa, xb = X(x0, x1)
            cube(name, (xa, y0, z0), (xb, y1, z1), paint)

        arm = bone(f"wing_{side}", (sx * 5.5, 20, -6))
        with into(arm):
            box(f"arm_bone_{side}", 5, 17, 19.5, 22.5, -9, -6, painter(feather("covert"), rod("x", (0, 21, -7.5), 1.6, 1.6)))
            box(f"arm_coverts_{side}", 5, 17, 20, 21, -6, 0, painter(feather("covert")))
            for i, x in enumerate((5, 8, 11, 14)):
                box(f"secondary_{side}_{i}", x, x + 3, 20, 21, 0, 8 + (i % 2), painter(feather("secondary")))
            # Armoured shoulder.
            box(f"pauldron_{side}", 4, 11, 21, 23, -10, -5, painter(armour, ellipsoid((sx * 7.5, 20, -7.5), (5, 3.5, 3.5))))
            box(f"glow_pauldron_{side}", 4.5, 10.5, 22.6, 23.6, -5.6, -4.6, painter(glow))
            mid = bone(f"wing_{side}_mid", (sx * 17, 20.5, -7))
            with into(mid):
                box(f"forearm_{side}", 17, 29, 19.5, 21.5, -9, -6, painter(feather("covert"), rod("x", (0, 20.75, -7.5), 1.3, 1.5)))
                box(f"forearm_coverts_{side}", 17, 29, 20, 21, -6, 0, painter(feather("covert")))
                for i, x in enumerate((17, 20, 23, 26)):
                    box(f"secondary_{side}_{i + 4}", x, x + 3, 20, 21, 0, 9 - (i % 2) - i * 0.0, painter(feather("secondary")))
                tip = bone(f"wing_{side}_tip", (sx * 29, 20.5, -7))
                with into(tip):
                    box(f"hand_{side}", 29, 35, 19.5, 21.5, -8.5, -1.5, painter(feather("covert"), rod("x", (0, 20.5, -6), 1.2, 1.2)))
                    # Five slotted primaries fanned from the hand, longest in the middle.
                    for i, (spread, length, z) in enumerate(((8, 13, -8), (-2, 16, -6.5), (-12, 17, -5), (-22, 16, -3.5), (-32, 14, -2))):
                        f = bone(f"primary_{side}_{i}", (sx * 34, 20.5, z + 1), (0, sx * spread, 0))
                        with into(f):
                            box(f"primary_{side}_{i}", 34, 34 + length, 20 - i * 0.05, 21 - i * 0.05, z, z + 2 + (i == 2),
                                painter(feather("primary")))

    wing("left")
    wing("right")

    tail = bone("tail", (0, 17.5, 13))
    with into(tail):
        cube("tail_coverts", (-3, 16.5, 12), (3, 18.5, 18), painter(feather("covert"), ellipsoid((0, 17.5, 13), (3.5, 2, 6))))
        for i, spread in enumerate((-26, -13, 0, 13, 26)):
            f = bone(f"tail_{i}", (0, 17.5, 14), (0, spread, 0))
            with into(f):
                y = 17 - abs(i - 2) * 0.1
                cube(f"tail_{i}", (-1.5, y, 14), (1.5, y + 1, 27), painter(feather("tail")))

    for side, sx in (("left", 1), ("right", -1)):
        leg = bone(f"leg_{side}", (sx * 3, 11.5, 2))
        with into(leg):
            def bx(name, x0, x1, *rest, paint):
                cube(name, (min(sx * x0, sx * x1), rest[0], rest[2]), (max(sx * x0, sx * x1), rest[1], rest[3]), paint)
            bx(f"trouser_{side}", 1.5, 4.5, 6, 12, 0, 4, paint=painter(plumage, rod("y", (sx * 3, 0, 2), 1.8, 2.2)))
            bx(f"shin_{side}", 2.5, 3.5, 1, 6, 1.5, 2.5, paint=painter(flat(YELLOW), rod("y", (sx * 3, 0, 2), 0.6, 0.6)))
            bx(f"toe_mid_{side}", 2.5, 3.5, 0, 1, -1.5, 2.5, paint=painter(flat(YELLOW)))
            bx(f"toe_in_{side}", 1.5, 2.5, 0, 1, -0.5, 2.5, paint=painter(flat(YELLOW)))
            bx(f"toe_out_{side}", 3.5, 4.5, 0, 1, -0.5, 2.5, paint=painter(flat(YELLOW)))
            bx(f"toe_back_{side}", 2.5, 3.5, 0, 1, 2.5, 4.5, paint=painter(flat(YELLOW)))
            bx(f"talon_mid_{side}", 2.5, 3.5, -1, 1, -2.5, -1.5, paint=painter(shiny(TALON)))
            bx(f"talon_in_{side}", 1.5, 2.5, -1, 1, -1.5, -0.5, paint=painter(shiny(TALON)))
            bx(f"talon_out_{side}", 3.5, 4.5, -1, 1, -1.5, -0.5, paint=painter(shiny(TALON)))
            bx(f"talon_back_{side}", 2.5, 3.5, -1, 1, 4.5, 5.5, paint=painter(shiny(TALON)))


# ---- texture and file -------------------------------------------------------------------------

def pack():
    for side in (64, 128, 256, 512):
        x = y = shelf = 0
        ok = True
        for c in sorted(cubes, key=lambda c: -(c["size"][2] + c["size"][1])):
            w, h, d = c["size"]
            nw, nh = 2 * (w + d), d + h
            if x + nw > side:
                x, y, shelf = 0, y + shelf, 0
            if nw > side or y + nh > side:
                ok = False
                break
            c["uv"] = [x, y]
            x += nw
            shelf = max(shelf, nh)
        if ok:
            return side
    raise ValueError("atlas too big")


def faces(c):
    u, v = c["uv"]
    w, h, d = c["size"]
    return {
        "east": [u, v + d, u + d, v + d + h],
        "north": [u + d, v + d, u + d + w, v + d + h],
        "west": [u + d + w, v + d, u + 2 * d + w, v + d + h],
        "south": [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h],
        "up": [u + d, v, u + d + w, v + d],
        "down": [u + d + w, v, u + d + 2 * w, v + d],
    }


def ident(s):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + "/" + s))


def outline(b):
    out = {"name": b.name, "origin": b.origin, "rotation": b.rotation, "color": 0, "uuid": ident("bone/" + b.name),
           "export": True, "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0,
           "children": []}
    for ch in b.children:
        out["children"].append(outline(ch) if isinstance(ch, Bone) else ident(ch["name"]))
    return out


def main():
    side = pack()
    k = DENSITY
    im = Image.new("RGBA", (side * k, side * k), CLEAR)
    px = im.load()
    for c in cubes:
        for face, (u0, v0, u1, v1) in faces(c).items():
            w, h = (u1 - u0) * k, (v1 - v0) * k
            if w <= 0 or h <= 0:
                continue
            rows = c["paint"](c, face, w, h)
            for y in range(h):
                for x in range(w):
                    px[u0 * k + x, v0 * k + y] = rows[y][x]
    os.makedirs(f"{A}/textures/entity/bb", exist_ok=True)
    os.makedirs(f"{A}/bbmodel", exist_ok=True)
    im.save(f"{A}/textures/entity/bb/{NAME}.png")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    elements = []
    for c in cubes:
        centre = c["origin"] or [(c["frm"][i] + c["to"][i]) / 2 for i in range(3)]
        extra = {"rotation": c["rotation"]} if c["rotation"] else {}
        elements.append({**extra,
            "name": c["name"], "box_uv": True, "rescale": False, "locked": False, "render_order": "default",
            "allow_mirror_modeling": True, "from": c["frm"], "to": c["to"], "autouv": 0, "color": 0,
            "inflate": c["inflate"], "origin": centre, "uv_offset": c["uv"],
            "faces": {f: {"uv": r, "texture": 0} for f, r in faces(c).items()},
            "type": "cube", "uuid": ident(c["name"]),
        })
    model = {
        "meta": {"format_version": "4.10", "model_format": "modded_entity", "box_uv": True},
        "name": NAME, "model_identifier": NAME, "modded_entity_entity_class": "", "modded_entity_version": "Fabric 1.17+",
        "modded_entity_flip_y": True, "visible_box": [1.4, 1.4, 0], "variable_placeholders": "",
        "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": side, "height": side},
        "elements": elements,
        "outliner": [outline(b) for b in root_bones],
        "textures": [{
            "path": "", "name": f"{NAME}.png", "folder": "entity/bb", "namespace": "lanternring", "id": "0", "group": "",
            "width": side * k, "height": side * k, "uv_width": side, "uv_height": side, "particle": False,
            "use_as_default": True, "layers_enabled": False, "sync_to_project": "", "render_mode": "default",
            "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
            "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": ident("texture"),
            "relative_path": f"../textures/entity/bb/{NAME}.png",
            "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        }],
    }
    with open(f"{A}/bbmodel/{NAME}.bbmodel", "w") as f:
        json.dump(model, f, indent=1)
    print(f"{NAME}: {len(cubes)} cubes, {side * k}x{side * k} texture")


main()
