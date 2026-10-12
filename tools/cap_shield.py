"""Captain America's Shield: the 64x64 texture and the 3D item model.

The front art (rings of red and silver round a blue disc with a white star) is drawn at 2 pixels per
model unit in the texture's top-left 32x32; the back (brushed steel with leather straps) is in the
top-right 32x32, and the rim's steel is a strip under them. The model is a 1.5-unit-thick disc made
of one cube per row, with a slightly raised star boss in the middle.

    python3 tools/cap_shield.py
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "src/main/resources/assets/lanternring"
TEX = ASSETS / "textures/item/cap_shield.png"
MODEL = ASSETS / "models/item/cap_shield.json"
ITEM = ASSETS / "items/cap_shield.json"

RED = (178, 24, 32)
RED_DARK = (128, 14, 22)
SILVER = (214, 220, 228)
SILVER_DARK = (150, 158, 170)
BLUE = (26, 52, 140)
BLUE_DARK = (16, 32, 96)
WHITE = (246, 246, 250)
STEEL = (120, 128, 140)
STEEL_DARK = (84, 90, 102)
LEATHER = (92, 56, 32)


def star(cx, cy, r_out, r_in, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def texture():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    # Front: concentric rings, shaded a little darker to the lower right like a curved dish.
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16, y + 0.5 - 16
            d = math.hypot(dx, dy)
            if d > 16:
                continue
            shade = (dx + dy) / 32  # -1 top left .. +1 bottom right
            if d > 13:
                c, cd = RED, RED_DARK
            elif d > 10:
                c, cd = SILVER, SILVER_DARK
            elif d > 7:
                c, cd = RED, RED_DARK
            else:
                c, cd = BLUE, BLUE_DARK
            t = max(0.0, min(1.0, 0.35 + shade * 0.6))
            col = tuple(int(c[i] * (1 - t) + cd[i] * t) for i in range(3))
            # A thin bright highlight on the upper left of each ring.
            if shade < -0.45 and d > 7 and int(d) in (15, 12, 9):
                col = tuple(min(255, v + 40) for v in col)
            img.putpixel((x, y), col + (255,))
    ImageDraw.Draw(img).polygon(star(16, 16.4, 6.6, 2.6), fill=WHITE + (255,))
    # Back: brushed steel, with two leather straps.
    for y in range(32):
        for x in range(32, 64):
            d = math.hypot(x + 0.5 - 48, y + 0.5 - 16)
            if d > 16:
                continue
            v = 0.85 + 0.15 * math.sin(y * 1.7 + x * 0.3)
            img.putpixel((x, y), tuple(int(c * v) for c in STEEL) + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle([37, 11, 58, 13], fill=LEATHER + (255,))
    draw.rectangle([37, 19, 58, 21], fill=LEATHER + (255,))
    # Rim steel strip (uv 0..16, 8..9).
    for x in range(64):
        for y in range(32, 36):
            img.putpixel((x, y), (SILVER if y < 34 else SILVER_DARK) + (255,))
    # Star boss sides (uv 0..1, 9..10): white.
    draw.rectangle([0, 36, 3, 39], fill=WHITE + (255,))
    TEX.parent.mkdir(parents=True, exist_ok=True)
    img.save(TEX)


def model():
    elements = []
    z0, z1 = 7.25, 8.75
    rim = [0, 8, 16, 9]
    for row in range(16):
        # Model y runs up; texture rows run down.
        yc = row + 0.5 - 8
        half = math.sqrt(max(0.0, 64 - yc * yc))
        half = round(half * 2) / 2
        if half < 1:
            continue
        x0, x1 = 8 - half, 8 + half
        y0, y1 = row, row + 1
        # Front faces north (towards -z), which the display transforms turn to face away from the player.
        front = [x0 / 2, (16 - y1) / 2, x1 / 2, (16 - y0) / 2]
        # The back is mirrored left to right.
        back = [8 + (16 - x0) / 2, (16 - y1) / 2, 8 + (16 - x1) / 2, (16 - y0) / 2]
        elements.append({
            "name": f"row_{row}",
            "from": [x0, y0, z0],
            "to": [x1, y1, z1],
            "faces": {
                "north": {"uv": front, "texture": "#t"},
                "south": {"uv": back, "texture": "#t"},
                "east": {"uv": rim, "texture": "#t"},
                "west": {"uv": rim, "texture": "#t"},
                "up": {"uv": rim, "texture": "#t"},
                "down": {"uv": rim, "texture": "#t"},
            },
        })
    # The star boss: a slightly raised square under the star's centre (the star itself is painted).
    elements.append({
        "name": "boss",
        "from": [6.5, 6.5, 6.75],
        "to": [9.5, 9.5, 7.25],
        "faces": {
            "north": {"uv": [6.5 / 2, 6.5 / 2, 9.5 / 2, 9.5 / 2], "texture": "#t"},
            "east": {"uv": [0, 9, 1, 10], "texture": "#t"},
            "west": {"uv": [0, 9, 1, 10], "texture": "#t"},
            "up": {"uv": [0, 9, 1, 10], "texture": "#t"},
            "down": {"uv": [0, 9, 1, 10], "texture": "#t"},
        },
    })
    data = {
        "ambientocclusion": False,
        "textures": {"t": "lanternring:item/cap_shield", "particle": "lanternring:item/cap_shield"},
        "elements": elements,
        "gui_light": "front",
        "display": {
            "gui": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]},
            "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
            "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
            "head": {"rotation": [0, 0, 0], "translation": [0, 8, -6], "scale": [1, 1, 1]},
            "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [3, 2, 1], "scale": [1, 1, 1]},
            "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [3, 2, 1], "scale": [1, 1, 1]},
            "firstperson_righthand": {"rotation": [0, 170, 5], "translation": [2, 3, 0], "scale": [0.55, 0.55, 0.55]},
            "firstperson_lefthand": {"rotation": [0, 170, 5], "translation": [2, 3, 0], "scale": [0.55, 0.55, 0.55]},
        },
    }
    MODEL.write_text(json.dumps(data, indent="\t") + "\n")
    ITEM.write_text(json.dumps({"model": {"type": "minecraft:model", "model": "lanternring:item/cap_shield"}}, indent="\t") + "\n")


if __name__ == "__main__":
    texture()
    model()
    print("wrote", TEX.relative_to(ROOT), MODEL.relative_to(ROOT), ITEM.relative_to(ROOT))
