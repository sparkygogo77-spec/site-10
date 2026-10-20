"""Top-down maps of burrow web layouts (J's lair note 4): tunnels coloured by height over a faint lair outline.

python burrow_web_maps.py <out.png> <label>=<sequence dir> [<label>=<dir> ...]
Writes one picture with the layouts side by side, each titled with its label and tunnel/den counts.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
items = [a.split("=", 1) for a in sys.argv[2:]]
panels = []
for label, d in items:
    z = np.load(os.path.join(d, "sequence.npz"))
    mask, solid = z["mask"], z["solid"]
    meta = json.loads(str(z["meta"]))
    X, Y, Z = mask.shape
    tun = np.isin(mask, (11,))
    den = mask == 12
    ring = np.isin(mask, (3,))
    lair_air = (~solid) & (mask == 1) & (np.arange(Y)[None, :, None] < meta["trap"]["lair_roof_y"] - meta["y_min"] + 12)
    ys = np.arange(Y)[None, :, None]
    img = np.zeros((Z, X, 3), float) + np.array([22, 22, 26])
    foot = lair_air.any(1).T
    img[foot] = [52, 58, 74]
    # tunnels: brightness by height (high = pale gold, low = deep amber)
    any_t = tun.any(1)
    hy = np.where(tun, ys, -1).max(1).astype(float)
    lo, hi = np.percentile(hy[any_t], 3), np.percentile(hy[any_t], 97)
    t = np.clip((hy - lo) / max(1, hi - lo), 0, 1)
    col = np.stack([150 + 105 * t, 80 + 140 * t, 30 + 90 * t], -1)
    img[any_t.T] = col.transpose(1, 0, 2)[any_t.T]
    img[ring.any(1).T] = [120, 160, 200]
    img[den.any(1).T] = [235, 235, 225]
    im = Image.fromarray(img.astype(np.uint8)).resize((X * 2, Z * 2), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype("arialbd.ttf", 28); f2 = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    bw = meta["trap"]["burrow_web"]
    dr.text((14, 10), label, fill=(255, 255, 255), font=f1)
    dr.text((14, 46), f"{bw.get('den_count', 5)} dens, {bw.get('tunnels')} tunnels", fill=(220, 220, 220), font=f2)
    panels.append(im)
W_ = sum(p.width for p in panels) + 20 * (len(panels) - 1)
H_ = max(p.height for p in panels) + 40
sheet = Image.new("RGB", (W_, H_), (14, 14, 16))
x = 0
for p in panels:
    sheet.paste(p, (x, 0)); x += p.width + 20
dr = ImageDraw.Draw(sheet)
try:
    f2 = ImageFont.truetype("arial.ttf", 18)
except OSError:
    f2 = ImageFont.load_default()
dr.text((14, H_ - 30), "Seen from above. Gold = burrows (pale = higher), white = dens, blue = the lair's ring tunnel, slate = the lair below.", fill=(200, 200, 200), font=f2)
sheet.save(out)
print("map", out, sheet.size)
