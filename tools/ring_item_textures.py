import math, random, sys
from PIL import Image
random.seed(7)
OUT = sys.argv[1]
T = (0, 0, 0, 0)
GOLD, GOLD_D, GOLD_L = (222, 178, 74, 255), (168, 124, 44, 255), (246, 214, 120, 255)
BLACK = (14, 18, 16, 255)
GREENS = [(10, 46, 36, 255), (16, 66, 50, 255), (24, 92, 66, 255), (36, 122, 84, 255)]
GRAYS = [(78, 78, 80, 255), (104, 104, 108, 255), (132, 132, 136, 255)]

def ring():
    im = Image.new("RGBA", (16, 16), T)
    px = im.load()
    def bar(y0, y1):
        for x in range(1, 15):
            px[x, y0] = GOLD_L if y0 < 8 else GOLD
            px[x, y1] = GOLD_D
        for y in range(y0 + 1, y1):
            px[1, y] = GOLD; px[14, y] = GOLD_D
            for x in range(2, 14):
                px[x, y] = random.choice(GREENS)
    bar(1, 4)
    bar(11, 14)
    # middle: band, frame, black housing, gold brackets, glowing orb
    for y in range(5, 11):
        px[0, y] = GRAYS[(y + 1) % 3]; px[15, y] = GRAYS[y % 2]
        px[1, y] = GOLD; px[14, y] = GOLD_D
        for x in range(2, 14):
            px[x, y] = BLACK
    for y in range(6, 10):
        px[3, y] = GOLD; px[12, y] = GOLD_D
    px[4, 5] = GOLD; px[4, 10] = GOLD_D; px[11, 5] = GOLD; px[11, 10] = GOLD_D
    cx, cy = 7.5, 7.5
    for y in range(5, 11):
        for x in range(5, 11):
            d = math.hypot(x - cx, (y - cy) * 1.15)
            if d > 3.3:
                continue
            g = max(0.0, 1 - d / 3.3)
            px[x, y] = (int(30 + 90 * g), int(110 + 145 * g), int(30 + 40 * g), 255)
    px[6, 6] = (190, 255, 170, 255)  # glint
    return im

def hard_light():
    im = Image.new("RGBA", (16, 16), T)
    px = im.load()
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            if edge:
                px[x, y] = (120, 255, 140, 220)
            else:
                a = 90 + random.randint(-10, 10)
                px[x, y] = (40, 230, 90, a)
    for i in range(2, 6):  # little sheen in one corner
        px[i, 2] = px[2, i] = (200, 255, 210, 170)
    return im

def battery_side():
    im = Image.new("RGBA", (16, 16), T)
    px = im.load()
    # used area: x 3..12, y 2..15 (model uv 3,2,13,16)
    for y in range(2, 16):
        for x in range(3, 13):
            px[x, y] = BLACK
    for x in range(3, 13):
        px[x, 2] = GOLD_L; px[x, 3] = GOLD; px[x, 14] = GOLD; px[x, 15] = GOLD_D
    for y in range(2, 16):
        px[3, y] = GOLD; px[12, y] = GOLD_D
    # glowing core with the bracket motif
    for y in range(5, 13):
        for x in range(5, 11):
            d = math.hypot(x - 7.5, (y - 8.5) * 0.8)
            g = max(0.0, 1 - d / 3.6)
            px[x, y] = (int(20 + 110 * g), int(90 + 165 * g), int(30 + 50 * g), 255)
    for y in range(6, 12):
        px[4, y] = GOLD; px[11, y] = GOLD_D
    return im

def battery_top():
    im = Image.new("RGBA", (16, 16), T)
    px = im.load()
    for y in range(3, 13):
        for x in range(3, 13):
            px[x, y] = GOLD if x in (3, 12) or y in (3, 12) else GOLD_D
    for y in range(6, 10):
        for x in range(6, 10):
            px[x, y] = (120, 255, 140, 255)
    return im

def icon():
    return ring().resize((128, 128), Image.NEAREST)

ring().save(f"{OUT}/textures/item/power_ring.png")
hard_light().save(f"{OUT}/textures/block/hard_light.png")
battery_side().save(f"{OUT}/textures/block/power_battery_side.png")
battery_top().save(f"{OUT}/textures/block/power_battery_top.png")
icon().save(f"{OUT}/icon.png")
ring().resize((256, 256), Image.NEAREST).save(sys.argv[2])
