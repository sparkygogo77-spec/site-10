"""The small socket the ring docks into on lanterns without an emblem of their own (the Stone and
Compact batteries; the others dock on their emblem, lens or built-in socket):
python tools/lantern_port_assets.py src/main/resources/assets/lanternring

  bbmodel/lantern_port.bbmodel     A round collar 5 units across, set into the face (its back at
                                   z = 0, 0.75 proud), around a glowing disc sunk a quarter unit.
  textures/entity/bb/lantern_port[_stone][_<corps>].png
                                   The collar in the lantern's own trim (dark jade metal, or the
                                   Stone battery's mossy stone) and the disc in each corps' colour.
"""
import json, os, random, sys, uuid
from PIL import Image

ASSETS = sys.argv[1]
CORPS = {"": 0x3CFF5A, "_red": 0xFF2A1A, "_violet": 0xA83CFF, "_orange": 0xFF8A00, "_blue": 0x3AA8FF, "_yellow": 0xFFD21A}
TRIMS = {"": [(20, 52, 30), (34, 78, 44), (14, 34, 20)], "_stone": [(58, 62, 56), (74, 80, 70), (52, 72, 46)]}
N = 16


def cube(name, frm, to, uv):
    return {"name": name, "box_uv": True, "from": frm, "to": to, "origin": [0, 0, 0], "uv_offset": uv,
            "type": "cube", "uuid": str(uuid.uuid5(uuid.NAMESPACE_DNS, "lantern_port2." + name))}


# Four bars with the corners left out read as a round collar at this size.
elements = [
    cube("collar_top", [-1.5, 1.5, -0.75], [1.5, 2.5, 0], [0, 0]),
    cube("collar_bottom", [-1.5, -2.5, -0.75], [1.5, -1.5, 0], [0, 0]),
    cube("collar_left", [-2.5, -1.5, -0.75], [-1.5, 1.5, 0], [0, 0]),
    cube("collar_right", [1.5, -1.5, -0.75], [2.5, 1.5, 0], [0, 0]),
    cube("glow_disc", [-1.5, -1.5, -0.25], [1.5, 1.5, 0], [0, 8]),
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

for trim, shades in TRIMS.items():
    for suffix, rgb in CORPS.items():
        random.seed(11)
        img = Image.new("RGBA", (N, N))
        px = img.load()
        cr, cg, cb = rgb >> 16 & 0xFF, rgb >> 8 & 0xFF, rgb & 0xFF
        for y in range(N):
            for x in range(N):
                if y < 8:
                    px[x, y] = random.choice(shades) + (255,)
                else:
                    # The disc (front face at 0.25..3.25, 8.25..11.25): a hot middle fading to the edge.
                    d = max(abs(x - 1.5), abs(y - 9.5))
                    w = 0.6 if d < 1 else 0.15
                    k = 1.0 if d < 1 else 0.75
                    px[x, y] = (int(min(255, cr * k + 255 * w)), int(min(255, cg * k + 255 * w)), int(min(255, cb * k + 255 * w)), 255)
        img.save(os.path.join(ASSETS, "textures/entity/bb/lantern_port" + trim + suffix + ".png"))
