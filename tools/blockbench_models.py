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
# Optional model names to write (e.g. blast_drill); every model when left out.
ONLY = set(sys.argv[2:]) or None
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
        if ONLY is not None and self.name not in ONLY:
            return
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
# After J's keychain lantern: a ribbed green glass bottle that swells a little in the middle,
# a stepped brass base, a stepped brass cap with a knob and a loop handle, two brass bands
# wrapping the glass and a round ringed emblem on the front between them. Painted at 4 pixels
# per unit in clean flat colours: polished brass with a lit top edge and a shaded bottom edge,
# glass ribs with a pale crest, and no noise, scratches or wear. The lens centre (0, 8, -6) and
# handle top (y 20) are where LanternFirstPerson aims the ring and holds the lantern.
LD = 4  # texture pixels per unit
BRASS = rgb("#a8802e")
BRASS_HI = rgb("#e6c066")
BRASS_LO = rgb("#5e4416")
BRASS_DEEP = rgb("#3a280c")
CLEAR = (0, 0, 0, 0)


def mix(a, b, k):
    return tuple(clamp(a[i] + (b[i] - a[i]) * k) for i in range(3))


def brass_paint(groove=False, base=BRASS):
    """Polished brass: a pale top edge, a shaded bottom edge, a soft sheen down the left and
    (``groove``) an engraved line round the middle of the side faces."""
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                if face in ("up", "down"):
                    edge = min(x, y, w - 1 - x, h - 1 - y)
                    c = BRASS_HI if edge == 0 and (x == 0 or y == 0) else (BRASS_LO if edge == 0 else base)
                    if edge == 1:
                        c = mix(base, BRASS_HI, 0.3)
                else:
                    c = base
                    sheen = abs(x - w * 0.3) / max(w, 1)
                    if sheen < 0.08:
                        c = mix(c, BRASS_HI, 0.35)
                    if y == 0:
                        c = BRASS_HI
                    elif y == h - 1 and h > 2:
                        c = BRASS_LO
                    elif groove and h >= 6 and y == h // 2:
                        c = BRASS_DEEP
                    elif groove and h >= 6 and y == h // 2 + 1:
                        c = mix(base, BRASS_HI, 0.4)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


brass = brass_paint()
brass_grooved = brass_paint(groove=True)
brass_dark = brass_paint(base=mix(BRASS, BRASS_LO, 0.55))


def glass_ribs(face, w, h):
    """Lit green glass in ribs one unit apart: a pale crest, bright body and a deep groove. It
    is brightest in the middle of each face and has a pale reflection near the left edge.
    Painted bright, since glow covers what is behind it."""
    rows = []
    for y in range(h):
        p = y % LD
        rib = [(170, 255, 185), (90, 255, 130), (60, 225, 100), (22, 130, 52)][p]
        row = []
        for x in range(w):
            if face in ("up", "down"):
                c = (60, 225, 100)
            else:
                k = abs(x - (w - 1) / 2) / ((w - 1) / 2)
                c = mix(rib, (14, 90, 36), 0.5 * k * k)
                if LD <= x <= LD + 1 and p < 3:
                    c = mix(c, (225, 255, 230), 0.5)
            row.append(c + (255,))
        rows.append(row)
    return rows


def disc(face, w, h, fill):
    """Cuts a cube's faces round: the front and back keep a circle, the sides keep only the
    middle strip where the circle touches them."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            if face in ("north", "south"):
                r = math.hypot(x - cx, y - cy)
                row.append(fill(r, x - cx, y - cy, w / 2) if r <= w / 2 else CLEAR)
            elif face in ("east", "west"):
                row.append(BRASS_LO + (255,) if abs(y - cy) < h * 0.22 else CLEAR)
            else:
                row.append(BRASS + (255,) if abs(x - cx) < w * 0.22 else CLEAR)
        rows.append(row)
    return rows


def emblem(face, w, h):
    """The front emblem: a polished brass rim, dark green enamel with two fine lighter rings,
    then a brass inner ring round the socket the glowing lens sits in."""
    def fill(r, dx, dy, R):
        lit = dx + dy < 0
        if r > R - 2:
            c = BRASS_HI if lit else BRASS
        elif r > R - 2.6:
            c = BRASS_LO
        elif r > R - 7:
            ring = R - r
            c = (40, 110, 60) if abs(ring - 3.8) < 0.5 or abs(ring - 5.6) < 0.5 else (16, 58, 32)
        elif r > R - 8.5:
            c = BRASS_HI if lit else BRASS
        else:
            c = (10, 40, 20)
        return c + (255,)
    return disc(face, w, h, fill)


def lens(face, w, h):
    """The glowing lens in the middle of the emblem: pale core, bright green, a highlight."""
    def fill(r, dx, dy, R):
        if r < 1.3:
            c = (235, 255, 240)
        elif dx < -0.5 and dy < -0.5 and r < 2.7:
            c = (190, 255, 205)
        elif r > R - 1:
            c = (50, 215, 95)
        else:
            c = (95, 255, 140)
        return c + (255,)
    return disc(face, w, h, fill)


def cap_rings(face, w, h):
    """The cap's top: concentric brass steps, like the turned rings on the reference."""
    if face != "up":
        return brass(face, w, h)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            c = (BRASS_HI, BRASS, BRASS_LO, BRASS)[edge % 4]
            row.append(c + (255,))
        rows.append(row)
    return rows


def wire(face, w, h):
    """Round brass wire: a highlight line along the top, shade along the bottom."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            if face in ("up", "down"):
                t = x if h > w else y
                n = w if h > w else h
            else:
                t, n = (x, w) if h > w else (y, h)
            k = t / max(n - 1, 1)
            c = BRASS_HI if k < 0.3 else (BRASS if k < 0.75 else BRASS_LO)
            row.append(c + (255,))
        rows.append(row)
    return rows


lantern = Model("power_lantern", density=LD)
L = lantern.cube
# Base: a wide foot, a polished rim, a darker band and a lip the glass sits in.
L("base_foot", (-5, 0, -5), (5, 1, 5), brass)
L("base_rim", (-5.5, 1, -5.5), (5.5, 2, 5.5), brass)
L("base_band", (-5, 2, -5), (5, 3, 5), brass_dark)
L("base_lip", (-4.5, 3, -4.5), (4.5, 4, 4.5), brass)
# The glass bottle, swelling a little in the middle.
L("glow_glass_low", (-4, 4, -4), (4, 7, 4), glass_ribs)
L("glow_glass_mid", (-4.5, 7, -4.5), (4.5, 10, 4.5), glass_ribs)
L("glow_glass_high", (-4, 10, -4), (4, 13, 4), glass_ribs)
# Two brass bands wrap the glass, above and below the emblem.
for name, y in (("band_low", 6), ("band_high", 9.5)):
    L(f"{name}_front", (-5, y, -5), (5, y + 1, -4), wire)
    L(f"{name}_back", (-5, y, 4), (5, y + 1, 5), wire)
    L(f"{name}_left", (-5, y, -4), (-4, y + 1, 4), wire)
    L(f"{name}_right", (4, y, -4), (5, y + 1, 4), wire)
# The emblem on the front, and its lens.
L("emblem", (-2.5, 5.5, -6), (2.5, 10.5, -5), emblem)
L("glow_lens", (-1, 7, -6.4), (1, 9, -5.4), lens)
# Cap: a rim over the glass, a grooved collar, turned rings, a knob and a loop handle.
L("cap_rim", (-4.5, 13, -4.5), (4.5, 14, 4.5), brass)
L("cap", (-4, 14, -4), (4, 15, 4), brass_dark)
L("cap_ring", (-3.5, 15, -3.5), (3.5, 16, 3.5), cap_rings)
L("cap_top", (-2.5, 16, -2.5), (2.5, 17, 2.5), cap_rings)
L("knob", (-1, 17, -1), (1, 18, 1), brass)
L("handle_left", (-3, 17, -0.5), (-2, 19, 0.5), wire)
L("handle_right", (2, 17, -0.5), (3, 19, 0.5), wire)
L("handle_top", (-3, 19, -0.5), (3, 20, 0.5), wire)
lantern.write()

# ---- the Dark Lantern (Lab option): after the "Dark lantern" concept art ---------------------
# A rounded three-sided body that twists up its height like a spiral and pinches in at the
# waist, built from stacked ribs of dark jade with the lantern's light glowing between them:
# near white in the middle like light itself, green at the edges, with traces of yellow
# (fear) running through it and gold veins in the jade. Gold rims top and bottom, two gold
# bands round the waist with a round emblem on the front between them, a short neck and a
# triangular loop handle. Clean colours, no wear. Lens centre (0, 8, -4.45), handle top y 23;
# keep LanternFirstPerson's DARK look in step if these move.
JADE = (20, 84, 56)
JADE_HI = (96, 180, 130)
JADE_LO = (8, 40, 26)
FEAR = (255, 212, 84)
TWIST = 12  # degrees each layer turns from the one below; the waist (y 8) faces front


def jade_rib(layer):
    """Dark polished jade: a pale glint along the top edge, shade below, a thin gold vein."""
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                if face in ("up", "down"):
                    edge = min(x, y, w - 1 - x, h - 1 - y)
                    c = JADE_HI if edge == 0 else JADE
                else:
                    c = JADE_HI if y == 0 else (JADE_LO if y == h - 1 else JADE)
                    if 0 < y < h - 1 and (x + 2 * y + 5 * layer) % 31 == 0:
                        c = mix(FEAR, JADE, 0.25)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def light_core(level, layer):
    """The light between the ribs: near white through the middle of each face, green at the
    edges, shaded under the rib above, with yellow traces. Brightest at the waist (level 1)."""
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                k = abs(x - (w - 1) / 2) / max((w - 1) / 2, 1)
                if face in ("up", "down"):
                    k = max(k, abs(y - (h - 1) / 2) / max((h - 1) / 2, 1))
                c = mix((235, 255, 238), (60, 235, 110), min(1, k * 1.2))
                c = mix((30, 150, 70), c, 0.55 + 0.45 * level)
                if face not in ("up", "down") and y == 0:
                    c = mix(c, (10, 70, 30), 0.5)
                elif (x * 5 + y * 3 + 7 * layer) % 29 == 0:
                    c = FEAR
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


dark_model = Model("dark_lantern", density=LD)
DL = dark_model.cube


def tri_layer(name, y, s, paint, glow=False, angle=0.0):
    """One horizontal layer of the rounded three-sided body at scale s: 1-unit strips from the
    flat front to the narrow back, the first and last a step narrower to round the corners,
    all turned ``angle`` degrees about the body's middle."""
    depth = max(2, round(9 * s))
    front, back = 10 * s, 2 * s
    z0 = -depth / 2
    centre = [0, y, z0 + depth / 3]
    rot = [0, round(angle, 2), 0] if angle else None
    for i in range(depth):
        w = round(front + (back - front) * (i + 0.5) / depth)
        if i in (0, depth - 1):
            w -= 1
        w = max(w, 1)
        prefix = "glow_" if glow else ""
        DL(f"{prefix}{name}_{i}", (-w / 2, y, z0 + i), (w / 2, y + 1, z0 + i + 1), paint,
           rotation=rot, origin=centre if rot else None)


def waist(y):
    t = (y + 0.5 - 8.5) / 6.5
    return 0.72 + 0.28 * min(t * t, 1)


tri_layer("base_foot", 0, 1.0, brass)
tri_layer("base_rim", 1, 1.08, brass)
for y in range(2, 15):
    s = waist(y)
    turn = TWIST * (y - 8)
    if y in (6, 10):
        tri_layer(f"band_{y}", y, s + 0.1, wire, angle=turn)
    elif y % 2 == 0:
        tri_layer(f"rib_{y}", y, s, jade_rib(y), angle=turn)
    else:
        tri_layer(f"core_{y}", y, s - 0.08, light_core(1 - abs(y - 8.5) / 6.5, y), glow=True, angle=turn)
tri_layer("top_rim", 15, 1.08, brass)
tri_layer("cap", 16, 0.8, brass_dark)
DL("neck", (-1.5, 17, -1.5), (1.5, 18, 1.5), brass)
DL("neck_top", (-1, 18, -1), (1, 19, 1), cap_rings)
# The emblem on the front of the waist, and its lens.
DL("emblem", (-2, 6, -4), (2, 10, -3), emblem)
DL("glow_lens", (-1, 7, -4.4), (1, 9, -3.4), lens)
# Triangular loop handle, stepping in toward its top bar.
DL("handle_base", (-3.5, 19, -0.5), (3.5, 20, 0.5), wire)
for i, x in enumerate((3, 2.5, 2)):
    DL(f"handle_left_{i}", (-x - 0.5, 20 + i, -0.5), (-x + 0.5, 21 + i, 0.5), wire)
    DL(f"handle_right_{i}", (x - 0.5, 20 + i, -0.5), (x + 0.5, 21 + i, 0.5), wire)
DL("handle_top", (-2, 22, -0.5), (2, 23, 0.5), wire)
dark_model.write()

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
# The drill's colours: jade for the green ring, and molten obsidian for the red one (written as
# blast_drill_red.png on the same layout; CorpsTint picks it for a red ring).
DRILL_PALETTES = {
    "": dict(deep=(6, 62, 36), mid=(22, 120, 66), edge=(70, 200, 120), vein=(40, 160, 90),
             glow=(130, 255, 175), hot=(215, 255, 228)),
    "_red": dict(deep=(26, 6, 6), mid=(120, 18, 12), edge=(235, 70, 24), vein=(210, 52, 14),
                 glow=(255, 150, 50), hot=(255, 232, 170)),
    # The yellow ring's: dark amber, nearly black in the grooves, with a burning gold edge.
    "_yellow": dict(deep=(22, 16, 2), mid=(110, 78, 8), edge=(240, 190, 30), vein=(200, 150, 10),
                    glow=(255, 225, 70), hot=(255, 248, 200)),
}
DP = DRILL_PALETTES[""]


def drill_body(face, w, h):
    """The core: dark, with a pair of bright spiral grooves that wind round it as it spins."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = DP["deep"]
            if (x + 2 * y) % 9 in (0, 1):
                c = DP["vein"]
            elif (x + 2 * y) % 9 == 2:
                c = DP["mid"]
            v = drng.randint(-5, 5)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def drill_blade(face, w, h):
    """A flute: dark at the root, brightening to a polished edge, with a lit lip along the top."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            t = x / max(1, w - 1) if face in ("north", "south", "up", "down") else 0.5
            c = mix(DP["deep"], DP["mid"], min(1, t * 1.6)) if t < 0.6 else mix(DP["mid"], DP["edge"], (t - 0.6) / 0.4)
            if y == 0:
                c = mix(c, DP["edge"], 0.5)
            v = drng.randint(-6, 6)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def drill_glow(face, w, h):
    return [[(DP["hot"] if (x + y) % 5 == 0 else DP["glow"]) + (255,) for x in range(w)] for y in range(h)]


# A cone of stacked core slices with two helical flutes winding 1.5 turns from the hub to the tip,
# each flute built from thin slices that step round a few degrees at a time so it reads as one
# smooth spiral, with a glowing cutting lip along its outer edge. Tip at -Z, hub at +Z.
drill = Model("blast_drill")
D = drill.cube
LENGTH, CORE_SEG, FLUTE_SEG = 88, 4, 2
TURN = 540  # degrees each flute winds round over the length


def radius_at(z):
    """Core radius at depth z (0 at the hub, LENGTH at the tip)."""
    return max(2.0, 18 - 15.5 * (z / LENGTH) ** 1.15)


D("hub", (-20, -20, 0), (20, 20, 6), drill_body)
D("glow_core", (-4, -4, 6.05), (4, 4, 6.05), drill_glow)
D("glow_spoke_long", (-2, 4, 6.05), (2, 19, 6.05), drill_glow)
D("glow_spoke_short", (-1.5, 4, 6.05), (1.5, 12, 6.05), drill_glow, rotation=[0, 0, 140], origin=[0, 0, 6])
D("collar", (-21, -21, -3), (21, 21, 0), drill_body)
for i in range(LENGTH // CORE_SEG):
    z0, z1 = -CORE_SEG * (i + 1), -CORE_SEG * i
    r = round(radius_at(CORE_SEG * i + CORE_SEG / 2))
    D(f"core_{i}", (-r, -r, z0), (r, r, z1), drill_body, rotation=[0, 0, (i * 9) % 90], origin=[0, 0, (z0 + z1) / 2])
for i in range(LENGTH // FLUTE_SEG):
    z0, z1 = -FLUTE_SEG * (i + 1), -FLUTE_SEG * i
    depth = FLUTE_SEG * i + FLUTE_SEG / 2
    r = radius_at(depth)
    out = max(2, round(7 * (1 - depth / (LENGTH + 10))))
    thick = 3 if depth < LENGTH * 0.6 else 2
    root = max(0, round(r) - 2)
    for k in range(2):
        angle = (k * 180 + TURN * depth / LENGTH) % 360
        rot = [0, 0, round(angle, 1)]
        org = [0, 0, (z0 + z1) / 2]
        D(f"flute_{k}_{i}", (root, -thick / 2, z0), (round(r) + out, thick / 2, z1), drill_blade, rotation=rot, origin=org)
        D(f"glow_lip_{k}_{i}", (round(r) + out - 1, -thick / 2, z0), (round(r) + out, thick / 2, z1), drill_glow,
          inflate=0.05, rotation=rot, origin=org)
D("tip", (-2, -2, -LENGTH - 4), (2, 2, -LENGTH), drill_body)
D("glow_tip", (-1, -1, -LENGTH - 8), (1, 1, -LENGTH - 4), drill_glow)
if ONLY is None or "blast_drill" in ONLY:
    drill.write()
    # The red ring's drill: the same model, painted as molten obsidian.
    DP = DRILL_PALETTES["_red"]
    drill.texture().save(f"{A}/textures/entity/bb/blast_drill_red.png")
    # The yellow ring's: burning gold on dark amber.
    DP = DRILL_PALETTES["_yellow"]
    drill.texture().save(f"{A}/textures/entity/bb/blast_drill_yellow.png")


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


# ---- shared bits for the concept-sheet batteries (Torus Core, Compact Unit) -------------------
# Painted at LD pixels per unit like the keychain lantern. Round parts are three stacked boxes
# (w x d, d x w and a middle square) so the outline steps like Minecraft pixel art; their up and
# down faces are painted flat so the overlapping tops don't flicker.
LG = (34, 92, 46)       # green lantern metal
LG_HI = (96, 176, 98)
LG_LO = (14, 46, 22)
LG_DEEP = (8, 26, 12)


def ring_metal(base=LG, seam=4):
    """Dark green metal round a battery: a lit top edge, a shaded bottom edge, a soft sheen
    and a darker seam every ``seam`` units, like the panelled rings on the concept sheet."""
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                if face in ("up", "down"):
                    c = base
                else:
                    c = base
                    if abs(x - w * 0.3) / max(w, 1) < 0.1:
                        c = mix(c, LG_HI, 0.3)
                    if y == 0:
                        c = mix(base, LG_HI, 0.75)
                    elif y == h - 1 and h > 2:
                        c = mix(base, LG_DEEP, 0.7)
                    elif seam and x % (seam * LD) == seam * LD - 1:
                        c = mix(base, LG_DEEP, 0.55)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def logo_mask(w, h, cx, cy, R):
    """The lantern emblem in a face: a circle band with a bar across its top and bottom.
    Returns a function (x, y) -> 0 outside, 1 the pale emblem, 2 its dark outline."""
    def pale(x, y):
        r = math.hypot(x - cx, y - cy)
        ring = R * 0.52 <= r <= R * 0.86
        bar = R * 0.9 <= abs(y - cy) <= R * 1.18 and abs(x - cx) <= R * 0.95
        return ring or bar

    def at(x, y):
        if pale(x, y):
            return 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            if pale(x + dx, y + dy):
                return 2
        return 0
    return at


def lit_glass(logo_faces=("north", "south", "east", "west"), logo_w=None):
    """Glowing green battery glass, brightest through the middle and shaded under the rings
    at top and bottom, with the pale emblem (dark outlined) on the listed faces. ``logo_w``
    sizes the emblem to the visible width when frames cover the face's edges."""
    def paint(face, w, h):
        rows = []
        mask = None
        if face in logo_faces:
            vw = (logo_w or w / LD) * LD
            mask = logo_mask(w, h, (w - 1) / 2, (h - 1) / 2, min(vw, h) * 0.36)
        for y in range(h):
            row = []
            ky = abs(y - (h - 1) / 2) / max((h - 1) / 2, 1)
            for x in range(w):
                if face in ("up", "down"):
                    row.append((60, 225, 100, 255))
                    continue
                kx = abs(x - (w - 1) / 2) / max((w - 1) / 2, 1)
                c = mix((150, 255, 150), (40, 200, 80), min(1, kx * 0.9))
                c = mix(c, (18, 110, 44), max(0, ky - 0.7) * 2.2)
                if y % LD == 0:
                    c = mix(c, (30, 150, 60), 0.25)
                if mask:
                    m = mask(x, y)
                    if m == 1:
                        c = (236, 255, 222)
                    elif m == 2:
                        c = (16, 90, 38)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def lit_plate(face, w, h):
    """A glowing opening seen from above: pale in the middle, green toward its edge."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            k = max(abs(x - (w - 1) / 2), abs(y - (h - 1) / 2)) / max((w - 1) / 2, 1)
            row.append(mix((225, 255, 225), (50, 220, 95), min(1, k * 1.1)) + (255,))
        rows.append(row)
    return rows


def handle_bar(face, w, h):
    """02's chunky green handle: bright green, a pale top edge and a dark outline below."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = (52, 140, 62)
            if face == "up" or (face not in ("down",) and y == 0):
                c = (110, 200, 110)
            elif face == "down" or y == h - 1:
                c = (16, 52, 24)
            elif x == 0 or x == w - 1:
                c = (30, 96, 42)
            row.append(c + (255,))
        rows.append(row)
    return rows


def round_layer(cube, name, y0, y1, d, paint):
    """A stepped round layer about the Y axis, ``d`` units across."""
    cube(f"{name}_a", (-d / 2, y0, -(d - 2) / 2), (d / 2, y1, (d - 2) / 2), paint)
    cube(f"{name}_b", (-(d - 2) / 2, y0, -d / 2), ((d - 2) / 2, y1, d / 2), paint)
    cube(f"{name}_c", (-(d - 1) / 2, y0, -(d - 1) / 2), ((d - 1) / 2, y1, (d - 1) / 2), paint)


# ---- the Torus Core battery (concept 04 with 02's ring handle) -------------------------------
# Two panelled green torus rings and a lighter band make the base, a glowing glass cylinder with
# the emblem on all four sides makes the body, and a green collar and a small stepped cap carry
# 02's chunky arched handle in place of 04's top ring. Lens centre (0, 10, -4.5) on the front
# emblem; handle top y 24. Keep LanternFirstPerson's TORUS look in step if these move.
torus = Model("torus_lantern", density=LD)
T = torus.cube
dark_ring = ring_metal()
light_band = ring_metal(base=(70, 150, 74), seam=0)
round_layer(T, "foot_ring", 0, 2, 12, dark_ring)
round_layer(T, "mid_band", 2, 3, 11, light_band)
round_layer(T, "base_ring", 3, 5, 12, dark_ring)
round_layer(T, "glow_glass", 5, 15, 9, lit_glass())
round_layer(T, "collar", 15, 17, 11, dark_ring)
round_layer(T, "collar_lip", 17, 18, 9, light_band)
round_layer(T, "cap", 18, 19, 7, ring_metal(base=(24, 70, 34), seam=0))
T("glow_cap_light", (-2, 19.02, -2), (2, 19.02, 2), lit_plate)
# 02's handle: two posts on the cap, a stepped corner each side and a top bar.
for s in (-1, 1):
    T(f"handle_post_{s}", (min(s * 2, s * 4), 19, -1), (max(s * 2, s * 4), 22, 1), handle_bar)
    T(f"handle_corner_{s}", (min(s * 1, s * 3), 22, -1), (max(s * 1, s * 3), 23, 1), handle_bar)
T("handle_top", (-2, 23, -1), (2, 24, 1), handle_bar)
torus.write()


# ---- the Compact Unit (concept 07, my take) --------------------------------------------------
# A small square battery: a dark stone foot, green metal rims, four dark corner pillars framing
# glowing glass panels with the emblem on each side, a cap with a glowing top and a slim square
# loop handle. Lens centre (0, 7, -4) on the front panel; handle top y 18.
STONE = (44, 50, 44)


def dark_stone(face, w, h):
    """Dark mossy stone with a few cracks and a lit top edge."""
    rows = []
    rnd = random.Random(w * 31 + h + len(face))
    cracks = {(rnd.randrange(w), rnd.randrange(h)) for _ in range(max(1, w * h // 40))}
    for y in range(h):
        row = []
        for x in range(w):
            c = mix(STONE, (30, 60, 36), ((x * 7 + y * 13) % 5) / 12)
            if face != "up" and face != "down" and y == 0:
                c = mix(STONE, (110, 120, 108), 0.5)
            if any(abs(x - cx) + abs(y - cy) <= 1 and (x - cx == y - cy) for cx, cy in cracks):
                c = (20, 24, 20)
            row.append(c + (255,))
        rows.append(row)
    return rows


compact = Model("compact_lantern", density=LD)
C = compact.cube
C("base_stone", (-5, 0, -5), (5, 2, 5), dark_stone)
C("base_rim", (-4.5, 2, -4.5), (4.5, 3, 4.5), ring_metal(seam=0))
C("glow_glass", (-4, 3, -4), (4, 11, 4), lit_glass(logo_w=5))
for sx in (-1, 1):
    for sz in (-1, 1):
        C(f"pillar_{sx}_{sz}", (min(sx * 2.5, sx * 4.5), 3, min(sz * 2.5, sz * 4.5)),
          (max(sx * 2.5, sx * 4.5), 11, max(sz * 2.5, sz * 4.5)), ring_metal(base=(26, 60, 34), seam=0))
C("top_rim", (-4.5, 11, -4.5), (4.5, 12, 4.5), ring_metal(seam=0))
C("cap", (-3.5, 12, -3.5), (3.5, 13, 3.5), ring_metal(base=(24, 70, 34), seam=0))
C("glow_cap_light", (-2, 13.02, -2), (2, 13.02, 2), lit_plate)
for s in (-1, 1):
    C(f"handle_post_{s}", (min(s * 2, s * 3), 13, -0.5), (max(s * 2, s * 3), 17, 0.5), handle_bar)
C("handle_top", (-3, 17, -0.5), (3, 18, 0.5), handle_bar)
compact.write()


# ---- the Nebula battery (J's dark-glass concept) ---------------------------------------------
# A stacked green and gold cylinder round a chamber of very dark glass. The glass is its own
# model (nebula_glass, drawn see-through and full-bright) whose texture flows: NEBULA_FRAMES
# looping frames of slow smoky cloud and pale glacier-ice veins drifting over near-black, like a
# nebula. Inside hangs one small, very bright orb (cubes named "core"), which the mod swells
# into a sun while the lantern charges. Orb centre (0, 11.5, 0); cap top y 21.
NEBULA_FRAMES = 24
nebula = Model("nebula_lantern", density=LD)
N = nebula.cube
gold_ring = brass_paint()
round_layer(N, "foot", 0, 1, 12, ring_metal(base=(20, 56, 30), seam=0))
round_layer(N, "base", 1, 3, 11, dark_ring)
round_layer(N, "glow_base_light", 3, 5, 10, lit_glass(logo_faces=()))
round_layer(N, "gold_low", 5, 6, 12, gold_ring)
round_layer(N, "rim_low", 6, 7, 11, dark_ring)
round_layer(N, "rim_high", 16, 17, 11, dark_ring)
round_layer(N, "gold_high", 17, 18, 12, gold_ring)
round_layer(N, "top_ring", 18, 20, 11, ring_metal(base=(40, 108, 54)))
round_layer(N, "cap", 20, 21, 8, ring_metal(base=(24, 70, 34), seam=0))
N("glow_cap_light", (-2.5, 21.02, -2.5), (2.5, 21.02, 2.5), lit_plate)


def orb(face, w, h):
    """The orb: white-hot through the middle, a thin pale green edge."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            k = max(abs(x - (w - 1) / 2) / max((w - 1) / 2, 1), abs(y - (h - 1) / 2) / max((h - 1) / 2, 1))
            row.append(mix((255, 255, 250), (150, 255, 170), max(0, k - 0.45) * 1.8) + (255,))
        rows.append(row)
    return rows


N("core_a", (-1.5, 10.5, -1), (1.5, 12.5, 1), orb)
N("core_b", (-1, 10.5, -1.5), (1, 12.5, 1.5), orb)
N("core_c", (-1, 10, -1), (1, 13, 1), orb)
nebula.write()


def _vnoise3(seed):
    """Smooth periodic 3D value noise on a 32^3 lattice, sampled with numpy arrays."""
    import numpy as np
    g = np.random.default_rng(seed).random((32, 32, 32))

    def f(x, y, z):
        xi, yi, zi = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int)
        xf, yf, zf = x - xi, y - yi, z - zi
        u, v, w = (t * t * (3 - 2 * t) for t in (xf, yf, zf))
        out = 0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    c = g[(xi + dx) % 32, (yi + dy) % 32, (zi + dz) % 32]
                    out = out + c * (u if dx else 1 - u) * (v if dy else 1 - v) * (w if dz else 1 - w)
        return out
    return f


_N1, _N2, _N3 = _vnoise3(1), _vnoise3(2), _vnoise3(3)


def _fbm(n, x, y, z, octaves=4):
    s, a, tot = 1.0, 0.5, 0
    for _ in range(octaves):
        tot = tot + a * n(x * s, y * s, z * s)
        s, a = s * 2.03, a * 0.5
    return tot


def nebula_field(x, y, z, t):
    """RGBA (numpy, 0..255) of the glass at world points x, y, z (units) and loop time t in [0, 1).
    Two copies of the field drift upward and are cross-faded so the loop is seamless."""
    import numpy as np
    def at(tt):
        k = 0.17
        X, Y, Z = x * k, y * k - tt * 1.2, z * k
        smoke = _fbm(_N1, X + 0.4 * tt, Y, Z, 5)
        warp = _fbm(_N2, X * 1.3, Y * 1.3 + 3, Z * 1.3, 3)
        ice = 1 - np.abs(_fbm(_N3, X * 1.6 + warp * 1.4, Y * 0.9 + warp, Z * 1.6, 4) * 2 - 1)
        return smoke, ice, warp
    s1, i1, w1 = at(t)
    s2, i2, w2 = at(t - 1)
    smoke, ice, warp = s1 * (1 - t) + s2 * t, i1 * (1 - t) + i2 * t, w1 * (1 - t) + w2 * t
    base = np.array([3, 7, 9], float)
    cloud = np.clip((smoke - 0.44) * 2.4, 0, 1)[..., None] ** 1.3
    tint = np.clip((warp - 0.5) * 4, 0, 1)[..., None]
    cloud_col = np.array([10, 62, 42], float) * (1 - tint) + np.array([34, 20, 64], float) * tint
    veins = np.clip((ice - 0.93) * 14, 0, 1) ** 1.5
    col = base + cloud * cloud_col + veins[..., None] * np.array([70, 190, 150], float)
    # A few faint specks, like far stars in the smoke.
    h = np.sin(np.floor(x * LD) * 12.9898 + np.floor(y * LD) * 78.233 + np.floor(z * LD) * 37.719) * 43758.5453
    stars = ((h - np.floor(h)) > 0.992)[..., None]
    col = np.where(stars, np.array([150, 230, 200], float), col)
    alpha = 108 + 70 * cloud[..., 0] + 80 * veins
    return np.concatenate([np.clip(col, 0, 255), np.clip(alpha, 0, 255)[..., None]], -1)


NEBULA_T = [0.0]  # the frame being painted


def nebula_glass(frm, to, keep_faces):
    """Paints one glass box: its outer faces with the flowing nebula in world space; the faces
    that sit inside the other glass box are left clear so the see-through glass never doubles."""
    import numpy as np
    def paint(face, w, h):
        if face not in keep_faces:
            # The long faces of each box hide inside the other box except for their outer 1-unit ends.
            if face in ("up", "down") or face not in {"north", "south", "east", "west"}:
                return [[CLEAR] * w for _ in range(h)]
        u = (np.arange(w) + 0.5) / LD
        v = (np.arange(h) + 0.5) / LD
        U, V = np.meshgrid(u, v)
        Y = to[1] - V
        if face == "north":
            X, Z = to[0] - U, np.full_like(U, frm[2])
        elif face == "south":
            X, Z = frm[0] + U, np.full_like(U, to[2])
        elif face == "east":
            X, Z = np.full_like(U, to[0]), to[2] - U
        else:
            X, Z = np.full_like(U, frm[0]), frm[2] + U
        px = nebula_field(X, Y, Z, NEBULA_T[0])
        rows = []
        for yy in range(h):
            row = []
            for xx in range(w):
                inner = face not in keep_faces and LD <= xx < w - LD
                row.append(CLEAR if inner else tuple(int(c) for c in px[yy, xx]))
            rows.append(row)
        return rows
    return paint


glass = Model("nebula_glass", density=LD)
GD = 10
ga = ((-GD / 2, 7, -(GD - 2) / 2), (GD / 2, 16, (GD - 2) / 2))
gb = ((-(GD - 2) / 2, 7, -GD / 2), ((GD - 2) / 2, 16, GD / 2))
glass.cube("glass_a", *ga, nebula_glass(*ga, keep_faces=("east", "west")))
glass.cube("glass_b", *gb, nebula_glass(*gb, keep_faces=("north", "south")))
if ONLY is None or "nebula_glass" in ONLY:
    glass.write()
    # The flowing frames (same layout), for the held lantern, and a strip for the item model.
    frames = []
    for i in range(NEBULA_FRAMES):
        NEBULA_T[0] = i / NEBULA_FRAMES
        im = glass.texture()
        im.save(f"{A}/textures/entity/bb/nebula_glass_f{i}.png")
        frames.append(im)
    NEBULA_T[0] = 0.0
    strip = Image.new("RGBA", (frames[0].width, frames[0].height * len(frames)))
    for i, im in enumerate(frames):
        strip.paste(im, (0, i * im.height))
    os.makedirs(f"{A}/textures/block", exist_ok=True)
    strip.save(f"{A}/textures/block/nebula_glass.png")
    with open(f"{A}/textures/block/nebula_glass.png.mcmeta", "w") as f:
        json.dump({"animation": {"frametime": 3, "interpolate": True}}, f, indent="\t")


# ---- the Ring Forge (green): after J's "Ring Forge" card ----------------------------------------
# A stepped base of dark mossy stone, gold trim and panelled green metal, with a dark frame and
# corner posts round a glowing well. Above it float (drawn by RingForgeRenderer, bobbing): a
# glowing core, a hard-light port on each side of it facing in, and the lantern emblem standing
# upright, always turned to the viewer, its opening full of endless light (forge_light frames,
# rings of light falling inward). ring_forge_display is everything in one piece for the item.
# Units: 1 = 1/16 block, the base fills the block (x, z -8..8, y 0..11).
FORGE_FRAMES = 16
FORGE_CORE_Y, FORGE_PORT_R, FORGE_EMBLEM_Y = 15, 6.5, 23
DARK_FRAME = ring_metal(base=(30, 40, 34), seam=0)


def forge_base(cube):
    cube("base_stone", (-8, 0, -8), (8, 3, 8), dark_stone)
    cube("base_trim", (-7.5, 3, -7.5), (7.5, 4, 7.5), brass)
    cube("body", (-7, 4, -7), (7, 7, 7), dark_ring)
    cube("gold_band", (-7.5, 7, -7.5), (7.5, 8, 7.5), brass_grooved)
    cube("frame_n", (-7, 8, -7), (7, 10, -5), DARK_FRAME)
    cube("frame_s", (-7, 8, 5), (7, 10, 7), DARK_FRAME)
    cube("frame_w", (-7, 8, -5), (-5, 10, 5), DARK_FRAME)
    cube("frame_e", (5, 8, -5), (7, 10, 5), DARK_FRAME)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cube(f"post_{sx}_{sz}", (min(sx * 4, sx * 7), 10, min(sz * 4, sz * 7)),
                 (max(sx * 4, sx * 7), 12, max(sz * 4, sz * 7)), dark_stone)
    cube("glow_well", (-5, 8.02, -5), (5, 8.02, 5), lit_plate)
    cube("glow_seat", (-2, 8, -2), (2, 9, 2), lit_plate)


def forge_core(cube, y=0.0):
    cube("glow_core_a", (-2.5, y - 2, -2), (2.5, y + 2, 2), orb)
    cube("glow_core_b", (-2, y - 2, -2.5), (2, y + 2, 2.5), orb)
    cube("glow_core_c", (-2, y - 2.5, -2), (2, y + 2.5, 2), orb)


def port_face(face, w, h):
    """A port's frame: dark metal with a gold rim on its front and back."""
    if face in ("north", "south"):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                edge = min(x, y, w - 1 - x, h - 1 - y)
                c = BRASS_HI if edge == 0 else (BRASS if edge < LD // 2 else (110, 255, 145))
                row.append(c + (255,))
            rows.append(row)
        return rows
    return [[(70, 220, 110, 255)] * w for _ in range(h)]


def forge_port(cube, cx=0.0, cy=0.0, cz=0.0, along_x=False):
    """One port facing along Z (or X): an open 4x4 frame of hard light, 1 deep, gold-rimmed."""
    def bar(name, x0, x1, y0, y1, paint):
        if along_x:
            cube(name, (cx - 0.5, cy + y0, cz + x0), (cx + 0.5, cy + y1, cz + x1), paint)
        else:
            cube(name, (cx + x0, cy + y0, cz - 0.5), (cx + x1, cy + y1, cz + 0.5), paint)
    # An open frame, so the core shows through it, with a glowing lining round the opening.
    bar("glow_port_top", -2, 2, 1, 2, port_face)
    bar("glow_port_bottom", -2, 2, -2, -1, port_face)
    bar("glow_port_left", -2, -1, -1, 1, port_face)
    bar("glow_port_right", 1, 2, -1, 1, port_face)


EMBLEM_ROWS = [  # top row first, 1 unit per cell, centred on (0, 0)
    "#########",
    "..#####..",
    ".##...##.",
    ".#.....#.",
    ".#.....#.",
    ".#.....#.",
    ".##...##.",
    "..#####..",
    "#########",
]


def emblem_rows():
    """The upright emblem as (x0, x1, y0) runs in the XY plane: a ring with a bar over and under it."""
    spans = []
    for i, row in enumerate(EMBLEM_ROWS):
        y0 = 3.5 - i
        x = 0
        while x < len(row):
            if row[x] == "#":
                x1 = x
                while x1 < len(row) and row[x1] == "#":
                    x1 += 1
                spans.append((x - 4.5, x1 - 4.5, y0))
                x = x1
            else:
                x += 1
    return spans


def emblem_glow(face, w, h):
    """The emblem's hard light: bright green, a pale top edge and a deeper bottom edge."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = (110, 255, 145) if face in ("north", "south", "up") else (60, 210, 100)
            row.append(c + (255,))
        rows.append(row)
    return rows


def forge_emblem(cube, cy=0.0, depth=1.0):
    for i, (x0, x1, y0) in enumerate(emblem_rows()):
        cube(f"glow_emblem_{i}", (x0, cy + y0, -depth / 2), (x1, cy + y0 + 1, depth / 2), emblem_glow)


FORGE_T = [0.0]


def forge_light(face, w, h):
    """Endless light: rings of light falling inward to a white-hot middle; FORGE_T moves them."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            r = math.hypot(x - cx, y - cy) / (w / 2)
            if r > 1.05:
                row.append(CLEAR)
                continue
            # Rings crowd together toward the middle, like looking down a tunnel.
            depth = 1 / max(r, 0.08)
            wave = 0.5 + 0.5 * math.cos(2 * math.pi * (depth * 0.9 + FORGE_T[0]))
            core = max(0.0, 1 - r * 2.2)
            c = mix((40, 200, 80), (170, 255, 190), wave * 0.8)
            c = mix(c, (255, 255, 250), core)
            row.append(c + (255,))
        rows.append(row)
    return rows


base = Model("ring_forge", density=LD)
forge_base(base.cube)
base.write()
core_m = Model("ring_forge_core", density=LD)
forge_core(core_m.cube)
core_m.write()
port_m = Model("ring_forge_port", density=LD)
forge_port(port_m.cube)
port_m.write()
emb_m = Model("ring_forge_emblem", density=LD)
forge_emblem(emb_m.cube)
emb_m.write()
light_m = Model("ring_forge_light", density=8)
light_m.cube("glow_light", (-2.5, -2.5, 0), (2.5, 2.5, 0), forge_light)
if ONLY is None or "ring_forge_light" in ONLY:
    light_m.write()
    frames = []
    for i in range(FORGE_FRAMES):
        FORGE_T[0] = i / FORGE_FRAMES
        im = light_m.texture()
        im.save(f"{A}/textures/entity/bb/ring_forge_light_f{i}.png")
        frames.append(im)
    FORGE_T[0] = 0.0
    strip = Image.new("RGBA", (frames[0].width, frames[0].height * len(frames)))
    for i, im in enumerate(frames):
        strip.paste(im, (0, i * im.height))
    strip.save(f"{A}/textures/block/ring_forge_light.png")
    with open(f"{A}/textures/block/ring_forge_light.png.mcmeta", "w") as f:
        json.dump({"animation": {"frametime": 2, "interpolate": True}}, f, indent="\t")

# Everything in one piece for the item model (the light is added from ring_forge_light).
display = Model("ring_forge_display", density=LD)
forge_base(display.cube)
forge_core(display.cube, FORGE_CORE_Y)
for name, (cx, cz, ax) in {"n": (0, -FORGE_PORT_R, False), "s": (0, FORGE_PORT_R, False),
                           "w": (-FORGE_PORT_R, 0, True), "e": (FORGE_PORT_R, 0, True)}.items():
    forge_port(lambda n, a, b, p, _s=name: display.cube(f"{n}_{_s}", a, b, p), cx, FORGE_CORE_Y, cz, ax)
forge_emblem(display.cube, FORGE_EMBLEM_Y)
display.write()


# ---- the big batteries: the Great Power Battery (green) and the Lava Font (red) ----------------
# Both are tables with a basin on top; the liquid in the basin is added by bbmodel_json.py with
# its own animated texture (tools/font_liquid_textures.py), at y 13.5 over x, z -6..6.
# The Great Power Battery: a dark stone foot, gold trim, a glowing glass column with the emblem
# on all four sides between dark corner pillars, and a wide green table top with a raised rim.
great = Model("great_battery", density=LD)
G_ = great.cube
G_("foot", (-8, 0, -8), (8, 2, 8), dark_stone)
G_("trim", (-7.5, 2, -7.5), (7.5, 3, 7.5), brass)
G_("plinth", (-6, 3, -6), (6, 4, 6), dark_ring)
G_("glow_column", (-4, 4, -4), (4, 10, 4), lit_glass(logo_w=6))
for sx in (-1, 1):
    for sz in (-1, 1):
        G_(f"pillar_{sx}_{sz}", (min(sx * 3, sx * 5), 4, min(sz * 3, sz * 5)),
           (max(sx * 3, sx * 5), 10, max(sz * 3, sz * 5)), ring_metal(base=(26, 60, 34), seam=0))
G_("table", (-8, 10, -8), (8, 12, 8), dark_ring)
G_("table_gold", (-7.5, 12, -7.5), (7.5, 13, 7.5), brass_grooved)
G_("rim_n", (-8, 13, -8), (8, 15, -6), ring_metal(seam=0))
G_("rim_s", (-8, 13, 6), (8, 15, 8), ring_metal(seam=0))
G_("rim_w", (-8, 13, -6), (-6, 15, 6), ring_metal(seam=0))
G_("rim_e", (6, 13, -6), (8, 15, 6), ring_metal(seam=0))
great.write()

# The Lava Font: a red lantern birdbath of blackstone with crimson veins and gold bands: a
# square foot, a round stem, a wide bowl and a rim round a pool of red lava.
BLACKSTONE = (34, 28, 32)


def blackstone(face, w, h):
    """Dark blackstone with thin crimson veins and a lit top edge."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = mix(BLACKSTONE, (52, 40, 46), ((x * 5 + y * 11) % 7) / 14)
            if face not in ("up", "down") and y == 0:
                c = mix(BLACKSTONE, (110, 96, 100), 0.5)
            if (x * 3 + y * 7 + len(face)) % 37 == 0 or (x * 7 - y * 3) % 53 == 0:
                c = (150, 20, 26)
            row.append(c + (255,))
        rows.append(row)
    return rows


font = Model("lava_font", density=LD)
F_ = font.cube
F_("foot", (-6, 0, -6), (6, 2, 6), blackstone)
F_("foot_gold", (-5, 2, -5), (5, 3, 5), brass)
round_layer(F_, "stem", 3, 9, 6, blackstone)
round_layer(F_, "stem_band", 5, 6, 7, brass)
round_layer(F_, "bowl_low", 9, 11, 12, blackstone)
F_("bowl", (-8, 11, -8), (8, 13, 8), blackstone)
F_("rim_n", (-8, 13, -8), (8, 15, -6), blackstone)
F_("rim_s", (-8, 13, 6), (8, 15, 8), blackstone)
F_("rim_w", (-8, 13, -6), (-6, 15, 6), blackstone)
F_("rim_e", (6, 13, -6), (8, 15, 6), blackstone)
for n, frm, to in (("n", (-8, 15, -8), (8, 16, -7)), ("s", (-8, 15, 7), (8, 16, 8)),
                   ("w", (-8, 15, -7), (-7, 16, 7)), ("e", (7, 15, -7), (8, 16, 7))):
    F_(f"rim_gold_{n}", frm, to, brass)
font.write()
