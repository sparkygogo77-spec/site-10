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
    def __init__(self, name):
        self.name = name
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
# Bronze and black like J's reference: a stepped base on four feet, ribbed green glass between
# corner posts, a round lens on the front and back, a ring on each side, and a stepped dome
# under an arched handle. The lens centre (0, 7, -5) and handle top (y 20) are where
# LanternFirstPerson aims the ring and holds the lantern, so keep them in place.


def riveted(face, w, h):
    """Bronze with a bevel and a row of dark rivets along the middle of the side faces."""
    rows = bronze(face, w, h)
    if face in ("up", "down") or h < 1:
        return rows
    y = h // 2
    for x in range(1, w - 1, 3):
        rows[y][x] = DARK + (255,)
        if y > 0:
            rows[y - 1][x] = BRONZE_HI + (255,)
    return rows


def black_trim(face, w, h):
    """Blackened iron: dark with a faint lighter top edge so stacked bands read apart."""
    rows = dark(face, w, h)
    if face not in ("up", "down"):
        rows[0] = [(70, 64, 58, 255)] * w
    return rows


def lens_face(x0, y1):
    """The lens rim seen from the front/back. Its two crossing cubes paint from one shared
    octagon (left edge x0, top y1), so where they overlap they show the same pixels: a bronze
    rim, a black ring inside it, and the dark socket the lens sits in."""
    def inside(gx, gy):
        dx, dy = abs(gx), abs(gy - 7)
        return dx < 3 and dy < 3 and not (dx > 2 and dy > 2)

    def depth(gx, gy):
        for d in range(4):
            if any(not inside(gx + ox, gy + oy) for ox, oy in ((d, 0), (-d, 0), (0, d), (0, -d), (d, d), (-d, -d), (d, -d), (-d, d))):
                return d
        return 4

    def paint(face, w, h):
        if face not in ("north", "south"):
            return bronze(face, w, h)
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                gx, gy = x0 + x + 0.5, y1 - y - 0.5
                d = depth(gx, gy)
                if d <= 1:
                    c = BRONZE_HI if gx < 0 and gy > 7 else (BRONZE_LO if gx > 0 and gy < 7 else BRONZE)
                elif d == 2:
                    c = DARK
                else:
                    c = (14, 70, 30)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def lens_glow(face, w, h):
    """The lens itself: pale centre, bright green, with a highlight top-left."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            r = max(abs(x - cx), abs(y - cy))
            if face in ("north", "south") and r < 0.8:
                c = (225, 255, 230)
            elif face in ("north", "south") and x <= 0.5 and y <= 1.5:
                c = (170, 255, 190)
            else:
                c = (70, 255, 120) if face in ("north", "south") else (40, 200, 85)
            row.append(c + (255,))
        rows.append(row)
    return rows


lantern = Model("power_lantern")
L = lantern.cube
# Base: black foot plate on four bronze feet, a riveted bronze band, then a black step.
for sx in (-1, 1):
    for sz in (-1, 1):
        L(f"foot_{sx}_{sz}", (min(sx * 6.5, sx * 4.5), 0, min(sz * 6.5, sz * 4.5)),
          (max(sx * 6.5, sx * 4.5), 1, max(sz * 6.5, sz * 4.5)), bronze)
L("base_plate", (-6, 1, -6), (6, 2, 6), black_trim)
L("base", (-6, 2, -6), (6, 3, 6), riveted)
L("base_step", (-5, 3, -5), (5, 4, 5), black_trim)
# The glass and its light, framed by four corner posts and a black band at each end.
L("glass", (-4, 4, -4), (4, 12, 4), glass)
L("glow_glass", (-4, 4, -4), (4, 12, 4), glass_glow, inflate=0.05)
for sx in (-1, 1):
    for sz in (-1, 1):
        x0, z0 = (4 if sx > 0 else -5), (4 if sz > 0 else -5)
        L(f"post_{sx}_{sz}", (x0, 4, z0), (x0 + 1, 12, z0 + 1), bronze)
# Round lens on the front and back: an octagonal bronze rim with the glowing lens standing out.
for side, z in (("front", -5), ("back", 4)):
    L(f"lens_rim_{side}_h", (-3, 5, z), (3, 9, z + 1), lens_face(-3, 9))
    L(f"lens_rim_{side}_v", (-2, 4, z), (2, 10, z + 1), lens_face(-2, 10))
    out = -0.5 if side == "front" else 0.5
    L(f"glow_lens_{side}_h", (-1.5, 6, z + out), (1.5, 8, z + 1 + out), lens_glow)
    L(f"glow_lens_{side}_v", (-1, 5.5, z + out), (1, 8.5, z + 1 + out), lens_glow)
# A ring on each side, standing off the glass on a short bracket.
for sx in (-1, 1):
    x0 = 5 if sx > 0 else -6
    xb = 4 if sx > 0 else -5
    n = "east" if sx > 0 else "west"
    L(f"ring_{n}_top", (x0, 10, -1.5), (x0 + 1, 11, 1.5), bronze)
    L(f"ring_{n}_bottom", (x0, 4, -1.5), (x0 + 1, 5, 1.5), bronze)
    L(f"ring_{n}_front", (x0, 5, -2.5), (x0 + 1, 10, -1.5), bronze)
    L(f"ring_{n}_back", (x0, 5, 1.5), (x0 + 1, 10, 2.5), bronze)
    L(f"ring_{n}_bracket", (xb, 7, -0.5), (xb + 1, 8, 0.5), black_trim)
# Top: bronze lip, black band, a stepped dome and a finial.
L("top_lip", (-6, 12, -6), (6, 13, 6), riveted)
L("top_band", (-5, 13, -5), (5, 14, 5), black_trim)
L("dome_low", (-4, 14, -4), (4, 15, 4), bronze)
L("dome_mid", (-3, 15, -3), (3, 16, 3), bronze)
L("dome_top", (-2, 16, -2), (2, 17, 2), black_trim)
L("finial", (-1, 17, -1), (1, 18, 1), bronze)
# Arched handle, pinned to the dome on each side.
for sx in (-1, 1):
    x0 = 4 if sx > 0 else -5
    n = "right" if sx > 0 else "left"
    L(f"handle_pin_{n}", (x0, 13.5, -1), (x0 + 1, 15.5, 1), black_trim)
    L(f"handle_{n}", (x0, 15.5, -0.5), (x0 + 1, 18.5, 0.5), bronze)
    L(f"handle_{n}_bend", (x0 - sx, 18.5, -0.5), (x0 - sx + 1, 19.5, 0.5), bronze)
L("handle_top", (-3, 19, -0.5), (3, 20, 0.5), bronze)
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
gem_stack(forged, [(5, 2), (4, 1), (3, 1), (2, 1)], 8)
forged.write()
