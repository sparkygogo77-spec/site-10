"""Fallen Titan, round 3: one boss through the whole Titan (J, 2026-10-19: "One boss, whole Titan ★").

After two rounds of room bosses were turned down, J picked one huge thing that killed the Titan, still living inside
it and hunting you room to room. Three takes, each shown two ways (the whole Titan cut open from above, and a close
shot inside the chest), with a 1.8-block player for scale:

  K1 the Gnawer        an 80-block fear centipede threaded through the body: boot, leg, chest, out along the arm
  K2 the Hollow Lantern a gaunt Yellow Lantern wraith (9 blocks) who killed the Titan's pilot, with fear constructs
  K3 the Fear Seed     a giant made of hundreds of yellow construct cubes, streams of cubes running down the limbs

The Titan: a 60-block hollow construct lying face-down in a valley (one boot sunk in mud, one arm broken), its shell
3 blocks thick, dead green seams.

blender.exe -b --python titan_killer_blend.py -- <out.blend> [--no-render]
"""
import math, os, sys
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
RENDER = "--no-render" not in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
K.sc = sc
box, seg, mat, pmat, cmat = K.box, K._seg, K.mat, K.pixel_mat, K.construct_mat
M = dict(
    titan=pmat("titan stone", (0.28, 0.29, 0.31), (0.50, 0.51, 0.53)),
    inner=pmat("titan inner", (0.10, 0.10, 0.12), (0.22, 0.22, 0.25)),
    cut=pmat("titan cut", (0.18, 0.18, 0.20), (0.32, 0.32, 0.34)),
    grass=pmat("valley grass", (0.12, 0.25, 0.07), (0.25, 0.42, 0.13)),
    mud=pmat("mud", (0.12, 0.08, 0.05), (0.26, 0.18, 0.11), 0.6),
    seam=mat("dead green seam", (0.15, 0.5, 0.25), 0.3, (0.2, 0.8, 0.35), 0.5),
    chitin=pmat("fear chitin", (0.03, 0.03, 0.03), (0.12, 0.11, 0.09), 0.3),
    yellow=cmat("yellow hard light", 1.2, 0.75),
    yseam=mat("yellow glow", (1, 0.78, 0.15), 0.3, (1, 0.72, 0.08), 1.5),
    cloak=pmat("wraith cloak", (0.03, 0.03, 0.04), (0.10, 0.09, 0.11), 0.9),
    bone=pmat("wraith bone", (0.55, 0.52, 0.45), (0.80, 0.77, 0.68), 0.6),
    heart=mat("dead lantern-heart", (0.1, 0.4, 0.2), 0.3, (0.2, 0.7, 0.35), 0.6),
)
MI = {k: i for i, k in enumerate(M)}
cams = []

# ------------------------------------------------------------------ the Titan, lying face-down along +x
TX, TY, TZ = 80, 26, 50


def titan_grid():
    xs = np.arange(TX)[:, None, None].astype(float); ys = np.arange(TY)[None, :, None].astype(float); zs = np.arange(TZ)[None, None, :].astype(float) - TZ / 2
    yc = 10.0
    outer = np.zeros((TX, TY, TZ), bool); inner = np.zeros_like(outer)

    def ell(cx, cy, cz, rx, ry, rz, shell=3.0):
        o = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 + ((zs - cz) / rz) ** 2 <= 1
        i = ((xs - cx) / max(1, rx - shell)) ** 2 + ((ys - cy) / max(1, ry - shell)) ** 2 + ((zs - cz) / max(1, rz - shell)) ** 2 <= 1
        return o, i

    def tube(x0, x1, cz, r, cy=yc, shell=3.0):
        span = (xs >= x0) & (xs <= x1)
        d = np.sqrt((ys - cy) ** 2 + (zs - cz) ** 2)
        return span & (d <= r), span & (d <= r - shell)
    parts = []
    for sz in (-6.5, 6.5):                       # legs (shin and thigh), boots at x 0-6
        parts.append(tube(5, 26, sz, 5.5))
    parts.append(ell(3, 7, -6.5, 5, 7, 6.5))     # left boot, sunk lower in the mud
    parts.append(ell(3, 9, 6.5, 5, 7, 6.5))
    parts.append(ell(29, yc, 0, 7, 8, 10))       # pelvis
    parts.append(ell(39, yc, 0, 10, 9.5, 14))    # chest, wide at the shoulders
    for sz in (-1, 1):
        parts.append(ell(45, yc, sz * 14, 5, 6, 5))   # shoulders
        parts.append(ell(15, yc, sz * 6.5, 4, 6.5, 6.5, shell=2.5))   # knees
    parts.append(tube(48, 51, 0, 4))             # neck
    parts.append(ell(56, yc + 1, 0, 6, 6.5, 6))  # head
    parts.append(ell(76, yc - 1, 16, 4, 5, 5))   # fists
    parts.append(ell(76, yc - 1, -16, 4, 5, 5))
    for sz in (-16, 16):                          # arms stretched forward past the head
        parts.append(tube(42, 74, sz, 4.5, cy=yc - 1))
    for o, i in parts:
        outer |= o; inner |= i
    # connect the rooms: open passages from leg to pelvis, chest to arms and head
    for o, i in (tube(20, 30, -6.5, 2.5), tube(20, 30, 6.5, 2.5), tube(46, 52, 0, 2.5), ):
        inner |= i
    for sz in (-1, 1):
        inner |= (xs >= 40) & (xs <= 48) & (np.abs(zs - sz * 11) <= 3.5) & (np.abs(ys - (yc - 1)) <= 2.5)
    shell = outer & ~inner
    broken = (xs >= 58) & (xs <= 63) & (zs > 8)    # the right arm is snapped
    shell &= ~broken
    shell &= ys > 1
    return shell, inner & ~broken


SHELL, INNER = titan_grid()


def titan(name, origin, cut_y=None):
    s = SHELL.copy()
    if cut_y is not None:
        s[:, cut_y:, :] = False

    def mf(i, n, a, d):
        X, Y, Z = s.shape
        ni = np.clip(n, 0, [X - 1, Y - 1, Z - 1])
        into_inner = INNER[ni[:, 0], ni[:, 1], ni[:, 2]] & (n[:, 0] >= 0) & (n[:, 1] >= 0) & (n[:, 2] >= 0) & (n[:, 0] < X) & (n[:, 1] < Y) & (n[:, 2] < Z)
        cut_face = (a == 1) & (d == 1) & (i[:, 1] == (cut_y - 1 if cut_y else -9))
        return np.where(cut_face, MI["cut"], np.where(into_inner, MI["inner"], MI["titan"]))
    o = K.voxel_mesh(name, s, mf, list(M.values()))
    o.location = origin + Vector((0, TZ / 2, 0))
    # dead seams down the back, and the valley floor with mud round the sunk boot
    rng = np.random.default_rng(3)
    for k in range(10):
        a = origin + Vector((8 + k * 6.5, rng.uniform(-6, 6), 19.5 if cut_y is None else cut_y))
        seg(f"{name} seam{k}", a, a + Vector((4, rng.uniform(-3, 3), 0)), 0.35, M["seam"], None)
    bpy.ops.mesh.primitive_plane_add(size=160, location=tuple(origin + Vector((40, 0, 1))))
    p = bpy.context.object; p.name = f"{name} valley"; p.data.materials.append(M["grass"])
    bpy.ops.mesh.primitive_plane_add(size=22, location=tuple(origin + Vector((3, 6.5, 1.05))))
    p = bpy.context.object; p.name = f"{name} mud"; p.data.materials.append(M["mud"])
    K._blob(f"{name} lantern-heart", tuple(origin + Vector((38, 0, 9))), (4, 4, 5), M["heart"], None)
    return o


def W(origin, x, y, z):
    """Titan grid (x along the body, y up, z across) to Blender."""
    return origin + Vector((x, -z, y))


# ------------------------------------------------------------------ K1 the Gnawer
GNAW_PATH = [(1, 6, 6.5), (8, 9, 6.5), (18, 10, 6.5), (26, 10, 5), (32, 9, 1), (38, 8, -3), (43, 9, -9), (48, 9, -16), (56, 9, -16), (66, 9, -16), (72, 9, -16)]
# coiled on the floor with its front third raised to strike (the hero shot)
HERO_PATH = [(-18, 2.5, 10), (-8, 2.5, 14), (2, 2.5, 8), (4, 2.5, -2), (-4, 2.5, -9), (-14, 2.5, -6), (-12, 2.5, 3), (-4, 5, 4), (2, 10, 2), (6, 14, 0), (9, 15, 0)]


def gnawer(origin, root_name, path=None, head_at=22):
    root = K.empty(root_name, tuple(origin))
    path = path or GNAW_PATH
    pts = [Vector(p) for p in path]
    dense = []
    for i in range(len(pts) - 1):
        for j in range(4):
            dense.append(pts[i].lerp(pts[i + 1], j / 4))
    head_at = min(head_at, len(dense) - 1)
    for i, c in enumerate(dense):
        w = 4.0 if i != head_at else 5.5
        q = W(Vector((0, 0, 0)), c.x, c.y, c.z)
        K._blob(f"{root_name} seg{i}", tuple(q), (w, w, w * 0.8), M["chitin"], root)
        box(f"{root_name} band{i}", tuple(q), (w * 1.05, 0.7, w * 0.9), M["yseam"], root)
        for sx in (-1, 1):                         # legs
            d_ = (dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]); d_.y = 0
            side = Vector((-d_.z, 0, d_.x)).normalized() * sx if d_.length > 0 else Vector((0, 0, sx))
            a = c + side * w * 0.45
            k1 = a + side * 2.2 + Vector((0, 1.0, 0))
            f = a + side * 3.2 + Vector((0, -2.0, 0))
            seg(f"{root_name} leg{i}{sx}a", W(Vector((0, 0, 0)), *a), W(Vector((0, 0, 0)), *k1), 0.45, M["chitin"], root)
            seg(f"{root_name} leg{i}{sx}b", W(Vector((0, 0, 0)), *k1), W(Vector((0, 0, 0)), *f), 0.35, M["yseam"], root)
    h = dense[head_at]
    hq = W(Vector((0, 0, 0)), h.x, h.y, h.z)
    for sx in (-1, 1):
        seg(f"{root_name} mandible{sx}", hq + Vector((1.5, sx * 1.5, 0)), hq + Vector((5, sx * 0.6, -0.8)), 1.0, M["yseam"], root)
    box(f"{root_name} eyes", tuple(hq + Vector((2.2, 0, 1.2))), (0.8, 3.0, 0.8), M["yseam"], root)
    return root


# ------------------------------------------------------------------ K2 the Hollow Lantern
def hollow_lantern(origin, root_name, at):
    """Hunched and gaunt: a cloak of long torn strips, bone arms to its knees, a caged lantern for a skull."""
    root = K.empty(root_name, tuple(origin + at))
    root.scale = (1.35, 1.35, 1.35)
    lean = Vector((0, -1.2, 0))
    seg(f"{root_name} spine", Vector((0, 0, 2.5)), Vector((0, 0, 8)) + lean, 0.9, M["bone"], root)
    for k in range(5):
        box(f"{root_name} rib{k}", tuple(Vector((0, 0, 4.2 + k * 0.75)) + lean * (k / 5)), (2.0, 0.5, 0.25), M["bone"], root)
    rng = np.random.default_rng(9)
    for k in range(24):   # torn cloak strips from the shoulders to the floor, ragged ends
        a = k / 24 * math.tau
        top = Vector((math.cos(a) * 1.5, math.sin(a) * 1.1, 8.0)) + lean
        mid = Vector((math.cos(a) * 2.4, math.sin(a) * 1.9, 4.0)) + lean * 0.4
        bot = Vector((math.cos(a) * 2.8 + rng.uniform(-0.4, 0.4), math.sin(a) * 2.3, rng.uniform(0.0, 1.8)))
        seg(f"{root_name} cloak{k}a", top, mid, 0.55, M["cloak"], root)
        seg(f"{root_name} cloak{k}b", mid, bot, 0.5, M["cloak"], root)
    sk = Vector((0, -1.6, 9.0))
    box(f"{root_name} skull light", tuple(sk), (1.3, 1.3, 1.5), M["yseam"], root)
    box(f"{root_name} skull cage", tuple(sk), (1.8, 1.8, 2.0), M["cloak"], root, wire=0.16)
    box(f"{root_name} skull cap", tuple(sk + Vector((0, 0, 1.15))), (2.0, 2.0, 0.35), M["cloak"], root)
    seg(f"{root_name} hook", sk + Vector((0, 0, 1.3)), sk + Vector((0, 0.4, 2.3)), 0.25, M["cloak"], root)
    for sx in (-1, 1):
        box(f"{root_name} eye{sx}", tuple(sk + Vector((sx * 0.35, -0.95, 0.2))), (0.3, 0.1, 0.5), M["cloak"], root)
    for sx in (-1, 1):   # long arms hanging to the knees, claws open
        sh = Vector((sx * 1.6, -1.0, 7.6)); el = sh + Vector((sx * 1.4, -1.6, -3.0)); wr = el + Vector((sx * 0.3, -1.4, -2.8))
        seg(f"{root_name} arm{sx}a", sh, el, 0.42, M["bone"], root); seg(f"{root_name} arm{sx}b", el, wr, 0.38, M["bone"], root)
        for f in range(4):
            seg(f"{root_name} claw{sx}{f}", wr, wr + Vector((sx * (f - 1.5) * 0.35, -1.0, -1.4)), 0.14, M["bone"], root)
    for k in range(10):   # its fear-ring constructs: blades circling it
        a = k / 10 * math.tau
        c = Vector((math.cos(a) * 4.8, math.sin(a) * 4.8, 5.5 + math.sin(a * 2) * 0.8))
        b = box(f"{root_name} blade{k}", tuple(c), (0.25, 2.0, 0.55), M["yellow"], root)
        b.rotation_euler = (0, 0, a)
    return root


# ------------------------------------------------------------------ K3 the Fear Seed
def fear_seed(origin, root_name, at):
    root = K.empty(root_name, tuple(origin + at))
    rng = np.random.default_rng(12)
    def cloud(c, r, n, size):
        for k in range(n):
            off = Vector(tuple(rng.normal(0, 1, 3))); off = off.normalized() * (r * rng.random() ** 0.5)
            q = size * rng.uniform(0.6, 1.2)
            b = box(f"{root_name} cube", tuple(c + off), (q, q, q), M["yellow"] if rng.random() < 0.8 else M["yseam"], root)
            b.rotation_euler = tuple(rng.uniform(0, 1, 3))
    # a hunched giant made of cubes: short legs, a big torso, long knuckle-dragging arms, a low head
    cloud(Vector((0, 0, 8)), 3.8, 220, 0.75)       # torso
    cloud(Vector((1.5, 0, 11.5)), 2.6, 80, 0.7)    # shoulders
    cloud(Vector((3.6, 0, 11.2)), 1.9, 60, 0.6)    # head, thrust forward
    for sx in (-1, 1):
        for t in np.linspace(0, 1, 6):             # legs
            cloud(Vector((-1.0, sx * 2.0, 4.5 - t * 4.2)), 1.3, 10, 0.6)
        for t in np.linspace(0, 1, 12):            # arms, shoulder to knuckles on the floor
            cloud(Vector((1.5 + t * 3.5, sx * (3.6 + t * 1.0), 11.5 - t * 10.8)), 1.0 - t * 0.3, 7, 0.55)
    for sx in (-1, 1):
        box(f"{root_name} eye{sx}", (5.3, sx * 0.6, 11.6), (0.4, 0.5, 0.35), M["yseam"], root)
    return root


def streams(origin, name):
    """Cube streams running down the limbs (K3): the seed is spreading through the Titan."""
    rng = np.random.default_rng(13)
    for path in (((36, 9, 0), (24, 10, 6.5), (6, 9, 6.5)), ((36, 9, 0), (24, 10, -6.5), (6, 8, -6.5)),
                 ((40, 9, 0), (46, 9, 16), (70, 9, 16)), ((40, 9, 0), (46, 9, -16), (58, 9, -16))):
        pts = [Vector(p) for p in path]
        for i in range(len(pts) - 1):
            for t in np.linspace(0, 1, 18):
                c = pts[i].lerp(pts[i + 1], t) + Vector(tuple(rng.normal(0, 0.8, 3)))
                q = rng.uniform(0.3, 0.6)
                box(f"{name} stream cube", tuple(W(origin, c.x, c.y, c.z)), (q, q, q), M["yellow"], None).rotation_euler = tuple(rng.uniform(0, 1, 3))


# ------------------------------------------------------------------ lay out: each take gets the cut-open Titan
TAKES = [("K1", "the Gnawer"), ("K2", "the Hollow Lantern"), ("K3", "the Fear Seed")]
CUT = 12
for ti, (code, nm) in enumerate(TAKES):
    o = Vector((ti * 250.0, 0, 0))
    titan(f"{code} titan", o, cut_y=CUT)
    chest = W(o, 38, 3, 0)
    if code == "K1":
        g = gnawer(o, f"{code} {nm}")
        g.location = o
    elif code == "K2":
        hollow_lantern(o, f"{code} {nm}", W(Vector((0, 0, 0)), 39, 3, -2))
    else:
        fear_seed(o, f"{code} {nm}", W(Vector((0, 0, 0)), 37, 3, 0))
        streams(o, f"{code}")
    K.player(f"{code} player", tuple(W(o, 30, 3, 3)))
    cams.append(K.camera(f"{len(cams) + 1:02d} {code} {nm} whole Titan", tuple(o + Vector((36, -62, 62))), tuple(o + Vector((38, 0, 6))), 30))
    # the hero shot: the killer alone on Titan stone beside you, well lit
    hp = o + Vector((0, -150, 0))
    bpy.ops.mesh.primitive_plane_add(size=70, location=tuple(hp + Vector((0, 0, 0))))
    pl_ = bpy.context.object; pl_.name = f"{code} hero floor"; pl_.data.materials.append(M["inner"])
    if code == "K1":
        gnawer(hp, f"{code} {nm} hero", path=HERO_PATH, head_at=40)
        tgt = hp + Vector((-2, 0, 6))
    elif code == "K2":
        hollow_lantern(hp, f"{code} {nm} hero", Vector((0, 0, 0)))
        tgt = hp + Vector((0, 0, 6.5))
    else:
        fear_seed(hp, f"{code} {nm} hero", Vector((0, 0, 0)))
        tgt = hp + Vector((1, 0, 5))
    K.player(f"{code} hero player", tuple(hp + Vector((-6, -9, 0))))
    d_ = 1.7 if code == "K1" else 1.0
    cams.append(K.camera(f"{len(cams) + 1:02d} {code} {nm} hero", tuple(tgt + Vector((22, -30, 7)) * d_), tuple(tgt), 32))
    K.light(f"{code} hero key", tuple(hp + Vector((25, -30, 35))), 30000, (1, 0.95, 0.88), "AREA", 30)
    K.light(f"{code} hero rim", tuple(hp + Vector((-25, 25, 20))), 30000, (0.6, 0.75, 1.0), "AREA", 25)
    K.light(f"{code} sun", tuple(o + Vector((30, -60, 120))), 300000, (1, 0.95, 0.88), "AREA", 120)
    K.light(f"{code} chest glow", tuple(W(o, 37, 11, 0)), 6000, (1, 0.8, 0.35))
    K.light(f"{code} chest fill", tuple(W(o, 28, 8, 4)), 900, (0.7, 0.8, 1.0))

w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.45, 0.62, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
except Exception as e:
    print("world", e)
sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.cycles.use_denoising = True; sc.cycles.use_preview_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences
for dt in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dt; prefs.get_devices()
        if any(dv.type == dt for dv in prefs.devices):
            for dv in prefs.devices:
                dv.use = dv.type == dt
            sc.cycles.device = "GPU"; break
    except TypeError:
        continue
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "Standard"
sc.camera = cams[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if RENDER:
    rdir = os.path.join(os.path.dirname(OUT), "renders_titan_killer")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("done", OUT)
