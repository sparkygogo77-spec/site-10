"""The Blue Lantern from J's sheet as a real mesh (see mesh_kit.py): a rounded slate-blue stone
body with grooves cut round each face, bevelled octagonal frames sunk round the windows, the
emblem behind glass front and back, domed lenses with bronze ports on the sides, a turned bronze
cap with bolts, a stepped octagonal foot with notched blocks and a chunky stone handle.

    python tools/mesh_blue_lantern.py <out.json>
"""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from mesh_kit import Model, rounded_box, lathe, oct_pt, fbm, norm

OUT = sys.argv[1] if len(sys.argv) > 1 else "blue_lantern_mesh.json"
m = Model("blue_lantern")

# ---- textures ------------------------------------------------------------------------------------
S = 512
n1 = fbm(S, 3)
n2 = fbm(S, 11, ((24, 0.6), (48, 0.4)))
crack = np.abs(fbm(S, 21, ((6, 0.6), (12, 0.4))) - 0.5)
base = np.array([80, 108, 146], float)       # slate blue, as the sheet
img = base[None, None, :] * (0.7 + 0.5 * n1[..., None]) * (0.94 + 0.12 * n2[..., None])
grain = fbm(S, 31, ((64, 0.6), (128, 0.4)))
img = img * (0.9 + 0.18 * grain[..., None])
m.texture("stone", Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.SMOOTH))

B = 4.6          # window: about 70% of the face, as measured on the sheet octagon half size
EMB = 0.873      # emblem outer radius as a fraction of B


def emblem_img(size=512):
    """The Blue Lantern emblem 1:1 from the sheet (same geometry as blockbench_models.blue_emblem),
    drawn smooth at high resolution over the window's glow."""
    ss = 3
    N = size * ss
    y, x = np.mgrid[0:N, 0:N]
    u = (x + 0.5) / N * 2 - 1
    v = 1 - (y + 0.5) / N * 2
    r = np.hypot(u, v)
    X, Y = u / EMB, v / EMB
    rr = np.hypot(X, Y)
    a = np.degrees(np.arctan2(np.abs(Y), np.abs(X)))
    line = ((rr >= 0.87) & (rr <= 1.0)) | ((rr >= 0.355) & (rr < 0.47)) | \
           ((rr >= 0.62) & (rr <= 0.79) & (a <= 52)) | \
           ((np.abs(X) < 0.3) & (np.abs(Y) >= 0.63) & (np.abs(Y) <= 0.79)) | \
           ((np.abs(X) < 0.055) & (np.abs(Y) >= 0.45) & (np.abs(Y) <= 0.66))
    disc = rr < 0.355
    field = (rr < 0.87) & ~line & ~disc
    out = np.zeros((N, N, 3))
    t = np.clip((r - EMB) / (1.08 - EMB), 0, 1)[..., None]
    out[:] = np.array([40, 130, 250]) * (1 - t) + np.array([8, 30, 120]) * t
    q = rr[..., None]
    out = np.where(field[..., None], np.array([70, 160, 240]) * (1 - q) + np.array([34, 104, 214]) * q, out)
    dq = np.clip(rr / 0.355, 0, 1)[..., None] ** 1.4
    out = np.where(disc[..., None], np.array([238, 252, 255]) * (1 - dq) + np.array([96, 214, 255]) * dq, out)
    out = np.where(line[..., None], np.array([230, 247, 255]) * (1 - q * 0.6) + np.array([176, 222, 255]) * q * 0.6, out)
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    return im


m.texture("emblem", emblem_img())


def cap_top_img(size=256):
    """The cap's top: turned rings round a recessed slate disc with the crown mark."""
    im = Image.new("RGB", (size, size), (168, 116, 64))
    d = ImageDraw.Draw(im)
    c = size / 2
    for rad, col in ((0.98, (120, 78, 40)), (0.93, (196, 140, 82)), (0.80, (120, 78, 40)), (0.76, (176, 122, 70)),
                     (0.62, (110, 70, 36)), (0.58, (70, 98, 136))):
        rr = rad * c
        d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=col)
    k = size / 256
    crown = [(-34, 22), (-34, -14), (-17, 4), (0, -24), (17, 4), (34, -14), (34, 22)]
    d.polygon([(c + x * k, c + y * k) for x, y in crown], fill=(214, 170, 104))
    d.rectangle((c - 34 * k, c + 22 * k, c + 34 * k, c + 30 * k), fill=(214, 170, 104))
    return im


m.texture("captop", cap_top_img())

# ---- the body ------------------------------------------------------------------------------------
BY = 10.0
HALF = (7.0, 6.6, 7.0)   # measured from the sheet's front and side views
R = 2.0


def shade(face, kind, data):
    if kind == "seam":
        return (0.62,) * 3                     # a dark cut line where each face meets its chamfers
    if kind in ("margin", "corner"):
        return (1 + 0.55 * data,) * 3          # the chamfers catch the light and wear pale
    return {"groove": (0.5,) * 3, "wall": (0.7,) * 3, "frametop": (1.15,) * 3, "framefoot": (0.82,) * 3,
            "face": (1.0,) * 3}.get(kind, (1, 1, 1))


def frame_loops(bulge=0.3):
    """The relief on a side face, outer to inner, as the sheet draws it: a thin cut line just inside
    the chamfer, the face bulging gently, then a thick bevelled octagonal frame hugging the glass
    and stepping down into it."""
    return [
        (0.96, 1.0, 0.0, False, "face"),
        (0.93, 1.0, -0.12, True, "groove"),
        (0.90, 1.0, 0.0, True, "face"),
        (0.5, 1.085, bulge, False, "face"),
        (0.0, 1.085, bulge * 0.8, True, "framefoot"),
        (0.0, 1.06, 0.5, True, "frametop"),
        (0.0, 1.005, 0.5, True, "frametop"),
        (0.0, 0.985, 0.25, True, "wall"),
        (0.0, 0.97, -0.4, False, "wall"),
    ]


def emblem_glass(model, pts, base, n, eu, ev):
    part = model.part("glow_emblem", "emblem")
    def uv(p):
        d = p - base
        return (np.dot(d, eu) / (2 * B) + 0.5, np.dot(d, ev) / (2 * B) + 0.5)
    mid = base - 0.42 * n
    c = part.v(mid, uv(mid))
    ids = [part.v(p, uv(p)) for p in pts]
    for j in range(len(ids)):
        part.tri.append([ids[j], ids[(j + 1) % len(ids)], c])


def lens_glass(model, pts, base, n, eu, ev):
    """A domed lens of light bulging out of the window, with a bronze port at its crown."""
    part = model.part("glow_lens", "lens")
    loops = [(1.0, -0.4), (0.93, 0.15), (0.8, 0.62), (0.62, 0.95), (0.47, 1.08)]
    prev = None
    for k, h in loops:
        ids = []
        for p in pts:
            d = p - base
            q = base + (np.dot(d, eu) * k) * eu + (np.dot(d, ev) * k) * ev + h * n
            rr = k
            f = ((rr - 0.44) / 0.56) ** 1.3
            col = tuple(np.array([200, 236, 255]) / 255 * (1 - f) + np.array([28, 104, 240]) / 255 * f)
            ids.append(part.v(q, (0, 0), col))
        if prev:
            for j in range(len(ids)):
                j2 = (j + 1) % len(ids)
                part.quad(prev[j], prev[j2], ids[j2], ids[j])
        prev = ids
    # the bronze port: a short tube with a lip, dark inside
    port = model.part("port", "bronze")
    rings = [(1.62, 1.0), (1.62, 1.42), (1.42, 1.55), (1.0, 1.5), (0.95, 1.3), (0.95, 0.75)]
    rows = []
    for rad, h in rings:
        row = []
        for i in range(25):
            th = 2 * math.pi * i / 24
            q = base + rad * math.cos(th) * eu + rad * math.sin(th) * ev + h * n
            row.append(port.v(q, (0, 0), (1, 1, 1) if h > 1.2 or rad > 1.3 else (0.2, 0.15, 0.12)))
        rows.append(row)
    for a in range(len(rows) - 1):
        for i in range(24):
            port.quad(rows[a][i], rows[a][i + 1], rows[a + 1][i + 1], rows[a + 1][i])
    # orient the port's faces outward along n (rings run counter-clockwise about n)
    P = np.array(port.p)
    for t in port.tri:
        fn = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
        mid = (P[t[0]] + P[t[1]] + P[t[2]]) / 3
        radial = mid - base - np.dot(mid - base, n) * n
        want = radial + 0.4 * n
        if np.dot(fn, want) < 0:
            t[1], t[2] = t[2], t[1]


def panel(face):
    if face in ("pz", "nz"):
        return {"B": B, "loops": frame_loops(), "glass": emblem_glass}
    if face in ("px", "nx"):
        return {"B": B, "loops": frame_loops(), "glass": lens_glass}
    # top and bottom: a groove round the edge, then flat (the cap and foot cover the middle)
    return {"B": 2.6, "loops": [(0.97, 1.0, 0.0, False, "face"), (0.94, 1.0, -0.16, True, "groove"),
                                (0.90, 1.0, -0.16, True, "groove"), (0.87, 1.0, 0.0, False, "face"),
                                (0.0, 1.0, 0.0, False, "face")]}


rounded_box(m, "body", "stone", (0, BY, 0), HALF, R, M=16, n_arc=6, panel=panel, color=shade, shape=1.12)

# ---- the cap -------------------------------------------------------------------------------------
TOP = BY + HALF[1]
# A wide, low bronze collar and a narrower ring on top, as on the sheet.
cap = [(TOP - 0.3, 4.5), (TOP + 0.55, 4.5), (TOP + 0.7, 4.35, "hard"), (TOP + 0.7, 3.9, "hard"),
       (TOP + 0.8, 3.85), (TOP + 1.55, 3.85), (TOP + 1.7, 3.7, "hard"), (TOP + 1.7, 3.2, "hard"),
       (TOP + 1.8, 3.15), (TOP + 2.0, 3.15), (TOP + 2.1, 3.02, "hard")]
lathe(m, "cap", "bronze", cap, 40, cap_uv=None, caps=(True, False),
      color=lambda y, r: (0.82, 0.82, 0.82) if r < 3.2 and y < TOP + 1.8 else (1, 1, 1))
top = m.part("cap_top", "captop")
cy = TOP + 2.101
mid = top.v((0, cy, 0), (0.5, 0.5))
rim = []
for i in range(48):
    th = 2 * math.pi * i / 48
    x, z = 3.02 * math.sin(th), -3.02 * math.cos(th)
    rim.append(top.v((x, cy, z), (0.5 + x / 6.04, 0.5 - z / 6.04)))
for i in range(48):
    top.tri.append([mid, rim[(i + 1) % 48], rim[i]])


def bolt(name, x, y, z, nrm, size=0.2):
    """A small domed bolt head facing along nrm."""
    nrm = norm(nrm)
    t1 = norm(np.cross(nrm, [0, 1, 0]) if abs(nrm[1]) < 0.9 else np.cross(nrm, [1, 0, 0]))
    t2 = np.cross(nrm, t1)
    p = m.part(name, "bronze")
    rings = [(size, 0.0), (size, 0.07), (size * 0.75, 0.15), (0.0, 0.19)]
    rows = []
    for rad, h in rings:
        rows.append([p.v(np.array([x, y, z]) + rad * math.cos(2 * math.pi * i / 10) * t1 +
                         rad * math.sin(2 * math.pi * i / 10) * t2 + h * nrm, (0, 0), (1.15,) * 3) for i in range(11)])
    for a in range(len(rows) - 1):
        for i in range(10):
            p.quad(rows[a][i], rows[a][i + 1], rows[a + 1][i + 1], rows[a + 1][i])
    P = np.array(p.p)
    for t in p.tri:
        fn = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
        if np.dot(fn, nrm) < -1e-9 or (abs(np.dot(fn, nrm)) < 1e-9 and np.dot(fn, (P[t[0]] - [x, y, z])) < 0):
            t[1], t[2] = t[2], t[1]


for i in range(16):
    th = 2 * math.pi * (i + 0.5) / 16
    bolt(f"cap_bolt_{i}", 4.5 * math.sin(th), TOP + 0.3, -4.5 * math.cos(th), (math.sin(th), 0, -math.cos(th)), 0.18)
for i in range(20):
    th = 2 * math.pi * i / 20
    bolt(f"cap_bolt_hi_{i}", 3.85 * math.sin(th), TOP + 1.18, -3.85 * math.cos(th), (math.sin(th), 0, -math.cos(th)), 0.13)

# ---- the foot ------------------------------------------------------------------------------------
OR = 1 / math.cos(math.radians(22.5))
FB = BY - HALF[1]
# A clean stepped octagonal foot (a wide slab, a step, a neck into the body), each step with a
# small bevel on its top edge, and four square feet on the corners of the slab as on the sheet.
foot = [(0.0, 4.6 * OR), (1.3, 4.6 * OR), (1.45, 4.45 * OR), (1.45, 3.95 * OR), (2.6, 3.95 * OR),
        (2.75, 3.8 * OR), (2.75, 3.3 * OR), (FB + 0.4, 3.3 * OR)]
lathe(m, "foot", "stone", foot, 8, phase=22.5, smooth=False,
      color=lambda y, r: (0.8,) * 3 if y < 1.0 else ((1.12,) * 3 if r < 4.3 * OR and y in (1.1, 2.2) else (1.0,) * 3))
for i in range(4):
    th = math.radians(45 + 90 * i)
    cx, cz = 4.45 * math.sin(th), -4.45 * math.cos(th)
    part = rounded_box(m, f"foot_corner_{i}", "stone", (cx, 0.85, cz), (0.9, 0.85, 0.9), 0.14, M=4, n_arc=2,
                       color=lambda *a: (1.0,) * 3)
    P = np.array(part.p) - [cx, 0.85, cz]
    c, s_ = math.cos(-th), math.sin(-th)
    Rm = np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
    part.p = (P @ Rm.T + [cx, 0.85, cz]).tolist()

# ---- the handle ----------------------------------------------------------------------------------
HT = 0.62
for sx in (-1, 1):
    rounded_box(m, f"handle_post_{sx}", "stone", (sx * 4.0, TOP + 3.9, 0), (HT, 2.15, HT), 0.22, M=8, n_arc=3)
    rounded_box(m, f"handle_step_{sx}", "stone", (sx * 3.15, TOP + 6.4, 0), (HT, HT, HT), 0.22, M=4, n_arc=3)
rounded_box(m, "handle_top", "stone", (0, TOP + 7.45, 0), (2.9, HT, HT), 0.22, M=12, n_arc=3)

tris = m.save(OUT)
print(f"{OUT}: {tris} triangles, {sum(len(p.p) for p in m.parts)} vertices, {len(m.parts)} parts")
