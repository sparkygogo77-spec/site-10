"""Writes the Red Lantern's Rage Bull as a rigged Blockbench model plus its texture.

    python tools/rage_bull.py src/main/resources/assets/lanternring

The bull is the Red ring's biggest Blast (RageBull): drawn about 8.5 times this size it fills the
20-block round tunnel it bulldozes. Its bones are Blockbench groups (body, head, the four legs,
tail), and RageBullModel animates them by name (a heavy trot, the head low and tossing, the tail
swinging), so it can be reshaped in Blockbench as long as the group names stay.

The shape is a fighting bull built for charging: a deep chest and a hump of muscle over the
shoulders, a lean waist, thick-thighed legs on dark hooves, the head carried low with a broad
muzzle and dewlap, and big horns that sweep out from the poll and curve forward and up (kept within
the tunnel's width). The texture is a real bull's colouring shaded from the surface each texel
stands for (lit from above and in front): the game turns it into red hard light by its brightness
(ConstructSkins), so pale horns and muzzle come out bright and the dark coat deep red. Cubes named
"glow..." (eyes and nostrils) burn full-bright.

Coordinates are Blockbench's (+Y up, 1 unit = 1 pixel, the muzzle points north / -Z, hooves on y=0).
"""
import base64, io, json, math, os, sys, uuid
from PIL import Image

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
NAME = "rage_bull"
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


L = norm((0.3, 0.8, -0.5))
H = norm((0.3, 0.8, -1.5))


def matte(c, n):
    d = max(0.0, dot(n, L))
    return mix(tuple(x * 0.4 for x in c), c, 0.22 + 0.78 * d)


def sheen(c, n, power=14, amount=0.35):
    """The coat's short-haired gloss over the muscles."""
    col = matte(c, n)
    return mix(col, (255, 240, 225), amount * max(0.0, dot(n, H)) ** power)


FACE_N = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


def texel(frm, to, face, u, v, w, h):
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
    def paint(c, face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = texel(c["frm"], c["to"], face, u, v, w, h)
                n = surface(p) if surface else FACE_N[face]
                if dot(n, FACE_N[face]) < 0.15:
                    # A round part's surface normal never faces away from the face it is drawn on.
                    n = norm(tuple(n[i] + FACE_N[face][i] for i in range(3)))
                col = fn(p, n, face, c)
                row.append(col if len(col) == 4 else col + (255,))
            rows.append(row)
        return rows
    return paint


def ellipsoid(centre, radii):
    return lambda p: norm(tuple((p[i] - centre[i]) / (radii[i] ** 2) for i in range(3)))


def rod(axis, centre, rx, ry):
    i = "xyz".index(axis)
    j, k = [m for m in range(3) if m != i]

    def n(p):
        v = [0.0, 0.0, 0.0]
        v[j] = (p[j] - centre[j]) / (rx * rx)
        v[k] = (p[k] - centre[k]) / (ry * ry)
        return norm(v)
    return n


# ---- colours ----------------------------------------------------------------------------------

COAT = (92, 44, 30)        # deep bay coat
COAT_HI = (150, 82, 52)    # the lit crest of the hump and the shoulders
BELLY = (58, 30, 22)
MUZZLE = (176, 136, 112)
HORN = (238, 226, 198)
HORN_TIP = (70, 58, 46)
HOOF = (40, 34, 32)
TUFT = (40, 24, 18)


def coat(p, n, face, c):
    """Darker underneath, lit along the topline, the shoulder muscle catching the light."""
    col = mix(BELLY, COAT, smooth(-0.7, 0.1, n[1]))
    col = mix(col, COAT_HI, 0.55 * smooth(0.45, 0.95, n[1]) * smooth(4, -10, p[2]))
    return sheen(col, n)


def legs(p, n, face, c):
    """Coat down to the knee, then darker socks down to the hoof."""
    col = mix(TUFT, COAT, smooth(4, 9, p[1]))
    return sheen(col, n, amount=0.2)


def head(p, n, face, c):
    """Dark head, the muzzle pale and soft toward the nose."""
    col = mix(COAT, MUZZLE, smooth(-21, -24.5, p[2]))
    if p[1] > 25.5:
        col = mix(col, TUFT, 0.6)  # the curly poll between the horns
    return sheen(col, n, amount=0.25)


def flat(col):
    return lambda p, n, face, c: matte(col, n)


def horn(t0, t1):
    """Ivory at the base darkening to a black tip; t0..t1 is how far along the horn this piece is."""
    def fn(p, n, face, c):
        frm, to = c["frm"], c["to"]
        t = t0 + (t1 - t0) * (p[0] - frm[0]) / max(to[0] - frm[0], 1e-6)
        col = mix(HORN, HORN_TIP, smooth(0.55, 1.0, t))
        # Growth rings near the base.
        if t < 0.35:
            col = mix(col, (200, 186, 156), 0.4 * (0.5 + 0.5 * math.cos(t * 60)))
        return sheen(col, n, power=24, amount=0.5)
    return fn


def glow(p, n, face, c):
    frm, to = c["frm"], c["to"]
    centre = [(frm[i] + to[i]) / 2 for i in range(3)]
    half = [max((to[i] - frm[i]) / 2, 1e-6) for i in range(3)]
    d = max(abs(p[i] - centre[i]) / half[i] for i in range(3) if FACE_N[face][i] == 0)
    return mix((255, 250, 235), (255, 200, 170), d)


# ---- the model --------------------------------------------------------------------------------

class Bone:
    def __init__(self, name, origin, rotation=(0, 0, 0)):
        self.name, self.origin, self.rotation = name, list(origin), list(rotation)
        self.children = []


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


def cube(name, frm, to, paint, rotation=None, origin=None):
    size = [to[i] - frm[i] for i in range(3)]
    assert all(abs(s - round(s)) < 1e-6 and s >= 0 for s in size), (name, size)
    c = dict(name=name, frm=list(frm), to=list(to), size=[int(round(s)) for s in size], paint=paint,
             rotation=rotation, origin=origin)
    cubes.append(c)
    stack[-1].children.append(c)
    return c


def box(name, x0, x1, y0, y1, z0, z1, fn, surface=None):
    return cube(name, (x0, y0, z0), (x1, y1, z1), painter(fn, surface))


def rot_y(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) + v[2] * math.sin(a), v[1], -v[0] * math.sin(a) + v[2] * math.cos(a))


def rot_z(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a), v[2])


BODY_C = (0, 19, 0)
BODY_R = (8, 8, 14)

body = bone("body", (0, 17, 0))
with into(body):
    surf = ellipsoid(BODY_C, BODY_R)
    # Barrel and ribs, slung low, narrowing to the loin.
    box("barrel", -7, 7, 11, 25, -9, 11, coat, surf)
    box("barrel_side", -7.5, 7.5, 13, 23, -8, 9, coat, surf)
    # A deep chest that reaches down between the forelegs, and the hump of muscle over the withers.
    box("chest", -8, 8, 10, 26, -15, -6, coat, ellipsoid((0, 19, -8), (9, 9, 8)))
    box("brisket", -5, 5, 8, 12, -15, -8, coat, ellipsoid((0, 12, -11), (6, 5, 5)))
    box("hump", -6, 6, 26, 30, -13, -3, coat, ellipsoid((0, 25, -8), (7, 5, 6)))
    box("hump_top", -4, 4, 30, 31, -11, -5, coat, ellipsoid((0, 26, -8), (5, 5, 4)))
    # The quarters: round over the hips, the tail set high.
    box("quarters", -7, 7, 12, 24, 10, 15, coat, ellipsoid((0, 18, 10), (8, 7, 6)))
    box("hips", -6, 6, 24, 25, 6, 14, coat, ellipsoid((0, 19, 10), (7, 6, 6)))
    # The neck, thick and low, running into the head.
    box("neck", -6, 6, 15, 26, -19, -14, coat, ellipsoid((0, 20, -15), (7, 7, 6)))
    box("dewlap", -2, 2, 11, 16, -19, -14, coat, rod("z", (0, 14, 0), 2.5, 3))

    hd = bone("head", (0, 21, -19))
    with into(hd):
        HC = (0, 20, -22)
        hs = ellipsoid(HC, (5.5, 6, 5))
        # A broad skull carried low, a deep face and a wide square muzzle.
        box("skull", -5, 5, 18, 27, -24, -18, head, hs)
        box("brow", -5.5, 5.5, 22, 26, -24, -20, head, hs)
        box("face", -4, 4, 13, 18, -25, -19, head, ellipsoid((0, 17, -21), (5, 6, 5)))
        box("muzzle", -4.5, 4.5, 11, 16, -28, -23, head, ellipsoid((0, 14, -24), (5, 4, 5)))
        box("jaw", -3, 3, 10, 12, -27, -21, flat(MUZZLE))
        box("poll", -3, 3, 26, 28, -23, -19, head, hs)
        # Ears flicked back under the horns.
        box("ear_l", 5, 8, 22, 24, -20, -18, head)
        box("ear_r", -8, -5, 22, 24, -20, -18, head)
        # Burning eyes and nostrils.
        box("glow_eye_l", 5, 6, 21, 23, -23, -21, glow)
        box("glow_eye_r", -6, -5, 21, 23, -23, -21, glow)
        box("glow_nostril_l", 1, 3, 13, 15, -29, -28, glow)
        box("glow_nostril_r", -3, -1, 13, 15, -29, -28, glow)

        # The horns: out from the poll, then curving forward and up to dark points. Each piece is
        # a box along its own +X turned about its base, the next starting where it ends.
        for side, sx in (("l", 1), ("r", -1)):
            base = (sx * 4.5, 24.5, -21.5)
            pieces = [(6, 4, 4, 6), (5, 3, 16, 24), (4, 3, 28, 42), (4, 2, 38, 58), (3, 1, 44, 72)]
            p = base
            total = sum(pc[0] for pc in pieces)
            done = 0
            for i, (length, thick, yaw, up) in enumerate(pieces):
                h = thick / 2
                t0, t1 = done / total, (done + length) / total
                if sx > 0:
                    frm, to = (p[0], p[1] - h, p[2] - h), (p[0] + length, p[1] + h, p[2] + h)
                    rot = [0, yaw, up]
                else:
                    frm, to = (p[0] - length, p[1] - h, p[2] - h), (p[0], p[1] + h, p[2] + h)
                    rot = [0, -yaw, -up]
                fn = horn(t0, t1) if sx > 0 else horn(t1, t0)
                cube(f"horn_{side}_{i}", frm, to, painter(fn, rod("x", (0, p[1], p[2]), h + 0.3, h + 0.3)), rotation=rot, origin=list(p))
                d = rot_z(rot_y((sx * length, 0, 0), rot[1]), rot[2])
                p = (p[0] + d[0] * 0.85, p[1] + d[1] * 0.85, p[2] + d[2] * 0.85)
                done += length

    tail = bone("tail", (0, 24, 15))
    with into(tail):
        box("tail_root", -1, 1, 22, 25, 14, 16, coat)
        box("tail", -0.5, 0.5, 9, 22, 15, 16, coat)
        box("tail_tuft", -1.5, 1.5, 5, 10, 14, 17, flat(TUFT), rod("y", (0, 0, 15.5), 1.8, 1.8))


def leg(name, x, z, front):
    b = bone(name, (x, 18, z))
    with into(b):
        s = 1 if x > 0 else -1
        ax = (x, 0, z)
        if front:
            box(f"{name}_arm", x - 3, x + 3, 10, 20, z - 3, z + 3, legs, rod("y", ax, 3.5, 3.5))
        else:
            box(f"{name}_thigh", x - 3.5, x + 3.5, 11, 21, z - 3.5, z + 3.5, legs, rod("y", ax, 4, 4.5))
        box(f"{name}_shin", x - 2, x + 2, 3, 10, z - 2, z + 2, legs, rod("y", ax, 2.4, 2.4))
        box(f"{name}_fetlock", x - 2.5, x + 2.5, 2, 4, z - 2.5, z + 2.5, legs, rod("y", ax, 2.8, 2.8))
        box(f"{name}_hoof", x - 2.5, x + 2.5, 0, 2, z - 3, z + 2, flat(HOOF))
    return b

leg("leg_front_left", 4.5, -9, True)
leg("leg_front_right", -4.5, -9, True)
leg("leg_back_left", 4.5, 10, False)
leg("leg_back_right", -4.5, 10, False)

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
            "inflate": 0.0, "origin": centre, "uv_offset": c["uv"],
            "faces": {f: {"uv": r, "texture": 0} for f, r in faces(c).items()},
            "type": "cube", "uuid": ident(c["name"]),
        })
    model = {
        "meta": {"format_version": "4.10", "model_format": "modded_entity", "box_uv": True},
        "name": NAME, "model_identifier": NAME, "modded_entity_entity_class": "", "modded_entity_version": "Fabric 1.17+",
        "modded_entity_flip_y": True, "visible_box": [2, 2, 0], "variable_placeholders": "",
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
