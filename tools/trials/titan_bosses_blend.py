"""Fallen Titan room bosses, round 2: six new bosses as voxel-style renders in their rooms (J, 2026-10-19).

J on round 1 (six drawn concepts): "These are awful", then via coordinator 3 "I need better concepts", then
"New bosses, not these six". Each boss is a clear silhouette in its room, two variants each, a 1.8-block player for
scale.

blender.exe -b --python titan_bosses_blend.py -- <out.blend> [--no-render]

  B1 Boot Hermit    boot    a giant crab wearing a broken Titan toe-plate as its shell. V1 mud crab, V2 hard-light claws
  B2 Piston Wyrm    leg     a segmented worm running up and down the hollow shin.  V1 Titan stone, V2 yellow fear
  B3 Heart Moth     chest   a moth drawn to the dead lantern-heart.               V1 dust moth, V2 stained glass
  B4 The Grasp      arm     the Titan's severed hand crawling on its fingers.     V1 stone, V2 red rage
  B5 Carrion King   spine   a vulture nesting on the Titan's back.                V1 feathered, V2 bone construct
  B6 Gilded Queen   neck    a wasp queen in a hive of stolen lantern gold.        V1 orange greed, V2 yellow fear
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
    titan=pmat("titan stone", (0.30, 0.31, 0.33), (0.52, 0.53, 0.55)),
    titan_dark=pmat("titan stone dark", (0.12, 0.12, 0.14), (0.25, 0.25, 0.28)),
    mud=pmat("mud", (0.12, 0.08, 0.05), (0.26, 0.18, 0.11), 0.6),
    chitin=pmat("crab chitin", (0.18, 0.09, 0.05), (0.40, 0.20, 0.10), 0.5),
    moss=pmat("moss", (0.10, 0.18, 0.06), (0.22, 0.34, 0.12)),
    green=cmat("green hard light", 1.2, 0.7),
    seam=mat("green seam", (0.3, 1.0, 0.45), 0.3, (0.3, 1.0, 0.45), 1.4),
    yellow=cmat("yellow hard light", 1.2, 0.75),
    yseam=mat("yellow seam", (1, 0.8, 0.2), 0.3, (1, 0.75, 0.1), 1.4),
    black=pmat("black chitin", (0.02, 0.02, 0.025), (0.08, 0.08, 0.1), 0.25),
    dust=pmat("dust wing", (0.22, 0.19, 0.15), (0.45, 0.40, 0.33), 0.9),
    eyespot=mat("eye spot", (0.05, 0.04, 0.03), 0.8),
    eyering=mat("eye ring", (0.8, 0.6, 0.3), 0.7),
    glass=mat("stained glass", (0.3, 0.9, 0.5), 0.05, (0.3, 0.9, 0.4), 0.6, alpha=0.45),
    glass2=mat("stained glass gold", (1.0, 0.75, 0.2), 0.05, (1.0, 0.7, 0.15), 0.6, alpha=0.45),
    lead=mat("lead lines", (0.03, 0.03, 0.03), 0.4),
    fur=pmat("moth fur", (0.30, 0.27, 0.22), (0.55, 0.50, 0.42), 1.0),
    red=mat("red rage", (1.0, 0.12, 0.08), 0.3, (1.0, 0.1, 0.05), 1.5),
    redstone=pmat("rage stone", (0.10, 0.05, 0.05), (0.24, 0.12, 0.11)),
    feather=pmat("feathers", (0.06, 0.05, 0.05), (0.20, 0.17, 0.16), 0.9),
    skin=pmat("bald head", (0.45, 0.18, 0.15), (0.65, 0.30, 0.25), 0.6),
    beak=pmat("beak", (0.55, 0.50, 0.35), (0.80, 0.75, 0.55), 0.4),
    bone=pmat("bone", (0.70, 0.67, 0.58), (0.92, 0.90, 0.82), 0.6),
    gold=pmat("hive gold", (0.45, 0.28, 0.05), (0.85, 0.62, 0.18), 0.35),
    orange=mat("orange greed", (1.0, 0.45, 0.05), 0.3, (1.0, 0.4, 0.02), 1.4),
    wing=mat("wasp wing", (0.8, 0.85, 0.9), 0.05, alpha=0.35),
    eye=mat("eyes", (1, 0.8, 0.1), 0.3, (1, 0.75, 0.05), 1.5),
    eyer=mat("eyes red", (1, 0.15, 0.1), 0.3, (1, 0.1, 0.05), 1.5),
    heart=mat("lantern heart", (0.2, 0.9, 0.4), 0.3, (0.2, 0.9, 0.4), 1.5),
)
cams = []


def V(*a):
    return Vector(a)


def room_mesh(name, solid, origin, mat_fn):
    o = K.voxel_mesh(name, solid, mat_fn, list(M.values()))
    o.location = origin
    return o


MI = {k: i for i, k in enumerate(M)}


def const(key):
    return lambda i, n, a, d: np.full(len(i), MI[key])


def legs_from(root, base, n, side_len, drop, thick, m, spread=(-40, 40), side=1, ground=0.0, prefix="leg"):
    """n legs on one side: up-out to a knee, down to the ground."""
    for k in range(n):
        ang = math.radians(spread[0] + (spread[1] - spread[0]) * k / max(1, n - 1))
        hip = base + V(side * 0.3 * side_len, math.sin(ang) * side_len * 0.25, 0)
        dirn = V(side * math.cos(ang), math.sin(ang), 0)
        knee = hip + dirn * side_len * 0.55 + V(0, 0, drop * 0.5)
        foot = hip + dirn * side_len + V(0, 0, 0)
        foot.z = ground
        seg(f"{root.name} {prefix}{side}{k}a", hip, knee, thick, m, root)
        seg(f"{root.name} {prefix}{side}{k}b", knee, foot, thick * 0.75, m, root)


# ======================================================================== B1 Boot Hermit
def boot_room(ox, oy):
    X, Y, Z = 90, 45, 80
    xs = np.arange(X)[:, None, None] - X / 2; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :] - Z / 2
    inside = (xs / 40) ** 2 + (zs / 34) ** 2 < 1
    solid = (~inside & (ys < 42)) | (ys < 3)
    solid[:, :, int(Z / 2 + 8):] = False                # open toward the camera
    mud = np.broadcast_to(ys < 3, solid.shape)

    def mf(i, n, a, d):
        own_mud = mud[np.clip(i[:, 0], 0, X - 1), np.clip(i[:, 1], 0, Y - 1), np.clip(i[:, 2], 0, Z - 1)]
        return np.where(own_mud, MI["mud"], MI["titan"])
    room_mesh("B1 boot room", solid, V(ox - X / 2, oy + Z / 2, 0), mf)
    bpy.ops.mesh.primitive_plane_add(size=78, location=(ox, oy, 3.05))
    p = bpy.context.object; p.name = "B1 mud pool"; p.data.materials.append(mat("mud water", (0.1, 0.07, 0.04), 0.08))


def boot_hermit(var, p):
    root = K.empty(f"B1 Boot Hermit {var}", tuple(p))
    claw_m = M["green"] if var == "V2" else M["chitin"]
    base = V(0, 0, 6)
    K._blob(root.name + " body", tuple(base), (16, 11, 6), M["chitin"], root)
    # the shell: a broken Titan toe-plate, riveted, with a dead green crack, moss on top
    box(root.name + " toe plate", tuple(base + V(0, 3, 6.5)), (21, 17, 7), M["titan"], root).rotation_euler = (math.radians(-8), 0, 0)
    box(root.name + " toe cap", tuple(base + V(0, -4.5, 6)), (19, 6, 6), M["titan_dark"], root).rotation_euler = (math.radians(-25), 0, 0)
    for k in range(6):
        box(root.name + f" rivet {k}", tuple(base + V(-8 + k * 3.2, -7.4, 6.5)), (1, 1, 1), M["titan_dark"], root)
    seg(root.name + " crack", base + V(-7, 0, 10.2), base + V(6, 8, 10.4), 0.5, M["seam"] if var == "V1" else M["seam"], root)
    box(root.name + " moss", tuple(base + V(2, 5, 10.4)), (12, 8, 0.8), M["moss"], root)
    # eyes on stalks
    for sx in (-1, 1):
        seg(root.name + f" stalk{sx}", base + V(sx * 2.5, -5, 2.5), base + V(sx * 3.2, -6.5, 6), 0.7, M["chitin"], root)
        box(root.name + f" eye{sx}", tuple(base + V(sx * 3.2, -6.6, 6.4)), (1.4, 1.4, 1.4), M["eye"], root)
    # claws: the right one huge
    for sx, scale in ((-1, 0.7), (1, 1.15)):
        sh = base + V(sx * 6, -5, 0)
        el = sh + V(sx * 6 * scale, -6 * scale, 2 * scale)
        wr = el + V(sx * 1 * scale, -6 * scale, 1 * scale)
        seg(root.name + f" arm{sx}a", sh, el, 2.6 * scale, M["chitin"], root)
        seg(root.name + f" arm{sx}b", el, wr, 2.8 * scale, claw_m, root)
        box(root.name + f" claw{sx} hand", tuple(wr + V(0, -2.5 * scale, 0)), (5 * scale, 6 * scale, 4 * scale), claw_m, root)
        seg(root.name + f" claw{sx} top", wr + V(0, -4.5 * scale, 1.2 * scale), wr + V(-sx * 1.5 * scale, -10 * scale, 2.5 * scale), 2.2 * scale, claw_m, root)
        seg(root.name + f" claw{sx} bottom", wr + V(0, -4.5 * scale, -1.2 * scale), wr + V(-sx * 1 * scale, -9 * scale, -1.5 * scale), 1.8 * scale, claw_m, root)
        if var == "V2":
            box(root.name + f" claw{sx} seam", tuple(wr + V(0, -2.5 * scale, 0)), (5.1 * scale, 6.1 * scale, 4.1 * scale), M["seam"], root, wire=0.18)
    for sx in (-1, 1):
        legs_from(root, base + V(0, 3, -1), 4, 18, 6, 1.4, M["chitin"], spread=(-15, 55), side=sx, ground=-6 + 3)


# ======================================================================== B2 Piston Wyrm
def leg_room(ox, oy):
    X, Y, Z = 60, 110, 60
    xs = np.arange(X)[:, None, None] - X / 2; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :] - Z / 2
    rr = np.sqrt(xs ** 2 + zs ** 2)
    solid = ((rr > 20) & (rr < 27)) | ((ys < 3) & (rr < 27))
    solid &= np.broadcast_to(zs < 2, solid.shape)       # cut in half toward the camera
    room_mesh("B2 shin shaft", solid, V(ox - X / 2, oy + Z / 2, 0), const("titan"))
    for k in range(3):                                  # ledges you climb
        box(f"B2 ledge {k}", (ox - 17 + k * 6, oy + 4, 15 + k * 28), (8, 8, 1.5), M["titan_dark"], None)


def piston_wyrm(var, p):
    root = K.empty(f"B2 Piston Wyrm {var}", tuple(p))
    body_m = M["black"] if var == "V2" else M["titan"]
    ring_m = M["yseam"] if var == "V2" else M["seam"]
    n = 30
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = t * math.tau * 1.6
        pts.append(V(math.cos(a) * 12, math.sin(a) * 6 + 2, 8 + t * 80))
    # a continuous body: overlapping rounded segments, a glowing band round every second joint
    dense = []
    for i in range(n - 1):
        for j in range(3):
            dense.append(pts[i].lerp(pts[i + 1], j / 3))
    for i, c in enumerate(dense):
        u = i / len(dense)
        w = 7.5 - 3.5 * abs(u - 0.65)
        d_ = (dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]).normalized()
        K._blob(root.name + f" seg{i}", tuple(c), (w, w, w), body_m, root)
        if i % 6 == 0:
            box(root.name + f" band{i}", tuple(c), (w * 1.12, 1.1, w * 1.12), ring_m, root, along=d_)
        if var == "V2" and i % 3 == 0:
            out = (c - V(0, 2, c.z)); out.z = 0
            out = out.normalized() if out.length > 0.1 else V(1, 0, 0)
            seg(root.name + f" spine{i}", c + out * w * 0.4, c + out * (w * 0.4 + 3.5) + V(0, 0, 1.5), 0.9, M["yseam"], root)
    head = pts[-1]
    d = (pts[-1] - pts[-2]).normalized()
    box(root.name + " head", tuple(head + d * 3), (8, 7, 8), body_m, root, along=d)
    for sx in (-1, 1):   # mandibles
        seg(root.name + f" mandible{sx}", head + d * 5 + V(sx * 3, 0, 0), head + d * 9 + V(sx * 1, -2, -1), 1.4, ring_m, root)
    box(root.name + " eye slit", tuple(head + d * 6.5 + V(0, -3.6, 1)), (6, 0.6, 1.2), M["eye"] if var == "V2" else M["seam"], root)


# ======================================================================== B3 Heart Moth
def chest_room(ox, oy):
    X, Y, Z = 110, 70, 70
    xs = np.arange(X)[:, None, None] - X / 2; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :] - Z / 2
    solid = np.broadcast_to((ys < 3) | (zs < -28), (X, Y, Z)).copy()
    for k in range(6):   # ribs arching over
        cx = -45 + k * 18
        ring = (np.abs(np.sqrt((xs - cx) ** 2 * 0 + (ys - 0) ** 2 + (zs + 5) ** 2) - 52) < 3) & (np.abs(xs - cx) < 3) & (ys > 2)
        solid |= ring
    solid &= np.broadcast_to(zs < 24, solid.shape)
    room_mesh("B3 chest", solid, V(ox - X / 2, oy + Z / 2, 0), const("titan_dark"))
    K._blob("B3 lantern heart", (ox, oy + 24, 22), (14, 10, 18), M["heart"], None)
    K.light("B3 heart light", (ox, oy + 16, 22), 40000, (0.3, 1, 0.45))


def heart_moth(var, p):
    root = K.empty(f"B3 Heart Moth {var}", tuple(p))
    body = M["fur"]
    K._blob(root.name + " thorax", (0, 0, 0), (5, 6, 5), body, root)
    K._blob(root.name + " head", (0, -4, 0.5), (3.6, 3, 3.4), body, root)
    for i in range(6):
        K._blob(root.name + f" abdomen{i}", (0, 3.5 + i * 2, -0.6 * i), (4 - i * 0.4, 2.4, 3.6 - i * 0.4), body, root)
    for sx in (-1, 1):
        box(root.name + f" eye{sx}", (sx * 1.6, -5.2, 1), (1.6, 1.4, 1.8), M["eye"] if var == "V1" else M["heart"], root)
        a0 = V(sx * 1, -5, 2); a1 = V(sx * 6, -11, 9)
        seg(root.name + f" antenna{sx}", a0, a1, 0.35, body, root)
        for j in range(6):   # feathery antennae
            q = a0.lerp(a1, (j + 1) / 7)
            seg(root.name + f" antenna{sx} barb{j}", q, q + V(sx * 1.2, -0.6, -0.8), 0.18, body, root)
    wing_m = M["dust"] if var == "V1" else M["glass"]
    for sx in (-1, 1):
        for wi, (span, chord, up, back) in enumerate(((24, 14, 4, -2), (17, 10, -3, 7))):
            # each wing: plates fanning out, narrowing at the tip
            for k in range(7):
                t = k / 6
                cx_ = sx * (3 + t * span)
                w = chord * (1 - 0.55 * t)
                b = box(root.name + f" wing{wi}{sx} plate{k}", (cx_, back + t * 2, up + t * 4 * (1 if wi == 0 else -0.3)), (span / 6.5, w, 0.5), wing_m, root)
                b.rotation_euler = (0, sx * math.radians(12 * (1 if wi == 0 else -1)), 0)
                if var == "V2":
                    box(root.name + f" wing{wi}{sx} lead{k}", (cx_, back + t * 2, up + t * 4 * (1 if wi == 0 else -0.3)), (span / 6.5, w, 0.55), M["lead"], root, wire=0.15).rotation_euler = b.rotation_euler
            # eye spot on the fore wing
            if wi == 0:
                c = (sx * (3 + 0.55 * span), back + 1.2, up + 2.4)
                box(root.name + f" eyespot ring{sx}", c, (6, 6, 0.7), M["eyering"] if var == "V1" else M["glass2"], root).rotation_euler = (0, sx * math.radians(12), 0)
                box(root.name + f" eyespot{sx}", (c[0], c[1], c[2] + 0.1), (3.2, 3.2, 0.8), M["eyespot"], root).rotation_euler = (0, sx * math.radians(12), 0)
    for sx in (-1, 1):
        for k in range(3):
            hip = V(sx * 1.5, -1.5 + k * 1.5, -2)
            seg(root.name + f" leg{sx}{k}a", hip, hip + V(sx * 3, -1, -2), 0.5, body, root)
            seg(root.name + f" leg{sx}{k}b", hip + V(sx * 3, -1, -2), hip + V(sx * 4, -2, -5), 0.4, body, root)
    root.rotation_euler = (math.radians(70), 0, 0)   # hovering upright, wings spread toward you


# ======================================================================== B4 The Grasp
def arm_room(ox, oy):
    X, Y, Z = 150, 40, 60
    xs = np.arange(X)[:, None, None]; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :] - Z / 2
    bridge = (np.abs(zs) < 11) & (ys >= 18) & (ys < 24)
    gap = (xs > 34) & (xs < 52)
    rag = (np.random.default_rng(4).random((X, 1, Z)) < 0.35) & ((np.abs(xs - 34) < 3) | (np.abs(xs - 52) < 3))
    solid = bridge & ~gap & ~(rag & bridge)
    room_mesh("B4 broken arm", solid, V(ox - X / 2, oy + Z / 2, 0), const("titan"))
    for k in range(8):   # snapped light cables hanging into the gap
        x = ox - X / 2 + 34 + (k % 2) * 18
        seg(f"B4 cable {k}", V(x, oy + (k - 4) * 2.2, 18), V(x + (1 if k % 2 else -1) * 3, oy + (k - 4) * 2.4, 6 - k), 0.5, M["seam"], None)


def grasp(var, p):
    root = K.empty(f"B4 The Grasp {var}", tuple(p))
    st = M["redstone"] if var == "V2" else M["titan"]
    vein = M["red"] if var == "V2" else M["seam"]
    palm_c = V(0, 2, 8)
    palm = box(root.name + " palm", tuple(palm_c), (19, 20, 6), st, root)
    palm.rotation_euler = (math.radians(-10), 0, 0)
    box(root.name + " palm seam", tuple(palm_c), (19.1, 20.1, 6.1), vein, root, wire=0.25).rotation_euler = palm.rotation_euler
    for k in range(4):   # knuckle row
        box(root.name + f" knuckle bulge{k}", tuple(palm_c + V(-7 + k * 4.6, -9.5, 2.2)), (4, 3.5, 3.5), st, root)
    box(root.name + " wrist", tuple(palm_c + V(0, 13, 1.5)), (13, 8, 7), st, root)
    for k in range(6):   # broken wrist: light strands trailing out of the stump
        seg(root.name + f" strand{k}", palm_c + V(-5 + k * 2, 17, 1), palm_c + V(-6 + k * 2.4, 25, -5 + k * 0.8), 0.45, vein, root)
    # four fingers reaching forward and arching down onto the bridge, spread like a crawling hand
    for k in range(4):
        x0 = -7 + k * 4.6
        spread = (k - 1.5) * 0.18
        base = palm_c + V(x0, -10.5, 1.5)
        k1 = base + V(x0 * 0.12 + spread * 8, -8, 4.5)
        k2 = k1 + V(spread * 6, -7, -1.5)
        tip = V(k2.x + spread * 3, k2.y - 4, 0.6)
        for j_, (a, b, t) in enumerate(((base, k1, 3.4), (k1, k2, 3.0), (k2, tip, 2.6))):
            seg(root.name + f" finger{k}-{j_}", a, b, t, st, root)
            box(root.name + f" joint{k}-{j_}", tuple(b), (t * 1.15,) * 3, st, root)
            seg(root.name + f" finger{k}-{j_} vein", a + V(0, 0, t * 0.52), b + V(0, 0, t * 0.52), 0.32, vein, root)
        nail_m = M["red"] if var == "V2" else M["titan_dark"]
        seg(root.name + f" nail{k}", tip + V(0, 1.2, 2.2), tip + V(0, -1.6 - (1.5 if var == "V2" else 0), 0.2), 2.0 if var == "V1" else 1.2, nail_m, root)
    tb = palm_c + V(-10, -2, 0)
    tk = tb + V(-7, -4, 3); tt = V(tb.x - 12, tb.y - 9, 0.6)
    seg(root.name + " thumb a", tb, tk, 3.6, st, root); seg(root.name + " thumb b", tk, tt, 3.0, st, root)
    box(root.name + " thumb joint", tuple(tk), (4, 4, 4), st, root)
    seg(root.name + " thumb nail", tt + V(0, 1, 2), tt + V(-1, -2, 0.2), 1.8, M["red"] if var == "V2" else M["titan_dark"], root)
    # a slit of an eye opened in the back of the hand
    box(root.name + " eye", tuple(palm_c + V(0, 0, 3.4)), (5, 2.2, 0.6), M["eyer"] if var == "V2" else M["eye"], root).rotation_euler = palm.rotation_euler


# ======================================================================== B5 Carrion King
def spine_room(ox, oy):
    X, Y, Z = 140, 30, 90
    xs = np.arange(X)[:, None, None] - X / 2; ys = np.arange(Y)[None, :, None]; zs = np.arange(Z)[None, None, :] - Z / 2
    h = 14 - (xs / 70) ** 2 * 6 - (zs / 45) ** 2 * 10
    plates = ((np.floor(xs / 12) + np.floor(zs / 12)) % 2) * 1.0
    solid = ys < (h + plates)
    room_mesh("B5 titan back", solid, V(ox - X / 2, oy + Z / 2, 0), const("titan"))
    for k in range(5):   # spine ridges
        box(f"B5 spine ridge {k}", (ox - 40 + k * 20, oy + 25, 17), (6, 8, 6), M["titan_dark"], None)


def carrion_king(var, p):
    root = K.empty(f"B5 Carrion King {var}", tuple(p))
    skel = var == "V2"
    bm = M["bone"] if skel else M["feather"]
    K._blob(root.name + " body", (0, 2, 10), (9, 13, 9), M["green"] if skel else bm, root)
    if skel:
        for k in range(5):
            box(root.name + f" rib{k}", (0, -2 + k * 2.4, 10), (10, 0.8, 9), M["bone"], root, wire=0.6)
    seg(root.name + " neck", V(0, -4, 13), V(0, -9, 19), 2.6, M["bone"] if skel else M["skin"], root)
    box(root.name + " head", (0, -11, 20), (4, 5, 4), M["bone"] if skel else M["skin"], root)
    seg(root.name + " beak", V(0, -13.5, 20.5), V(0, -17, 18), 1.6, M["beak"], root)
    seg(root.name + " beak hook", V(0, -17, 18), V(0, -16.2, 16.6), 1.0, M["beak"], root)
    for sx in (-1, 1):
        box(root.name + f" eye{sx}", (sx * 1.8, -12, 21), (0.8, 0.8, 0.8), M["eye"] if skel else M["eyer"], root)
        box(root.name + f" ruff{sx}", (sx * 3.5, -5, 15), (5, 4, 4), M["bone"] if skel else M["feather"], root)
    for sx in (-1, 1):   # wings half open, raised like a threat
        sh = V(sx * 4, 0, 15)
        el = sh + V(sx * 12, 2, 8)
        wr = el + V(sx * 13, 4, -2)
        seg(root.name + f" wing bone{sx}a", sh, el, 1.6, M["bone"] if skel else bm, root)
        seg(root.name + f" wing bone{sx}b", el, wr, 1.3, M["bone"] if skel else bm, root)
        for k in range(9):   # flight feathers (or hard-light vanes) hanging from the arm
            t = k / 8
            a = sh.lerp(el, min(1, t * 2)) if t < 0.5 else el.lerp(wr, (t - 0.5) * 2)
            L = 14 - abs(t - 0.6) * 10
            b = a + V(sx * 2, 3, -L)
            seg(root.name + f" feather{sx}{k}", a, b, 1.8 if not skel else 1.4, M["green"] if skel else M["feather"], root)
    for sx in (-1, 1):   # legs and talons gripping the Titan's back
        seg(root.name + f" leg{sx}", V(sx * 3, 3, 6), V(sx * 4, 1, 1), 1.6, M["skin"] if not skel else M["bone"], root)
        for k in range(3):
            seg(root.name + f" talon{sx}{k}", V(sx * 4, 1, 1), V(sx * 4 + (k - 1) * 1.5, -2, 0), 0.6, M["beak"], root)
    # the nest behind: a ring of green construct bones (the Titan's broken light)
    for k in range(16):
        a = k / 16 * math.tau
        seg(root.name + f" nest{k}", V(math.cos(a) * 9, 18 + math.sin(a) * 7, 2), V(math.cos(a + 0.9) * 10, 18 + math.sin(a + 0.9) * 8, 4),
            0.9, M["green"] if k % 2 else M["bone"], root)


# ======================================================================== B6 Gilded Queen
def neck_room(ox, oy):
    X, Y, Z = 110, 60, 60
    xs = np.arange(X)[:, None, None] - X / 2; ys = np.arange(Y)[None, :, None] - 28; zs = np.arange(Z)[None, None, :] - Z / 2
    rr = np.sqrt(ys ** 2 + zs ** 2)
    solid = np.broadcast_to((rr > 26) & (rr < 31), (X, Y, Z)).copy()
    solid &= np.broadcast_to(zs < 4, solid.shape)
    room_mesh("B6 neck", solid, V(ox - X / 2, oy + Z / 2, 0), const("titan_dark"))
    rng = np.random.default_rng(6)
    for k in range(140):   # honeycomb of stolen lantern gold on the walls
        a = rng.uniform(math.pi * 0.05, math.pi * 0.95); x = rng.uniform(-50, 50)
        c = V(ox + x, oy + math.cos(a) * 25 * -1 + 10, 28 + math.sin(a) * 25 - 3)
        if c.z < 2:
            continue
        b = box(f"B6 comb {k}", tuple(c), (3.2, 3.2, 3.2), M["gold"], None)
        b.rotation_euler = (0, 0, math.radians(30))


def gilded_queen(var, p):
    root = K.empty(f"B6 Gilded Queen {var}", tuple(p))
    glow = M["orange"] if var == "V1" else M["yseam"]
    stripe = M["gold"] if var == "V1" else M["yellow"]
    K._blob(root.name + " head", (0, -8, 12), (5, 4, 5), M["black"], root)
    for sx in (-1, 1):
        K._blob(root.name + f" eye{sx}", (sx * 2.3, -8.6, 12.5), (2, 2.6, 3.2), glow, root)
        seg(root.name + f" mandible{sx}", V(sx * 1.2, -10, 10.5), V(sx * 0.4, -12, 9.5), 0.8, M["black"], root)
        seg(root.name + f" antenna{sx}", V(sx * 1, -9.5, 14), V(sx * 4, -14, 19), 0.4, M["black"], root)
    K._blob(root.name + " thorax", (0, -3, 12), (6, 6, 6), M["black"], root)
    box(root.name + " waist", (0, 0.8, 12), (2, 2, 2), M["black"], root)
    for k in range(6):   # striped abdomen curling down to the sting
        t = k / 5
        c = V(0, 3 + k * 2.6, 12 - t * t * 7)
        w = 7.5 - abs(t - 0.35) * 6
        K._blob(root.name + f" abdomen{k}", tuple(c), (w, 2.8, w * 0.9), stripe if k % 2 == 0 else M["black"], root)
    seg(root.name + " sting", V(0, 17, 4.5), V(0, 19.5, 1), 0.9, glow, root)
    for sx in (-1, 1):
        for wi, (L, up) in enumerate(((16, 4), (11, 2))):
            b = box(root.name + f" wing{sx}{wi}", (sx * (3 + L / 2), -2 + wi * 3, 16 + up), (L, 5, 0.3), M["wing"], root)
            b.rotation_euler = (0, sx * math.radians(-18 - wi * 6), sx * math.radians(12))
            box(root.name + f" wing vein{sx}{wi}", b.location, (L, 5, 0.32), glow, root, wire=0.12).rotation_euler = b.rotation_euler
        for k in range(3):
            hip = V(sx * 2.5, -4.5 + k * 2.2, 10)
            kn = hip + V(sx * 5, -1, 1)
            seg(root.name + f" leg{sx}{k}a", hip, kn, 0.8, M["black"], root)
            seg(root.name + f" leg{sx}{k}b", kn, kn + V(sx * 2, -1, -10), 0.6, stripe, root)
    # her crown: a stolen lantern ring cast in gold
    for k in range(8):
        a = k / 8 * math.tau
        box(root.name + f" crown{k}", (math.cos(a) * 2.5, -8 + math.sin(a) * 2, 15.5), (1, 1, 2), M["gold"], root)


# ======================================================================== lay out the 12 takes
BOSSES = [
    ("B1", "Boot Hermit", "boot", boot_room, boot_hermit, V(0, -4, 3), (0, -95, 40), (0, 0, 10), 36),
    ("B2", "Piston Wyrm", "leg", leg_room, piston_wyrm, V(0, 0, 0), (0, -120, 60), (0, 0, 50), 30),
    ("B3", "Heart Moth", "chest", chest_room, heart_moth, V(0, 0, 28), (0, -110, 30), (0, 0, 28), 30),
    ("B4", "The Grasp", "arm", arm_room, grasp, V(20, 0, 24), (-20, -70, 62), (14, -2, 28), 30),
    ("B5", "Carrion King", "spine", spine_room, carrion_king, V(0, 0, 13), (-10, -85, 30), (0, 0, 18), 30),
    ("B6", "Gilded Queen", "neck", neck_room, gilded_queen, V(0, 0, 14), (8, -60, 20), (0, 0, 18), 30),
]
PLAYER_AT = {"B1": V(-22, -18, 3), "B2": V(-17, 4, 16.5), "B3": V(-12, -6, 3), "B4": V(-5, -4, 24), "B5": V(-14, -12, 13), "B6": V(-12, -6, 3)}
for bi, (code, name, room, room_fn, boss_fn, at, cam_off, tgt_off, lens) in enumerate(BOSSES):
    for vi, var in enumerate(("V1", "V2")):
        ox, oy = bi * 400.0, -vi * 400.0
        room_fn(ox, oy)
        boss_fn(var, V(ox, oy, 0) + at)
        K.player(f"{code} {var} player", tuple(V(ox, oy, 0) + PLAYER_AT[code]))
        cams.append(K.camera(f"{len(cams) + 1:02d} {code} {name} {var}", tuple(V(ox, oy, 0) + V(*cam_off)), tuple(V(ox, oy, 0) + V(*tgt_off)), lens))
        K.light(f"{code} {var} key", tuple(V(ox + 40, oy - 80, 90)), 220000, (1, 0.95, 0.88), "AREA", 80)
        K.light(f"{code} {var} rim", tuple(V(ox - 50, oy + 40, 60)), 90000, (0.6, 0.75, 1.0), "AREA", 60)

w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
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
    rdir = os.path.join(os.path.dirname(OUT), "renders_titan_bosses")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("done", OUT)
