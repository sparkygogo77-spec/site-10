"""Glowing nether bricks (J, 2026-10-14: "keep nether bricks actually, they just should look closer to the glowing
construct version we have"). The vanilla nether bricks as a corps metal, with the mortar lit like BR1's glowing joints:
the bricks run through the corps metal ramp, the mortar (the tile's darkest pixels) becomes the ramp's bright light.

PREVIEW copies only (from J's own game); in game recolour the vanilla texture at load time and light the mortar with an
emissive overlay or a LabPBR specular map (the _s file: alpha = emission on the mortar, smooth metal elsewhere).

    python tools/glowing_nether_bricks.py nether_bricks.png OUTDIR [colour ...]
  -> nether_bricks_glow_<colour>.png, _e.png (emission mask), _s.png (LabPBR specular with emission in alpha)
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src, out = sys.argv[1], sys.argv[2]
cols = sys.argv[3:] or ["crimson", "green", "blue", "yellow", "violet", "orange", "black"]
os.makedirs(out, exist_ok=True)
_argv, sys.argv = sys.argv, ["corps_metal_recolour.py", os.path.dirname(src), os.path.join(out, "_m")]
import corps_metal_recolour as CM  # noqa: E402  (writes its preview set to OUT/_m; only RAMPS is used)
sys.argv = _argv
a = np.asarray(Image.open(src).convert("RGBA")).astype(float)
lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
mortar = lum <= np.percentile(lum, 22) + 0.5
for c in cols:
    ramp = CM.RAMPS[c]
    rgb = CM.recolour(a, ramp)[..., :3].astype(float)
    glow = np.array(ramp[3], float) * 0.45 + np.array(ramp[4], float) * 0.55
    rgb[mortar] = glow
    Image.fromarray(np.concatenate([rgb, a[..., 3:]], -1).round().astype(np.uint8), "RGBA").save(os.path.join(out, f"nether_bricks_glow_{c}.png"))
    e = np.where(mortar, 255, 0).astype(np.uint8)
    Image.fromarray(e, "L").save(os.path.join(out, f"nether_bricks_glow_{c}_e.png"))
    s = np.zeros(a.shape[:2] + (4,), np.uint8); s[..., 0] = np.where(mortar, 140, 225); s[..., 1] = 10
    s[..., 3] = np.where(mortar, 254, 0)                        # LabPBR: alpha 1..254 = emission
    Image.fromarray(s, "RGBA").save(os.path.join(out, f"nether_bricks_glow_{c}_s.png"))
print("ok")
