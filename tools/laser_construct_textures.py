"""Ring laser textures for Blender passes 834 (L2) and 830 (T2-T6), drawn by LaserBeams.

White intensity textures (the game tints them with the corps colour and draws them additive), made from J's construct
strips already in the mod, so the beam wears the same patterns as his constructs:
  laser_glow_hex      L2 construct lance: frame 0 of H1 hex, mapped 0.3..1.5, times the glow's bright-middle falloff
                      ((1 - |2u - 1|)^2.2 x 0.85), one tile every half block (834_laser.update.py, pattern "lib")
  laser_tube_brick    T2 sheath: BR1 bricks, every frame (24), wrapped round the tube
  laser_tube_weave    T3 sheath: W1 weave (24 frames)
  laser_tube_ripple   T4 sheath: X3D1 ripples (32 frames)
  laser_tube_r2       T6 sheath: R2 (32 frames)
  laser_glow_soft     T4/T5 "game glow": a plain strip, (1 - |2u - 1|)^2.5 x 0.7 (830_ring_beam3.update.py, ribbon_mat)
T5's hex sheath reuses laser_tube_hex (pass 836 C3). Each frame is 32x32, frames stacked down.

Run from the repo root: python3 tools/laser_construct_textures.py
"""
import os

from PIL import Image

BLOCK = "src/main/resources/assets/lanternring/textures/block"
OUT = "src/main/resources/assets/lanternring/textures/misc/laser"
S = 32


def frames(name):
    im = Image.open(os.path.join(BLOCK, f"construct_ripples_{name}.png")).convert("RGBA")
    w, h = im.size
    return [im.crop((0, k * w, w, (k + 1) * w)).resize((S, S), Image.BOX) for k in range(h // w)]


def intensity(fr):
    """How bright each texel is, whatever its colour: the brightest channel times its alpha, 0..1."""
    px = fr.load()
    return [[max(px[x, y][:3]) * px[x, y][3] / 255 / 255 for x in range(S)] for y in range(S)]


def normalised(frs):
    vals = [intensity(f) for f in frs]
    flat = sorted(v for fr in vals for row in fr for v in row)
    lo, hi = flat[int(0.01 * len(flat))], flat[int(0.99 * len(flat))]
    return [[[min(1.0, max(0.0, (v - lo) / max(1e-6, hi - lo))) for v in row] for row in fr] for fr in vals]


def save(name, rows_per_frame):
    n = len(rows_per_frame)
    out = Image.new("LA", (S, S * n))
    px = out.load()
    for k, fr in enumerate(rows_per_frame):
        for y in range(S):
            for x in range(S):
                v = max(0, min(255, round(fr[y][x] * 255)))
                px[x, k * S + y] = (v, v)
    out.save(os.path.join(OUT, name + ".png"), optimize=True)
    print(name, out.size)


def fall(x, p):
    u = (x + 0.5) / S
    return (1 - abs(2 * u - 1)) ** p


def tube(name, src):
    # As laser_tube_hex: never fully dark (so the sheath reads as a tube), the pattern at about half brightness.
    save(name, [[[(32 + 95 * v) / 255 for v in row] for row in fr] for fr in normalised(frames(src))])


if __name__ == "__main__":
    hex0 = normalised(frames("h1_neon"))[0]
    save("laser_glow_hex", [[[0.8 * min(0.99, 0.85 * fall(x, 2.2) * (0.3 + 1.2 * hex0[y][x])) for x in range(S)] for y in range(S)]])
    save("laser_glow_soft", [[[0.7 * fall(x, 2.5) for x in range(S)] for _ in range(S)]])
    tube("laser_tube_brick", "br1_neon")
    tube("laser_tube_weave", "w1_neon")
    tube("laser_tube_ripple", "green_x3d1_emerald")
    tube("laser_tube_r2", "red_r2")
