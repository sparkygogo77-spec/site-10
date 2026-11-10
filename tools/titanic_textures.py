"""Hull plating textures drawn for the Titanic construct (pass 952 rev 2).

J's own textures are not copied or changed here. (Rev 1 made "polished" copies of BR1 / W1 / H1; J: "your new
textures are copies of mine but not as good", so they were removed.) This writes three new hull platings to
docs/texture_library/green/hp1..hp3/construct_<tex>_green_ship.png (+ .mcmeta) and measures loop and seams.

    python tools/titanic_textures.py [docs/texture_library] [extra out dir]
"""
import json, os, sys
import numpy as np
from PIL import Image

LIB = sys.argv[1] if len(sys.argv) > 1 else "docs/texture_library"
EXTRA = sys.argv[2] if len(sys.argv) > 2 else None


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


# ------------------------------------------------------------------ new hull plating, drawn for the ship (952 rev 2)
# J on D4: "the bricks dont fit on the hull ... or the hexagons anywhere really" / "a proper design green lantern
# version of what we have". Three hull platings, each built a different way, 128 px = 4 blocks, 24 frames,
# frametime 5. Dark lines (never white), shades of green only, the hull the darkest part of the ship.
HULLS = {"hp1": "HP1 riveted strakes", "hp2": "HP2 inlaid armour panels", "hp3": "HP3 flow plating"}
STOPS = np.array([(3, 30, 17), (6, 58, 30), (11, 92, 44), (22, 138, 60), (58, 205, 92)], np.float32)


def ramp(v):
    """0-1 -> the five greens, smoothstep between stops."""
    v = np.clip(v, 0, 1) * (len(STOPS) - 1)
    i = np.minimum(v.astype(int), len(STOPS) - 2)
    f = v - i
    f = f * f * (3 - 2 * f)
    return STOPS[i] * (1 - f[..., None]) + STOPS[i + 1] * f[..., None]


def hsh(a, b=0):
    return ((np.sin(a * 127.1 + b * 311.7) * 43758.5453) % 1.0)


def hull_frames(kind, n=24, w=128):
    y, x = np.mgrid[0:w, 0:w].astype(np.float32)
    out = []
    for f in range(n):
        t = f / n
        if kind == "hp1":
            r = y // 16; ly = y % 16
            off = (r * 37) % 64
            lx = (x + off) % 64
            plate = hsh(r, (x + off) // 64 % 2 + r * 3)
            v = 0.26 + 0.10 * plate + 0.05 * (1 - ly / 15)                 # each plate its own tone, lighter at the top
            v = np.where(ly == 1, v + 0.10, v)                             # the top lip
            seam = (ly == 0) | (lx == 0)
            run = np.maximum(0, np.cos(2 * np.pi * (x / w - t + r * 0.375))) ** 8
            v = np.where(seam, 0.06 + 0.62 * run * (ly == 0), v)           # dark seams; light glides along the long ones
            rivet = ((ly == 3) & (x % 4 == 1)) | ((lx == 2) & (ly % 4 == 2)) | ((lx == 62) & (ly % 4 == 2))
            v = np.where(rivet & ~seam, v + 0.13, v)
        elif kind == "hp2":
            r = y // 32
            px = (x + (r % 2) * 32) % 64; py = y % 32
            pid = hsh(r, (x + (r % 2) * 32) // 64 % 2 + r * 5)
            edge = np.minimum(np.minimum(px, 63 - px), np.minimum(py, 31 - py))
            v = 0.24 + 0.07 * pid + 0 * x
            v = np.where((edge >= 1) & (edge <= 2) & ((px <= 2) | (py <= 2)), v + 0.12, v)      # bevel: light top-left
            v = np.where((edge >= 1) & (edge <= 2) & ((px >= 61) | (py >= 29)), v - 0.09, v)    # dark bottom-right
            v = np.where(edge == 0, 0.05, v)
            breathe = 0.5 + 0.5 * np.cos(2 * np.pi * (t - pid))
            v = np.where(edge == 6, 0.30 + 0.50 * breathe, v)                                    # the glowing inlay line
            bolt = ((px % 56 >= 4) & (px % 56 <= 5)) & ((py % 24 >= 4) & (py % 24 <= 5)) & (edge <= 5)
            v = np.where(bolt, 0.10, v)
        else:
            r = y // 32; ly = y % 32
            v = 0.22 + 0.06 * hsh(r, 9) + 0.04 * np.sin(2 * np.pi * (2 * x / w + t + hsh(y, 3)))
            row = hsh(y, 1)
            s = np.sin(2 * np.pi * (3 * x / w - t) + row * 6.28) * np.sin(2 * np.pi * (x / w - 2 * t) + row * 17.0)
            v = np.where((row > 0.55) & (s > 0.55), v + 0.34 * (s - 0.55) / 0.45, v)             # streaks gliding one way
            v = np.where(ly == 0, 0.07, v)
            v = np.where((ly == 1), v + 0.08, v)
        out.append(ramp(v))
    return np.array(out, np.float32)


for tex, label in HULLS.items():
    fr = hull_frames(tex)
    m = measure(fr)
    n, w = fr.shape[0], fr.shape[1]
    strip = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8).reshape(n * w, w, 3)).quantize(256, method=Image.Quantize.FASTOCTREE)
    for d in [os.path.join(LIB, "green", tex)] + ([EXTRA] if EXTRA else []):
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"construct_{tex}_green_ship.png")
        strip.save(p, optimize=True)
        json.dump({"animation": {"interpolate": True, "frametime": 5}}, open(p + ".mcmeta", "w"))
    print(tex, label, "KB", os.path.getsize(p) // 1024, m)
