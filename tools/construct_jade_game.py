"""Game textures for the jade construct packs (J's round-three picks R1, R3, R4 with T1 smoke):
    python tools/construct_jade_game.py <out textures/block dir>

Writes:
- construct_jade.png: the plain cloudy jade (style J from construct_face_options.py) in its six
  outline variants side by side, 3 x 2 tiles of 128 px: plain, edge, corner / strip, three, frame.
  construct_jade_s.png is its LabPBR specular map (tools/construct_jade_specular.py).
  The game model (FlowConstructModel) picks the tile and turns it by the block's neighbours.
- construct_ripples_r1/r3/r4.png (+ .mcmeta): moving ripples over the faces, a looping animation
  that spans 4 x 4 blocks (64 px per block), sliced by world position in game so it runs across
  block edges. Made by animated line-integral convolution: noise smeared along a flowing direction
  field turns into streaks, and a travelling window along each streak makes them move; every
  motion completes whole cycles over the loop, so the last frame runs into the first.
    r1 mixed sizes   r3 large and slow   r4 mixed sizes, pulsing
- construct_smoke.png (+ .mcmeta): the T1 smoke skin, thin soft wisps, looping, 4 x 4 blocks.
"""
import math, os, sys
import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the jade sheet ---------------------------------------------------------------------------------
import subprocess, tempfile
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable, os.path.join(HERE, "construct_face_options.py"), tmp, "128"], check=True,
               stdout=subprocess.DEVNULL)
order = ["plain", "edge", "corner", "strip", "three", "frame"]
sheet = Image.new("RGBA", (128 * 3, 128 * 2))
for k, name in enumerate(order):
    sheet.paste(Image.open(os.path.join(tmp, f"J_{name}.png")), ((k % 3) * 128, (k // 3) * 128))
# in game the sky and terrain show through far more than Blender's dark room: keep the jade denser
px = np.asarray(sheet).astype(float)
px[..., 3] = np.clip(px[..., 3] * 1.55, 0, 255)
Image.fromarray(px.astype(np.uint8), "RGBA").save(os.path.join(OUT, "construct_jade.png"))
# and its LabPBR specular map, so shader packs make the jade shine
subprocess.run([sys.executable, os.path.join(HERE, "construct_jade_specular.py"), os.path.join(OUT, "construct_jade.png")], check=True)

# ---- shared: periodic fields on a torus -------------------------------------------------------------
N = 256                       # 4 blocks x 64 px
FRAMES = 24
rng = np.random.default_rng(4242)
kx = np.fft.fftfreq(N, 1.0 / N)
KX, KY = np.meshgrid(kx, kx, indexing="xy")
K = np.hypot(KX, KY)


def field(kmin, kmax, beta, seed):
    r = np.random.default_rng(seed)
    amp = np.where((K >= kmin) & (K <= kmax), np.maximum(K, 1e-9) ** -beta, 0.0)
    spec = amp * np.exp(1j * r.uniform(0, 2 * np.pi, K.shape))
    f = np.real(np.fft.ifft2(spec))
    return (f - f.mean()) / (f.std() + 1e-9)


def blurred_noise(grain, seed):
    """White noise blurred to blobs about `grain` px, wrapping."""
    r = np.random.default_rng(seed)
    w = r.random((N, N))
    g = np.exp(-(K / (N / (grain * 2.5))) ** 2)
    f = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    return (f - f.mean()) / (f.std() + 1e-9)


def sample(f, x, y):
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    tx, ty = x - x0, y - y0
    x0 %= N; y0 %= N; x1 = (x0 + 1) % N; y1 = (y0 + 1) % N
    return (f[y0, x0] * (1 - tx) + f[y0, x1] * tx) * (1 - ty) + (f[y1, x0] * (1 - tx) + f[y1, x1] * tx) * ty


yy, xx = np.mgrid[0:N, 0:N].astype(float)
theta = field(1, 4, 1.6, 7) * 2.4          # the flow direction, changing from area to area
DX, DY = np.cos(theta), np.sin(theta)


def lic_samples(noise, steps):
    """Noise read along each pixel's streamline, steps each way: array [2*steps+1, N, N]."""
    out = [noise]
    for sgn in (1, -1):
        x, y = xx.copy(), yy.copy()
        seq = []
        for _ in range(steps):
            dx, dy = sample(DX, x, y), sample(DY, x, y)
            x, y = x + sgn * dx, y + sgn * dy
            seq.append(sample(noise, x, y))
        out = (seq[::-1] + out) if sgn == -1 else (out + seq)
    return np.stack(out)


def ripples(layers, pulse=0.0):
    """layers: (grain px, steps, wavelength px, cycles per loop, weight). Returns RGBA frames."""
    frames = np.zeros((FRAMES, N, N))
    for li, (grain, steps, lam, cycles, weight) in enumerate(layers):
        S = lic_samples(blurred_noise(grain, 100 + li), steps)
        s = np.arange(-steps, steps + 1)[:, None, None]
        for f in range(FRAMES):
            t = f / FRAMES
            # a travelling window along the streamline: the streaks slide along their direction
            k = 0.5 + 0.5 * np.cos(2 * np.pi * (s / lam - cycles * t))
            k = k * np.exp(-(s / steps) ** 2 * 1.2)
            v = (S * k).sum(0) / k.sum(0)
            v = (v - v.mean()) / (v.std() + 1e-9)
            frames[f] += np.clip((v - 0.25) / 1.6, 0, 1) ** 1.4 * weight
    # cut into pieces that come and go, looping: a mask field whose phase turns once per loop
    m1, m2 = field(2, 10, 1.2, 31), field(2, 10, 1.2, 32)
    for f in range(FRAMES):
        a = 2 * np.pi * f / FRAMES
        mask = np.clip((m1 * np.cos(a) + m2 * np.sin(a) + 0.2) / 0.9, 0, 1)
        frames[f] *= mask
        if pulse:
            frames[f] *= 1 + pulse * np.sin(2 * a * 2)
    a = np.clip(frames * 1.15, 0, 1)
    rgb = np.empty((FRAMES, N, N, 3))
    for c, (lo, hi) in enumerate(((120, 225), (255, 255), (150, 232))):
        rgb[..., c] = lo + (hi - lo) * a
    return np.concatenate([rgb, (a * 235)[..., None]], -1)


def save_strip(name, frames, frametime):
    strip = np.concatenate(list(frames), axis=0).astype(np.uint8)
    Image.fromarray(strip, "RGBA").save(os.path.join(OUT, name + ".png"), optimize=True)
    with open(os.path.join(OUT, name + ".png.mcmeta"), "w") as fh:
        fh.write('{\n\t"animation": {\n\t\t"frametime": %d,\n\t\t"interpolate": true\n\t}\n}\n' % frametime)


MIXED = [(1.1, 30, 26, 2, 1.0), (2.4, 44, 40, 1, 0.8)]
save_strip("construct_ripples_r1", ripples(MIXED), 3)
save_strip("construct_ripples_r3", ripples([(3.2, 64, 60, 1, 1.0)]), 5)
save_strip("construct_ripples_r4", ripples(MIXED, pulse=0.5), 3)

# ---- T1 smoke skin: thin soft wisps, 32 px per block, looping ---------------------------------------
NS = 128
kxs = np.fft.fftfreq(NS, 1.0 / NS)
KXs, KYs = np.meshgrid(kxs, kxs, indexing="xy")
Ks = np.hypot(KXs, KYs)
r = np.random.default_rng(77)
amp = np.where((Ks >= 2) & (Ks <= 40), np.maximum(Ks, 1e-9) ** -1.4, 0.0)
phi = r.uniform(0, 2 * np.pi, Ks.shape)
turn = r.choice([-1, 1], Ks.shape) * (r.random(Ks.shape) < 0.5) + np.rint(-KYs * 1).astype(int)  # drift up a frame
smoke = []
for f in range(FRAMES):
    t = f / FRAMES
    v = np.real(np.fft.ifft2(amp * np.exp(1j * (phi + 2 * np.pi * turn * t))))
    v = (v - v.mean()) / (v.std() + 1e-9)
    d = np.clip((v - 0.2) / 1.8, 0, 1) ** 1.3
    rgba = np.zeros((NS, NS, 4))
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 175 + 50 * d, 255, 195 + 35 * d
    rgba[..., 3] = d * 70                   # thin: never more than about a quarter opaque
    smoke.append(rgba)
save_strip("construct_smoke", smoke, 4)
print("wrote construct_jade, construct_ripples_r1/r3/r4, construct_smoke to", OUT)
