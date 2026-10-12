"""The socket on every lantern that the ring docks into while charging:
python tools/lantern_port_assets.py src/main/resources/assets/lanternring

  bbmodel/lantern_port.bbmodel                A gold collar with a glowing plate sunk in its middle and
                                              four corner prongs, its back at z = 0, facing -z.
  textures/entity/bb/lantern_port[_<corps>].png  Gold, with the plate in each corps' colour.
"""
import json, os, random, sys, uuid
from PIL import Image

ASSETS = sys.argv[1]
CORPS = {"": 0x3CFF5A, "_red": 0xFF2A1A, "_violet": 0xA83CFF, "_orange": 0xFF8A00, "_blue": 0x3AA8FF, "_yellow": 0xFFD21A}
N = 32


def cube(name, frm, to, uv):
    return {"name": name, "box_uv": True, "from": frm, "to": to, "origin": [0, 0, 0], "uv_offset": uv,
            "type": "cube", "uuid": str(uuid.uuid5(uuid.NAMESPACE_DNS, "lantern_port." + name))}


elements = [
    cube("collar_top", [-5, 3.5, -2], [5, 5, 0], [0, 0]),
    cube("collar_bottom", [-5, -5, -2], [5, -3.5, 0], [0, 0]),
    cube("collar_left", [-5, -3.5, -2], [-3.5, 3.5, 0], [0, 0]),
    cube("collar_right", [3.5, -3.5, -2], [5, 3.5, 0], [0, 0]),
    cube("prong_tl", [-5, 4, -3], [-4, 5, -2], [0, 0]),
    cube("prong_tr", [4, 4, -3], [5, 5, -2], [0, 0]),
    cube("prong_bl", [-5, -5, -3], [-4, -4, -2], [0, 0]),
    cube("prong_br", [4, -5, -3], [5, -4, -2], [0, 0]),
    # The plate the ring's face presses on, sunk half a pixel into the collar.
    cube("glow_plate", [-3.5, -3.5, -0.5], [3.5, 3.5, 0], [0, 16]),
]
model = {
    "meta": {"format_version": "4.10", "model_format": "modded_entity", "box_uv": True},
    "name": "lantern_port",
    "resolution": {"width": N, "height": N},
    "elements": elements,
    "outliner": [{"name": "lantern_port", "origin": [0, 0, 0], "children": [e["uuid"] for e in elements]}],
    "textures": [{"name": "lantern_port.png", "folder": "entity/bb", "namespace": "lanternring", "id": "0",
                  "width": N, "height": N, "uv_width": N, "uv_height": N}],
}
with open(os.path.join(ASSETS, "bbmodel/lantern_port.bbmodel"), "w") as f:
    json.dump(model, f, indent=1)

for suffix, rgb in CORPS.items():
    random.seed(7)
    img = Image.new("RGBA", (N, N))
    px = img.load()
    cr, cg, cb = rgb >> 16 & 0xFF, rgb >> 8 & 0xFF, rgb & 0xFF
    for y in range(N):
        for x in range(N):
            if y < 16:
                # Brushed gold with a darker band every few pixels.
                k = 0.85 + 0.15 * random.random() - (0.12 if x % 5 == 0 else 0)
                px[x, y] = (int(232 * k), int(180 * k), int(52 * k), 255)
            else:
                # The plate: a bright core and a thin ring around it, so the ring's face reads as docked.
                # Centred on the plate's front face (box UV puts it at 0.5..7.5, 16.5..23.5).
                cx, cy = x - 4, y - 20
                d = max(abs(cx), abs(cy))
                k = 1.0 if d <= 1 else 0.55 if d == 2 else 0.85
                w = 0.55 if d <= 1 else 0.1
                px[x, y] = (int(min(255, cr * k + 255 * w)), int(min(255, cg * k + 255 * w)), int(min(255, cb * k + 255 * w)), 255)
    img.save(os.path.join(ASSETS, "textures/entity/bb/lantern_port" + suffix + ".png"))
