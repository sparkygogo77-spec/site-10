"""Writes the lantern and ring as Blockbench models (.bbmodel) plus their texture atlases.

    python tools/blockbench_models.py src/main/resources/assets/lanternring

Open the .bbmodel files in Blockbench (File > Open Model) to edit them; the mod reads them
straight from assets/lanternring/bbmodel/ at startup, so an edited file can simply replace the
generated one. Conventions the mod relies on:

- "Modded Entity" format with box UV, 1 unit = 1 pixel. Coordinates are exactly as Blockbench
  shows them (+Y up, the lantern's front faces north / -Z).
- Cubes whose name starts with "glow" are drawn full-bright and additive (they light up), using
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

bronze = noise_fill(BRONZE, 8, BRONZE_HI, BRONZE_LO)
dark = noise_fill(DARK, 5)


def glass(face, w, h):
    """Ribbed green glass: alternating ridge and groove rows, a lighter streak near one edge."""
    rows = []
    for y in range(h):
        ridge = y % 2 == 0
        row = []
        for x in range(w):
            c = (28, 128, 52) if ridge else (12, 78, 30)
            if face in ("north", "south", "east", "west") and x == 1:
                c = (88, 190, 110) if ridge else (40, 130, 60)
            v = random.randint(-6, 6)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def glass_glow(face, w, h):
    """The light inside the glass: bright on the ridges, a dim flicker in the grooves."""
    rows = []
    for y in range(h):
        ridge = y % 2 == 0
        row = []
        for x in range(w):
            if ridge:
                c = (60, 255, 110) if random.random() > 0.15 else (150, 255, 170)
                a = 255
            else:
                c = (20, 150, 50)
                a = 255
            row.append(c + (a,))
        rows.append(row)
    return rows


def emblem(face, w, h):
    """The round lens on the lantern's front: bronze rim, dark ring, bronze ring, dark centre."""
    if face != "north":
        return bronze(face, w, h)
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            r = math.hypot(x - cx, y - cy)
            if r > w / 2 + 0.2:
                c = BRONZE_LO
            elif r > w / 2 - 0.9:
                c = BRONZE_HI if (x + y) < w else BRONZE
            elif r > w / 2 - 1.8:
                c = DARK
            else:
                c = BRONZE
            row.append(c + (255,))
        rows.append(row)
    return rows


def glow_core(face, w, h):
    rows = []
    for y in range(h):
        rows.append([(120, 255, 150, 255) if (x + y) % 3 else (60, 255, 110, 255) for x in range(w)])
    return rows


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
    """Faint light around the gem. Darker texels add less light (glow cubes are additive)."""
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
    def __init__(self, name):
        self.name = name
        self.cubes = []

    def cube(self, name, frm, to, paint, inflate=0.0):
        size = [to[i] - frm[i] for i in range(3)]
        assert all(abs(s - round(s)) < 1e-6 and s >= 0 for s in size), (name, size)
        self.cubes.append(dict(name=name, frm=list(frm), to=list(to), size=[int(round(s)) for s in size],
                               paint=paint, inflate=inflate))

    def pack(self):
        """Shelf-pack each cube's box-UV net (2(w+d) x (d+h)) into the smallest square atlas."""
        for side in (16, 32, 64, 128, 256):
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
        im = Image.new("RGBA", (self.side, self.side), (0, 0, 0, 0))
        px = im.load()
        for c in self.cubes:
            for face, (u0, v0, u1, v1) in self.faces(c).items():
                w, h = u1 - u0, v1 - v0
                if w <= 0 or h <= 0:
                    continue
                rows = c["paint"](face, w, h)
                for y in range(h):
                    for x in range(w):
                        px[u0 + x, v0 + y] = rows[y][x]
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
            centre = [(c["frm"][i] + c["to"][i]) / 2 for i in range(3)]
            elements.append({
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
                "id": "0", "group": "", "width": self.side, "height": self.side,
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
        print(f"{self.name}: {len(self.cubes)} cubes, {self.side}x{self.side} texture")


# ---- the Power Battery lantern (front faces north, hangs from the top of its handle) -------
lantern = Model("power_lantern")
L = lantern.cube
L("base", (-6, 0, -6), (6, 1, 6), bronze)
L("base_band", (-6, 1, -6), (6, 2, 6), dark)
L("base_lip", (-5, 2, -5), (5, 3, 5), bronze)
L("glass", (-4, 3, -4), (4, 12, 4), glass)
L("glow_glass", (-4, 3, -4), (4, 12, 4), glass_glow, inflate=0.05)
L("hoop_low", (-6, 5, -2), (6, 6, 2), bronze)
L("hoop_high", (-6, 9, -2), (6, 10, 2), bronze)
L("lens", (-3, 4, -5), (3, 10, -4), emblem)
L("glow_lens", (-1, 6, -5.4), (1, 8, -4.4), glow_core)
L("top_lip", (-5, 12, -5), (5, 13, 5), bronze)
L("top_band", (-5, 13, -5), (5, 14, 5), dark)
L("top", (-4, 14, -4), (4, 15, 4), bronze)
L("cap", (-2, 15, -2), (2, 17, 2), bronze)
L("tip", (-1, 17, -1), (1, 18, 1), bronze)
L("handle_left", (-5, 14, -0.5), (-4, 20, 0.5), bronze)
L("handle_right", (4, 14, -0.5), (5, 20, 0.5), bronze)
L("handle_top", (-4, 19, -0.5), (4, 20, 0.5), bronze)
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
        return tuple(clamp(ch * (0.25 + 0.13 * band)) for ch in c)
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
    """Light over a bar's emerald (glow cubes add their colour, so black adds nothing)."""
    return [[tuple(clamp(ch * 0.45) for ch in EMERALDS[2 + (max(x, y) // 2 + x * y) % 2]) + (255,)
             for x in range(w)] for y in range(h)]


def lit_square(face, w, h):
    return [[emerald_at(x, y, w, h, lit=True) + (255,) for x in range(w)] for y in range(h)]


def lit_core(face, w, h):
    cx, cy = (w - 1) / 2, (h - 1) / 2
    return [[((200, 255, 215) if max(abs(x - cx), abs(y - cy)) < 1 else (60, 230, 110)) + (255,)
             for x in range(w)] for y in range(h)]


def ring_halo(face, w, h):
    return [[(clamp(30 * 0.25), clamp(255 * 0.25), clamp(90 * 0.25), 255)] * w for _ in range(h)]


GLOW_Y = 0.05  # light planes float this far above the surface they light


def crest(name, band_paint, plate_h=2, bar_h=2, prongs=False):
    """J's signet: a gold plate with an emerald bar at each end and a framed square between."""
    m = Model(name)
    C = m.cube
    C("shank", (-11, -8, -9), (11, 0, 9), band_paint)
    C("shank_low", (-9, -14, -7), (9, -8, 7), band_paint)
    C("plate", (-14, 0, -12), (14, plate_h, 12), plate)
    top = plate_h + bar_h
    C("bar_knuckle", (-13, plate_h, -11), (-8, top, 11), bar)
    C("bar_palm", (8, plate_h, -11), (13, top, 11), bar)
    C("setting", (-7, plate_h, -8), (7, top, 8), setting)
    C("gem", (-4, top, -4), (4, top + 1, 4), gem)
    if prongs:
        for sx in (-1, 1):
            for sz in (-1, 1):
                C(f"prong_{sx}_{sz}", (sx * 6 - 1, top, sz * 7 - 1), (sx * 6 + 1, top + 1, sz * 7 + 1), gold)
    g = top + GLOW_Y
    C("glow_bar_knuckle", (-12, g, -10), (-9, g, 10), lit_bar)
    C("glow_bar_palm", (9, g, -10), (12, g, 10), lit_bar)
    C("glow_setting", (-4, g, -5), (4, g, 5), lit_square)
    C("glow_gem", (-3, top + 1 + GLOW_Y, -3), (3, top + 1 + GLOW_Y, 3), lit_core)
    C("glow_halo", (-6, top, -6), (6, top + 4, 6), ring_halo)
    m.write()


crest("ring_crest", silver)
crest("ring_crest_gold", gold, plate_h=3, prongs=True)

# The beacon: no bars, a rounded gold plate and a stepped emerald that stands well proud of it.
beacon = Model("ring_beacon")
B = beacon.cube
B("shank", (-10, -8, -9), (10, 0, 9), silver)
B("shank_low", (-8, -14, -7), (8, -8, 7), silver)
B("plate", (-12, 0, -12), (12, 2, 12), plate)
B("gem_low", (-9, 2, -9), (9, 4, 9), setting)
B("gem_mid", (-6, 4, -6), (6, 6, 6), gem)
B("gem_top", (-3, 6, -3), (3, 7, 3), gem)
B("glow_low", (-7, 4 + GLOW_Y, -7), (7, 4 + GLOW_Y, 7), lit_square)
B("glow_mid", (-5, 6 + GLOW_Y, -5), (5, 6 + GLOW_Y, 5), lit_square)
B("glow_top", (-2, 7 + GLOW_Y, -2), (2, 7 + GLOW_Y, 2), lit_core)
B("glow_halo", (-9, 2, -9), (9, 10, 9), ring_halo)
beacon.write()
