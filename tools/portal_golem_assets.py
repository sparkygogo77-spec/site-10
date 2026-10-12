"""The Portal's swirl and the Loot Golem's Blockbench models:

    python tools/portal_golem_assets.py src/main/resources/assets/lanternring

Writes:
- textures/entity/portal_swirl.png  a round Rick and Morty style portal: lime rim, green spiral
  arms and a pale centre, transparent outside the circle. PortalFx spins it and squashes it into
  the portal's oval.
- bbmodel/loot_golem.bbmodel (+ texture)  a hard-light copper golem: big head with a nose and a
  lightning-rod antenna, short arms and legs, glowing eyes, seams and chest light.
- bbmodel/loot_golem_bag.bbmodel (+ texture)  the glowing sack on its back, which PortalFx grows
  as it fills up.

The Model class is borrowed from blockbench_models.py (only its top half runs, so the other
models aren't rewritten).
"""
import math, os, random, sys

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "blockbench_models.py")) as f:
    src = f.read().split("# ---- the Power Battery lantern")[0]
ns = {"__name__": "bb", "__file__": os.path.join(HERE, "blockbench_models.py")}
sys.argv = [sys.argv[0], A]
exec(compile(src, "blockbench_models.py", "exec"), ns)
Model, clamp = ns["Model"], ns["clamp"]
from PIL import Image

# ---- portal swirl ---------------------------------------------------------------------------
N = 256
img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
px = img.load()
for y in range(N):
    for x in range(N):
        u = (x + 0.5) / N * 2 - 1
        v = (y + 0.5) / N * 2 - 1
        r = math.hypot(u, v)
        if r > 1:
            continue
        a = math.atan2(v, u)
        # Four spiral arms winding in, plus a finer counter-swirl, so spinning reads as a vortex.
        arms = 0.5 + 0.5 * math.sin(4 * a + 9 * math.log(r + 0.06))
        fine = 0.5 + 0.5 * math.sin(9 * a - 14 * r + 1.7)
        swirl = 0.65 * arms ** 1.5 + 0.35 * fine ** 3
        core = max(0.0, 1 - r / 0.35) ** 2
        rim = max(0.0, 1 - abs(r - 0.93) / 0.07)
        k = min(1.0, 0.35 + 0.65 * swirl)
        cr = 40 + 120 * swirl + 150 * core
        cg = 150 + 105 * k
        cb = 40 + 90 * swirl + 140 * core
        if rim > 0:
            cr, cg, cb = cr + (190 - cr) * rim, cg + (255 - cg) * rim, cb + (120 - cb) * rim
        alpha = 0.62 + 0.3 * swirl + 0.25 * core
        alpha = max(alpha, rim)
        if r > 0.98:
            alpha *= max(0.0, (1 - r) / 0.02)
        px[x, y] = (clamp(cr), clamp(cg), clamp(cb), clamp(255 * min(1.0, alpha)))
os.makedirs(f"{A}/textures/entity", exist_ok=True)
img.save(f"{A}/textures/entity/portal_swirl.png")
print("portal_swirl: 256x256")

# ---- the Loot Golem -------------------------------------------------------------------------
grng = random.Random(23)
JADE_DEEP = (18, 92, 52)
JADE_MID = (38, 150, 84)
JADE_EDGE = (90, 215, 140)
MINT = (140, 255, 180)
MINT_HOT = (220, 255, 232)


def jade(face, w, h):
    """Mid jade with a lit top/left edge and a deep bottom/right edge, faint diagonal grain."""
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            c = JADE_MID
            if (x + 2 * y) % 7 == 0:
                c = tuple((a + b) // 2 for a, b in zip(JADE_MID, JADE_EDGE))
            if y == 0 or x == 0:
                c = JADE_EDGE
            elif (y == h - 1 or x == w - 1) and min(w, h) > 2:
                c = JADE_DEEP
            v = grng.randint(-6, 6)
            row.append(tuple(clamp(ch + v) for ch in c) + (255,))
        rows.append(row)
    return rows


def jade_dark(face, w, h):
    return [[tuple(clamp(ch + grng.randint(-5, 5)) for ch in JADE_DEEP) + (255,) for _ in range(w)] for _ in range(h)]


def glow(face, w, h):
    return [[(MINT_HOT if (x + y) % 4 == 0 else MINT) + (255,) for x in range(w)] for y in range(h)]


def hot(face, w, h):
    return [[MINT_HOT + (255,) for _ in range(w)] for _ in range(h)]


g = Model("loot_golem")
G = g.cube
# Legs and feet.
for s, n in ((-1, "l"), (1, "r")):
    G(f"leg_{n}", (s * 3.5 - 1.5, 0, -1.5), (s * 3.5 + 1.5, 4, 1.5), jade)
    G(f"arm_{n}", (s * 5 - 1, 3, -1), (s * 5 + 1, 10, 1), jade, rotation=[0, 0, s * 8], origin=[s * 5, 10, 0])
    G(f"glow_hand_{n}", (s * 5 - 1, 2, -1), (s * 5 + 1, 3, 1), glow, rotation=[0, 0, s * 8], origin=[s * 5, 10, 0])
G("body", (-4, 4, -3), (4, 11, 3), jade)
G("glow_chest", (-1.5, 6, -3.05), (1.5, 9, -3.05), hot)
G("glow_belt", (-4, 4, -3), (4, 5, 3), glow, inflate=0.05)
# The big head, the long nose, the eyes and the seam under the brow.
G("head", (-5, 11, -4), (5, 18, 4), jade)
G("glow_seam", (-5, 11, -4), (5, 12, 4), glow, inflate=0.05)
G("nose", (-1, 12, -6), (1, 15, -4), jade_dark)
for s, n in ((-1, "l"), (1, "r")):
    G(f"glow_eye_{n}", (s * 2.5 - 1, 14, -4.05), (s * 2.5 + 1, 16, -4.05), hot)
# The lightning-rod antenna with a glowing ball on top.
G("rod", (-0.5, 18, -0.5), (0.5, 22, 0.5), jade_dark)
G("glow_tip", (-1, 22, -1), (1, 24, 1), hot)
g.write()

b = Model("loot_golem_bag")
b.cube("glow_sack", (-3, -3, -2), (3, 3, 2), glow)
b.cube("glow_knot", (-1, 3, -1), (1, 4, 1), hot)
b.write()
