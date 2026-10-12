"""The streak of light behind fast ring flight: python tools/flight_trail_texture.py <assets_dir>

  <assets_dir>/textures/entity/flight_trail.png  4x16 white, opaque down the middle row and fading
                                                 to clear at the top and bottom edges. FlightTrail
                                                 tints it with the ring's corps colour.
"""
import math, os, sys
from PIL import Image

OUT = sys.argv[1]
W, H = 4, 16
img = Image.new("RGBA", (W, H))
px = img.load()
for y in range(H):
    d = abs((y + 0.5) / H - 0.5) * 2  # 0 in the middle, 1 at the edges
    a = math.exp(-(d / 0.42) ** 2)
    for x in range(W):
        px[x, y] = (255, 255, 255, int(255 * a))
os.makedirs(os.path.join(OUT, "textures/entity"), exist_ok=True)
img.save(os.path.join(OUT, "textures/entity/flight_trail.png"))
