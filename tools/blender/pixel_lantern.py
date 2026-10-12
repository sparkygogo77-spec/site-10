"""The Blue Lantern built straight on Minecraft's pixel grid from measurements of J's sheet: cubes on
a GRID (0.5 = 32 per block, 0.25 = 64 per block), every cube face painted as pixel art at 4 pixels
per unit (64 per block). The emblem is authored pixel by pixel, not shrunk from a picture. Renders
the sheet's nine views in Blender beside the sheet and scores the silhouette against it.

    python tools/blender/pixel_lantern.py <sheet.jpg> <out.png> [--grid 0.5] [--fast]

Units are the mod's (1 = 1/16 block). Measured from the sheet's front and side views at 12 px per
unit: body 13.3 wide and 13.6 tall on a 4.6 tall stepped foot, windows a 5.5 octagon frame round a
4.75 domed glass, bronze collar 4.35 round, stone handle loop to 26.7.
"""
import math, os, sys
import numpy as np

SHEET, OUT = sys.argv[1], sys.argv[2]
G = float(sys.argv[sys.argv.index("--grid") + 1]) if "--grid" in sys.argv else 0.5
T = 0.25                                  # one texture pixel: 64 per block
FAST = "--fast" in sys.argv
K = int(round(G / T))                     # texture pixels across one cube face
# the glowing emblem glass may use finer pixels than the rest (--emblem-res 128 = 128 per block)
TG = 16 / float(sys.argv[sys.argv.index("--emblem-res") + 1]) / 16 * 1 if "--emblem-res" in sys.argv else T
TG = 1 / (float(sys.argv[sys.argv.index("--emblem-res") + 1]) / 16) if "--emblem-res" in sys.argv else T

# ---- dimensions ------------------------------------------------------------------------------------
HX, HZ, CZ = 6.65, 6.8, 11.4              # body half width/depth, half height, centre height
CH = 1.9                                  # chamfer
FR_OUT, GL = 5.5, 4.75                    # window frame outer half size, glass half size
FR_UP = 0.5                               # how far the frame stands proud
DOME = 0.9                                # how far the glass domes out past the face
EMB_PX = 17.5                             # emblem radius in texture pixels (4.4 units, measured)
TOP = CZ + HZ                             # 18.2


def octn(s, t):
    return np.maximum(np.maximum(np.abs(s), np.abs(t)), (np.abs(s) + np.abs(t)) / math.sqrt(2))


# body planes (normal, offset) about the body centre: inside where n.q <= d for all
PLANES = []
for ax in range(3):
    for sg in (-1, 1):
        n = np.zeros(3)
        n[ax] = sg
        PLANES.append((n, HZ if ax == 2 else HX))
for a, b in ((0, 1), (0, 2), (1, 2)):
    for sa in (-1, 1):
        for sb in (-1, 1):
            n = np.zeros(3)
            n[a], n[b] = sa, sb
            ha = HZ if a == 2 else HX
            hb = HZ if b == 2 else HX
            PLANES.append((n / math.sqrt(2), (ha + hb - CH) / math.sqrt(2)))
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            PLANES.append((np.array([sx, sy, sz]) / math.sqrt(3), (HX + HX + HZ - 1.5 * CH) / math.sqrt(3)))
PN = np.array([p[0] for p in PLANES])
PD = np.array([p[1] for p in PLANES])

# ---- the cube grid ---------------------------------------------------------------------------------
xs = np.arange(-8.5, 8.5, G) + G / 2
zs = np.arange(-0.0, 27.5, G) + G / 2
X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
P = np.stack([X, Y, Z - CZ], -1)
part = np.zeros(X.shape, np.int8)          # 0 empty
STONE, FRAME, EMBLEM, LENS, PORT, HOLLOW, BRONZE, CAPTOP, HANDLE, FOOT = range(1, 11)

body = np.all(P @ PN.T <= PD + 1e-6, axis=-1)
part[body] = STONE

# the four windows: a raised octagonal frame, glass sunk inside it and domed outward
SIDES = [("front", 1, -1), ("back", 1, 1), ("right", 0, 1), ("left", 0, -1)]   # (name, axis, sign)
for name, ax, sg in SIDES:
    depth = P[..., ax] * sg - HX            # height above the face plane
    s = P[..., 1 - ax] if ax == 0 else P[..., 0]
    t = P[..., 2]
    r = octn(s, t)
    frame = (r >= GL) & (r < FR_OUT) & (depth > 0) & (depth <= FR_UP)
    part[frame] = FRAME
    # sink the face under the glass, then dome the glass out
    sunk = (r < GL) & (depth > -G) & (depth <= 0)
    part[sunk] = 0
    dome_h = DOME * np.sqrt(np.clip(1 - (r / GL) ** 2, 0, 1))
    glass = (r < GL) & (depth > -G) & (depth <= dome_h - G * 0.5 + 1e-6)
    part[glass] = EMBLEM if ax == 1 else LENS
    if ax == 0:
        rr = np.hypot(s, t)
        port = (rr >= 1.5) & (rr < 2.3) & (depth > -G) & (depth <= DOME + 0.25)
        part[port] = PORT
        part[(rr < 1.5) & (depth > -G) & (depth <= DOME + 0.25)] = 0
        part[(rr < 1.5) & (depth > -G) & (depth <= 0.25)] = HOLLOW
        part[(rr < 1.4) & (depth > -G) & (depth <= 0)] = HOLLOW

# the cap: a stone step, the bronze collar, its crowned top
rr = np.hypot(X, Y)
part[(rr < 4.4) & (Z > TOP - 0.5) & (Z <= TOP + 1.0)] = STONE
part[(rr < 4.35) & (Z > TOP + 1.0) & (Z <= TOP + 2.5)] = BRONZE
part[(rr < 3.4) & (Z > TOP + 2.0) & (Z <= TOP + 2.5)] = CAPTOP

# the foot: a notched slab, a chamfered step, an octagonal neck
slab = (np.abs(X) <= 5.5) & (np.abs(Y) <= 5.5) & (Z <= 2.3)
for a, b in ((X, Y), (Y, X)):
    slab &= ~((np.abs(np.abs(a) - 4.25) < 0.3) & (np.abs(b) > 5.0) & (Z <= 1.8))
part[slab] = FOOT
step = (np.abs(X) <= 4.7) & (np.abs(Y) <= 4.7) & (np.abs(X) + np.abs(Y) <= 8.4) & (Z > 2.3) & (Z <= 4.0)
part[step] = FOOT
part[(octn(X, Y) <= 4.05) & (Z > 4.0) & (Z <= 4.7)] = FOOT

# the handle: posts, stepped corners, top bar (1 wide across, 1.5 deep)
hd = np.abs(Y) <= 0.75
part[hd & (np.abs(X) > 4.5) & (np.abs(X) <= 5.5) & (Z > TOP) & (Z <= 24.7)] = HANDLE
part[hd & (np.abs(X) > 3.5) & (np.abs(X) <= 4.5) & (Z > 24.7) & (Z <= 25.7)] = HANDLE
part[hd & (np.abs(X) <= 3.5) & (Z > 25.7) & (Z <= 26.7)] = HANDLE
occ = part > 0

# ---- pixel art -------------------------------------------------------------------------------------
def hashf(*a):
    h = 2166136261
    for v in a:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return (h & 0xFFFF) / 0xFFFF


STONE_PAL = [(34, 48, 72), (52, 72, 102), (68, 92, 128), (88, 114, 150), (118, 142, 174)]
BRONZE_PAL = [(78, 44, 18), (122, 76, 36), (160, 104, 52), (198, 142, 78), (232, 190, 124)]


def stone_tone(q, base=2):
    """A worn stone pixel: mostly the base tone, a few 2x2 clumps a step lighter or darker."""
    u = [math.floor(c / (T * 2)) for c in q]
    h = hashf(*u, 7)
    h2 = hashf(*[math.floor(c / T) for c in q], 3)
    k = base + (1 if h > 0.88 else -1 if h < 0.1 else 0) + (1 if h2 > 0.975 else -1 if h2 < 0.02 else 0)
    return STONE_PAL[max(0, min(4, k))]


def body_facet(q):
    """For a point on the body: (active plane index, distance to the facet's nearest edge)."""
    c = PN @ q - PD
    i = int(np.argmax(c))
    others = [(c[i] - c[j]) / (np.linalg.norm(PN[i] - PN[j]) + 1e-9) for j in range(len(PN)) if j != i
              and np.dot(PN[i], PN[j]) > 0.3]
    return i, (min(others) if others else 9)


def emblem_px(u, v):
    """The Blue Lantern emblem as pixel art, proportions measured off J's sheet (fractions of its
    radius R): outer ring 0.89-1.0, a C arc each side 0.62-0.78 reaching 55 degrees up and down,
    a short bar top and bottom (half width 0.28, 0.67-0.8) on a stem (0.49-0.67) down to an inner
    ring 0.39-0.5, and the glowing disc inside it. u, v are pixels from the centre (pixel centres
    at half-integers, so it is exactly symmetric). Returns 'line', 'disc', 'field' or None."""
    R = EMB_PX
    r = math.hypot(u, v) / R
    a = math.degrees(math.atan2(abs(v), abs(u)))
    x, y = abs(u) / R, abs(v) / R
    if r >= 1.0:
        return None
    if r >= 0.886:
        return "line"
    if r < 0.375:
        return "disc"
    if r < 0.5:
        return "line"
    if 0.622 <= r < 0.783 and a <= 55:
        return "line"
    if x < 0.286 and 0.668 <= y < 0.8:
        return "line"
    if x < 0.058 and 0.49 <= y < 0.668:
        return "line"
    return "field"


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def crown_px(u, v):
    if abs(u) <= 4.5 and -3.5 <= v <= 0:
        return True
    return any(abs(u - cx) <= (3.5 - v) * 0.42 for cx in (-4, 0, 4)) and 0 < v <= 3.5


def texel(pid, q, n, vox):
    """(srgb colour, kind 0 stone / 1 metal / 2 glow) for the texture pixel centred at q on a face
    with outward normal n of the cube at index vox."""
    x, y, z = q
    up = n[2] > 0.5
    if pid in (STONE, FRAME, HANDLE, FOOT):
        if pid == FOOT and abs(z) < 1e-6 and n[2] < -0.5 and math.hypot(x, y) < 4.8:
            r = math.hypot(x, y)       # the bronze plate underneath, turned rings and four emblems
            for ring in (4.6, 3.8, 3.3, 2.2, 1.2):
                if abs(r - ring) < T * 0.6:
                    return BRONZE_PAL[0], 1
            for a in range(4):
                if math.hypot(x - 2.9 * math.cos(a * math.pi / 2), y - 2.9 * math.sin(a * math.pi / 2)) < 0.5:
                    return STONE_PAL[3], 0
            return BRONZE_PAL[2], 1
        if pid == FOOT and n[1] > 0.5 and abs(x) < 1.6 and 2.6 < z < 3.7:
            # the nameplate on the back of the step, two engraved lines
            if abs(x) < 1.2 and (abs(z - 2.95) < T * 0.6 or abs(z - 3.35) < T * 0.6):
                return BRONZE_PAL[0], 1
            return BRONZE_PAL[3], 1
        base = 3 if up else (1 if n[2] < -0.5 else 2)
        col = stone_tone(q, base)
        if pid == STONE:
            qb = np.array([x, y, z - CZ])
            if np.all(PN @ qb <= PD + G):
                i, d = body_facet(qb)
                # each facet framed as on the sheet: a worn pale edge, a dark cut line, a light catch
                if d < T:
                    col = STONE_PAL[4]
                elif d < 2 * T and d >= T * 1.5:
                    col = STONE_PAL[0]
                elif 2 * T <= d < 3 * T:
                    col = STONE_PAL[3]
        axis = np.array([0.0, 1.0, 0.0]) if abs(y) > abs(x) else np.array([1.0, 0.0, 0.0])
        if pid in (STONE, FRAME) and abs(np.dot(n, axis)) > 0.5 and abs(z - CZ) < FR_OUT + 0.5:
            s_ = x if axis[0] == 0 else y
            k = float(octn(np.array(s_), np.array(z - CZ)))
            if k < FR_OUT + T:
                # inner lip in shadow, the frame's face, a lit bevel, a dark cut line round it
                if k < GL + T:
                    return STONE_PAL[0], 0
                if k < GL + 2 * T:
                    return STONE_PAL[4], 0
                if k < FR_OUT - T:
                    return stone_tone(q, 3), 0
                if k < FR_OUT:
                    return STONE_PAL[4], 0
                return STONE_PAL[0], 0
        if pid == FRAME:
            # the raised octagonal frame: lit face, pale top edges, shadowed sides
            axis = np.array([0.0, 1.0, 0.0]) if abs(y) > abs(x) else np.array([1.0, 0.0, 0.0])
            if abs(np.dot(n, axis)) > 0.5:
                col = STONE_PAL[3] if hashf(*[math.floor(c / T) for c in q]) > 0.08 else STONE_PAL[4]
            elif up:
                col = STONE_PAL[4]
            else:
                col = STONE_PAL[1]
        if pid == HANDLE:
            # bevelled edges: the outermost pixel row of every face catches the light
            lo = [abs(((c + 1000) % G)) for c in q]
            if any(min(l, G - l) < T * 0.6 for l, nn in zip(lo, n) if abs(nn) < 0.5):
                col = STONE_PAL[3] if up or n[2] > -0.5 else STONE_PAL[1]
        return col, 0
    if pid == EMBLEM:
        # each pixel takes the average of 4 x 4 samples inside it, so the curves get one soft
        # in-between tone at their edges (hand-drawn pixel art's anti-aliasing) instead of stairs
        s0 = x if y < 0 else -x
        t0 = z - CZ
        acc = np.zeros(3)
        for i in range(4):
            for j in range(4):
                ss = s0 + (i - 1.5) / 4 * TG
                tt = t0 + (j - 1.5) / 4 * TG
                u, v = ss / T, tt / T
                m = emblem_px(u, v)
                r = math.hypot(u, v) / EMB_PX
                if m == "line":
                    c = mix((214, 242, 255), (176, 224, 250), r)
                elif m == "disc":
                    c = mix((200, 250, 255), (64, 196, 240), (r / 0.375) ** 1.5)
                elif m == "field":
                    c = mix((60, 140, 220), (40, 104, 190), r)
                else:
                    k = float(octn(np.array(ss), np.array(tt))) / GL
                    c = mix((30, 84, 184), (12, 40, 120), (k - 0.85) / 0.15)
                acc += np.array(c) ** 2.2
        return tuple((acc / 16) ** (1 / 2.2)), 2
    if pid == LENS:
        s, t = y, z - CZ
        k = float(octn(np.array(s), np.array(t))) / GL
        if k < 0.5:
            return mix((176, 228, 255), (96, 184, 250), k / 0.5), 2
        return mix((70, 150, 240), (14, 46, 140), (k - 0.5) / 0.5), 2
    if pid == PORT:
        rr_ = math.hypot(y, z - CZ)
        if n[0] * (1 if x > 0 else -1) > 0.5:
            # the ring's face: a lit outer lip, a turned groove, a pale inner lip
            if rr_ > 2.3 - T:
                return BRONZE_PAL[2], 1
            if rr_ < 1.5 + T:
                return BRONZE_PAL[4], 1
            return BRONZE_PAL[3], 1
        return BRONZE_PAL[1], 1
    if pid == HOLLOW:
        # the cup inside the port: dark bronze, darkest at its middle
        rr_ = math.hypot(y, z - CZ)
        return mix(BRONZE_PAL[1], (40, 22, 10), 1 - rr_ / 1.5), 1
    if pid == BRONZE:
        if up:
            return BRONZE_PAL[3], 1
        if n[2] < -0.5:
            return BRONZE_PAL[0], 1
        # a turned collar in bands: a dark foot, mid body, a bright band, a lit rim
        band = z - (TOP + 1.0)
        tone = 0 if band < T else 1 if band < 3 * T else 2 if band < 4 * T else 3 if band < 5 * T else 4
        return BRONZE_PAL[tone], 1
    if pid == CAPTOP:
        r = math.hypot(x, y)
        if not up:
            return BRONZE_PAL[2], 1
        if r > 3.1:
            return BRONZE_PAL[4], 1
        if r > 2.85:
            return BRONZE_PAL[1], 1
        if r > 2.4:
            return stone_tone(q, 2), 0
        if r > 2.0:
            return BRONZE_PAL[3], 1
        if r > 1.8:
            return BRONZE_PAL[0], 1
        u, v = x / T, -y / T
        if crown_px(u, v):
            return BRONZE_PAL[4], 1
        return stone_tone(q, 1), 0
    return (255, 0, 255), 0


# ---- faces at pixel resolution --------------------------------------------------------------------
DIRS = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
        ((0, 1, 0), (0, 0, 1), (1, 0, 0)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (0, 1, 0), (1, 0, 0))]
quads, qcol, qkind = [], [], []
idx = np.argwhere(occ)
S = occ.shape
for i, j, k in idx:
    c = np.array([xs[i], xs[j], zs[k]])
    pid = int(part[i, j, k])
    for n, a, b in DIRS:
        ni, nj, nk = i + n[0], j + n[1], k + n[2]
        if 0 <= ni < S[0] and 0 <= nj < S[1] and 0 <= nk < S[2] and occ[ni, nj, nk]:
            continue
        n_, a_, b_ = np.array(n, float), np.array(a, float), np.array(b, float)
        f0 = c + n_ * G / 2
        Tp = TG if pid == EMBLEM else T
        Kp = int(round(G / Tp))
        for ta in range(Kp):
            for tb in range(Kp):
                oa = -G / 2 + (ta + 0.5) * Tp
                ob = -G / 2 + (tb + 0.5) * Tp
                q = f0 + a_ * oa + b_ * ob
                col, kind = texel(pid, q, n_, (i, j, k))
                # pixel ambient occlusion: darken a pixel where a cube sits beside it above the face
                ao = 0
                for e, oo in ((a_, oa), (b_, ob)):
                    side = np.sign(oo)
                    if abs(oo) > G / 2 - Tp * 1.01:
                        m = np.array([i, j, k]) + n_.astype(int) + (e * side).astype(int)
                        if all(0 <= m[w] < S[w] for w in range(3)) and occ[tuple(m)]:
                            ao += 1
                if kind != 2 and ao:
                    col = tuple(cc * (0.78 if ao == 1 else 0.66) for cc in col)
                corners = [q + (a_ * sa + b_ * sb) * Tp / 2 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                if np.dot(np.cross(corners[1] - corners[0], corners[2] - corners[0]), n_) < 0:
                    corners = corners[::-1]
                quads.append(corners)
                qcol.append(col)
                qkind.append(kind)
print(f"grid {G} ({int(round(16 / G))} per block): {int(occ.sum()):,} cubes, "
      f"{len(quads):,} pixel quads")

# ---- export for the Lantern Model Bench viewer: quad count, corner positions, colour + kind -----------
if "--export" in sys.argv:
    path = sys.argv[sys.argv.index("--export") + 1]
    with open(path, "wb") as f:
        f.write(np.uint32(len(quads)).tobytes())
        f.write(np.asarray(quads, np.float32).tobytes())
        f.write(np.hstack([np.clip(np.round(qcol), 0, 255), np.array(qkind)[:, None]]).astype(np.uint8).tobytes())
    print("exported", path, os.path.getsize(path), "bytes")

# ---- Blender ---------------------------------------------------------------------------------------
import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
verts = np.array(quads).reshape(-1, 3)
faces = np.arange(len(verts)).reshape(-1, 4)
me = bpy.data.meshes.new("lantern")
me.from_pydata(verts.tolist(), [], faces.tolist())
lin = (np.array(qcol) / 255) ** 2.2
attr = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
cols = np.repeat(lin, 4, axis=0)
attr.data.foreach_set("color", np.hstack([cols, np.ones((len(cols), 1))]).ravel())


def mat(name, metal, glow):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute")
    at.attribute_name = "col"
    L.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45 if metal else 0.9
    bsdf.inputs["Metallic"].default_value = 0.75 if metal else 0.0
    if glow:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        for l in list(bsdf.inputs["Base Color"].links):
            L.remove(l)
        L.new(at.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.2
    return m


for m in (mat("stone", False, False), mat("metal", True, False), mat("glow", False, True)):
    me.materials.append(m)
me.polygons.foreach_set("material_index", qkind)
obj = bpy.data.objects.new("lantern", me)
scene.collection.objects.link(obj)

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.43, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5


def area(name, loc, power, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.size = size
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 12)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("key", (-28, -40, 40), 14000, 30)
area("fill", (35, -25, 12), 3500, 30)
area("rim", (10, 40, 30), 6000, 25)
scene.render.engine = "CYCLES"
scene.cycles.samples = 12 if FAST else 32
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam = bpy.data.objects.new("cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
SIZE = 341
scene.render.resolution_x = scene.render.resolution_y = SIZE
# the sheet's tiles are 341 px at 12 px per unit with the ground at 332 px: match that framing
cam_d.ortho_scale = SIZE / 12.0
TARGET = Vector((0, 0, (332.5 - SIZE / 2) / 12.0))
VIEWS = [("FRONT", 0, 0), ("BACK", 180, 0), ("TOP", 0, 90), ("LEFT", -90, 0), ("RIGHT", 90, 0),
         ("BOTTOM", 0, -90), ("FRONT LEFT", -40, 14), ("FRONT RIGHT", 40, 14), ("BACK RIGHT", 140, 14)]
work = os.path.dirname(OUT)
TAG = os.path.splitext(os.path.basename(OUT))[0]
tiles = []
for label, yaw, pitch in VIEWS:
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    tgt = TARGET if abs(pitch) < 80 else Vector((0, 0, 12))
    cam.location = tgt + d * 80
    if abs(pitch) >= 80:
        cam.rotation_euler = (0, 0, 0) if pitch > 0 else (math.pi, 0, 0)
    else:
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    scene.render.film_transparent = label in ("FRONT", "LEFT")
    path = os.path.join(work, f"{TAG}_{label.replace(' ', '_')}.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    tiles.append((label, path))

# a close-up of the front window
cam_d.ortho_scale = 11
cam.location = Vector((0, -80, CZ))
cam.rotation_euler = (Vector((0, 1, 0))).to_track_quat("-Z", "Y").to_euler()
scene.render.film_transparent = False
scene.render.resolution_x = scene.render.resolution_y = 480
scene.render.filepath = os.path.join(work, f"{TAG}_closeup.png")
bpy.ops.render.render(write_still=True)
scene.render.resolution_x = scene.render.resolution_y = SIZE

# ---- compare with the sheet ------------------------------------------------------------------------
from PIL import Image, ImageDraw

sheet = Image.open(SHEET).convert("RGB")


def sheet_mask(tile_rc):
    r, c = tile_rc
    t = np.asarray(sheet.crop((c * SIZE, r * SIZE, (c + 1) * SIZE, (r + 1) * SIZE))).astype(int)
    chroma = t.max(2) - t.min(2)
    m = (chroma > 14) | (t.mean(2) < 80)
    m[:40] = False
    return m


scores = []
for (label, path), rc in (((tiles[0]), (0, 0)), ((tiles[3]), (1, 0))):
    ours = np.asarray(Image.open(path).convert("RGBA"))[..., 3] > 128
    theirs = sheet_mask(rc)
    iou = (ours & theirs).sum() / max(1, (ours | theirs).sum())
    scores.append((label, iou))
    print(f"{label} silhouette match (intersection over union): {iou:.1%}")

grid = Image.new("RGB", (SIZE * 3, SIZE * 3), (107, 109, 115))
for i, (label, path) in enumerate(tiles):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (107, 109, 115, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    if label in ("FRONT", "LEFT"):
        # the sheet's outline in red over our render
        rc = (0, 0) if label == "FRONT" else (1, 0)
        m = sheet_mask(rc)
        edge = m ^ np.roll(m, 1, 0) | m ^ np.roll(m, 1, 1)
        a = np.asarray(im).copy()
        a[edge] = (255, 40, 40)
        im = Image.fromarray(a)
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), label + (f"  match {dict(scores)[label]:.0%}" if label in dict(scores) else ""), fill=(255, 255, 255))
    grid.paste(im, ((i % 3) * SIZE, (i // 3) * SIZE))
sh = sheet.resize((int(sheet.width * SIZE * 3 / sheet.height), SIZE * 3))
both = Image.new("RGB", (sh.width + grid.width, SIZE * 3))
both.paste(sh, (0, 0))
both.paste(grid, (sh.width, 0))
both.save(OUT)
print("wrote", OUT)
