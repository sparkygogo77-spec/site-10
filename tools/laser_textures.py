"""Textures for the ring laser test picks (Blender pass 836: H3, N1, N2, N3, P1, C1, C2, C3).

    python3 tools/laser_textures.py            # writes docs/handoff/2026-10-15-laser-test-picks/textures/

Every texture is drawn on a ribbon quad that turns to the camera: u runs ACROSS the beam (0..1, bright in the middle),
v runs ALONG it, 32 px a block, and tiles in v so the game can scroll it toward the target (v -= flow * ticks).
Colour is white/grey (RGB = alpha = intensity): tint it with the corps colour per vertex (green (8, 255, 56)) so the
glow stays saturated, never white. Draw additively (like energySwirl) or as translucent emissive under a shader pack.
The patterns copy the Blender shaders (laser_kit.py in pass 834/836): falloff (1 - |2u - 1|)^p times a pattern.
"""
import json
import math
import os

import numpy as np
from PIL import Image

OUT = "docs/handoff/2026-10-15-laser-test-picks/textures"
LIB = "docs/texture_library/green"
W = 32            # px across
PPB = 32          # px a block along the beam


def falloff(p, w=W):
    u = (np.arange(w) + 0.5) / w
    return (1 - np.abs(2 * u - 1)) ** p if p > 0 else np.ones(w)


def periodic_noise(h, w, gy, gx, rng, octaves=3):
    """Value noise, periodic in both axes (gy x gx cells at the first octave), 0..1."""
    out = np.zeros((h, w)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        cy, cx = gy * 2 ** o, gx * 2 ** o
        g = rng.random((cy, cx))
        y = np.arange(h) / h * cy; x = np.arange(w) / w * cx
        y0 = np.floor(y).astype(int); x0 = np.floor(x).astype(int)
        fy = (y - y0)[:, None]; fx = (x - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0 % cy][:, x0 % cx]; b = g[y0 % cy][:, (x0 + 1) % cx]
        c = g[(y0 + 1) % cy][:, x0 % cx]; d = g[(y0 + 1) % cy][:, (x0 + 1) % cx]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        tot += amp; amp *= 0.5
    return out / tot


def save(name, a, frames=None, frametime=None):
    a = np.clip(a, 0, 1)
    v = (a * 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([v, v, v, v]), "RGBA")
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, name + ".png"))
    if frames:
        json.dump({"animation": {"frametime": frametime, "interpolate": True}}, open(os.path.join(OUT, name + ".png.mcmeta"), "w"))
    print(name, im.size, "frames" if frames else "")


def streak(name, streak_len, streak_x, p=2.2, alpha=0.85, seed=0):
    """Noise drawn out along the beam: Blender used noise(u * streak_x, v * streak_len). One tile = cells / streak_len
    blocks, so it repeats cleanly."""
    cells = 3
    blocks = max(2, int(round(cells / streak_len)))
    h = blocks * PPB
    n = periodic_noise(h, W, cells, max(2, int(round(streak_x))), np.random.default_rng(seed))
    pat = np.clip((n - 0.35) / 0.35, 0, 1) * 0.65 + 0.35
    save(name, falloff(p)[None, :] * alpha * pat)
    return blocks


def pulse(name, pulse_len, cut, p=2.2, alpha=0.85):
    h = int(round(pulse_len * PPB))
    v = (np.arange(h) + 0.5) / PPB
    s = np.sin(2 * math.pi * v / pulse_len)
    pat = np.clip((s - cut) / (1 - cut), 0, 1) * (1.4 - 0.45) + 0.45
    save(name, falloff(p)[None, :] * alpha * pat[:, None] / 1.4)


def construct(name, look, p, alpha):
    """J's construct strip across the glow, two tiles a block along it, every frame kept (animated like the blocks)."""
    im = Image.open(os.path.join(LIB, look, f"construct_{look}_green.png")).convert("RGBA")
    w, h = im.size; n = h // w
    frames = []
    for k in range(n):
        fr = np.asarray(im.crop((0, k * w, w, (k + 1) * w)).resize((W, PPB // 2), Image.NEAREST), float) / 255
        lum = 0.3 * fr[..., 0] + 0.59 * fr[..., 1] + 0.11 * fr[..., 2]
        lum = lum / max(lum.max(), 1e-6)
        pat = 0.3 + 1.2 * lum
        tile = np.vstack([pat, pat])                       # 2 tiles = 1 block
        frames.append(np.clip(falloff(p)[None, :] * alpha * tile / 1.5, 0, 0.99))
    meta = json.load(open(os.path.join(LIB, look, f"construct_{look}_green.png.mcmeta")))
    save(name, np.vstack(frames), frames=n, frametime=meta.get("animation", {}).get("frametime", 4))


def main():
    save("laser_core", falloff(0.6)[None, :].repeat(PPB, 0))                 # solid core, soft only at the very edge
    save("laser_haze", (falloff(3.0) * 0.26)[None, :].repeat(PPB, 0))
    save("laser_strand", falloff(0.8)[None, :].repeat(PPB, 0))               # H3 strand core
    save("laser_strand_sheath", (falloff(2.0) * 0.3)[None, :].repeat(PPB, 0))
    b = {}
    b["laser_glow_streak"] = streak("laser_glow_streak", 0.35, 9.0, seed=1)          # H3, C3 outer glow
    b["laser_glow_needle"] = streak("laser_glow_needle", 0.12, 9.0, seed=2)          # N1
    b["laser_glow_layer_inner"] = streak("laser_glow_layer_inner", 0.35, 9.0, seed=3)  # N2 inner
    b["laser_glow_layer_outer"] = streak("laser_glow_layer_outer", 0.5, 9.0, alpha=0.6, seed=4)  # N2 outer
    b["laser_glow_crackle"] = streak("laser_glow_crackle", 0.9, 22.0, seed=5)         # N3
    pulse("laser_glow_pulse", 1.0, 0.3)                                               # P1
    construct("laser_glow_weave", "w1", 1.2, 0.95)                                    # C1
    construct("laser_glow_brick", "br1", 1.2, 0.95)                                   # C2
    construct("laser_tube_hex", "h1", 0.0, 0.5)                                       # C3 tube (no falloff: it wraps round)
    yy, xx = np.mgrid[0:64, 0:64]
    r = np.hypot(xx - 31.5, yy - 31.5) / 32
    save("laser_flare", np.clip(1 - r, 0, 1) ** 2.6 * 0.8)
    json.dump(b, open(os.path.join(OUT, "tile_blocks.json"), "w"), indent=1)
    print("tile lengths (blocks):", b)


if __name__ == "__main__":
    main()
