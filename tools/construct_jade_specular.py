"""LabPBR specular map for the jade construct sheet, so shader packs make the jade shine:
    python tools/construct_jade_specular.py <construct_jade.png> [more sheets...]

Writes construct_jade_s.png next to each sheet, same size, so every outline tile lines up:
- R  perceptual smoothness: polished jade, about 0.93, with a faint grain so the reflection
     isn't a flat mirror; the dark flecks are rougher stone and the glowing rims a little softer.
- G  F0 0.05 (13/255), a dielectric gem like emerald, not metal.
- B  0: no porosity or subsurface (the jade's own translucency already does that job).
- A  emission in labPBR terms, from the jade's brightness, so the jade still glows when a pack
     reads the map in labPBR mode (Complementary's own construct glow covers Integrated PBR+).
"""
import os, sys
import numpy as np
from PIL import Image

F0 = 13  # 0.05 * 255


def specular(sheet):
    px = np.asarray(sheet.convert("RGBA")).astype(float) / 255.0
    rgb, alpha = px[..., :3], px[..., 3]
    lum = rgb @ np.array([0.2125, 0.7154, 0.0721])
    body = np.median(lum[alpha > 0.5])

    smooth = np.full(lum.shape, 0.93)
    smooth += (lum - body) * 0.25                                           # faint grain from the jade's own mottling
    smooth -= np.clip((body - lum - 0.05) * 4.0, 0, 1) * 0.30               # dark flecks: rough inclusions
    smooth -= np.clip((lum - 0.55) * 2.0, 0, 1) * 0.12                      # glowing rims: softer
    smooth = np.clip(smooth, 0.55, 0.97)

    out = np.zeros(px.shape)
    out[..., 0] = smooth
    out[..., 1] = F0 / 255.0
    out[..., 2] = 0.0
    out[..., 3] = np.clip(lum * 0.53, 0.0, 254 / 255.0)
    out[alpha == 0] = 0.0
    return Image.fromarray(np.round(out * 255).astype(np.uint8), "RGBA")


if __name__ == "__main__":
    for path in sys.argv[1:]:
        out = os.path.splitext(path)[0] + "_s.png"
        specular(Image.open(path)).save(out, optimize=True)
        print("wrote", out)
