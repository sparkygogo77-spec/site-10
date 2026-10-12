"""Lasso bubble and rope textures and its looping hum: python tools/lasso_assets.py <assets_dir>

  <assets_dir>/textures/entity/lasso_bubble.png  cracked jade glass with glowing cracks, mapped once
                                                  around the sphere (wraps left to right)
  <assets_dir>/textures/entity/lasso_rope.png    one smooth tube of hard light with soft bands along it
                                                  (u goes around the tube, v along it)
  <assets_dir>/sounds/lasso_hum.ogg              a 2-second seamless loop of humming hard light; the
                                                  game bends its pitch and volume with the rope's length

Needs Pillow, numpy and ffmpeg (with libvorbis).
"""
import math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image

OUT = sys.argv[1]
JADE_DARK = np.array([18, 92, 58, 150])
JADE = np.array([52, 170, 105, 175])
CRACK = np.array([150, 255, 190, 235])
HOT = np.array([235, 255, 240, 255])


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return a + (b - a) * t


def smooth_noise(w, h, cells, seed):
    rnd = np.random.default_rng(seed)
    small = Image.fromarray((rnd.random((h // cells, w // cells)) * 255).astype(np.uint8))
    # Tile 3x3 before scaling so the result wraps seamlessly, then cut out the middle.
    big = Image.new("L", (small.width * 3, small.height * 3))
    for i in range(3):
        for j in range(3):
            big.paste(small, (i * small.width, j * small.height))
    big = big.resize((w * 3, h * 3), Image.BICUBIC).crop((w, h, 2 * w, 2 * h))
    return np.asarray(big, dtype=float) / 255


def bubble(w=128, h=64):
    """Voronoi cracks on a torus, so the texture wraps around the sphere without a seam."""
    rnd = random.Random(11)
    pts = np.array([(rnd.random() * w, rnd.random() * h) for _ in range(46)])
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    ds = []
    for px, py in pts:
        dx = np.abs(xs - px); dx = np.minimum(dx, w - dx)
        dy = np.abs(ys - py); dy = np.minimum(dy, h - dy)
        ds.append(np.sqrt(dx * dx + dy * dy))
    ds = np.sort(np.stack(ds), axis=0)
    edge = (ds[1] - ds[0]) / 2                       # distance to the nearest crack
    cell = ds[0] / (ds[1] + 1e-6)                    # 0 at a cell's heart, 1 at its edge
    n = smooth_noise(w, h, 8, 3)
    fine = smooth_noise(w, h, 2, 4)
    c = mix(JADE_DARK, JADE, 0.35 + 0.5 * n + 0.15 * fine)
    c = mix(c, CRACK, 0.55 * cell ** 3)              # glow gathers towards the cracks
    halo = np.clip(1 - edge / 3.0, 0, 1) ** 2
    c = mix(c, CRACK, 0.7 * halo)
    c = mix(c, HOT, (edge < 0.75) * (0.55 + 0.45 * n))  # the cracks themselves, hot white-green
    # Hairline sub-cracks inside some cells.
    sub = np.abs(np.sin(xs * 0.9 + ys * 0.35 + n * 9)) < 0.05
    c = np.where((sub & (fine > 0.6))[..., None], mix(c, CRACK, np.full(edge.shape, 0.6)), c)
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGBA")


def rope(w=16, h=64):
    """One smooth tube of hard light: the same all the way round, with soft brighter bands along it
    (the game shades the edges, so it reads as a round tube, not twisted strands)."""
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    v = ys / h
    band = 0.5 + 0.5 * np.sin(v * 2 * math.pi)        # one soft band per tile, wraps along the rope
    c = mix(JADE + [0, 0, 0, 40], CRACK, 0.45 + 0.25 * band)
    c = mix(c, HOT, 0.12 * band ** 4)
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGBA")


def hum(seconds=2.0, rate=44100):
    """Every partial fits a whole number of cycles in the loop, so it repeats without a click."""
    t = np.arange(int(seconds * rate)) / rate
    sig = np.zeros_like(t)
    for f, a in [(110, 0.5), (110.5, 0.35), (220, 0.28), (330.5, 0.12), (441, 0.07), (661.5, 0.04)]:
        sig += a * np.sin(2 * np.pi * f * t)
    sig *= 0.82 + 0.18 * np.sin(2 * np.pi * 6 * t)       # a slow shimmer
    # Airy fizz: band-passed noise, filtered in the frequency domain so it wraps too.
    spec = np.fft.rfft(np.random.default_rng(1).standard_normal(len(t)))
    freqs = np.fft.rfftfreq(len(t), 1 / rate)
    spec *= np.exp(-((freqs - 2400) / 900) ** 2)
    fizz = np.fft.irfft(spec, len(t))
    sig += 0.25 * fizz / np.abs(fizz).max() * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    sig = sig / np.abs(sig).max() * 0.85
    return (sig * 32767).astype(np.int16), rate


def main():
    tex = os.path.join(OUT, "textures", "entity"); os.makedirs(tex, exist_ok=True)
    bubble().save(os.path.join(tex, "lasso_bubble.png"))
    rope().save(os.path.join(tex, "lasso_rope.png"))
    snd = os.path.join(OUT, "sounds"); os.makedirs(snd, exist_ok=True)
    data, rate = hum()
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "hum.wav")
        with wave.open(wav, "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(data.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "5",
                        os.path.join(snd, "lasso_hum.ogg")], check=True)


main()
