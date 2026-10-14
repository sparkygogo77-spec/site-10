"""Flight trail light textures and the sonic boom (lead Blender chat, 2026-10-14). J picked T4 (thin ribbon + wind +
speed ring) and wants the trail "made out of light" in the ring's corps colour, plus a sonic boom with screen shake and a
sound when you hit fast flight.

    python tools/flight_fx_textures.py OUTDIR

Writes:
  flight_trail_light.png      64 x 1024: 16 frames of 64 x 64. A ribbon of light running left to right along the trail:
                              a hot white core, two braided filaments twisting round it and fine sparks, all scrolling
                              seamlessly (frame 16 wraps to frame 1). Drawn in the mod's construct green so CorpsTint
                              recolours it per corps like every other green effect.
  flight_trail_light_white.png the same in white/grey for a renderer that multiplies by the corps colour itself.
  sonic_boom_ring.png         64 x 512: 8 frames of 64 x 64. A ring of light bursting outward with a bright shock rim,
                              a faint inner haze and a few spokes; ends fully faded. Green, recoloured like the above.
  sonic_boom.ogg              mono 44.1 kHz, 1.6 s: the double crack of an N-wave (two sharp bangs 0.09 s apart), a
                              low thump under it and a rolling rumble tail.
  sonic_boom_close.ogg        first-person version, 0.9 s: tighter, louder crack with a fast whoosh into it.
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
TAU = math.tau
GREEN = np.array([60, 255, 110], float)        # construct green: CorpsTint maps this hue to each corps


def colourise(v, white=False):
    """Brightness 0..1.3 -> RGBA. Low values are the tinted glow, the top end goes to a white-hot core."""
    v = np.clip(v, 0, 1.3)
    base = np.array([235, 235, 235], float) if white else GREEN
    hot = np.clip((v - 0.75) / 0.55, 0, 1)[..., None]
    rgb = base * np.clip(v, 0, 1)[..., None] ** 0.8 * (1 - hot) + np.array([255, 255, 255]) * hot
    a = np.clip(255 * np.clip(v, 0, 1) ** 0.65, 0, 255)
    return np.concatenate([rgb, a[..., None]], -1).clip(0, 255).astype(np.uint8)


def trail(n=64, frames=16):
    y, x = np.mgrid[0:n, 0:n].astype(float)
    yc = (y - (n - 1) / 2) / (n / 2)                  # -1..1 across the ribbon
    rng = np.random.default_rng(218)
    sx, sy, sp = rng.uniform(0, n, 40), rng.normal(0, 0.35, 40), rng.uniform(0, 1, 40)
    out = []
    for f in range(frames):
        t = f / frames
        u = (x / n - t) % 1.0                         # scrolls one tile per loop -> seamless along the trail
        core = np.exp(-(yc / 0.09) ** 2) * (0.9 + 0.1 * np.cos(TAU * (3 * u)))
        glow = np.exp(-(yc / 0.38) ** 2) * 0.35
        fil = 0.0
        for k, ph in ((1, 0.0), (1, 0.5)):
            c = 0.42 * np.sin(TAU * (2 * u + ph)) * (0.8 + 0.2 * np.cos(TAU * u))
            fil = fil + np.exp(-((yc - c) / 0.06) ** 2) * (0.55 + 0.45 * np.cos(TAU * (4 * u + ph)) ** 2)
        sparks = np.zeros_like(x)
        for a, b, p in zip(sx, sy, sp):
            px = (a + n * t) % n
            tw = 0.5 + 0.5 * math.sin(TAU * (2 * t + p))
            d = np.hypot(np.minimum(abs(x - px), n - abs(x - px)), (yc - b) * n / 2)
            sparks += tw * np.exp(-(d / 0.8) ** 2)
        edge = np.clip(1.0 - np.abs(yc) ** 6, 0, 1)    # fades out before the tile's top and bottom
        out.append((core * 1.25 + glow + 0.75 * fil + 0.6 * sparks) * edge)
    return out


def boom(n=64, frames=8):
    y, x = np.mgrid[0:n, 0:n].astype(float)
    r = np.hypot(x - (n - 1) / 2, y - (n - 1) / 2) / (n / 2)
    ang = np.arctan2(y - n / 2, x - n / 2)
    out = []
    for f in range(frames):
        t = (f + 0.5) / frames
        R = 0.18 + 0.78 * (1 - (1 - t) ** 2)          # fast out, easing at the edge
        w = 0.05 + 0.06 * t
        fade = (1 - t) ** 1.3
        rim = np.exp(-((r - R) / w) ** 2)
        haze = np.exp(-((r - R * 0.7) / (0.35 * R + 0.05)) ** 2) * 0.25
        spokes = (0.5 + 0.5 * np.cos(12 * ang + 3 * t)) ** 8 * np.exp(-((r - R * 0.85) / 0.12) ** 2) * 0.5
        v = (1.25 * rim + haze + spokes) * fade * np.clip((1 - r) / 0.06, 0, 1)
        out.append(v)
    return out


def save_strip(frames, name, white=False):
    strip = np.concatenate([colourise(v, white) for v in frames], 0)
    Image.fromarray(strip, "RGBA").save(os.path.join(OUT, name), optimize=True)
    print(name, strip.shape)


save_strip(trail(), "flight_trail_light.png")
save_strip(trail(), "flight_trail_light_white.png", white=True)
save_strip(boom(), "sonic_boom_ring.png")

# ------------------------------------------------------------------ sounds
SR = 44100


def nwave(t, t0, dur, amp):
    """One N-wave: a sharp rise, a linear fall through zero, a sharp return (what makes the boom's 'crack')."""
    u = (t - t0) / dur
    s = np.where((u >= 0) & (u <= 1), 1 - 2 * u, 0.0)
    return amp * s


def write_ogg(sig, name):
    sig = sig / max(1e-9, np.abs(sig).max()) * 0.92
    wav = os.path.join(OUT, name.replace(".ogg", ".wav"))
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "5",
                    os.path.join(OUT, name)], check=True)
    os.remove(wav)
    print(name, round(len(sig) / SR, 2), "s")


def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


rng = np.random.default_rng(7)
t = np.arange(int(SR * 1.6)) / SR
crack = nwave(t, 0.02, 0.012, 1.0) + nwave(t, 0.11, 0.012, 0.9)
crack = crack + 0.25 * rng.normal(0, 1, t.size) * np.exp(-((t - 0.02) / 0.01) ** 2)
thump = np.sin(TAU * 42 * t) * np.exp(-np.maximum(t - 0.02, 0) / 0.18) * (t > 0.02) * 0.9
rumble = lowpass(rng.normal(0, 1, t.size), 0.004) * np.exp(-np.maximum(t - 0.1, 0) / 0.55) * (t > 0.08) * 9.0
write_ogg(crack + thump + rumble, "sonic_boom.ogg")

t = np.arange(int(SR * 0.9)) / SR
whoosh = lowpass(rng.normal(0, 1, t.size), 0.05) * np.clip(t / 0.12, 0, 1) ** 2 * (t < 0.14) * 3.0
crack = nwave(t, 0.14, 0.008, 1.2) + nwave(t, 0.2, 0.008, 1.0)
crack = crack + 0.35 * rng.normal(0, 1, t.size) * np.exp(-((t - 0.14) / 0.008) ** 2)
thump = np.sin(TAU * 55 * t) * np.exp(-np.maximum(t - 0.14, 0) / 0.12) * (t > 0.14)
tail = lowpass(rng.normal(0, 1, t.size), 0.01) * np.exp(-np.maximum(t - 0.2, 0) / 0.25) * (t > 0.18) * 5.0
write_ogg(whoosh + crack + thump + tail, "sonic_boom_close.ogg")
