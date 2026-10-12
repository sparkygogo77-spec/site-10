"""Gives the Blue Lantern villagers their faces and expressions (J, 2026-10-12: "they should have
emotion as they are fighters and builders and hope lanterns"):
python tools/villager_faces.py <assets_dir>

Run after blue_villager_skin.py / hard_light_skins.py. For the suit (blue_villager.png) and the
hard light construct (blue_construct.png) it repaints the brow, eyes and mouth on the head's front
face and writes one texture per expression next to it:
  <name>.png         hopeful: a raised, arched brow and a smile (the default)
  <name>_focus.png   building: the brow lowered and level, eyes up at the work, mouth set
  <name>_fierce.png  fighting: the brow in a hard V, narrowed eyes, teeth bared
  <name>_blink.png   eyes shut (BlueVillagerRenderer blinks every few seconds)
The suit keeps the vanilla villager's skin and green eyes; the construct's features are glowing
hard light (pale eyes with deep blue pupils, a bright brow and mouth) on its smooth face.
"""
import os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hard_light_skins import ramp  # noqa: E402

S = 4
FACE_X, FACE_Y = 8 * S, 8 * S  # the head's front face in the 64x64 layout
W = 8 * S

STYLES = {
    "blue_villager": dict(skin=(0xBE, 0x88, 0x6C), skin_lo=(0xB3, 0x7B, 0x62), brow=(0x33, 0x24, 0x11),
                          white=(255, 255, 255), pupil=(0x00, 0x96, 0x11), mouth=(0x77, 0x42, 0x35),
                          teeth=(240, 236, 226), alpha=255),
    # Deep blue brow and mouth read clearly on the bright plate; the eyes glow.
    "blue_construct": dict(skin=None, skin_lo=None, brow=(8, 30, 96), white=(236, 252, 255),
                           pupil=(8, 30, 96), mouth=(8, 30, 96), teeth=(236, 252, 255), alpha=255),
}


def line(px, x0, y0, x1, y1, thick, col):
    """A thick line between two points (local face pixels)."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for dx in range(thick):
            for dy in range(thick):
                px(round(x - thick / 2 + dx + 0.5), round(y - thick / 2 + dy + 0.5), col)


def plate(x, y):
    """The construct's smooth face plate at a face pixel, as hard_light_skins.py paints it."""
    return ramp(0.55 + 0.06 + 0.18 * (1 - (x / W + y / (10 * S)) / 2))


def paint(base, st, mood):
    img = base.copy()
    p = img.load()
    a = st["alpha"]

    def put(x, y, col):
        if 0 <= x < W and 0 <= y < 10 * S:
            p[FACE_X + x, FACE_Y + y] = col + (a,)

    # Clear the features (texel rows 4 to 9, columns 1 to 6) back to plain skin.
    for y in range(4 * S, 9 * S + S):
        for x in range(1 * S, 7 * S):
            if st["skin"] is not None:
                put(x, y, st["skin"] if y < 7 * S else st["skin_lo"])
            else:
                put(x, y, plate(x, y))

    eye_top = 6 * S
    if mood == "hope":
        # Raised brows, the outer ends a little lower: open and hopeful.
        for x in range(4, 28):
            lift = 1 if 7 <= x <= 24 else 0
            for y in (21 - lift, 22 - lift):
                put(x, y, st["brow"])
    elif mood == "focus":
        for x in range(4, 28):
            for y in (21, 22, 23):
                put(x, y, st["brow"])
    elif mood == "fierce":
        line(put, 4, 19, 15, 24, 3, st["brow"])
        line(put, 16, 24, 27, 19, 3, st["brow"])
        eye_top = 6 * S + 1
    elif mood == "blink":
        for x in range(4, 28):
            for y in (20, 21):
                put(x, y, st["brow"])

    # Eyes: white outside, pupil inside (the villager's), pupils up when focused on the work.
    if mood == "blink":
        for x in list(range(4, 12)) + list(range(20, 28)):
            put(x, 26, st["brow"])
            put(x, 27, st["brow"])
    else:
        for y in range(eye_top, 7 * S):
            for x in range(4, 8):
                put(x, y, st["white"])
                put(x + 20, y, st["white"])
            for x in range(8, 12):
                put(x, y, st["pupil"])
                put(x + 12, y, st["pupil"])
        if mood == "focus":
            for x in list(range(4, 12)) + list(range(20, 28)):
                put(x, 27, st["skin"] or plate(x, 27))
            for x in list(range(8, 12)) + list(range(20, 24)):
                put(x, 24, st["pupil"])
        if mood == "hope":
            # A glint in each pupil.
            put(9, 24, st["white"])
            put(21, 24, st["white"])

    # Mouth (texel row 8), under the nose.
    if mood == "hope":
        line(put, 9, 32, 11, 34, 1, st["mouth"])
        for x in range(11, 21):
            put(x, 34, st["mouth"])
            put(x, 35, st["mouth"])
        line(put, 20, 34, 22, 32, 1, st["mouth"])
    elif mood == "focus":
        for x in range(12, 20):
            put(x, 34, st["mouth"])
    elif mood == "fierce":
        for y in range(32, 37):
            for x in range(9, 23):
                put(x, y, st["mouth"] if y in (32, 36) or x in (9, 22) else st["teeth"])
        for x in range(10, 22, 3):
            put(x, 34, st["mouth"])
    else:
        for x in range(11, 21):
            put(x, 34, st["mouth"])
    return img


if __name__ == "__main__":
    folder = os.path.join(sys.argv[1], "textures", "entity")
    for name, st in STYLES.items():
        path = os.path.join(folder, name + ".png")
        base = Image.open(path).convert("RGBA")
        for mood, suffix in (("focus", "_focus"), ("fierce", "_fierce"), ("blink", "_blink"), ("hope", "")):
            out = os.path.join(folder, name + suffix + ".png")
            paint(base, st, mood).save(out)
            print("wrote", out)
