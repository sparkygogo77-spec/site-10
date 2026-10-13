"""The Yellow Blast level 4 runner (J: Sinestro's blast sprints at a scary pace through whatever you aim
at): an original gaunt fear construct of yellow hard light, hunched, horned and clawed, built pixel by
pixel like the lanterns but in jointed parts so it can run.

Each part is voxelised in its own frame (rest pose: standing straight, arms hanging), so a joint turns it
about its pivot. 32 pixels per block (G = 0.5 model pixels, 16 model pixels = 1 block).

    python tools/pixel_dread_runner.py OUTDIR   -> OUTDIR/dread_runner.npz

npz: for part n, q<n> (faces x 4 x 3, in the part's frame, pivot at 0), c<n> (sRGB), k<n> (material kind),
and names, parents (-1 = root), pivots (rest-pose pivot in model pixels, z up, +y forward).
Kinds: 0 dark core, 4 amber hard light, 6 bright hard-light edges, 7 eyes (white-hot).
"""
import os, sys
import numpy as np

G = 0.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def _seg(P, a, b, r0, r1=None):
    """Distance to a capsule from a to b whose radius runs r0 -> r1."""
    r1 = r0 if r1 is None else r1
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(1e-9, ab @ ab), 0, 1)
    d = np.linalg.norm(P - (a + t[..., None] * ab), axis=-1)
    return d - (r0 + (r1 - r0) * t), t


# Variants (J wants options): a = gaunt (the first one), b = brute, c = wraith.
VARIANTS = {
    "a": dict(tr=1.0, r=1.0, horn=1.0, claw=1.0, spike=1.0),
    "b": dict(tr=1.35, r=1.45, horn=1.5, claw=0.8, spike=1.4),
    "c": dict(tr=0.8, r=0.72, horn=1.25, claw=1.9, spike=1.7),
}
V = dict(VARIANTS["a"])


def seg(P, a, b, r0, r1=None, k="r"):
    """seg with its radii scaled by the variant's k."""
    r1 = r0 if r1 is None else r1
    return _seg(P, a, b, r0 * V[k], r1 * V[k])


def smin(a, b, k=1.2):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


# The skeleton at rest: name, parent, pivot (model pixels).
PARTS = [
    ("torso", -1, (0, 0, 22)),
    ("head", 0, (0, 0.5, 37)),
    ("arm_l", 0, (6, 0, 34)), ("fore_l", 2, (6.5, 0, 24.5)),
    ("arm_r", 0, (-6, 0, 34)), ("fore_r", 4, (-6.5, 0, 24.5)),
    ("thigh_l", 0, (3, 0, 22)), ("shin_l", 6, (3, 1.5, 13)),
    ("thigh_r", 0, (-3, 0, 22)), ("shin_r", 8, (-3, 1.5, 13)),
]


def shape(name, P):
    """Signed distance (model pixels) of a part, P in world rest-pose coordinates; plus a tag array:
    0 body, 1 spine/ridge, 2 eye, 3 claw/horn."""
    tag = np.zeros(P.shape[:-1], np.int8)
    s = 1 if name.endswith("_l") else -1
    if name == "torso":
        # Ribcage swelling at the chest, a pinched waist, hips; spikes down the back.
        d, _ = seg(P, (0, 0, 22.5), (0, 0.3, 28), 2.6, 3.0, k="tr")
        d2, _ = seg(P, (0, 0.6, 29), (0, 0.2, 35), 4.6, 3.6, k="tr")
        d = smin(d, d2, 1.5)
        hips, _ = seg(P, (-3, 0, 22.5), (3, 0, 22.5), 2.2)
        d = smin(d, hips, 1.0)
        sh, _ = seg(P, (-6, 0, 34.2), (6, 0, 34.2), 1.9, 1.9)
        d = smin(d, sh, 1.2)
        for z in np.arange(24, 36, 2.2):
            L = V["spike"]
            sp, t = _seg(P, (0, -2.6 * V["tr"], z), (0, -2.6 * V["tr"] - 2.6 * L, z + 1.2 * L), 0.9, 0.15)
            hit = sp < d
            tag[hit & (sp < 0)] = 1
            d = np.minimum(d, sp)
        return d, tag
    if name == "head":
        # A long skull pushed forward, sunken cheeks, a jaw, swept-back horns, two eyes.
        d, _ = seg(P, (0, 0, 38.2), (0, 3.6, 40.4), 2.4, 2.0, k="tr")
        jaw, _ = seg(P, (0, 1.2, 37.6), (0, 4.4, 38.4), 1.4, 0.9, k="tr")
        d = smin(d, jaw, 0.8)
        neck, _ = seg(P, (0, 0, 36), (0, 0.6, 38.4), 1.2)
        d = smin(d, neck, 0.8)
        for sx in (1, -1):
            H = V["horn"]
            m1 = (1.4 * sx + 2.0 * sx * H, 0.6 - 2.2 * H, 41.4 + 2.2 * H)
            h1, _ = _seg(P, (1.4 * sx, 0.6, 41.4), m1, 0.8 * min(H, 1.3), 0.45)
            h2, _ = _seg(P, m1, (m1[0] + 0.6 * sx * H, m1[1] - 3.0 * H, m1[2] + 0.8 * H), 0.45, 0.1)
            horn = np.minimum(h1, h2)
            tag[(horn < d) & (horn < 0)] = 3
            d = np.minimum(d, horn)
            eye = np.linalg.norm(P - np.array([1.05 * sx * V["tr"], 4.0 + 1.6 * (V["tr"] - 1), 40.5]), axis=-1) - 0.75
            tag[(eye < 0.15) & (d < 0.6)] = 2
        return d, tag
    if name.startswith("arm"):
        d, _ = seg(P, (6 * s, 0, 34), (6.5 * s, 0, 24.5), 1.7, 1.2)
        return d, tag
    if name.startswith("fore"):
        d, _ = seg(P, (6.5 * s, 0, 24.5), (6.6 * s, 0.6, 15), 1.2, 1.0)
        hand, _ = seg(P, (6.6 * s, 0.6, 15), (6.6 * s, 1.0, 13.4), 1.3, 1.0)
        d = smin(d, hand, 0.5)
        for dx in (-0.9, 0, 0.9):
            C_ = V["claw"]
            cl, _ = _seg(P, (6.6 * s + dx, 1.0, 13.4), (6.6 * s + dx * 1.4, 1.0 + 1.6 * C_, 13.4 - 3.8 * C_), 0.45, 0.08)
            tag[(cl < d) & (cl < 0)] = 3
            d = np.minimum(d, cl)
        return d, tag
    if name.startswith("thigh"):
        d, _ = seg(P, (3 * s, 0, 22), (3 * s, 1.5, 13), 2.3, 1.5)
        return d, tag
    if name.startswith("shin"):
        # Long shin back to a raised heel, then a clawed foot: a runner's leg.
        d, _ = seg(P, (3 * s, 1.5, 13), (3 * s, -1.6, 3.2), 1.4, 0.9)
        foot, _ = seg(P, (3 * s, -1.6, 3.2), (3 * s, 2.6, 0.9), 0.9, 0.8)
        d = smin(d, foot, 0.6)
        for dx in (-0.8, 0.8):
            cl, _ = _seg(P, (3 * s + dx, 2.6, 0.9), (3 * s + dx * 1.2, 2.6 + 2.0 * V["claw"], 0.3), 0.4, 0.08)
            tag[(cl < d) & (cl < 0)] = 3
            d = np.minimum(d, cl)
        return d, tag
    raise KeyError(name)


def colour(name, tag, depth, c, n):
    """Face colour and kind. depth: how far inside the surface the voxel is (pixels)."""
    x, y, z = c
    if tag == 2:
        return np.array([255, 252, 220.0]), 7
    if tag in (1, 3):
        return np.array([255, 226, 96.0]), 6
    # Hard-light skin: bright yellow edges where the surface turns (thin shell), amber inside,
    # dark sinew bands (ribs on the chest, lengthwise striations on the limbs).
    if name == "torso" and 28 < z < 35 and np.sin(z * 2.1) > 0.55 and y > -1.5:
        return np.array([70, 44, 6.0]), 0
    if name != "torso" and name != "head" and np.sin((x * 3.1 + y * 2.3) * 1.3 + z * 0.15) > 0.82:
        return np.array([92, 60, 8.0]), 0
    if n[2] < -0.5:
        return np.array([120, 78, 10.0]), 4          # undersides darker
    edge = n[2] > 0.5 or abs(n[0]) > 0.5 and abs(y) < 0.6
    if edge:
        return np.array([255, 214, 70.0]), 6
    v = 0.85 + 0.15 * np.sin(x * 1.7 + z * 1.3) * np.cos(y * 2.1)
    return np.array([236, 168, 24.0]) * v, 4


def voxelise(name, pivot):
    lo = np.array([-12, -9, -2.0]); hi = np.array([12, 9, 48.0])
    xs = np.arange(lo[0], hi[0], G) + G / 2
    ys = np.arange(lo[1], hi[1], G) + G / 2
    zs = np.arange(lo[2], hi[2], G) + G / 2
    P = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1)
    d, tag = shape(name, P)
    occ = d < 0
    Q, C, K = [], [], []
    S = occ.shape
    for i, j, k in np.argwhere(occ):
        c = np.array([xs[i], ys[j], zs[k]])
        for nn in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            a_, b_, c_ = i + nn[0], j + nn[1], k + nn[2]
            if 0 <= a_ < S[0] and 0 <= b_ < S[1] and 0 <= c_ < S[2] and occ[a_, b_, c_]:
                continue
            nv = np.array(nn, float)
            col, kind = colour(name, int(tag[i, j, k]), -d[i, j, k], c, nv)
            ax = np.array([0, 1, 0.]) if nn[0] else np.array([1, 0, 0.])
            bx = np.cross(nv, ax)
            f0 = c + nv * G / 2
            cs = [f0 + (ax * sa + bx * sb) * G / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            if np.dot(np.cross(cs[1] - cs[0], cs[2] - cs[0]), nv) < 0:
                cs = cs[::-1]
            Q.append(np.asarray(cs) - np.asarray(pivot, float)); C.append(np.clip(col, 0, 255)); K.append(kind)
    return np.asarray(Q, np.float32), np.asarray(C, np.float32), np.asarray(K, np.int8)


def write(variant, path):
    V.update(VARIANTS[variant])
    out = {}
    for n, (name, parent, pivot) in enumerate(PARTS):
        q, c, k = voxelise(name, pivot)
        out[f"q{n}"], out[f"c{n}"], out[f"k{n}"] = q, c, k
        print(name, len(q), "faces", np.bincount(k, minlength=8))
    out["names"] = np.array([p[0] for p in PARTS])
    out["parents"] = np.array([p[1] for p in PARTS], np.int32)
    out["pivots"] = np.array([p[2] for p in PARTS], np.float32)
    np.savez_compressed(path, **out)


if __name__ == "__main__":
    write("a", os.path.join(OUT, "dread_runner.npz"))
    for v in VARIANTS:
        print("variant", v)
        write(v, os.path.join(OUT, f"dread_runner_{v}.npz"))
