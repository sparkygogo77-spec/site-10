"""Corps metals (J, 2026-10-14: "create colours of every metal like diamond in the hue of every lantern corps, do black
as a metal"). The vanilla metal and gem blocks that shine under shader packs (diamond, emerald, iron, gold, netherite,
copper), every quartz block and every nether brick, each recoloured into every corps hue plus a black metal, the same way as the crimson diamond: each pixel's
brightness (darkest..brightest of the tile, darkest kept at 12 %) runs through the colour's five-stop ramp.

Mojang's textures are not ours to ship, so this only makes PREVIEW copies from J's own game jar (for Blender). In the
game, keep the vanilla texture and its shader ID and recolour it at load time with these ramps (see the hand-off).

    python tools/corps_metal_recolour.py BLOCK_TEXTURE_DIR OUTDIR   -> <block>_<colour>.png, metals_sheet.png
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
RAMPS = {
    "crimson": [(28, 2, 8), (88, 6, 20), (150, 14, 34), (214, 52, 66), (255, 176, 180)],      # the Red battery's C1
    "green":   [(2, 22, 10), (6, 70, 32), (14, 132, 62), (60, 206, 112), (196, 255, 214)],
    "blue":    [(2, 8, 30), (6, 30, 90), (14, 72, 170), (60, 150, 240), (196, 230, 255)],
    "yellow":  [(30, 16, 0), (96, 56, 0), (176, 122, 6), (240, 200, 46), (255, 248, 196)],
    "violet":  [(14, 4, 30), (50, 12, 92), (106, 34, 172), (178, 100, 246), (238, 214, 255)],
    "orange":  [(30, 8, 0), (96, 30, 0), (176, 76, 4), (246, 146, 30), (255, 226, 176)],
    "black":   [(4, 4, 6), (14, 14, 18), (32, 32, 38), (70, 72, 82), (168, 172, 186)],        # gunmetal: dark, bright edges
}
BLOCKS = ["diamond_block", "emerald_block", "iron_block", "gold_block", "netherite_block", "copper_block",
          # J, 2026-10-14: quartz and nether brick metals; then "remove quartz, smooth quartz and nether bricks"
          "chiseled_quartz_block", "quartz_bricks", "quartz_pillar_side",
          "red_nether_bricks", "chiseled_nether_bricks", "cracked_nether_bricks"]


def recolour(a, ramp):
    lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
    span = lum.max() - lum.min()
    v = (lum - lum.min()) / max(span, 1)
    k = float(np.clip(span / 110.0, 0.4, 1.0))          # near-flat tiles (smooth quartz) keep their soft look
    v = 0.58 + (v - 0.5) * k if k < 1 else v
    v = 0.12 + 0.88 * v
    t = v * 4; i = np.minimum(t.astype(int), 3); f = (t - i)[..., None]; f = f * f * (3 - 2 * f)
    s = np.array(ramp, float)
    return np.concatenate([s[i] * (1 - f) + s[i + 1] * f, a[..., 3:]], -1).round().astype(np.uint8)


T, P = 96, 8
sheet = Image.new("RGB", (130 + len(RAMPS) * (T + P), 40 + len(BLOCKS) * (T + P)), (16, 18, 22))
d = ImageDraw.Draw(sheet)
for j, col in enumerate(RAMPS):
    d.text((130 + j * (T + P) + 4, 14), col.upper(), fill=tuple(RAMPS[col][3]) if col != "black" else (200, 200, 210))
for i, b in enumerate(BLOCKS):
    a = np.asarray(Image.open(os.path.join(SRC, b + ".png")).convert("RGBA")).astype(float)
    d.text((6, 40 + i * (T + P) + 40), b.replace("_block", "").replace("_side", "").replace("quartz_bottom", "smooth quartz"), fill=(230, 230, 230))
    for j, col in enumerate(RAMPS):
        im = Image.fromarray(recolour(a, RAMPS[col]), "RGBA")
        im.save(os.path.join(OUT, f"{b}_{col}.png"))
        sheet.paste(im.convert("RGB").resize((T, T), Image.NEAREST), (130 + j * (T + P), 40 + i * (T + P)))
sheet.save(os.path.join(OUT, "metals_sheet.png"))
json.dump({"ramps": RAMPS, "blocks": BLOCKS}, open(os.path.join(OUT, "metals.json"), "w"), indent=1)
print("ok")
