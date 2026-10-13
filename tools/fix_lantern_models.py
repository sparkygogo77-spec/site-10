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
