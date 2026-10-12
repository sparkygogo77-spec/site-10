"""Draft hard light texture looks (32x32 tiles) and mockups on Wall, Dome, Bridge and the builder.
python tools/hard_light_looks.py docs/texture-drafts/hard-light  (drafts for J to pick from; not used by the mod yet)"""
import math, random, os, sys
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
N = 32

DARK = (6, 20, 70)
DEEP = (12, 52, 150)
MID = (30, 120, 235)
HI = (110, 205, 255)
CORE = (225, 248, 255)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(t):
    t = max(0.0, min(1.0, t))
    if t < 0.33:
        return mix(DARK, DEEP, t / 0.33)
    if t < 0.66:
        return mix(DEEP, MID, (t - 0.33) / 0.33)
    return mix(MID, HI, (t - 0.66) / 0.34)


def noise(seed, n=N, cells=4):
    """Tileable value noise 0..1."""
    rnd = random.Random(seed)
    g = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            fx, fy = x / n * cells, y / n * cells
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[y0 % cells][x0 % cells]; b = g[y0 % cells][(x0 + 1) % cells]
            c = g[(y0 + 1) % cells][x0 % cells]; d = g[(y0 + 1) % cells][(x0 + 1) % cells]
            out[y][x] = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return out


def voronoi(seed, count, n=N):
    rnd = random.Random(seed)
    pts = [(rnd.uniform(0, n), rnd.uniform(0, n), rnd.uniform(-1, 1)) for _ in range(count)]
    best = [[None] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            d1 = d2 = 1e9; v = 0
            for px, py, o in pts:
                for ox in (-n, 0, n):
                    for oy in (-n, 0, n):
                        dd = (px + ox - x - .5) ** 2 + (py + oy - y - .5) ** 2
                        if dd < d1:
                            d2, d1, v = d1, dd, o
                        elif dd < d2:
                            d2 = dd
            best[y][x] = (math.sqrt(d2) - math.sqrt(d1), v)
    return best


def img_from(fn):
    im = Image.new("RGBA", (N, N))
    p = im.load()
    for y in range(N):
        for x in range(N):
            p[x, y] = fn(x, y)
    return im


# ---- the looks ------------------------------------------------------------------------------------

def look_brick():
    nz = noise(3)
    def f(x, y):
        row = y // 8
        off = 8 if row % 2 else 0
        bx, by = (x + off) % 16, y % 8
        mortar = bx == 0 or by == 0
        if mortar:
            return CORE + (255,) if (bx == 0 and by in (3, 4)) or (by == 0 and bx in (7, 8)) else HI + (255,)
        edge_hi = by == 1 or bx == 1
        edge_lo = by == 7 or bx == 15
        t = 0.62 + 0.12 * nz[y][x] - 0.02 * by
        c = ramp(t)
        if edge_hi: c = mix(c, HI, 0.55)
        if edge_lo: c = mix(c, DEEP, 0.5)
        return c + (225,)
    return img_from(f)


def look_lattice():
    nz = noise(7, cells=2)
    def f(x, y):
        line = x % 8 == 0 or y % 8 == 0
        diag = (x + y) % 16 == 0 or (x - y) % 16 == 0
        cloud = nz[y][x]
        if line:
            return (CORE if (x % 8 == 0 and y % 8 == 0) else HI) + (255,)
        if diag:
            return mix(MID, HI, 0.4) + (215,)
        c = ramp(0.25 + 0.45 * cloud)
        return c + (round(110 + 70 * cloud),)
    return img_from(f)


def look_crystal():
    rnd = random.Random(11)
    # Triangulated facets: a jittered grid of points, each square split into two triangles.
    k = 4
    pts = {}
    for j in range(k + 1):
        for i in range(k + 1):
            jx = 0 if i in (0, k) else rnd.uniform(-2.5, 2.5)
            jy = 0 if j in (0, k) else rnd.uniform(-2.5, 2.5)
            pts[i, j] = (i * N / k + jx, j * N / k + jy)
    im = Image.new("RGBA", (N, N))
    d = ImageDraw.Draw(im)
    tris = []
    for j in range(k):
        for i in range(k):
            a, b, c, e = pts[i, j], pts[i + 1, j], pts[i, j + 1], pts[i + 1, j + 1]
            if (i + j) % 2:
                tris += [(a, b, e), (a, e, c)]
            else:
                tris += [(a, b, c), (b, e, c)]
    for t in tris:
        cx = sum(p[0] for p in t) / 3; cy = sum(p[1] for p in t) / 3
        light = 0.5 + 0.25 * math.sin(cx * 0.4 + cy * 0.2 + rnd.random() * 3) - 0.15 * (cy / N) + 0.1 * (1 - cx / N)
        d.polygon(t, fill=ramp(light) + (220,))
    for t in tris:
        d.line(list(t) + [t[0]], fill=HI + (245,), width=1)
    for i in range(N):  # bright rim, as the hard light edge
        d.point((i, 0), CORE + (255,)); d.point((0, i), CORE + (255,))
        d.point((i, N - 1), HI + (255,)); d.point((N - 1, i), HI + (255,))
    return im


def look_shards():
    v = voronoi(5, 9)
    def f(x, y):
        edge, o = v[y][x]
        if edge < 0.7:
            return CORE + (255,)
        if edge < 1.4:
            return HI + (235,)
        c = ramp(0.42 + 0.14 * o + 0.05 * min(edge, 5) / 5)
        return c + (200,)
    return img_from(f)


def look_hex():
    # Bubble cells on a staggered grid (so it tiles), thin glowing walls, each cell brighter inside.
    rnd = random.Random(9)
    pts = []
    for j in range(4):
        for i in range(3):
            pts.append(((i + (0.5 if j % 2 else 0)) * N / 3 + rnd.uniform(-1, 1), j * N / 4 + 4 + rnd.uniform(-1, 1)))
    def f(x, y):
        d1 = d2 = 1e9
        for px, py in pts:
            for ox in (-N, 0, N):
                for oy in (-N, 0, N):
                    dd = math.hypot(px + ox - x - .5, py + oy - y - .5)
                    if dd < d1: d2, d1 = d1, dd
                    elif dd < d2: d2 = dd
        edge = d2 - d1
        if edge < 0.8: return CORE + (255,)
        if edge < 1.6: return HI + (230,)
        return ramp(0.3 + 0.35 * max(0, 1 - d1 / 7)) + (round(120 + 60 * max(0, 1 - d1 / 7)),)
    return img_from(f)


def emblem_tile():
    # Concentric rings with the emblem: a feature tile (Wall centre, Dome cap, Bridge end).
    def f(x, y):
        dx, dy = (x + .5 - N / 2) / (N / 2), (y + .5 - N / 2) / (N / 2)
        d = math.hypot(dx, dy)
        base = ramp(0.45 + 0.1 * math.cos(d * 20)) + (215,)
        if d > 0.98:
            return base
        r = d / 0.62
        if r <= 1:
            ay = abs(dy / 0.62)
            if 0.8 < r: return CORE + (255,)
            if 0.34 < r < 0.54: return CORE + (255,)
            if r <= 0.34: return MID + (255,)
            if abs(dx / 0.62) < 0.12 and 0.5 < ay: return CORE + (255,)
            if 0.6 < ay < 0.74 and abs(dx / 0.62) < 0.38: return CORE + (255,)
            return DARK + (240,)
        if abs(d - 0.8) < 0.04 or abs(d - 0.92) < 0.03:
            return HI + (245,)
        return base
    return img_from(f)


LOOKS = [
    ("brick", "Glowing Brick", "Raised hard light bricks with glowing mortar, like the brick sheet. Solid and readable; best for Wall.", look_brick),
    ("lattice", "Lattice Grid", "A glowing grid with diagonal struts over a cloudy see-through core. The most see-through and 'tech'.", look_lattice),
    ("crystal", "Faceted Crystal", "Big flat triangular facets with bright edges, like the gem tile and the crystal golem.", look_crystal),
    ("shards", "Cracked Shards", "Uneven crystal plates split by white-hot seams, like the shattered-cell tile.", look_shards),
    ("hex", "Hex Bubble", "Honeycomb cells with glowing walls, like the bubble shield. Made for the Dome.", look_hex),
]


# ---- mockups -------------------------------------------------------------------------------------

def tiled(tile, w, h):
    im = Image.new("RGBA", (w * N, h * N))
    for j in range(h):
        for i in range(w):
            im.paste(tile, (i * N, j * N))
    return im




def affine_face(face, quad, size):
    """Maps face (rectangle) onto the parallelogram quad=(origin, u-vector, v-vector) in an image of size."""
    (ox, oy), (ux, uy), (vx, vy) = quad
    W, H = face.size
    # Inverse map: output (X,Y) -> face (x,y). X = ox + x/W*ux + y/H*vx
    det = ux * vy - uy * vx
    a = vy / det * W; b = -vx / det * W
    d_ = -uy / det * H; e = ux / det * H
    c = -(a * ox + b * oy); f = -(d_ * ox + e * oy)
    return face.transform(size, Image.AFFINE, (a, b, c, d_, e, f), resample=Image.NEAREST)


def shade(im, k):
    r, g, b, a = im.split()
    r = r.point(lambda v: min(255, round(v * k))); g = g.point(lambda v: min(255, round(v * k))); b = b.point(lambda v: min(255, round(v * k)))
    return Image.merge("RGBA", (r, g, b, a))


def bg(size):
    im = Image.new("RGBA", size, (18, 22, 34, 255))
    d = ImageDraw.Draw(im)
    for y in range(size[1] // 2, size[1]):
        t = (y - size[1] / 2) / (size[1] / 2)
        d.line([(0, y), (size[0], y)], fill=(round(30 + 20 * t), round(52 + 30 * t), round(30 + 10 * t), 255))
    return im


def wall_mock(tile, feature):
    """A 5x3 wall seen at an angle, the centre block the emblem panel, plus its thin top."""
    w, h = 5, 3
    face = tiled(tile, w, h)
    if feature is not None:
        face.paste(feature, (2 * N, 1 * N))
    S = 3
    size = (560, 380)
    out = bg(size)
    ox, oy = 50, 110
    u = (w * N * S * 0.9, -w * N * S * 0.18)
    v = (0, h * N * S * 0.9)
    front = affine_face(face, ((ox, oy), u, v), size)
    top = affine_face(shade(tiled(tile, w, 1), 1.25), ((ox, oy), u, (N * S * 0.45, -N * S * 0.3)), size)
    out.alpha_composite(top)
    out.alpha_composite(front)
    return out.crop((0, 0, size[0], size[1]))


def bridge_mock(tile):
    size = (560, 380)
    out = bg(size)
    S = 3
    length, width = 8, 2
    deck = tiled(tile, length, width)
    side = shade(tiled(tile, length, 1).crop((0, 0, length * N, N // 2)), 0.75)
    o = (40, 200)
    u = (length * N * S * 0.6, -length * N * S * 0.2)
    v = (width * N * S * 0.45, width * N * S * 0.25)
    out.alpha_composite(affine_face(deck, (o, u, v), size))
    o2 = (o[0] + v[0], o[1] + v[1])
    out.alpha_composite(affine_face(side, (o2, u, (0, N * S * 0.45)), size))
    return out


def dome_mock(tile, feature):
    """A dome: the texture wrapped round a sphere (equirectangular), lit from the top left, see-through."""
    size = (560, 380)
    out = bg(size)
    R = 160
    cx, cy = 280, 330
    tex = tiled(tile, 8, 4)
    tp = tex.load()
    TW, TH = tex.size
    o = out.load()
    for y in range(cy - R, cy + 1):
        for x in range(cx - R, cx + R + 1):
            dx, dy = (x - cx) / R, (cy - y) / R
            r2 = dx * dx + dy * dy
            if r2 > 1:
                continue
            dz = math.sqrt(1 - r2)
            lon = math.atan2(dx, dz) + 0.4
            lat = math.asin(dy)
            u = (lon / (2 * math.pi)) % 1
            vv = 1 - (lat / (math.pi / 2))
            c = tp[int(u * TW) % TW, min(TH - 1, int(vv * TH))]
            light = 0.7 + 0.45 * max(0, -0.5 * dx + 0.6 * dy + 0.6 * dz)
            rim = (1 - dz) ** 3
            col = tuple(min(255, round(c[i] * light + 200 * rim * (0.3 if i == 0 else 0.8 if i == 1 else 1))) for i in range(3))
            a = min(1, c[3] / 255 * 0.85 + rim * 0.6)
            base = o[x, y]
            o[x, y] = tuple(round(base[i] * (1 - a) + col[i] * a) for i in range(3)) + (255,)
    return out


def builder_mock(tile):
    """The villager builder from the front: head, nose, body, arms and legs filled with the material."""
    size = (560, 380)
    out = bg(size)
    S = 9  # screen px per texel
    parts = [  # x, y, w, h in texels (front view), centred at x=0
        (-4, 0, 8, 10), (-4, 10, 8, 12), (-8, 10, 4, 12), (4, 10, 4, 12), (-4, 22, 4, 12), (0, 22, 4, 12)]
    big = tile.resize((N * S // 4, N * S // 4), Image.NEAREST)  # 8 texels per tile
    for (x, y, w, h) in parts:
        fw, fh = w * S, h * S
        face = Image.new("RGBA", (fw, fh))
        for j in range(0, fh, big.height):
            for i in range(0, fw, big.width):
                face.paste(big, (i, j))
        d = ImageDraw.Draw(face)
        d.rectangle([0, 0, fw - 1, fh - 1], outline=CORE + (255,), width=3)
        out.alpha_composite(face, (280 + x * S, 30 + y * S // 1 // 1 * 1 - 0))
    # A villager face over the head, and the nose.
    d = ImageDraw.Draw(out)
    hx, hy = 280 - 4 * S, 30
    d.rectangle([hx + 1 * S, hy + 5 * S, hx + 7 * S, hy + 5 * S + S // 2], fill=DARK + (255,))
    for ex in (1, 5):
        d.rectangle([hx + ex * S, hy + 6 * S, hx + (ex + 1) * S - 1, hy + 7 * S - 1], fill=CORE + (255,))
        d.rectangle([hx + (ex + 1) * S, hy + 6 * S, hx + (ex + 2) * S - 1, hy + 7 * S - 1], fill=DARK + (255,))
    d.rectangle([hx + 3 * S, hy + 7 * S, hx + 5 * S - 1, hy + 11 * S - 1], fill=MID + (255,), outline=CORE + (255,), width=2)
    d.line([hx + 2 * S, hy + 8 * S + 4, hx + 3 * S, hy + 8 * S + 8], fill=DARK + (255,), width=3)
    d.line([hx + 5 * S, hy + 8 * S + 8, hx + 6 * S, hy + 8 * S + 4], fill=DARK + (255,), width=3)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    feature = emblem_tile()
    feature.resize((256, 256), Image.NEAREST).save(os.path.join(OUT, "emblem_tile.png"))
    for key, name, desc, fn in LOOKS:
        t = fn()
        t.save(os.path.join(OUT, f"{key}_32.png"))
        t.resize((256, 256), Image.NEAREST).save(os.path.join(OUT, f"{key}_tile.png"))
        wall_mock(t, feature if key != "hex" else None).save(os.path.join(OUT, f"{key}_wall.png"))
        dome_mock(t, feature).save(os.path.join(OUT, f"{key}_dome.png"))
        bridge_mock(t).save(os.path.join(OUT, f"{key}_bridge.png"))
        builder_mock(t).save(os.path.join(OUT, f"{key}_builder.png"))
        print("made", key)
