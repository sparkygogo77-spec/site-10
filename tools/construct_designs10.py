"""Construct designs, round ten (J, 2026-10-14, looking at the X3 power aura on a falling Anvil in game: "this texture
is good needs more detail and maybe less stressful on the game we need the code to maybe treat it like glass so it
doesnt need to be so dense"). Three detailed X3 takes, same strip format as round six (256 px = 4 blocks at 64 px a
block, 32 frames at frametime 5, seamless, looping):

  X3D1 glass aura    - X3's strands + a fine third layer of hair-thin wisps and sparks; the space between is fully
                       clear (alpha 0) and the light fully solid, so the game can draw it CUTOUT like glass: no
                       sorting, no stacked haze, no matter how many faces are behind each other
  X3D2 tinted aura   - the same detail over a faint emerald tint (alpha 28), for a see-through but glassy body
  X3D3 dense aura    - D1's detail at X3's density (strands brighter, more of them), cutout like D1

Today's X3 is 50-246 alpha everywhere (mean 104), so every face behind another adds a layer of green fog: a 10-block
column stacks ~20 faces. D1/D3 stack nothing where they are clear.

    python tools/construct_designs10.py OUTDIR [assets_dir]  -> face_<key>_emerald.png/.gif (+ the game strips with assets_dir)
"""
import os, sys, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
ASSETS = sys.argv[2] if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs6.py", os.path.join(OUT, "_r6")]
sys.path.insert(0, HERE)
import construct_designs6 as D6  # noqa: E402
sys.argv = _argv
D4, N, NF, FT = D6.D4, D6.N, D6.NF, D6.FT
field, warp, ridged, blur, smooth, stars, sway = D6.field, D6.warp, D6.ridged, D6.blur, D6.smooth, D6.stars, D6.sway
_c = {}


def layers(t):
    if not _c:
        _c["f"] = (field(2, 7, 1.5, 633), field(3, 11, 1.4, 634), field(1, 3, 2.0, 635), field(6, 26, 1.2, 1001), field(9, 40, 1.1, 1002))
    f1, f2, f3, f4, f5 = _c["f"]
    dx, dy = sway(t, 4.0, 631)
    s1 = warp(f1, dx, dy); s2 = warp(f2, -dy * 1.3, dx * 1.3)
    s4 = warp(f4, dx * 2.2, -dy * 2.2); s5 = warp(f5, -dx * 3, dy * 3)
    strands = ridged(s1, 4.5) ** 1.6 * 0.75 + ridged(s2, 6.0) ** 2 * 0.5
    wisps = ridged(s4, 7.0) ** 2.2 * 0.45 * smooth(0.02, 0.4, blur(strands, 6.0))   # fine hairs that follow the strands
    hair = ridged(s5, 9.0) ** 3 * 0.25
    glow = blur(strands, 4.0) * 1.1
    return strands, wisps, hair, glow, stars(636, 90, t, 0.7)


def take(key, t):
    strands, wisps, hair, glow, st = layers(t)
    if key == "X3D3":
        strands = strands * 1.35
    v = strands + wisps + hair + 0.35 * glow + 0.7 * st
    v = np.clip(v * (0.95 if key != "X3D3" else 1.05), 0, 1.25)
    tone = 0.1 + 0.9 * np.clip(v, 0, 1) ** 0.8
    solid = v > (0.16 if key != "X3D3" else 0.13)
    if key == "X3D2":
        a = np.where(solid, 255, 28)
    else:
        a = np.where(solid, 255, 0)
    return tone, a.astype(float)


KEYS = ["X3D1", "X3D2", "X3D3"]
if __name__ == "__main__":
    for key in KEYS:
        frames = [take(key, f / NF) for f in range(NF)]
        rgba = [np.concatenate([D4.colour(v, "emerald"), a[..., None]], -1) for v, a in frames]
        strip = np.concatenate(rgba, 0).clip(0, 255).astype(np.uint8)
        im = Image.fromarray(strip, "RGBA")
        im.save(os.path.join(OUT, f"face_{key}_emerald.png"), optimize=True)
        bg = [Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)), Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB") for i in range(NF)]
        bg[0].save(os.path.join(OUT, f"face_{key}_emerald.gif"), save_all=True, append_images=bg[1:], duration=FT * 50, loop=0)
        if ASSETS:
            p = os.path.join(ASSETS, "textures", "block", f"construct_ripples_green_{key.lower()}_emerald.png")
            im.save(p, optimize=True)
            open(p + ".mcmeta", "w").write('{"animation": {"interpolate": true, "frametime": %d}}' % FT)
        print(key, "done", flush=True)
