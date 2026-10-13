# Pass 208: kneel at a lantern, round 2 (lead Blender chat, 2026-10-13).
# J on round 1 (K1-K3): "revise what the legs are doing here, needs work". The reason: Minecraft's legs are single
# rigid boxes with no knee, so a kneel can only swing a straight leg, which reads as a leg stuck out. This round
# gives the player's legs a knee (thigh 6 px + shin 6 px, the same 12 px leg split in two, the way the Dread Runner
# rig already splits its limbs), so the game would draw split legs during this animation only. One take (K7) keeps
# the vanilla rigid legs as the fallback if split legs are not wanted.
#   K4 genuflect: the ring knee goes down to the ground, the other foot planted in front, the ring hand takes the
#      handle, the lantern comes up to the chest as he rises.
#   K5 both knees: drops onto both knees, leans in, two-handed lift, rises.
#   K6 deep squat: heels under the hips, knees up and apart, scoops the lantern, stands.
#   K7 rigid crouch (no knees): the vanilla crouch taken lower; the torso sinks into the legs and leans far forward.
# Same pose format as before, plus the shins: per part rot (xRot, yRot, zRot rad) and offset_px from the vanilla
# pivot; the shin's vanilla pivot is the knee (6 px below the hip). Ring on the right hand; mirror for left.
# Writes LanternLive\kneel2_poses.json and builds LanternLive\kneel2.blend. Cameras "Cam K4".."Cam K7" (side on),
# "Cam K4 front".."Cam K7 front", "Cam all".
import json, math, os
import bpy
import numpy as np

R = math.radians
OUT = os.path.join(FOLDER, "kneel2.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Kneel Two")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Kneel Two")
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


# ------------------------------------------------------------------ the poses
IDLE = dict(ring=(0.05, 0, 0.05), free=(0.05, 0, 0.05))
P = {
    # K4 genuflect: ring knee down, free foot planted in front
    "K4_down": dict(body=(0.15, 0, 0), head=(0.35, 0, 0), ring=(-0.5, 0, 0.12), free=(-0.2, 0.2, -0.2),
                    ringleg=(0.15, 0, 0.04), ringknee=1.2, freeleg=(-1.2, 0, -0.06), freeknee=1.25),
    "K4_grab": dict(body=(0.3, 0, 0), head=(0.45, 0, 0), ring=(-0.6, 0, 0.1), free=(-0.15, 0.25, -0.25),
                    ringleg=(0.05, 0, 0.04), ringknee=1.55, freeleg=(-1.45, 0, -0.06), freeknee=1.5),
    "K4_lift": dict(body=(0.1, 0, 0), head=(0.1, 0, 0), ring=(-1.15, -0.35, 0.05), free=(-0.95, 0.45, 0),
                    ringleg=(0.25, 0, 0.04), ringknee=0.8, freeleg=(-0.7, 0, -0.06), freeknee=0.8),
    "K4_stand": dict(body=(0.0, 0, 0), head=(0.1, 0, 0), ring=(-0.95, -0.4, 0.05), free=(-0.85, 0.45, 0)),
    # K5 both knees
    "K5_down": dict(body=(0.2, 0, 0), head=(0.35, 0, 0), ring=(-0.5, 0.15, 0.1), free=(-0.5, 0.15, 0.1),
                    ringleg=(0.1, 0, 0.08), ringknee=1.2, freeleg=(0.1, 0, 0.08), freeknee=1.2),
    "K5_grab": dict(body=(0.45, 0, 0), head=(0.4, 0, 0), ring=(-0.6, 0.3, 0.05), free=(-0.6, 0.3, 0.05),
                    ringleg=(-0.05, 0, 0.08), ringknee=1.6, freeleg=(-0.05, 0, 0.08), freeknee=1.6),
    "K5_lift": dict(body=(0.1, 0, 0), head=(0.1, 0, 0), ring=(-1.05, 0.35, 0), free=(-1.05, 0.35, 0),
                    ringleg=(-0.6, 0, 0.06), ringknee=1.0, freeleg=(0.2, 0, 0.06), freeknee=1.4),
    "K5_stand": dict(body=(0.0, 0, 0), head=(0.05, 0, 0), ring=(-0.9, 0.35, 0), free=(-0.9, 0.35, 0)),
    # K6 deep squat: thighs forward and apart, shins folded back under
    "K6_down": dict(body=(0.5, 0, 0), head=(0.1, 0, 0), ring=(-0.6, 0.15, 0.1), free=(-0.6, 0.15, 0.1),
                    ringleg=(-0.9, 0, 0.3), ringknee=1.6, freeleg=(-0.9, 0, 0.3), freeknee=1.6),
    "K6_grab": dict(body=(0.7, 0, 0), head=(0.2, 0, 0), ring=(-0.6, 0.3, 0.05), free=(-0.6, 0.3, 0.05),
                    ringleg=(-1.3, 0, 0.38), ringknee=2.35, freeleg=(-1.3, 0, 0.38), freeknee=2.35),
    "K6_lift": dict(body=(0.3, 0, 0), head=(0.1, 0, 0), ring=(-1.05, 0.35, 0), free=(-1.05, 0.35, 0),
                    ringleg=(-0.7, 0, 0.2), ringknee=1.2, freeleg=(-0.7, 0, 0.2), freeknee=1.2),
    "K6_stand": dict(body=(0.0, 0, 0), head=(0.05, 0, 0), ring=(-0.9, 0.35, 0), free=(-0.9, 0.35, 0)),
    # K7 rigid (no knees): the vanilla crouch, much lower, the torso sinking into the legs
    "K7_down": dict(body=(0.6, 0, 0), head=(0.1, 0, 0), ring=(-0.5, 0, 0.1), free=(-0.3, 0, -0.1),
                    ringleg=(0.12, 0, 0.06), freeleg=(-0.12, 0, 0.06), sink=4.0),
    "K7_grab": dict(body=(0.9, 0, 0), head=(-0.05, 0, 0), ring=(-0.6, 0, 0.1), free=(-0.3, 0, -0.1),
                    ringleg=(0.18, 0, 0.08), freeleg=(-0.18, 0, 0.08), sink=7.0),
    "K7_lift": dict(body=(0.35, 0, 0), head=(0.05, 0, 0), ring=(-1.1, -0.35, 0.05), free=(-0.9, 0.45, 0),
                    ringleg=(0.08, 0, 0.04), freeleg=(-0.08, 0, 0.04), sink=2.0),
    "K7_stand": dict(body=(0.0, 0, 0), head=(0.1, 0, 0), ring=(-0.95, -0.4, 0.05), free=(-0.85, 0.45, 0)),
}
TAKES = {
    "K4": dict(keys=[("idle", 0), ("K4_down", 9), ("K4_grab", 15), ("K4_grab", 19), ("K4_lift", 29), ("K4_stand", 39),
                     ("K4_stand", 60)], carry=19, two=False, lantern="ground"),
    "K5": dict(keys=[("idle", 0), ("K5_down", 10), ("K5_grab", 16), ("K5_grab", 20), ("K5_lift", 31), ("K5_stand", 41),
                     ("K5_stand", 60)], carry=20, two=True, lantern="ground"),
    "K6": dict(keys=[("idle", 0), ("K6_down", 9), ("K6_grab", 15), ("K6_grab", 19), ("K6_lift", 28), ("K6_stand", 38),
                     ("K6_stand", 60)], carry=19, two=True, lantern="ground"),
    "K7": dict(keys=[("idle", 0), ("K7_down", 8), ("K7_grab", 14), ("K7_grab", 18), ("K7_lift", 27), ("K7_stand", 36),
                     ("K7_stand", 60)], carry=18, two=False, lantern="ground"),
}


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
        off = abs((GROUND - hp[1]) - HANDLE_PX)
        # within a pixel of the handle's height, take the reach that puts the lantern furthest out in front
        err = (0 if off < 1.0 else 100 + off) + 0.25 * hp[2]
        if best is None or err < best[0]:
            best = (err, x)
    p["ring"] = (best[1], p["ring"][1], p["ring"][2])
    if two:
        p["free"] = (best[1], p["free"][1], p["free"][2])


for _n, _two in (("K4_grab", False), ("K5_grab", True), ("K6_grab", True), ("K7_grab", False)):
    fit_reach(_n, _two)
for _t, _two in (("K4", False), ("K5", True), ("K6", True), ("K7", False)):
    P[_t + "_down"]["ring"] = tuple(np.array(P[_t + "_grab"]["ring"]) * 0.75)
    if _two:
        P[_t + "_down"]["free"] = P[_t + "_down"]["ring"]


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


JADE = mat("KL jade", (0.02, 0.22, 0.08), rough=0.25)
GLOWM = mat("KL lantern glow", (0.15, 1.0, 0.3), emit=2.0)
GOLD = mat("KL gold", (0.85, 0.62, 0.2), rough=0.3, metal=0.9)
STONE = mat("KL block", (0.45, 0.45, 0.47))


def make_lantern(tag):
    """A stand-in Green lantern at the mod's lantern size (8 px wide, 16 tall with the handle), origin at its base."""
    parts = [((-4, -13, -4), (4, -2, 4), JADE), ((-5, -2, -5), (5, 0, 5), GOLD), ((-5, -14, -5), (5, -13, 5), GOLD),
             ((-0.75, -15.5, -0.75), (0.75, -14, 0.75), GOLD), ((-2.5, -16, -0.75), (2.5, -15.25, 0.75), GOLD),
             ((-2, -10, 3.95), (2, -5, 4.35), GLOWM)]
    root = link(bpy.data.objects.new(f"KL {tag} lantern", None))
    root.empty_display_size = 0.05
    for i, (a, b, m) in enumerate(parts):
        o = link(bpy.data.objects.new(f"KL {tag} lantern {i}", box_mesh(f"KL {tag} lan {i}", a, b, m)))
        o.parent = root
        if m is GLOWM:
            root["glow_obj"] = o.name
    return root


# ------------------------------------------------------------------ build the takes
dump = {"format": "per take: ticks, and per key pose part rotations (xRot,yRot,zRot rad) and offset_px from the "
                  "vanilla pivot; ring = right arm", "takes": {}}
LAYOUT = {"K4": (0, 0), "K5": (8, 0), "K6": (16, 0), "K7": (24, 0)}
END = 0
for take, spec in TAKES.items():
    ox, oy = LAYOUT[take]
    origin = np.array([ox, oy, 0.0])
    objs = make_player(take)
    lan = make_lantern(take)
    last = spec["keys"][-1][1]
    END = max(END, last)
    side = R(28) if spec.get("side") else 0.0
    if spec["lantern"] == "block":
        bl = link(bpy.data.objects.new(f"KL {take} block", box_mesh(f"KL {take} block", (-8, -16, -8), (8, 0, 8), STONE)))
        lz = -15.0 + (-2.0 if spec.get("side") else 0.0)
        bl_loc = origin + to_bl((-4.0 if spec.get("side") else 0.0, GROUND, lz))
        bl.location = tuple(bl_loc)
        lan.location = tuple(bl_loc + np.array([0, 0, 1.0]))
    else:
        # the lantern sits where the hand lands in the grab pose, so the grip always meets the handle
        gp = solve(pose_at(spec["carry"], spec["keys"]))
        hp = hand_point(gp, "rarm") if not spec.get("two") else (hand_point(gp, "rarm") + hand_point(gp, "larm")) / 2
        spec["spot"] = (float(hp[0]), GROUND, float(hp[2]))      # handle under the hand (hand at handle height)
        lan.location = tuple(origin + to_bl(spec["spot"]))
    gl = bpy.data.objects[lan["glow_obj"]]
    gm = mat(f"KL glow {take}", (0.15, 1.0, 0.3), emit=1.5)
    gl.data.materials[0] = gm
    rm = mat(f"KL ring {take}", (0.1, 1.0, 0.25), emit=2.0)
    objs["ring"].data.materials[0] = rm
    for t in range(0, last + 1):
        p = pose_at(t, spec["keys"])
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1, side)
        if spec["lantern"] == "ground" and "carry" in spec:
            if t >= spec["carry"]:
                hp = hand_point(sol, "rarm")
                if spec.get("two"):
                    hp = (hp + hand_point(sol, "larm")) / 2
                lan.location = tuple(origin + to_bl(hp + np.array([0, 15.5, 0])))
            else:
                lan.location = tuple(origin + to_bl(spec["spot"]))
            lan.keyframe_insert("location", frame=t + 1)
        # ring and lantern light
        e = 2.0
        if "charge" in spec:
            a, b = spec["charge"]
            if a <= t <= b:
                e = 2.0 + 10.0 * smooth((t - a) / (b - a))
        if "flare" in spec:
            a, b = spec["flare"]
            if a <= t <= b:
                e = 2.0 + 14.0 * math.sin(math.pi * (t - a) / (b - a))
        rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = e
        rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert("default_value", frame=t + 1)
        gm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5 + e * 0.6
        gm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert("default_value", frame=t + 1)
    # pose dump
    keys = []
    for name, tick in spec["keys"]:
        sol = solve(pose_of(name))
        keys.append({"tick": tick, "pose": name, "parts": {k: {"rot": [round(float(v), 4) for v in sol[k][0]],
                                                              "offset_px": [round(float(v), 3) for v in
                                                                            sol[k][1] - np.array(PIVOT[k], float)]}
                                                          for k in PARTS}})
    dump["takes"][take] = {"keys": keys, "carry_from_tick": spec.get("carry"), "two_handed": spec.get("two", False),
                           "charge_ticks": spec.get("charge"), "flare_ticks": spec.get("flare"),
                           "lantern": spec["lantern"], "body_yaw_rad": side}
    cu = bpy.data.curves.new("KL label " + take, "FONT"); cu.body = take; cu.size = 0.45; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("KL label " + take, cu)); tl.location = tuple(origin + np.array([0, 1.4, 0.01]))
    tl.data.materials.append(mat("KL label", (0.8, 1.0, 0.85), emit=2.0))

with open(os.path.join(FOLDER, "kneel2_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)

scene.frame_start, scene.frame_end = 1, END + 1
bpy.ops.mesh.primitive_plane_add(size=80, location=(8, 4.5, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "KL floor"; g.data.materials.append(mat("KL grass", (0.22, 0.4, 0.15)))
world = bpy.data.worlds.get("KL world") or bpy.data.worlds.new("KL world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("KL sun", bpy.data.lights.new("KL sun", "SUN")))
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


cams = {"all": cam("Cam all", (12, -14, 6), (12, 0, 0.5), 30)}
for take, (ox, oy) in LAYOUT.items():
    cams[take] = cam("Cam " + take, (ox + 3.6, oy + 0.6, 1.1), (ox, oy - 0.35, 0.6), 35)
    cams[take + " front"] = cam("Cam " + take + " front", (ox - 2.4, oy - 3.2, 1.3), (ox, oy - 0.4, 0.6), 35)
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
SHOTS = {"K4": 17, "K5": 18, "K6": 17, "K7": 16}
if not os.environ.get("LL_NO_RENDER"):
    for take, f in SHOTS.items():
        for view in ("", " front"):
            scene.camera = cams[take + view]; scene.frame_set(f + 1)
            scene.render.filepath = os.path.join(rdir, f"208_{take}{view.replace(' ', '_')}.png")
            bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["all"]
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
