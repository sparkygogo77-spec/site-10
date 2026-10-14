# Pass 217: flight in the air and landings (lead Blender chat, 2026-10-14). J picked "2 and 3": landing from flight and
# flight poses in the air; for the arms "we'll need both" (ring arm forward, and both arms back).
# Row 1, poses held in the air (loops with a slight bob), each in two arm styles: A = ring arm forward, B = both arms back:
#   cruise, bank left, bank right, dive, climb, hover (upright, legs loose, treading), turn (yaws into the turn).
# Row 2, landings from level flight about 12 blocks up (J's takeoff height):
#   L1 run-out: glides down, swings upright, feet down and lands running, three strides to a stop.
#   L2 hover stop: brakes in the air, comes upright, sinks, knees soak up the touchdown.
#   L3 hero landing: dives in, lands on the ring knee with the ring fist to the ground and a ring flare.
# Cameras ride with each take: "Cam <take>" over the right shoulder, "Cam <take> side"; plus "Cam poses", "Cam landings".
# Writes LanternLive\flight_air_poses.json, builds LanternLive\flight_air.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "flight_air.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Flight Air")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Flight Air")
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


# ------------------------------------------------------------------ the run cycle
STRIDE, LOOP, SPEED = 12, 48, 0.28          # ticks a stride, ticks a loop, blocks a tick


def legs(ph, amp=0.85, lean=0.0):
    """Thigh and knee for one leg at phase ph: the thigh swings (forward is negative), the knee folds most while the
    leg comes through under the body and is nearly straight as the foot strikes out in front."""
    thigh = 0.15 - amp * math.sin(ph) - lean * 0.5
    knee = 0.12 + 1.45 * ((1 + math.cos(ph + 0.35)) / 2) ** 2
    return thigh, knee


def run_pose(take, t):
    ph = 2 * math.pi * t / STRIDE
    amp = {"S3": 1.0}.get(take, 0.85)
    lean = {"S1": 0.26, "S2": 0.3, "S3": 0.46, "S4": 0.24}[take]
    tr, kr = legs(ph, amp, lean)
    tf, kf = legs(ph + math.pi, amp, lean)
    swing = math.sin(ph)
    p = dict(body=(lean + 0.03 * math.sin(2 * ph), 0.07 * swing, 0.0), head=(-lean * 0.8, -0.05 * swing, 0.0),
             ringleg=(tr, 0, 0.02), ringknee=kr, freeleg=(tf, 0, -0.02), freeknee=kf)
    free_swing = 0.15 - 0.95 * swing
    if take == "S1":
        p["ring"] = (-1.42 + 0.06 * math.sin(2 * ph), 0.06, 0.05)
        p["free"] = (free_swing, 0, -0.08)
    elif take == "S2":
        p["ring"] = (0.15 + 0.95 * swing, 0, 0.08)
        p["free"] = (free_swing, 0, -0.08)
    elif take == "S3":
        p["ring"] = (1.05 + 0.08 * swing, 0, 0.22)
        p["free"] = (0.15 - 1.1 * swing, 0, -0.1)
    else:                                       # S4: the free hand carries the lantern low at the hip
        p["ring"] = (0.15 + 0.95 * swing, 0, 0.08)
        p["free"] = (-0.1 - 0.25 * swing, 0, -0.18)
    return p



def P_(**k):
    d = dict(grounded=False); d.update(k); return d


ARMS = {"A": dict(ring=(-1.57, 0, 0.02), free=(1.35, 0, -0.12)), "B": dict(ring=(1.45, 0, 0.14), free=(1.45, 0, -0.14))}
LEGS = dict(ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4)
POSES = {
    "cruise": P_(body=(1.42, 0, 0), head=(-1.25, 0, 0), **LEGS),
    "bank left": P_(body=(1.38, 0.0, 0.55), head=(-1.2, 0, 0.3), **LEGS),
    "bank right": P_(body=(1.38, 0.0, -0.55), head=(-1.2, 0, -0.3), **LEGS),
    "dive": P_(body=(2.15, 0, 0), head=(-1.7, 0, 0), ringleg=(2.0, 0, 0.03), ringknee=0.1, freeleg=(1.95, 0, -0.03), freeknee=0.15),
    "climb": P_(body=(0.85, 0, 0), head=(-0.9, 0, 0), ringleg=(0.85, 0, 0.03), ringknee=0.3, freeleg=(0.75, 0, -0.03), freeknee=0.5),
    "hover": P_(body=(0.1, 0, 0), head=(0.0, 0, 0), ringleg=(0.15, 0, 0.06), ringknee=0.5, freeleg=(-0.1, 0, -0.06), freeknee=0.35),
    "turn": P_(body=(1.35, 0.45, 0.25), head=(-1.15, 0.35, 0.1), **LEGS),
}
HOVER_ARMS = {"A": dict(ring=(-0.6, 0, 0.25), free=(0.1, 0, -0.35)), "B": dict(ring=(0.25, 0, 0.35), free=(0.25, 0, -0.35))}


def air_pose(name, arms, t):
    p = dict(POSES[name]); p.update(HOVER_ARMS[arms] if name == "hover" else ARMS[arms])
    ph = 2 * math.pi * t / 30
    if name == "hover":                       # treading: the legs cycle gently
        p["ringknee"] = 0.5 + 0.25 * math.sin(ph); p["freeknee"] = 0.35 + 0.25 * math.sin(ph + math.pi)
    else:
        bx, by, bz = p["body"]; p["body"] = (bx + 0.03 * math.sin(ph), by, bz)
    return p, 0.12 * math.sin(ph)


FLYA = dict(POSES["cruise"]); FLYA.update(ARMS["A"])
UPRIGHT = P_(body=(-0.15, 0, 0), head=(0.1, 0, 0), ring=(-0.4, 0, 0.5), free=(-0.2, 0, -0.5),
             ringleg=(-0.35, 0, 0.05), ringknee=0.6, freeleg=(0.2, 0, -0.05), freeknee=0.4)
SOAK = dict(body=(0.45, 0, 0), head=(-0.3, 0, 0), ring=(-0.3, 0, 0.4), free=(-0.2, 0, -0.4),
            ringleg=(-0.9, 0, 0.06), ringknee=1.6, freeleg=(-0.8, 0, -0.06), freeknee=1.5)
HERO = dict(body=(0.5, 0, 0), head=(-0.35, 0, 0), ring=(-0.25, 0, 0.12), free=(0.6, 0, -0.5),
            ringleg=(0.15, 0, 0.04), ringknee=1.25, freeleg=(-1.15, 0, -0.06), freeknee=1.3)
STAND = dict(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.05), free=(0.05, 0, -0.05))
H0 = 12.0


def landing(take, t):
    """(pose, forward blocks, height, ring glow) for a landing take."""
    if take == "L1":                          # glide down, come upright, run out
        if t < 34:
            w = smooth(t / 34)
            return FLYA, 0.55 * t, H0 * (1 - w), 6
        if t < 42:
            w = smooth((t - 34) / 8)
            return mixp(FLYA, UPRIGHT, w), 0.55 * 34 + 0.45 * (t - 34), 0.0 + 0.4 * (1 - w), 6
        tt = t - 42
        speed = max(0.0, 0.42 - 0.012 * tt)
        x = 0.55 * 34 + 0.45 * 8 + 0.42 * tt - 0.006 * tt * tt
        if speed > 0.02:
            return run_pose("S2", tt), x, 0.0, 4
        return STAND, x, 0.0, 3
    if take == "L2":                          # brake, upright, sink, soak
        if t < 20:
            return FLYA, 0.5 * t, H0, 6
        x20 = 10.0
        if t < 34:
            w = smooth((t - 20) / 14)
            return mixp(FLYA, POSES["hover"] | HOVER_ARMS["A"], w), x20 + 0.5 * (t - 20) * (1 - w * 0.6), H0, 8
        tt = t - 34
        x = x20 + 4.2
        if tt < 26:
            h = H0 * (1 - smooth(tt / 26))
            p, _ = air_pose("hover", "A", tt)
            return p, x, h, 7
        st = tt - 26
        if st < 6:
            return mixp(UPRIGHT | {"grounded": True}, SOAK, smooth(st / 3) if st < 3 else 1 - smooth((st - 3) / 3) * 0.0), x, 0.0, 5
        return mixp(SOAK, STAND, smooth(min(1, (st - 6) / 10))), x, 0.0, 3
    # L3 hero landing
    if t < 16:
        return FLYA, 0.55 * t, H0, 6
    x16 = 8.8
    if t < 30:
        w = smooth((t - 16) / 14)
        dv = dict(POSES["dive"]); dv.update(ARMS["A"])
        return mixp(FLYA, dv, min(1, w * 2)), x16 + 0.5 * (t - 16), H0 * (1 - w), 9
    tt = t - 30
    if tt < 4:
        return mixp(UPRIGHT, HERO, smooth(tt / 4)), x16 + 7.0 + 0.1 * tt, 0.0, 9
    if tt < 30:
        return HERO, x16 + 7.4, 0.0, 30 if tt < 6 else 3     # the ring flares on impact
    return mixp(HERO, STAND, smooth(min(1, (tt - 30) / 12))), x16 + 7.4, 0.0, 3


TAKES = []
for i, nm in enumerate(POSES):
    for j, arms in enumerate(("A", "B")):
        TAKES.append((f"{nm} {arms}", "air", (i * 3.0 + j * 1.3, 0.0)))
for i, lt in enumerate(("L1", "L2", "L3")):
    TAKES.append((lt, "land", (i * 6.0, 14.0)))
NAMES = {"L1": "run-out", "L2": "hover stop", "L3": "hero landing"}
END = 90
dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot (shins pivot at the "
                  "knee), forward and up in blocks, ring glow; ring = right arm. Air poses loop every 30 ticks.", "takes": {}}
for take, kind, (ox, oy) in TAKES:
    objs = make_player(take)
    rm = mat(f"FA ring {take}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"FA {take} mover", None)); mover.empty_display_size = 0.1
    ticks = []
    n = 30 if kind == "air" else END
    for t in range(n + 1):
        if kind == "air":
            p, bob = air_pose(take.rsplit(" ", 1)[0], take[-1], t)
            fwd, up, glow = 0.0, 3.0 + bob, 6.0
        else:
            p, fwd, up, glow = landing(take, t)
        origin = np.array([ox, oy - fwd, up])
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1)
        mover.location = (ox, oy - fwd, up * 0.7 if kind == "land" else 3.0); mover.keyframe_insert("location", frame=t + 1)
        s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = glow; s.keyframe_insert("default_value", frame=t + 1)
        ticks.append({"forward": round(float(fwd), 3), "up": round(float(up), 3), "glow": round(float(glow), 2),
                      "parts": {kk: {"rot": [round(float(v), 4) for v in sol[kk][0]],
                                     "offset_px": [round(float(v), 3) for v in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    dump["takes"][take] = {"kind": kind, "ticks": ticks}
    label = take if kind == "air" else f"{take}  {NAMES[take]}"
    cu = bpy.data.curves.new("FA label " + take, "FONT"); cu.body = label; cu.size = 0.22 if kind == "air" else 0.35
    cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FA label " + take, cu)); tl.location = (ox, oy + 1.0, 0.01)
    tl.data.materials.append(mat("FA label", (0.8, 1.0, 0.85), emit=2.0))
    if kind == "air":
        shots = ((f"Cam {take}", (-0.6, 2.3, 1.0), (0.1, -3.0, 0.0), 30), (f"Cam {take} side", (5.5, -0.3, 0.3), (0, -0.3, 0.1), 32))
    else:
        shots = ((f"Cam {take}", (-0.6, 2.3, 2.4), (0.15, -4.0, 1.3), 28), (f"Cam {take} side", (9.0, -2.0, 1.8), (0, -2.0, 1.4), 30))
    for nm_, loc, look, lens in shots:
        c = cam(nm_, (ox + loc[0], oy + loc[1], (3.0 if kind == "air" else 0) + loc[2]),
                (ox + look[0], oy + look[1], (3.0 if kind == "air" else 0) + look[2]), lens)
        mw = c.matrix_world.copy(); c.parent = mover; c.matrix_world = mw
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "flight_air_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=1, location=(10, -10, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "FA ground"; g.scale = (60, 80, 1)
gm = bpy.data.materials.new("FA ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 80
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("FA world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("FA sun", bpy.data.lights.new("FA sun", "SUN")))
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
cam("Cam poses", (9.5, -12, 6), (9.5, 0, 3), 30)
cam("Cam landings", (6, 30, 9), (6, 4, 3), 30)
scene.camera = bpy.data.objects["Cam poses"]
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
