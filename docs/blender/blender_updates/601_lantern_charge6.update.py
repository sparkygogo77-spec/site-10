# Pass 601: the lantern charge in 6 seconds (Chat D, lanterns/charging, 2026-10-14). J: "I need a much shorter charge
# animation now maybe 6 seconds to match how much animation time we have with the lantern".
# KEEP: L1c (picked) - stand, half step in, ring fist into the emblem port, two pushes that tip the lantern; the charge
# light running from the port down the whole lantern (fill front h = 1.05 - 1.15 x charge, bright band, saturated);
# the G3 order: fill -> overcharge -> let-go flash -> fade, spin one way, gold cracks dim, never white.
# NEW: the whole thing fits 6 s (120 ticks): L1c's pushes stretched to fit (idle 0, lean 9, push 30, lean 52, push 74,
# lean 96, idle 120), and three ways to split the 6 s:
#   C6a  fill 4 s (ticks 9-90), overcharge 1 s (90-110, pulsing to 1.25), let-go flash + fade 0.5 s (110-120)
#   C6b  fill 4.5 s (9-100), overcharge 0.6 s (100-112), let-go 0.4 s (112-120)
#   C6c  fill 3.3 s (9-75), overcharge 1.5 s (75-105), let-go 0.75 s (105-120)
# After the let-go the lantern settles to its idle glow (0.12). Cameras "Cam C6a".."Cam C6c" (side), "Cam leans".
# Builds LanternLive\lanterns\lantern_charge6.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "lantern_charge6.blend")
ASSETS = os.path.join(FOLDER, "kl_assets")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Kneel Lean 4")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Kneel Lean 4")
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
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")   # knees (as pass 208): J, "kneel, not splits"
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


def euler_of(Rm):
    """XYZ euler (x, y, z) of R = Rz @ Ry @ Rx, the inverse of rot()."""
    y = math.asin(max(-1.0, min(1.0, -Rm[2, 0])))
    return (math.atan2(Rm[2, 1], Rm[2, 2]), y, math.atan2(Rm[1, 0], Rm[0, 0]))


def solve(p):
    """Pose (ring = right side) -> per part rotation and pivot. The body turns about the hips, the legs hang from the
    hips, grounded poses drop the hips until the lowest foot touches, `sink` lowers the torso into the legs."""
    rot_ = {"body": p.get("body", (0, 0, 0)), "head": p.get("head", (0, 0, 0))}
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
        rot_[shin] = euler_of(rot(*rot_[leg]) @ rot(float(p.get(kk, 0.0)), 0, 0))
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


# ------------------------------------------------------------------ the poses
IDLE = dict(ring=(0.05, 0, 0.05), free=(0.05, 0, 0.05))
P = {
    # K1 one knee
    "K1_down": dict(body=(0.38, 0, 0), head=(0.35, 0, 0), ring=(-0.55, 0, 0.12), free=(-0.35, 0.2, -0.15),
                    ringleg=(1.05, 0, 0.05), freeleg=(-0.95, 0, -0.08), sink=2.0),
    "K1_grab": dict(body=(0.35, 0, 0), head=(0.45, 0, 0), ring=(-0.25, 0, 0.1), free=(-0.45, 0.2, -0.15),
                    ringleg=(1.05, 0, 0.05), freeleg=(-0.95, 0, -0.08), sink=3.0),
    "K1_lift": dict(body=(0.15, 0, 0), head=(0.1, 0, 0), ring=(-1.2, -0.35, 0.05), free=(-1.0, 0.45, 0),
                    ringleg=(0.95, 0, 0.05), freeleg=(-0.9, 0, -0.08), sink=1.0),
    "K1_stand": dict(body=(0.0, 0, 0), head=(0.1, 0, 0), ring=(-0.95, -0.4, 0.05), free=(-0.85, 0.45, 0)),
    # K2 squat
    "K2_down": dict(body=(0.75, 0, 0), head=(0.2, 0, 0), ring=(-0.65, 0.15, 0.1), free=(-0.65, 0.15, 0.1),
                    ringleg=(-0.7, 0, 0.4), freeleg=(-0.7, 0, 0.4), sink=5.0),
    "K2_grab": dict(body=(0.95, 0, 0), head=(0.35, 0, 0), ring=(-0.4, 0.3, 0.05), free=(-0.4, 0.3, 0.05),
                    ringleg=(-0.7, 0, 0.4), freeleg=(-0.7, 0, 0.4), sink=6.0),
    "K2_lift": dict(body=(0.3, 0, 0), head=(0.1, 0, 0), ring=(-1.05, 0.35, 0), free=(-1.05, 0.35, 0),
                    ringleg=(-0.45, 0, 0.2), freeleg=(-0.45, 0, 0.2), sink=2.0),
    "K2_stand": dict(body=(0.0, 0, 0), head=(0.05, 0, 0), ring=(-0.9, 0.35, 0), free=(-0.9, 0.35, 0)),
    # K3 vow
    "K3_kneel": dict(body=(0.2, 0, 0), head=(0.75, 0, 0), ring=(-0.7, 0, 0.1), free=(0.15, 0, -0.1),
                     ringleg=(0.12, 0, 0.0), ringknee=1.5, freeleg=(-1.42, 0, -0.05), freeknee=1.42),
    "K3_vow": dict(body=(0.3, 0, 0), head=(0.8, 0, 0), ring=(-0.45, 0, 0.1), free=(0.2, 0, -0.1),
                   ringleg=(0.12, 0, 0.0), ringknee=1.5, freeleg=(-1.42, 0, -0.05), freeknee=1.42),
    "K3_raise": dict(body=(-0.1, 0, 0), head=(-0.55, 0, 0), ring=(-2.9, 0, 0.1), free=(0.1, 0, 0.2),
                     ringleg=(0.95, 0, 0.0), freeleg=(-1.2, 0, -0.05), sink=1.0),
    "K3_stand": dict(body=(0.0, 0, 0), head=(0.1, 0, 0), ring=(-1.0, -0.4, 0.05), free=(-0.2, 0, 0.05)),
    # leans: the lantern stands on a block one block in front, its port at about shoulder height
    "L1_lean": dict(body=(0.32, 0, 0), head=(0.15, 0, 0), ring=(-1.25, 0, 0.12), free=(-0.75, -0.35, -0.2),
                    ringleg=(0.32, 0, 0.06), freeleg=(-0.3, 0, -0.04), fwd=1.0),
    "L1_push": dict(body=(0.45, 0, 0), head=(0.25, 0, 0), ring=(-1.15, 0, 0.12), free=(-0.85, -0.35, -0.2),
                    ringleg=(0.42, 0, 0.06), freeleg=(-0.32, 0, -0.04), fwd=1.5),
    "L2_lean": dict(body=(0.28, 0, 0), head=(0.55, 0, 0), ring=(-1.85, 0, 0.18), free=(0.05, 0, 0.75),
                    ringleg=(0.2, 0, 0.05), freeleg=(-0.15, 0, -0.03), fwd=0.5),
    "L2_push": dict(body=(0.38, 0, 0), head=(0.7, 0, 0), ring=(-1.75, 0, 0.18), free=(0.05, 0, 0.8),
                    ringleg=(0.25, 0, 0.05), freeleg=(-0.15, 0, -0.03), fwd=1.0),
    "L3_lean": dict(body=(0.05, -0.35, -0.22), head=(-0.05, 0.25, 0.1), ring=(-1.55, 0.35, 0.55),
                    free=(0.15, 0, 0.35), ringleg=(0.05, 0, -0.22), freeleg=(-0.05, 0, 0.28), fwd=2.5),
    "L3_push": dict(body=(0.1, -0.4, -0.26), head=(0.05, 0.3, 0.1), ring=(-1.5, 0.35, 0.6),
                    free=(0.15, 0, 0.4), ringleg=(0.05, 0, -0.22), freeleg=(-0.05, 0, 0.28), fwd=2.8),
}
def pose_of(name):
    return IDLE if name == "idle" else P[name]


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


def pose_at(t, keys):
    for (na, ta), (nb, tb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = 0 if tb == ta else smooth((t - ta) / (tb - ta))
            return mixp(pose_of(na), pose_of(nb), w)
    return pose_of(keys[-1][0])


# ------------------------------------------------------------------ materials and meshes
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


HANDLE_PX = 15.5                                   # handle height above the lantern's base


def fit_reach(name, two=False):
    """Tilt the reaching arm(s) of a grab pose so the hand comes down to the lantern's handle height, out in front."""
    p = P[name]
    best = None
    for x in np.linspace(-1.8, -0.2, 161):
        q = dict(p); q["ring"] = (x, p["ring"][1], p["ring"][2])
        if two:
            q["free"] = (x, p["free"][1], p["free"][2])
        sol = solve(q)
        hp = hand_point(sol, "rarm")
        err = abs((GROUND - hp[1]) - HANDLE_PX) - 0.02 * (-hp[2])       # at handle height, as far forward as can be
        if best is None or err < best[0]:
            best = (err, x)
    p["ring"] = (best[1], p["ring"][1], p["ring"][2])
    if two:
        p["free"] = (best[1], p["free"][1], p["free"][2])



# ------------------------------------------------------------------ round 3 changes to the poses
fit_reach("K3_vow")
P["K3_kneel"]["ring"] = tuple(np.array(P["K3_vow"]["ring"]) * 0.8)
# lift to the chest, not overhead: arm forward and a little up, head level (round 1 had ring -2.9, head -0.55)
P["K3_raise"] = dict(body=(-0.05, 0, 0), head=(-0.12, 0, 0), ring=(-1.45, -0.25, 0.08), free=(-0.35, 0.3, 0.1),
                     ringleg=(0.12, 0, 0.0), ringknee=1.5, freeleg=(-1.42, 0, -0.05), freeknee=1.42)
P["K3_stand"] = dict(body=(0.0, 0, 0), head=(0.08, 0, 0), ring=(-1.05, -0.35, 0.05), free=(-0.2, 0, 0.05))
# lean bodies (the ring arm and the forward lean are solved every tick, so only the rest of the body is set here)
P.update({
    "L1c_lean": dict(body=(0.12, 0, 0), head=(0.1, 0, 0), ring=(-1.5, 0, 0.1), free=(0.45, 0, -0.12),
                     ringleg=(0.38, 0, 0.04), freeleg=(-0.3, 0, -0.04)),
    "L1c_push": dict(body=(0.2, 0, 0), head=(0.15, 0, 0), ring=(-1.5, 0, 0.1), free=(0.6, 0, -0.15),
                     ringleg=(0.48, 0, 0.04), freeleg=(-0.36, 0, -0.04)),
    "L1d_lean": dict(body=(0.32, 0, 0), head=(0.2, 0, 0), ring=(-1.4, 0, 0.1), free=(-1.3, 0, -0.35),
                     ringleg=(0.42, 0, 0.06), freeleg=(-0.32, 0, -0.05)),
    "L1d_push": dict(body=(0.42, 0, 0), head=(0.3, 0, 0), ring=(-1.4, 0, 0.1), free=(-1.3, 0, -0.35),
                     ringleg=(0.52, 0, 0.06), freeleg=(-0.36, 0, -0.05)),
    "L1e_lean": dict(body=(0.42, 0, 0), head=(0.32, 0, 0), ring=(-1.1, 0, 0.1), free=(0.4, 0, -0.15),
                     ringleg=(0.2, 0, 0.12), freeleg=(-0.25, 0, -0.12)),
    "L1e_push": dict(body=(0.5, 0, 0), head=(0.38, 0, 0), ring=(-1.1, 0, 0.1), free=(0.5, 0, -0.15),
                     ringleg=(0.26, 0, 0.12), freeleg=(-0.3, 0, -0.12)),
    "L2c_lean": dict(body=(0.18, 0, 0), head=(0.5, 0, 0), ring=(-1.6, 0, 0.1), free=(-2.0, 0, -0.3),
                     ringleg=(0.2, 0, 0.05), freeleg=(-0.15, 0, -0.03)),
    "L2c_push": dict(body=(0.26, 0, 0), head=(0.65, 0, 0), ring=(-1.6, 0, 0.1), free=(-2.0, 0, -0.3),
                     ringleg=(0.25, 0, 0.05), freeleg=(-0.17, 0, -0.03)),
})


def lean_keys(n):
    return [("idle", 0), (n + "_lean", 9), (n + "_push", 26), (n + "_lean", 42), (n + "_push", 58), (n + "_lean", 70),
            ("idle", 84)]


def keys6(n):
    return [("idle", 0), (n + "_lean", 9), (n + "_push", 30), (n + "_lean", 52), (n + "_push", 74), (n + "_lean", 96),
            ("idle", 120)]


CURVES = {"C6a": (9, 90, 110, 120), "C6b": (9, 100, 112, 120), "C6c": (9, 75, 105, 120)}


def charge6(take, t):
    """0..1 fill, then overcharge pulsing up to 1.25, a let-go flash, then a fast fade to the idle 0.12."""
    a, b, c, d = CURVES[take]
    if t < a:
        return 0.12
    if t <= b:
        return 0.12 + 0.88 * smooth((t - a) / (b - a))
    if t <= c:
        u = (t - b) / (c - b)
        return 1.0 + 0.25 * u * (0.75 + 0.25 * math.sin(t * 1.3))
    if t <= d:
        u = (t - c) / max(1, d - c)
        return (1.6 if t - c < 2 else 1.25 * (1 - u) + 0.12 * u)
    return 0.12


TAKES6 = {k: dict(keys=keys6("L1c"), lantern="block", charge=(CURVES[k][0], CURVES[k][1]), hand="fist", free=None)
          for k in CURVES}
_TAKES_OLD = {
    "K3c": dict(keys=[("idle", 0), ("K3_kneel", 10), ("K3_vow", 16), ("K3_vow", 30), ("K3_raise", 44), ("K3_raise", 52),
                      ("K3_stand", 62), ("K3_stand", 84)], carry=30, lantern="ground", flare=(16, 30), glow=(10, 72)),
    "L1c": dict(keys=lean_keys("L1c"), lantern="block", charge=(9, 70), hand="fist", free=None),
    "L1d": dict(keys=lean_keys("L1d"), lantern="block", charge=(9, 70), hand="fist", free="side"),
    "L1e": dict(keys=lean_keys("L1e"), lantern="block", charge=(9, 70), hand="fist", free=None),
    "L2c": dict(keys=lean_keys("L2c"), lantern="block", charge=(9, 70), hand="palm", free="top"),
}
TAKES = TAKES6
PUSH = {"idle": 0.0}
for _n in ("L1c", "L1d", "L1e", "L2c"):
    PUSH[_n + "_lean"] = 0.45; PUSH[_n + "_push"] = 1.0

# ------------------------------------------------------------------ the lantern as a solid (rig space: px, y down, -z forward)
LH = 16.0                       # placed height with the handle
DL_H, DL_W, DL_BODY = 28.5, 11.0, 21.0  # dark_lantern.bbmodel: height, width, top of the body (handle above)
S_DL = LH / DL_H
HW = DL_W * S_DL / 2            # half width of the body
BODY_H = DL_BODY * S_DL         # body height
BLOCK_TOP = GROUND - 16.0
PORT_Y = BODY_H * 0.52          # the emblem port's centre above the base
PORT_R = 2.4                    # half size of the port opening (a fist is 4 px across)
PORT_D = 3.0                    # how deep the port goes


def box_sdf(q, lo, hi):
    """Signed distance from points q (n,3) to an axis-aligned box: negative inside."""
    c = (lo + hi) / 2; h = (hi - lo) / 2
    d = np.abs(q - c) - h
    out = np.linalg.norm(np.maximum(d, 0), axis=1)
    ins = np.minimum(d.max(1), 0)
    return out + ins


class Lantern:
    """Base centre at (x0, base_y, z0); tilt > 0 tips the top away from the player (toward -z) about the far edge."""

    def __init__(self, x0, base_y, z0):
        self.x0, self.base_y, self.z0, self.tilt = x0, base_y, z0, 0.0

    def to_local(self, q):
        piv = np.array([self.x0, self.base_y, self.z0 - HW])
        a = -self.tilt
        Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        return (q - piv) @ Rx.T + piv

    def sdf(self, q):
        p = self.to_local(q)
        x0, y0, z0 = self.x0, self.base_y, self.z0
        body = box_sdf(p, np.array([x0 - HW, y0 - BODY_H, z0 - HW]), np.array([x0 + HW, y0, z0 + HW]))
        handle = box_sdf(p, np.array([x0 - HW * 0.8, y0 - LH, z0 - 0.5]), np.array([x0 + HW * 0.8, y0 - BODY_H, z0 + 0.5]))
        solid = np.minimum(body, handle)
        port = box_sdf(p, *self.port_box())
        return np.maximum(solid, -port)               # the port is a recess the fist can go into

    def port_box(self):
        y = self.base_y - PORT_Y
        return (np.array([self.x0 - PORT_R, y - PORT_R, self.z0 + HW - PORT_D]),
                np.array([self.x0 + PORT_R, y + PORT_R, self.z0 + HW + 0.5]))

    def world(self, local_pt):
        M = self.matrix()
        return M[:3, :3] @ (np.asarray(local_pt, float) - np.array([self.x0, self.base_y, self.z0])) + M[:3, 3]

    def port_target(self, depth):
        """The port's centre, `depth` px in from the front face, on the lantern as tilted now."""
        return self.world((self.x0, self.base_y - PORT_Y, self.z0 + HW - depth))

    def side_target(self):
        return self.world((self.x0 + HW + 2.6, self.base_y - BODY_H * 0.62, self.z0))      # palm on the side: hand centre 2 px out

    def top_target(self):
        return self.world((self.x0 + 1.0, self.base_y - BODY_H - 2.6, self.z0 + HW * 0.9))      # hand resting on the shoulder

    def matrix(self):
        """Rig-space 4x4 of the lantern's base frame (rotation about the far bottom edge)."""
        a = self.tilt
        Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        piv = np.array([self.x0, self.base_y, self.z0 - HW])
        base = np.array([self.x0, self.base_y, self.z0])
        M = np.eye(4); M[:3, :3] = Rx; M[:3, 3] = Rx @ (base - piv) + piv
        return M


def block_sdf(q, bx, bz):
    return box_sdf(q, np.array([bx - 8, BLOCK_TOP, bz - 8]), np.array([bx + 8, GROUND, bz + 8]))


_G = np.linspace(0, 1, 4)


def part_points(sol, part):
    a, b = (np.array(v, float) for v in BOX[part])
    pts = np.array([a + (b - a) * np.array([u, v, w]) for u in _G for v in _G for w in _G])
    r, pv = sol[part]
    return pts @ rot(*r).T + pv


def clearance(sol, parts, lan, block):
    q = np.concatenate([part_points(sol, k) for k in parts])
    d = lan.sdf(q)
    if block is not None:
        d = np.minimum(d, block_sdf(q, *block))
    return float(d.min())


BODYPARTS = ("head", "body", "larm", "rleg", "lleg", "rshin", "lshin")


ARM_TIP = {"fist": np.array([-1.0, 10.0, 0.0]), "palm": np.array([-1.0, 10.0, 0.0])}   # palm: the flat of the hand on the face
FREE_TIP = np.array([1.0, 9.6, -2.0])
_XS, _YS = np.meshgrid(np.arange(-2.7, -0.2, 0.006), np.arange(-1.1, 1.1, 0.006), indexing="ij")


def _rot_many(x, y, z):
    """rot(x, y, z) for arrays of x and y (z fixed): (n, 3, 3). x lifts the arm, y swings it across the body."""
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), math.cos(z), math.sin(z)
    n = x.size
    Rx = np.zeros((n, 3, 3)); Rx[:, 0, 0] = 1; Rx[:, 1, 1] = cx; Rx[:, 1, 2] = -sx; Rx[:, 2, 1] = sx; Rx[:, 2, 2] = cx
    Ry = np.zeros((n, 3, 3)); Ry[:, 0, 0] = cy; Ry[:, 0, 2] = sy; Ry[:, 1, 1] = 1; Ry[:, 2, 0] = -sy; Ry[:, 2, 2] = cy
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def reach(pivot, tip_local, target, z_rot, sgn=1, fwd_free=True):
    """Arm angles (x lift, y swing across) putting the arm's tip on target. With fwd_free the forward offset is solved
    too (returned); else the tip must hit the target in all three axes."""
    x = _XS.ravel(); y = _YS.ravel()
    tips = (_rot_many(x, sgn * y, sgn * z_rot) @ tip_local) + pivot
    if fwd_free:
        err = (tips[:, 0] - target[0]) ** 2 + (tips[:, 1] - target[1]) ** 2 + 0.002 * (x + 1.57) ** 2
    else:
        err = ((tips - target) ** 2).sum(1)
    i = int(np.argmin(err))
    fwd = float(tips[i, 2] - target[2]) if fwd_free else 0.0
    return float(x[i]), float(y[i]), fwd, float(err[i])


def port_pose(p, lan, block, hand, free, press):
    """The pose with the ring fist (or palm) on the port and the forward lean that puts it there."""
    q = dict(p)
    q.pop("fwd", None)
    sol0 = solve(dict(q, fwd=0.0))
    depth = (0.5 + 0.7 * press) if hand == "fist" else -0.7      # the knuckles in the port, the ring at its mouth
    tgt = lan.port_target(depth)
    rx, ry, fwd, err = reach(sol0["rarm"][1], ARM_TIP[hand], tgt, p["ring"][2], 1, True)
    q["ring"] = (rx, ry, p["ring"][2]); q["fwd"] = fwd
    # the stance must not step into the block: close the legs in until they clear it
    legs = (p.get("ringleg", (0, 0, 0)), p.get("freeleg", (0, 0, 0)))
    for k in np.linspace(1.0, 0.0, 11):
        q["ringleg"] = tuple(np.array(legs[0]) * k); q["freeleg"] = tuple(np.array(legs[1]) * k)
        if clearance(solve(q), ("rleg", "lleg", "rshin", "lshin"), lan, block) >= 0:
            break
    if free:
        sol1 = solve(q)
        ft = lan.side_target() if free == "side" else lan.top_target()
        fx, fy, _, _ = reach(sol1["larm"][1], FREE_TIP, ft, p["free"][2], -1, False)
        q["free"] = (fx, fy, p["free"][2])
    return q


def push_at(t, keys):
    for (na, ta), (nb, tb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = 0 if tb == ta else smooth((t - ta) / (tb - ta))
            return PUSH.get(na, 0.0) + (PUSH.get(nb, 0.0) - PUSH.get(na, 0.0)) * w
    return PUSH.get(keys[-1][0], 0.0)


def rock(push, ticks, tilt_max=R(7.0), freq=2.6, zeta=0.18, sub=20):
    """The lantern rocking on the block: a damped spring toward the static tilt the push holds it at, and it can't
    tip back past upright (it sits on its base): theta'' = w^2 (A*push - theta) - 2 zeta w theta'."""
    w = 2 * math.pi * freq
    th = om = 0.0
    out = []
    dt = 1 / 20 / sub
    for t in range(ticks + 1):
        for _ in range(sub):
            acc = w * w * (tilt_max * push[t] - th) - 2 * zeta * w * om
            om += acc * dt; th += om * dt
            if th < 0:
                th, om = 0.0, -0.35 * om       # lands on its base: a small bounce
        out.append(th)
    return out


def carry_physics(hands, carry, spot, zeta=0.12, sub=20):
    """The lantern picked up by its handle. While the grip is lower than the lantern is tall, the base stays on the floor
    and slides/tips under the hand (it can't be shorter than it is). Once the grip lifts it clear it hangs and swings,
    starting from the tilt and spin it had on the floor: phi'' = -(g/Lc) sin phi + drive(a)/Lc - 2 zeta w phi',
    where the drive makes it lag the hand (it swings against the motion). Returns (phi_x, phi_z) per tick."""
    Lg = LH - 0.5                                   # grip to base
    Lc = Lg - BODY_H / 2                            # grip to the centre of mass
    g = 9.81 * 16
    w0 = math.sqrt(g / Lc)
    hands = np.asarray(hands, float)
    acc = np.gradient(np.gradient(hands, 1 / 20, axis=0), 1 / 20, axis=0)
    B = np.array(spot, float)
    phi = np.zeros(2); om = np.zeros(2); airborne = False
    out = []
    dt = 1 / 20 / sub
    last_dir = np.array([0.0, -1.0])
    for t in range(len(hands)):
        if t < carry:
            out.append(np.zeros(2)); continue
        grip = hands[t]
        h = GROUND - grip[1]
        if not airborne and h < Lg - 0.02:
            d = np.array([B[0] - grip[0], B[2] - grip[2]])
            r = math.sqrt(max(Lg * Lg - h * h, 0.0))
            n = float(np.hypot(*d))
            u = d / n if n > 1e-6 else last_dir
            last_dir = u
            B[0], B[2] = grip[0] + u[0] * r, grip[2] + u[1] * r
            new = np.array([math.asin(max(-1, min(1, (grip[0] - B[0]) / Lg))),
                            math.asin(max(-1, min(1, (B[2] - grip[2]) / Lg)))])
            om = (new - phi) * 20; phi = new
        else:
            airborne = True
            a = np.array([acc[t, 0], -acc[t, 2]])
            for _ in range(sub):
                al = -(g / Lc) * np.sin(phi) + (a / Lc) * np.cos(phi) - 2 * zeta * w0 * om
                om = om + al * dt; phi = phi + om * dt
        out.append(phi.copy())
    return out


# ------------------------------------------------------------------ the Dark Lantern meshes
def import_lantern(tag):
    root = link(bpy.data.objects.new(f"KL4 {tag} lantern", None))
    root.empty_display_size = 0.05
    glow_mats = []
    charge_vals = []
    for name in ("dark_lantern", "dark_lantern_glow"):
        path = os.path.join(ASSETS, name + ".glb")
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            if o.type == "MESH":
                mats = []
                for i, m in enumerate(o.data.materials):
                    if m is None:
                        continue
                    m2 = m.copy(); m2.name = f"KL4 {tag} {m.name}"
                    o.data.materials[i] = m2
                    for n in m2.node_tree.nodes:
                        if n.type == "TEX_IMAGE":
                            n.interpolation = "Closest"
                    if "glow" in m.name.lower() or name.endswith("glow"):
                        bsdf = next((n for n in m2.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                        tex = next((n for n in m2.node_tree.nodes if n.type == "TEX_IMAGE"), None)
                        if bsdf is not None:
                            if tex is not None:
                                m2.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
                            else:
                                bsdf.inputs["Emission Color"].default_value = (0.15, 1.0, 0.3, 1)
                            glow_mats.append(bsdf)
                            lime = m2.node_tree.nodes.new("ShaderNodeMix"); lime.data_type = "RGBA"
                            lime.inputs[0].default_value = 0.5; lime.inputs[7].default_value = (0.3, 1.0, 0.4, 1)
                            if tex is not None:
                                m2.node_tree.links.new(tex.outputs["Color"], lime.inputs[6])
                            m2.node_tree.links.new(lime.outputs[2], bsdf.inputs["Emission Color"])
                    else:
                        cv = charge_light(m2, root)
                        if cv is not None:
                            charge_vals.append(cv)
        tops = [o for o in new if o.parent is None]
        for o in tops:
            o.parent = root
    # fit: base centre at the root, 16 px (1 block) tall
    bpy.context.view_layer.update()
    from mathutils import Vector
    pts = []
    for o in root.children_recursive:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    if pts:
        P_ = np.array([tuple(p) for p in pts])
        lo, hi = P_.min(0), P_.max(0)
        s = (LH / 16.0) / max(hi[2] - lo[2], 1e-6)
        print("lantern mesh", tag, "w", round((hi[0] - lo[0]) * s * 16, 2), "d", round((hi[1] - lo[1]) * s * 16, 2), "h px", LH, "model hw*2", round(2 * HW, 2))
        for o in root.children:
            o.matrix_world = Matrix.Scale(s, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])) @ o.matrix_world
    lamp = link(bpy.data.objects.new(f"KL4 {tag} lantern lamp", bpy.data.lights.new(f"KL4 {tag} lamp", "POINT")))
    lamp.data.color = (0.55, 1.0, 0.6); lamp.data.energy = 0.0; lamp.data.shadow_soft_size = 0.2
    lamp.parent = root; lamp.location = (0, 0, LH / 32.0)
    return root, glow_mats, (charge_vals, lamp)


def charge_light(m, root):
    """The charge runs down the whole lantern: the body lights from the port at the top down to the base as the
    charge rises, with a bright band at the front of the light. `Charge` (0..1) is keyed per tick."""
    N, Lk = m.node_tree.nodes, m.node_tree.links
    bsdf = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return None
    tex = next((n for n in N if n.type == "TEX_IMAGE"), None)
    tc = N.new("ShaderNodeTexCoord"); tc.object = root
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Object"], sep.inputs[0])
    h = N.new("ShaderNodeMath"); h.operation = "DIVIDE"; h.inputs[1].default_value = LH / 16.0
    Lk.new(sep.outputs["Z"], h.inputs[0])                                   # 0 at the base, 1 at the top
    cv = N.new("ShaderNodeValue"); cv.name = "Charge"; cv.outputs[0].default_value = 0.0
    front = N.new("ShaderNodeMath"); front.operation = "MULTIPLY_ADD"       # front = 1.05 - 1.15 * charge
    front.inputs[1].default_value = -1.15; front.inputs[2].default_value = 1.05
    Lk.new(cv.outputs[0], front.inputs[0])
    d = N.new("ShaderNodeMath"); d.operation = "SUBTRACT"; Lk.new(h.outputs[0], d.inputs[0]); Lk.new(front.outputs[0], d.inputs[1])
    lit = N.new("ShaderNodeMapRange"); lit.inputs[1].default_value = -0.06; lit.inputs[2].default_value = 0.06
    Lk.new(d.outputs[0], lit.inputs[0])                                     # 1 above the front (already lit)
    band = N.new("ShaderNodeMath"); band.operation = "ABSOLUTE"; Lk.new(d.outputs[0], band.inputs[0])
    bandr = N.new("ShaderNodeMapRange"); bandr.inputs[1].default_value = 0.0; bandr.inputs[2].default_value = 0.07
    bandr.inputs[3].default_value = 3.0; bandr.inputs[4].default_value = 0.0; Lk.new(band.outputs[0], bandr.inputs[0])
    tot = N.new("ShaderNodeMath"); tot.operation = "ADD"; Lk.new(lit.outputs[0], tot.inputs[0]); Lk.new(bandr.outputs[0], tot.inputs[1])
    # only the dark glass lights up, the gold frame stays metal: weight by how dark the texel is
    w = N.new("ShaderNodeMath"); w.operation = "MULTIPLY"; Lk.new(tot.outputs[0], w.inputs[0])
    if tex is not None:
        bw = N.new("ShaderNodeRGBToBW"); Lk.new(tex.outputs["Color"], bw.inputs[0])
        inv = N.new("ShaderNodeMapRange"); inv.inputs[1].default_value = 0.05; inv.inputs[2].default_value = 0.35
        inv.inputs[3].default_value = 1.0; inv.inputs[4].default_value = 0.15
        Lk.new(bw.outputs[0], inv.inputs[0]); Lk.new(inv.outputs[0], w.inputs[1])
    else:
        w.inputs[1].default_value = 1.0
    strength = N.new("ShaderNodeMath"); strength.operation = "MULTIPLY"; strength.inputs[1].default_value = 2.2
    Lk.new(w.outputs[0], strength.inputs[0])
    on = N.new("ShaderNodeMath"); on.operation = "MULTIPLY"                  # nothing at all when uncharged
    Lk.new(strength.outputs[0], on.inputs[0]); Lk.new(cv.outputs[0], on.inputs[1])
    bsdf.inputs["Emission Color"].default_value = (0.2, 1.0, 0.3, 1)
    Lk.new(on.outputs[0], bsdf.inputs["Emission Strength"])
    return cv


def bl_matrix(M_rig, origin, side):
    rs = np.array([[math.cos(side), -math.sin(side), 0], [math.sin(side), math.cos(side), 0], [0, 0, 1]])
    out = np.eye(4)
    out[:3, :3] = rs @ (A @ M_rig[:3, :3] @ A.T)
    out[:3, 3] = rs @ to_bl(M_rig[:3, 3]) + np.asarray(origin)
    return Matrix(out.tolist())


def key_root(root, M, frame):
    root.matrix_world = M
    root.keyframe_insert("location", frame=frame); root.keyframe_insert("rotation_euler", frame=frame)


def mat_box(name, a, b, m, origin, side, M_rig=None):
    o = link(bpy.data.objects.new(name, box_mesh(name, a, b, m)))
    o.matrix_world = bl_matrix(np.eye(4) if M_rig is None else M_rig, origin, side)
    return o


STONE = mat("KL block", (0.45, 0.45, 0.47))

# ------------------------------------------------------------------ build the takes
dump = {"format": "per take: per tick solved pose (part rot rad, offset_px from the vanilla pivot), lantern tilt (rad, "
                  "about its far bottom edge, top away from the player) or swing (rad, x/z, hanging from the handle), "
                  "glow 0..1; ring = right arm; 20 ticks a second", "takes": {}}
LAYOUT = {"C6a": (0, 0), "C6b": (8, 0), "C6c": (16, 0)}
END = 0
for take, spec in TAKES.items():
    ox, oy = LAYOUT[take]
    origin = np.array([ox, oy, 0.0])
    side = R(28) if spec.get("side") else 0.0
    last = spec["keys"][-1][1]
    END = max(END, last)
    objs = make_player(take)
    root, glows, (charges, lamp) = import_lantern(take)
    rm = mat(f"KL4 ring {take}", (0.1, 1.0, 0.25), emit=2.0)
    objs["ring"].data.materials[0] = rm
    ticks = []
    if spec["lantern"] == "block":
        bx, bz = 0.0, -15.0
        mat_box(f"KL4 {take} block", (bx - 8, BLOCK_TOP, bz - 8), (bx + 8, GROUND, bz + 8), STONE, origin, side)
        lan = Lantern(bx, BLOCK_TOP, bz)
        push = [push_at(t, spec["keys"]) for t in range(last + 1)]
        tilt = rock(push, last)
        for t in range(last + 1):
            lan.tilt = tilt[t]
            q = port_pose(pose_at(t, spec["keys"]), lan, (bx, bz), spec["hand"], spec["free"], push[t])
            sol = solve(q)
            set_pose(objs, sol, origin, t + 1, side)
            key_root(root, bl_matrix(lan.matrix(), origin, side), t + 1)
            glow = charge6(take, t)
            ticks.append(dict(sol=sol, tilt=tilt[t], glow=glow, fwd=q.get("fwd", 0.0)))
    else:
        # K3b: the lantern on the ground where the vow hand lands, then carried by the handle and swinging
        gp = solve(pose_at(spec["carry"], spec["keys"]))
        hp0 = hand_point(gp, "rarm")
        spot = np.array([hp0[0], GROUND, hp0[2]])
        sols = [solve(pose_at(t, spec["keys"])) for t in range(last + 1)]
        hands = [hand_point(s, "rarm") for s in sols]
        sw = carry_physics(hands, spec["carry"], spot)
        for t in range(last + 1):
            set_pose(objs, sols[t], origin, t + 1, side)
            M = np.eye(4)
            if t >= spec["carry"]:
                phx, phz = sw[t]
                # from the handle: rotate about the grip (x tilt about the z axis, z tilt about the x axis): rotate about the grip, x swing about z-axis and z swing about x-axis
                cz, sz_, cx, sx = math.cos(phx), math.sin(phx), math.cos(phz), math.sin(phz)
                Rz = np.array([[cz, -sz_, 0], [sz_, cz, 0], [0, 0, 1]])
                Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
                Rr = Rz @ Rx
                grip = hands[t]
                base_from_grip = np.array([0.0, LH - 0.5, 0.0])
                M[:3, :3] = Rr; M[:3, 3] = grip + Rr @ base_from_grip
            else:
                sw[t] = np.zeros(2)
                M[:3, 3] = spot
            key_root(root, bl_matrix(M, origin, side), t + 1)
            a, b = spec["glow"]
            glow = math.sin(math.pi * min(1.0, max(0.0, (t - a) / (b - a)))) ** 0.6 if a <= t <= b else 0.0
            ticks.append(dict(sol=sols[t], swing=[float(v) for v in sw[t]], glow=glow))
    # light: the ring (flare / charge) and the lantern's glow cubes
    for t, tk in enumerate(ticks):
        e = 2.0
        if "charge" in spec:
            e = 2.0 + 10.0 * min(1.25, tk["glow"])
        if "flare" in spec:
            a, b = spec["flare"]
            if a <= t <= b:
                e = max(e, 2.0 + 14.0 * math.sin(math.pi * (t - a) / (b - a)))
        sock = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        sock.default_value = e; sock.keyframe_insert("default_value", frame=t + 1)
        for bsdf in glows:
            s = bsdf.inputs["Emission Strength"]
            s.default_value = 1.0 + 5.0 * min(1.3, tk["glow"]); s.keyframe_insert("default_value", frame=t + 1)
        for cv in charges:
            cv.outputs[0].default_value = min(1.0, tk["glow"]); cv.outputs[0].keyframe_insert("default_value", frame=t + 1)
        lamp.data.energy = 25.0 * tk["glow"]; lamp.data.keyframe_insert("energy", frame=t + 1)
    dump["takes"][take] = {"curve_ticks": CURVES[take], 
        "ticks": [{k: v for k, v in dict(
            tilt=round(float(tk["tilt"]), 4) if "tilt" in tk else None,
            swing=tk.get("swing"), glow=round(float(tk["glow"]), 3),
            parts={k: {"rot": [round(float(v), 4) for v in tk["sol"][k][0]],
                       "offset_px": [round(float(v), 3) for v in tk["sol"][k][1] - np.array(PIVOT[k], float)]}
                   for k in PARTS}).items() if v is not None} for tk in ticks],
        "lantern": spec["lantern"], "body_yaw_rad": side, "carry_from_tick": spec.get("carry")}
    cu = bpy.data.curves.new("KL4 label " + take, "FONT"); cu.body = take; cu.size = 0.45; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("KL4 label " + take, cu)); tl.location = tuple(origin + np.array([0, 1.6, 0.01]))
    tl.data.materials.append(mat("KL label", (0.8, 1.0, 0.85), emit=2.0))
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "lantern_charge6_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, END + 1
bpy.ops.mesh.primitive_plane_add(size=90, location=(8, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "KL4 floor"; g.data.materials.append(mat("KL grass", (0.22, 0.4, 0.15)))
world = bpy.data.worlds.get("KL world") or bpy.data.worlds.new("KL world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("KL4 sun", bpy.data.lights.new("KL4 sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass

def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


cams = {"leans": cam("Cam leans", (8, -9, 2.6), (8, -0.5, 0.9), 22)}
for take, (ox, oy) in LAYOUT.items():
    cams[take] = cam("Cam " + take, (ox + 4.6, oy - 0.7, 1.1), (ox, oy - 0.7, 0.85), 35)       # from the side: contact shows
scene.camera = cams["leans"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
SHOTS = {}
if not os.environ.get("LL_NO_RENDER"):
    for take, f in SHOTS.items():
        scene.camera = cams[take]; scene.frame_set(f + 1)
        scene.render.filepath = os.path.join(rdir, f"212_{take}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["leans"]
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
