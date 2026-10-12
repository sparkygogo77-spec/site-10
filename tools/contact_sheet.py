import sys, glob
from PIL import Image, ImageDraw
d, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3])
crop = sys.argv[4] if len(sys.argv) > 4 else None
fs = sorted(glob.glob(d + "/*.png"))
ims = [Image.open(f).convert("RGB") for f in fs]
if crop:
    x0, y0, x1, y1 = map(int, crop.split(","))
    ims = [im.crop((x0, y0, x1, y1)) for im in ims]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows))
dr = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(fs, ims)):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    dr.text(((i % cols) * w + 6, (i // cols) * h + 4), f.split("/")[-1][5:-4], fill=(255, 255, 0))
scale = min(1.0, 1600 / sheet.width)
sheet.resize((int(sheet.width * scale), int(sheet.height * scale))).save(out)
