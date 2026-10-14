"""The crimson diamond block (J, 2026-10-14: "use the crimson red diamond blocks like the ones I wanted on my red
battery"). The Red battery's C1 crimson cut-gem tile (tools/pixel_rage_battery3.py: bevelled rim, a cut diamond in
the middle, a few glints), two tiles a side, as a whole block texture.

    python tools/crimson_diamond_block.py OUTDIR
  -> diamond_crimson.png      32 x 32, the block (2 x 2 gem tiles)
     diamond_crimson_16px.png 16 x 16, one tile (vanilla resolution)
     diamond_crimson_s.png    LabPBR specular for shader packs: smooth gem (R 230 smoothness, G 10 = F0 about 0.04)
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
_argv, sys.argv = sys.argv, ["pixel_rage_battery3.py", os.path.join(OUT, "_r3")]
import pixel_rage_battery3 as P3  # noqa: E402
sys.argv = _argv

t = P3.gem_tile("c1")
rgb = P3.ramp(t, P3.REDS["c1"]).round().clip(0, 255).astype(np.uint8)
tile = np.transpose(rgb, (1, 0, 2))                         # gem_tile is indexed (u, w) = (x, y)
block = np.tile(tile, (2, 2, 1))
Image.fromarray(block, "RGB").save(os.path.join(OUT, "diamond_crimson.png"))
Image.fromarray(tile, "RGB").save(os.path.join(OUT, "diamond_crimson_16px.png"))
spec = np.zeros((32, 32, 4), np.uint8)
spec[..., 0] = 230; spec[..., 1] = 10; spec[..., 2] = 0; spec[..., 3] = 255
seam = np.tile(np.transpose(t, (1, 0)), (2, 2)) < 0.15
spec[seam, 0] = 120                                          # the seams between tiles are rougher
Image.fromarray(spec, "RGBA").save(os.path.join(OUT, "diamond_crimson_s.png"))
print("ok")
