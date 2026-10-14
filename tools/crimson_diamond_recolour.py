"""Vanilla diamond block, recoloured to the Red battery's C1 crimson (J, 2026-10-14: "the diamond blocks that reflect,
used as the surface ... because it reflects well in my shaders and looks like good metal", "just turned into the
crimson red hue like we've made in Blender before").

Mojang's texture is not ours to ship, so this makes a PREVIEW copy only (for J's Blender, from his own game jar). In
the game, keep the real diamond_block texture and its shader ID and recolour it at load time (see the hand-off).

    python tools/crimson_diamond_recolour.py diamond_block.png OUT.png [scale]
Each pixel's brightness (darkest..brightest of the tile) runs through the battery's C1 crimson ramp.
"""
import sys
import numpy as np
from PIL import Image

C1 = [(28, 2, 8), (88, 6, 20), (150, 14, 34), (214, 52, 66), (255, 176, 180)]   # tools/pixel_rage_battery3.py REDS["c1"]
src, out = sys.argv[1], sys.argv[2]
scale = int(sys.argv[3]) if len(sys.argv) > 3 else 1
a = np.asarray(Image.open(src).convert("RGBA")).astype(float)
lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
v = (lum - lum.min()) / max(lum.max() - lum.min(), 1)
v = 0.12 + 0.88 * v                                       # keep the darkest pixels off black
t = v * 4; i = np.minimum(t.astype(int), 3); f = (t - i)[..., None]; f = f * f * (3 - 2 * f)
s = np.array(C1, float)
rgb = s[i] * (1 - f) + s[i + 1] * f
im = Image.fromarray(np.concatenate([rgb, a[..., 3:]], -1).round().astype(np.uint8), "RGBA")
if scale > 1:
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
im.save(out)
print("ok")
