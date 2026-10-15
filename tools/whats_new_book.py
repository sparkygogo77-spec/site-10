"""The What's New book's 16x16 item texture: a dark green written book with the Lantern Ring emblem on the cover."""
from PIL import Image

OUT = "src/main/resources/assets/lanternring/textures/item/whats_new_book.png"
img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
px = img.load()
cover, edge, spine, pages, glow, gold = (20, 70, 40, 255), (10, 40, 22, 255), (12, 48, 28, 255), (230, 226, 205, 255), (90, 255, 140, 255), (210, 170, 60, 255)
# Cover (x 3..13, y 1..14), spine on the left, pages peeking on the right and bottom.
for y in range(1, 15):
    for x in range(3, 14):
        px[x, y] = cover
    px[2, y] = spine
    px[14, y] = pages if 2 <= y <= 14 else (0, 0, 0, 0)
for x in range(3, 14):
    px[x, 15] = pages
    px[x, 1] = edge
    px[x, 14] = edge
for y in range(1, 15):
    px[13, y] = edge
# Gold corner studs.
for x, y in ((4, 2), (12, 2), (4, 13), (12, 13)):
    px[x, y] = gold
# Lantern emblem: a ring with bars above and below (the Green Lantern mark).
ring = [(7, 6), (8, 6), (9, 6), (6, 7), (10, 7), (6, 8), (10, 8), (6, 9), (10, 9), (7, 10), (8, 10), (9, 10)]
for x, y in ring:
    px[x, y] = glow
for x in range(5, 12):
    px[x, 4] = glow
    px[x, 12] = glow
px[8, 8] = (200, 255, 210, 255)
img.save(OUT)
print("wrote", OUT)
