"""A small kit for building lanterns as real triangle meshes (not Blockbench boxes), so rounded
bodies, cut grooves, bevelled frames and domed lenses are true geometry with smooth shading.

Each model is a list of parts; a part has one material ("stone", "bronze", "glow", "lens", ...),
positions, normals, uvs, vertex colours and triangle indices. ``Model.save`` writes it as JSON
with its textures embedded, which the Lantern Model Bench viewer draws and a mod renderer can load.
"""
import base64, io, json, math
import numpy as np
from PIL import Image

T8 = math.tan(math.radians(22.5))


def norm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


class Part:
    def __init__(self, name, mat):
        self.name, self.mat = name, mat
        self.p, self.uv, self.c, self.tri = [], [], [], []

    def v(self, p, uv=(0.0, 0.0), c=(1.0, 1.0, 1.0)):
        self.p.append([float(x) for x in p])
        self.uv.append([float(uv[0]), float(uv[1])])
        self.c.append([float(x) for x in c])
        return len(self.p) - 1

    def quad(self, a, b, c, d):
        """Two triangles for a quad given counter-clockwise as seen from outside."""
        self.tri += [[a, b, c], [a, c, d]]

    def normals(self):
        P = np.array(self.p)
        N = np.zeros_like(P)
        for a, b, c in self.tri:
            fn = np.cross(P[b] - P[a], P[c] - P[a])
            N[a] += fn
            N[b] += fn
            N[c] += fn
        L = np.linalg.norm(N, axis=1, keepdims=True)
        L[L < 1e-12] = 1
        return N / L

    def out(self):
        return {"name": self.name, "mat": self.mat,
                "pos": [round(x, 4) for p in self.p for x in p],
                "nrm": [round(float(x), 4) for n in self.normals() for x in n],
                "uv": [round(x, 4) for u in self.uv for x in u],
                "col": [round(x, 3) for c in self.c for x in c],
                "idx": [i for t in self.tri for i in t]}


class Model:
    def __init__(self, name):
        self.name, self.parts, self.textures = name, [], {}

    def part(self, name, mat):
        p = Part(name, mat)
        self.parts.append(p)
        return p

    def texture(self, key, img):
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        self.textures[key] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    def save(self, path):
        tris = sum(len(p.tri) for p in self.parts)
        with open(path, "w") as f:
            json.dump({"name": self.name, "parts": [p.out() for p in self.parts], "textures": self.textures}, f)
        return tris


# ---- outlines: a rectangle and an octagon sampled with matching indices ------------------------
def rect_pt(j, M, Wu, Wv):
    """Point j (0..4M) round the rectangle |u|<=Wu, |v|<=Wv, uniform along each side, starting at
    the lower-left corner and running counter-clockwise."""
    s, i = divmod(j % (4 * M), M)
    f = i / M
    return [(-Wu + 2 * Wu * f, -Wv), (Wu, -Wv + 2 * Wv * f), (Wu - 2 * Wu * f, Wv), (-Wu, Wv - 2 * Wv * f)][s]


def oct_pt(j, M, B):
    """Point j round an octagon of half size B (flat sides facing u and v), indexed like rect_pt
    so the rectangle's corners meet the middles of the octagon's diagonal sides."""
    assert M % 4 == 0
    q = M // 4
    s, i = divmod(j % (4 * M), M)
    a, b = B * T8, B
    mid = B * (1 + T8) / 2
    # bottom side path: diag midpoint -> (-a,-b) -> (a,-b) -> diag midpoint
    if i <= q:
        f = i / q
        x, y = -mid + (mid - a) * f * -1 * -1, 0
        x = -mid + (-a + mid) * f
        y = -mid + (-b + mid) * f
    elif i <= M - q:
        f = (i - q) / (M - 2 * q)
        x, y = -a + 2 * a * f, -b
    else:
        f = (i - (M - q)) / q
        x = a + (mid - a) * f
        y = -b + (-mid + b) * f
    # rotate the bottom path to the side it belongs to (counter-clockwise quarter turns)
    for _ in range(s):
        x, y = -y, x
    return (x, y)


# ---- a rounded box whose four sides can carry relief panels ------------------------------------
def pnorm(v, p):
    if p == 2:
        return norm(v)
    m = sum(abs(x) ** p for x in v) ** (1 / p)
    return np.asarray(v, float) / m if m > 1e-12 else np.asarray(v, float)


def rounded_box(model, name, mat, center, half, R, M=16, n_arc=5, panel=None, color=None, uvscale=0.16, shape=2):
    """A box with every edge rounded to radius R. ``panel(face)`` may return a relief spec for a
    face (see ``panel_mesh``); faces are named "px","nx","py","ny","pz","nz". ``color(face, kind,
    data)`` returns a vertex colour multiplier."""
    part = model.part(name, mat)
    C = np.asarray(center, float)
    H = np.asarray(half, float)
    color = color or (lambda *a: (1, 1, 1))
    faces = []
    for ax in range(3):
        for sg in (1, -1):
            n = np.zeros(3)
            n[ax] = sg
            up = np.array([0, 1.0, 0]) if ax != 1 else np.array([0, 0, -1.0 * sg])
            ev = up
            eu = np.cross(ev, n)
            faces.append(({0: "x", 1: "y", 2: "z"}[ax], sg, n, eu, ev))
    for axn, sg, n, eu, ev in faces:
        fname = ("p" if sg > 0 else "n") + axn
        iu, iv, ia = int(np.argmax(np.abs(eu))), int(np.argmax(np.abs(ev))), int(np.argmax(np.abs(n)))
        hu, hv, hn = H[iu], H[iv], H[ia]
        Wu, Wv, Wn = hu - R, hv - R, hn - R

        def place(cu, cv):
            """Model point for extended face coordinates (cu, cv) (beyond W = into the rounding)."""
            c = cu * eu + cv * ev + (Wn + R) * n
            inner = np.clip(c, -(H - R), H - R)
            off = c - inner
            # shape 2: round edges; shape 1: flat chamfers and triangular corners (as on the
            # sheets); in between: chamfers softened where they meet the faces.
            return C + inner + R * pnorm(off, shape), norm(off)

        def samples(W):
            ang = [math.radians(45 * k / n_arc) for k in range(n_arc, 0, -1)]
            lo = [-(W + R * math.tan(a)) for a in ang]
            flat = [-W + 2 * W * i / M for i in range(M + 1)]
            return lo + flat + [-x for x in reversed(lo)]
        su, sv = samples(Wu), samples(Wv)
        nu, nv = len(su), len(sv)
        grid = {}
        f0, f1 = n_arc, n_arc + M     # the flat range of indices
        for a in range(nu):
            for b in range(nv):
                inside = f0 <= a <= f1 and f0 <= b <= f1
                edge = a in (f0, f1) or b in (f0, f1)
                if inside and not edge:
                    continue
                p, nn = place(su[a], sv[b])
                curve = 1 - float(np.dot(nn, n))
                out_a = max(f0 - a, a - f1, 0)
                out_b = max(f0 - b, b - f1, 0)
                kind = "seam" if max(out_a, out_b) == 1 else ("corner" if out_a and out_b else "margin")
                grid[(a, b)] = part.v(p, (su[a] * uvscale, sv[b] * uvscale), color(fname, kind, curve))
        for a in range(nu - 1):
            for b in range(nv - 1):
                if f0 <= a < f1 and f0 <= b < f1:
                    continue
                part.quad(grid[(a, b)], grid[(a + 1, b)], grid[(a + 1, b + 1)], grid[(a, b + 1)])
        # the flat middle: relief loops from the rectangle in to the panel's middle
        ring = []
        for j in range(4 * M):
            s_, i = divmod(j, M)
            a, b = [(f0 + i, f0), (f1, f0 + i), (f1 - i, f1), (f0, f1 - i)][s_]
            ring.append(grid[(a, b)])
        spec = panel(fname) if panel else None
        panel_mesh(model, part, ring, spec, C, n, eu, ev, Wn + R, Wu, Wv, M, uvscale, fname, color)
    return part


def panel_mesh(model, part, ring, spec, C, n, eu, ev, hn, Wu, Wv, M, uvscale, fname, color):
    """Relief inside a face's flat rectangle. ``spec`` is a dict:
      loops: [(t, k, h, hard, kind), ...] outer to inner; a point is lerp(k*octagon, rectangle, t)
             lifted h along the face normal; hard loops split shading there (crisp edges).
      B: the octagon's half size; glass(model, centre, n, eu, ev, inner_ring_points): fills the
      middle (a window), else the middle is closed flat.
    Without a spec the face is filled with a few shrinking loops."""
    if spec is None:
        spec = {"B": min(Wu, Wv) * 0.5, "loops": [(0.5, 1.0, 0.0, False, "face"), (0.0, 0.6, 0.0, False, "face")]}
    B = spec["B"]
    base = C + hn * n
    prev = ring
    prev_pts = None
    for t, k, h, hard, kind in spec["loops"]:
        pts, ids = [], []
        for j in range(4 * M):
            ou, ov = oct_pt(j, M, B)
            ru, rv = rect_pt(j, M, Wu, Wv)
            u = k * ou * (1 - t) + ru * t
            vv = k * ov * (1 - t) + rv * t
            p = base + u * eu + vv * ev + h * n
            pts.append(p)
            ids.append(part.v(p, (u * uvscale, vv * uvscale), color(fname, kind, h)))
        for j in range(4 * M):
            j2 = (j + 1) % (4 * M)
            part.quad(prev[j], prev[j2], ids[j2], ids[j])
        if hard:   # a fresh copy of this loop, so the next band shades on its own (a crisp edge)
            ids = [part.v(part.p[i], part.uv[i], part.c[i]) for i in ids]
        prev, prev_pts = ids, pts
    if spec.get("glass"):
        spec["glass"](model, prev_pts, base, n, eu, ev)
    else:
        mid = part.v(base + spec["loops"][-1][2] * n, (0, 0), color(fname, "face", 0))
        for j in range(4 * M):
            part.tri.append([prev[j], prev[(j + 1) % (4 * M)], mid])


# ---- turned parts ----------------------------------------------------------------------------------
def lathe(model, name, mat, profile, sides, base=(0, 0, 0), phase=0.0, smooth=True, color=None,
          caps=(True, True), cap_uv=None, part=None):
    """Turn ``profile`` [(y, r) or (y, r, "hard"), ...] (bottom to top) about the vertical axis
    through ``base``. Rows marked hard start a fresh ring of vertices (a crisp edge). Steps that
    go inward face up, steps that go outward face down. ``smooth=False`` keeps flat facets."""
    part = part or model.part(name, mat)
    color = color or (lambda y, r: (1, 1, 1))
    bx, by, bz = base
    ph = math.radians(phase)

    def at(y, r, th):
        return (bx + r * math.sin(th), by + y, bz - r * math.cos(th))

    def ring(y, r):
        return [part.v(at(y, r, ph + 2 * math.pi * i / sides), (i / sides * 4, y * 0.16), color(y, r))
                for i in range(sides + 1)]
    if smooth:
        cur = ring(*profile[0][:2])
        for s in range(1, len(profile)):
            y, r = profile[s][:2]
            nxt = ring(y, r)
            for i in range(sides):
                part.quad(cur[i], nxt[i], nxt[i + 1], cur[i + 1])
            cur = ring(y, r) if len(profile[s]) > 2 else nxt
    else:
        for s in range(len(profile) - 1):
            (y0, r0), (y1, r1) = profile[s][:2], profile[s + 1][:2]
            for i in range(sides):
                ta, tb = ph + 2 * math.pi * i / sides, ph + 2 * math.pi * (i + 1) / sides
                a = part.v(at(y0, r0, ta), (0, y0 * 0.16), color(y0, r0))
                b = part.v(at(y0, r0, tb), (r0 * 0.16, y0 * 0.16), color(y0, r0))
                c = part.v(at(y1, r1, tb), (r1 * 0.16, y1 * 0.16), color(y1, r1))
                d = part.v(at(y1, r1, ta), (0, y1 * 0.16), color(y1, r1))
                part.quad(a, d, c, b)
    cuv = cap_uv or (lambda x, z: (x * 0.16, z * 0.16))
    for end, top in ((0, False), (-1, True)):
        y, r = profile[end][:2]
        if r <= 0 or not caps[1 if top else 0]:
            continue
        mid = part.v((bx, by + y, bz), cuv(0, 0), color(y, 0))
        rim = []
        for i in range(sides):
            th = ph + 2 * math.pi * i / sides
            x, z = r * math.sin(th), -r * math.cos(th)
            rim.append(part.v((bx + x, by + y, bz + z), cuv(x, z), color(y, r)))
        for i in range(sides):
            a, b = rim[i], rim[(i + 1) % sides]
            part.tri.append([mid, b, a] if top else [mid, a, b])
    return part


# ---- textures -------------------------------------------------------------------------------------
def value_noise(size, cells, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((cells + 1, cells + 1))
    g[-1, :] = g[0, :]
    g[:, -1] = g[:, 0]
    x = np.linspace(0, cells, size, endpoint=False)
    i = x.astype(int)
    f = x - i
    f = f * f * (3 - 2 * f)
    a = g[i][:, i] * (1 - f)[None, :] + g[i][:, i + 1] * f[None, :]
    b = g[i + 1][:, i] * (1 - f)[None, :] + g[i + 1][:, i + 1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def fbm(size, seed, octaves=((4, 0.5), (8, 0.25), (16, 0.15), (32, 0.1))):
    return sum(w * value_noise(size, c, seed + k) for k, (c, w) in enumerate(octaves))
