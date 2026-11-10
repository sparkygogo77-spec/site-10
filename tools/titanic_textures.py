"""Ship versions of J's green construct textures for the Titanic construct (pass 952).

Takes the library strips he picked (BR1 emerald bricks, W1 neon weave, H1 hex) and polishes them for a 269-block
ship: slower and smoother (each frame blended with its neighbours, frametime 5), highlights pulled back from pale
mint to saturated green (red <= 0.30 x green, blue <= 0.50 x green), 12% darker, and the tile seams and the loop
measured. The originals are not touched: this writes construct_<tex>_green_ship.png (+ .mcmeta) beside them.

    python tools/titanic_textures.py [docs/texture_library] [extra out dir]
"""
import json, os, sys
import numpy as np
from PIL import Image

LIB = sys.argv[1] if len(sys.argv) > 1 else "docs/texture_library"
EXTRA = sys.argv[2] if len(sys.argv) > 2 else None
NAMES = {"br1": "BR1 bricks (hull plating)", "w1": "W1 weave (decks and cabins)", "h1": "H1 hex (funnels)"}


def measure(fr):
    n = len(fr)
    step = [np.abs(fr[j] - fr[(j + 1) % n]).mean() for j in range(n)]
    # a seam shows as a jump across the tile edge that is bigger than the same jump one tile-row further in
    sx = np.abs(fr[:, :, 0] - fr[:, :, -1]).mean(); ix = np.abs(fr[:, :, 1:] - fr[:, :, :-1]).mean((0, 1, 3)).max()
    sy = np.abs(fr[:, 0] - fr[:, -1]).mean(); iy = np.abs(fr[:, 1:] - fr[:, :-1]).mean((0, 2, 3)).max()
    return {"loop_jump": round(float(step[-1]), 2), "mean_step": round(float(np.mean(step[:-1])), 2),
            "seam_x": round(float(sx), 1), "worst_inner_x": round(float(ix), 1),
            "seam_y": round(float(sy), 1), "worst_inner_y": round(float(iy), 1),
            "motion": round(float(np.mean(step)), 2), "max_rgb": [int(v) for v in fr.max((0, 1, 2))]}


for tex in NAMES:
    src = os.path.join(LIB, "green", tex, f"construct_{tex}_green.png")
    im = Image.open(src).convert("RGB")
    w = im.size[0]; n = im.size[1] // w
    fr = np.asarray(im, np.float32).reshape(n, w, w, 3)
    before = measure(fr)
    out = 0.25 * np.roll(fr, 1, 0) + 0.5 * fr + 0.25 * np.roll(fr, -1, 0)       # smoother, the loop stays closed
    g = out[..., 1]
    out[..., 0] = np.minimum(out[..., 0], 0.30 * g)                             # no pale mint
    out[..., 2] = np.minimum(out[..., 2], 0.50 * g)
    out *= 0.88
    after = measure(out)
    strip = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8).reshape(n * w, w, 3))
    strip = strip.quantize(256, method=Image.Quantize.FASTOCTREE)
    for d in [os.path.join(LIB, "green", tex)] + ([EXTRA] if EXTRA else []):
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"construct_{tex}_green_ship.png")
        strip.save(p, optimize=True)
        json.dump({"animation": {"interpolate": True, "frametime": 5}}, open(p + ".mcmeta", "w"))
    print(tex, NAMES[tex], "frames", n, "KB", os.path.getsize(p) // 1024)
    print("  before", before)
    print("  after ", after)
