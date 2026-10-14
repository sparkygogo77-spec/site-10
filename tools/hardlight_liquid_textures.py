"""The Green Deluge liquid, brighter (J, 2026-10-13: "green deluge also isnt bright enough at all",
"the water looks like it may ripple too much"): python tools/hardlight_liquid_textures.py <assets_dir> [W1|W2|W3]

Today the liquid is vanilla water tinted green: water's textures are dark blue-grey and see-through, so
the tint comes out dim. These are near-white (the game's tint makes them green at full strength), more
opaque, with slow, low ripples and thin bright caustic lines so it reads as liquid light:
  W1 calm glow     alpha 205, soft ripples only
  W2 light lines   alpha 215, soft ripples + thin bright caustic lines (the pick I'd test first)
  W3 solid light   alpha 236, brighter base, lines, barely see-through
Writes textures/block/hardlight_still.png (16 px, 32 frames) and hardlight_flow.png (32 px, 32 frames)
with .mcmeta. Every frame tiles, and the animation loops (3 ticks a frame: 4.8 s a loop, half of
vanilla water's ripple speed and amplitude).
"""
import math, os, sys
from PIL import Image

A = sys.argv[1]
TAKE = sys.argv[2] if len(sys.argv) > 2 else "W2"
OUT = os.path.join(A, "textures", "block")
FRAMES = 32
TAU = 2 * math.pi
LOOK = {"W1": dict(alpha=205, base=0.80, amp=0.10, lines=0.0),
        "W2": dict(alpha=215, base=0.84, amp=0.08, lines=0.16),
        "W3": dict(alpha=236, base=0.90, amp=0.06, lines=0.10)}[TAKE]


def tex(size, frame, flow):
    im = Image.new("RGBA", (size, size))
    px = im.load()
    t = frame / FRAMES * TAU
    for y in range(size):
        for x in range(size):
            u, v = x / size * TAU, y / size * TAU
            if flow:
                h = 0.6 * math.sin(v - t + 0.5 * math.sin(u)) + 0.4 * math.sin(2 * v + u - 2 * t)
                c2 = math.sin(2 * v - 2 * t + math.sin(u + t))
            else:
                h = (math.sin(u + v + t) + math.sin(u - 2 * v - t) + 0.5 * math.sin(2 * u + v + 2 * t)) / 2.5
                c2 = math.sin(u + v + t + 0.8 * math.sin(u - v - t))
            caustic = max(0.0, 1 - abs(c2) * 2.5) ** 2   # soft bright lines where the waves cross
            k = LOOK["base"] + LOOK["amp"] * (h * 0.5 + 0.5) + LOOK["lines"] * caustic
            c = min(255, int(255 * k))
            px[x, y] = (c, c, c, min(255, LOOK["alpha"] + int(30 * caustic * (LOOK["lines"] > 0))))
    return im


def strip(size, flow):
    s = Image.new("RGBA", (size, size * FRAMES))
    for f in range(FRAMES):
        s.paste(tex(size, f, flow), (0, f * size))
    return s


if __name__ == "__main__":
    for name, size, flow in (("hardlight_still", 16, False), ("hardlight_flow", 32, True)):
        strip(size, flow).save(os.path.join(OUT, name + ".png"))
        with open(os.path.join(OUT, name + ".png.mcmeta"), "w") as fh:
            fh.write('{\n\t"animation": {\n\t\t"frametime": 3,\n\t\t"interpolate": true\n\t}\n}\n')
    print("wrote", TAKE)
