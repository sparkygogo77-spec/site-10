"""Smooth black metal (J, 2026-10-14: "one with more black metal but remove the lines and make it as smooth of a surface
as can be but also still textured"). Our own 16 x 16 tile (no vanilla source): the black gunmetal ramp, no bevels, seams
or edge lines; only a soft, seamless mottling and a faint diagonal brushed grain so it still reads as a texture, and a
gentle sheen band. Tiles seamlessly, so a wall of it reads as one surface.

    python tools/smooth_black_metal.py OUTDIR [colour]  -> smooth_metal_<colour>.png (16 px), _s.png (LabPBR: smooth metal)
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]; COL = sys.argv[2] if len(sys.argv) > 2 else "black"
os.makedirs(OUT, exist_ok=True)
RAMPS = {"black": [(4, 4, 6), (14, 14, 18), (32, 32, 38), (70, 72, 82), (168, 172, 186)],
         "crimson": [(28, 2, 8), (88, 6, 20), (150, 14, 34), (214, 52, 66), (255, 176, 180)]}
N = 16
r = np.random.default_rng(7)
y, x = np.mgrid[0:N, 0:N]
v = np.zeros((N, N))
for k in (1, 2):                                                   # soft periodic mottling (seamless)
    for _ in range(3):
        fx, fy = r.integers(-k, k + 1, 2); ph = r.uniform(0, 2 * np.pi)
        v += 0.04 / k * np.cos(2 * np.pi * (fx * x + fy * y) / N + ph)
v += 0.025 * np.cos(2 * np.pi * (x + y) * 4 / N + 1.3)            # faint diagonal brushed grain
v += 0.03 * np.exp(-(((x - y) % N - N / 2) / 3.5) ** 2)            # gentle sheen band
v = 0.40 + v                                                       # mid-dark gunmetal, no edges
s = np.array(RAMPS[COL], float); t = np.clip(v, 0, 1) * 4
i = np.minimum(t.astype(int), 3); f = (t - i)[..., None]; f = f * f * (3 - 2 * f)
rgb = (s[i] * (1 - f) + s[i + 1] * f).round().astype(np.uint8)
Image.fromarray(rgb, "RGB").save(os.path.join(OUT, f"smooth_metal_{COL}.png"))
sp = np.zeros((N, N, 4), np.uint8); sp[..., 0] = 235; sp[..., 1] = 230; sp[..., 3] = 255   # LabPBR: smooth, metal (iron)
Image.fromarray(sp, "RGBA").save(os.path.join(OUT, f"smooth_metal_{COL}_s.png"))
print("ok")
