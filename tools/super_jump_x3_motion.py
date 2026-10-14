"""X3 emerald power aura, motion takes for the super jump landing (J, 2026-10-14, on pass 90's T4: "T4 needs some
texture adjustment, the lines are very bright and most likely don't move enough for their level of detail, it looks
too still").

Round six's X3 only sways each point 4 px round a circle once every 8 s, so its fine strands barely move, and the
strands peak at the top of the emerald ramp (near white). Each take here keeps X3's strands but dims them and moves
them more. Same strip format as round six: 256 px = 4 blocks at 64 px a block, seamless, looping.

  XM1 drift     - the two strand layers glide across each other in opposite directions, one full tile per loop
                  (256 px in 9.6 s, about 0.4 blocks a second), lines at 60 % brightness
  XM2 currents  - the strands swirl in place: 14 px sway twice a loop (X3 had 4 px once), lines at 60 %
  XM3 pulse     - one layer drifts (a tile per loop), the other sways; lines at 45 % with pulses running along them

48 frames at frametime 4 = 9.6 s loop (more frames than X3's 32 so the faster motion stays smooth).

    python tools/super_jump_x3_motion.py OUTDIR   -> face_<key>.png (game strip + .mcmeta), face_<key>.gif,
                                                    tex_<key>.mp4 (20 fps, for Blender), compare.gif
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)
_argv, sys.argv = sys.argv, ["construct_designs6.py", os.path.join(OUT, "_r6")]
sys.path.insert(0, HERE)
import construct_designs6 as D6  # noqa: E402
sys.argv = _argv
D4, N, TAU = D6.D4, D6.N, D6.TAU
field, warp, ridged, blur, smooth, stars, sway, finish = (D6.field, D6.warp, D6.ridged, D6.blur, D6.smooth,
                                                         D6.stars, D6.sway, D6.finish)
NF, FT = 48, 4
_c = {}


def fields():
    if not _c:
        _c["f"] = (field(2, 7, 1.5, 633), field(3, 11, 1.4, 634), field(1, 3, 2.0, 635), field(1, 4, 2.0, 637))
    return _c["f"]


def x3(t):
    """Round six's X3, unchanged (T4 in pass 90)."""
    return D6.DESIGNS["X3"][1](t)


def take(key, t):
    f1, f2, f3, fp = fields()
    if key == "XM2":
        dx, dy = sway(t * 2, 14.0, 631)
        a1, b1, a2, b2 = dx, dy, -dy * 1.3, dx * 1.3
    elif key == "XM1":
        dx, dy = sway(t, 5.0, 631)
        a1, b1 = dx + N * t, dy + N * t             # layer 1 glides diagonally, one tile each way per loop
        a2, b2 = -dy * 1.3 - N * t, dx * 1.3        # layer 2 glides the other way along x
    else:                                           # XM3: only layer 1 drifts (one tile along x, the slowest that
        dx, dy = sway(t, 5.0, 631)                  # still loops); layer 2 just sways
        a1, b1 = dx + N * t, dy
        a2, b2 = -dy * 1.3, dx * 1.3
    s1 = warp(f1, a1, b1)
    s2 = warp(f2, a2, b2)
    l1 = ridged(s1, 4.5) ** 1.6 * 0.75
    l2 = ridged(s2, 6.0) ** 2 * 0.5
    strands = l1 + l2
    glow = blur(strands, 4.0) * 1.1
    cloud = np.clip(warp(f3, a1 * 0.5, b1 * 0.5) * 0.18 + 0.22, 0, 1) * smooth(0.0, 0.5, glow + 0.2)
    gain = 0.6
    if key == "XM3":
        gain = 0.45
        ph = warp(fp, a1, b1) * 3.0                  # pulses ride along layer 1 and run through it twice a loop
        pulse = (0.5 + 0.5 * np.cos(TAU * (2 * t) + ph * TAU)) ** 6
        strands = strands + l1 * pulse * 0.9
    v = strands * gain + 0.4 * glow * gain + 0.3 * cloud + 0.35 * stars(636, 50, t, 0.8)
    return finish(np.minimum(v * 0.85, 0.82))        # cap below the near-white top of the ramp


KEYS = ["XM1", "XM2", "XM3"]


def strip_of(fn):
    frames = [fn(f / NF) for f in range(NF)]
    rgba = [np.concatenate([D4.colour(v, "emerald"), a[..., None]], -1) for v, a in frames]
    return np.concatenate(rgba, 0).clip(0, 255).astype(np.uint8)


def on_dark(strip, i):
    return Image.alpha_composite(Image.new("RGBA", (N, N), (24, 28, 32, 255)),
                                 Image.fromarray(strip[i * N:(i + 1) * N], "RGBA")).convert("RGB")


def interp(strip, nf, ft):
    """The game's interpolated playback at 20 ticks a second: nf * ft opaque frames."""
    out = []
    for k in range(nf * ft):
        i, u = divmod(k, ft)
        a = np.asarray(on_dark(strip, i), float); b = np.asarray(on_dark(strip, (i + 1) % nf), float)
        out.append((a + (b - a) * u / ft).astype(np.uint8))
    return out


if __name__ == "__main__":
    sets = [("X3", strip_of(x3), 32, 5)] + [(k, strip_of(lambda t, k=k: take(k, t)), NF, FT) for k in KEYS]
    played = {}
    for key, strip, nf, ft in sets:
        im = Image.fromarray(strip, "RGBA")
        im.save(os.path.join(OUT, f"face_{key}.png"), optimize=True)
        open(os.path.join(OUT, f"face_{key}.png.mcmeta"), "w").write(
            '{"animation": {"interpolate": true, "frametime": %d}}' % ft)
        fr = interp(strip, nf, ft)
        played[key] = fr
        fr2 = [Image.fromarray(f) for f in fr[::2]]
        fr2[0].save(os.path.join(OUT, f"face_{key}.gif"), save_all=True, append_images=fr2[1:], duration=100, loop=0)
        p = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                            f"{N}x{N}", "-r", "20", "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                            os.path.join(OUT, f"tex_{key}.mp4")], input=b"".join(f.tobytes() for f in fr))
        print(key, "done", nf * ft / 20, "s", flush=True)
    # side by side: X3 (T4) | XM1 | XM2 | XM3, 2 x 2 blocks each, 10 s at 10 fps
    names = ["X3", "XM1", "XM2", "XM3"]
    n = 96
    pics = []
    for k in range(0, n * 2, 2):
        row = np.concatenate([np.pad(played[nm][k % len(played[nm])][:128, :128], ((0, 0), (4, 4), (0, 0)),
                                     constant_values=12) for nm in names], 1)
        pics.append(Image.fromarray(row).resize((row.shape[1] * 2, 256), Image.NEAREST))
    pics[0].save(os.path.join(OUT, "compare.gif"), save_all=True, append_images=pics[1:], duration=100, loop=0)
