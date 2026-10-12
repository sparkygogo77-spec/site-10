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

    def cube(self, name, frm, to, paint, inflate=0.0, rotation=None, origin=None, share=None):
        """rotation is Blockbench's [x, y, z] degrees about origin (default: the cube's centre).
        ``share`` names an earlier cube of the same size whose texture this one reuses (e.g. a
        glow copy of a solid cube), so the atlas holds it once."""
        size = [to[i] - frm[i] for i in range(3)]
        # Sizes are whole texture pixels (a whole unit at density 1), so every face lands on whole
        # pixels of the atlas.
        k = self.density
        assert all(abs(s * k - round(s * k)) < 1e-6 and s >= 0 for s in size), (name, size)
        size = [round(s * k) / k for s in size]
        size = [int(s) if s == int(s) else s for s in size]
        self.cubes.append(dict(name=name, frm=list(frm), to=list(to), size=size,
                               paint=paint, inflate=inflate, rotation=rotation, origin=origin, share=share))

    def pack(self):
        """Shelf-pack each cube's box-UV net (2(w+d) x (d+h)) into the smallest square atlas."""
        for side in (16, 32, 64, 128, 256, 512, 1024):
            x = y = shelf = 0
            ok = True
            for c in sorted(self.cubes, key=lambda c: -(c["size"][2] + c["size"][1])):
                if c.get("share"):
                    continue
                w, h, d = c["size"]
                nw, nh = math.ceil(2 * (w + d) - 1e-9), math.ceil(d + h - 1e-9)
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
                byname = {c["name"]: c for c in self.cubes}
                for c in self.cubes:
                    if c.get("share"):
                        c["uv"] = byname[c["share"]]["uv"]
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
            if c.get("share"):
                continue
            for face, (u0, v0, u1, v1) in self.faces(c).items():
                w, h = round((u1 - u0) * k), round((v1 - v0) * k)
                if w <= 0 or h <= 0:
                    continue
                rows = c["paint"](face, w, h)
                x0, y0 = round(u0 * k), round(v0 * k)
                for y in range(h):
                    for x in range(w):
                        px[x0 + x, y0 + y] = rows[y][x]
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
# glass ribs with a pale crest, and no noise, scratches or wear. These painters stay for the
# parts other models share; the keychain lantern itself is now built in the Classic style below.
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


# ---- the Dark Lantern (Lab option): a twisted square tower, after the S7 Green Lantern lanterns ---
# Square plates of dark jade stacked with the lantern's light between them (near white like light
# itself, green at its edges), each layer turned TWIST degrees from the one below, so the stack
# twists a quarter turn and more from foot to cap. Every piece turns about the middle, so the
# layers stay centred. A square belt in the middle faces the front, between two gold bands (fear's
# yellow), with the ring's port on it: a gold rim round the lantern's light. Port light front
# (0, 9, -4.85), handle top y 26; keep LanternFirstPerson's DARK look in step if these move. The
# model itself is built near the end of this file, in the Classic style.
JADE = (22, 92, 60)
JADE_HI = (110, 196, 146)
JADE_LO = (8, 42, 27)
FEAR = (255, 208, 70)
TWIST = 9  # degrees each layer turns from the one below


def jade(layer, base=JADE, vein=True):
    """Polished dark jade: a pale glint on the top edge, shade on the bottom, a rare gold vein."""
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                edge = min(x, y, w - 1 - x, h - 1 - y)
                if face in ("up", "down"):
                    c = JADE_HI if edge == 0 and face == "up" else base
                else:
                    c = mix(JADE_HI, base, 0.35) if y == 0 else (JADE_LO if y == h - 1 else base)
                if vein and 0 < y < h - 1 and (2 * x + 3 * y + 11 * layer) % 37 == 0:
                    c = mix(FEAR, base, 0.15)
                v = random.randint(-4, 4)
                row.append(tuple(clamp(ch + v) for ch in c) + (255,))
            rows.append(row)
        return rows
    return paint


def core(layer):
    """The light: near white through the middle of each face, green at the edges, a few yellow
    sparks. Painted bright since Blockbench glow is not additive."""
    def paint(face, w, h):
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                k = abs(x - (w - 1) / 2) / max((w - 1) / 2, 1)
                if face in ("up", "down"):
                    k = max(k, abs(y - (h - 1) / 2) / max((h - 1) / 2, 1))
                c = mix((240, 255, 242), (70, 240, 118), min(1, k * k * 1.3))
                if (x * 7 + y * 5 + 13 * layer) % 41 == 0:
                    c = (255, 236, 140)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def port_light(face, w, h):
    """The socket's floor: the lantern emblem in light, a white disc in a green ring."""
    rows = []
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        row = []
        for x in range(w):
            r = math.hypot(x - cx, y - cy) / max(cx, 1)
            if face != "north":
                c = (80, 245, 125)
            elif r < 0.42:
                c = (245, 255, 245)
            elif r < 0.62:
                c = (60, 225, 105)
            elif r < 0.8:
                c = (200, 255, 210)
            else:
                c = (90, 250, 135)
            row.append(c + (255,))
        rows.append(row)
    return rows



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


dark_ring = ring_metal()
light_band = ring_metal(base=(70, 150, 74), seam=0)




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




# ---- the Nebula battery (J's dark-glass concept) ---------------------------------------------
# A stacked green and gold cylinder round a chamber of very dark glass. The glass is its own
# model (nebula_glass, drawn see-through and full-bright) whose texture flows: NEBULA_FRAMES
# looping frames of slow smoky cloud and pale glacier-ice veins drifting over near-black, like a
# nebula. Inside hangs one small, very bright orb (cubes named "core"), which the mod swells
# into a sun while the lantern charges. Orb centre (0, 11.5, 0); cap top y 21. The round metal
# and glass are built in the Classic style near the end of this file (nebula_round).
NEBULA_FRAMES = 24
nebula = Model("nebula_lantern", density=LD)
N = nebula.cube
gold_ring = brass_paint()
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


# ---- the Infinity Stones and the Infinity Gauntlet --------------------------------------------
# Each stone is a faceted oval gem, 8 wide, 9 tall and 6 deep, centred on x/z with its foot at
# y 0. Every gem cube is named "glow..." so the whole stone shines full-bright, painted in bright
# flat facets (Blockbench glow is not additive, so there are no faint halo boxes). The Time Stone
# sits in a gold Eye of Agamotto frame. The gauntlet stands fist up with the back of the hand
# facing north (-Z): the Time Stone sets into the big socket on the back of the hand, the Soul
# Stone into the socket on the thumb, and four empty knuckle sockets wait for the other stones.
STONE_D = 4
SOUL = (rgb("#ff8a1c"), rgb("#ffe07a"), rgb("#b8420a"))
TIME = (rgb("#2ee86a"), rgb("#c4ffd6"), rgb("#0a7a34"))
FACE_LIGHT = {"up": 1.12, "north": 1.0, "west": 0.94, "south": 0.9, "east": 0.84, "down": 0.72}


def gem_paint(colours):
    """Bright facets: each face split by its diagonals into four facets, lit from the top left,
    with pale facet lines, a darker rim and a white glint."""
    base, hi, lo = colours

    def paint(face, w, h):
        rows = []
        k = FACE_LIGHT[face]
        line = 1.0 / max(w, h)
        for y in range(h):
            row = []
            for x in range(w):
                u, v = (x + 0.5) / w, (y + 0.5) / h
                a, b = u - v, u + v - 1
                if a > 0 and b < 0:
                    c = mix(base, hi, 0.45)
                elif a < 0 and b < 0:
                    c = mix(base, hi, 0.15)
                elif a > 0 and b > 0:
                    c = mix(base, lo, 0.2)
                else:
                    c = mix(base, lo, 0.4)
                if abs(a) < line or abs(b) < line:
                    c = mix(c, hi, 0.5)
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    c = mix(c, lo, 0.55)
                c = tuple(clamp(ch * k) for ch in c)
                if face in ("north", "south", "up") and 0.18 < u < 0.38 and 0.14 < v < 0.3:
                    c = mix(c, (255, 255, 255), 0.7)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def stone_socket(colours):
    """A small round stone for a gauntlet socket: cut-out corners, bright facets."""
    facets = gem_paint(colours)

    def paint(face, w, h):
        rows = facets(face, w, h)
        if face in ("north", "south"):
            for y in range(h):
                for x in range(w):
                    dx, dy = (x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5
                    if dx * dx + dy * dy > 0.25:
                        rows[y][x] = CLEAR
        return rows
    return paint


def gem(m, colours, dz=0.0):
    """The faceted oval gem; dz moves it forward (toward -Z) for settings."""
    p = gem_paint(colours)
    G = lambda name, f, t: m.cube(name, (f[0], f[1], f[2] - dz), (t[0], t[1], t[2] - dz), p)
    G("glow_body", (-3, 2, -2), (3, 7, 2))
    G("glow_column", (-2, 1, -1.5), (2, 8, 1.5))
    G("glow_wide", (-4, 3, -1), (4, 6, 1))
    G("glow_crown", (-2, 3, -3), (2, 6, 3))
    G("glow_foot", (-1, 0, -1), (1, 1, 1))
    G("glow_tip", (-1, 8, -1), (1, 9, 1))


def clean_gold(base=GOLD, hi=GOLD_HI, lo=GOLD_LO, panel=False):
    """Polished gold in clean flat colours: a lit top and left edge, a shaded bottom and right
    edge, and (panel) a recessed line one pixel in from the rim."""
    def paint(face, w, h):
        rows = []
        k = FACE_LIGHT[face]
        for y in range(h):
            row = []
            for x in range(w):
                if y == 0 or x == 0:
                    c = hi
                elif y == h - 1 or x == w - 1:
                    c = lo
                elif panel and w > 6 and h > 6 and (x in (2, w - 3) and 2 <= y <= h - 3 or y in (2, h - 3) and 2 <= x <= w - 3):
                    c = mix(base, lo, 0.6)
                else:
                    c = mix(base, hi, 0.25 * (1 - y / max(1, h - 1)))
                row.append(tuple(clamp(ch * k) for ch in c) + (255,))
            rows.append(row)
        return rows
    return paint


def socket_paint(face, w, h):
    """A gold socket rim around a dark empty hollow (on the north face)."""
    rim = clean_gold(base=mix(GOLD, GOLD_LO, 0.4))(face, w, h)
    if face == "north" and w >= 8 and h >= 8:
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                d = ((x + 0.5) / w - 0.5) ** 2 + ((y + 0.5) / h - 0.5) ** 2
                rim[y][x] = (mix(DARK, GOLD_EDGE, 0.5) if d > 0.09 else DARK) + (255,)
    return rim


soul = Model("soul_stone", density=STONE_D)
gem(soul, SOUL)
soul.write()

time_stone = Model("time_stone", density=STONE_D)
gem(time_stone, TIME)
eye_gold = clean_gold()
for name, frm, to in (("frame_l", (-6, 2, -1), (-5, 7, 1)), ("frame_tl1", (-5, 7, -1), (-4, 8, 1)),
                      ("frame_tl2", (-4, 8, -1), (-3, 9, 1)), ("frame_t", (-3, 9, -1), (3, 10, 1)),
                      ("frame_tr2", (3, 8, -1), (4, 9, 1)), ("frame_tr1", (4, 7, -1), (5, 8, 1)),
                      ("frame_r", (5, 2, -1), (6, 7, 1)), ("frame_br1", (4, 1, -1), (5, 2, 1)),
                      ("frame_br2", (3, 0, -1), (4, 1, 1)), ("frame_b", (-3, -1, -1), (3, 0, 1)),
                      ("frame_bl2", (-4, 0, -1), (-3, 1, 1)), ("frame_bl1", (-5, 1, -1), (-4, 2, 1)),
                      ("frame_loop", (-1, 10, -0.5), (1, 12, 0.5))):
    time_stone.cube(name, frm, to, eye_gold)
time_stone.write()

gauntlet = Model("infinity_gauntlet", density=STONE_D)
U = gauntlet.cube
g_gold = clean_gold()
g_panel = clean_gold(panel=True)
g_dark = clean_gold(base=mix(GOLD, GOLD_LO, 0.5), hi=GOLD, lo=GOLD_EDGE)
U("cuff_flare", (-6, 0, -5), (6, 1, 5), g_dark)
U("cuff", (-5, 1, -4), (5, 5, 4), g_panel)
U("cuff_rim", (-6, 4, -5), (6, 6, 5), g_dark)
U("hand", (-5, 6, -3), (5, 14, 3), g_gold)
U("back_plate", (-4, 7, -4), (4, 13, -3), g_panel)
U("socket_time", (-3, 7.5, -5), (3, 12.5, -4), socket_paint)
U("glow_time", (-2, 8, -6), (2, 12, -5), stone_socket(TIME))
for i, (x0, tall) in enumerate(((-5, 2), (-2.333, 3), (0.333, 3), (3, 2))):
    U(f"finger{i}_base", (x0, 14, -2.5), (x0 + 2, 17, 0.5), g_gold)
    U(f"finger{i}_mid", (x0, 17, -3), (x0 + 2, 17 + tall, 0), g_gold)
    U(f"finger{i}_tip", (x0, 17 + tall, -3.5), (x0 + 2, 18 + tall, -1.5), g_dark)
    U(f"socket_knuckle{i}", (x0 + 0.5, 13, -4), (x0 + 1.5, 14, -3), socket_paint)
U("thumb_base", (5, 7, -2), (8, 11, 1), g_gold)
U("thumb_tip", (6, 11, -2.5), (8, 14, 0.5), g_dark)
U("socket_soul", (5, 7.5, -3), (8, 10.5, -2), socket_paint)
U("glow_soul", (5.5, 8, -4), (7.5, 10, -3), stone_socket(SOUL))
gauntlet.write()


# ---- the Stone Lantern (Lab option, the default): an ancient sealed battery ------------------
# After J's two face sheets, but closed: J found the open emblem pane read as an eye. A square
# shrine of green-painted weathered stone with no window at all: a stepped plinth with a sill
# front and back, four block-coursed corner pillars half a unit proud of solid panels, a lintel
# and overhanging cornice under a dark plank lid, a square stone handle with one post wrapped in
# moss, moss over the cornice and down the front. The light is sealed inside and only shows
# through cracks: every panel, pillar and band has branching fissures, painted as deep shadow in
# the stone and as bright light on paper-thin "glow_crack" planes just in front of it. At rest
# LanternFirstPerson keeps those nearly dark (a faint seep); as the lantern charges they blaze,
# like a sun in a bottle. The placed block and item show them lit. Painted at 6 pixels per unit
# with its own random streams. Lens centre (0, 9, -4.55); handle top y 22; keep LanternFirstPerson's
# STONE look in step if these move.
SD = 6
STONE_G = (70, 84, 66)      # green-painted stone, worn
STONE_GP = (58, 70, 56)     # the pillars, a shade darker
MORTAR = (30, 36, 30)
MOSS = [(36, 78, 30), (52, 104, 38), (66, 124, 44), (92, 150, 56)]
RUST = (112, 68, 38)
CRACK_DEEP = (8, 22, 10)
CRACK_HOT = (240, 255, 228)
CRACK_LIT = (120, 255, 140)
CRACK_EDGE = (40, 200, 80)


def _rows(w, h, fill=CLEAR):
    return [[fill] * w for _ in range(h)]


def moss_px(rnd):
    return rnd.choices(MOSS, weights=(2, 4, 4, 1))[0] + (255,)


_CRACKS = {}


def cracks(seed, face, w, h, amount):
    """Branching fissures over a face: {(x, y): 2 for the hot middle, 1 for the lit edge}. The
    same (seed, face, size) always gives the same cracks, so the stone and its glow plane agree."""
    key = (seed, face, w, h, amount)
    if key in _CRACKS:
        return _CRACKS[key]
    rnd = random.Random(f"crack/{seed}/{face}/{w}x{h}")
    out = {}

    def walk(x, y, dx, dy, length, hot):
        for _ in range(length):
            if not (0 <= x < w and 0 <= y < h):
                return
            out[(x, y)] = max(out.get((x, y), 0), 2 if hot else 1)
            if hot:
                for nx, ny in ((x + 1, y), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and rnd.random() < 0.45:
                        out.setdefault((nx, ny), 1)
            if rnd.random() < 0.035 and length > 10:
                bdx, bdy = rnd.choice(((1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)))
                walk(x, y, bdx, bdy, rnd.randint(3, max(4, length // 2)), False)
            if dx and dy and rnd.random() < 0.45:
                if rnd.random() < 0.5:
                    x += dx
                else:
                    y += dy
            elif rnd.random() < 0.3:
                x += rnd.choice((-1, 0, 1)) if dx == 0 else dx
                y += dy if dy else rnd.choice((-1, 0, 1))
            else:
                x += dx
                y += dy
    n = max(1, round(amount * w * h / 260))
    for i in range(n):
        side = rnd.random()
        if side < 0.35:
            x, y, dx, dy = rnd.randrange(w), 0, 0, 1
        elif side < 0.6:
            x, y, dx, dy = rnd.randrange(w), h - 1, 0, -1
        elif side < 0.8:
            x, y, dx, dy = 0, rnd.randrange(h), 1, rnd.choice((-1, 0, 1))
        else:
            x, y, dx, dy = w - 1, rnd.randrange(h), -1, rnd.choice((-1, 0, 1))
        walk(x, y, dx, dy, rnd.randint(min(w, h) // 2, max(w, h)), i % 2 == 0 or rnd.random() < 0.5)
    # The body's panels: light leaks down the joints where they meet the pillars, in broken runs.
    if seed == "body" and face in ("north", "south", "east", "west"):
        for x in (int(1.5 * SD), w - 1 - int(1.5 * SD)):
            for y in range(h):
                if (y // 5) % 4 != 3 or rnd.random() < 0.3:
                    out[(x, y)] = 2 if rnd.random() < 0.6 else 1
    _CRACKS[key] = out
    return out


def stone(seed, base=STONE_G, course=2, moss_top=0.0, moss_up=0.0, rust=0.0, crack=0.0):
    """Weathered stone blocks: courses ``course`` units high with staggered joints, each block a
    slightly different tone with a lit top edge, dark mortar, pits and rust stains. Moss hangs
    ``moss_top`` of the way down the side faces and covers about ``moss_up`` of the top face;
    ``crack`` cuts that many fissures (per area) into it, painted as deep shadow."""
    def paint(face, w, h):
        rnd = random.Random(f"{seed}/{face}/{w}x{h}")
        ch = max(1, course * SD)
        joints = []
        for _ in range(h // ch + 2):
            xs, x = [], -rnd.randint(0, 3 * SD)
            while x < w:
                xs.append(x)
                x += rnd.randint(2 * SD, 4 * SD)
            joints.append(xs)
        tone = {}
        depth = [0.0] * w
        if moss_top and face not in ("up", "down"):
            raw = [moss_top * h * (0.35 + 0.65 * rnd.random()) for _ in range(w)]
            for _ in range(3):
                raw = [(raw[max(i - 1, 0)] + raw[i] + raw[min(i + 1, w - 1)]) / 3 for i in range(w)]
            depth = [d + rnd.uniform(-1.5, 1.5) for d in raw]
        blobs = []
        if moss_up and face == "up":
            for _ in range(int(3 + 10 * moss_up)):
                if rnd.random() < 0.5:
                    bx, by = rnd.choice((rnd.uniform(0, w * 0.2), rnd.uniform(w * 0.8, w))), rnd.uniform(0, h)
                else:
                    bx, by = rnd.uniform(0, w), rnd.choice((rnd.uniform(0, h * 0.2), rnd.uniform(h * 0.8, h)))
                blobs.append((bx, by, rnd.uniform(0.08, 0.2) * min(w, h) * (0.6 + moss_up)))
        fissures = cracks(seed, face, w, h, crack) if crack and face not in ("down",) else {}
        rows = []
        for y in range(h):
            r, yy = divmod(y, ch)
            xs = joints[r]
            row = []
            for x in range(w):
                bi = max(i for i, j in enumerate(xs) if j <= x) if xs[0] <= x else 0
                t = tone.setdefault((r, bi), rnd.uniform(-14, 10))
                c = tuple(clamp(v + t) for v in base)
                if x in xs or yy == ch - 1:
                    c = MORTAR
                elif yy == 0:
                    c = mix(c, (150, 160, 140), 0.32)
                elif x - 1 in xs:
                    c = mix(c, (150, 160, 140), 0.14)
                elif yy == ch - 2:
                    c = mix(c, MORTAR, 0.25)
                v = rnd.randint(-5, 5)
                c = tuple(clamp(ch_ + v) for ch_ in c)
                roll = rnd.random()
                if roll < 0.025:
                    c = mix(c, MORTAR, 0.6)
                elif roll < 0.025 + rust:
                    c = mix(RUST, c, rnd.uniform(0, 0.4))
                px = c + (255,)
                if y < depth[x]:
                    px = moss_px(rnd)
                elif blobs and any(math.hypot(x - bx, y - by) < br * (0.8 + 0.4 * rnd.random()) for bx, by, br in blobs):
                    px = moss_px(rnd)
                k = fissures.get((x, y))
                if k:
                    px = (CRACK_DEEP if k == 2 else mix(CRACK_DEEP, c, 0.35)) + (255,)
                row.append(px)
            rows.append(row)
        return rows
    return paint


def crack_light(seed, face_of, crack):
    """The light through a stone face's cracks, for a zero-thickness plane laid on that face:
    pale-hot in the middle of each fissure, green at its edges, clear everywhere else.
    ``face_of`` is the stone face it covers; the plane's other side stays clear."""
    def paint(face, w, h):
        if face != face_of:
            return _rows(w, h)
        f = cracks(seed, face, w, h, crack)
        rows = _rows(w, h)
        for (x, y), k in f.items():
            rows[y][x] = (CRACK_HOT if k == 2 else CRACK_LIT) + (255,)
        # The light spills a pixel into the stone beside the hot cracks.
        for (x, y), k in f.items():
            if k != 2:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and rows[ny][nx] == CLEAR:
                    rows[ny][nx] = CRACK_EDGE + (255,)
        return rows
    return paint


def plank_lid(face, w, h):
    """The dark plank lid: weathered grey-brown boards with dark seams and a worn edge."""
    rnd = random.Random(f"lid/{face}/{w}x{h}")
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = (68, 58, 48)
            if face == "up":
                edge = min(x, y, w - 1 - x, h - 1 - y)
                if edge < 2:
                    c = (52, 46, 40) if edge else (98, 90, 80)
                elif (y - 2) % (2 * SD) == 0:
                    c = (34, 28, 24)
                elif rnd.random() < 0.05:
                    c = (84, 74, 62)
            elif y == 0:
                c = (98, 90, 80)
            v = rnd.randint(-5, 5)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def handle_stone(face, w, h):
    """The handle: pale weathered stone with a lit top edge, a shaded underside and rust specks."""
    rnd = random.Random(f"handle/{face}/{w}x{h}")
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = (112, 106, 98)
            if face == "up" or (face != "down" and y < 2 and h > 6):
                c = (150, 144, 134)
            elif face == "down" or (y >= h - 2 and h > 6):
                c = (62, 58, 54)
            elif x < 1 or x >= w - 1:
                c = (84, 80, 74)
            if rnd.random() < 0.04:
                c = RUST
            v = rnd.randint(-5, 5)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def mossy(seed, ragged=False):
    """A clump of moss, mostly green with stone peeking through. ``ragged`` frays the bottom
    edge of the side faces into hanging strands (cut out)."""
    def paint(face, w, h):
        rnd = random.Random(f"moss/{seed}/{face}/{w}x{h}")
        hang = [h - rnd.randint(0, h // 2) for _ in range(w)] if ragged and face not in ("up", "down") else [h] * w
        rows = []
        for y in range(h):
            row = []
            for x in range(w):
                if y >= hang[x]:
                    row.append(CLEAR)
                elif rnd.random() < 0.1:
                    row.append(tuple(clamp(v + rnd.randint(-6, 6)) for v in STONE_GP) + (255,))
                else:
                    row.append(moss_px(rnd))
            rows.append(row)
        return rows
    return paint


def foot_paint(face, w, h):
    """The plinth's foot; underneath, a recessed panel with a socket in each corner."""
    if face != "down":
        return stone("foot", course=1)(face, w, h)
    rows = stone("foot", course=12)(face, w, h)
    s = SD
    for y in range(h):
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if s <= edge < s + 2:
                rows[y][x] = (118, 128, 112, 255)
            ex, ey = min(x, w - 1 - x), min(y, h - 1 - y)
            if 1.4 * s <= ex <= 2.2 * s and 1.4 * s <= ey <= 2.2 * s:
                rows[y][x] = (18, 18, 16, 255)
            if abs(x - (w - 1) / 2) <= 0.5 * s and abs(y - (h - 1) / 2) <= 0.5 * s:
                rows[y][x] = (18, 18, 16, 255)
    return rows


stone_l = Model("stone_lantern", density=SD)
S = stone_l.cube
EPS = 0.02


def cracked(name, frm, to, seed, faces, crack, **kw):
    """A stone cube with fissures on ``faces``, each with a glow plane laid just outside it."""
    S(name, frm, to, stone(seed, crack=crack, **kw))
    (x0, y0, z0), (x1, y1, z1) = frm, to
    planes = {
        "north": ((x0, y0, z0 - EPS), (x1, y1, z0 - EPS)), "south": ((x0, y0, z1 + EPS), (x1, y1, z1 + EPS)),
        "west": ((x0 - EPS, y0, z0), (x0 - EPS, y1, z1)), "east": ((x1 + EPS, y0, z0), (x1 + EPS, y1, z1)),
        "up": ((x0, y1 + EPS, z0), (x1, y1 + EPS, z1)),
    }
    for f in faces:
        a, b = planes[f]
        S(f"glow_crack_{name}_{f}", a, b, crack_light(seed, f, crack))


SIDES = ("north", "south", "east", "west")
# Plinth: a wide foot and a coursed base, a sill under the front and back panels, a mossy corner.
S("foot", (-6, 0, -6), (6, 1, 6), foot_paint)
cracked("base", (-5.5, 1, -5.5), (5.5, 3, 5.5), "base", SIDES, 0.35, course=1, rust=0.01)
S("sill_front", (-2, 3, -5.5), (2, 4, -4.5), stone("sill_f", base=(88, 100, 84), course=1))
S("sill_back", (-2, 3, 4.5), (2, 4, 5.5), stone("sill_b", base=(88, 100, 84), course=1))
S("moss_plinth", (-6.5, 1, -6.5), (-4.5, 3, -4.5), mossy("plinth"))
# Four corner pillars standing half a unit proud of the panels, each on a base block and under a capital.
for sx in (-1, 1):
    for sz in (-1, 1):
        x0, x1 = sorted((sx * 3, sx * 5))
        z0, z1 = sorted((sz * 3, sz * 5))
        out = ("east" if sx > 0 else "west", "south" if sz > 0 else "north")
        cracked(f"pillar_{sx}_{sz}", (x0, 4, z0), (x1, 14, z1), f"pillar{sx}{sz}", out, 0.6,
                base=STONE_GP, course=3, rust=0.008)
        bx0, bx1 = sorted((sx * 2.5, sx * 5.5))
        bz0, bz1 = sorted((sz * 2.5, sz * 5.5))
        S(f"pillar_base_{sx}_{sz}", (bx0, 3, bz0), (bx1, 4, bz1), stone(f"pbase{sx}{sz}", course=1))
        S(f"pillar_cap_{sx}_{sz}", (bx0, 14, bz0), (bx1, 15, bz1), stone(f"pcap{sx}{sz}", course=1, rust=0.02))
# The sealed body: one solid block of stone, its panels cracked all over.
cracked("body", (-4.5, 3, -4.5), (4.5, 15, 4.5), "body", SIDES, 0.4, course=3, moss_top=0.16)
# Lintel, overhanging cornice, moss on top and hanging over the front, and the plank lid.
cracked("lintel", (-5.5, 15, -5.5), (5.5, 16, 5.5), "lintel", SIDES, 0.4, course=1, moss_top=0.5, rust=0.02)
S("cornice", (-6, 16, -6), (6, 17, 6), stone("cornice", base=(64, 76, 60), course=1, moss_top=0.7, moss_up=0.6, rust=0.015))
S("moss_drape", (-2, 13, -5.5), (1, 16, -4.5), mossy("drape", ragged=True))
S("moss_top_ne", (4, 17, -6), (6, 18, -1), mossy("ne"))
S("moss_top_sw", (-6, 17, 4), (-2, 18, 6), mossy("sw"))
S("lid", (-4, 17, -4), (4, 18, 4), plank_lid)
# The light leaks round the lid: a bright seam where it sits on the cornice.
def lid_seam(face_of):
    def paint(face, w, h):
        rows = _rows(w, h)
        if face == face_of:
            rows[h - 1] = [CRACK_HOT + (255,)] * w
            rows[h - 2] = [(CRACK_LIT if (x // 3) % 3 else CRACK_EDGE) + (255,) for x in range(w)]
        return rows
    return paint


for f, a, b in (("north", (-4, 17, -4 - EPS), (4, 18, -4 - EPS)), ("south", (-4, 17, 4 + EPS), (4, 18, 4 + EPS)),
                ("west", (-4 - EPS, 17, -4), (-4 - EPS, 18, 4)), ("east", (4 + EPS, 17, -4), (4 + EPS, 18, 4))):
    S(f"glow_crack_lid_{f}", a, b, lid_seam(f))
# The square handle; its right post is wrapped in moss.
S("handle_left", (-4, 18, -0.5), (-3, 21, 0.5), handle_stone)
S("handle_right", (3, 18, -0.5), (4, 21, 0.5), mossy("post"))
S("handle_top", (-4, 21, -0.5), (4, 22, 0.5), handle_stone)
stone_l.write()


# ---- the Classic battery (Lab option): the comic Power Battery from J's face sheets -----------
# A glossy green metal ball with a short stacked cap on top and a stepped foot below, a round
# port on each side and a flat round plate on the back, a thin arched handle from the side
# ports over the cap, and on the front a round housing with the glowing lens recessed in it:
# the charging port, where the ring docks. The round parts are sliced into one-unit boxes, and
# each texel is shaded from the real surface it stands for (the ball's or a cylinder's normal),
# so the slices read as one smooth glossy shape. Shading only depends on how far a surface faces
# up, so it looks the same whichever way a face's texture runs. Lens centre (0, 9.5, -7.05);
# handle top y 22. Keep LanternFirstPerson's CLASSIC look in step if these move.
CD = 4
GM = (52, 140, 64)          # glossy green metal
GM_DARK = (14, 50, 22)
GM_HI = (196, 250, 196)
GM_RIM = (120, 200, 124)
GREEN_METAL = (GM_DARK, GM, GM_HI, GM_RIM)

classic = Model("classic_lantern", density=CD)
CB = classic.cube


def _norm(v):
    m = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / m for c in v)


def lit(n, pal=None):
    """Green metal lit from above and in front, as on the sheets: dark underneath and round the
    back, with a bright glint where the surface faces between the light and the viewer and a
    faint green bounce from below. Symmetric left to right, so it looks the same whichever way
    a face's texture runs."""
    dark, base, hi, rim = pal or GREEN_METAL
    L = _norm((0.0, 0.75, -0.65))
    H = _norm((0.0, 0.75, -1.65))
    diff = max(0.0, sum(n[i] * L[i] for i in range(3)))
    c = mix(dark, base, 0.2 + 0.8 * diff)
    spec = max(0.0, sum(n[i] * H[i] for i in range(3))) ** 24
    c = mix(c, hi, min(1.0, spec * 0.95))
    c = mix(c, rim, 0.3 * max(0.0, -n[1]) ** 2)
    return c


def _texel(frm, to, face, u, v, w, h):
    """The model-space point a texel stands for (one face of an axis-aligned box), following the
    way ModelPart lays box UV onto each face once BbModel has turned the model about Z."""
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


AXES = {"x": 0, "y": 1, "z": 2}
CAP_FACES = {"x": ("east", "west"), "y": ("up", "down"), "z": ("north", "south")}


def metal(frm, to, shape, cap=None, pal=None):
    """Glossy green metal for one slice of a round part. ``shape`` is ("ball", centre) or
    ("cyl", axis, centre, radius). ``cap(p, r, R, face)`` may repaint a cylinder's flat ends
    (return a colour, CLEAR, or None to keep the metal)."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                if shape[0] == "ball":
                    c = lit(_norm(tuple(p[i] - shape[1][i] for i in range(3))), pal)
                else:
                    _, axis, centre, R = shape
                    i = AXES[axis]
                    d = [p[k] - centre[k] for k in range(3)]
                    d[i] = 0.0
                    r = math.sqrt(sum(x * x for x in d))
                    if face in CAP_FACES[axis]:
                        if r > R + 0.15:
                            row.append(CLEAR)  # cut the stepped slices' ends round
                            continue
                        n = [0.0, 0.0, 0.0]
                        n[i] = 1.0 if face in ("east", "up", "south") else -1.0
                        # A flat end: a bevelled rim (bright above, dark below) round a flat face.
                        c = lit(_norm((d[0] * 0.15 / R + n[0], d[1] * 0.35 / R + n[1], n[2])), pal)
                        if r > R - 0.6:
                            P = pal or GREEN_METAL
                            c = P[2] if d[1] > 0.5 else (P[3] if d[1] > -0.8 else P[0])
                        elif r > R - 0.9:
                            c = (pal or GREEN_METAL)[0]
                        if cap:
                            k = cap(p, r, R, face)
                            if k is not None:
                                row.append(k)
                                continue
                    elif r < R - 1.05:
                        row.append(CLEAR)  # a face inside the part: only seen through a hole
                        continue
                    else:
                        c = lit(_norm(d), pal)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def half(x):
    """Rounds a half-width to the half unit, so every slice is a whole number of units wide."""
    return round(x * 2) / 2


def cylinder(name, axis, centre, R, a0, a1, cap=None, pal=None, cube=None, paint=None):
    """A round part along ``axis`` from a0 to a1, sliced into one-unit boxes across it."""
    i = AXES[axis]
    j, k = [m for m in range(3) if m != i]
    # Slice along j (one unit thick), each box spanning ±half-width along k.
    n = int(round(2 * R))
    for s in range(n):
        off = -R + s + 0.5
        hw = half(math.sqrt(max(R * R - off * off, 0)) + 0.15)
        if hw <= 0:
            continue
        frm, to = [0.0] * 3, [0.0] * 3
        frm[i], to[i] = a0, a1
        frm[j], to[j] = centre[j] + off - 0.5, centre[j] + off + 0.5
        frm[k], to[k] = centre[k] - hw, centre[k] + hw
        p = paint(tuple(frm), tuple(to)) if paint else metal(tuple(frm), tuple(to), ("cyl", axis, centre, R), cap, pal)
        (cube or CB)(f"{name}_{s}", tuple(frm), tuple(to), p)


BALL = (0.0, 9.5, 0.0)
BR = 6
# The ball: one-unit layers up its height, each sliced front to back.
for ly in range(2 * BR):
    yc = BALL[1] - BR + ly + 0.5
    rr = math.sqrt(max(BR * BR - (yc - BALL[1]) ** 2, 0)) + 0.2
    for s in range(int(round(2 * rr))):
        zc = -rr + s + 0.5
        zc = round(zc * 2) / 2 if abs(round(zc * 2) / 2 - zc) < 1e-6 else zc
        hw = half(math.sqrt(max(rr * rr - zc * zc, 0)))
        if hw <= 0:
            continue
        frm = (-hw, yc - 0.5, zc - 0.5)
        to = (hw, yc + 0.5, zc + 0.5)
        CB(f"ball_{ly}_{s}", frm, to, metal(frm, to, ("ball", BALL)))


def bolts(p, r, R, face):
    """The foot's underside: a ring line and four bolts."""
    if abs(r - (R - 1.6)) < 0.25:
        return GM_DARK + (255,)
    for ang in (45, 135, 225, 315):
        bx, bz = (R - 1.0) * math.cos(math.radians(ang)), (R - 1.0) * math.sin(math.radians(ang))
        if math.hypot(p[0] - bx, p[2] - bz) < 0.45:
            return GM_HI + (255,)
    return None


def cap_top(p, r, R, face):
    """The cap's top: a raised outer rim with a sunken disc inside it."""
    if face == "up" and r < R - 1.3:
        return (lit((0.0, 0.9, -0.3)) if r < R - 1.6 else GM_DARK) + (255,)
    return None


# Foot, neck, the ball, neck and the stacked cap (round parts along Y).
cylinder("foot", "y", (0, 0, 0), 5, 0, 1, cap=bolts)
cylinder("foot_band", "y", (0, 0, 0), 4.6, 1, 3)
cylinder("neck_low", "y", (0, 0, 0), 3.5, 3, 4)
cylinder("neck_high", "y", (0, 0, 0), 4, 15, 16)
cylinder("cap", "y", (0, 0, 0), 4.5, 16, 18, cap=cap_top)


def port_face(p, r, R, face):
    """A side port's end: a plain cap with a fine groove ring."""
    if abs(r - (R - 1.8)) < 0.2:
        return GM_DARK + (255,)
    return None


# Round ports on both sides and a flat plate on the back.
cylinder("port_w", "x", (0, 9.5, 0), 3, -7.5, -4.5, cap=port_face)
cylinder("port_e", "x", (0, 9.5, 0), 3, 4.5, 7.5, cap=port_face)
cylinder("back_plate", "z", (0, 9.5, 0), 4, 4.5, 6.5, cap=port_face)


def housing_face(p, r, R, face):
    """The lens housing's front: a bright bevelled rim, a dark ring and the hole for the lens."""
    if face == "north" and r < 2.3:
        return CLEAR
    if face == "north" and r < 2.7:
        return (6, 22, 10, 255)
    return None


def lens_paint(frm, to):
    """The lens: one box whose front is cut round (the housing's hole frames it), white-hot in
    the middle and green at its edge. Its other faces are clear."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                r = math.hypot(p[0], p[1] - 9.5)
                if face != "north" or r > 2.5:
                    row.append(CLEAR)
                    continue
                if r < 1.0:
                    c = (245, 255, 240)
                elif r < 1.8:
                    c = mix((245, 255, 240), (120, 255, 150), (r - 1.0) / 0.8)
                else:
                    c = mix((120, 255, 150), (40, 210, 80), min(1, (r - 1.8) / 0.9))
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


# The front: the lens housing (the charging port) with the glowing lens set into it.
cylinder("housing", "z", (0, 9.5, 0), 3.6, -7, -5, cap=housing_face)
CB("glow_lens", (-2.5, 7, -6.8), (2.5, 12, -5.8), lens_paint((-2.5, 7, -6.8), (2.5, 12, -5.8)))


def wire(face, w, h):
    """The thin handle: same colour all along so its pieces join seamlessly."""
    c = {"up": GM_HI, "down": GM_DARK}.get(face, GM)
    return [[c + (255,)] * w for _ in range(h)]


# The thin arched handle: up from the top of each side port, then a half circle over the cap.
# Cells along the arc, joined edge to edge (a diagonal step gets a filler cell) so it reads as
# one unbroken wire.
path = []
for st in range(0, 181, 2):
    a = math.radians(st)
    c = (round(7 * math.cos(a)), round(14 + 7 * math.sin(a)))
    if path and c == path[-1]:
        continue
    if path and abs(c[0] - path[-1][0]) == 1 and abs(c[1] - path[-1][1]) == 1:
        path.append((c[0], path[-1][1]) if c[1] > path[-1][1] else (path[-1][0], c[1]))
    path.append(c)
cells = set(path) | {(-7, 13), (7, 13)}
for x, y in sorted(cells):
    CB(f"handle_{x}_{y}", (x - 0.5, y - 0.5, -0.5), (x + 0.5, y + 0.5, 0.5), wire)
classic.write()




# ---- the Keychain lantern (Lab option; model power_lantern), restyled like the Classic -----------
# J's keychain lantern: a ribbed green glass bottle that swells in the middle, a stepped brass
# base, two brass bands round the glass, a round brass emblem on the front with the glowing lens in
# it (where the ring docks), a stepped brass cap with turned rings, a knob and a loop handle. Every
# round part is sliced and lit per texel like the Classic battery; only the lens glows. Lens
# centre (0, 8, -5.55); handle top y 20. Keep LanternFirstPerson's KEYCHAIN look in step.
BRASS_PAL = ((96, 66, 22), (206, 160, 70), (255, 242, 190), (232, 192, 108))
KEY_GLASS = ((24, 120, 52), (80, 236, 120), (230, 255, 230), (150, 250, 176))

key = Model("power_lantern", density=CD)
KC = key.cube


def key_glass(R):
    """Green glass for one slice of a bottle layer: lit like the Classic's metal, a little
    luminous, with a pale crest at the top of each one-unit rib and a dark groove under it."""
    def factory(frm, to):
        def paint(face, w, h):
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    p = _texel(frm, to, face, u, v, w, h)
                    r = math.hypot(p[0], p[2])
                    if face in ("up", "down"):
                        if r > R + 0.15:
                            row.append(CLEAR)
                            continue
                        c = lit((0.0, 1.0 if face == "up" else -1.0, 0.0), KEY_GLASS)
                    else:
                        if r < R - 1.05:
                            row.append(CLEAR)
                            continue
                        c = mix(lit(_norm((p[0], 0.0, p[2])), KEY_GLASS), KEY_GLASS[1], 0.55)
                        f = p[1] % 1.0
                        if f > 0.8:
                            c = mix(c, KEY_GLASS[2], 0.2)
                        elif f < 0.15:
                            c = mix(c, KEY_GLASS[0], 0.25)
                    row.append(c + (255,))
                rows.append(row)
            return rows
        return paint
    return factory


def key_r(y):
    """The bottle's radius at height y: 4 at the ends, swelling to 4.6 in the middle."""
    return 4 + 0.6 * math.sin(math.pi * (y - 4) / 9)


def turned(p, r, R, face):
    """The cap's top: turned rings, alternately bright and shaded."""
    if face != "up":
        return None
    if int(r / 0.75) % 2:
        return BRASS_PAL[0 if r > 1 else 3] + (255,)
    return None


# Base, the bottle layer by layer, the two bands and the cap.
cylinder("base_foot", "y", (0, 0, 0), 5, 0, 1, pal=BRASS_PAL, cube=KC)
cylinder("base_rim", "y", (0, 0, 0), 5.5, 1, 2, pal=BRASS_PAL, cube=KC)
cylinder("base_band", "y", (0, 0, 0), 5, 2, 3, pal=BRASS_PAL, cube=KC)
cylinder("base_lip", "y", (0, 0, 0), 4.5, 3, 4, pal=BRASS_PAL, cube=KC)
for y in range(4, 13):
    R = key_r(y + 0.5)
    cylinder(f"glass_{y}", "y", (0, 0, 0), R, y, y + 1, cube=KC, paint=key_glass(R))
cylinder("band_low", "y", (0, 0, 0), key_r(5.5) + 0.7, 5, 6, pal=BRASS_PAL, cube=KC)
cylinder("band_high", "y", (0, 0, 0), key_r(10.5) + 0.7, 10, 11, pal=BRASS_PAL, cube=KC)
cylinder("cap_rim", "y", (0, 0, 0), 4.5, 13, 14, pal=BRASS_PAL, cube=KC)
cylinder("cap", "y", (0, 0, 0), 4, 14, 15, pal=BRASS_PAL, cube=KC)
cylinder("cap_ring", "y", (0, 0, 0), 3.5, 15, 16, pal=BRASS_PAL, cube=KC)
cylinder("cap_top", "y", (0, 0, 0), 2.5, 16, 17, cap=turned, pal=BRASS_PAL, cube=KC)
cylinder("knob", "y", (0, 0, 0), 1, 17, 18, pal=BRASS_PAL, cube=KC)


def key_emblem(p, r, R, face):
    """The emblem's front: dark green enamel with two fine lighter rings, then a brass ring round
    the hole the lens shows through."""
    if face != "north" or r > R - 0.7:
        return None
    if r < 1.4:
        return CLEAR
    if r < 1.8:
        return lit((0.0, 0.5, -1.0), BRASS_PAL) + (255,)
    if abs(r - 2.3) < 0.18:
        return (44, 118, 64, 255)
    return (16, 58, 32, 255)


def key_lens(frm, to):
    """The lens: white-hot in the middle, bright green to its edge. Only the front shows."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                r = math.hypot(p[0], p[1] - 8)
                if face != "north" or r > 1.5:
                    row.append(CLEAR)
                    continue
                c = mix((245, 255, 240), (110, 255, 145), min(1.0, r / 0.9))
                if r > 0.9:
                    c = mix((110, 255, 145), (40, 210, 80), (r - 0.9) / 0.6)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


# The emblem on the front, with the lens recessed in it (drawn solid and glowing).
cylinder("emblem", "z", (0, 8, 0), 3, -5.7, -4.7, cap=key_emblem, pal=BRASS_PAL, cube=KC)
for n in ("lens", "glow_lens"):
    KC(n, (-1.5, 6.5, -5.5), (1.5, 9.5, -4.5), key_lens((-1.5, 6.5, -5.5), (1.5, 9.5, -4.5)))


def key_wire(face, w, h):
    """The handle: one even brass colour so its cells join seamlessly."""
    c = {"up": BRASS_PAL[2], "down": BRASS_PAL[0]}.get(face, BRASS_PAL[1])
    return [[c + (255,)] * w for _ in range(h)]


# The loop handle: a half ellipse over the knob, cells joined edge to edge.
loop = []
for st in range(0, 181, 2):
    a = math.radians(st)
    c = (round(3 * math.cos(a)), math.floor(17 + 2.99 * math.sin(a)))
    if loop and c == loop[-1]:
        continue
    if loop and abs(c[0] - loop[-1][0]) == 1 and abs(c[1] - loop[-1][1]) == 1:
        loop.append((c[0], loop[-1][1]) if c[1] > loop[-1][1] else (loop[-1][0], c[1]))
    loop.append(c)
for x, y in sorted(set(loop)):
    KC(f"handle_{x}_{y}", (x - 0.5, y, -0.5), (x + 0.5, y + 1, 0.5), key_wire)
key.write()


# ---- the Torus Core battery (Lab option), restyled like the Classic --------------------------
# Concept 04 with 02's ring handle: two round torus rings with a band between them make the
# base, a round glass body carries the pale lantern emblem on all four sides, a rounded collar,
# a lip and a small cap carry a chunky arched handle. Every round part is sliced and lit per
# texel like the Classic battery. Only the lens in the middle of the front emblem glows; the
# ring docks there. Lens centre (0, 10, -4.75); handle top y 24. Keep LanternFirstPerson's TORUS
# look in step if these move.
torus = Model("torus_lantern", density=CD)
TC = torus.cube
TORUS_GLASS = KEY_GLASS


def torus_paint(R, yc, R0, pal=None):
    """Glossy metal for one slice of a round ring whose cross-section is round: lit from the
    normal of a tube of centre radius R0 at height yc. R is the slice layer's outer radius."""
    def factory(frm, to):
        def paint(face, w, h):
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    p = _texel(frm, to, face, u, v, w, h)
                    r = math.hypot(p[0], p[2])
                    if face in ("up", "down") and r > R + 0.15:
                        row.append(CLEAR)
                        continue
                    if face not in ("up", "down") and r < R - 1.05:
                        row.append(CLEAR)
                        continue
                    k = R0 / max(r, 1e-6)
                    c = lit(_norm((p[0] * (1 - k), p[1] - yc, p[2] * (1 - k))), pal)
                    row.append(c + (255,))
                rows.append(row)
            return rows
        return paint
    return factory


def ring_of(name, y0, y1, yc, R0, tube):
    """A round torus ring from y0 to y1, one layer per unit, its radius following the tube."""
    for y in range(y0, y1):
        dy = (y + 0.5 - yc) / tube
        R = R0 + tube * math.sqrt(max(1 - dy * dy, 0.0)) * 0.95 + 0.1
        cylinder(f"{name}_{y}", "y", (0, 0, 0), R, y, y + 1, cube=TC, paint=torus_paint(R, yc, R0))


ER = 2.4  # the emblem's size on the glass


def torus_emblem(t, d):
    """1 for the pale emblem, 2 for its dark outline, 0 elsewhere (t across, d up, in units)."""
    def pale(t, d):
        r = math.hypot(t, d)
        return ER * 0.52 <= r <= ER * 0.86 or (ER * 0.9 <= abs(d) <= ER * 1.18 and abs(t) <= ER * 0.8)
    if pale(t, d):
        return 1
    for a in range(0, 360, 45):
        if pale(t + 0.3 * math.cos(math.radians(a)), d + 0.3 * math.sin(math.radians(a))):
            return 2
    return 0


def torus_glass(R):
    def factory(frm, to):
        def paint(face, w, h):
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    p = _texel(frm, to, face, u, v, w, h)
                    r = math.hypot(p[0], p[2])
                    if face in ("up", "down"):
                        row.append(CLEAR if r > R + 0.15 else TORUS_GLASS[1] + (255,))
                        continue
                    if r < R - 1.05:
                        row.append(CLEAR)
                        continue
                    c = mix(lit(_norm((p[0], 0.0, p[2])), TORUS_GLASS), TORUS_GLASS[1], 0.55)
                    a = math.degrees(math.atan2(p[0], -p[2]))
                    da = (a + 45) % 90 - 45
                    m = torus_emblem(math.radians(da) * R, p[1] - 10)
                    if m == 1:
                        c = (236, 255, 226)
                    elif m == 2:
                        c = TORUS_GLASS[0]
                    row.append(c + (255,))
                rows.append(row)
            return rows
        return paint
    return factory


# The base: a torus ring, a band and a second torus ring; the glass body; collar, lip and cap.
ring_of("foot_ring", 0, 2, 1, 4.6, 1.3)
cylinder("mid_band", "y", (0, 0, 0), 5.2, 2, 3, cube=TC)
ring_of("base_ring", 3, 5, 4, 4.6, 1.3)
for y in range(5, 15):
    cylinder(f"glass_{y}", "y", (0, 0, 0), 4.5, y, y + 1, cube=TC, paint=torus_glass(4.5))
ring_of("collar", 15, 17, 16, 4.4, 1.3)
cylinder("collar_lip", "y", (0, 0, 0), 4.5, 17, 18, cube=TC)


def torus_cap(p, r, R, face):
    """The cap's top: a dark ring round a raised disc."""
    if face == "up" and r < R - 1.0:
        return (lit((0.0, 0.9, -0.3)) if r < R - 1.4 else GM_DARK) + (255,)
    return None


cylinder("cap", "y", (0, 0, 0), 3.5, 18, 19, cap=torus_cap, cube=TC)


def torus_lens(frm, to):
    """The lens in the front emblem's ring: white-hot in the middle, green at its edge."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                r = math.hypot(p[0], p[1] - 10)
                if face != "north" or r > ER * 0.52 - 0.1:
                    row.append(CLEAR)
                    continue
                c = mix((245, 255, 240), (60, 230, 100), min(1.0, r / (ER * 0.52)))
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


for n in ("lens", "glow_lens"):
    TC(n, (-1.5, 8.5, -4.7), (1.5, 11.5, -3.7), torus_lens((-1.5, 8.5, -4.7), (1.5, 11.5, -3.7)))


def torus_handle(face, w, h):
    """The chunky handle: lit top, shaded underside, one colour along it so cells join."""
    c = {"up": GM_HI, "down": GM_DARK}.get(face, GM)
    if face in ("north", "south"):
        c = mix(GM, GM_RIM, 0.3)
    return [[c + (255,)] * w for _ in range(h)]


# The chunky arched handle: a half circle over the cap, two units thick, cells joined edge to edge.
arc = []
for st in range(0, 181, 2):
    a = math.radians(st)
    c = (round(3 * math.cos(a)), math.floor(19.5 + 4.49 * math.sin(a)))
    if arc and c == arc[-1]:
        continue
    if arc and abs(c[0] - arc[-1][0]) == 1 and abs(c[1] - arc[-1][1]) == 1:
        arc.append((c[0], arc[-1][1]) if c[1] > arc[-1][1] else (arc[-1][0], c[1]))
    arc.append(c)
for x, y in sorted(set(arc)):
    TC(f"handle_{x}_{y}", (x - 0.5, y, -1), (x + 0.5, y + 1, 1), torus_handle)
torus.write()


# ---- the Compact Unit (Lab option), restyled like the Classic --------------------------------
# A square lantern: a plinth, a rim, a glass box with the lantern emblem on all four sides between
# four round corner columns, a top rim, a small cap and a square handle. The square parts are
# bevelled boxes and the columns round slices, all lit per texel like the Classic battery with no
# noise. Only the lens in the middle of the front emblem glows; the ring docks there. Lens centre
# (0, 7, -4.25); handle top y 18. Keep LanternFirstPerson's COMPACT look in step if these move.
compact = Model("compact_lantern", density=CD)
CC = compact.cube
PLINTH = ((10, 34, 16), (36, 96, 46), (170, 230, 170), (80, 150, 86))


def bevelled(frm, to, pal=None, bev=0.45, top=None):
    """A box of glossy metal with rounded edges: each texel is lit from its face's normal, bent
    toward any edge it is within ``bev`` of. ``top(p)`` may repaint the up face."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                n = [0.0, 0.0, 0.0]
                i = {"east": 0, "west": 0, "up": 1, "down": 1, "south": 2, "north": 2}[face]
                n[i] = 1.0 if face in ("east", "up", "south") else -1.0
                for k in range(3):
                    if k == i:
                        continue
                    if p[k] - frm[k] < bev:
                        n[k] -= 0.8 * (1 - (p[k] - frm[k]) / bev)
                    elif to[k] - p[k] < bev:
                        n[k] += 0.8 * (1 - (to[k] - p[k]) / bev)
                c = lit(_norm(n), pal)
                if top and face == "up":
                    c = top(p) or c
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def box(name, frm, to, pal=None, top=None):
    CC(name, frm, to, bevelled(frm, to, pal, top=top))


def compact_glass(frm, to):
    """The glass box: luminous green, lit flat per face, with the pale emblem (dark outlined)
    centred on each side face between the columns."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                if face in ("up", "down"):
                    row.append(TORUS_GLASS[1] + (255,))
                    continue
                n = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}[face]
                c = mix(lit(n, TORUS_GLASS), TORUS_GLASS[1], 0.55)
                t = p[0] if face in ("north", "south") else p[2]
                m = compact_emblem(t, p[1] - 7)
                if m == 1:
                    c = (236, 255, 226)
                elif m == 2:
                    c = TORUS_GLASS[0]
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


def compact_emblem(t, d, E=2.1):
    def pale(t, d):
        r = math.hypot(t, d)
        return E * 0.52 <= r <= E * 0.86 or (E * 0.9 <= abs(d) <= E * 1.18 and abs(t) <= E * 0.8)
    if pale(t, d):
        return 1
    for a in range(0, 360, 45):
        if pale(t + 0.3 * math.cos(math.radians(a)), d + 0.3 * math.sin(math.radians(a))):
            return 2
    return 0


def compact_cap(p):
    """The cap's top: a dark groove square round a raised plate."""
    e = max(abs(p[0]), abs(p[2]))
    if 2.2 < e < 2.6:
        return GM_DARK
    return None


box("base", (-5, 0, -5), (5, 2, 5), PLINTH)
box("base_rim", (-4.5, 2, -4.5), (4.5, 3, 4.5))
CC("glass", (-4, 3, -4), (4, 11, 4), compact_glass((-4, 3, -4), (4, 11, 4)))
for sx in (-1, 1):
    for sz in (-1, 1):
        cylinder(f"column_{sx}_{sz}", "y", (sx * 3.5, 0, sz * 3.5), 1.25, 3, 11, cube=CC)
box("top_rim", (-4.5, 11, -4.5), (4.5, 12, 4.5))
box("cap", (-3.5, 12, -3.5), (3.5, 13, 3.5), top=compact_cap)


def compact_lens(frm, to):
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                r = math.hypot(p[0], p[1] - 7)
                if face != "north" or r > 1.0:
                    row.append(CLEAR)
                    continue
                row.append(mix((245, 255, 240), (60, 230, 100), r) + (255,))
            rows.append(row)
        return rows
    return paint


for n in ("lens", "glow_lens"):
    CC(n, (-1.5, 5.5, -4.2), (1.5, 8.5, -3.2), compact_lens((-1.5, 5.5, -4.2), (1.5, 8.5, -3.2)))
# The square handle: two posts and a top bar, rounded like wire.
for sx in (-1, 1):
    box(f"handle_post_{sx}", (min(sx * 2, sx * 3), 13, -0.5), (max(sx * 2, sx * 3), 17, 0.5))
box("handle_top", (-3, 17, -0.5), (3, 18, 0.5))
compact.write()


# ---- the Nebula battery's round body (restyled like the Classic) ------------------------------
# The orb is added above; here the green metal and gold rings round it are round slices lit per
# texel, and the dark nebula glass is a round see-through cylinder (radius 5, y 7 to 16) whose
# flowing frames are painted in world space. Only the orb glows. Glass front z -5 (the ring docks
# there, at the orb's height); keep LanternFirstPerson's NEBULA look in step if these move.
def neb_cap(p, r, R, face):
    if face == "up" and r < R - 1.0:
        return (lit((0.0, 0.9, -0.3)) if r < R - 1.4 else GM_DARK) + (255,)
    return None


cylinder("foot", "y", (0, 0, 0), 6, 0, 1, pal=PLINTH, cube=N)
cylinder("base", "y", (0, 0, 0), 5.5, 1, 3, cube=N)
cylinder("base_glass", "y", (0, 0, 0), 5, 3, 5, cube=N, paint=key_glass(5))
cylinder("gold_low", "y", (0, 0, 0), 6, 5, 6, pal=BRASS_PAL, cube=N)
cylinder("rim_low", "y", (0, 0, 0), 5.5, 6, 7, cube=N)
cylinder("rim_high", "y", (0, 0, 0), 5.5, 16, 17, cube=N)
cylinder("gold_high", "y", (0, 0, 0), 6, 17, 18, pal=BRASS_PAL, cube=N)
cylinder("top_ring", "y", (0, 0, 0), 5.5, 18, 20, cube=N)
cylinder("cap", "y", (0, 0, 0), 4, 20, 21, cap=neb_cap, cube=N)
nebula.write()

GLASS_D = CD


def nebula_slice(frm, to, R):
    """One slice of the round glass: its outer faces carry the flowing nebula (world space);
    the faces inside the cylinder and the ends are clear, so the see-through glass never doubles."""
    import numpy as np
    def paint(face, w, h):
        if face in ("up", "down"):
            return [[CLEAR] * w for _ in range(h)]
        (x0, y0, z0), (x1, y1, z1) = frm, to
        a = (np.arange(w) + 0.5) / w
        b = (np.arange(h) + 0.5) / h
        A_, B_ = np.meshgrid(a, b)
        Y = y1 - B_ * (y1 - y0)
        if face == "north":
            X, Z = x1 - A_ * (x1 - x0), np.full_like(A_, z0)
        elif face == "south":
            X, Z = x0 + A_ * (x1 - x0), np.full_like(A_, z1)
        elif face == "east":
            X, Z = np.full_like(A_, x1), z1 - A_ * (z1 - z0)
        else:
            X, Z = np.full_like(A_, x0), z0 + A_ * (z1 - z0)
        px = nebula_field(X, Y, Z, NEBULA_T[0])
        r = np.hypot(X, Z)
        rows = []
        for yy in range(h):
            row = []
            for xx in range(w):
                row.append(CLEAR if r[yy, xx] < R - 1.05 else tuple(int(c) for c in px[yy, xx]))
            rows.append(row)
        return rows
    return paint


glass = Model("nebula_glass", density=GLASS_D)
cylinder("glass", "y", (0, 0, 0), 5, 7, 16, cube=glass.cube, paint=lambda f, t: nebula_slice(f, t, 5))
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


# ---- the Dark Lantern's twisted tower, restyled like the Classic -------------------------------
# Same tower as described above: bevelled plates of smooth dark jade with bright layers
# of the lantern's light between them, a square belt between two fear-gold bands and an arched
# handle. Every box is lit per texel (no speckle or veins); the light layers are painted bright
# but only the round port on the belt glows, where the ring docks.
JADE_PAL = ((16, 66, 44), (34, 124, 82), (164, 236, 194), (80, 172, 120))
FEAR_PAL = ((110, 78, 10), (226, 176, 48), (255, 246, 196), (250, 210, 96))
LIGHT_PAL = ((80, 210, 120), (160, 255, 184), (250, 255, 250), (196, 255, 212))

dark_model = Model("dark_lantern", density=CD)
DL = dark_model.cube


def plate_angle(y):
    """Below the belt the plates turn back toward it, above it they keep turning on."""
    return -TWIST * (6 - y) if y < 6 else (TWIST * (y - 11) if y > 11 else 0.0)


def turned(name, y, frm, to, pal, angle):
    """A 1-unit-high bevelled piece of layer y (x/z given), turned ``angle`` degrees about the axis."""
    f, t = (frm[0], y, frm[1]), (to[0], y + 1, to[1])
    rot = [0, round(angle, 2), 0] if abs(angle) > 1e-6 else None
    DL(name, f, t, bevelled(f, t, pal), rotation=rot, origin=[0, y, 0] if rot else None)


def slab(name, y, half, pal, angle):
    turned(name, y, (-half, -half), (half, half), pal, angle)


def stack(y0, y1):
    for y in range(y0, y1):
        if y % 2 == 0:
            slab(f"light_{y}", y, 3.5, LIGHT_PAL, plate_angle(y))
        else:
            slab(f"plate_{y}", y, 4, JADE_PAL, plate_angle(y))


slab("foot", 0, 5, PLINTH, plate_angle(0))
slab("rim_low", 1, 4.5, FEAR_PAL, plate_angle(1))
stack(2, 6)
slab("belt_gold_low", 6, 4.5, FEAR_PAL, 0)
DL("belt", (-4, 7, -4), (4, 11, 4), bevelled((-4, 7, -4), (4, 11, 4), JADE_PAL))
slab("belt_gold_high", 11, 4.5, FEAR_PAL, 0)
stack(12, 20)
slab("cap", 20, 3.5, JADE_PAL, plate_angle(20))
slab("collar", 21, 2.5, FEAR_PAL, plate_angle(21))
cylinder("neck", "y", (0, 0, 0), 1.25, 22, 23, pal=JADE_PAL, cube=DL)


def dark_port(p, r, R, face):
    """The port's front: a gold rim round the hole the light shows through."""
    if face == "north" and r < 1.3:
        return CLEAR
    if face == "north" and r < 1.6:
        return FEAR_PAL[0] + (255,)
    return None


def dark_lens(frm, to):
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                r = math.hypot(p[0], p[1] - 9)
                if face != "north" or r > 1.4:
                    row.append(CLEAR)
                    continue
                row.append(mix((250, 255, 245), (70, 240, 118), min(1.0, r / 1.4)) + (255,))
            rows.append(row)
        return rows
    return paint


cylinder("port", "z", (0, 9, 0), 2.2, -5, -4, cap=dark_port, pal=FEAR_PAL, cube=DL)
for n in ("lens", "glow_lens"):
    DL(n, (-1.5, 7.5, -4.8), (1.5, 10.5, -3.8), dark_lens((-1.5, 7.5, -4.8), (1.5, 10.5, -3.8)))


def dark_wire(face, w, h):
    c = {"up": FEAR_PAL[2], "down": FEAR_PAL[0]}.get(face, FEAR_PAL[1])
    return [[c + (255,)] * w for _ in range(h)]


# The arched handle in fear's gold, its cells joined edge to edge.
arc = []
for st in range(0, 181, 2):
    a = math.radians(st)
    c = (round(3 * math.cos(a)), math.floor(22 + 3.99 * math.sin(a)))
    if arc and c == arc[-1]:
        continue
    if arc and abs(c[0] - arc[-1][0]) == 1 and abs(c[1] - arc[-1][1]) == 1:
        arc.append((c[0], arc[-1][1]) if c[1] > arc[-1][1] else (arc[-1][0], c[1]))
    arc.append(c)
for x, y in sorted(set(arc)):
    DL(f"handle_{x}_{y}", (x - 0.5, y, -0.5), (x + 0.5, y + 1, 0.5), dark_wire)
dark_model.write()


# ---- the Red Lantern battery (the red corps' lantern): from J's 9-view sheet -------------------
# A bottle of marbled blood-red glass (lit from within, with drips running over
# the base), a stepped copper base, a copper cap with a grille on top, two copper rods round its
# middle tied to the frame, the round copper housing with the red emblem lens on the front (the
# ring docks there), a riveted plate on the back, and a copper frame: a flat bar each side rising
# from the base and flaring out into a spike, a smooth arch over the cap and a round ring to hang
# it by. Diagonal and curved pieces are turned boxes, so they read as solid bars, not steps. The
# copper is a warm red-orange and never tinted by corps. Built and shaded like the Classic. Lens
# centre (0, 11, -7.05); top of the hanging ring y 28. Keep LanternFirstPerson's RED look in step.
COPPER = ((70, 28, 12), (200, 100, 52), (255, 206, 160), (226, 134, 82))
BLOOD_GLASS = ((70, 0, 6), (214, 22, 32), (255, 190, 176), (236, 84, 80))

red = Model("red_lantern", density=CD)
RC = red.cube


def _marble(x, y, z):
    """Marbling in -1..1 from layered, warped waves (smooth, no speckle): streaks that swirl
    round the bottle a few times across its face."""
    w = math.sin(z * 1.1 + y * 0.7) * 1.4 + math.sin(x * 1.3 - y * 0.5) * 1.1
    m = math.sin(x * 1.6 + y * 1.1 + w)
    m += 0.7 * math.sin(z * 1.9 - y * 1.4 + w * 0.8)
    m += 0.4 * math.sin((x - z) * 2.6 + y * 2.1)
    return m / 2.1


def red_glass(R):
    """Blood glass for one slice of a body layer of radius R: lit from within,
    marbled with dark veins and bright swirls, ribbed only round the bottom and the shoulder (as on
    the sheet), and darker where the drips gather at the foot."""
    def factory(frm, to):
        def paint(face, w, h):
            rows = []
            for v in range(h):
                row = []
                for u in range(w):
                    p = _texel(frm, to, face, u, v, w, h)
                    r = math.hypot(p[0], p[2])
                    if face in ("up", "down"):
                        # Painted solid (they sit inside the bottle): clear texels here bled into
                        # the edges of the side faces next to them and drew a dark line per layer.
                        row.append(mix(BLOOD_GLASS[0], BLOOD_GLASS[1], 0.6) + (255,))
                        continue
                    if r < R - 1.05:
                        row.append(CLEAR)
                        continue
                    c = mix(lit(_norm((p[0], 0.0, p[2])), BLOOD_GLASS), BLOOD_GLASS[1], 0.5)
                    m = _marble(p[0], p[1], p[2])
                    if m > 0.25:
                        c = mix(c, (255, 110, 96), min(1.0, (m - 0.25) * 1.3))
                    elif m < -0.3:
                        c = mix(c, (60, 0, 6), min(0.85, (-0.3 - m) * 1.7))
                    y = p[1]
                    if y < 7 or y > 15:
                        f = y % 1.0
                        if f > 0.8:
                            c = mix(c, BLOOD_GLASS[2], 0.15)
                        elif f < 0.15:
                            c = mix(c, BLOOD_GLASS[0], 0.25)
                    a = math.atan2(p[2], p[0])
                    if y < 4.4 + 1.6 * max(0.0, math.sin(a * 7 + 0.5)) ** 4:
                        c = mix(c, (120, 0, 12), 0.5)
                    row.append(c + (255,))
                rows.append(row)
            return rows
        return paint
    return factory


def body_r(y):
    """The bottle's radius at height y: full and round low down, easing in toward the cap."""
    return 5.3 if y < 12 else 5.3 - 0.18 * (y - 12)


def grille(p, r, R, face):
    """The cap's top: a brass disc inside a ring of dark slots."""
    if face != "up":
        return None
    if r < 2.4:
        return lit((0.0, 0.85, -0.5), ((90, 66, 20), (196, 160, 70), (255, 236, 160), (220, 180, 90))) + (255,)
    if r < 3.2:
        a = math.degrees(math.atan2(p[2], p[0])) % 20
        return ((24, 10, 6) if a < 9 else COPPER[1]) + (255,)
    return None


def carved(p, r, R, face):
    """The underside: carved rings and four small round emblems."""
    if face != "down":
        return None
    for ring in (R - 1.1, 3.7, 2.0):
        if abs(r - ring) < 0.22:
            return COPPER[0] + (255,)
    for ang in (0, 90, 180, 270):
        ex, ez = 4.4 * math.cos(math.radians(ang)), 4.4 * math.sin(math.radians(ang))
        e = math.hypot(p[0] - ex, p[2] - ez)
        if 0.35 < e < 0.65 or (e < 0.2):
            return COPPER[0] + (255,)
    return None


# Base, the glass bottle layer by layer, and the cap. Each glass slice is drawn solid and again as
# glow on top, so it shines from within (brighter as the lantern charges) whatever light is around;
# see-through glass drew its layers over each other in bands.
cylinder("base_foot", "y", (0, 0, 0), 6, 0, 1, cap=carved, pal=COPPER, cube=RC)
cylinder("base_step", "y", (0, 0, 0), 5.7, 1, 2, pal=COPPER, cube=RC)
cylinder("base_lip", "y", (0, 0, 0), 5.5, 2, 4, pal=COPPER, cube=RC)
for y in range(4, 17):
    R = body_r(y + 0.5)
    # Slices on one fixed grid (centred on whole units) for every layer, so the layers line up
    # instead of shifting like bricks as the radius eases in.
    for k in range(-5, 6):
        hw = half(math.sqrt(max(R * R - k * k, 0)) + 0.15)
        if hw <= 0 or abs(k) > R:
            continue
        frm, to = (k - 0.5, y, -hw), (k + 0.5, y + 1, hw)
        paint = red_glass(R)(frm, to)
        RC(f"body_{y}_{k + 5}", frm, to, paint)
        RC(f"glow_body_{y}_{k + 5}", frm, to, paint, share=f"body_{y}_{k + 5}")


def drip(face, w, h):
    return [[(mix(BLOOD_GLASS[1], BLOOD_GLASS[2], 0.3) if face == "up" else BLOOD_GLASS[1]) + (255,)] * w for _ in range(h)]


# Blood running down over the base's lip: thin drips of different lengths.
for i in range(11):
    a = math.radians(i * 360 / 11 + 9)
    x, z = 5.55 * math.cos(a), 5.55 * math.sin(a)
    length = (1, 2, 1, 1, 2)[i % 5]
    x, z = round(x * 4) / 4, round(z * 4) / 4
    RC(f"drip_{i}", (x - 0.5, 4 - length, z - 0.5), (x + 0.5, 4, z + 0.5), drip, inflate=-0.3,
       rotation=[0, -math.degrees(a), 0])
cylinder("cap_lip", "y", (0, 0, 0), 4.4, 17, 18, pal=COPPER, cube=RC)
cylinder("cap", "y", (0, 0, 0), 4.0, 18, 20, pal=COPPER, cube=RC)
cylinder("cap_top", "y", (0, 0, 0), 3.6, 20, 21, cap=grille, pal=COPPER, cube=RC)
# Two copper rods round the middle.
cylinder("rod_low", "y", (0, 0, 0), 5.9, 9, 10, pal=COPPER, cube=RC)
cylinder("rod_high", "y", (0, 0, 0), 5.9, 12, 13, pal=COPPER, cube=RC)


def red_housing(p, r, R, face):
    if face == "north" and r < 2.1:
        return CLEAR
    if face == "north" and r < 2.45:
        return (30, 6, 4, 255)
    return None


def red_lens(frm, to):
    """The red lens: blazing red with the emblem in dark blood: a ring, a bar across it and two
    horns above, like the Red Lantern symbol. Only the front shows."""
    def paint(face, w, h):
        rows = []
        for v in range(h):
            row = []
            for u in range(w):
                p = _texel(frm, to, face, u, v, w, h)
                dx, dy = p[0], p[1] - 11
                r = math.hypot(dx, dy)
                if face != "north" or r > 2.15:
                    row.append(CLEAR)
                    continue
                c = mix((255, 236, 220), (255, 50, 40), min(1.0, r / 1.1))
                if r > 1.5:
                    c = mix((255, 50, 40), (200, 10, 20), (r - 1.5) / 0.65)
                dark = 1.15 < r < 1.5 or (abs(dy) < 0.2 and r < 1.15) or \
                    (dy > 1.1 and abs(abs(dx) - 0.75) < 0.2 and r < 2.0)
                if dark:
                    c = (70, 0, 8)
                row.append(c + (255,))
            rows.append(row)
        return rows
    return paint


# The emblem housing on the front and its lens; the riveted plate on the back.
cylinder("housing", "z", (0, 11, 0), 3, -7, -5, cap=red_housing, pal=COPPER, cube=RC)
# The lens is drawn solid as well as glowing, so it stays red-hot even while the glow is low.
RC("lens", (-2, 9, -6.8), (2, 13, -5.8), red_lens((-2, 9, -6.8), (2, 13, -5.8)))
RC("glow_lens", (-2, 9, -6.8), (2, 13, -5.8), red_lens((-2, 9, -6.8), (2, 13, -5.8)))


def plate(face, w, h):
    """The riveted copper plate: lit flat face, bevelled edge, a rivet at each corner and side."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = lit(_norm((0.0, 0.35 - 0.7 * y / max(h - 1, 1), 1.0)), COPPER)
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if face == "south":
                if edge == 0:
                    c = COPPER[2] if y < h / 2 else COPPER[0]
                for rx, ry in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3), (w // 2, 2), (w // 2, h - 3), (2, h // 2), (w - 3, h // 2)):
                    if abs(x - rx) <= 1 and abs(y - ry) <= 1:
                        c = COPPER[2] if (x - rx) + (y - ry) < 0 else COPPER[0]
            row.append(c + (255,))
        rows.append(row)
    return rows


RC("back_plate", (-2.5, 8.5, 5), (2.5, 13.5, 6), plate)


def bar(name, centre, length, angle, thick=1, deep=1, inflate=0.0):
    """A copper bar ``length`` long centred on (x, y) in the front plane, turned ``angle``
    degrees from horizontal about Z, so slanted and curved pieces stay solid."""
    cx, cy = centre
    frm = (cx - length / 2, cy - thick / 2, -deep / 2)
    to = (cx + length / 2, cy + thick / 2, deep / 2)
    rot = [0, 0, round(angle, 2)] if abs(angle) > 1e-6 else None
    RC(name, frm, to, bevelled(frm, to, COPPER, bev=0.3), inflate=inflate, rotation=rot,
       origin=[cx, cy, 0] if rot else None)


# The frame: a flat bar each side from the base up past the cap, flaring out into a spike.
for s in (-1, 1):
    bar(f"frame_bar_{s}", (s * 7.5, 10.5), 17, 90, thick=2)
    bar(f"frame_spike_{s}", (s * 8.62, 21.4), 6, 90 - s * 22, thick=2)
    bar(f"frame_foot_{s}", (s * 6.0, 2.5), 2, 0)
    for y in (9.5, 12.5):
        bar(f"frame_rod_{s}_{y}", (s * 6.0, y), 2, 0)
# The arch over the cap, from bar to bar, in overlapping turned segments.
N_ARCH = 12
for i in range(N_ARCH):
    t = math.pi * (i + 0.5) / N_ARCH
    x, y = 7 * math.cos(t), 18.6 + 5.0 * math.sin(t)
    ang = math.degrees(math.atan2(5.0 * math.cos(t), -7 * math.sin(t)))
    bar(f"frame_arch_{i}", (x, y), 2, ang, inflate=-0.08)
# The hanging ring: a round loop of turned segments on top of the arch.
RING_C, RING_R = (0.0, 25.7), 1.6
for i in range(16):
    t = 2 * math.pi * i / 16
    x, y = RING_C[0] + RING_R * math.cos(t), RING_C[1] + RING_R * math.sin(t)
    bar(f"ring_{i}", (x, y), 1, math.degrees(t) + 90, inflate=-0.12)
red.write()


BRONZE = ((70, 44, 18), (172, 118, 60), (252, 216, 164), (206, 152, 92))


# ---- the Sinestro Corps lantern (the yellow corps' lantern): from J's sheet -----------------------
# A tall square cage of old bronze: four corner posts studded with spikes, rails top and bottom with
# spikes underneath, splayed feet, a stepped pyramid roof with a curved horn rising from each corner
# and a round ring on top. The front and both sides are windows of swirling yellow light with the
# Sinestro emblem, each under a bronze skull; the back is a tablet of runes; the underside carries
# the emblem in a ring of runes. Lit per texel like the Classic battery, no noise. Front emblem
# centre (0, 8, -4.65); top of the ring y 24.5. Keep LanternFirstPerson's YELLOW look in step.
SIN_BRONZE = ((48, 36, 12), (150, 118, 50), (240, 218, 146), (190, 158, 82))
FEAR = (255, 214, 30)
FEAR_PALE = (255, 250, 200)
FEAR_DEEP = (190, 120, 0)

sin = Model("yellow_lantern", density=CD)
SC = sin.cube


def sbox(name, frm, to, inflate=0.0, top=None):
    SC(name, frm, to, bevelled(frm, to, SIN_BRONZE, bev=0.35, top=top), inflate=inflate)


def sinestro_emblem(t, d):
    """The Sinestro Corps emblem: a ring round a small ring, with a bracket bar each side."""
    r = math.hypot(t, d)
    return (1.55 < r < 2.05 or 0.55 < r < 0.95
            or (2.4 < abs(t) < 2.8 and abs(d) < 1.5)
            or (abs(d) > 1.2 and abs(d) < 1.55 and 2.05 < abs(t) < 2.8))


def fear_light(t, d, glow=False):
    """A window's oval of swirling yellow light with the emblem in dark gold, or None outside."""
    e = (t / 2.8) ** 2 + (d / 4.6) ** 2
    if e > 1:
        return None
    r = math.hypot(t, d * 0.7)
    a = math.atan2(d, t)
    swirl = math.sin(a * 2 + r * 2.2) * 0.5 + 0.5
    c = mix(FEAR_PALE, FEAR, min(1.0, r / 2.0))
    c = mix(c, FEAR_PALE, 0.55 * swirl)
    c = mix(c, FEAR_DEEP, 0.25 * (1 - swirl) * min(1.0, r / 2.5))
    c = mix(c, FEAR_DEEP, max(0.0, e - 0.75) * 2.4)
    if sinestro_emblem(t, d):
        c = (92, 60, 0)
    return c


def window(frm, to, face_name, glow):
    """A window plate: bronze with the oval of light cut in it (``glow``: only the light, on a box
    that stands just proud of the plate)."""
    base = bevelled(frm, to, SIN_BRONZE, bev=0.35)

    def paint(face, w, h):
        rows = base(face, w, h) if not glow else [[CLEAR] * w for _ in range(h)]
        if face != face_name:
            return rows
        for v in range(h):
            for u in range(w):
                x, y, z = _texel(frm, to, face, u, v, w, h)
                t = x if face in ("north", "south") else z
                k = fear_light(t, y - 8, glow)
                if k is not None:
                    rows[v][u] = k + (255,)
                elif not glow:
                    e = (t / 2.8) ** 2 + ((y - 8) / 4.6) ** 2
                    if e < 1.3:
                        rows[v][u] = SIN_BRONZE[0] + (255,)  # the oval's sunken rim
        return rows
    return paint


def runes(frm, to):
    """The back tablet: a bronze plate with an oval border and rows of carved runes."""
    base = bevelled(frm, to, SIN_BRONZE, bev=0.35)

    def paint(face, w, h):
        rows = base(face, w, h)
        if face != "south":
            return rows
        for v in range(h):
            for u in range(w):
                x, y, z = _texel(frm, to, face, u, v, w, h)
                e = (x / 2.8) ** 2 + ((y - 8) / 4.6) ** 2
                if 0.9 < e < 1.12:
                    rows[v][u] = SIN_BRONZE[0] + (255,)
                    continue
                if e < 0.8:
                    row_i = math.floor((y - 4.6) / 1.6)
                    fy = (y - 4.6) % 1.6
                    col_i = math.floor((x + 3) / 1.0)
                    fx = (x + 3) % 1.0
                    seed = (row_i * 7 + col_i * 13) % 5
                    stroke = (seed == 0 and abs(fx - 0.5) < 0.12) or (seed == 1 and abs(fy - 0.6) < 0.12) or \
                        (seed == 2 and abs(fx - fy * 0.6) < 0.12) or (seed == 3 and abs(fx - 0.5) < 0.12 and fy > 0.6) or \
                        (seed == 4 and abs(fy - 0.3) < 0.12 and fx < 0.7)
                    if 0.2 < fy < 1.25 and stroke:
                        rows[v][u] = SIN_BRONZE[0] + (255,)
        return rows
    return paint


def underside(p):
    return None


# Corner posts, splayed feet and the rails top and bottom.
for sx in (-1, 1):
    for sz in (-1, 1):
        x0, x1 = sorted((sx * 3, sx * 5))
        z0, z1 = sorted((sz * 3, sz * 5))
        sbox(f"post_{sx}_{sz}", (x0, 1, z0), (x1, 15, z1))
        fx0, fx1 = sorted((sx * 3.5, sx * 5.5))
        fz0, fz1 = sorted((sz * 3.5, sz * 5.5))
        sbox(f"foot_{sx}_{sz}", (fx0, 0, fz0), (fx1, 1, fz1))
        # Spikes up the post's two outer faces.
        for y in (4, 7, 10, 13):
            xs = (x1, x1 + 1) if sx > 0 else (x0 - 1, x0)
            zs = (z1, z1 + 1) if sz > 0 else (z0 - 1, z0)
            sbox(f"spike_x_{sx}_{sz}_{y}", (xs[0], y, sz * 4 - 0.5), (xs[1], y + 1, sz * 4 + 0.5), inflate=-0.22)
            sbox(f"spike_z_{sx}_{sz}_{y}", (sx * 4 - 0.5, y, zs[0]), (sx * 4 + 0.5, y + 1, zs[1]), inflate=-0.22)
for name, frm, to in (("rail_low_n", (-3, 1, -5), (3, 3, -4)), ("rail_low_s", (-3, 1, 4), (3, 3, 5)),
                      ("rail_low_w", (-5, 1, -3), (-4, 3, 3)), ("rail_low_e", (4, 1, -3), (5, 3, 3)),
                      ("rail_top_n", (-3, 13, -5), (3, 15, -4)), ("rail_top_s", (-3, 17, 4), (3, 19, 5)),
                      ("rail_top_w", (-5, 13, -3), (-4, 15, 3)), ("rail_top_e", (4, 13, -3), (5, 15, 3))):
    sbox(name, frm, to)
# Spikes under the bottom rails.
for i, x in enumerate((-2, 0, 2)):
    sbox(f"drop_n_{i}", (x - 0.5, 0, -5), (x + 0.5, 1, -4), inflate=-0.22)
    sbox(f"drop_s_{i}", (x - 0.5, 0, 4), (x + 0.5, 1, 5), inflate=-0.22)
    sbox(f"drop_w_{i}", (-5, 0, x - 0.5), (-4, 1, x + 0.5), inflate=-0.22)
    sbox(f"drop_e_{i}", (4, 0, x - 0.5), (5, 1, x + 0.5), inflate=-0.22)


def emblem_floor(p):
    """The underside: the emblem in a ring of runes (seen from below)."""
    return None


def bottom(frm, to):
    base = bevelled(frm, to, SIN_BRONZE, bev=0.35)

    def paint(face, w, h):
        rows = base(face, w, h)
        if face != "down":
            return rows
        for v in range(h):
            for u in range(w):
                x, y, z = _texel(frm, to, face, u, v, w, h)
                r = math.hypot(x, z)
                mark = abs(r - 4.2) < 0.15 or abs(r - 3.2) < 0.15 or sinestro_emblem(x * 1.0, z * 1.0)
                if 3.35 < r < 4.05 and (math.degrees(math.atan2(z, x)) % 15) < 5:
                    mark = True
                if mark:
                    rows[v][u] = SIN_BRONZE[0] + (255,)
        return rows
    return paint


SC("floor", (-4, 1, -4), (4, 2, 4), bottom((-4, 1, -4), (4, 2, 4)))
# The windows (front and sides) and the rune tablet (back), set in between the posts.
for name, frm, to, face in (("window_n", (-3, 3, -4.5), (3, 13, -3.5), "north"),
                            ("window_w", (-4.5, 3, -3), (-3.5, 13, 3), "west"),
                            ("window_e", (3.5, 3, -3), (4.5, 13, 3), "east")):
    SC(name, frm, to, window(frm, to, face, False))
for name, frm, to, face in (("glow_n", (-3, 3, -4.6), (3, 13, -3.6), "north"),
                            ("glow_w", (-4.6, 3, -3), (-3.6, 13, 3), "west"),
                            ("glow_e", (3.6, 3, -3), (4.6, 13, 3), "east")):
    SC(name, frm, to, window(frm, to, face, True))
SC("tablet", (-3, 3, 3.5), (3, 13, 4.5), runes((-3, 3, 3.5), (3, 13, 4.5)))


def skull(frm, to, face_name):
    """A small bronze skull: lit dome, two dark eye sockets, a nose and a row of teeth."""
    base = bevelled(frm, to, SIN_BRONZE, bev=0.45)

    def paint(face, w, h):
        rows = base(face, w, h)
        if face != face_name:
            return rows
        for v in range(h):
            for u in range(w):
                x, y, z = _texel(frm, to, face, u, v, w, h)
                t = (x if face in ("north", "south") else z) - (frm[0] + to[0]) / 2 * (face in ("north", "south")) \
                    - (frm[2] + to[2]) / 2 * (face in ("east", "west"))
                d = y - (frm[1] + to[1]) / 2
                if math.hypot(abs(t) - 0.75, d - 0.15) < 0.42:
                    rows[v][u] = (20, 14, 4, 255)
                elif abs(t) < 0.2 and -0.55 < d < -0.2:
                    rows[v][u] = (30, 22, 6, 255)
                elif -1.4 < d < -0.85 and abs(t) < 0.9 and (int((t + 1) * 4) % 2 == 0):
                    rows[v][u] = (40, 30, 8, 255)
        return rows
    return paint


# A skull over each window, on the top rail.
for name, frm, to, face in (("skull_n", (-1.5, 12, -5.5), (1.5, 15, -4.5), "north"),
                            ("skull_w", (-5.5, 12, -1.5), (-4.5, 15, 1.5), "west"),
                            ("skull_e", (4.5, 12, -1.5), (5.5, 15, 1.5), "east")):
    SC(name, frm, to, skull(frm, to, face))
# The stepped pyramid roof with a cross ridge on top.
for i, (hw, y) in enumerate(((5.5, 15), (4.5, 16), (3.5, 17), (2.5, 18), (1.5, 19))):
    sbox(f"roof_{i}", (-hw, y, -hw), (hw, y + 1, hw))
sbox("ridge_x", (-2.5, 19, -0.5), (2.5, 20, 0.5))
sbox("ridge_z", (-0.5, 19, -2.5), (0.5, 20, 2.5))
sbox("neck", (-0.5, 20, -0.5), (0.5, 21, 0.5))
# A curved horn rising from each corner of the roof.
for sx in (-1, 1):
    for sz in (-1, 1):
        for i, (o, y, inf) in enumerate(((5.0, 15, 0.0), (5.6, 16, -0.05), (5.9, 17, -0.12), (5.9, 18, -0.2),
                                         (5.6, 19, -0.3))):
            sbox(f"horn_{sx}_{sz}_{i}", (sx * o - 0.5, y, sz * o - 0.5), (sx * o + 0.5, y + 1, sz * o + 0.5), inflate=inf)


def ring_bar(name, centre, length, angle, inflate):
    cx, cy = centre
    frm, to = (cx - length / 2, cy - 0.5, -0.5), (cx + length / 2, cy + 0.5, 0.5)
    SC(name, frm, to, bevelled(frm, to, SIN_BRONZE, bev=0.3), inflate=inflate,
       rotation=[0, 0, round(angle, 2)], origin=[cx, cy, 0])


# The round ring to hang it by.
for i in range(16):
    t = 2 * math.pi * i / 16
    ring_bar(f"ring_{i}", (1.6 * math.cos(t), 22.4 + 1.6 * math.sin(t)), 1, math.degrees(t) + 90, -0.12)
sin.write()


# ---- the mesh kit: flat facets and lathed shapes ---------------------------------------------------
# The older lanterns are stacks of one-unit boxes, so anything round or slanted steps like a staircase
# and every slanted line is painted onto the steps at 4 pixels per unit. These helpers build a lantern
# the way J's sheets draw it instead: every flat facet of the real shape is one zero-thickness plate
# turned to face its own way (any convex polygon: the texels outside it are clear), and round parts
# are lathed from a profile into N facets. Each texel is shaded from the real surface it stands for and
# averaged over SS x SS samples, so emblems and edges stay smooth at MD pixels per unit. Compare a
# model with its sheet using tools/bbmodel_preview.py.
MD = 8
SS = 3


def _add(a, b, k=1.0):
    return tuple(a[i] + b[i] * k for i in range(3))


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _euler(cu, cv, cw):
    """Blockbench's [x, y, z] degrees (R = Rz Ry Rx, as ModelPart and 26.x JSON models apply it) for
    the rotation whose columns are cu, cv, cw."""
    sb = max(-1.0, min(1.0, -cu[2]))
    b = math.asin(sb)
    if abs(math.cos(b)) > 1e-6:
        a = math.atan2(cv[2], cw[2])
        g = math.atan2(cu[1], cu[0])
    else:
        a, g = math.atan2(-cw[1], cv[1]), 0.0
    out = [round(math.degrees(x), 4) for x in (a, b, g)]
    return None if all(abs(x) < 1e-4 for x in out) else out


def plate(model, name, pts, shader, out=None, lift=0.0):
    """One flat facet. ``pts`` are its corners (3 or more, coplanar, convex, in any order); it faces
    along ``out`` (a rough outward direction). ``shader(p, n)`` gives the RGB colour at model point
    p (None for a clear texel); ``lift`` moves the facet out along its normal (light over a face)."""
    c0 = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
    n = (0.0, 0.0, 0.0)
    for i in range(len(pts)):  # Newell's normal, steady for any vertex order of a convex polygon
        a, b = _sub(pts[i], c0), _sub(pts[(i + 1) % len(pts)], c0)
        n = _add(n, _cross(a, b))
    n = _norm(n)
    if out is not None and _dot(n, out) < 0:
        n = tuple(-x for x in n)
    pts = [_add(p, n, lift) for p in pts]
    c0 = _add(c0, n, lift)
    # Line the texture up with the longest edge, so long thin facets (bars) get straight, crisp
    # edges and a small rectangle instead of a stair-stepped diagonal across a big one.
    longest = max(((pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))), key=lambda e: math.dist(*e))
    up = _sub(longest[1], longest[0])
    if up[1] < 0 or (abs(up[1]) < 1e-9 and up[0] + up[2] < 0):
        up = tuple(-x for x in up)
    ev = _norm(_add(up, n, -_dot(up, n)))
    eu = _cross(n, ev)
    st = [(_dot(_sub(p, c0), eu), _dot(_sub(p, c0), ev)) for p in pts]
    k = model.density
    s0, s1 = min(s for s, _ in st), max(s for s, _ in st)
    t0, t1 = min(t for _, t in st), max(t for _, t in st)
    w = max(1, math.ceil((s1 - s0) * k - 1e-6)) / k
    h = max(1, math.ceil((t1 - t0) * k - 1e-6)) / k
    sm, tm = (s0 + s1) / 2, (t0 + t1) / 2
    c = _add(_add(c0, eu, sm), ev, tm)
    poly = [(s - sm, t - tm) for s, t in st]
    mx, my = sum(s for s, _ in poly) / len(poly), sum(t for _, t in poly) / len(poly)
    poly.sort(key=lambda q: math.atan2(q[1] - my, q[0] - mx))
    edges = []
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
        ln = math.hypot(bx - ax, by - ay)
        if ln > 1e-9:
            edges.append((ax, ay, (bx - ax) / ln, (by - ay) / ln))
    grow = 0.6 / k

    def inside(s, t):
        return all((ex * (t - ay) - ey * (s - ax)) >= -grow for ax, ay, ex, ey in edges)

    def paint(face, wp, hp):
        if face != "north":
            return [[CLEAR] * wp for _ in range(hp)]
        rows = []
        for v in range(hp):
            row = []
            for u in range(wp):
                ds, dt = w / 2 - (u + 0.5) / wp * w, h / 2 - (v + 0.5) / hp * h
                if not inside(ds, dt):
                    row.append(CLEAR)
                    continue
                acc, hits = [0, 0, 0], 0
                for i in range(SS):
                    for j in range(SS):
                        a = w / 2 - (u + (i + 0.5) / SS) / wp * w
                        b = h / 2 - (v + (j + 0.5) / SS) / hp * h
                        col = shader(_add(_add(c, eu, a), ev, b), n)
                        if col is not None:
                            hits += 1
                            for q in range(3):
                                acc[q] += col[q]
                row.append(CLEAR if hits * 2 < SS * SS else tuple(clamp(x / hits) for x in acc) + (255,))
            rows.append(row)
        return rows
    frm = (c[0] - w / 2, c[1] - h / 2, c[2])
    to = (c[0] + w / 2, c[1] + h / 2, c[2])
    model.cube(name, frm, to, paint, rotation=_euler(eu, ev, tuple(-x for x in n)), origin=list(c))
    return n


def lathe(model, name, profile, sides, shader, base=(0.0, 0.0, 0.0), axis=(0.0, 1.0, 0.0),
          phase=0.0, smooth=True, caps=(True, True)):
    """A round part: ``profile`` lists (along, radius) pairs from one end to the other, turned about
    ``axis`` through ``base``, each step making ``sides`` facets (theta 0 faces the front for an
    upright part). Smooth parts are shaded from the round surface, so 16-24 sides read as round;
    flat ones (``smooth=False``) keep crisp facets, e.g. an octagonal tier with phase 22.5. The ends
    get flat caps where their radius is above 0. ``shader(p, n)`` colours it."""
    A = _norm(axis)
    B2 = (0.0, 0.0, -1.0) if abs(A[1]) > 0.9 else (0.0, 1.0, 0.0)
    B1 = _cross(B2, A) if abs(A[1]) > 0.9 else _cross(A, B2)

    def at(y, r, th):
        return _add(_add(_add(base, A, y), B1, r * math.sin(th)), B2, r * math.cos(th))

    def radial(p):
        d = _sub(p, base)
        return _norm(_add(d, A, -_dot(d, A)))
    step = 2 * math.pi / sides
    ph = math.radians(phase)
    for j in range(len(profile) - 1):
        (y0, r0), (y1, r1) = profile[j], profile[j + 1]
        if r0 == 0 and r1 == 0:
            continue
        for i in range(sides):
            ta, tb = ph + i * step, ph + (i + 1) * step
            pts = [at(y0, r0, ta), at(y0, r0, tb), at(y1, r1, tb), at(y1, r1, ta)]
            pts = [p for q, p in enumerate(pts) if all(_dot(_sub(p, o), _sub(p, o)) > 1e-9 for o in pts[:q])]
            if abs(y1 - y0) < 1e-9:
                out = tuple(x * (1 if r1 < r0 else -1) for x in A)
                sh = (lambda o: (lambda p, n: shader(p, o)))(out)
            else:
                mid = (ta + tb) / 2
                out = _add(_add((0, 0, 0), B1, math.sin(mid)), B2, math.cos(mid))
                if smooth:
                    dy, dr = y1 - y0, r0 - r1
                    sh = (lambda dy, dr: (lambda p, n: shader(p, _norm(_add(tuple(x * dy for x in radial(p)), A, dr)))))(dy, dr)
                else:
                    sh = shader
            plate(model, f"{name}_{j}_{i}", pts, sh, out=out)
    for end, (y, r), sign in ((0, profile[0], -1), (1, profile[-1], 1)):
        if caps[end] and r > 0:
            pts = [at(y, r, ph + i * step) for i in range(sides)]
            out = tuple(x * sign for x in A)
            plate(model, f"{name}_cap{end}", pts, (lambda o: (lambda p, n: shader(p, o)))(out), out=out)


def _hash3(i, j, k, seed):
    h = (i * 374761393 + j * 668265263 + k * 2147483647 + seed * 144269504) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 0xFFFFFFFF


def mottle(p, scale=1.6, seed=0):
    """Soft, large-scale variation in -1..1 (two octaves of smooth value noise): enough to read as
    worn stone or cast metal without the pixel speckle J dislikes."""
    tot = 0.0
    for octave, amp in ((1.0, 0.65), (2.1, 0.35)):
        x, y, z = (c / scale * octave for c in p)
        i, j, k = math.floor(x), math.floor(y), math.floor(z)
        fx, fy, fz = x - i, y - j, z - k
        fx, fy, fz = (t * t * (3 - 2 * t) for t in (fx, fy, fz))
        v = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    wgt = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                    v += wgt * _hash3(i + dx, j + dy, k + dz, seed + int(octave * 10))
        tot += amp * (v * 2 - 1)
    return tot


def _seg_dist(p, a, b):
    ab = _sub(b, a)
    t = max(0.0, min(1.0, _dot(_sub(p, a), ab) / max(1e-9, _dot(ab, ab))))
    return math.dist(p, _add(a, ab, t))


def edge_dist(pts):
    """How far a point on a facet lies from the facet's nearest edge (for bevels and panel lines)."""
    segs = list(zip(pts, pts[1:] + pts[:1]))
    return lambda p: min(_seg_dist(p, a, b) for a, b in segs)


def finish(col, d, pal, wear=0.0, lines=True):
    """Hand-made finish on a facet ``d`` from its edge: a bright worn bevel right on the edge, a dark
    shadow line just inside it, then a thin catch of light, so every panel reads as cut and fitted
    the way J's sheets draw them instead of as flat colour."""
    if d < 0.11:
        return mix(col, pal[2], 0.30 + wear)
    if d < 0.2:
        return mix(col, pal[2], 0.12)
    if lines and 0.34 < d < 0.44:
        return mix(col, pal[0], 0.55)
    if lines and 0.44 <= d < 0.52:
        return mix(col, pal[2], 0.18)
    return col


# ---- the Blue Lantern battery (the blue corps' lantern): from J's sheet, built with the mesh kit -----
# A block of blue stone with every edge chamfered (12 slanted strips and 8 corner triangles, as on
# the sheet), on a stepped octagonal stone foot with a bronze plate underneath, a two-tier bronze cap
# and a squared stone loop handle with stepped corners. Each of its four faces shows the power source
# (J: "show on all sides", "more blue"): a glowing octagonal window with the Blue Lantern emblem in
# front and behind, and a glowing orb round a bronze port on each side. Front emblem centre
# (0, 9, -5.55); handle top y 22.4. Keep LanternFirstPerson's BLUE look in step if these move.
BLUE_STONE = ((28, 42, 70), (72, 104, 152), (178, 200, 226), (102, 136, 182))  # slate blue, as the sheet
HOPE = (36, 112, 255)
HOPE_PALE = (226, 244, 255)
HOPE_INK = (14, 46, 160)

blue = Model("blue_lantern", density=MD)
BS, BY = 5.5, 9.0       # half size of the stone block, its centre height
BCH = 1.9               # how far each chamfer cuts in
BW = 3.05               # the windows' half size (big, as on the sheet)
BFR = 0.3               # the bevelled frame round each window


def oct_k(s, t):
    """An octagon's 'radius' at (s, t): its half size where the point lies on its outline."""
    return max(abs(s), abs(t), (abs(s) + abs(t)) / 1.3)


def blue_stone(p, n, dark=0.0):
    c = shade(lit(n, BLUE_STONE), 1 + 0.13 * mottle(p, 1.1, 3) + 0.05 * mottle(p, 0.35, 9))[:3]
    if abs(mottle(p, 1.7, 21)) < 0.018:   # fine hairline cracks wandering through the stone
        c = mix(c, BLUE_STONE[0], 0.45)
    # A little darker low down, like the sheet's soft shadow under the bulge.
    return mix(c, BLUE_STONE[0], 0.12 * max(0.0, (BY - p[1]) / BS) + dark)


def face_coords(p, n):
    """(across, up) on a body face, from its centre, seen from outside."""
    if abs(n[2]) > 0.9:
        return (-p[0] if n[2] < 0 else p[0]), p[1] - BY
    return (p[2] if n[0] < 0 else -p[2]), p[1] - BY


def blue_face(p, n):
    """A flat face of the block: a groove just inside its edge and the window's bevelled frame (the
    light itself is a separate glowing plate)."""
    s, t = face_coords(p, n)
    e = max(abs(s), abs(t))
    k = oct_k(s, t)
    if BW + BFR <= k < BW + BFR + 0.26:
        # A raised octagonal rim round the window: lit top edge, shadowed foot.
        d = (k - BW - BFR) / 0.26
        col = blue_stone(p, n)
        if d > 0.82:
            return mix(col, BLUE_STONE[0], 0.6)
        return mix(col, BLUE_STONE[2], 0.22 * (1 - d))
    if k < BW + BFR:
        # The frame slopes down into the window: lit as if tipped inward.
        if k < BW:
            return HOPE_INK
        d = (k - BW) / BFR
        tip = 0.7 * (1 - d)
        sx = s / max(k, 1e-6)
        ty = t / max(k, 1e-6)
        if abs(n[2]) > 0.9:
            nn = _norm((sx * tip if n[2] > 0 else -sx * tip, -ty * tip, n[2]))
        else:
            nn = _norm((n[0], -ty * tip, (-sx * tip if n[0] > 0 else sx * tip)))
        col = lit(nn, BLUE_STONE)
        if d < 0.18:
            col = mix(col, BLUE_STONE[0], 0.6)
        return col
    return blue_stone(p, n)


def blue_emblem(s, t):
    """The Blue Lantern emblem from the sheet, in pale light: an outer ring, a ring inside it joined
    to it by four short spokes, and a bright disc in the middle. Returns 2 for a line, 1 for the dark
    ink just round it, 0 for the light behind."""
    r = math.hypot(s, t)

    def line(s, t):
        r = math.hypot(s, t)
        return (2.05 < r < 2.42 or 1.12 < r < 1.42 or r < 0.62
                or ((abs(s) < 0.17 or abs(t) < 0.17) and 1.3 < r < 2.2))
    if line(s, t):
        return 2
    if any(line(s + 0.16 * math.cos(a), t + 0.16 * math.sin(a)) for a in (0, 1.57, 3.14, 4.71, 0.8, 2.4, 3.9, 5.5)):
        return 1
    return 0 if r < 2.62 else 1


def hope_light(emblem):
    def shade_(p, n):
        c = _hope(p, n)
        s, t = face_coords(p, n)
        k = oct_k(s, t)
        if k > BW - 0.35:   # the glass sinks under the frame: a deep blue shadow round its edge
            c = mix(c, HOPE_INK, 0.65 * (k - (BW - 0.35)) / 0.35)
        return c

    def _hope(p, n):
        s, t = face_coords(p, n)
        r = math.hypot(s, t)
        if emblem:
            m = blue_emblem(s * 2.85 / BW, t * 2.85 / BW)
            if m == 2:
                return mix(HOPE_PALE, (150, 210, 255), min(1.0, r / (2.4 * BW / 2.85)) * 0.6)
            if m == 1:
                return HOPE_INK
            return mix(mix(HOPE, HOPE_PALE, 0.35), HOPE, min(1.0, r / 2.0))
        # The orb round a side port: palest near the port, deep blue at the window's edge.
        return mix(HOPE_PALE, HOPE, min(1.0, max(0.0, (r - 1.0) / (BW - 0.9))) ** 0.8)
    return shade_


# The block: six faces, twelve chamfers and eight corner triangles. It is drawn as a cube and then
# widened by BK across x and z, so it sits squat and broad like the sheet's body; shaders see the
# cube's own coordinates, so the windows and emblems keep their round shapes.
BK = 1.09


def bplate(name, pts, shader, out=None, lift=0.0, panel=True):
    wide = [(x * BK, y, z * BK) for x, y, z in pts]
    ed = edge_dist(pts)

    def sh(p, n):
        q = (p[0] / BK, p[1], p[2] / BK)
        c = shader(q, n)
        return finish(c, ed(q), BLUE_STONE, lines=not name.startswith("face_")) if panel and c is not None else c
    plate(blue, name, wide, sh, out=out, lift=lift)



F = BS - BCH
for ax in range(3):
    for sg in (-1, 1):
        def corner(a, b):
            q = [0.0, 0.0, 0.0]
            q[ax] = sg * BS
            o = [i for i in range(3) if i != ax]
            q[o[0]], q[o[1]] = a * F, b * F
            return (q[0], q[1] + BY, q[2])
        pts = [corner(a, b) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        out = [0.0, 0.0, 0.0]
        out[ax] = sg
        nm = {(0, -1): "west", (0, 1): "east", (1, -1): "down", (1, 1): "up", (2, -1): "north", (2, 1): "south"}[(ax, sg)]
        bplate(f"face_{nm}", pts, blue_face if ax != 1 else blue_stone, out=tuple(out))
for i in range(3):
    j, k2 = [m for m in range(3) if m != i]
    for sj in (-1, 1):
        for sk in (-1, 1):
            def pt(a, bj, bk):
                q = [0.0, 0.0, 0.0]
                q[i] = a * F
                q[j] = bj
                q[k2] = bk
                return (q[0], q[1] + BY, q[2])
            pts = [pt(-1, sj * BS, sk * F), pt(1, sj * BS, sk * F), pt(1, sj * F, sk * BS), pt(-1, sj * F, sk * BS)]
            out = [0.0, 0.0, 0.0]
            out[j], out[k2] = sj, sk
            bplate(f"chamfer_{i}_{sj}_{sk}", pts, blue_stone, out=tuple(out))
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            pts = [(sx * BS, BY + sy * F, sz * F), (sx * F, BY + sy * BS, sz * F), (sx * F, BY + sy * F, sz * BS)]
            bplate(f"corner_{sx}_{sy}_{sz}", pts, blue_stone, out=(sx, sy, sz))

# The light in all four windows, just proud of the stone.
OCT = [(BW * math.cos(math.radians(22.5 + 45 * i)) / math.cos(math.radians(22.5)),
        BW * math.sin(math.radians(22.5 + 45 * i)) / math.cos(math.radians(22.5))) for i in range(8)]
OCT = [(s * 0.995, t * 0.995) for s, t in OCT]
for nm, to3d, out, emblem in (
        ("front", lambda s, t: (s, BY + t, -BS), (0, 0, -1), True),
        ("back", lambda s, t: (s, BY + t, BS), (0, 0, 1), True),
):
    bplate(f"glow_{nm}", [to3d(s, t) for s, t in OCT], hope_light(emblem), out=out, lift=0.03, panel=False)


def bronze(p, n, dark=0.0):
    return mix(shade(lit(n, BRONZE), 1 + 0.06 * mottle(p, 1.0, 5))[:3], BRONZE[0], dark)


def port_shader(p, n):
    if abs(n[0]) > 0.9:
        r = math.hypot(p[1] - BY, p[2])
        if r < 0.82:
            return mix(BRONZE[0], (0, 0, 0), 0.4)
    return bronze(p, n)


# A bronze port in each side window: a low ring set into the orb with a dark hollow, barely proud of
# the stone so it does not stick out past the lantern's outline (it sits inside the glow on the sheet).
LENS = 0.78   # how far the side lenses bulge out of the stone
for nm, sg in (("port_e", 1), ("port_w", -1)):
    lathe(blue, nm, [(-0.15, 1.3), (0.2, 1.3), (0.2, 0.9), (0.02, 0.9)], 16, port_shader,
          base=(sg * (BS * BK + LENS), BY, 0.0), axis=(sg, 0.0, 0.0), caps=(False, True))


def foot_shader(p, n):
    if n[1] < -0.9:
        # The underside: a bronze plate with turned rings and four small emblems, as on the sheet.
        r = math.hypot(p[0], p[2])
        c = mix(BRONZE[1], BRONZE[3], 0.3)
        for ring in (4.0, 3.3, 2.0, 1.2):
            if abs(r - ring) < 0.1:
                c = BRONZE[0]
        for a in range(4):
            ex, ez = 2.65 * math.cos(a * math.pi / 2), 2.65 * math.sin(a * math.pi / 2)
            d = math.hypot(p[0] - ex, p[2] - ez)
            if d < 0.5:
                c = BLUE_STONE[1] if d < 0.32 else BRONZE[0]
        return c
    c = blue_stone(p, n)
    if abs(n[1]) < 0.5 and p[1] < 1.6:
        # Fluting round the lowest step.
        tng = _cross((0.0, 1.0, 0.0), n)
        s = _dot(p, tng)
        if (s + 10) % 0.7 < 0.16 and 0.25 < p[1] < 1.35:
            c = mix(c, BLUE_STONE[0], 0.55)
    return c


OCT_R = 1 / math.cos(math.radians(22.5))
lathe(blue, "foot", [(0.0, 4.1 * OCT_R), (1.6, 4.1 * OCT_R), (1.6, 3.7 * OCT_R), (2.7, 3.7 * OCT_R),
                     (2.7, 3.0 * OCT_R), (BY - BS, 3.0 * OCT_R)], 8, foot_shader, phase=22.5, smooth=False,
      caps=(True, False))


def cap_shader(p, n):
    c = bronze(p, n)
    if n[1] > 0.9:
        r = math.hypot(p[0], p[2])
        if p[1] > 17.0:
            # The top: a turned ring round a recessed disc with the crown mark.
            for ring in (2.55, 1.85):
                if abs(r - ring) < 0.08:
                    return BRONZE[0]
            if r < 1.45:
                c = mix(BLUE_STONE[1], BLUE_STONE[0], 0.3)
                x, z = p[0], p[2]
                crown = (-0.75 < x < 0.75 and -0.55 < z < -0.25) or \
                        (-0.25 < z < 0.6 and any(abs(x - cx) < 0.17 + (0.6 - z) * 0.12 for cx in (-0.62, 0.0, 0.62)))
                if crown:
                    c = BRONZE[2]
                elif r > 1.3:
                    c = BRONZE[0]
    elif abs(n[1]) < 0.6:
        if abs(p[1] - 15.4) < 0.06 or abs(p[1] - 16.55) < 0.06:
            c = mix(c, BRONZE[0], 0.6)
    return c


lathe(blue, "cap", [(BY + BS, 4.25), (14.95, 4.25), (14.95, 3.85), (15.85, 3.85), (15.85, 4.05), (16.15, 4.05),
                    (16.15, 3.35), (16.95, 3.35), (17.15, 3.05)], 24, cap_shader, caps=(False, True))

# The squared stone loop handle with stepped corners: chunky, as on the sheet.
for s_ in (-1, 1):
    for nm, x0, x1, y0, y1 in (("post", 3.375, 4.625, 16.125, 20.25), ("step", 2.5, 3.75, 20.25, 21.5)):
        frm = (min(s_ * x0, s_ * x1), y0, -0.625)
        to = (max(s_ * x0, s_ * x1), y1, 0.625)
        blue.cube(f"handle_{nm}_{s_}", frm, to, bevelled(frm, to, BLUE_STONE, bev=0.35))
blue.cube("handle_top", (-2.875, 21.5, -0.625), (2.875, 22.75, 0.625),
          bevelled((-2.875, 21.5, -0.625), (2.875, 22.75, 0.625), BLUE_STONE, bev=0.35))


# ---- real relief, so the lantern has the sheet's depth instead of painted-on detail ----
def sbar(name, a, b, out, wide=0.45, high=0.4):
    """A raised stone rib from a to b (cube coordinates), standing ``high`` proud along ``out``."""
    e = _norm(_sub(b, a))
    o = _norm(_add(out, e, -_dot(out, e)))
    sd = _cross(e, o)

    def at(p, side, up):
        return _add(_add(p, sd, side * wide / 2), o, up)
    a2, b2 = _add(a, e, -wide * 0.5), _add(b, e, wide * 0.5)
    bplate(f"{name}_top", [at(a2, -1, high), at(b2, -1, high), at(b2, 1, high), at(a2, 1, high)], blue_stone, out=o)
    for k in (-1, 1):
        bplate(f"{name}_side{k}", [at(a2, k, 0.0), at(b2, k, 0.0), at(b2, k, high), at(a2, k, high)],
               lambda p, n: blue_stone(p, n, 0.18), out=tuple(x * k for x in sd))


# A raised octagonal frame round each window, so the glass sits down inside it.
FR = (BW + 0.2) / BW
for nm, to3d, out in (("front", lambda s, t: (s, BY + t, -BS), (0, 0, -1)),
                      ("back", lambda s, t: (s, BY + t, BS), (0, 0, 1)),
                      ("left", lambda s, t: (BS, BY + t, s), (1, 0, 0)),
                      ("right", lambda s, t: (-BS, BY + t, s), (-1, 0, 0))):
    ring = [to3d(s * FR, t * FR) for s, t in OCT]
    for i in range(8):
        sbar(f"frame_{nm}_{i}", ring[i], ring[(i + 1) % 8], out, wide=0.42, high=0.42)

# Raised ribs where each side face meets its chamfers (the sheet's panel lines).
for ax in (0, 2):
    for sg in (-1, 1):
        def cpt(a, b):
            q = [0.0, 0.0, 0.0]
            q[ax] = sg * BS
            q[2 - ax] = a * F
            return (q[0], BY + b * F, q[2])
        out = [0.0, 0.0, 0.0]
        out[ax] = sg
        cs = [cpt(-1, -1), cpt(1, -1), cpt(1, 1), cpt(-1, 1)]
        for i in range(4):
            sbar(f"rib_{ax}_{sg}_{i}", cs[i], cs[(i + 1) % 4], tuple(out), wide=0.36, high=0.22)


# The side windows are domed lenses of light that bulge out of the stone, a bronze port at the crown.
def lens_shader(sg):
    def sh(p, n):
        r = math.hypot(p[1] - BY, p[2])
        c = mix(HOPE_PALE, HOPE, min(1.0, max(0.0, (r - 1.0) / (BW - 0.9))) ** 0.8)
        if r > BW * 0.92:
            c = mix(c, HOPE_INK, 0.5)
        return c
    return sh


VR = BW / math.cos(math.radians(22.5))
for nm, sg in (("glow_lens_e", 1), ("glow_lens_w", -1)):
    lathe(blue, nm, [(0.0, VR), (0.3, VR * 0.9), (0.58, VR * 0.66), (LENS, 1.3)], 8, lens_shader(sg),
          base=(sg * BS * BK, BY, 0.0), axis=(sg, 0.0, 0.0), phase=22.5, caps=(False, False))


# Small square blocks set round the lantern: the notched steps of the foot, bolts round the cap.
def ring_block(name, ang, r0, r1, half, y0, y1, shader=None, lines=False):
    shader = shader or blue_stone
    th = math.radians(ang)
    u, w = (math.sin(th), 0.0, -math.cos(th)), (math.cos(th), 0.0, math.sin(th))

    def P(r, s_, y):
        return (u[0] * r + w[0] * s_, y, u[2] * r + w[2] * s_)
    faces = {"out": [P(r1, -half, y0), P(r1, half, y0), P(r1, half, y1), P(r1, -half, y1)],
             "top": [P(r0, -half, y1), P(r1, -half, y1), P(r1, half, y1), P(r0, half, y1)],
             "l": [P(r0, -half, y0), P(r1, -half, y0), P(r1, -half, y1), P(r0, -half, y1)],
             "r": [P(r0, half, y0), P(r1, half, y0), P(r1, half, y1), P(r0, half, y1)]}
    outs = {"out": u, "top": (0, 1, 0), "l": tuple(-x for x in w), "r": w}
    pal = BRONZE if shader is not blue_stone else BLUE_STONE
    for k, pts in faces.items():
        ed = edge_dist(pts)
        plate(blue, f"{name}_{k}", pts,
              (lambda ed: lambda p, n: finish(shader(p, n), ed(p), pal, lines=lines))(ed), out=outs[k])


for i in range(8):   # two rows of notched blocks round the foot, staggered like the sheet's base
    ring_block(f"foot_block_{i}", 45 * i, 4.0, 4.45, 0.55, 0.0, 1.25)
    ring_block(f"foot_block_hi_{i}", 45 * i + 22.5, 3.6, 3.95, 0.42, 1.6, 2.55)
for i in range(12):  # bolts round the cap's collar
    ring_block(f"cap_bolt_{i}", 30 * i + 15, 4.2, 4.42, 0.17, 14.55, 14.85, bronze)
for i in range(16):  # and a ring of small bolts round its top drum
    ring_block(f"cap_bolt_hi_{i}", 22.5 * i, 3.3, 3.48, 0.13, 16.45, 16.7, bronze)


# A bronze nameplate on the foot's back step, engraved with lines of text, as on the sheet.
def nameplate(p, n):
    c = bronze(p, n)
    if n[2] > 0.6 and any(abs(p[1] - ly) < 0.045 for ly in (1.88, 2.06, 2.24)) and abs(p[0]) < 0.85:
        return BRONZE[0]
    return c


ring_block("nameplate", 180, 3.0 * OCT_R - 0.05, 3.0 * OCT_R + 0.18, 1.05, 1.7, 2.42, nameplate)


# Raised ribs round each corner triangle, so the corners read as fitted stone panels.
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            tri = [(sx * BS, BY + sy * F, sz * F), (sx * F, BY + sy * BS, sz * F), (sx * F, BY + sy * F, sz * BS)]
            c0 = tuple(sum(q[i] for q in tri) / 3 for i in range(3))
            inset = [_add(q, _sub(c0, q), 0.28) for q in tri]
            for i in range(3):
                sbar(f"corner_rib_{sx}_{sy}_{sz}_{i}", inset[i], inset[(i + 1) % 3], _norm((sx, sy, sz)),
                     wide=0.28, high=0.16)
blue.write()


# ---- the Star Sapphire lantern (the violet corps' lantern): from J's sheet, built with the mesh kit ---
# A faceted violet gem, lit from within, caged in riveted bronze: five rings of eight points, each
# ring turned half a step from the next, so every band between them is a row of real triangular
# facets (tall ones round the middle, as on the sheet) with a bronze bar along every edge. The big
# downward panels carry a Star Sapphire star in front and on both sides and runes on the back. It
# stands on a hexagonal bronze foot with ribs, a nameplate behind and a carved disc underneath.
# The crystal is all glow (full-bright, never dimmer than 75%); the cage stands proud of it.
# Front star centre (0, 11.4, -5.0); top y 20. Keep LanternFirstPerson's VIOLET look in step.
LOVE_CRYSTAL = ((88, 26, 150), (162, 84, 236), (250, 228, 255), (196, 140, 252))
LOVE = (172, 84, 252)
LOVE_PALE = (240, 214, 255)
LOVE_INK = (70, 16, 124)
SAPPHIRE_BRONZE = ((70, 38, 16), (168, 102, 52), (252, 206, 158), (206, 140, 82))

violet = Model("violet_lantern", density=MD)
# The gem as J's sheet cuts it: four big kite facets on the diagonals (stars in front, runes and a
# star behind) running from the foot to the shoulder, narrow kites between them, small triangles at
# the waist, a ring of crown facets and a low square pyramid on top. Rings: (height, radius, angles).
GEM_B = (3.0, 3.7, [45 * i for i in range(8)])                          # the foot ring
GEM_W = (8.8, 5.5, sorted(d + o for d in (45, 135, 225, 315) for o in (-30, 30)))  # the waist
GEM_S = (14.2, 4.7, [45 * i for i in range(8)])                         # the shoulder
GEM_T = (17.0, 2.9, [45, 135, 225, 315])                                # the crown
GEM_APEX = (0.0, 18.5, 0.0)
GEM_TOP = 18.5


def ring_pt(ring, ang):
    y, r, _ = ring
    th = math.radians(ang)
    return (r * math.sin(th), y, -r * math.cos(th))

def star_r(a):
    """The Star Sapphire star's outline radius at angle a: eight points, the four upright and
    sideways ones longer, like the star on J's sheet."""
    k = (a % (math.pi / 4)) / (math.pi / 4)          # 0 at a point, 0.5 between, 1 at the next
    long_pt = round(a / (math.pi / 4)) % 2 == 0
    tip = 1.75 if long_pt else 1.35
    return 0.72 + (tip - 0.72) * abs(1 - 2 * k) ** 1.6


def sapphire_star(s, t):
    """The cut star: a thick dark outline of an eight-pointed star with pale light left inside it
    and a dark heart, read as carved into the glass."""
    r = math.hypot(s, t)
    f = star_r(math.atan2(t, s))
    return (0.66 * f < r < f) or r < 0.22


def love_runes(s, t):
    """Rows of carved runes, like the sheet's back panel."""
    if abs(s) > 1.15 or not -2.2 < t < 2.4:
        return False
    row_i, fy = math.floor((t + 2.2) / 0.92), (t + 2.2) % 0.92
    col_i, fx = math.floor((s + 1.15) / 0.77), (s + 1.15) % 0.77
    seed = (row_i * 5 + col_i * 11) % 6
    if not (0.1 < fy < 0.75 and 0.08 < fx < 0.66):
        return False
    return ((seed in (0, 3) and abs(fx - 0.37) < 0.08) or (seed in (1, 4) and abs(fy - 0.42) < 0.08)
            or (seed == 2 and abs(fx - 0.12 - fy * 0.7) < 0.09) or (seed == 5 and abs(fy - 0.2) < 0.08 and fx > 0.25)
            or (seed == 4 and abs(fx - 0.15) < 0.08 and fy > 0.4))


def crystal(pts, mark=None):
    """A facet of the gem, full of violet light: palest at its heart and darker toward its edges,
    with the facet's own sheen so neighbouring facets read apart; ``mark`` cuts the star or runes.
    Finished like cut glass: a deep shadow where it sinks under the cage, a pale bevel line just
    inside that, and faint cut lines running from its heart to each corner."""
    c = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
    R = max(math.dist(c, p) for p in pts)
    ed = edge_dist(pts)
    spokes = [(c, q) for q in pts]

    def shader(p, n):
        ev = _norm(_add((0.0, 1.0, 0.0), n, -n[1]))
        eu = _cross(n, ev)
        d = _sub(p, c)
        s, t = _dot(d, eu), _dot(d, ev)
        if mark == "star":
            if sapphire_star(s / 1.3, (t - 0.6) / 1.3):
                return LOVE_INK
            if sapphire_star(s / 1.3 * 0.86, (t - 0.6) / 1.3 * 0.86):   # a pale halo round the cut star
                return mix(LOVE_PALE, (255, 255, 255), 0.4)
        if mark == "runes" and love_runes(s, t - 0.6):
            return LOVE_INK
        heart = math.hypot(s, t - (0.6 if mark else 0.0)) / R
        col = mix(lit(n, LOVE_CRYSTAL), LOVE, 0.35)
        col = mix(col, LOVE_PALE, max(0.0, 0.62 - heart * 0.75))
        e = ed(p)
        if e < 0.32:
            return mix(col, LOVE_INK, 0.55 * (1 - e / 0.32) + 0.15)
        if e < 0.42:
            return mix(col, (255, 255, 255), 0.35)
        if any(_seg_dist(p, a, b) < 0.05 for a, b in spokes):
            return mix(col, LOVE_PALE, 0.35)
        return col
    return shader


def bar(model, name, a, b, out, shader, wide=0.55, high=0.32):
    """A square bronze bar along a gem edge from a to b, standing ``high`` proud of the surface."""
    e = _norm(_sub(b, a))
    o = _norm(_add(out, e, -_dot(out, e)))
    sd = _cross(e, o)
    def at(p, side, up):
        return _add(_add(p, sd, side * wide / 2), o, up)
    # The top runs on past both ends so the bars meet without gaps; the sides stop at the ends,
    # or they would stick out as fins where the gem bends away.
    a2, b2 = _add(a, e, -wide * 0.45), _add(b, e, wide * 0.45)
    plate(model, f"{name}_top", [at(a2, -1, high), at(b2, -1, high), at(b2, 1, high), at(a2, 1, high)],
          shader, out=o)
    for k in (-1, 1):
        plate(model, f"{name}_side{k}", [at(a, k, 0.0), at(b, k, 0.0), at(b, k, high), at(a, k, high)],
              shader, out=tuple(x * k for x in sd))


def cage(p, n):
    c = shade(lit(n, SAPPHIRE_BRONZE), 1 + 0.06 * mottle(p, 1.0, 7))[:3]
    return c


def riveted(a, b):
    """A cage bar's finish, as on the sheet: a raised lip along both edges with a dark groove inside
    it, and a row of round rivet heads down the middle (lit on top, shadowed below)."""
    e = _norm(_sub(b, a))
    ln = math.dist(a, b)

    def shader(p, n):
        c = cage(p, n)
        along = _dot(_sub(p, a), e)
        foot = _add(a, e, along)
        across = math.dist(p, foot)
        top = _dot(n, _norm(_sub(p, (0, p[1], 0)))) > 0.3 or n[1] > 0.6
        if not top:
            return mix(c, SAPPHIRE_BRONZE[0], 0.35)
        if across > 0.27:
            return mix(c, SAPPHIRE_BRONZE[2], 0.35)
        if across > 0.19:
            return mix(c, SAPPHIRE_BRONZE[0], 0.55)
        k = max(1, round(ln / 0.55))
        step = ln / k
        r = math.hypot((along % step) - step / 2, across)
        if r < 0.1:
            return mix(c, SAPPHIRE_BRONZE[2], 0.6)
        if r < 0.14:
            return mix(c, SAPPHIRE_BRONZE[0], 0.5)
        return c
    return shader


# The crystal and its cage. Facets that make one big kite share a shader (so a mark sits across
# both halves) and the bar between them is left out, so the cage outlines the sheet's big panels.
def _around(angs, a):
    """The angles in ``angs`` just below and just above angle a (wrapping round)."""
    lo = max([x for x in angs if x < a] or [max(angs) - 360])
    hi = min([x for x in angs if x > a] or [min(angs) + 360])
    return lo, hi


KITE_MARKS = {315: "star", 45: "star", 135: "runes", 225: "star"}
facets, skip = [], set()
for k in GEM_B[2]:
    lo, hi = _around(GEM_W[2], k)
    wl, wh = ring_pt(GEM_W, lo), ring_pt(GEM_W, hi)
    b_, s_ = ring_pt(GEM_B, k), ring_pt(GEM_S, k)
    if k in KITE_MARKS:
        # A big panel on each diagonal, as on the sheet: broad at the foot and the shoulder, with
        # the star (or runes) in the middle. It is a kite plus the four waist triangles beside it,
        # all shaded as one piece with no bars across it.
        bl, bh = ring_pt(GEM_B, k - 45), ring_pt(GEM_B, k + 45)
        sl, sh2 = ring_pt(GEM_S, k - 45), ring_pt(GEM_S, k + 45)
        sh = crystal([bl, b_, bh, wh, sh2, s_, sl, wl], KITE_MARKS[k])
        facets += [(f"kite_{k}_lo", [wl, wh, b_], sh), (f"kite_{k}_hi", [wl, wh, s_], sh),
                   (f"side_{k}_bl", [bl, b_, wl], sh), (f"side_{k}_bh", [b_, bh, wh], sh),
                   (f"side_{k}_sl", [sl, s_, wl], sh), (f"side_{k}_sh", [s_, sh2, wh], sh)]
        skip.update(frozenset(e) for e in ((wl, wh), (wl, b_), (wh, b_), (wl, s_), (wh, s_)))
    else:
        # A narrow kite between two big panels, pinched to a point at the foot and the shoulder.
        kite = [b_, wl, s_, wh]
        sh = crystal(kite)
        facets += [(f"kite_{k}_lo", [wl, wh, b_], sh), (f"kite_{k}_hi", [wl, wh, s_], sh)]
        skip.add(frozenset((wl, wh)))
for d in GEM_T[2]:                       # the crown: a four-sided facet on each diagonal...
    t_ = ring_pt(GEM_T, d)
    sl, sm, sh_ = ring_pt(GEM_S, d - 45), ring_pt(GEM_S, d), ring_pt(GEM_S, d + 45)
    quad = [sl, sm, sh_, t_]
    shq = crystal(quad)
    facets += [(f"crown_{d}_a", [sl, sm, t_], shq), (f"crown_{d}_b", [sm, sh_, t_], shq)]
    skip.add(frozenset((sm, t_)))
for c in (0, 90, 180, 270):              # ...a triangle between them on each side...
    facets.append((f"crown_c{c}", [ring_pt(GEM_T, c - 45), ring_pt(GEM_T, c + 45), ring_pt(GEM_S, c)], None))
for d in GEM_T[2]:                       # ...and the low square pyramid on top
    facets.append((f"apex_{d}", [ring_pt(GEM_T, d), ring_pt(GEM_T, d + 90), GEM_APEX], None))
bottom = [ring_pt(GEM_B, k) for k in GEM_B[2]]
facets.append(("bottom", bottom, crystal(bottom)))

edges = {}
for nm, tri, sh in facets:
    c = tuple(sum(p[q] for p in tri) / len(tri) for q in range(3))
    out = (0, -1, 0) if nm == "bottom" else _norm((c[0], c[1] - 9.0, c[2]))
    plate(violet, f"glow_gem_{nm}", tri, sh or crystal(tri), out=out)
    if nm != "bottom":
        for i in range(len(tri)):
            e = frozenset((tri[i], tri[(i + 1) % len(tri)]))
            if e not in skip:
                edges[e] = None
for k, e in enumerate(edges):
    a, b = tuple(e)
    mid = tuple((a[q] + b[q]) / 2 for q in range(3))
    out = _norm((mid[0], (mid[1] - 10.0) * 0.6, mid[2]))
    bar(violet, f"cage_{k}", a, b, out, riveted(a, b), wide=0.7, high=0.36)
lathe(violet, "tip", [(GEM_TOP - 0.15, 0.75), (GEM_TOP + 0.35, 0.75), (GEM_TOP + 0.35, 0.45), (GEM_TOP + 0.7, 0.25)],
      12, cage)


def hex_foot(p, n):
    c = cage(p, n)
    if n[1] < -0.9:
        # Underneath: a carved disc of rings and four marks, like the sheet's bottom view.
        r = math.hypot(p[0], p[2])
        c = mix(SAPPHIRE_BRONZE[1], SAPPHIRE_BRONZE[3], 0.25)
        mark = any(abs(r - q) < 0.1 for q in (4.6, 3.8, 2.3, 1.0)) or (0.5 < r < 0.72)
        for b in range(4):
            lx, lz = 3.05 * math.cos(b * math.pi / 2), 3.05 * math.sin(b * math.pi / 2)
            if math.hypot(p[0] - lx, p[2] - lz) < 0.32:
                mark = True
        return SAPPHIRE_BRONZE[0] if mark else c
    if abs(n[1]) < 0.3 and p[1] < 1.7:
        if n[2] > 0.9 and abs(p[0]) < 1.9 and 0.35 < p[1] < 1.35:
            # The nameplate on the back, with three engraved lines.
            c = mix(SAPPHIRE_BRONZE[3], SAPPHIRE_BRONZE[2], 0.2)
            if any(abs(p[1] - ly) < 0.07 for ly in (0.62, 0.85, 1.08)) and abs(p[0]) < 1.5:
                return SAPPHIRE_BRONZE[0]
            return c
        tng = _cross((0.0, 1.0, 0.0), n)
        if (_dot(p, tng) + 10) % 0.6 < 0.16 and 0.2 < p[1] < 1.5:
            c = mix(c, SAPPHIRE_BRONZE[0], 0.6)
    return c


H6 = 1 / math.cos(math.radians(30))
lathe(violet, "foot", [(0.0, 6.0 * H6), (1.7, 6.0 * H6), (1.7, 5.5 * H6), (3.0, 3.4 * H6)], 6, hex_foot,
      phase=30, smooth=False)
violet.write()


# ---- the Orange Lantern (Larfleeze's, the orange corps' lantern): from J's sheet, with the mesh kit --
# A round column of orange light wrapped by two twisted copper bands (a double helix, one and a quarter
# turns), between a stepped round plinth and a stepped capital that holds a pool of light on top. A
# copper medallion with the Orange Lantern emblem sits on the front of the light, where the ring docks.
# When the lantern is charged a flame burns over the pool: crossed flame plates named "core..." that
# LanternFirstPerson swells from nothing as the charge builds (the placed block shows it lit).
# Underneath is a socket. Emblem centre (0, 8.5, -5.3); capital top y 16.2.
COPPER = ((98, 44, 24), (198, 110, 66), (255, 214, 176), (226, 146, 100))
AVARICE = (255, 140, 20)
AVARICE_PALE = (255, 236, 150)
AVARICE_DEEP = (214, 70, 10)

orange = Model("orange_lantern", density=MD)
O_CORE, O_Y0, O_Y1 = 3.3, 2.0, 14.0


def copper(p, n, dark=0.0):
    # Lit like the Classic, but with more fill: the sheet's copper stays warm all the way round.
    c = mix(lit(n, COPPER), COPPER[1], 0.35)
    return mix(shade(c, 1 + 0.07 * mottle(p, 1.0, 11))[:3], COPPER[0], dark)


def avarice_swirl(p, n):
    """The column's light: bright streaks that wind up it against the bands."""
    th = math.atan2(p[0], -p[2])
    k = 0.5 + 0.5 * math.sin(th * 3 - p[1] * 0.95 + 0.6 * math.sin(p[1] * 0.4 + th))
    c = mix(AVARICE, AVARICE_PALE, k ** 2 * 0.85)
    return mix(c, AVARICE_DEEP, 0.25 * (1 - k) ** 2)


lathe(orange, "glow_core", [(O_Y0, O_CORE), (O_Y1, O_CORE)], 24, avarice_swirl, caps=(False, False))

# Two copper bands winding round the light, rounded like twisted rope, with gaps of light between.
TURNS, BAND_H, R_IN, R_OUT = 0.8, 5.0, O_CORE - 0.2, O_CORE + 1.25
STEPS = 40


def band_y(a, ph):
    """The height of a band's middle at angle a along it (a runs from ph)."""
    lo, hi = O_Y0 + 0.4, O_Y1 - 0.4  # the ends tuck under the plinth and capital
    return lo + (hi - lo) * ((a - ph) / (2 * math.pi * TURNS))


def band_shader(ph):
    def shader(p, n):
        th = math.atan2(p[0], -p[2])
        ys = [band_y(th + 2 * math.pi * k, ph) for k in range(-1, 3)
              if ph - 0.2 <= th + 2 * math.pi * k <= ph + 2 * math.pi * TURNS + 0.2]
        d = min((p[1] - y for y in ys), key=abs) if ys else 0.0
        if abs(n[1]) < 0.6:
            # Round the band over from top to bottom, so it reads as a twisted rope of copper.
            q = max(-1.0, min(1.0, d / (BAND_H / 2)))
            rad = _norm((p[0], 0.0, p[2]))
            n = _norm(_add(tuple(x * math.sqrt(max(0.0, 1 - q * q * 0.8)) for x in rad), (0.0, 1.0, 0.0), q * 0.9))
        c = copper(p, n)
        if abs(n[1]) < 0.95 and any(abs(d - g) < 0.12 for g in (-1.25, 0.0, 1.25)):
            c = mix(c, COPPER[0], 0.65)
        return c
    return shader


def at_r(r, a, y):
    y = max(O_Y0, min(O_Y1, y))  # hidden inside the plinth or capital beyond these
    return (r * math.sin(a), y, -r * math.cos(a))


for b in range(2):
    ph = math.pi * b
    sh = band_shader(ph)
    for s in range(int(STEPS * TURNS)):
        a0 = ph + 2 * math.pi * s / STEPS
        a1 = ph + 2 * math.pi * (s + 1) / STEPS
        y0, y1 = band_y(a0, ph), band_y(a1, ph)
        h = BAND_H / 2
        mid = (a0 + a1) / 2
        out = (math.sin(mid), 0.0, -math.cos(mid))
        plate(orange, f"band_{b}_{s}_out", [at_r(R_OUT, a0, y0 - h), at_r(R_OUT, a1, y1 - h), at_r(R_OUT, a1, y1 + h),
                                             at_r(R_OUT, a0, y0 + h)], sh, out=out)
        for nm, dy, up in (("top", h, 1.0), ("bot", -h, -1.0)):
            if not O_Y0 < y0 + dy < O_Y1 or not O_Y0 < y1 + dy < O_Y1:
                continue
            plate(orange, f"band_{b}_{s}_{nm}", [at_r(R_IN, a0, y0 + dy), at_r(R_OUT, a0, y0 + dy),
                                                 at_r(R_OUT, a1, y1 + dy), at_r(R_IN, a1, y1 + dy)], sh, out=(0.0, up, 0.0))


def plinth(p, n):
    c = copper(p, n)
    if n[1] < -0.9:
        # Underneath: rings round a dark square socket.
        r = math.hypot(p[0], p[2])
        c = mix(COPPER[1], COPPER[3], 0.2)
        if any(abs(r - q) < 0.1 for q in (4.6, 3.6, 2.2)):
            return COPPER[0]
        if max(abs(p[0]), abs(p[2])) < 1.2:
            return (36, 18, 10) if max(abs(p[0]), abs(p[2])) < 0.95 else COPPER[0]
        return c
    if abs(n[1]) < 0.6 and any(abs(p[1] - g) < 0.07 for g in (0.45, 14.55, 15.75)):
        c = mix(c, COPPER[0], 0.55)
    return c


lathe(orange, "plinth", [(0.0, 5.8), (0.9, 5.8), (0.9, 5.4), (1.5, 5.4), (1.5, 5.0), (2.0, 5.0),
                         (2.0, R_OUT + 0.15)], 24, plinth, caps=(True, True))
lathe(orange, "capital", [(O_Y1, R_OUT + 0.15), (O_Y1, 5.0), (14.6, 5.0), (14.6, 5.5), (15.3, 5.5), (15.3, 5.9),
                          (16.2, 5.9), (16.2, 3.4), (15.8, 3.4)], 24, plinth, caps=(True, False))


def pool(p, n):
    r = math.hypot(p[0], p[2])
    th = math.atan2(p[0], p[2])
    k = 0.5 + 0.5 * math.sin(th * 2 + r * 2.2)
    return mix(mix(AVARICE_PALE, AVARICE, min(1.0, r / 3.0)), AVARICE_DEEP, 0.2 * k * r / 3)


lathe(orange, "glow_pool", [(15.82, 3.4), (15.82, 0.0)], 24, pool, caps=(False, False))


def orange_emblem(s, t):
    """The Orange Lantern emblem in raised copper: a ring, a small ring at the top of a cup, and the
    lantern's foot bar."""
    r = math.hypot(s, t)
    return (1.45 < r < 1.75 or abs(math.hypot(s, t - 0.45) - 0.42) < 0.13
            or (abs(r - 0.95) < 0.13 and t < 0.1) or (abs(t + 1.15) < 0.12 and abs(s) < 0.75))


def medallion(p, n):
    if n[2] < -0.9:
        s, t = -p[0], p[1] - 8.5
        if orange_emblem(s, t):
            return lit(_norm((0.0, 0.35, -1.0)), COPPER)
        if math.hypot(s, t) < 1.45:
            return mix(COPPER[1], COPPER[0], 0.45)
    return copper(p, n)


lathe(orange, "medallion", [(0.0, 2.05), (1.05, 2.05), (1.05, 1.85)], 20, medallion,
      base=(0.0, 8.5, -R_OUT + 0.3), axis=(0.0, 0.0, -1.0), caps=(False, True))


TONGUES = ((-1.9, 0.5, 0.75), (-0.85, 0.82, 0.9), (0.15, 1.0, 1.0), (1.15, 0.72, 0.9), (2.0, 0.48, 0.7))


def flame_heat(s, t, H, seed):
    """How hot a point of the flame is (0 at the heart, above 1 at its edge), or None outside it.
    The flame is a row of tongues (centre, height, width), each a teardrop that leans and sways."""
    if t < 0:
        return None
    best = None
    for k, (cx, ht, wd) in enumerate(TONGUES):
        u = t / (H * ht)
        if u >= 1:
            continue
        sway = 0.25 * math.sin(u * 4.5 + seed + k * 1.3) * u
        w = wd * (1 - u) ** 0.8 * (0.75 + 1.2 * u * (1 - u))
        d = abs(s - cx - sway) / max(w, 1e-6)
        if d < 1:
            heat = d * 0.6 + u * 0.75
            best = heat if best is None else min(best, heat)
    if t < 1.1 and abs(s) < 2.5 - t * 0.3:
        best = min(best if best is not None else 9, abs(s) / 2.5 * 0.7 + 0.15)
    return best


def flame_paint(H, seed):
    def shader(p, n):
        eu = _cross(n, (0.0, 1.0, 0.0))
        heat = flame_heat(_dot(p, eu), p[1] - 16.2, H, seed)
        if heat is None:
            return None
        if heat < 0.45:
            return mix((255, 252, 222), AVARICE_PALE, heat / 0.45)
        if heat < 0.9:
            return mix(AVARICE_PALE, AVARICE, (heat - 0.45) / 0.45)
        return mix(AVARICE, AVARICE_DEEP, min(1.0, (heat - 0.9) / 0.5))
    return shader


FH, FW = 6.5, 3.0
for i, ang in enumerate((0, 60, 120)):
    a = math.radians(ang)
    d = (math.cos(a), 0.0, math.sin(a))
    nrm = (-math.sin(a), 0.0, math.cos(a))
    pts = [(-FW * d[0], 16.2, -FW * d[2]), (FW * d[0], 16.2, FW * d[2]),
           (FW * d[0], 16.2 + FH, FW * d[2]), (-FW * d[0], 16.2 + FH, -FW * d[2])]
    for side in (1, -1):
        out = tuple(x * side for x in nrm)
        plate(orange, f"core_flame_{i}_{side}", pts, flame_paint(FH, i * 1.7), out=out, lift=0.02 * side)
orange.write()
