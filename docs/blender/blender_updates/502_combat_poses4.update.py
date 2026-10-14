# Pass 502: combat poses round 4 (Chat C, 2026-10-14), from J's notes on 221 (P1-P6):
#   P1 "doesnt look like an actual punch" -> IMPROVE: real punches, driven from the hips and the ring shoulder (221 turned
#      the ring shoulder BACK as the arm went out). P1a straight cross, P1b step-in jab, P1c hook. Flash + pixels on impact.
#   P2 "blast is good but the non ring hand shouldnt move so much as the ring hand both first person and third" ->
#      KEEP the blast; the free hand stays braced and follows the ring hand's recoil by only 0% (P2a), 25% (P2b), 50% (P2c).
#   P3 "the shield looks like a worse version of the one we have" -> DROP (the game's shield stays).
#   P4 beam hold "should have maybe a different effect coming out ... the stance should shake a little more ... a looped
#      feedback animation where the ring arm shakes a little and the other arm is to stabilize" -> a 2 s seamless loop:
#      the ring arm shakes (several sine layers), the free hand grips the ring forearm and pushes against it (40% counter
#      shake), legs braced. Three new beams: P4a helix (two pixel strands spiralling a thin core), P4b pulse rings running
#      out along the beam, P4c pixel stream (a beam made of flowing construct pixels). Saturated green, never white.
#   P5 wall "is good but only use the ring arm instead of both hands" -> KEEP the wall; only the ring arm sweeps up. Free
#      arm: P5a hangs relaxed, P5b fist at the chest, P5c out and back for balance.
#   P6 ground slam "is good ... but the animation wastes time by putting the arm up first" -> one smooth drop from standing
#      straight into the slam, no wind-up: P6a 5 ticks, P6b 7 ticks, P6c 10 ticks to impact.
# Every take has "Cam <take>" (over the right shoulder), "Cam <take> fp" (first person, eye height, looking ahead) and
# "Cam <take> front". Takes sit 10 blocks apart so effects don't bleed into each other. 20 ticks a second, 40-tick loops.
# Builds LanternLive\combat\combat_poses4.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "combat_poses4.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Combat Poses 4")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Combat Poses 4")
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


ORDER = ["P1a", "P1b", "P1c", "P2a", "P2b", "P2c", "P4a", "P4b", "P4c", "P5a", "P5b", "P5c", "P6a", "P6b", "P6c"]
NAMES = {"P1a": "straight cross", "P1b": "step-in jab", "P1c": "hook",
         "P2a": "blast - free hand still", "P2b": "blast - free hand 25%", "P2c": "blast - free hand 50%",
         "P4a": "beam - helix", "P4b": "beam - pulse rings", "P4c": "beam - pixel stream",
         "P5a": "wall - free arm relaxed", "P5b": "wall - free fist at chest", "P5c": "wall - free arm back",
         "P6a": "slam - 5 tick drop", "P6b": "slam - 7 tick drop", "P6c": "slam - 10 tick drop"}
SPACING = 10.0
BEAM_LEN = 8.0
dump = {"format": "per take, per tick: part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, ring glow. "
                  "20 ticks a second; every take is a seamless 40-tick loop.", "takes": {}}

for idx, take in enumerate(ORDER):
    base = np.array([idx * SPACING, 0.0, 0.0])
    rng = np.random.default_rng(502 + idx)
    objs = make_player(take)
    rm, _ = emis(f"C4 ring {take}", (0.1, 1.0, 0.25), 2.0); objs["ring"].data.materials[0] = rm
    fpc = fp_cam(f"Cam {take} fp", None)
    fam = take[:2]
    fx = {}
    if fam == "P2":
        fx["bolt"] = unit_cube(f"C4 {take} bolt", BOLT, 1.0)
    elif fam == "P5":
        fx["wall"] = unit_cube(f"C4 {take} wall", HARD, 1.0)
    elif fam == "P6":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, major_segments=48, minor_segments=6)
        w = bpy.context.active_object
        for cc in list(w.users_collection):
            cc.objects.unlink(w)
        link(w); w.name = f"C4 {take} shockwave"; w.data.materials.append(HARD); fx["wave"] = w
    elif fam == "P4":
        root = link(bpy.data.objects.new(f"C4 {take} beam root", None)); root.empty_display_size = 0.2
        fx["root"] = root
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.0, depth=1.0)
        core = bpy.context.active_object
        for cc in list(core.users_collection):
            cc.objects.unlink(core)
        link(core); core.name = f"C4 {take} beam core"; core.data.materials.append(CORE)
        core.parent = root; core.rotation_euler = (R(90), 0, 0)
        r_core = 0.05 if take != "P4c" else 0.03
        core.scale = (r_core, r_core, BEAM_LEN); core.location = (0, -BEAM_LEN / 2, 0)
        parts = []
        if take == "P4a":
            for s in range(2):
                for i in range(36):
                    o = unit_cube(f"C4 {take} strand{s} {i}", PIX if (i + s) % 3 else PIXD, 0.075); o.parent = root
                    parts.append(("helix", o, s, i))
        elif take == "P4b":
            for i in range(8):
                bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.12, major_segments=24, minor_segments=4)
                o = bpy.context.active_object
                for cc in list(o.users_collection):
                    cc.objects.unlink(o)
                link(o); o.name = f"C4 {take} ring{i}"; o.data.materials.append(PIX); o.parent = root
                parts.append(("ring", o, 0, i))
        else:
            for i in range(90):
                o = unit_cube(f"C4 {take} px{i}", PIX if i % 3 else PIXD, 0.06 + 0.04 * rng.random()); o.parent = root
                parts.append(("stream", o, rng.random() * 2 * math.pi, i))
        fx["parts"] = parts
    ticks = []
    for t in range(LOOP + 1):
        f = t + 1
        origin = base.copy()
        glow = 3.0
        if fam == "P1":
            p = keyed(P1_KEYS[take], t)
            if take in STEP:
                origin = origin + np.array([0, -lerp_keys(STEP[take], t), 0])
            glow = 3.0 + (22.0 if any(h <= t < h + 2 for h in HITS[take]) else 0.0)
        elif fam == "P2":
            q = keyed(P2_KEYS, t); p = dict(q)
            k_f = P2_FOLLOW[take]
            p["free"] = add_t(BLAST_SET["free"], np.array(q["ring"]) - np.array(BLAST_SET["ring"]), k_f)
            glow = 2.0 + 12.0 * min(1, max(0, (t - 6) / 16)) if t < 23 else (26.0 if t < 25 else 3.0)
        elif fam == "P4":
            p = dict(BEAM)
            sx = 0.045 * math.sin(5 * TW * t) + 0.025 * math.sin(11 * TW * t + 1.0) + 0.012 * math.sin(17 * TW * t)
            sy = 0.03 * math.sin(7 * TW * t + 2.0) + 0.015 * math.sin(13 * TW * t)
            p["ring"] = add_t(BEAM["ring"], (sx, sy, 0))
            p["free"] = add_t(BEAM["free"], (-0.4 * sx, -0.4 * sy, 0))      # the free hand pushes back against it
            p["body"] = add_t(BEAM["body"], (0.02 * math.sin(5 * TW * t + 0.6), 0.01 * math.sin(3 * TW * t), 0))
            p["head"] = add_t(BEAM["head"], (-0.01 * math.sin(5 * TW * t + 0.6), 0, 0))
            p["sink"] = BEAM["sink"] + 0.25 * math.sin(2 * TW * t)
            glow = 9.0 + 2.5 * math.sin(5 * TW * t) + 1.5 * math.sin(9 * TW * t)
        elif fam == "P5":
            keys = [(dict(STAND), 0), (LOW_R, 8), (LOW_R, 12), (SWEEP_R, 20), (SWEEP_R, 32), (dict(STAND), 40)]
            p = keyed(keys, t); p["free"] = P5_FREE[take]
        else:
            n = P6_DROP[take]; t0 = 4
            keys = [(dict(STAND), 0), (dict(STAND), t0), (SLAM, t0 + n), (SLAM, t0 + n + 12), (dict(STAND), 38),
                    (dict(STAND), 40)]
            p = keyed(keys, t)
            glow = 26.0 if t0 + n <= t < t0 + n + 3 else 3.0
        sol = solve(p)
        set_pose(objs, sol, origin, f)
        key_fp(fpc, sol, origin, f)
        hand = to_bl(hand_point(sol)) + origin
        s_ = rm.node_tree.nodes["Emission"].inputs["Strength"]; s_.default_value = glow; s_.keyframe_insert("default_value", frame=f)
        if fam == "P1" and t in HITS[take]:
            burst(f"C4 {take} hit{t}", hand + np.array([0, -0.15, 0]), f, rng, n=7)
        if fam == "P2":
            b = fx["bolt"]
            if 23 <= t < 33:
                keyo(b, f, loc=hand + np.array([0, -0.4 - (t - 23) * 1.1, 0]), scale=(0.16, 0.7, 0.16))
            else:
                keyo(b, f, loc=hand, scale=(0, 0, 0))
        if fam == "P5":
            w = smooth(min(1, max(0, (t - 12) / 8))) * (1.0 if t < 32 else max(0, 1 - (t - 32) / 6))
            keyo(fx["wall"], f, loc=base + np.array([0, -2.2, 1.0 * w]), scale=(2.8, 0.15, 2.0 * w + 0.001))
        if fam == "P6":
            n = P6_DROP[take]; ti = 4 + n
            r = 0.0 if t < ti else 0.3 + (t - ti) * 0.3
            keyo(fx["wave"], f, loc=base + np.array([0, -0.6, 0.05]),
                 scale=(r, r, r * 0.6) if ti <= t < ti + 16 else (0, 0, 0))
            if t == ti:
                burst(f"C4 {take} impact", hand + np.array([0, 0, 0.1]), f, rng, n=10, fwd=(0, 0, 1))
        if fam == "P4":
            from mathutils import Vector
            d = arm_dir(sol)
            keyo(fx["root"], f, loc=hand, quat=Vector((0, -1, 0)).rotation_difference(Vector(d)))
            for kind, o, a, i in fx["parts"]:
                if kind == "helix":
                    sdist = (i / 36 * BEAM_LEN + 0.4 * t) % BEAM_LEN
                    ang = sdist * 2.4 + a * math.pi + 2 * TW * t
                    rr = 0.17
                    keyo(o, f, loc=(rr * math.cos(ang), -sdist, rr * math.sin(ang)), scale=[min(1, (BEAM_LEN - sdist) / 1.5)] * 3)
                elif kind == "ring":
                    sdist = (i * BEAM_LEN / 8 + 0.2 * t) % BEAM_LEN
                    rr = 0.12 + 0.12 * sdist / BEAM_LEN
                    fade = min(1, (BEAM_LEN - sdist) / 2.0)
                    keyo(o, f, loc=(0, -sdist, 0), scale=(rr * fade, rr * fade, 0.25 * fade + 0.001), rot=(R(90), 0, 0))
                else:
                    ph = a
                    sdist = (i / 90 * BEAM_LEN + 0.4 * t) % BEAM_LEN
                    lat = 0.08 + 0.05 * math.sin(3 * TW * t + ph)
                    keyo(o, f, loc=(lat * math.cos(ph + TW * t * 2), -sdist, lat * math.sin(ph + TW * t * 2)),
                         scale=[min(1, (BEAM_LEN - sdist) / 1.5)] * 3)
        ticks.append({"glow": round(float(glow), 2), "fwd_blocks": round(float(base[1] - origin[1]), 3),
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    if fam == "P4":
        for kind, o, a, i in fx["parts"]:
            ad = o.animation_data
            if ad and ad.action:
                try:
                    for fc in ad.action.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "CONSTANT"
                except Exception:
                    pass
    dump["takes"][take] = {"name": NAMES[take], "ticks": ticks}
    cu = bpy.data.curves.new("C4 label " + take, "FONT"); cu.body = f"{take}  {NAMES[take]}"; cu.size = 0.3
    cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("C4 label " + take, cu)); tl.location = tuple(base + np.array([0, 1.4, 0.01]))
    tl.data.materials.append(mat("C4 label", (0.8, 1.0, 0.85), emit=2.0))
    cam(f"Cam {take}", tuple(base + np.array([-1.1, 2.8, 2.4])), tuple(base + np.array([0.1, -2.2, 0.9])), 30)
    cam(f"Cam {take} front", tuple(base + np.array([2.2, -4.5, 1.5])), tuple(base + np.array([0, -0.4, 0.9])), 35)
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "combat_poses4_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=1, location=(70, -2, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "C4 ground"; g.scale = (220, 80, 1); g.data.materials.append(mat("C4 ground", (0.18, 0.3, 0.12)))
world = bpy.data.worlds.new("C4 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.32, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("C4 sun", bpy.data.lights.new("C4 sun", "SUN")))
sun.data.energy = 2.5; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    tree = bpy.data.node_groups.new("C4 Glow", "CompositorNodeTree")
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
cam("Cam all", (70, 30, 18), (70, -2, 1.0), 30)
scene.camera = bpy.data.objects["Cam P1a"]
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
