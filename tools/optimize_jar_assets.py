"""Shrinks what the jar carries, losslessly. Run it before building a jar:

    python tools/optimize_jar_assets.py src/main/resources/assets/lanternring [--check]

1. bbmodel/*.bbmodel: drops each texture's embedded base64 copy ("source") and writes compact JSON.
   The mod never reads either: BbModel and BbRig load textures/entity/bb/<name>.png and read only resolution
   and elements. Blockbench still opens the files: it loads the texture from "relative_path".
   Measured on 2026-10-13: the bbmodels deflate to 2.7 MB in the jar before, 1.1 MB after.
2. textures/**/*.png: rewrites a PNG only when the new file is pixel-for-pixel identical and smaller:
   a palette where the image has 256 colours or fewer, then oxipng (pip install pyoxipng).
   Measured on the entity/bb textures: 9.8 MB -> 8.1 MB. Animated strips and .mcmeta files are untouched.

--check reports the savings without writing anything. Re-running it is harmless (already-slim files are skipped).
"""
import io, json, os, sys
from PIL import Image

A = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "src/main/resources/assets/lanternring"
CHECK = "--check" in sys.argv
try:
    import oxipng
except ImportError:
    oxipng = None
    print("pyoxipng not installed: PNGs only get the lossless palette step (pip install pyoxipng)")


def slim_bbmodels():
    before = after = 0
    d = os.path.join(A, "bbmodel")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".bbmodel"):
            continue
        p = os.path.join(d, f)
        raw = open(p, "rb").read()
        model = json.loads(raw)
        for t in model.get("textures", []):
            t.pop("source", None)
        out = json.dumps(model, separators=(",", ":")).encode()
        before += len(raw)
        if len(out) < len(raw):
            after += len(out)
            if not CHECK:
                open(p, "wb").write(out)
        else:
            after += len(raw)
    print(f"bbmodels: {before // 1024} KB -> {after // 1024} KB")


def same_pixels(a, b):
    return a.size == b.size and a.tobytes() == b.tobytes()


def slim_pngs():
    before = after = changed = 0
    for root, _, files in os.walk(os.path.join(A, "textures")):
        for f in files:
            if not f.endswith(".png"):
                continue
            p = os.path.join(root, f)
            raw = open(p, "rb").read()
            best = raw
            try:
                im = Image.open(io.BytesIO(raw)).convert("RGBA")
                cols = im.getcolors(256)
                if cols is not None:
                    q = im.quantize(len(cols), method=Image.Quantize.FASTOCTREE)
                    b = io.BytesIO(); q.save(b, "PNG"); cand = b.getvalue()
                    if same_pixels(Image.open(io.BytesIO(cand)).convert("RGBA"), im) and len(cand) < len(best):
                        best = cand
                if oxipng is not None:
                    cand = oxipng.optimize_from_memory(best, level=4)
                    if same_pixels(Image.open(io.BytesIO(cand)).convert("RGBA"), im) and len(cand) < len(best):
                        best = cand
            except Exception as e:
                print("skip", p, e)
            before += len(raw); after += len(best)
            if len(best) < len(raw):
                changed += 1
                if not CHECK:
                    open(p, "wb").write(best)
    print(f"textures: {before // 1024} KB -> {after // 1024} KB ({changed} files smaller)")


if __name__ == "__main__":
    slim_bbmodels()
    slim_pngs()
    if CHECK:
        print("(check only: nothing written)")
