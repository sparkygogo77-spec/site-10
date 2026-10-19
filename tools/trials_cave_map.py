"""Side-section concept map of the Dread Warren (Pillow only). Usage: python cave_map.py OUT.png"""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 1000
random.seed(7)
img = Image.new("RGB", (W, H), (10, 9, 6))
d = ImageDraw.Draw(img)
try:
    F = ImageFont.truetype("arial.ttf", 22); FS = ImageFont.truetype("arial.ttf", 16); FB = ImageFont.truetype("arialbd.ttf", 34)
except OSError:
    F = FS = FB = ImageFont.load_default()

# sky / surface
d.rectangle([0, 0, W, 120], fill=(22, 24, 30))
d.rectangle([0, 120, W, 140], fill=(60, 62, 55))  # dead grass
for x in range(40, W, 70):  # dead trees
    if 520 < x < 700: continue
    d.line([x, 120, x, 70], fill=(45, 42, 38), width=5)
    d.line([x, 85, x - 14, 70], fill=(45, 42, 38), width=3)

# rock body with yellow veins
d.rectangle([0, 140, W, H], fill=(24, 22, 18))
for _ in range(90):
    x, y = random.randint(0, W), random.randint(150, H)
    pts = [(x, y)]
    for _ in range(5):
        x += random.randint(-30, 30); y += random.randint(-20, 20); pts.append((x, y))
    d.line(pts, fill=(70, 58, 18), width=1)

CAVE = (6, 5, 4)
def room(poly): d.polygon(poly, fill=CAVE)
# Z1 maw shaft
room([(560, 120), (690, 120), (660, 330), (590, 330)])
# Z2 gallery (tall)
room([(590, 300), (900, 280), (960, 330), (950, 520), (600, 520)])
# Z3 hatchery (low wide)
room([(700, 510), (1200, 500), (1220, 580), (690, 590)])
# Z4 bridge chasm
room([(1150, 560), (1500, 560), (1520, 700), (1140, 700)])
room([(1260, 700), (1400, 700), (1380, 960), (1280, 960)])  # abyss
# Z5 hollow
room([(1050, 690), (1180, 690), (1180, 760), (1050, 760)])
# Z6 brood heart dome
d.pieslice([300, 620, 1020, 1100], 180, 360, fill=CAVE)
room([(300, 860), (1020, 860), (1020, 900), (300, 900)])
room([(1010, 730), (1060, 730), (1060, 800), (1000, 800)])  # passage hollow -> arena
# false caves
room([(60, 135), (110, 135), (230, 230), (300, 250), (300, 285), (210, 275), (90, 170)])
room([(1350, 135), (1400, 135), (1450, 220), (1520, 260), (1510, 290), (1420, 255)])
for cx, cy in [(300, 268), (1515, 275)]:  # collapsed throats
    for _ in range(14):
        rx, ry = cx + random.randint(-14, 14), cy + random.randint(-14, 14)
        d.rectangle([rx, ry, rx + 7, ry + 7], fill=(70, 66, 58))
    d.line([cx - 16, cy - 16, cx + 16, cy + 16], fill=(230, 190, 40), width=3)
    d.line([cx - 16, cy + 16, cx + 16, cy - 16], fill=(230, 190, 40), width=3)

glow = Image.new("RGB", (W, H), (0, 0, 0))
g = ImageDraw.Draw(glow)
Y, YD = (255, 210, 26), (150, 115, 10)
# silk strands
for x0 in range(610, 940, 40):
    g.line([x0, 300, x0 + random.randint(-30, 30), 515], fill=YD, width=2)
for _ in range(10):  # dome web
    a = random.uniform(math.pi * 1.05, math.pi * 1.95)
    g.line([660, 860, 660 + 360 * math.cos(a), 860 + 240 * math.sin(a)], fill=YD, width=2)
for r in (90, 160, 230):
    g.arc([660 - r * 1.5, 860 - r, 660 + r * 1.5, 860 + r], 190, 350, fill=YD, width=2)
# bridges
for yb in (600, 640):
    g.line([(1150, yb)] + [(1150 + i * 37, yb + 18 * math.sin(i / 10 * math.pi)) for i in range(1, 11)], fill=Y, width=3)
# egg sacs
for x in range(730, 1180, 55):
    g.ellipse([x, 515, x + 22, 545], outline=Y, width=2)
    g.ellipse([x + 6, 523, x + 16, 537], fill=YD)
# spiders (small x-legged marks) on walls / ceiling
def spider(x, y, s=1.0, c=Y):
    g.ellipse([x - 6 * s, y - 4 * s, x + 6 * s, y + 4 * s], fill=c)
    for k in range(4):
        for sgn in (-1, 1):
            ang = (k - 1.5) * 0.45
            kx, ky = x + sgn * 10 * s * math.cos(ang), y - 6 * s
            g.line([x, y, kx, ky, x + sgn * 16 * s * math.cos(ang), y + 6 * s * math.sin(ang) + 4 * s], fill=c, width=2)
for p in [(600, 200), (650, 260), (700, 296), (820, 292), (930, 400), (1240, 575), (1480, 600), (400, 760), (920, 760)]:
    spider(*p)
g.line([760, 284, 760, 420], fill=YD, width=1); spider(760, 425)   # ceiling drop on a thread
# mother + heart crystal
g.line([660, 640, 660, 700], fill=Y, width=2)
g.ellipse([620, 700, 700, 770], fill=(200, 160, 20)); spider(660, 712, 3.2)
g.polygon([(660, 830), (680, 860), (660, 890), (640, 860)], fill=Y)
# brazier
g.ellipse([1100, 735, 1116, 751], fill=(255, 140, 40))
blur = glow.filter(ImageFilter.GaussianBlur(6))
from PIL import ImageChops
img = Image.composite(glow, img, glow.convert("L").point(lambda v: 255 if v else 0))
img = ImageChops.add(img, blur)

# player's green ring light in the gallery
light = Image.new("RGB", (W, H), (0, 0, 0))
ImageDraw.Draw(light).ellipse([630, 380, 790, 540], fill=(30, 140, 50))
img = ImageChops.add(img, light.filter(ImageFilter.GaussianBlur(40)))
d = ImageDraw.Draw(img)
d.ellipse([700, 494, 714, 520], fill=(200, 200, 200)); d.ellipse([710, 496, 718, 504], fill=(60, 255, 90))

def label(x, y, t, sub=""):
    d.text((x, y), t, fill=(255, 225, 120), font=F)
    if sub: d.text((x, y + 25), sub, fill=(190, 180, 150), font=FS)
label(700, 160, "Z1 THE MAW", "the one true entrance; watchers on walls")
label(300, 320, "Z2 WEAVE GALLERY", "ceiling drops")
label(720, 600, "Z3 HATCHERY", "Dread hatches eggs")
label(1230, 710, "Z4 BRIDGE OF THREADS", "packs + weavers over the abyss")
label(1050, 775, "Z5 HOLLOW", "brazier checkpoint")
label(330, 905, "Z6 BROOD HEART", "the Matron in the web dome; heart-crystal below")
label(110, 290, "false cave A", "collapsed throat")
label(1300, 300, "false cave B", "collapsed throat")
d.text((24, 18), "THE DREAD WARREN  (side section, concept)", fill=(255, 210, 26), font=FB)
d.text((24, 60), "yellow = fear construct (silk, eggs, brood)     green = your ring light, the only steady light", fill=(200, 200, 200), font=FS)
img.save(sys.argv[1])
print("saved", sys.argv[1])
