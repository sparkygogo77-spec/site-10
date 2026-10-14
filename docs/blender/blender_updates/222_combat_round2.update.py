# Pass 222: combat round 2 (lead Blender chat, 2026-10-14). J: combos, and the free hand "mix per power": it guards
# for strikes, braces the ring wrist for blasts, swings out for balance in the air. Knee rig, 20 ticks a second, the
# body moves for real (steps, jumps, spins); the power stand-ins are simple (the game draws the real effects).
#   K1 jab, jab, blast: two quick ring jabs (free hand in guard), then the free hand braces the wrist for a blast.
#   K2 dodge and counter: a hop to the side away from a hit, then a ring hook back in.
#   K3 aerial slam: jumps two blocks up, hangs, drives down ring-fist first, a ring of light spreads from the landing.
#   K4 launcher: a rising ring uppercut that throws up a hard-light pillar in front.
#   K5 spin backfist: a full spin on the ball of the foot, the ring backfist sweeping an arc of light.
# Cameras "Cam K1".."Cam K5" (over the right shoulder), "Cam K1 front".., "Cam all". Builds LanternLive\combat_round2.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "combat_round2.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Combat Round 2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Combat Round 2")
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


GUARD = P(body=(0.15, -0.35, 0), head=(0.05, 0.3, 0), ring=(-1.15, 0.45, 0.25), free=(-1.25, -0.5, -0.2),
          ringleg=(0.35, 0, 0.12), ringknee=0.35, freeleg=(-0.35, 0, -0.1), freeknee=0.4)
JAB = P(body=(0.22, 0.25, 0), head=(0.0, -0.2, 0), ring=(-1.57, 0.0, 0.05), free=(-1.3, -0.55, -0.2),
        ringleg=(0.45, 0, 0.12), ringknee=0.2, freeleg=(-0.45, 0, -0.1), freeknee=0.45)
BLAST_SET = P(body=(0.1, -0.2, 0), head=(0.0, 0.15, 0), ring=(-1.5, 0.1, 0.05), free=(-1.45, -0.45, -0.1),
              ringleg=(0.45, 0, 0.25), ringknee=0.45, freeleg=(-0.45, 0, -0.25), freeknee=0.45)
BLAST_KICK = P(body=(-0.12, -0.2, 0), head=(-0.15, 0.15, 0), ring=(-1.85, 0.1, 0.05), free=(-1.7, -0.45, -0.1),
               ringleg=(0.5, 0, 0.25), ringknee=0.6, freeleg=(-0.4, 0, -0.25), freeknee=0.4)
SHIELD = P(body=(0.3, -0.15, 0), head=(0.25, 0.1, 0), ring=(-1.55, 0.6, 0.6), free=(-0.7, -0.3, -0.2),
           ringleg=(-0.55, 0, 0.18), ringknee=1.0, freeleg=(0.45, 0, -0.15), freeknee=0.6)
SHIELD_HIT = P(body=(0.05, -0.15, 0), head=(0.0, 0.1, 0), ring=(-1.45, 0.6, 0.6), free=(-0.5, -0.3, -0.25),
               ringleg=(-0.4, 0, 0.18), ringknee=0.75, freeleg=(0.55, 0, -0.15), freeknee=0.5)
BEAM = P(body=(-0.05, -0.25, 0), head=(0.0, 0.2, 0), ring=(-1.57, 0.2, 0.0), free=(-1.2, -0.6, -0.3),
         ringleg=(0.55, 0, 0.2), ringknee=0.5, freeleg=(-0.4, 0, -0.2), freeknee=0.35)
LOW = P(body=(0.45, 0, 0), head=(0.1, 0, 0), ring=(0.35, 0, 0.35), free=(0.35, 0, -0.35),
        ringleg=(-0.6, 0, 0.2), ringknee=1.2, freeleg=(-0.6, 0, -0.2), freeknee=1.2)
SWEEP = P(body=(-0.1, 0, 0), head=(-0.2, 0, 0), ring=(-2.6, 0, 0.45), free=(-2.6, 0, -0.45),
          ringleg=(0.05, 0, 0.12), ringknee=0.1, freeleg=(0.05, 0, -0.12), freeknee=0.1)
CROUCH = P(body=(0.5, 0, 0), head=(-0.3, 0, 0), ring=(-2.7, 0, 0.1), free=(0.7, 0, -0.3),
           ringleg=(-0.8, 0, 0.1), ringknee=1.5, freeleg=(-0.6, 0, -0.1), freeknee=1.3)
SLAM = P(body=(0.9, 0, 0), head=(-0.6, 0, 0), ring=(-0.2, 0, 0.1), free=(0.9, 0, -0.5),
         ringleg=(0.2, 0, 0.06), ringknee=1.35, freeleg=(-1.2, 0, -0.08), freeknee=1.3)
STANDP = P(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.05), free=(0.05, 0, -0.05))

def keyed(keys, t):
    for (pa, ta), (pb, tb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return mixp(pa, pb, 0 if tb == ta else smooth((t - ta) / (tb - ta)))
    return keys[-1][0]


def keyo(o, f, loc=None, scale=None, rot=None):
    if loc is not None:
        o.location = tuple(loc); o.keyframe_insert("location", frame=f)
    if scale is not None:
        o.scale = tuple(scale); o.keyframe_insert("scale", frame=f)
    if rot is not None:
        o.rotation_euler = tuple(rot); o.keyframe_insert("rotation_euler", frame=f)



HOOK = P(body=(0.2, 0.55, 0), head=(0.0, -0.35, 0), ring=(-1.5, -0.7, 0.9), free=(-1.25, -0.5, -0.2),
         ringleg=(0.4, 0, 0.12), ringknee=0.3, freeleg=(-0.45, 0, -0.1), freeknee=0.45)
DODGE = P(body=(0.25, 0, -0.35), head=(0.05, 0, 0.3), ring=(-1.0, 0.3, 0.6), free=(-1.1, -0.4, -0.5),
          ringleg=(0.1, 0, 0.35), ringknee=0.6, freeleg=(-0.3, 0, -0.05), freeknee=0.5)
AIR = P(body=(0.2, 0, 0), head=(-0.4, 0, 0), ring=(-2.9, 0, 0.2), free=(-0.3, 0, -1.2),
        ringleg=(-0.9, 0, 0.1), ringknee=1.6, freeleg=(-0.6, 0, -0.1), freeknee=1.5, grounded=False)
UPPER_LOAD = P(body=(0.45, -0.3, 0), head=(0.1, 0.2, 0), ring=(0.4, 0, 0.3), free=(-1.25, -0.5, -0.2),
               ringleg=(-0.6, 0, 0.15), ringknee=1.2, freeleg=(-0.2, 0, -0.15), freeknee=0.9)
UPPER = P(body=(-0.15, 0.3, 0), head=(-0.3, -0.2, 0), ring=(-2.8, 0.2, 0.15), free=(-1.25, -0.5, -0.2),
          ringleg=(0.1, 0, 0.1), ringknee=0.1, freeleg=(0.2, 0, -0.1), freeknee=0.3)
BACKFIST = P(body=(0.1, 0, 0), head=(0.0, 0, 0), ring=(-1.57, -0.9, 0.2), free=(0.3, 0, -0.5),
             ringleg=(0.25, 0, 0.1), ringknee=0.3, freeleg=(-0.2, 0, -0.1), freeknee=0.3)
LOOP = 70


def root_motion(take, t):
    """(dx, dy forward, dz up, yaw) of the body in blocks / radians."""
    if take == "K2":
        if 10 <= t < 18:
            return (0.9 * smooth((t - 10) / 8), 0, 0.25 * math.sin(math.pi * (t - 10) / 8), 0)
        if t >= 18:
            back = smooth(min(1, max(0, (t - 26) / 10)))
            return (0.9 * (1 - back), -0.3 * back, 0, 0)
        return (0, 0, 0, 0)
    if take == "K3":
        if 8 <= t < 22:
            u = (t - 8) / 14
            return (0, -0.6 * u, 2.0 * math.sin(math.pi * u * 0.5) if u < 1 else 2.0, 0)
        if 22 <= t < 30:
            return (0, -0.6, 2.0, 0)
        if 30 <= t < 34:
            u = (t - 30) / 4
            return (0, -0.6 - 0.3 * u, 2.0 * (1 - u * u), 0)
        return (0, -0.9, 0, 0)
    if take == "K5":
        if 12 <= t < 26:
            return (0, -0.2 * (t - 12) / 14, 0, 2 * math.pi * smooth((t - 12) / 14))
        return (0, -0.2 if t >= 26 else 0, 0, 0)
    return (0, 0, 0, 0)


TAKES = {
    "K1": ("jab, jab, blast", [(GUARD, 0), (GUARD, 6), (JAB, 9), (GUARD, 15), (JAB, 18), (GUARD, 24), (BLAST_SET, 32),
                               (BLAST_SET, 44), (BLAST_KICK, 46), (BLAST_KICK, 50), (GUARD, 62), (GUARD, 70)]),
    "K2": ("dodge and counter", [(GUARD, 0), (GUARD, 9), (DODGE, 14), (DODGE, 20), (HOOK, 26), (HOOK, 30), (GUARD, 42), (GUARD, 70)]),
    "K3": ("aerial slam", [(STANDP, 0), (CROUCH, 6), (AIR, 14), (AIR, 30), (SLAM, 34), (SLAM, 50), (STANDP, 64), (STANDP, 70)]),
    "K4": ("launcher", [(GUARD, 0), (UPPER_LOAD, 10), (UPPER_LOAD, 14), (UPPER, 19), (UPPER, 30), (GUARD, 44), (GUARD, 70)]),
    "K5": ("spin backfist", [(GUARD, 0), (GUARD, 10), (BACKFIST, 22), (BACKFIST, 30), (GUARD, 42), (GUARD, 70)]),
}
JADE_T, _ = emis("CR hard light", (0.2, 1.0, 0.4), 3.0, alpha=0.45)
BOLT, _ = emis("CR bolt", (0.4, 1.0, 0.55), 12.0)
for k, (take, (nm, keys)) in enumerate(TAKES.items()):
    base = np.array([k * 4.5, 0.0, 0.0])
    objs = make_player(take)
    rm, _ = emis(f"CR ring {take}", (0.1, 1.0, 0.25), 2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"CR {take} mover", None))
    fx = None
    if take == "K1":
        fx = cube("CR K1 bolt", BOLT, 0.25)
    elif take == "K3":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, major_segments=48, minor_segments=6)
        fx = bpy.context.active_object
        for cc in list(fx.users_collection):
            cc.objects.unlink(fx)
        link(fx); fx.name = "CR K3 shockwave"; fx.data.materials.append(JADE_T)
    elif take == "K4":
        fx = cube("CR K4 pillar", JADE_T, 1.0)
    elif take == "K5":
        arc = [cube(f"CR K5 arc {i}", BOLT, 0.12) for i in range(14)]
    trail = []
    for t in range(LOOP + 1):
        dx, dy, dz, yaw = root_motion(take, t)
        origin = base + np.array([dx, dy, dz])
        sol = solve(keyed(keys, t))
        set_pose(objs, sol, origin, t + 1, yaw)
        mover.location = tuple(base + np.array([dx * 0.5, dy, dz * 0.4])); mover.keyframe_insert("location", frame=t + 1)
        rs = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
        hand = rs @ to_bl(hand_point(sol)) + origin
        e = 2.0
        if take == "K1":
            e = 25.0 if t in (9, 10, 18, 19) else (2 + 12 * min(1, max(0, (t - 32) / 12)) if 32 <= t < 45 else (40 if 45 <= t < 47 else 3))
            if 45 <= t < 60:
                keyo(fx, t + 1, loc=hand + np.array([0, -(t - 45) * 0.9, 0]), scale=(1, 1, 1))
            else:
                keyo(fx, t + 1, loc=hand, scale=(0, 0, 0))
        elif take == "K2":
            e = 25.0 if t in (26, 27) else 3.0
        elif take == "K3":
            e = 6.0 if 14 <= t < 34 else (35.0 if 34 <= t < 37 else 3.0)
            r = 0.0 if t < 34 else 0.3 + (t - 34) * 0.4
            keyo(fx, t + 1, loc=base + np.array([0, -1.5, 0.05]), scale=(r, r, r * 0.6 if t < 58 else 0.0))
        elif take == "K4":
            w = smooth(min(1, max(0, (t - 17) / 5))) * (1 if t < 44 else max(0, 1 - (t - 44) / 6))
            e = 3.0 + 25.0 * (1 if 18 <= t < 21 else 0)
            keyo(fx, t + 1, loc=base + np.array([0, -1.6, 1.25 * w]), scale=(0.9, 0.9, 2.5 * w + 0.001))
        elif take == "K5":
            e = 8.0 if 12 <= t < 30 else 3.0
            trail.append(hand.copy())
            for i, a in enumerate(arc):
                on = 12 <= t < 34 and t - i >= 12
                keyo(a, t + 1, loc=trail[max(0, len(trail) - 1 - i)], scale=(1, 1, 1) if on else (0, 0, 0))
        s_ = rm.node_tree.nodes["Emission"].inputs["Strength"]; s_.default_value = e; s_.keyframe_insert("default_value", frame=t + 1)
    cu = bpy.data.curves.new("CR label " + take, "FONT"); cu.body = f"{take}  {nm}"; cu.size = 0.3; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("CR label " + take, cu)); tl.location = tuple(base + np.array([0, 1.4, 0.01]))
    tl.data.materials.append(mat("CR label", (0.8, 1.0, 0.85), emit=2.0))
    for nm_, loc, look, lens in ((f"Cam {take}", (-1.1, 3.0, 2.6), (0.1, -2.2, 1.0), 30),
                                 (f"Cam {take} front", (2.0, -4.4, 1.6), (0, -0.4, 1.0), 33)):
        c = cam(nm_, tuple(base + np.array(loc)), tuple(base + np.array(look)), lens)
        scene.frame_set(1); bpy.context.view_layer.update()
        mw = c.matrix_world.copy(); c.parent = mover; c.matrix_world = mw
    print(take, "built", flush=True)

scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=50, location=(9, -2, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "CR ground"; g.data.materials.append(mat("CR ground", (0.18, 0.3, 0.12)))
world = bpy.data.worlds.new("CR world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.32, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("CR sun", bpy.data.lights.new("CR sun", "SUN")))
sun.data.energy = 2.5; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
cam("Cam all", (9, -15, 5), (9, 0, 1.0), 30)
scene.camera = bpy.data.objects["Cam K1 front"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    try:
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
