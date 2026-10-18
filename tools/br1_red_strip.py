"""BRJR (Blender pass 701, J's KEEP 2026-10-15): the BR1 jade construct strip recoloured to the Red corps' crimson.

The same recolour as the 701 Blender script's Hue/Saturation node (hue 0.135, saturation 1.2): every pixel's hue moves
-0.365 (jade 0.40 -> crimson ~0.035) and its saturation is multiplied by 1.2; value and alpha are kept.
Like the node, it works in linear colour.
Writes textures/block/construct_ripples_red_br1.png and copies the jade strip's .mcmeta (same frames and frametime).

    python3 tools/br1_red_strip.py
"""
import colorsys
import os
import shutil

import numpy as np
from PIL import Image

BLOCK = os.path.join(os.path.dirname(__file__), "..", "src/main/resources/assets/lanternring/textures/block")
SRC = os.path.join(BLOCK, "construct_ripples_br1_jade.png")
OUT = os.path.join(BLOCK, "construct_ripples_red_br1.png")

HUE_SHIFT = 0.135 - 0.5   # Blender's Hue input: 0.5 is no change
SAT = 1.2

im = np.asarray(Image.open(SRC).convert("RGBA")).astype(np.float64) / 255.0
# Blender's node works on linear colour, so shift there (in sRGB the same numbers land on brick orange).
srgb = im[..., :3]
rgb = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4).reshape(-1, 3)
out = np.empty_like(rgb)
for i, (r, g, b) in enumerate(rgb):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    out[i] = colorsys.hsv_to_rgb((h + HUE_SHIFT) % 1.0, min(1.0, s * SAT), v)
out = np.clip(out, 0, 1)
out = np.where(out <= 0.0031308, out * 12.92, 1.055 * out ** (1 / 2.4) - 0.055)
res = np.concatenate([out.reshape(im.shape[:2] + (3,)), im[..., 3:]], axis=2)
Image.fromarray(np.round(res * 255).astype(np.uint8), "RGBA").save(OUT, optimize=True)
shutil.copyfile(SRC + ".mcmeta", OUT + ".mcmeta")
print(OUT, Image.open(OUT).size)
