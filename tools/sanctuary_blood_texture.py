"""The Red sanctuary's pool of blood (block/sanctuary_blood.png): the red Deluge's own liquid, the
greyscale blood_still frames multiplied by the tint the game puts on the ember liquid
(EMBER_LIQUID_TINT 0x8C0610 in LanternRingClient), so the pool matches what a red Deluge pours.

    python3 tools/sanctuary_blood_texture.py
"""
import os
import shutil

from PIL import Image

BLOCK = os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "assets", "lanternring", "textures", "block")
TINT = (0x8C, 0x06, 0x10)


def main():
    src = Image.open(os.path.join(BLOCK, "blood_still.png")).convert("RGBA")
    out = Image.new("RGBA", src.size)
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = src.getpixel((x, y))
            out.putpixel((x, y), (r * TINT[0] // 255, g * TINT[1] // 255, b * TINT[2] // 255, 255))
    out.save(os.path.join(BLOCK, "sanctuary_blood.png"))
    shutil.copy(os.path.join(BLOCK, "blood_still.png.mcmeta"), os.path.join(BLOCK, "sanctuary_blood.png.mcmeta"))
    print("wrote sanctuary_blood.png")


if __name__ == "__main__":
    main()
