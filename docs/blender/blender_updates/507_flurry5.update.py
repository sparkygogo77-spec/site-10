# Pass 507: flurry round 5 (Chat C, 2026-10-14). J on 503's R5: "the flurries need less repetitive punching", then
# "mixed short burst combo string that sends them flying". Three short strings, every hit a different move, about a
# second each, the last hit launching the target far:
#   F1 jab - hook - uppercut: left jab, ring hook, ring uppercut that throws them up and back (construct fist under them).
#   F2 jab - cross - spinning backfist: left jab, ring cross, a full spin on the ball of the foot, the ring backfist
#      sweeping an arc of light that sends them flying sideways and back.
#   F3 body hook - cross - point-blank blast: left body hook, ring cross, then the ring hand opens on them and a green
#      blast at point blank throws them far back.
# Hits at ticks 6, 11, 18; the target flies 8-12 blocks. Each 60-tick loop. Cameras "Cam <take>" (over the right
# shoulder), "... fp", "... front", "... side". Builds LanternLive\combat\flurry5.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "flurry5.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Flurry 5")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Flurry 5")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ------------------------------------------------------------------ rig (Minecraft model space: px, y down, -z forward)
PIVOT = {"head": (0, 0, 0), "body": (0, 0, 0), "rarm": (-5, 2, 0), "larm": (5, 2, 0),
         "rleg": (-1.9, 12, 0), "lleg": (1.9, 12, 0), "rshin": (-1.9, 18, 0), "lshin": (1.9, 18, 0)}
BOX = {"head": ((-4, -8, -4), (4, 0, 4)), "body": ((-4, 0, -2), (4, 12, 2)), "rarm": ((-3, -2, -2), (1, 10, 2)),
       "larm": ((-1, -2, -2), (3, 10, 2)), "rleg": ((-2, 0, -2), (2, 6, 2)), "lleg": ((-2, 0, -2), (2, 6, 2)),
       "rshin": ((-2, 0, -2), (2, 6, 2)), "lshin": ((-2, 0, -2), (2, 6, 2))}
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")


def euler_of(Rm):
    """XYZ euler (x, y, z) of R = Rz @ Ry @ Rx, the inverse of rot()."""
    y = math.asin(max(-1.0, min(1.0, -Rm[2, 0])))
    return (math.atan2(Rm[2, 1], Rm[2, 2]), y, math.atan2(Rm[1, 0], Rm[0, 0]))
GROUND = 24.0
A = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # MC model axes -> Blender axes (x, z, -y)


def rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def corners(part, pivot, r):
    a, b = BOX[part]
    pts = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])], float)
    return pts @ rot(*r).T + np.asarray(pivot, float)


def solve(p):
    """Pose (ring = right side) -> per part rotation and pivot. The body turns about the hips, the legs hang from the
    hips, grounded poses drop the hips until the lowest foot touches, `sink` lowers the torso into the legs."""
    rot_ = {"body": p.get("body", (0, 0, 0)), "head": p.get("head", (0, 0, 0))}
    # the neck bends at most ~57 degrees back from the body, so a flat flyer looks ahead instead of folding the head
    # back into his own chest (J, F3)
    hb = rot_["head"]; rot_["head"] = (max(hb[0], rot_["body"][0] - 1.0), hb[1], hb[2])
    for k, part, sgn in (("ring", "rarm", 1), ("free", "larm", -1), ("ringleg", "rleg", 1), ("freeleg", "lleg", -1)):
        x, y, z = p.get(k, (0, 0, 0))
        rot_[part] = (x, sgn * y, sgn * z)
    Rb = rot(*rot_["body"])
    sink = float(p.get("sink", 0.0))
    piv = {}

    def place(d):
        hip = np.array([0.0, 12.0 + d, -float(p.get("fwd", 0.0))])
        neck = hip + Rb @ np.array([0.0, -12.0, 0.0]) + np.array([0.0, sink, 0.0])
        piv["body"] = neck; piv["head"] = neck.copy()
        piv["rarm"] = neck + Rb @ np.array([-5.0, 2.0, 0.0]); piv["larm"] = neck + Rb @ np.array([5.0, 2.0, 0.0])
        piv["rleg"] = hip + Rb @ np.array([-1.9, 0.0, 0.0]) * np.array([1, 0, 1]) + np.array([0, 0, 0])
        piv["lleg"] = hip + Rb @ np.array([1.9, 0.0, 0.0]) * np.array([1, 0, 1])
        for leg, shin in (("rleg", "rshin"), ("lleg", "lshin")):
            piv[shin] = piv[leg] + rot(*rot_[leg]) @ np.array([0.0, 6.0, 0.0])

    for leg, shin, kk in (("rleg", "rshin", "ringknee"), ("lleg", "lshin", "freeknee")):
        k = float(p.get(kk, 0.0))
        rot_[shin] = euler_of(rot(*rot_[leg]) @ rot(k, 0, 0))
    place(0.0)
    d = 0.0
    if p.get("grounded", True):
        low = max(corners(k, piv[k], rot_[k])[:, 1].max() for k in ("rleg", "lleg", "rshin", "lshin"))
        d = GROUND - low
        place(d)
    return {k: (np.asarray(rot_[k], float), piv[k]) for k in PARTS}


def hand_point(sol, part="rarm"):
    r, pv = sol[part]
    return np.array([-1.0 if part == "rarm" else 1.0, 10.0, 0.0]) @ rot(*r).T + pv


def to_bl(v):
    v = np.asarray(v, float)
    return A @ np.array([v[0], v[1] - GROUND, v[2]]) / 16.0


def mat(name, rgb, emit=0.0, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


SKIN = mat("KL skin", (0.62, 0.42, 0.3)); SHIRT = mat("KL shirt", (0.04, 0.28, 0.12))
PANTS = mat("KL pants", (0.03, 0.05, 0.09)); HAIR = mat("KL hair", (0.08, 0.05, 0.03))
RINGM = mat("KL ring", (0.1, 1.0, 0.25), emit=3.0)
SHOES = mat("KL shoes", (0.12, 0.12, 0.13))
PART_MAT = {"head": SKIN, "body": SHIRT, "rarm": SHIRT, "larm": SHIRT, "rleg": PANTS, "lleg": PANTS,
            "rshin": PANTS, "lshin": PANTS}


def box_mesh(name, a, b, m):
    a = np.array(a, float); b = np.array(b, float)
    pts = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    verts = [tuple(A @ p / 16.0) for p in pts]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(m)
    return me


def make_player(tag):
    objs = {}
    for k in PARTS:
        a, b = BOX[k]
        o = link(bpy.data.objects.new(f"KL {tag} {k}", box_mesh(f"KL {tag} {k}", a, b, PART_MAT[k])))
        o.rotation_mode = "XYZ"
        objs[k] = o
    # details as children: hair cap, hands, ring
    for k, (a, b), m in (("head", ((-4.05, -8.05, -4.05), (4.05, -6.5, 4.05)), HAIR),
                         ("rarm", ((-3.02, 7, -2.02), (1.02, 10.02, 2.02)), SKIN),
                         ("larm", ((-1.02, 7, -2.02), (3.02, 10.02, 2.02)), SKIN),
                         ("rarm", ((-3.4, 6.2, -2.4), (1.4, 7.4, 2.4)), RINGM),
                         ("rshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES),
                         ("lshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES)):
        c = link(bpy.data.objects.new(f"KL {tag} {k} detail", box_mesh(f"KL {tag} {k} d", a, b, m)))
        c.parent = objs[k]
        if m is RINGM:
            objs["ring"] = c
    return objs


def set_pose(objs, sol, origin, frame, side=0.0):
    rs = np.array([[math.cos(side), -math.sin(side), 0], [math.sin(side), math.cos(side), 0], [0, 0, 1]])
    for k in PARTS:
        r, pv = sol[k]
        Rb = rs @ (A @ rot(*r) @ A.T)
        loc = rs @ to_bl(pv) + np.asarray(origin)
        o = objs[k]
        M = np.eye(4); M[:3, :3] = Rb; M[:3, 3] = loc
        from mathutils import Matrix
        o.matrix_world = Matrix(M.tolist())
        o.keyframe_insert("location", frame=frame); o.keyframe_insert("rotation_euler", frame=frame)


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c



def smooth(t):
    return t * t * (3 - 2 * t)


def mixp(a, b, w):
    keys = set(a) | set(b)
    out = {}
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if k in ("grounded",):
            continue
        if isinstance(va, tuple) or isinstance(vb, tuple):
            va = np.array(va if va is not None else (0, 0, 0), float); vb = np.array(vb if vb is not None else (0, 0, 0), float)
            out[k] = tuple(va + (vb - va) * w)
        else:
            va = 0.0 if va is None else va; vb = 0.0 if vb is None else vb
            out[k] = va + (vb - va) * w
    return out


def emis(name, rgb, strength, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N.get("Material Output"); N.remove(N.get("Principled BSDF"))
    e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    if alpha < 1:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = alpha
        L.new(tr.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    else:
        L.new(e.outputs[0], out.inputs["Surface"])
    return m, e


def cube(name, m, size):
    me = bpy.data.meshes.new(name); h = size / 2
    me.from_pydata([(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))




def P(**k):
    return k


LOOP = 40
TW = 2 * math.pi / LOOP
STAND = P(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.05), free=(0.05, 0, -0.05))

# --- P1 punches: stance with the free (left) foot forward for the cross and hook, ring foot forward for the jab
GUARD_C = P(body=(0.12, 0.3, 0), head=(0.05, -0.3, 0), ring=(-1.15, -0.55, 0.1), free=(-1.45, -0.45, -0.1),
            ringleg=(0.35, 0, 0.1), ringknee=0.35, freeleg=(-0.35, 0, -0.1), freeknee=0.35, sink=0.6)
CHAMBER_C = P(body=(0.1, 0.42, 0), head=(0.05, -0.42, 0), ring=(-1.0, -0.65, 0.1), free=(-1.45, -0.45, -0.1),
              ringleg=(0.4, 0, 0.1), ringknee=0.45, freeleg=(-0.35, 0, -0.1), freeknee=0.35, sink=0.9)
CROSS = P(body=(0.22, -0.5, 0), head=(0.0, 0.5, 0), ring=(-1.57, -0.12, 0.0), free=(-1.35, -0.7, -0.15),
          ringleg=(0.42, 0, 0.12), ringknee=0.15, freeleg=(-0.42, 0, -0.1), freeknee=0.5, fwd=1.5, sink=0.6)
GUARD_J = P(body=(0.1, -0.3, 0), head=(0.05, 0.3, 0), ring=(-1.3, -0.35, 0.1), free=(-1.3, -0.6, -0.1),
            ringleg=(-0.35, 0, 0.1), ringknee=0.35, freeleg=(0.35, 0, -0.1), freeknee=0.35, sink=0.6)
JAB = P(body=(0.18, -0.45, 0), head=(0.0, 0.45, 0), ring=(-1.57, -0.05, 0.0), free=(-1.35, -0.65, -0.1),
        ringleg=(-0.5, 0, 0.1), ringknee=0.45, freeleg=(0.4, 0, -0.1), freeknee=0.2, fwd=1.0, sink=0.9)
HOOK_LOAD = P(body=(0.12, 0.5, 0), head=(0.05, -0.5, 0), ring=(-1.45, 0.75, 0.0), free=(-1.45, -0.45, -0.1),
              ringleg=(0.35, 0, 0.1), ringknee=0.45, freeleg=(-0.35, 0, -0.1), freeknee=0.35, sink=1.0)
HOOK = P(body=(0.18, -0.7, 0), head=(0.0, 0.7, 0), ring=(-1.5, -0.55, 0.0), free=(-1.35, -0.7, -0.15),
         ringleg=(0.4, 0, 0.12), ringknee=0.2, freeleg=(-0.4, 0, -0.1), freeknee=0.45, fwd=1.0, sink=0.7)
# (pose, tick); the strike frames are listed in HITS
P1_KEYS = {
    "P1a": [(GUARD_C, 0), (GUARD_C, 4), (CHAMBER_C, 7), (CROSS, 9), (CROSS, 11), (GUARD_C, 16), (GUARD_C, 24),
            (CHAMBER_C, 27), (CROSS, 29), (CROSS, 31), (GUARD_C, 36), (GUARD_C, 40)],
    "P1b": [(GUARD_J, 0), (GUARD_J, 6), (JAB, 8), (JAB, 10), (GUARD_J, 15), (GUARD_J, 26), (JAB, 28), (JAB, 30),
            (GUARD_J, 35), (GUARD_J, 40)],
    "P1c": [(GUARD_C, 0), (GUARD_C, 4), (HOOK_LOAD, 8), (HOOK, 11), (HOOK, 13), (GUARD_C, 19), (GUARD_C, 24),
            (HOOK_LOAD, 27), (HOOK, 30), (HOOK, 32), (GUARD_C, 38), (GUARD_C, 40)],
}
HITS = {"P1a": (9, 29), "P1b": (8, 28), "P1c": (11, 30)}
STEP = {"P1b": [(0, 0.0), (6, 0.0), (8, 0.45), (15, 0.45), (20, 0.0), (26, 0.0), (28, 0.45), (35, 0.45), (40, 0.0)]}

# --- P2 blast (KEEP the 221 poses; the free hand stays braced and moves a fraction of the ring hand)
BLAST_SET = P(body=(0.1, -0.2, 0), head=(0.0, 0.15, 0), ring=(-1.5, 0.1, 0.05), free=(-1.45, -0.45, -0.1),
              ringleg=(0.45, 0, 0.25), ringknee=0.45, freeleg=(-0.45, 0, -0.25), freeknee=0.45)
BLAST_KICK = P(body=(-0.12, -0.2, 0), head=(-0.15, 0.15, 0), ring=(-1.85, 0.1, 0.05), free=(-1.45, -0.45, -0.1),
               ringleg=(0.5, 0, 0.25), ringknee=0.6, freeleg=(-0.4, 0, -0.25), freeknee=0.4)
BLAST_LOW = mixp(BLAST_SET, P(ring=(-1.3, 0.1, 0.05)), 1.0)
BLAST_LOW.update({k: v for k, v in BLAST_SET.items() if k != "ring"})
P2_KEYS = [(BLAST_LOW, 0), (BLAST_SET, 6), (BLAST_SET, 22), (BLAST_KICK, 24), (BLAST_KICK, 27), (BLAST_SET, 34),
           (BLAST_LOW, 40)]
P2_FOLLOW = {"P2a": 0.0, "P2b": 0.25, "P2c": 0.5}

# --- P4 beam hold: braced, ring arm locked out, free hand gripping the ring forearm
BEAM = P(body=(0.08, -0.3, 0), head=(0.0, 0.3, 0), ring=(-1.57, -0.05, 0.0), free=(-1.3, -0.85, -0.1),
         ringleg=(0.55, 0, 0.22), ringknee=0.55, freeleg=(-0.45, 0, -0.22), freeknee=0.4, sink=1.2, fwd=0.6)

# --- P5 wall: the ring arm alone sweeps up from low
LOW_R = P(body=(0.35, 0, 0), head=(0.0, 0, 0), ring=(0.35, 0, 0.35), ringleg=(-0.5, 0, 0.15), ringknee=1.0,
          freeleg=(-0.3, 0, -0.15), freeknee=0.9)
SWEEP_R = P(body=(-0.1, 0, 0), head=(-0.2, 0, 0), ring=(-2.6, 0, 0.3), ringleg=(0.05, 0, 0.12), ringknee=0.1,
            freeleg=(0.05, 0, -0.12), freeknee=0.1)
P5_FREE = {"P5a": (0.05, 0, -0.08), "P5b": (-1.35, -0.6, -0.15), "P5c": (0.4, 0, -0.45)}

# --- P6 slam: straight from standing into the slam, one smooth drop
SLAM = P(body=(0.9, 0, 0), head=(-0.6, 0, 0), ring=(-0.2, 0, 0.1), free=(0.9, 0, -0.5),
         ringleg=(0.2, 0, 0.06), ringknee=1.35, freeleg=(-1.2, 0, -0.08), freeknee=1.3)
P6_DROP = {"P6a": 5, "P6b": 7, "P6c": 10}


def keyed(keys, t):
    for (pa, ta), (pb, tb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return mixp(pa, pb, 0 if tb == ta else smooth((t - ta) / (tb - ta)))
    return dict(keys[-1][0])


def lerp_keys(keys, t):
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return va + (vb - va) * smooth((t - ta) / (tb - ta) if tb > ta else 0)
    return keys[-1][1]


def keyo(o, f, loc=None, scale=None, rot=None, quat=None):
    if loc is not None:
        o.location = tuple(loc); o.keyframe_insert("location", frame=f)
    if scale is not None:
        o.scale = tuple(scale); o.keyframe_insert("scale", frame=f)
    if rot is not None:
        o.rotation_euler = tuple(rot); o.keyframe_insert("rotation_euler", frame=f)
    if quat is not None:
        o.rotation_mode = "QUATERNION"; o.rotation_quaternion = quat; o.keyframe_insert("rotation_quaternion", frame=f)


def add_t(a, b, s=1.0):
    return tuple(np.array(a, float) + s * np.array(b, float))


GREEN = (0.04, 1.0, 0.16)                       # saturated: G clips, R and B stay low, so it never reads white
HARD, _ = emis("C4 hard light", (0.2, 1.0, 0.4), 3.0, alpha=0.45)
CORE, _ = emis("C4 beam core", GREEN, 2.2, alpha=0.85)
PIX, _ = emis("C4 pixel", (0.06, 1.0, 0.25), 2.0)
PIXD, _ = emis("C4 pixel dark", (0.01, 0.55, 0.12), 1.6)
BOLT, _ = emis("C4 bolt", GREEN, 2.5)


def unit_cube(name, m, size):
    return cube(name, m, size)


def arm_dir(sol, part="rarm"):
    r, _ = sol[part]
    d = A @ (rot(*r) @ np.array([0.0, 1.0, 0.0]))
    return d / np.linalg.norm(d)


def burst(tag, at, f0, rng, n=6, fwd=(0, -1, 0), life=7):
    """A few construct pixels thrown off an impact point, shrinking to nothing."""
    for i in range(n):
        o = unit_cube(f"{tag} px{i}", PIX if i % 2 else PIXD, 0.09)
        v = np.array(fwd, float) * 0.09 + rng.normal(0, 0.05, 3); v[2] = abs(v[2]) + 0.02
        keyo(o, 1, loc=at, scale=(0, 0, 0)); keyo(o, f0 - 1, loc=at, scale=(0, 0, 0))
        for k in range(life + 1):
            keyo(o, f0 + k, loc=np.array(at) + v * k, scale=[max(0.0, 1 - k / life)] * 3)


def fp_cam(name, objs_sol_origin):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name))); c.data.lens = 24
    c.rotation_euler = (R(76), 0, R(180))
    return c


def key_fp(c, sol, origin, f):
    eye = to_bl(sol["head"][1] + np.array([0.0, -4.5, -4.8])) + origin
    c.location = tuple(eye); c.keyframe_insert("location", frame=f)


# ================================================================== pass 503 takes
from mathutils import Vector
LOOP = 80
TW = 2 * math.pi / LOOP
ENEMY_RGB = (1.0, 0.35, 0.03)

# left (free hand) jab: mirror of the cross, left shoulder drives forward
JAB_L = P(body=(0.2, 0.5, 0), head=(0.0, -0.5, 0), ring=(-1.3, -0.65, 0.1), free=(-1.57, -0.12, 0.0),
          ringleg=(0.42, 0, 0.12), ringknee=0.45, freeleg=(-0.42, 0, -0.1), freeknee=0.2, fwd=1.2, sink=0.6)
AIM = P(body=(0.05, -0.15, 0), head=(-0.15, 0.15, 0), ring=(-1.75, -0.05, 0.0), free=(0.1, 0, -0.08),
        ringleg=(0.25, 0, 0.1), ringknee=0.2, freeleg=(-0.25, 0, -0.1), freeknee=0.2)
CATCH = P(body=(-0.05, -0.25, 0), head=(0.05, 0.25, 0), ring=(-1.62, -0.05, 0.0), free=(-1.35, -0.8, -0.1),
          ringleg=(0.55, 0, 0.22), ringknee=0.6, freeleg=(-0.45, 0, -0.22), freeknee=0.45, sink=1.2)
FIRE = P(body=(0.3, -0.55, 0), head=(-0.05, 0.55, 0), ring=(-1.57, -0.1, 0.0), free=(-1.3, -0.8, -0.1),
         ringleg=(0.6, 0, 0.15), ringknee=0.2, freeleg=(-0.6, 0, -0.1), freeknee=0.7, fwd=2.5, sink=1.0)
DASH_A = P(body=(0.75, -0.3, 0), head=(-0.55, 0.3, 0), ring=(-2.3, -0.05, 0.0), free=(0.9, 0, -0.35),
           ringleg=(0.9, 0, 0.1), ringknee=0.6, freeleg=(-0.7, 0, -0.1), freeknee=0.9, grounded=False)
DASH_B = P(body=(0.65, 0.35, 0), head=(-0.5, -0.35, 0), ring=(0.6, 0, 0.25), free=(0.8, 0, -0.35),
           ringleg=(0.9, 0, 0.1), ringknee=0.6, freeleg=(-0.8, 0, -0.1), freeknee=0.9, grounded=False)
DASH_C = P(body=(0.6, 0, 0), head=(-0.45, 0, 0), ring=(1.2, 0, 0.25), free=(0.9, 0, -0.3),
           ringleg=(0.9, 0, 0.1), ringknee=0.6, freeleg=(-0.9, 0, -0.1), freeknee=0.9, grounded=False)
CROSS1 = dict(CROSS); CROSS1["free"] = (0.3, 0, -0.35)       # one-handed: the free arm swings back, not up
GUARD1 = dict(GUARD_C); GUARD1["free"] = (-0.6, -0.3, -0.2)
BIG_CROSS = dict(CROSS); BIG_CROSS.update(fwd=3.0, body=(0.3, -0.65, 0), head=(-0.05, 0.65, 0))

ORDER = ["F1", "F2", "F3"]
NAMES = {"R2a": "hammer - overhead", "R2b": "hammer - from the side", "R2c": "hammer - from behind",
         "R3a": "dash - flying ring fist", "R3b": "dash - fist at hip, then thrown", "R3c": "dash - free hand trails",
         "R4a": "absorb - held in a cage", "R4b": "absorb - turns green, charges", "R4c": "absorb - into the ring",
         "R5a": "flurry - left/right, ring cross", "R5b": "flurry - ring hand fists", "R5c": "flurry - both, giant fist"}
SPACING = 12.0
dump = {"format": "per take, per tick: part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, forward offset "
                  "in blocks, ring glow; plus the effect timings. 20 ticks a second, 80-tick loops.", "takes": {}}


def mob_stand(name):
    m = mat("C5 mob", (0.55, 0.32, 0.25))
    me = bpy.data.meshes.new(name)
    vs, fs = [], []
    for (a, b) in (((-0.3, -0.3, 0.0), (0.3, 0.3, 1.4)), ((-0.25, -0.25, 1.4), (0.25, 0.25, 1.9))):
        o = len(vs)
        vs += [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        fs += [tuple(o + i for i in f) for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))]
    me.from_pydata(vs, [], fs); me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def ground_hole(tag, cx, cy, half, size=5.0):
    """Ground pieces around a (2 half + 1)^2 hole at (cx, cy); the hole is filled by separate crater blocks."""
    gm = mat("C5 ground", (0.18, 0.3, 0.12))
    h = half + 0.5
    for i, (x0, x1, y0, y1) in enumerate(((cx - size, cx + size, cy + h, cy + size), (cx - size, cx + size, cy - size, cy - h),
                                          (cx - size, cx - h, cy - h, cy + h), (cx + h, cx + size, cy - h, cy + h))):
        me = bpy.data.meshes.new(f"{tag} g{i}")
        me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)]); me.materials.append(gm)
        link(bpy.data.objects.new(f"{tag} g{i}", me))


CRATER, _ = emis("C5 crater construct", (0.05, 0.9, 0.25), 2.5, alpha=0.7)
DIRT = mat("C5 dirt", (0.35, 0.25, 0.15))


def crater(tag, cx, cy, half, f_hit, rng):
    for dx in range(-half, half + 1):
        for dy in range(-half, half + 1):
            c = np.array([cx + dx, cy + dy, -0.5])
            top = cube(f"{tag} cell {dx} {dy}", DIRT, 1.0)
            lit = cube(f"{tag} cell {dx} {dy} lit", CRATER, 1.02)
            d = int(round(math.hypot(dx, dy)))
            f_l, f_g = f_hit + d, f_hit + 4 + 2 * d
            keyo(top, 1, loc=c, scale=(1, 1, 1)); keyo(top, f_l, scale=(1, 1, 1)); keyo(top, f_l + 1, scale=(0, 0, 0))
            keyo(lit, 1, loc=c, scale=(0, 0, 0)); keyo(lit, f_l, scale=(0, 0, 0)); keyo(lit, f_l + 1, scale=(1, 1, 1))
            keyo(lit, f_g - 1, scale=(1, 1, 1)); keyo(lit, f_g + 1, scale=(0, 0, 0))
            out = np.array([dx, dy, 0.0]); out = out / (np.linalg.norm(out) or 1.0)
            burst(f"{tag} c{dx}{dy}", c + np.array([0, 0, 0.45]), f_g, rng, n=6, fwd=tuple(out * 0.6 + np.array([0, 0, 0.6])))
    # the hole floor, a block down
    me = bpy.data.meshes.new(tag + " floor"); hh = half + 0.5
    me.from_pydata([(cx - hh, cy - hh, -1), (cx + hh, cy - hh, -1), (cx + hh, cy + hh, -1), (cx - hh, cy + hh, -1)], [], [(0, 1, 2, 3)])
    me.materials.append(DIRT); link(bpy.data.objects.new(tag + " floor", me))


def torus(name, m, minor=0.05):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=minor, major_segments=48, minor_segments=6)
    o = bpy.context.active_object
    for cc in list(o.users_collection):
        cc.objects.unlink(o)
    link(o); o.name = name; o.data.materials.append(m)
    return o


def knock(o, pos0, f_hit, vel, face=0.0, until=LOOP + 1, squash=True):
    pos = np.array(pos0, float); v = np.array(vel, float)
    keyo(o, 1, loc=pos, scale=(1, 1, 1), rot=(0, 0, face)); keyo(o, f_hit, loc=pos, scale=(1, 1, 1), rot=(0, 0, face))
    tilt = 0.0
    for f in range(f_hit + 1, until):
        if pos[2] > 0.0 or v[2] > 0:
            pos = pos + v; v[2] -= 0.08; v *= 0.98; tilt = min(1.2, tilt + 0.12)
            if pos[2] < 0:
                pos[2] = 0.0; v[:] = 0
        sc = (1.15, 1.15, 0.7) if squash and f < f_hit + 3 else (1, 1, 1)
        keyo(o, f, loc=pos, scale=sc, rot=(tilt, 0, face))


HAM, _ = emis("C5 hammer", (0.15, 1.0, 0.35), 2.4, alpha=0.8)
FIST, _ = emis("C5 construct fist", (0.15, 1.0, 0.35), 2.2, alpha=0.75)
CAGE, _ = emis("C5 cage", (0.15, 1.0, 0.35), 1.8, alpha=0.35)
BOLT_G, _ = emis("C5 green blast", GREEN, 3.0)


UPPER_LOAD = P(body=(0.45, -0.3, 0), head=(0.1, 0.3, 0), ring=(0.4, 0, 0.3), free=(-1.35, -0.6, -0.15),
               ringleg=(-0.4, 0, 0.15), ringknee=1.1, freeleg=(0.3, 0, -0.15), freeknee=0.9, sink=1.5)
UPPER = P(body=(-0.2, -0.45, 0), head=(-0.35, 0.45, 0), ring=(-2.85, -0.1, 0.1), free=(-1.2, -0.6, -0.15),
          ringleg=(0.2, 0, 0.1), ringknee=0.1, freeleg=(0.3, 0, -0.1), freeknee=0.2, fwd=1.0)
BACKFIST = P(body=(0.1, 0, 0), head=(0.0, 0, 0), ring=(-1.57, 0.95, 0.0), free=(0.3, 0, -0.5),
             ringleg=(0.25, 0, 0.1), ringknee=0.3, freeleg=(-0.2, 0, -0.1), freeknee=0.3)
BODY_HOOK = dict(JAB_L); BODY_HOOK.update(free=(-1.15, 0.35, 0.0), body=(0.35, 0.55, 0), sink=1.6)
PALM = dict(FIRE); PALM.update(ring=(-1.6, -0.05, 0.0))
STR = {
    "F1": [(GUARD_C, 0), (GUARD_C, 3), (JAB_L, 6), (GUARD_C, 8), (HOOK_LOAD, 9), (HOOK, 11), (UPPER_LOAD, 15),
           (UPPER, 18), (UPPER, 24), (dict(STAND), 36), (dict(STAND), 60)],
    "F2": [(GUARD_C, 0), (GUARD_C, 3), (JAB_L, 6), (GUARD_C, 8), (CHAMBER_C, 9), (CROSS, 11), (GUARD_C, 13),
           (BACKFIST, 18), (BACKFIST, 22), (dict(STAND), 34), (dict(STAND), 60)],
    "F3": [(GUARD_C, 0), (GUARD_C, 3), (BODY_HOOK, 6), (GUARD_C, 8), (CHAMBER_C, 9), (CROSS, 11), (CATCH, 15),
           (PALM, 18), (PALM, 24), (dict(STAND), 36), (dict(STAND), 60)],
}
NAMES = {"F1": "jab - hook - uppercut", "F2": "jab - cross - spinning backfist", "F3": "body hook - cross - point-blank blast"}
HITS = {"F1": [(6, "free"), (11, "ring"), (18, "ring")], "F2": [(6, "free"), (11, "ring"), (18, "ring")],
        "F3": [(6, "free"), (11, "ring"), (18, "ring")]}
LAUNCH = {"F1": (0, -0.55, 0.95), "F2": (0.6, -0.85, 0.45), "F3": (0, -1.25, 0.35)}
LOOP = 60
SPACING = 16.0
for idx, take in enumerate(ORDER):
    base = np.array([idx * SPACING, 0.0, 0.0])
    rng = np.random.default_rng(507 + idx)
    objs = make_player(take)
    rm, rem = emis(f"C7 ring {take}", (0.1, 1.0, 0.25), 2.0); objs["ring"].data.materials[0] = rm
    fpc = fp_cam(f"Cam {take} fp", None)
    mob = mob_stand(f"C7 {take} mob")
    mob0 = base + np.array([0, -1.7, 0])
    keys = STR[take]
    hit_ticks = [h for h, _ in HITS[take]]
    ticks = []
    for t in range(LOOP + 1):
        f = t + 1
        p = keyed(keys, t)
        side = 0.0
        if take == "F2" and 13 <= t <= 19:               # the spin: a full turn on the ball of the foot
            side = -2 * math.pi * smooth((t - 13) / 6)
        sol = solve(p)
        set_pose(objs, sol, base, f, side=side)
        key_fp(fpc, sol, base, f)
        rs = np.array([[math.cos(side), -math.sin(side), 0], [math.sin(side), math.cos(side), 0], [0, 0, 1]])
        hand = rs @ to_bl(hand_point(sol)) + base
        fhand = rs @ to_bl(hand_point(sol, "larm")) + base
        glow = 3.0
        for h, who in HITS[take]:
            if h <= t < h + 2 and who == "ring":
                glow = 24.0 if h != hit_ticks[-1] else 32.0
            if t == h:
                at = (hand if who == "ring" else fhand) + np.array([0, -0.15, 0])
                burst(f"C7 {take} hit{t}", at, f, rng, n=7 if h != hit_ticks[-1] else 18, life=7 if h != hit_ticks[-1] else 10)
        s_ = rm.node_tree.nodes["Emission"].inputs["Strength"]; s_.default_value = glow; s_.keyframe_insert("default_value", frame=f)
        ticks.append({"glow": glow, "side_yaw": round(side, 4),
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    # the target: rocked by the first two hits, launched by the third
    keyo(mob, 1, loc=mob0, rot=(0, 0, 0), scale=(1, 1, 1))
    for h in hit_ticks[:2]:
        keyo(mob, h + 1, loc=mob0, rot=(0, 0, 0)); keyo(mob, h + 2, loc=mob0 + np.array([0, -0.12, 0]), rot=(0.18, 0, 0))
        keyo(mob, h + 4, loc=mob0 + np.array([0, -0.08, 0]), rot=(0.05, 0, 0))
    hl = hit_ticks[-1] + 1
    knock(mob, mob0 + np.array([0, -0.08, 0]), hl, LAUNCH[take], until=LOOP + 1)
    # the finisher's effect
    if take == "F1":
        fo = cube(f"C7 {take} rising fist", FIST, 0.9)
        keyo(fo, 1, loc=mob0, scale=(0, 0, 0)); keyo(fo, hl - 1, loc=mob0 + np.array([0, 0, -0.4]), scale=(0, 0, 0))
        for k_ in range(10):
            keyo(fo, hl + k_, loc=mob0 + np.array([0, -0.4 * k_ * 0.5, -0.2 + 0.35 * k_]), scale=[max(0, 1 - k_ / 10)] * 3)
    elif take == "F2":
        arc = torus(f"C7 {take} arc", HARD, 0.06)
        keyo(arc, 1, loc=base + np.array([0, 0, 1.4]), scale=(0, 0, 0))
        for t in range(12, 24):
            w = 0 if t < 14 else min(1, (t - 14) / 3) * (1 if t < 20 else max(0, 1 - (t - 20) / 3))
            keyo(arc, t + 1, loc=base + np.array([0, 0, 1.35]), scale=(1.15 * w + 0.001, 1.15 * w + 0.001, 0.15 * w + 0.001))
    else:
        bl = cube(f"C7 {take} blast", BOLT_G, 1.0); fl = torus(f"C7 {take} flare", HARD, 0.08)
        keyo(bl, 1, loc=mob0, scale=(0, 0, 0)); keyo(fl, 1, loc=mob0, scale=(0, 0, 0))
        for k_ in range(0, 9):
            f = hl + k_
            keyo(bl, f, loc=base + np.array([0, -0.9 - 1.0 * k_, 1.15]), scale=(0.7 * max(0, 1 - k_ / 9), 1.4, 0.7 * max(0, 1 - k_ / 9)))
            keyo(fl, f, loc=base + np.array([0, -0.75, 1.15]), scale=((0.3 + 0.2 * k_) * max(0, 1 - k_ / 8),) * 3, rot=(R(90), 0, 0))
        keyo(bl, hl - 1, loc=mob0, scale=(0, 0, 0)); keyo(fl, hl - 1, loc=mob0, scale=(0, 0, 0))
    dump["takes"][take] = {"name": NAMES[take], "hits": hit_ticks, "launch_bpt": LAUNCH[take], "ticks": ticks}
    cu = bpy.data.curves.new("C7 label " + take, "FONT"); cu.body = f"{take}  {NAMES[take]}"; cu.size = 0.3
    cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("C7 label " + take, cu)); tl.location = tuple(base + np.array([0, 1.4, 0.01]))
    tl.data.materials.append(mat("C5 label", (0.8, 1.0, 0.85), emit=2.0))
    cam(f"Cam {take}", tuple(base + np.array([-1.3, 3.0, 2.8])), tuple(base + np.array([0.3, -3.0, 0.9])), 28)
    cam(f"Cam {take} front", tuple(base + np.array([3.0, -6.5, 2.0])), tuple(base + np.array([0, -1.5, 0.9])), 28)
    cam(f"Cam {take} side", tuple(base + np.array([-7.0, -2.5, 1.8])), tuple(base + np.array([0, -3.0, 1.2])), 28)
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "flurry5_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, LOOP
for i, x in enumerate([0, 1, 2]):
    pass
for idx, take in enumerate(ORDER):
    if not take.startswith("R2"):
        bx = idx * SPACING
        me = bpy.data.meshes.new(f"C5 ground {take}")
        me.from_pydata([(bx - 6, -12, 0), (bx + 6, -12, 0), (bx + 6, 6, 0), (bx - 6, 6, 0)], [], [(0, 1, 2, 3)])
        me.materials.append(mat("C5 ground", (0.18, 0.3, 0.12))); link(bpy.data.objects.new(f"C5 ground {take}", me))
    else:
        bx = idx * SPACING
        for (x0, x1, y0, y1) in ((bx - 6, bx + 6, -12, -9.0), (bx - 6, bx + 6, 1.0, 6), (bx - 6, bx - 5.0, -9.0, 1.0),
                                 (bx + 5.0, bx + 6, -9.0, 1.0)):
            me = bpy.data.meshes.new(f"C5 ground edge {take}")
            me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
            me.materials.append(mat("C5 ground", (0.18, 0.3, 0.12))); link(bpy.data.objects.new(f"C5 ground edge {take}", me))
world = bpy.data.worlds.new("C5 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.32, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("C5 sun", bpy.data.lights.new("C5 sun", "SUN")))
sun.data.energy = 2.5; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    tree = bpy.data.node_groups.new("C5 Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.6), ("Strength", 0.5), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
cam("Cam all", (16, 30, 18), (16, -3, 1.0), 30)
scene.camera = bpy.data.objects["Cam F1"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
