"""The Red battery's gem shine (J, 2026-10-15: "i want it to shine like these diamond blocks").

    python tools/red_battery_specular.py

For red_battery, red_battery_cover and the classic red_lantern (textures/entity/bb):
- Re-bakes the battery's stone faces to the approved smooth glossy crimson, sRGB (188, 30, 47)
  (red-battery-final hand-off): one colour per face, so no tiled facets, a very soft large-scale
  variation across the model, and faces turned away from the light a shade deeper.
  The classic red_lantern keeps its colours (only its map is made).
- Writes <name>_s.png next to each, a LabPBR specular map in the same layout:
    R  smoothness: 0.84 on the stone (215), a little softer on the glowing parts
    G  F0 0.04 (10), a gem, not a metal; the classic lantern's gold trim is gold (231)
    B  3: the mod's marker, so the patched Complementary reads these maps even in its
       Integrated PBR+ mode, where it ignores _s maps (ShaderPackPatcher.SHINE)
    A  emission: 255 (none) on the stone; the glowing texels keep their light
Glow texels are the faces of the model's glow_* cubes. Run tools/optimize_textures.py after.
"""
import json
import math
import os

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets", "lanternring")
CRIMSON = np.array([188, 30, 47], float)
# How light each face's direction is: the top catches the light, the underside is a shade deeper.
FACE_LIGHT = {"up": 1.04, "north": 1.0, "south": 1.0, "east": 0.97, "west": 0.97, "down": 0.88}
MARKER = 3
# Smoothness 0.84: glossy, but 0.9 mirrored so much sky that the crimson read pink-white (J, 2026-10-16).
STONE = 215


def faces(model, size):
    """Each face's texel rectangle, with its cube's name, centre and the face's direction."""
    sx = size[0] / model["resolution"]["width"]
    sy = size[1] / model["resolution"]["height"]
    for e in model["elements"]:
        centre = [(a + b) / 2 for a, b in zip(e["from"], e["to"])]
        for side, f in e["faces"].items():
            u0, v0, u1, v1 = f["uv"]
            x0, x1 = sorted((u0 * sx, u1 * sx))
            y0, y1 = sorted((v0 * sy, v1 * sy))
            yield e["name"], centre, side, (int(round(y0)), int(round(y1)), int(round(x0)), int(round(x1)))


def soft(c):
    """A very soft variation over the model, about +-3%, across a few blocks' worth of pixels."""
    x, y, z = c
    return 1.0 + 0.018 * math.sin(x * 0.21 + y * 0.13) + 0.012 * math.sin(z * 0.17 - y * 0.09 + 1.3)


def make(name, rebake):
    model = json.load(open(os.path.join(ROOT, "bbmodel", name + ".bbmodel")))
    path = os.path.join(ROOT, "textures", "entity", "bb", name + ".png")
    img = np.asarray(Image.open(path).convert("RGBA")).astype(float)
    h, w = img.shape[:2]
    spec = np.zeros((h, w, 4), float)
    out = img.copy()
    for cube, centre, side, (y0, y1, x0, x1) in faces(model, (w, h)):
        if y1 <= y0 or x1 <= x0:
            continue
        px = img[y0:y1, x0:x1]
        solid = px[..., 3] > 0
        if cube.startswith("glow"):
            lum = (px[..., :3] @ np.array([0.2125, 0.7154, 0.0721])) / 255.0
            s = spec[y0:y1, x0:x1]
            s[..., 0] = 200
            s[..., 1] = 10
            s[..., 2] = MARKER
            s[..., 3] = np.clip(np.round(lum * 254), 1, 254)
            s[~solid] = 0
            continue
        s = spec[y0:y1, x0:x1]
        if rebake:
            out[y0:y1, x0:x1, :3] = np.clip(CRIMSON * FACE_LIGHT[side] * soft(centre), 0, 255)
            s[..., :] = (STONE, 10, MARKER, 255)
        else:
            r, g, b = px[..., 0], px[..., 1], px[..., 2]
            gold = (g > 0.45 * r) & (r > b + 30)
            dark = px[..., :3].max(-1) < 40
            s[..., :] = (STONE, 10, MARKER, 255)
            s[gold] = (215, 231, MARKER, 255)
            s[dark] = (120, 10, MARKER, 255)
        s[~solid] = 0
    spec[img[..., 3] == 0] = 0
    if rebake:
        Image.fromarray(np.round(out).astype(np.uint8), "RGBA").save(path, optimize=True)
    Image.fromarray(np.round(spec).astype(np.uint8), "RGBA").save(path[:-4] + "_s.png", optimize=True)
    print("wrote", name, "_s.png", "(stone re-baked)" if rebake else "")


if __name__ == "__main__":
    make("red_battery", True)
    make("red_battery_cover", True)
    make("red_lantern", False)
