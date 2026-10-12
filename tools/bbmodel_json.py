"""Turns the Blockbench models in assets/lanternring/bbmodel/ into plain Minecraft JSON models, so
inventory icons, dropped items, item frames, third person and the placed lantern show the same
model as the custom first-person and on-hand renderers.

    python tools/bbmodel_json.py src/main/resources/assets/lanternring

Run it again after editing a .bbmodel in Blockbench. It writes:

- models/block/power_battery.json  the lantern, shrunk to fit one block (placed block + item)
- models/block/dark_lantern.json    the Dark Lantern, the same way (the item when it is picked)
- models/item/ring_<name>.json      each Blockbench ring, sized to fill an item slot
- textures/block/power_lantern.png and textures/item/ring_<name>.png, copies of the entity
  textures (JSON models can only use textures from the block and item atlases)

Cubes named "glow..." become full-bright (light_emission 15, unshaded). A solid cube with the
exact box of a glow cube is left out: the glow cube covers it anyway and the two would flicker.
"""
import json, os, shutil, sys

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
FACES = ("north", "east", "south", "west", "up", "down")


def load(name):
    with open(f"{A}/bbmodel/{name}.bbmodel") as f:
        return json.load(f)


def cubes(bb):
    out = []
    for el in bb["elements"]:
        if el.get("type", "cube") != "cube" or el.get("visibility") is False:
            continue
        rot = el.get("rotation") or [0, 0, 0]
        d = el.get("inflate", 0) or 0
        frm = [v - d for v in el["from"]]
        to = [v + d for v in el["to"]]
        out.append(dict(name=el["name"], frm=frm, to=to, faces=el["faces"], glow=el["name"].startswith(("glow", "core")),
                        rot=rot if any(rot) else None, origin=el.get("origin")))
    glow_boxes = {(tuple(c["frm"]), tuple(c["to"])) for c in out if c["glow"]}
    glow_boxes |= {(tuple(v + 0.05 for v in c["frm"]), tuple(v - 0.05 for v in c["to"])) for c in out if c["glow"]}
    return [c for c in out if c["glow"] or (tuple(c["frm"]), tuple(c["to"])) not in glow_boxes]


def face_area(face, size):
    w, h, d = size
    return {"north": w * h, "south": w * h, "east": d * h, "west": d * h, "up": w * d, "down": w * d}[face]


def r(v):
    return round(v, 4)


def json_model(bb, texture, scale, offset, parent=None, display=None):
    tw, th = bb["resolution"]["width"], bb["resolution"]["height"]
    elements = []
    for c in cubes(bb):
        frm = [r(offset[i] + c["frm"][i] * scale) for i in range(3)]
        to = [r(offset[i] + c["to"][i] * scale) for i in range(3)]
        size = [c["to"][i] - c["frm"][i] for i in range(3)]
        faces = {}
        for f in FACES:
            if face_area(f, size) <= 0 or f not in c["faces"]:
                continue
            u0, v0, u1, v1 = c["faces"][f]["uv"]
            faces[f] = {"uv": [r(u0 * 16 / tw), r(v0 * 16 / th), r(u1 * 16 / tw), r(v1 * 16 / th)], "texture": "#t"}
        el = {"name": c["name"], "from": frm, "to": to, "faces": faces}
        if c["rot"]:
            # Free Euler angles (26.x element rotation), about the cube's Blockbench origin.
            el["rotation"] = {"origin": [r(offset[i] + c["origin"][i] * scale) for i in range(3)],
                              "x": c["rot"][0], "y": c["rot"][1], "z": c["rot"][2]}
        if c["glow"]:
            el["shade"] = False
            el["light_emission"] = 15
        elements.append(el)
    model = {}
    if parent:
        model["parent"] = parent
    model["ambientocclusion"] = False
    model["textures"] = {"t": texture, "particle": texture}
    model["elements"] = elements
    if display:
        model["display"] = display
    return model


def bounds(bb):
    cs = cubes(bb)
    lo = [min(c["frm"][i] for c in cs) for i in range(3)]
    hi = [max(c["to"][i] for c in cs) for i in range(3)]
    return lo, hi


def write(path, model):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(model, f, indent="\t")
        f.write("\n")
    print("wrote", path, len(model["elements"]), "elements")


def copy_texture(name, folder, as_name):
    os.makedirs(f"{A}/textures/{folder}", exist_ok=True)
    shutil.copyfile(f"{A}/textures/entity/bb/{name}.png", f"{A}/textures/{folder}/{as_name}.png")


# ---- the lanterns: placed block and the item everywhere but the first-person off hand -----
LANTERN_DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, -0.5, 0], "scale": [0.8, 0.8, 0.8]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.4, 0.4, 0.4]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, -0.5, 0], "scale": [0.75, 0.75, 0.75]},
    "thirdperson_righthand": {"rotation": [75, 0, 0], "translation": [0, 2.5, 0], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_lefthand": {"rotation": [75, 0, 0], "translation": [0, 2.5, 0], "scale": [0.5, 0.5, 0.5]},
    "firstperson_righthand": {"rotation": [0, 135, 0], "translation": [0, 1, 0], "scale": [0.4, 0.4, 0.4]},
    "firstperson_lefthand": {"rotation": [0, 135, 0], "translation": [0, 1, 0], "scale": [0.4, 0.4, 0.4]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 0], "scale": [0.8, 0.8, 0.8]},
}
# Each lantern is shrunk so its full height fits one block (16 px).
for name, model in (("power_lantern", "power_battery"), ("dark_lantern", "dark_lantern"),
                    ("torus_lantern", "torus_lantern"), ("compact_lantern", "compact_lantern"),
                    ("stone_lantern", "stone_lantern"), ("classic_lantern", "classic_lantern"),
                    ("red_lantern", "red_lantern"), ("blue_lantern", "blue_lantern"),
                    ("yellow_lantern", "yellow_lantern")):
    bb = load(name)
    lo, hi = bounds(bb)
    copy_texture(name, "block", name)
    write(f"{A}/models/block/{model}.json", json_model(
        bb, f"lanternring:block/{name}", 16 / (hi[1] - lo[1]), [8, 0, 8], parent="minecraft:block/block",
        display=LANTERN_DISPLAY))

# The Nebula battery: its body plus the dark glass (a second texture, the animated strip
# textures/block/nebula_glass.png written by blockbench_models.py).
bb = load("nebula_lantern")
lo, hi = bounds(bb)
copy_texture("nebula_lantern", "block", "nebula_lantern")
scale = 16 / (hi[1] - lo[1])
body = json_model(bb, "lanternring:block/nebula_lantern", scale, [8, 0, 8], parent="minecraft:block/block", display=LANTERN_DISPLAY)
glass = json_model(load("nebula_glass"), "lanternring:block/nebula_glass", scale, [8, 0, 8])
for el in glass["elements"]:
    for f in el["faces"].values():
        f["texture"] = "#g"
body["textures"]["g"] = "lanternring:block/nebula_glass"
body["elements"] += glass["elements"]
write(f"{A}/models/block/nebula_lantern.json", body)

# The Ring Forge: the base as the placed block (its floating parts are drawn by RingForgeRenderer),
# and everything in one piece, shrunk to fit, for the item, with the endless light in the emblem
# (the animated strip textures/block/ring_forge_light.png).
FORGE_DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.625, 0.625, 0.625]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.25, 0.25, 0.25]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.375, 0.375, 0.375]},
    "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.375, 0.375, 0.375]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 2, 0], "scale": [0.7, 0.7, 0.7]},
    "firstperson_lefthand": {"rotation": [0, 45, 0], "translation": [0, 2, 0], "scale": [0.7, 0.7, 0.7]},
}
copy_texture("ring_forge", "block", "ring_forge")
write(f"{A}/models/block/ring_forge.json", json_model(load("ring_forge"), "lanternring:block/ring_forge", 1, [8, 0, 8],
                                                     parent="minecraft:block/block"))
bb = load("ring_forge_display")
lo, hi = bounds(bb)
copy_texture("ring_forge_display", "block", "ring_forge_display")
scale = 16 / max(hi[1] - lo[1], hi[0] - lo[0], hi[2] - lo[2])
item = json_model(bb, "lanternring:block/ring_forge_display", scale, [8, 0, 8], display=FORGE_DISPLAY)
light = load("ring_forge_light")
for el in light["elements"]:
    el["from"][1] += 23
    el["to"][1] += 23
light_json = json_model(light, "lanternring:block/ring_forge_light", scale, [8, 0, 8])
for el in light_json["elements"]:
    for f in el["faces"].values():
        f["texture"] = "#l"
item["textures"]["l"] = "lanternring:block/ring_forge_light"
item["elements"] += light_json["elements"]
write(f"{A}/models/item/ring_forge.json", item)

# The big batteries: tables with a pool of animated liquid in the basin (tools/font_liquid_textures.py).
def pool(y, texture):
    return {"name": "liquid", "from": [2, y, 2], "to": [14, y, 14], "shade": False, "light_emission": 15,
            "faces": {"up": {"uv": [2, 2, 14, 14], "texture": "#l"}, "down": {"uv": [2, 2, 14, 14], "texture": "#l"}}}


for name, y, liquid in (("great_battery", 13.5, "willpower_still"), ("lava_font", 14, "blood_lava_still")):
    copy_texture(name, "block", name)
    m = json_model(load(name), f"lanternring:block/{name}", 1, [8, 0, 8], parent="minecraft:block/block")
    if name == "lava_font":
        write(f"{A}/models/block/lava_font_empty.json", json.loads(json.dumps(m)))
    m["textures"]["l"] = f"lanternring:block/{liquid}"
    m["elements"].append(pool(y, liquid))
    write(f"{A}/models/block/{name}.json", m)

# ---- the rings: face up (+Y), centred in the 16^3 item box and filling 14 px of it --------
RING_DISPLAY = {
    # Tipped toward the viewer so the inventory icon shows the face and a little of the band.
    "gui": {"rotation": [50, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [-90, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 13, 0], "scale": [0.8, 0.8, 0.8]},
}
for name in ("ring_forged", "ring_crest", "ring_crest_gold", "ring_beacon", "power_ring"):
    bb = load(name)
    lo, hi = bounds(bb)
    scale = 14 / max(hi[i] - lo[i] for i in range(3))
    offset = [8 - (lo[i] + hi[i]) / 2 * scale for i in range(3)]
    tex = name if name.startswith("ring_") else "ring_emblem"
    copy_texture(name, "item", tex)
    write(f"{A}/models/item/{tex}.json", json_model(bb, f"lanternring:item/{tex}", scale, offset, display=RING_DISPLAY))

# ---- the Infinity Stones and the Infinity Gauntlet -------------------------------------------
STONE_DISPLAY = {
    "gui": {"rotation": [15, 30, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.35, 0.35, 0.35]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [0.8, 0.8, 0.8]},
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 2, 1], "scale": [0.35, 0.35, 0.35]},
    "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 2, 1], "scale": [0.35, 0.35, 0.35]},
    "firstperson_righthand": {"rotation": [0, -25, 0], "translation": [1, 3, 0], "scale": [0.4, 0.4, 0.4]},
    "firstperson_lefthand": {"rotation": [0, -25, 0], "translation": [1, 3, 0], "scale": [0.4, 0.4, 0.4]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 0], "scale": [0.6, 0.6, 0.6]},
}
# The back of the hand (north) faces the viewer in the inventory and item frames.
GAUNTLET_DISPLAY = {
    "gui": {"rotation": [10, 160, 0], "translation": [0, 0, 0], "scale": [0.95, 0.95, 0.95]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]},
    "thirdperson_righthand": {"rotation": [-80, 0, 0], "translation": [0, 1, 3], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_lefthand": {"rotation": [-80, 0, 0], "translation": [0, 1, 3], "scale": [0.5, 0.5, 0.5]},
    "firstperson_righthand": {"rotation": [-10, 200, 0], "translation": [0, 1, -1], "scale": [0.55, 0.55, 0.55]},
    "firstperson_lefthand": {"rotation": [-10, 160, 0], "translation": [0, 1, -1], "scale": [0.55, 0.55, 0.55]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 13, 0], "scale": [0.6, 0.6, 0.6]},
}


def fitted(name, display):
    """The model scaled so its biggest side fills 15 px, centred in the item box."""
    bb = load(name)
    lo, hi = bounds(bb)
    scale = 15 / max(hi[i] - lo[i] for i in range(3))
    offset = [8 - (lo[i] + hi[i]) / 2 * scale for i in range(3)]
    copy_texture(name, "item", name)
    return json_model(bb, f"lanternring:item/{name}", scale, offset, display=display)


for name in ("soul_stone", "time_stone"):
    write(f"{A}/models/item/{name}.json", fitted(name, STONE_DISPLAY))

# The gauntlet without its stones, plus one model per socketed stone (items/infinity_gauntlet.json
# adds each one when the lanternring:has_stone property says that stone is in).
whole = fitted("infinity_gauntlet", GAUNTLET_DISPLAY)
stones = {"soul": "glow_soul", "time": "glow_time"}
base = dict(whole, elements=[e for e in whole["elements"] if e["name"] not in stones.values()])
write(f"{A}/models/item/infinity_gauntlet.json", base)
for stone, cube in stones.items():
    write(f"{A}/models/item/infinity_gauntlet_{stone}.json",
          dict(whole, elements=[e for e in whole["elements"] if e["name"] == cube]))
