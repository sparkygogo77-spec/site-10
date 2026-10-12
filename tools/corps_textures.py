"""Recolours the green ring's textures for another Lantern Corps: python tools/corps_textures.py <assets_dir> <corps>

Only the green and jade pixels change hue (to the corps' colour); gold, black and grey parts stay as
they are, so a red ring keeps its gold band and only its gem and glow turn red. Each texture is
written beside the green one with a _<corps> suffix (and its .png.mcmeta copied), and the models that
use them get a _<corps> copy pointing at the new textures.
"""
import colorsys, json, os, shutil, sys
from PIL import Image

ASSETS = sys.argv[1]
CORPS = sys.argv[2]
# Target hue (degrees), saturation boost and brightness scale per corps.
STYLE = {
    "red": (358, 1.15, 0.95),
    "yellow": (50, 1.1, 1.05),
    "violet": (300, 1.0, 1.0),
    "blue": (205, 1.0, 1.0),
    "orange": (25, 1.15, 1.0),
    "indigo": (255, 1.0, 0.85),
}
HUE, SAT, VAL = STYLE[CORPS]

TEXTURES = [
    "block/construct_brick", "block/construct_inner", "block/construct_rim",
    "block/power_battery_core", "block/power_battery_frame", "block/power_lantern", "block/dark_lantern",
    "item/power_ring", "item/ring_beacon", "item/ring_crest", "item/ring_crest_gold", "item/ring_emblem", "item/ring_forged",
    "entity/ring/band", "entity/ring/dark", "entity/ring/gem", "entity/ring/gem_glow", "entity/ring/gold", "entity/ring/halo",
    "entity/bb/power_ring", "entity/bb/ring_beacon", "entity/bb/ring_crest", "entity/bb/ring_crest_gold", "entity/bb/ring_forged",
    "entity/bb/dark_lantern", "entity/bb/power_lantern", "entity/shockwave_glass",
]
MODELS = [
    "block/construct_brick", "block/construct_inner", "block/construct_rim", "block/power_battery", "block/dark_lantern",
    "item/power_ring", "item/ring_beacon", "item/ring_crest", "item/ring_crest_gold", "item/ring_emblem", "item/ring_forged",
]


def recolour(path_in, path_out):
    im = Image.open(path_in).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            deg = h * 360
            if s < 0.18 or not (70 <= deg <= 190):
                continue
            # Keep a little of the original's spread of hues so the shading still reads.
            nh = ((HUE + (deg - 140) * 0.25) % 360) / 360
            nr, ng, nb = colorsys.hsv_to_rgb(nh, min(1, s * SAT), min(1, v * VAL))
            px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
    im.save(path_out)


for t in TEXTURES:
    src = os.path.join(ASSETS, "textures", t + ".png")
    out = os.path.join(ASSETS, "textures", t + "_" + CORPS + ".png")
    recolour(src, out)
    if os.path.exists(src + ".mcmeta"):
        shutil.copy(src + ".mcmeta", out + ".mcmeta")

renamed = {"lanternring:" + t: "lanternring:" + t + "_" + CORPS for t in TEXTURES}
for m in MODELS:
    src = os.path.join(ASSETS, "models", m + ".json")
    with open(src) as f:
        model = json.load(f)

    def fix(node):
        if isinstance(node, dict):
            return {k: fix(v) for k, v in node.items()}
        if isinstance(node, list):
            return [fix(v) for v in node]
        if isinstance(node, str):
            return renamed.get(node, node)
        return node

    with open(os.path.join(ASSETS, "models", m + "_" + CORPS + ".json"), "w") as f:
        json.dump(fix(model), f, indent="\t")
