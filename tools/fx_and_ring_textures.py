import math, random, sys, os
from PIL import Image
random.seed(3)
A = sys.argv[1]
os.makedirs(f"{A}/textures/particle", exist_ok=True)
os.makedirs(f"{A}/textures/entity/ring", exist_ok=True)
os.makedirs(f"{A}/particles", exist_ok=True)

def save(im, path): im.save(f"{A}/{path}")

# --- particles: white so the code can tint them ---
m = Image.new("RGBA", (8, 8)); p = m.load()
for y in range(8):
    for x in range(8):
        d = math.hypot(x - 3.5, y - 3.5) / 3.6
        a = max(0.0, 1 - d) ** 1.4
        c = int(200 + 55 * max(0, 1 - d * 1.6))
        p[x, y] = (c, c, c, int(255 * a))
save(m, "textures/particle/glow_mote.png")

d = Image.new("RGBA", (8, 8)); p = d.load()
shape = ["...##...", "...##...", "..####..", "..####..", ".######.", ".######.", "..####..", "........"]
for y, row in enumerate(shape):
    for x, ch in enumerate(row):
        if ch == "#":
            edge = x in (1, 6) or y == 6 or (y < 4 and x in (2, 5))
            p[x, y] = (210, 210, 210, 200) if edge else (255, 255, 255, 255)
p[3, 3] = p[3, 4] = (255, 255, 255, 255)
save(d, "textures/particle/glow_drip.png")

s = Image.new("RGBA", (8, 8)); p = s.load()
for y in range(1, 7):
    for x in range(1, 7):
        edge = x in (1, 6) or y in (1, 6)
        p[x, y] = (255, 255, 255, 255) if edge else (255, 255, 255, 90)
save(s, "textures/particle/glow_shard.png")

k = Image.new("RGBA", (8, 8)); p = k.load()
for i in range(8):
    a = 255 if i in (3, 4) else 150 if i in (2, 5) else 60
    p[i, 3] = p[i, 4] = p[3, i] = p[4, i] = (255, 255, 255, a)
for x, y in [(3, 3), (3, 4), (4, 3), (4, 4)]:
    p[x, y] = (255, 255, 255, 255)
save(k, "textures/particle/glow_spark.png")

# pane: flat, faint glass. The particle shader discards pixels under 10% alpha, so a feathered
# edge would turn into dots; panes tile edge to edge instead.
w = Image.new("RGBA", (16, 16), (255, 255, 255, 46))
save(w, "textures/particle/glow_pane.png")

# halo: a big, faint disc drawn behind lingering light so it reads as a glow. Its alpha only
# falls to about half at the rim, so the 10% discard leaves a smooth circle rather than dots.
h = Image.new("RGBA", (16, 16)); p = h.load()
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5) / 8
        if d < 1:
            p[x, y] = (255, 255, 255, int(255 * (1 - 0.45 * d * d)))
save(h, "textures/particle/glow_halo.png")

# pane edge: the bright seam where the dome cuts into a block
e = Image.new("RGBA", (16, 16)); p = e.load()
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5) / 8
        p[x, y] = (255, 255, 255, int(235 * max(0.0, 1 - d) ** 1.5))
save(e, "textures/particle/glow_pane_edge.png")

for n in ["glow_mote", "glow_drip", "glow_shard", "glow_spark", "glow_halo"]:
    open(f"{A}/particles/{n}.json", "w").write('{\n\t"textures": ["lanternring:%s"]\n}\n' % n)
# the pane particle switches to its second sprite while it is a seam
open(f"{A}/particles/glow_pane.json", "w").write('{\n\t"textures": ["lanternring:glow_pane", "lanternring:glow_pane_edge"]\n}\n')

# --- ring materials, 16x16 each ---
def mat(name, base, var, hi=None):
    im = Image.new("RGBA", (16, 16)); p = im.load()
    for y in range(16):
        for x in range(16):
            v = random.randint(-var, var)
            r, g, b = (max(0, min(255, c + v)) for c in base)
            p[x, y] = (r, g, b, 255)
    if hi:
        for i in range(0, 16, 4):
            p[i, i] = hi
    im.save(f"{A}/textures/entity/ring/{name}.png")

mat("gold", (222, 176, 66), 14, (252, 226, 128, 255))
mat("band", (150, 154, 160), 12, (196, 200, 206, 255))   # silver-grey band
mat("dark", (14, 22, 18), 6)                              # black housing
mat("gem", (30, 150, 60), 22, (120, 255, 140, 255))       # emerald

g = Image.new("RGBA", (16, 16)); p = g.load()               # emissive gem layer
for y in range(16):
    for x in range(16):
        v = random.randint(0, 40)
        p[x, y] = (40 + v, 230 + v // 3, 80 + v, 255)
g.save(f"{A}/textures/entity/ring/gem_glow.png")

h = Image.new("RGBA", (16, 16)); p = h.load()               # faint glow shell
for y in range(16):
    for x in range(16):
        p[x, y] = (40, 255, 90, 60)
h.save(f"{A}/textures/entity/ring/halo.png")

# --- Shockwave dome glass: near-white so the code tints it jade; faint soft cloudiness so the
# glass isn't perfectly flat. Wraps once around the dome (u) and runs base to top (v). ---
rnd = random.Random(26)
W, H = 64, 32
g = Image.new("RGBA", (W, H)); p = g.load()
waves = [(rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), k) for k in (1, 2, 3, 5)]
for y in range(H):
    for x in range(W):
        n = sum(math.sin(2 * math.pi * k * x / W + a) * math.sin(math.pi * k * y / H + b) / k for a, b, k in waves)
        c = int(max(0, min(255, 236 + 14 * n)))
        p[x, y] = (c, c, c, 255)
save(g, "textures/entity/shockwave_glass.png")
