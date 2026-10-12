"""Writes the lantern and ring as Blockbench models (.bbmodel) plus their texture atlases.

    python tools/blockbench_models.py src/main/resources/assets/lanternring

Open the .bbmodel files in Blockbench (File > Open Model) to edit them; the mod reads them
straight from assets/lanternring/bbmodel/ at startup, so an edited file can simply replace the
generated one. Conventions the mod relies on:

- "Modded Entity" format with box UV, 1 unit = 1 pixel. Coordinates are exactly as Blockbench
  shows them (+Y up, the lantern's front faces north / -Z).
- Cubes whose name starts with "glow" are drawn full-bright (they light up in the dark), using
  the same texture. Everything else is drawn as normal lit, cut-out pixels.
- The texture lives next to the model under textures/entity/bb/<model>.png.
"""
import base64, io, json, math, os, random, sys, uuid
from PIL import Image

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
random.seed(7)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, k):
    return tuple(clamp(x * k) for x in c[:3]) + (c[3] if len(c) > 3 else 255,)


# ---- painters: (face, w, h) -> list of rows of RGBA -------------------------------------------
# face is one of north/south/east/west/up/down; w,h the face size in texels.

def noise_fill(base, var, hi=None, lo=None):
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                c = base
                if hi and y == 0:
                    c = hi
                elif lo and y == h - 1 and h > 1:
                    c = lo
                v = random.randint(-var, var)
                row.append(tuple(clamp(ch + v) for ch in c) + (255,))
            rows.append(row)
        return rows
    return paint


BRONZE = rgb("#9a6c45")
BRONZE_HI = rgb("#c99a68")
BRONZE_LO = rgb("#5e3f28")
DARK = rgb("#2a2624")
GOLD = rgb("#f2c230")
GOLD_HI = rgb("#ffe680")
GOLD_LO = rgb("#b07a12")
GOLD_EDGE = rgb("#6e4a0c")

dark = noise_fill(DARK, 5)


def gold(face, w, h):
    """Polished gold with a bevel: light top/left edge, dark bottom/right edge."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            if y == 0 or x == 0:
                c = GOLD_HI
            elif y == h - 1 or x == w - 1:
                c = GOLD_LO
            else:
                c = GOLD
            v = random.randint(-6, 6)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def bezel_top(face, w, h):
    """Top of the ring: a gold frame around the gem socket, with a dark gold groove."""
    if face != "up":
        return gold(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if edge == 0:
                c = GOLD_EDGE
            elif edge == 1:
                c = GOLD_HI if (x < w / 2 or y < h / 2) else GOLD_LO
            elif edge == 2:
                c = GOLD
            else:
                c = DARK  # the socket under the gem
            row.append(c + (255,))
        rows.append(row)
    return rows


def ring_gem(face, w, h):
    """The ring's emblem: a bright circle with a dark ring inside it, like the lantern's lens."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            r = math.hypot(x - cx, y - cy)
            if face != "up":
                c = (40, 200, 80)
            elif r < w * 0.18:
                c = (230, 255, 235)
            elif r < w * 0.3:
                c = (90, 255, 130)
            elif r < w * 0.38:
                c = (20, 120, 45)
            else:
                c = (60, 240, 105)
            row.append(c + (255,))
        rows.append(row)
    return rows


def ring_bar(face, w, h):
    return [[(70, 250, 115, 255) if (x + y) % 4 else (170, 255, 190, 255) for x in range(w)] for y in range(h)]


def halo(face, w, h):
    """Faint light around the gem. Drawn full-bright like every glow cube."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            k = 0.1 if edge == 0 else 0.2
            row.append((clamp(40 * k), clamp(255 * k), clamp(90 * k), 255))
        rows.append(row)
    return rows


# ---- model building -----------------------------------------------------------------------

class Model:
    def __init__(self, name, density=1):
        """density: texture pixels per model unit. Above 1 the image is that many times bigger
        than Blockbench's UV grid, so each face gets finer pixels (painters get pixel sizes)."""
        self.name = name
        self.density = density
        self.cubes = []

    def cube(self, name, frm, to, paint, inflate=0.0, rotation=None, origin=None):
        """rotation is Blockbench's [x, y, z] degrees about origin (default: the cube's centre)."""
        size = [to[i] - frm[i] for i in range(3)]
        assert all(abs(s - round(s)) < 1e-6 and s >= 0 for s in size), (name, size)
        self.cubes.append(dict(name=name, frm=list(frm), to=list(to), size=[int(round(s)) for s in size],
                               paint=paint, inflate=inflate, rotation=rotation, origin=origin))

    def pack(self):
        """Shelf-pack each cube's box-UV net (2(w+d) x (d+h)) into the smallest square atlas."""
        for side in (16, 32, 64, 128, 256, 512):
            x = y = shelf = 0
            ok = True
            for c in sorted(self.cubes, key=lambda c: -(c["size"][2] + c["size"][1])):
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
                self.side = side
                return
        raise ValueError("atlas too big")

    def faces(self, c):
        """Box-UV face rectangles, as Blockbench lays them out."""
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

    def texture(self):
        k = self.density
        im = Image.new("RGBA", (self.side * k, self.side * k), (0, 0, 0, 0))
        px = im.load()
        for c in self.cubes:
            for face, (u0, v0, u1, v1) in self.faces(c).items():
                w, h = (u1 - u0) * k, (v1 - v0) * k
                if w <= 0 or h <= 0:
                    continue
                rows = c["paint"](face, w, h)
                for y in range(h):
                    for x in range(w):
                        px[u0 * k + x, v0 * k + y] = rows[y][x]
        return im

    def write(self):
        self.pack()
        im = self.texture()
        tex_dir = f"{A}/textures/entity/bb"
        os.makedirs(tex_dir, exist_ok=True)
        os.makedirs(f"{A}/bbmodel", exist_ok=True)
        im.save(f"{tex_dir}/{self.name}.png")
        buf = io.BytesIO()
        im.save(buf, "PNG")
        elements = []
        for c in self.cubes:
            centre = c["origin"] or [(c["frm"][i] + c["to"][i]) / 2 for i in range(3)]
            extra = {"rotation": c["rotation"]} if c["rotation"] else {}
            elements.append({**extra,
                "name": c["name"], "box_uv": True, "rescale": False, "locked": False,
                "render_order": "default", "allow_mirror_modeling": True,
                "from": c["frm"], "to": c["to"], "autouv": 0, "color": 0,
                "inflate": c["inflate"], "origin": centre, "uv_offset": c["uv"],
                "faces": {f: {"uv": r, "texture": 0} for f, r in self.faces(c).items()},
                "type": "cube", "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, self.name + c["name"])),
            })
        model = {
            "meta": {"format_version": "4.10", "model_format": "modded_entity", "box_uv": True},
            "name": self.name,
            "model_identifier": self.name,
            "modded_entity_entity_class": "",
            "modded_entity_version": "Fabric 1.17+",
            "modded_entity_flip_y": True,
            "visible_box": [1, 1, 0],
            "variable_placeholders": "",
            "variable_placeholder_buttons": [],
            "timeline_setups": [],
            "unhandled_root_fields": {},
            "resolution": {"width": self.side, "height": self.side},
            "elements": elements,
            "outliner": [{
                "name": self.name, "origin": [0, 0, 0], "color": 0, "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, self.name)),
                "export": True, "mirror_uv": False, "isOpen": True, "locked": False, "visibility": True, "autouv": 0,
                "children": [e["uuid"] for e in elements],
            }],
            "textures": [{
                "path": "", "name": f"{self.name}.png", "folder": "entity/bb", "namespace": "lanternring",
                "id": "0", "group": "", "width": self.side * self.density, "height": self.side * self.density,
                "uv_width": self.side, "uv_height": self.side, "particle": False, "use_as_default": True,
                "layers_enabled": False, "sync_to_project": "", "render_mode": "default", "render_sides": "auto",
                "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
                "visible": True, "internal": True, "saved": True,
                "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, self.name + ".png")),
                "relative_path": f"../textures/entity/bb/{self.name}.png",
                "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
            }],
        }
        with open(f"{A}/bbmodel/{self.name}.bbmodel", "w") as f:
            json.dump(model, f, indent=1)
        print(f"{self.name}: {len(self.cubes)} cubes, {self.side * self.density}x{self.side * self.density} texture")


# ---- the Power Battery lantern (front faces north, hangs from the top of its handle) -------
# The original lantern shape (stepped bronze base, ribbed green glass with a hoop each side, a
# round emblem lens, a stepped top, a cap and a square handle), painted at 4 pixels per unit:
# hammered bronze with bevels, rivets and a little verdigris, blackened iron bands with studs,
# finely ribbed glass with a hot middle, a ringed emblem and twisted handle wire. The lens centre
# (0, 7, -5) and handle top (y 20) are where LanternFirstPerson aims the ring and holds the
# lantern, so keep them in place. It has its own random numbers, so editing it never shifts
# the rings' noise.
LD = 4  # texture pixels per unit
LR = random.Random(30)
VERDIGRIS = (88, 140, 112)


def mix(a, b, k):
    return tuple(clamp(a[i] + (b[i] - a[i]) * k) for i in range(3))


def jitter(c, v):
    d = LR.randint(-v, v)
    return tuple(clamp(ch + d) for ch in c[:3]) + (255,)


def rivet(rows, x, y, head=BRONZE_HI, body=BRONZE, shadow=DARK):
    """A 2x2 rivet head: lit top-left pixel, shadow under it."""
    h, w = len(rows), len(rows[0])
    for (dx, dy, c) in ((0, 0, head), (1, 0, body), (0, 1, body), (1, 1, BRONZE_LO), (2, 1, shadow), (1, 2, shadow), (2, 2, shadow)):
        if 0 <= x + dx < w and 0 <= y + dy < h:
            rows[y + dy][x + dx] = c + (255,)


def metal(base, hi, lo, var=7, patina=0.0, rivets=0, studs=None):
    """Hammered metal at LD pixels per unit: 2x2 dents, per-pixel grain, a bevel (light top and
    left edge, dark bottom and right), a few bright scratches, optional verdigris near the
    bottom and a row of rivets (every ``rivets`` pixels) along the middle of the side faces."""
    def paint(face, w, h):
        dents = {}
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                key = (x // 2, y // 2)
                if key not in dents:
                    dents[key] = LR.choice((-6, -3, 0, 0, 2, 5))
                c = tuple(clamp(ch + dents[key]) for ch in base)
                if face in ("up", "down"):
                    edge = min(x, y, w - 1 - x, h - 1 - y)
                    if edge == 0:
                        c = lo
                    elif edge == 1:
                        c = mix(c, hi, 0.55) if (x < w / 2 or y < h / 2) else mix(c, lo, 0.4)
                else:
                    if y == 0:
                        c = hi
                    elif y == 1 and h > 3:
                        c = mix(c, hi, 0.45)
                    elif y == h - 1 and h > 1:
                        c = lo
                    elif x == 0:
                        c = mix(c, hi, 0.3)
                    elif x == w - 1:
                        c = mix(c, lo, 0.5)
                    if patina and y >= h - 3 and 0 < y < h - 1 and LR.random() < patina:
                        c = mix(c, VERDIGRIS, 0.7)
                row.append(jitter(c, var))
            rows.append(row)
        # scratches: short bright diagonals
        for _ in range((w * h) // 90):
            x, y = LR.randrange(w), LR.randrange(h)
            for i in range(LR.randint(2, 4)):
                if 0 < x + i < w - 1 and 0 < y + i // 2 < h - 1:
                    rows[y + i // 2][x + i] = mix(rows[y + i // 2][x + i], hi, 0.6) + (255,)
        if rivets and face not in ("up", "down") and h >= 4:
            for x in range(rivets // 2, w - 2, rivets):
                rivet(rows, x, h // 2 - 1, *(studs or ()))
        return rows
    return paint


def l_dark_iron(stud_every=10):
    """Blackened iron with a faint grain, a lit top edge and bronze studs."""
    iron = metal(DARK, (78, 70, 62), (16, 14, 13), var=4, rivets=stud_every,
                 studs=((214, 170, 120), BRONZE, (10, 9, 8)))

    def paint(face, w, h):
        rows = iron(face, w, h)
        if face not in ("up", "down"):
            for y in range(1, h - 1):
                for x in range(w):
                    if (x + 3 * y) % 11 == 0:
                        rows[y][x] = mix(rows[y][x], (60, 55, 50), 0.7) + (255,)
        return rows
    return paint


l_bronze = metal(BRONZE, BRONZE_HI, BRONZE_LO, patina=0.07)
l_bronze_riveted = metal(BRONZE, BRONZE_HI, BRONZE_LO, patina=0.07, rivets=8)
l_iron = l_dark_iron()


def l_glass(face, w, h):
    """The glass under its light (hidden by the glow cube, but shown in Blockbench)."""
    return [[jitter((24, 120, 50) if (y // LD) % 2 == 0 else (12, 78, 30), 5) for x in range(w)] for y in range(h)]


def l_glass_glow(face, w, h):
    """The lit glass, painted bright since glow covers what is behind it. Each unit is a rib:
    a pale crest, bright body and a dark groove; brighter toward the hot middle, darker at the
    corner edges, with a pale streak near the left and a few sparks."""
    rows = []
    for y in range(h):
        p = y % LD
        rib = [(175, 255, 190), (80, 255, 125), (52, 220, 98), (18, 120, 45)][p]
        row = []
        for x in range(w):
            if face in ("up", "down"):
                c = (40, 200, 85)
            else:
                k = abs(x - (w - 1) / 2) / ((w - 1) / 2)  # 0 middle .. 1 edge
                c = mix(rib, (10, 70, 28), 0.55 * k * k)
                if x in (0, w - 1):
                    c = mix(c, (8, 40, 18), 0.6)
                if 3 <= x <= 4 and p < 3:
                    c = mix(c, (220, 255, 225), 0.55)
                if LR.random() < 0.03 and p < 3:
                    c = (200, 255, 210)
            row.append(c + (255,))
        rows.append(row)
    return rows


def l_emblem(face, w, h):
    """The lens plate seen from the front: a square bronze plate with a rivet in each corner, a
    raised rim, a black ring, an engraved inner ring and the dark socket the glowing lens sits in."""
    if face != "north":
        return l_bronze(face, w, h)
    rows = l_bronze(face, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    R = w / 2
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            lit = dx + dy < 0
            if r > R - 0.4:
                continue
            elif r > R - 2:
                c = BRONZE_HI if lit else BRONZE_LO
            elif r > R - 3:
                c = (24, 20, 18)
            elif r > R - 5.5:
                ang = math.degrees(math.atan2(dy, dx)) % 30
                c = BRONZE_LO if ang < 4 and R - 5 < r < R - 3.5 else (BRONZE if lit else mix(BRONZE, BRONZE_LO, 0.4))
            elif r > R - 6.5:
                c = BRONZE_LO
            else:
                c = (10, 52, 22)
            rows[y][x] = jitter(c, 4)
    for x, y in ((1, 1), (w - 4, 1), (1, h - 4), (w - 4, h - 4)):
        rivet(rows, x, y)
    return rows


def l_lens_glow(face, w, h):
    """The glowing lens: a round bright jewel with a pale core and a highlight top-left; the
    square's corners are deep green so it reads as round against the dark socket."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            if face not in ("north", "south"):
                c = (40, 200, 85)
            else:
                r = math.hypot(x - cx, y - cy)
                if r > w / 2:
                    c = (14, 80, 32)
                elif r < 1.2:
                    c = (235, 255, 240)
                elif x - cx < -0.5 and y - cy < -0.5 and r < 2.6:
                    c = (190, 255, 205)
                elif r < 2.4:
                    c = (110, 255, 150)
                elif r > w / 2 - 1:
                    c = (40, 210, 90)
                else:
                    c = (70, 255, 120)
            row.append(c + (255,))
        rows.append(row)
    return rows


def l_cap(face, w, h):
    """The cap: bronze with two vent slots on each side and a bright rim on top."""
    rows = l_bronze(face, w, h)
    if face in ("up", "down"):
        return rows
    for x0 in (w // 4, 3 * w // 4 - 1):
        for y in range(2, h - 2):
            rows[y][x0] = (14, 12, 11, 255)
            if x0 + 1 < w:
                rows[y][x0 + 1] = BRONZE_LO + (255,)
    return rows


def l_top(face, w, h):
    """The stepped top: bronze, with engraved spokes on the visible ring round the cap."""
    rows = l_bronze(face, w, h)
    if face != "up":
        return rows
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            if max(abs(dx), abs(dy)) > w / 4 + 1 and min(abs(dx), abs(dy)) < 0.6 or abs(abs(dx) - abs(dy)) < 0.6 and max(abs(dx), abs(dy)) > w / 4 + 1:
                if 1 < x < w - 2 and 1 < y < h - 2:
                    rows[y][x] = BRONZE_LO + (255,)
    return rows


def l_wire(face, w, h):
    """Twisted handle wire: alternating light and dark diagonal strands."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            t = (x + y) % 4
            c = (BRONZE_HI, BRONZE, BRONZE_LO, mix(BRONZE, BRONZE_LO, 0.5))[t]
            row.append(jitter(c, 5))
        rows.append(row)
    return rows


def l_tip(face, w, h):
    rows = l_bronze(face, w, h)
    if face == "up":
        rows[1][1] = (240, 210, 160, 255)
        rows[1][2] = BRONZE_HI + (255,)
    return rows


lantern = Model("power_lantern", density=LD)
L = lantern.cube
L("base", (-6, 0, -6), (6, 1, 6), l_bronze_riveted)
L("base_band", (-6, 1, -6), (6, 2, 6), l_iron)
L("base_lip", (-5, 2, -5), (5, 3, 5), l_bronze)
L("glass", (-4, 3, -4), (4, 12, 4), l_glass)
L("glow_glass", (-4, 3, -4), (4, 12, 4), l_glass_glow, inflate=0.05)
L("hoop_low", (-6, 5, -2), (6, 6, 2), l_bronze_riveted)
L("hoop_high", (-6, 9, -2), (6, 10, 2), l_bronze_riveted)
L("lens", (-3, 4, -5), (3, 10, -4), l_emblem)
L("glow_lens", (-1, 6, -5.4), (1, 8, -4.4), l_lens_glow)
L("top_lip", (-5, 12, -5), (5, 13, 5), l_bronze_riveted)
L("top_band", (-5, 13, -5), (5, 14, 5), l_iron)
L("top", (-4, 14, -4), (4, 15, 4), l_top)
L("cap", (-2, 15, -2), (2, 17, 2), l_cap)
L("tip", (-1, 17, -1), (1, 18, 1), l_tip)
L("handle_left", (-5, 14, -0.5), (-4, 20, 0.5), l_wire)
L("handle_right", (4, 14, -0.5), (5, 20, 0.5), l_wire)
L("handle_top", (-4, 19, -0.5), (4, 20, 0.5), l_wire)
lantern.write()

# ---- the ring's top, lying face up (+Y). 1 unit = 1/6 of a skin pixel; -X is the back of the hand.
ring = Model("power_ring")
R = ring.cube
R("seat", (-7, 0, -7), (7, 1, 7), dark)
R("bezel", (-7, 1, -7), (7, 4, 7), bezel_top)
R("glow_bar_a", (-5, 4, -6), (5, 5, -4), ring_bar)
R("glow_bar_b", (-5, 4, 4), (5, 5, 6), ring_bar)
R("glow_gem", (-3, 4, -3), (3, 5, 3), ring_gem)
R("glow_halo", (-5, 5, -5), (5, 8, 5), halo)
ring.write()


# ---- the signet rings from J's reference sheet ---------------------------------------------
# 1 unit = 1/16 of a skin pixel. The face lies up (+Y, out of the fist's punching face); X runs
# along the finger with -X toward the knuckles, Z across the fingers. The shank goes down into
# the fist and mostly hides there.

SILVER = rgb("#b9bcc0")
SILVER_HI = rgb("#e4e6e8")
SILVER_LO = rgb("#7d8084")
EMERALD_DEEP = rgb("#0b4a22")
EMERALDS = [rgb("#0d5f2a"), rgb("#14873a"), rgb("#1fae4a"), rgb("#3ad065"), rgb("#7cf29a")]

silver = noise_fill(SILVER, 10, SILVER_HI, SILVER_LO)


def gold_border(x, y, w, h):
    """Bevelled one-texel gold edge: light on the top/left, dark on the bottom/right."""
    if x == 0 or y == 0:
        return GOLD_HI
    if x == w - 1 or y == h - 1:
        return GOLD_LO
    return None


def emerald_at(x, y, w, h, lit=False):
    """Concentric square bands of emerald, brightest in the middle, as on the reference face."""
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
    ring = int((1 - d) * max(cx, cy) + 0.5)  # 0 at the edge, counting in toward the middle
    band = min(len(EMERALDS) - 1, ring // 2 + (ring % 2))
    c = EMERALDS[band] if ring % 2 else shade(EMERALDS[max(0, band - 1)], 0.8)[:3]
    if (x * 3 + y * 5) % 7 == 0:
        c = shade(c, 1.15)[:3]
    if lit:
        return tuple(clamp(ch * (1.0 + 0.1 * band)) for ch in c)
    return c


def plate(face, w, h):
    """The base plate: gold, with deep emerald showing between the bars and the setting."""
    if face != "up":
        return gold(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            c = gold_border(x, y, w, h) or (GOLD if edge == 1 else EMERALD_DEEP)
            row.append(c + (255,))
        rows.append(row)
    return rows


def bar(face, w, h):
    """An emerald bar in a gold frame. The stripes run along the bar."""
    if face != "up":
        return gold(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = gold_border(x, y, w, h)
            if c is None:
                long_axis = y if h > w else x
                c = EMERALDS[1 + (long_axis // 2 + x * y) % 3]
                if random.random() < 0.08:
                    c = EMERALDS[4]
            row.append(c + (255,))
        rows.append(row)
    return rows


def setting(face, w, h):
    """The centre square: gold frame with notched corners around concentric emerald."""
    if face != "up":
        return gold(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            corner = min(x, w - 1 - x) < 2 and min(y, h - 1 - y) < 2
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if corner and edge == 0:
                c = GOLD_EDGE
            elif edge == 0 or (corner and edge == 1):
                c = gold_border(x, y, w, h) or GOLD
            elif edge == 2:
                c = GOLD
            else:
                c = emerald_at(x - 1, y - 1, w - 2, h - 2)
            row.append(c + (255,))
        rows.append(row)
    return rows


def gem(face, w, h):
    if face != "up":
        return [[EMERALDS[2] + (255,)] * w for _ in range(h)]
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = emerald_at(x, y, w, h)
            if abs(x - (w - 1) / 2) < 1 and abs(y - (h - 1) / 2) < 1:
                c = rgb("#d8ffe2")
            row.append(c + (255,))
        rows.append(row)
    return rows


def lit_bar(face, w, h):
    """The bar's emerald drawn full-bright, so it glows at night."""
    return [[tuple(clamp(ch * 1.1) for ch in EMERALDS[2 + (max(x, y) // 2 + x * y) % 2]) + (255,)
             for x in range(w)] for y in range(h)]


def lit_square(face, w, h):
    return [[emerald_at(x, y, w, h, lit=True) + (255,) for x in range(w)] for y in range(h)]


def lit_core(face, w, h):
    cx, cy = (w - 1) / 2, (h - 1) / 2
    return [[((200, 255, 215) if max(abs(x - cx), abs(y - cy)) < 1 else (60, 230, 110)) + (255,)
             for x in range(w)] for y in range(h)]


GLOW_Y = 0.05  # light planes float this far above the surface they light


def lit_step(face, w, h):
    """The lit top of a gem step: the step above covers the middle, so only the rim shows. A
    pale edge and bright green, so the gem is the brightest thing on the ring."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            c = (150, 255, 175) if edge == 0 and (x == 0 or y == 0) else (EMERALDS[4] if edge == 0 else (60, 235, 110))
            row.append(c + (255,))
        rows.append(row)
    return rows


def gem_side(face, w, h):
    """A gem tier seen from the side: light at the top edge fading to deep green, with a glint."""
    if face == "up":
        return gem(face, w, h)
    rows = []
    for y in range(h):
        k = y / max(h - 1, 1)
        c = EMERALDS[3] if y == 0 else (EMERALDS[2] if k < 0.6 else EMERALDS[1])
        row = []
        for x in range(w):
            cc = EMERALDS[4] if (x == 1 and y < h - 1 and w > 3) else c
            row.append(cc + (255,))
        rows.append(row)
    return rows


def frame(face, w, h):
    """A step of the gold mount: bevelled gold, with a dark seam on the top just inside the edge."""
    if face != "up":
        return gold(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            c = gold_border(x, y, w, h) or (GOLD_EDGE if edge == 2 else GOLD)
            row.append(c + (255,))
        rows.append(row)
    return rows


def gallery(face, w, h):
    """The openwork under the face: dark gold with arched holes along the sides."""
    if face in ("up", "down"):
        return [[GOLD_EDGE + (255,)] * w for _ in range(h)]
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            hole = x % 4 in (1, 2) and y == h - 1 and 0 < x < w - 1
            c = DARK if hole else (GOLD_LO if y == 0 else GOLD_EDGE)
            row.append(c + (255,))
        rows.append(row)
    return rows


def gold_flat(face, w, h):
    """Gold without the bevel, for cubes that join into one surface (the beacon's round plate)."""
    return [[tuple(clamp(ch + random.randint(-6, 6)) for ch in GOLD) + (255,) for _ in range(w)] for _ in range(h)]


def band(m, paint, half_x=4):
    """The ring's band: a loop round the finger, which runs along X with its middle at y = -9.
    Under the face it flares into shoulders. On the hand everything below y = 0 sits inside the
    fist, so only the shoulders show there; the item views show the whole loop."""
    C = m.cube
    C("band_bottom", (-half_x, -21, -7), (half_x, -18, 7), paint)
    for sz in (-1, 1):
        n = "a" if sz < 0 else "b"
        C(f"band_corner_{n}", (-half_x, -19, min(sz * 7, sz * 10)), (half_x, -16, max(sz * 7, sz * 10)), paint)
        C(f"band_side_{n}", (-half_x, -16, min(sz * 8, sz * 11)), (half_x, -3, max(sz * 8, sz * 11)), paint)
        C(f"band_shoulder_{n}", (-half_x - 2, -3, min(sz * 8, sz * 12)), (half_x + 2, 2, max(sz * 8, sz * 12)), paint)


def gem_stack(m, tiers, base):
    """A gem that stands up in steps, each with a lit top so the rim of every step glows."""
    C = m.cube
    y = base
    for i, (r, h) in enumerate(tiers):
        C(f"gem_{i}", (-r, y, -r), (r, y + h, r), gem_side)
        y += h
        C(f"glow_gem_{i}", (-r, y + GLOW_Y, -r), (r, y + GLOW_Y, r), lit_core if i == len(tiers) - 1 else lit_step)
    return y


def crest(name, band_paint, lift=0, prongs=False):
    """J's signet: a stepped gold face with an emerald bar at each end and a gem standing up in
    the middle, on a band that wraps the finger. ``lift`` raises the gem mount."""
    m = Model(name)
    C = m.cube
    band(m, band_paint)
    C("gallery", (-12, 0, -10), (12, 2, 10), gallery)
    C("plate", (-14, 2, -12), (14, 4, 12), plate)
    C("bar_knuckle", (-13, 4, -11), (-8, 7, 11), bar)
    C("bar_palm", (8, 4, -11), (13, 7, 11), bar)
    C("glow_bar_knuckle", (-12, 7 + GLOW_Y, -10), (-9, 7 + GLOW_Y, 10), lit_bar)
    C("glow_bar_palm", (9, 7 + GLOW_Y, -10), (12, 7 + GLOW_Y, 10), lit_bar)
    C("mount_low", (-7, 4, -9), (7, 6 + lift, 9), frame)
    C("mount_high", (-6, 6 + lift, -7), (6, 8 + lift, 7), frame)
    top = gem_stack(m, [(5, 2), (4, 2), (2, 1)], 8 + lift)
    if prongs:
        for sx in (-1, 1):
            for sz in (-1, 1):
                C(f"prong_{sx}_{sz}", (sx * 5 - 1, 8 + lift, sz * 5 - 1), (sx * 5 + 1, 11 + lift, sz * 5 + 1), gold)
    m.write()
    return top


crest("ring_crest", silver)
crest("ring_crest_gold", gold, lift=1, prongs=True)

# The beacon: no bars, a round gold plate and a stepped emerald that stands well proud of it.
beacon = Model("ring_beacon")
B = beacon.cube
band(beacon, silver)
B("gallery", (-10, 0, -10), (10, 2, 10), gallery)
B("plate", (-12, 2, -9), (12, 4, 9), gold_flat)
B("plate_front", (-9, 2, -12), (9, 4, -9), gold_flat)
B("plate_back", (-9, 2, 9), (9, 4, 12), gold_flat)
B("mount", (-9, 4, -9), (9, 6, 9), frame)
gem_stack(beacon, [(7, 3), (5, 3), (3, 2), (1, 1)], 6)
for sx in (-1, 1):
    for sz in (-1, 1):
        B(f"claw_{sx}_{sz}", (sx * 7 - 1, 6, sz * 7 - 1), (sx * 7 + 1, 10, sz * 7 + 1), gold)
beacon.write()


# ---- the Blast drill: hard-light jade, 6 blocks long, tip toward -Z (north) -----------------
# A twisted, tapering core with three uneven helical blades (one big and glowing, one smaller,
# one broken every other turn), so the spin reads from behind. The back carries two unequal
# glowing spokes for the same reason. The mod spins it about Z and flies it tip first.

drng = random.Random(26)
JADE_DEEP = (6, 62, 36)
JADE_MID = (22, 120, 66)
JADE_EDGE = (70, 200, 120)
MINT = (130, 255, 175)
MINT_HOT = (215, 255, 228)


def drill_body(face, w, h):
    """Deep jade with diagonal veins, so a spinning side shows moving stripes."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = JADE_DEEP
            if (x + y) % 6 == 0:
                c = JADE_MID
            elif (x - 2 * y) % 11 == 0:
                c = JADE_EDGE
            v = drng.randint(-6, 6)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def drill_blade(face, w, h):
    """Mid jade with a lighter top edge and a dark root."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = JADE_EDGE if y == 0 or x == 0 else JADE_MID
            if y == h - 1 and h > 2:
                c = JADE_DEEP
            v = drng.randint(-8, 8)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def drill_glow(face, w, h):
    return [[(MINT_HOT if (x + y) % 5 == 0 else MINT) + (255,) for x in range(w)] for y in range(h)]


drill = Model("blast_drill")
D = drill.cube
SEGMENTS, SEG = 12, 8
D("hub", (-20, -20, 0), (20, 20, 6), drill_body)
D("glow_core", (-4, -4, 6.05), (4, 4, 6.05), drill_glow)
D("glow_spoke_long", (-2, 4, 6.05), (2, 19, 6.05), drill_glow)
D("glow_spoke_short", (-1.5, 4, 6.05), (1.5, 12, 6.05), drill_glow, rotation=[0, 0, 140], origin=[0, 0, 6])
BLADES = [(0, 7, 3, True), (115, 5, 2, True), (250, 4, 2, False)]  # angle, reach, thickness, glowing edge
for i in range(SEGMENTS):
    z0, z1 = -SEG * (i + 1), -SEG * i
    r = max(2, round(18 - 1.45 * i))
    taper = 1 - i / (SEGMENTS + 2)
    D(f"core_{i}", (-r, -r, z0), (r, r, z1), drill_body, rotation=[0, 0, i * 15], origin=[0, 0, (z0 + z1) / 2])
    for k, (angle, reach, thick, lit) in enumerate(BLADES):
        if k == 2 and i % 2:
            continue  # the third blade is broken every other turn
        out = max(2, round(reach * taper))
        rot = [0, 0, (i * 30 + angle) % 360]
        org = [0, 0, (z0 + z1) / 2]
        D(f"blade_{k}_{i}", (r - 2, -thick / 2, z0), (r + out, thick / 2, z1), drill_blade, rotation=rot, origin=org)
        if lit:
            D(f"glow_edge_{k}_{i}", (r + out - 1, -thick / 2, z0), (r + out, thick / 2, z1), drill_glow,
              inflate=0.05, rotation=rot, origin=org)
D("glow_tip", (-1, -1, -SEG * SEGMENTS - 4), (1, 1, -SEG * SEGMENTS), drill_glow)
drill.write()


# ---- the forged ring from J's second reference sheet ---------------------------------------
# Same axes as the signets (face up, -X toward the knuckles, 1 unit = 1/16 skin pixel). A dark
# forged-carbon band that tapers from the face down to a narrow underside, a square gold bezel
# with an emerald baguette at each end, and a stepped emerald-cut stone in a notched gold frame.
# J asked for the face to stand further proud than on the sheet, so the bezel is 5 deep and the
# stone climbs another 6 above it.

frng = random.Random(41)
CARBON = (50, 50, 55)
CARBON_HI = (104, 104, 112)
CARBON_LO = (24, 24, 28)


def carbon(face, w, h):
    """Forged carbon: dark grey with short chips of lighter and darker grey at random angles."""
    rows = [[tuple(clamp(ch + frng.randint(-5, 5)) for ch in CARBON) + (255,) for _ in range(w)] for _ in range(h)]
    for _ in range(max(1, w * h // 7)):
        x, y = frng.randrange(w), frng.randrange(h)
        dx, dy = frng.choice(((1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (1, 2)))
        c = CARBON_HI if frng.random() < 0.55 else CARBON_LO
        for k in range(frng.randint(1, 3)):
            px_, py_ = x + dx * k, y + dy * k
            if 0 <= px_ < w and 0 <= py_ < h:
                rows[py_][px_] = shade(c, 0.9 + 0.2 * frng.random())[:3] + (255,)
    return rows


def baguette(face, w, h):
    """A baguette emerald seen unlit: step-cut stripes along its length."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            across = min(x, w - 1 - x) if w < h else min(y, h - 1 - y)
            c = EMERALDS[min(3, 1 + across)] if face == "up" else EMERALDS[1]
            row.append(c + (255,))
        rows.append(row)
    return rows


def lit_baguette(face, w, h):
    """The baguette's glowing top: a pale table down the middle, bright step-cut stripes."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            across = min(x, w - 1 - x) if w < h else min(y, h - 1 - y)
            along = y if w < h else x
            c = (60, 225, 105) if across == 0 else (95, 255, 140)
            if across >= 1 and along % 5 == 2:
                c = (190, 255, 205)
            row.append(c + (255,))
        rows.append(row)
    return rows


def stepped_field(face, w, h):
    """The well around the stone: emerald, crossed by a gold line that steps in at each corner,
    like the outline on the reference."""
    if face != "up":
        return gold(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            ex, ey = min(x, w - 1 - x), min(y, h - 1 - y)
            # the line runs 1 texel in from the edge, stepping in by 2 at each corner
            on = (ex == 1 and ey >= 4) or (ey == 1 and ex >= 4) or (ex == 3 and 1 <= ey <= 4) or \
                 (ey == 3 and 1 <= ex <= 4) or (ex == 1 and ey == 3) or (ey == 1 and ex == 3)
            if on:
                c = GOLD_HI if (x < w / 2 and y < h / 2) else GOLD
            elif ex == 0 or ey == 0:
                c = EMERALD_DEEP
            else:
                c = EMERALDS[1] if (x + 2 * y) % 5 else EMERALDS[2]
            row.append(c + (255,))
        rows.append(row)
    return rows


def lit_facet(face, w, h):
    """A step of the emerald cut, lit: the step above covers the middle, so the 1-texel rim is what
    shows. Saturated emerald, lighter on the top/left facets and deeper on the bottom/right, with
    a pale table in the middle of the top step."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if w <= 4 and abs(x - cx) < 1 and abs(y - cy) < 1:
                c = (175, 255, 195)
            elif edge == 0 and (x == 0 or y == 0):
                c = (90, 250, 135)
            elif edge == 0:
                c = (25, 175, 70)
            else:
                c = (40, 215, 95)
            row.append(c + (255,))
        rows.append(row)
    return rows


forged = Model("ring_forged")
F = forged.cube
# The band: a loop round the finger (inner radius 8, outer 12, centred at y = -9) cut in 3-unit
# rows. Each row is narrower along the finger the lower it sits, so the side view tapers.
YC, R_IN, R_OUT = -9, 8, 12
for i, y0 in enumerate(range(YC - R_OUT, 0, 3)):
    ym = y0 + 1.5
    dy = ym - YC
    zo = R_OUT if dy >= 0 else round(math.sqrt(R_OUT ** 2 - dy ** 2))
    zi = round(math.sqrt(R_IN ** 2 - dy ** 2)) if abs(dy) < R_IN else 0
    hx = round(6 + 6 * (ym - (YC - R_OUT)) / R_OUT / 2)
    if zi == 0:
        F(f"band_{i}", (-hx, y0, -zo), (hx, y0 + 3, zo), carbon)
    else:
        zi = min(zi, zo - 2)
        F(f"band_{i}_a", (-hx, y0, -zo), (hx, y0 + 3, -zi), carbon)
        F(f"band_{i}_b", (-hx, y0, zi), (hx, y0 + 3, zo), carbon)
# Gold bezel, with gold corners running down onto the band at each end.
F("bezel", (-13, 0, -11), (13, 5, 11), gold)
for sx in (-1, 1):
    for sz in (-1, 1):
        F(f"bezel_leg_{sx}_{sz}", (min(sx * 12, sx * 13), -3, min(sz * 6, sz * 11)),
          (max(sx * 12, sx * 13), 0, max(sz * 6, sz * 11)), gold)
# Raised rim and the two dividers that box in the baguettes.
F("rim_knuckle", (-13, 5, -11), (-12, 7, 11), gold)
F("rim_palm", (12, 5, -11), (13, 7, 11), gold)
F("rim_a", (-12, 5, -11), (12, 7, -10), gold)
F("rim_b", (-12, 5, 10), (12, 7, 11), gold)
F("divider_knuckle", (-9, 5, -10), (-8, 7, 10), gold)
F("divider_palm", (8, 5, -10), (9, 7, 10), gold)
# Baguettes, sunk 1 below the rim, each with a bright light plane on top.
for n, x0 in (("knuckle", -12), ("palm", 9)):
    F(f"baguette_{n}", (x0, 5, -10), (x0 + 3, 6, 10), baguette)
    F(f"glow_baguette_{n}", (x0, 6 + GLOW_Y, -10), (x0 + 3, 6 + GLOW_Y, 10), lit_baguette)
# The centre: an emerald well with the stepped gold line, then a notched gold mount and the stone.
F("field", (-8, 5, -10), (8, 6, 10), stepped_field)
F("mount_a", (-6, 6, -5), (6, 8, 5), frame)
F("mount_b", (-5, 6, -6), (5, 8, 6), frame)
y = 8
for i, (r, h) in enumerate([(5, 2), (4, 1), (3, 1), (2, 1)]):
    F(f"stone_{i}", (-r, y, -r), (r, y + h, r), gem_side)
    y += h
    F(f"glow_stone_{i}", (-r, y + GLOW_Y, -r), (r, y + GLOW_Y, r), lit_facet)
forged.write()
