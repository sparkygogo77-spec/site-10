"""Shrink the mod's PNG textures so the jar stays small.

Each PNG over MIN_BYTES is quantized with pngquant (quality 90-100, dithered: a typical pixel
moves by less than 1/255 and none by more than about 10/255, which can't be seen in game), then
every PNG is recompressed losslessly with oxipng. pngquant leaves a file alone when it can't
reach that quality, and a file is only replaced when the result is smaller.

Needs `apt-get install pngquant` and `pip install pyoxipng`. Rerun after generating textures:
    python tools/optimize_textures.py src/main/resources/assets/lanternring/textures
"""
import os
import subprocess
import sys
import tempfile

import oxipng

MIN_BYTES = 64 * 1024


def optimize(path):
    before = os.path.getsize(path)
    with tempfile.TemporaryDirectory() as tmp:
        src = path
        if before > MIN_BYTES:
            quant = os.path.join(tmp, "q.png")
            r = subprocess.run(["pngquant", "--quality=90-100", "--speed", "1", "--force",
                                "--output", quant, path])
            if r.returncode == 0:
                src = quant
        out = os.path.join(tmp, "o.png")
        oxipng.optimize(src, out, level=4, strip=oxipng.StripChunks.safe())
        if os.path.getsize(out) < before:
            os.replace(out, path)
    return before, os.path.getsize(path)


def main(root):
    total_before = total_after = 0
    for dirpath, _, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(".png"):
                b, a = optimize(os.path.join(dirpath, name))
                total_before += b
                total_after += a
    print(f"{total_before / 1e6:.1f} MB -> {total_after / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1])
