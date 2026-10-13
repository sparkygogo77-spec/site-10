"""Model fixes for two corps lanterns (J, 2026-10-13):

- Red Lantern: "geometry bleeds and flashes through a lot". Every glass cube has a glow twin in exactly the
  same place (body_N_i / glow_body_N_i), so the two fight for the same pixels and flicker; the rods and the
  emblem housing also sit flush on the glass and the lens on the glow. And some glass texels are
  part-transparent, so the cube faces inside the barrel show through.
  Fix: the glow twins float 0.02 px outside their body cube (the light sits on top, no fight), the rods,
  housing, lens and frame rods float 0.01 px, and the glass texels are either solid or empty.
- Blue Lantern: "should be lit on both sides the same way as this one is". The lit emblem window is only on
  the front; the back is a dark plate. Fix: the emblem's glow cubes turned 180 degrees round the lantern's
  axis, so the back gets the same lit emblem.

    python tools/fix_lantern_models.py OUTDIR
writes OUTDIR/bbmodel/<name>.bbmodel and OUTDIR/textures/entity/bb/<name>.png, laid out like the jar.
"""
import copy, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "src", "main", "resources", "assets", "lanternring")
OUT = sys.argv[1]
os.makedirs(os.path.join(OUT, "bbmodel"), exist_ok=True)
os.makedirs(os.path.join(OUT, "textures", "entity", "bb"), exist_ok=True)


def load(name):
    return json.load(open(os.path.join(ASSETS, "bbmodel", name + ".bbmodel")))


def save(name, d, tex):
    import base64, io
    buf = io.BytesIO(); tex.save(buf, "PNG", optimize=True)
    for t in d.get("textures", []):                     # Blockbench keeps a copy of the texture inside the model
        if t.get("source", "").startswith("data:image/png"):
            t["source"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    json.dump(d, open(os.path.join(OUT, "bbmodel", name + ".bbmodel"), "w"))
    tex.save(os.path.join(OUT, "textures", "entity", "bb", name + ".png"), optimize=True)


def texture(name):
    return Image.open(os.path.join(ASSETS, "textures", "entity", "bb", name + ".png")).convert("RGBA")


# ---- red -------------------------------------------------------------------------------------------------
d = load("red_lantern")
n_glow = n_float = 0
for e in d["elements"]:
    nm = e["name"]
    if nm.startswith("glow"):
        e["inflate"] = round(e.get("inflate", 0) + 0.02, 3); n_glow += 1
    elif nm.startswith(("rod_", "housing", "lens", "frame_rod")):
        e["inflate"] = round(e.get("inflate", 0) + 0.01, 3); n_float += 1
tex = texture("red_lantern")
a = np.array(tex)
# glass texels: solid or empty (no half-see-through faces inside the barrel)
part = (a[..., 3] > 0) & (a[..., 3] < 255)
a[..., 3] = np.where(part, np.where(a[..., 3] >= 40, 255, 0), a[..., 3]).astype(np.uint8)
# J: "this one should be gold" - the copper frame, bands and handle become gold (hue 42, a touch less saturated),
# the red glass is left alone (it sits at hue 350-5, the copper at 8-40)
rgb = a[..., :3].astype(float) / 255
mx, mn = rgb.max(-1), rgb.min(-1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r_, g_, b_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g_ - b_), 2 * r_ - g_ - b_)) % 360
copper = (a[..., 3] > 0) & (hue > 8) & (hue < 40) & (sat > 0.15)
H = np.radians(42.0); S2 = sat * 0.78; V = mx
c = V * S2
hp = 42.0 / 60.0
x = c * (1 - abs(hp % 2 - 1))
gold = np.stack([V, V - c + x, V - c], -1)              # hue 42 is in the red->yellow sextant: (C, X, 0) + m
gold = np.stack([V, (V - c) + x, V - c], -1)
a[..., :3] = np.where(copper[..., None], np.clip(gold * 255 * 1.35 * np.array([1.0, 0.95, 0.8]), 0, 255), a[..., :3]).astype(np.uint8)
print(f"red: {int(copper.sum())} copper texels turned gold")
# the emblem housing's face (the lens, 4x4 px) gets the Red corps mark used on the battery: three claw slashes
# in a ring, glowing red on dark iron. (An original mark - not a copy of any existing logo.)
E = {e["name"]: e for e in d["elements"]}
u0, v0, u1, v1 = E["lens"]["faces"]["north"]["uv"]
sc = a.shape[0] / 256
x0, y0, x1, y1 = int(u0 * sc), int(v0 * sc), int(u1 * sc), int(v1 * sc)
n = x1 - x0
yy_, xx_ = np.mgrid[0:n, 0:n] + 0.5
cx = cy = n / 2
rr = np.hypot(xx_ - cx, yy_ - cy)
face = np.zeros((n, n, 4)); face[..., :3] = (34, 10, 10); face[..., 3] = 255
ringm = np.abs(rr - n * 0.43) < n * 0.05
slash = np.zeros((n, n), bool)
for off in (-0.26, 0.0, 0.26):
    dd = np.abs((xx_ - cx - off * n) * 0.94 + (yy_ - cy) * 0.34)
    slash |= (dd < n * 0.055) & (np.abs(yy_ - cy) < n * (0.33 - 0.5 * abs(off)))
face[ringm, :3] = (200, 150, 70)                        # a gold rim
face[slash, :3] = (255, 40, 30)
a[y0:y1, x0:x1] = face.astype(np.uint8)
# the same mark on the glow layer (black glows nothing, so only the slashes and rim light up)
u0, v0, u1, v1 = E["glow_lens"]["faces"]["north"]["uv"]
gx0, gy0 = int(u0 * sc), int(v0 * sc)
gface = np.zeros((n, n, 4)); gface[..., 3] = 255
gface[ringm, :3] = (120, 60, 20)
gface[slash, :3] = (255, 40, 30)
a[gy0:gy0 + n, gx0:gx0 + n] = gface.astype(np.uint8)
# the lens sat inside the housing (hidden): bring it and its glow 0.3 px proud of the housing front,
# keeping its 1 px depth so the jar's box UVs still line up
for nm in ("lens", "glow_lens"):
    e = E[nm]
    e["from"][2], e["to"][2] = -7.3, -6.3
save("red_lantern", d, Image.fromarray(a, "RGBA"))
print(f"red: {n_glow} glow cubes floated 0.02, {n_float} rods/housing/lens floated 0.01, {int(part.sum())} part-clear texels made solid/clear")

# ---- blue ------------------------------------------------------------------------------------------------
d = load("blue_lantern")
emblem = [e for e in d["elements"] if e["name"].startswith("glow_emblem")]
back = []
for e in emblem:
    b = copy.deepcopy(e)
    b["name"] = e["name"].replace("glow_emblem", "glow_emblem_back")
    b["origin"] = [0, 0, 0]
    b["rotation"] = [0, 180, 0]
    b.pop("uuid", None)
    back.append(b)
d["elements"].extend(back)
# put them in the outliner next to the front emblem so Blockbench shows them
try:
    import uuid
    for b in back:
        b["uuid"] = str(uuid.uuid4())
    d["outliner"].extend(b["uuid"] for b in back)
except Exception as ex:
    print("outliner:", ex)
save("blue_lantern", d, texture("blue_lantern"))
print(f"blue: {len(back)} emblem glow cubes mirrored to the back")
