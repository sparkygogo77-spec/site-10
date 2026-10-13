"""White flowing construct texture: python tools/construct_flow_texture.py <out.png> [px_per_block] [frames]

A flat white hard-light surface with soft dark smoke drifting over it, like a nebula. One frame
covers 8 x 8 blocks (the in-game model gives each block its slice by world position, see
FlowConstructModel), and the texture wraps at its edges, so any number of blocks side by side read
as one unbroken surface. The animation loops too.

How it stays seamless and loops, exactly: every layer is a sum of waves exp(i(k.x + phi + 2 pi n t)),
where each wave vector k is a whole number of cycles across the frame (so it wraps in space) and
each n is a whole number of cycles over the loop (so it wraps in time). Smoke is that sum, warped by
two slower sums of the same kind (sampled with wrap-around), then shaped and coloured.
"""
import sys
import numpy as np
from PIL import Image

OUT = sys.argv[1]
PPB = int(sys.argv[2]) if len(sys.argv) > 2 else 32        # pixels per block
FRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else 48
N = 8 * PPB                                                # one frame: 8 x 8 blocks
rng = np.random.default_rng(1729)

kx = np.fft.fftfreq(N, 1.0 / N)                            # whole cycles across the frame
KX, KY = np.meshgrid(kx, kx, indexing="xy")
K = np.hypot(KX, KY)


def layer(beta, kmin, kmax, drift, churn=0.0):
    """A periodic random field generator: amplitudes ~ k^-beta between kmin and kmax cycles per frame.
    It drifts by `drift` whole frames (dx, dy) per loop, which moves every wave by a whole number of
    cycles, so the loop closes; `churn` is the share of fine waves that also turn once per loop, so
    the smoke curls as it travels instead of sliding like a picture."""
    amp = np.where((K >= kmin) & (K <= kmax), np.maximum(K, 1e-9) ** -beta, 0.0)
    amp *= np.exp(-(K / kmax) ** 4)                        # soft high-frequency roll-off
    phi = rng.uniform(0, 2 * np.pi, K.shape)
    n = (rng.random(K.shape) < churn) * rng.choice([-1, 1], K.shape)
    n += np.rint(-(KX * drift[0] + KY * drift[1])).astype(int)

    def at(t):
        spec = amp * np.exp(1j * (phi + 2 * np.pi * n * t))
        f = np.real(np.fft.ifft2(spec)) * N * N
        return f / (np.std(f) + 1e-9)
    return at


smoke = layer(1.45, 2, 45, (1, 0), 0.25)       # the smoke: soft clouds down to fine wisps, drifting along
warp_a = layer(2.2, 1, 6, (0, 1))               # slow currents crossing it, stretching it into streaks
warp_b = layer(2.2, 1, 6, (-1, 0))
detail = layer(1.1, 12, 60, (1, 1), 0.4)        # fine grain inside the wisps

yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)


def sample_wrap(f, x, y):
    """Bilinear sample of the periodic field f at (x, y), wrapping round the edges."""
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    tx = x - x0; ty = y - y0
    x0 %= N; y0 %= N; x1 = (x0 + 1) % N; y1 = (y0 + 1) % N
    a = f[y0, x0] * (1 - tx) + f[y0, x1] * tx
    b = f[y1, x0] * (1 - tx) + f[y1, x1] * tx
    return a * (1 - ty) + b * ty


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


WHITE = np.array([246, 248, 252], float)
SMOKE = np.array([86, 94, 110], float)        # cool dark grey
GLOW = np.array([255, 255, 255], float)

frames = []
for f in range(FRAMES):
    t = f / FRAMES
    W = 0.055 * N                               # warp reach: about half a block
    wx, wy = warp_a(t) * W, warp_b(t) * W
    s = sample_wrap(smoke(t), xx + wx, yy + wy)
    d = sample_wrap(detail(t), xx + wx * 0.6, yy + wy * 0.6)
    s = s + 0.22 * d
    # dark smoke where the field is high, thinning to nothing: most of the surface stays white
    dens = smoothstep(0.1, 1.9, s) ** 1.2
    # a faint bright rim where smoke thins out, like light catching its edge
    rim = np.exp(-((s - 0.2) / 0.22) ** 2) * 0.35
    col = WHITE + (SMOKE - WHITE) * (0.62 * dens)[..., None]
    col = col + (GLOW - col) * rim[..., None] * (1 - dens)[..., None]
    frames.append(np.clip(col, 0, 255).astype(np.uint8))

strip = np.concatenate(frames, axis=0)
alpha = np.full(strip.shape[:2] + (1,), 236, np.uint8)     # hard light: nearly solid, a hint see-through
Image.fromarray(np.concatenate([strip, alpha], axis=2), "RGBA").save(OUT, optimize=True)
with open(OUT + ".mcmeta", "w") as fh:
    fh.write('{\n\t"animation": {\n\t\t"frametime": 6,\n\t\t"interpolate": true\n\t}\n}\n')
print(f"wrote {OUT}: {N}x{N} per frame ({PPB} px per block, 8 x 8 blocks), {FRAMES} frames")
