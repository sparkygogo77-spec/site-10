# Pass 82: super jump round 2. J: Takes 1 and 2 are good, Take 3 is dropped; Take 1's fall looks the best, but
# while the ring is in use its arm should be closer to Take 2's (aimed at the ground). Four rigs:
#   1a  Take 1 with D1a: D1's body, legs and free arm; the ring fist straight down at the ground (Take 2's arm)
#   1b  Take 1 with D1b: the ring fist out in front, aimed at the landing spot ahead
#   1c  Take 1 with D1c: the ring fist down and a little out to the side, set to plant for E1
#   2   Take 2 unchanged, for comparison
# The ring now glows up through the fall (in use), into the landing flare.
# Cameras: Cam 3/4 all, Cam side / Cam 3/4 / Cam back + T1a, T1b, T1c, T2. Builds LanternLive\super_jump_r2.blend.
import json, math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

R = math.radians
OUT = os.path.join(FOLDER, "super_jump_r2.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Super Jump R2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Super Jump R2")
col = scene.collection
scene.render.fps = 20                                   # one frame per game tick
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ======================================================================================================
# The rig in Minecraft model space: pixels, y down, forward is -z; the player's right arm is at -x.
# A part turns at its pivot by Rz.Ry.Rx (ModelPart's rotationZYX), the same order as Blender's XYZ euler.
# ======================================================================================================
PIVOT = {"head": (0, 0, 0), "body": (0, 0, 0), "rarm": (-5, 2, 0), "larm": (5, 2, 0),
         "rleg": (-1.9, 12, 0), "lleg": (1.9, 12, 0)}
BOX = {"head": ((-4, -8, -4), (4, 0, 4)), "body": ((-4, 0, -2), (4, 12, 2)), "rarm": ((-3, -2, -2), (1, 10, 2)),
       "larm": ((-1, -2, -2), (3, 10, 2)), "rleg": ((-2, 0, -2), (2, 12, 2)), "lleg": ((-2, 0, -2), (2, 12, 2))}
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")
GROUND = 24.0                                           # the feet's y when standing


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
    """A pose given as rotations (ring = right side, 'out' z) -> pivots and rotations per part.
    The body turns about the hips, so a lean folds the chest forward and the shoulders and neck follow it;
    the legs hang from the hips. Grounded poses drop the hips until the lowest foot touches the ground,
    and a planted fist has its arm angle solved so the fist touches too."""
    rot_ = {"body": p.get("body", (0, 0, 0)), "head": p.get("head", (0, 0, 0))}
    for k, part, sgn in (("ring", "rarm", 1), ("free", "larm", -1), ("ringleg", "rleg", 1), ("freeleg", "lleg", -1)):
        x, y, z = p.get(k, (0, 0, 0))
        rot_[part] = (x, sgn * y, sgn * z)
    Rb = rot(*rot_["body"])
    piv = {}

    sink = [float(p.get("sink", 0.0))]

    def place(d):
        hip = np.array([0.0, 12.0 + d, 0.0])
        # like vanilla's crouch, the torso can sink into the legs: the legs stay on the hips
        neck = hip + Rb @ np.array([0.0, -12.0, 0.0]) + np.array([0.0, sink[0], 0.0])
        piv["body"] = neck
        piv["head"] = neck.copy()
        piv["rarm"] = neck + Rb @ np.array([-5.0, 2.0, 0.0])
        piv["larm"] = neck + Rb @ np.array([5.0, 2.0, 0.0])
        piv["rleg"] = hip + np.array([-1.9, 0.0, 0.0])
        piv["lleg"] = hip + np.array([1.9, 0.0, 0.0])

    place(0.0)
    d = 0.0
    if p.get("grounded"):
        low = max(corners(k, piv[k], rot_[k])[:, 1].max() for k in ("rleg", "lleg"))
        d = GROUND - low
        place(d)
    if p.get("plant"):
        _, y, zo = rot_["rarm"]
        for _ in range(8):
            best = None
            for x in np.linspace(-1.7, 0.9, 261):       # the most forward arm angle that reaches the ground
                low = corners("rarm", piv["rarm"], (x, y, zo))[:, 1].max()
                if best is None or low > best[0] + 1e-6 or (abs(low - GROUND) < 0.15 and abs(best[0] - GROUND) >= 0.15):
                    best = (low, x)
                if abs(low - GROUND) < 0.15:
                    best = (low, x)
                    break
            if best[0] >= GROUND - 0.15:
                break
            sink[0] += GROUND - best[0]                    # can't reach: sink the torso until it does
            place(d)
        rot_["rarm"] = (float(best[1]), y, zo)
    return {k: (np.asarray(rot_[k], float), piv[k] - np.asarray(PIVOT[k], float)) for k in PARTS}, d, sink[0]


IDLE = {"grounded": True}
POSES = {
    # A  wind-up: the crouch deepens as it charges (35% of the way when armed at 0.35 s, full at 1.25 s)
    "A1": dict(note="coiled spring: deep lean, ring fist pulled back, free hand forward", grounded=True, sink=4.0,
               body=(0.55, 0, 0), head=(-0.55, 0, 0), ring=(1.15, 0, 0.25), free=(-0.75, 0.35, -0.15),
               ringleg=(-0.55, 0, 0.2), freeleg=(0.45, 0, 0.15)),
    "A2": dict(note="fist to the ground: ring fist planted between wide feet, free arm back", grounded=True, sink=5.0,
               plant=True, body=(0.85, 0, 0), head=(-0.75, 0, 0), ring=(0, 0, 0.1), free=(1.25, 0, 0.45),
               ringleg=(-0.45, 0, 0.4), freeleg=(0.65, 0, 0.4)),
    "A3": dict(note="ring at the hip, eyes up: torso turned, ring fist cocked back, free hand out", grounded=True, sink=3.5,
               body=(0.45, -0.3, 0), head=(-0.65, 0.3, 0), ring=(0.75, 0, 0.2), free=(-0.55, 0, 0.75),
               ringleg=(-0.3, 0, 0.35), freeleg=(0.4, 0, 0.3)),
    # B  launch: the first 5 ticks
    "B1": dict(note="piston: both arms driven down and back, legs locked straight", body=(-0.05, 0, 0),
               head=(-0.4, 0, 0), ring=(0.75, 0, 0.15), free=(0.75, 0, 0.15), ringleg=(0.15, 0, 0.03),
               freeleg=(0.15, 0, 0.03)),
    "B2": dict(note="uppercut: the ring fist already swinging up, free arm thrown back", body=(0.1, 0, 0),
               head=(-0.6, 0, 0), ring=(-1.9, 0, 0.1), free=(0.9, 0, 0.2), ringleg=(0.05, 0, 0.03),
               freeleg=(0.3, 0, 0.03)),
    "B3": dict(note="burst: arms flung out and down, chest arched, toes pointed", body=(-0.15, 0, 0),
               head=(-0.35, 0, 0), ring=(0.25, 0, 0.95), free=(0.25, 0, 0.95), ringleg=(0.25, 0, 0.1),
               freeleg=(0.25, 0, 0.1)),
    # C  rising: until it starts to fall
    "C1": dict(note="up, up and away: ring fist straight up, free arm back, ring knee up", body=(-0.08, 0, 0),
               head=(-0.45, 0, 0), ring=(-3.05, 0, 0.05), free=(0.35, 0, 0.12), ringleg=(-0.95, 0, 0.05),
               freeleg=(0.3, 0, 0.02)),
    "C2": dict(note="rocket: ring fist up, free fist tucked at the chest, legs together", body=(-0.12, 0, 0),
               head=(-0.35, 0, 0), ring=(-3.0, 0, 0.08), free=(-1.35, 0.6, -0.25), ringleg=(0.1, 0, 0),
               freeleg=(0.15, 0, 0)),
    "C3": dict(note="arc: ring fist leading up and forward, body arched, legs in a stride", body=(-0.25, 0, 0),
               head=(-0.75, 0, 0), ring=(-2.5, 0, 0.15), free=(0.85, 0, 0.3), ringleg=(-0.55, 0, 0.05),
               freeleg=(0.65, 0, 0.05)),
    # D  falling: sets up the landing
    "D1": dict(note="ground punch cocked: ring fist drawn up behind, free arm out, eyes on the spot",
               body=(0.25, 0, 0), head=(0.3, 0, 0), ring=(2.45, 0, 0.25), free=(-0.35, 0, 1.1),
               ringleg=(-0.45, 0, 0.08), freeleg=(0.35, 0, 0.08)),
    "D2": dict(note="dive: leaning into it, ring fist aimed at the ground, knees tucked", body=(0.55, 0, 0),
               head=(0.15, 0, 0), ring=(-0.15, 0, 0.05), free=(1.35, 0, 0.3), ringleg=(-0.95, 0, 0.05),
               freeleg=(-0.35, 0, 0.05)),
    "D3": dict(note="spread then gather: arms wide for balance, legs apart, looking down", body=(0.1, 0, 0),
               head=(0.35, 0, 0), ring=(-0.25, 0, 1.35), free=(-0.15, 0, 1.25), ringleg=(-0.35, 0, 0.25),
               freeleg=(0.25, 0, 0.25)),
    "D1a": dict(note="D1 with the ring fist straight down at the ground (Take 2's ring arm)",
                body=(0.25, 0, 0), head=(0.3, 0, 0), ring=(-0.15, 0, 0.05), free=(-0.35, 0, 1.1),
                ringleg=(-0.45, 0, 0.08), freeleg=(0.35, 0, 0.08)),
    "D1b": dict(note="D1 with the ring fist out in front, aimed at the landing spot ahead",
                body=(0.25, 0, 0), head=(0.3, 0, 0), ring=(-0.75, 0, 0.12), free=(-0.35, 0, 1.1),
                ringleg=(-0.45, 0, 0.08), freeleg=(0.35, 0, 0.08)),
    "D1c": dict(note="D1 with the ring fist down and a little out, set to plant for E1",
                body=(0.25, 0, 0), head=(0.3, 0, 0), ring=(-0.3, 0, 0.4), free=(-0.35, 0, 1.1),
                ringleg=(-0.45, 0, 0.08), freeleg=(0.35, 0, 0.08)),
    # E  landing: held 0.8 s
    "E1": dict(note="classic three-point: ring foot forward, other knee down, ring fist on the ground",
               grounded=True, sink=2.0, plant=True, body=(0.75, 0, 0), head=(-0.7, 0, 0), ring=(0, 0, 0.12),
               free=(1.3, 0, 0.5), ringleg=(-1.3, 0, 0.1), freeleg=(1.0, 0, 0.08)),
    "E2": dict(note="wide slam: feet wide, fist planted between them, free arm out (reads from behind)",
               grounded=True, sink=2.0, plant=True, body=(0.95, 0, 0), head=(-0.9, 0, 0), ring=(0, 0, -0.05),
               free=(0.45, 0, 1.2), ringleg=(-0.8, 0, 0.5), freeleg=(0.8, 0, 0.4)),
    "E3": dict(note="low hero, turned: fist planted outside the ring foot, torso turned to the ring side",
               grounded=True, sink=2.0, plant=True, body=(0.6, 0.25, 0), head=(-0.5, -0.2, 0), ring=(0, 0, 0.45),
               free=(0.9, 0, 0.25), ringleg=(-1.45, 0, 0.15), freeleg=(1.15, 0, 0.1)),
    # F  stand-up: halfway pose (F1 has none: an eased blend straight back to idle)
    "F2": dict(note="push off: the ring fist pushes off the ground first, chest leads up", grounded=True, sink=1.5,
               body=(0.35, 0, 0), head=(-0.3, 0, 0), ring=(0.4, 0, 0.2), free=(0.5, 0, 0.3),
               ringleg=(-0.5, 0, 0.08), freeleg=(0.35, 0, 0.05)),
    "F3": dict(note="power stand: rises tall, chest out, ring fist clenched in front", grounded=True,
               body=(-0.12, 0, 0), head=(-0.2, 0, 0), ring=(-0.3, 0, 0.1), free=(0.2, 0, 0.15),
               ringleg=(0.05, 0, 0.06), freeleg=(0.05, 0, 0.06)),
}
SOLVED = {"idle": solve(IDLE)[:2]}
SINK = {}
for k, p in POSES.items():
    pp, d, sk = solve(p)
    SOLVED[k] = (pp, d)
    SINK[k] = sk

# ---- the timeline in ticks ------------------------------------------------------------------------------
T_CROUCH, T_ARMED, T_FULL, T_GO = 10, 17, 35, 42          # crouch starts; armed (0.35 s); full (1.25 s); take-off
T_RISE, T_APEX, T_LAND = 47, 67, 95                       # launch ends; apex; touchdown
T_UP, T_IDLE, T_END = 111, 119, 135                       # stand-up starts after 0.8 s; idle; end
APEX_H = 28.0
scene.frame_start, scene.frame_end = 0, T_END


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def mix(a, b, w):
    return {k: (a[0][k][0] * (1 - w) + b[0][k][0] * w, a[0][k][1] * (1 - w) + b[0][k][1] * w) for k in PARTS}


T1 = dict(A="A1", B="B1", C="C1", E="E1", F="F1")
SEQ = {"1a": dict(T1, D="D1a"), "1b": dict(T1, D="D1b"), "1c": dict(T1, D="D1c"),
       "2": dict(A="A2", B="B2", C="C2", D="D2", E="E2", F="F2")}


def pose_at(f, n):
    """The resolved pose of take n at tick f, and the height of the feet above the ground in blocks."""
    q = SEQ[n]
    I, A, B, C, D, E = (SOLVED[x] for x in ("idle", q["A"], q["B"], q["C"], q["D"], q["E"]))
    as_pose = lambda q: (q, 0)
    if f < T_CROUCH:
        return mix(I, I, 0), 0.0
    if f < T_GO:
        if f < T_ARMED:
            w = 0.35 * smooth((f - T_CROUCH) / (T_ARMED - T_CROUCH))
        else:
            w = 0.35 + 0.65 * smooth((f - T_ARMED) / (T_FULL - T_ARMED))
        p = mix(I, A, w)
        if f >= T_FULL:                                    # full charge: the ring fist trembles
            r, o = p["rarm"]
            p["rarm"] = (r + np.array([0.03 * math.sin(f * 2.1), 0, 0.02 * math.sin(f * 3.3)]), o)
        return p, 0.0
    if f < T_LAND:
        if f < T_APEX:
            h = APEX_H * (1 - (1 - (f - T_GO) / (T_APEX - T_GO)) ** 2)
        else:
            h = APEX_H * (1 - ((f - T_APEX) / (T_LAND - T_APEX)) ** 2)
        if f < T_RISE:
            p = mix(A, B, smooth((f - T_GO) / 2.0))
        elif f < T_APEX:
            p = mix(as_pose(mix(A, B, 1)), C, smooth((f - T_RISE) / 3.0))
        else:
            p = mix(as_pose(mix(C, C, 0)), D, smooth((f - T_APEX) / 8.0))
        return p, h
    if f < T_UP:
        return mix(as_pose(mix(D, D, 0)), E, smooth((f - T_LAND) / 2.0)), 0.0
    if f < T_IDLE:
        u = (f - T_UP) / (T_IDLE - T_UP)
        mid = SOLVED.get(SEQ[n]["F"])
        if mid is None:
            return mix(E, I, smooth(u)), 0.0
        if u < 0.5:
            return mix(E, mid, smooth(u * 2)), 0.0
        return mix(mid, I, smooth(u * 2 - 1)), 0.0
    return mix(I, I, 0), 0.0


# ======================================================================================================
# The look: a Minecraft player in J's colours (purple hair, tan skin, pale shirt, dark trousers)
# ======================================================================================================
def mat(name, rgb, emit=0.0, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1)
        p.inputs["Emission Strength"].default_value = emit
    return m


SKIN, HAIR = mat("sj skin", (0.55, 0.32, 0.2)), mat("sj hair", (0.32, 0.18, 0.5))
SHIRT, PANTS = mat("sj shirt", (0.62, 0.72, 0.72)), mat("sj trousers", (0.08, 0.05, 0.1))
SHOE, EYE = mat("sj shoes", (0.03, 0.03, 0.03)), mat("sj eyes", (0.9, 0.95, 1.0))
GOLD = mat("sj ring gold", (0.85, 0.62, 0.18), rough=0.25, metal=1.0)
GREEN = (0.12, 1.0, 0.3)

# Boxes per part in model px, relative to the part's pivot.
LOOK = {
    "head": [((-4, -8, -4), (4, 0, 4), SKIN), ((-4.2, -8.2, -4.2), (4.2, -5.6, 4.2), HAIR),
             ((-4.2, -8.2, -0.5), (4.2, -1.5, 4.2), HAIR), ((-3, -4.6, -4.15), (-1.2, -3.6, -4.05), EYE),
             ((1.2, -4.6, -4.15), (3, -3.6, -4.05), EYE)],
    "body": [((-4, 0, -2), (4, 12, 2), SHIRT)],
    "rarm": [((-3, -2, -2), (1, 6.5, 2), SHIRT), ((-3, 6.5, -2), (1, 10, 2), SKIN),
             ((-3.35, 7.1, -2.35), (1.35, 8.1, 2.35), GOLD)],
    "larm": [((-1, -2, -2), (3, 6.5, 2), SHIRT), ((-1, 6.5, -2), (3, 10, 2), SKIN)],
    "rleg": [((-2, 0, -2), (2, 10, 2), PANTS), ((-2.05, 10, -2.05), (2.05, 12, 2.05), SHOE)],
    "lleg": [((-2, 0, -2), (2, 10, 2), PANTS), ((-2.05, 10, -2.05), (2.05, 12, 2.05), SHOE)],
}


def box_mesh(name, boxes, extra=None):
    bm = bmesh.new()
    mats = []
    for a, b, m in boxes + (extra or []):
        if m not in mats:
            mats.append(m)
        res = bmesh.ops.create_cube(bm, size=1.0)
        vs = res["verts"]
        for v in vs:
            v.co = Vector((a[0] if v.co.x < 0 else b[0], a[1] if v.co.y < 0 else b[1], a[2] if v.co.z < 0 else b[2]))
        for fc in {f for v in vs for f in v.link_faces}:
            fc.material_index = mats.index(m)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


def keyed(owner, path, frames_values, index=-1):
    for f, v in frames_values:
        if index >= 0:
            getattr(owner, path)[index] = v
            owner.keyframe_insert(path, index=index, frame=f)
        else:
            setattr(owner, path, v)
            owner.keyframe_insert(path, frame=f)


def emissive(name, rgb, strength, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m, em.inputs["Strength"], mx.inputs[0]


def keyed_socket(sock, frames_values):
    for f, v in frames_values:
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=f)


rng = np.random.default_rng(81)
SPACING = 5.0
TAKES = tuple(SEQ)
X0 = {n: (i - 1.5) * SPACING for i, n in enumerate(TAKES)}
POSE_DUMP = {}

for n in TAKES:
    base = Vector((X0[n], 0, 0))
    # the rig: model px -> blocks, y down -> z up, forward -z -> -Y (facing the front cameras)
    rig = link(bpy.data.objects.new(f"SJ rig T{n}", None))
    rig.empty_display_size = 0.3
    rig.rotation_euler = (R(-90), 0, 0)
    rig.scale = (1 / 16,) * 3
    gem_m, gem_s, _ = emissive(f"sj ring gem T{n}", GREEN, 4.0)
    parts = {}
    for part in PARTS:
        extra = [((-3.75, 7.2, -0.7), (-3.3, 8.0, 0.7), gem_m)] if part == "rarm" else None
        o = link(bpy.data.objects.new(f"SJ {part} T{n}", box_mesh(f"sj {part} T{n}", LOOK[part], extra)))
        o.parent = rig
        o.rotation_mode = "XYZ"
        parts[part] = o
    # the ring's flare: a light at the ring fist
    li = bpy.data.lights.new(f"sj ring light T{n}", "POINT")
    li.color = GREEN; li.shadow_soft_size = 0.05
    lo = link(bpy.data.objects.new(f"SJ ring light T{n}", li))
    lo.parent = parts["rarm"]; lo.location = (-4.5, 8.5, 0)
    # every tick: pose, height
    for f in range(T_END + 1):
        p, h = pose_at(f, n)
        rig.location = base + Vector((0, 0, 1.5 + h))
        rig.keyframe_insert("location", frame=f)
        for part, o in parts.items():
            r, off = p[part]
            o.location = Vector(np.asarray(PIVOT[part]) + off)
            o.rotation_euler = tuple(r)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)
    flare = [(0, 0), (T_CROUCH, 0), (T_ARMED, 8), (T_FULL, 40), (T_GO - 1, 45), (T_GO + 1, 420), (T_GO + 6, 30),
             (T_APEX, 30), (T_LAND - 2, 160), (T_LAND, 600), (T_LAND + 8, 60), (T_UP, 25), (T_IDLE, 0), (T_END, 0)]
    keyed(li, "energy", flare)
    keyed_socket(gem_s, [(f, 3 + v / 12) for f, v in flare])
    for oo in [rig] + list(parts.values()):
        if oo.animation_data and oo.animation_data.action:
            for fc in oo.animation_data.action.fcurves if hasattr(oo.animation_data.action, "fcurves") else []:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- take-off: a ring of hard light skimming the ground, a dirt burst -------------------------------
    rm_, rs, ra = emissive(f"sj takeoff ring T{n}", GREEN, 6.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.035, major_segments=64, minor_segments=6)
    ring = bpy.context.active_object
    for c in list(ring.users_collection):
        c.objects.unlink(ring)
    col.objects.link(ring)
    ring.name = f"SJ takeoff ring T{n}"
    ring.data.materials.append(rm_)
    ring.location = base + Vector((0, 0, 0.06))
    ring.scale = (1, 1, 0.6)
    keyed(ring, "scale", [(T_GO - 1, (0.2, 0.2, 0.6)), (T_GO + 10, (4.0, 4.0, 0.6))])
    keyed_socket(ra, [(T_GO - 1, 0), (T_GO, 1), (T_GO + 6, 0.7), (T_GO + 10, 0)])
    # ---- landing: a low wall of hard-light panes rolling out with the quake -------------------------------
    R_MAX = 11.0                                       # 5 to 14 blocks by fall height; a full 28-block fall here
    t_out = R_MAX / 0.75
    bm = bmesh.new()
    NP = 56
    for i in range(NP):
        a0, a1 = 2 * math.pi * i / NP, 2 * math.pi * (i + 0.8) / NP
        hgt = 0.55 + 0.25 * rng.random()
        v = [bm.verts.new((math.cos(a0), math.sin(a0), 0)), bm.verts.new((math.cos(a1), math.sin(a1), 0)),
             bm.verts.new((math.cos(a1), math.sin(a1), hgt)), bm.verts.new((math.cos(a0), math.sin(a0), hgt))]
        bm.faces.new(v)
    wme = bpy.data.meshes.new(f"sj quake wall T{n}")
    bm.to_mesh(wme); bm.free()
    wm_, ws, wa = emissive(f"sj quake wall T{n}", GREEN, 3.0)
    wme.materials.append(wm_)
    wall = link(bpy.data.objects.new(f"SJ quake wall T{n}", wme))
    wall.location = base
    keyed(wall, "scale", [(T_LAND - 1, (0.05, 0.05, 0.0)), (T_LAND, (0.4, 0.4, 1.0)),
                          (T_LAND + round(t_out), (R_MAX, R_MAX, 0.35))])
    keyed_socket(wa, [(T_LAND - 1, 0), (T_LAND, 0.9), (T_LAND + round(t_out * 0.6), 0.6), (T_LAND + round(t_out), 0)])
    # ---- dirt and shards: thrown up at take-off and along the wave ---------------------------------------
    dirt = mat(f"sj dirt T{n}", (0.2, 0.12, 0.06))
    shard_m, _, _ = emissive(f"sj shard T{n}", GREEN, 5.0)
    cube = box_mesh(f"sj chunk T{n}", [((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), dirt)])
    shard = box_mesh(f"sj shard T{n}", [((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), shard_m)])
    bursts = [(T_GO, 0.6, 14, 0.0)]                    # (tick, radius, count, wave speed)
    for t0, r0, cnt, speed in bursts + [(T_LAND, 0.5, 46, 0.75)]:
        for i in range(cnt):
            ang = rng.random() * 2 * math.pi
            r = r0 + (rng.random() * (R_MAX - 1) if speed else rng.random() * 0.6)
            ts = t0 + (r / speed if speed else 0)
            is_shard = speed and i % 4 == 0
            o = link(bpy.data.objects.new(f"SJ {'shard' if is_shard else 'dirt'} T{n}", shard if is_shard else cube))
            sz = (0.07 + 0.08 * rng.random()) * (0.7 if is_shard else 1)
            vup = 0.18 + 0.15 * rng.random()
            vout = 0.04 + 0.06 * rng.random()
            o.rotation_euler = tuple(rng.random(3) * 3)
            keys = []
            for k in range(0, 13, 2):
                rr = r + vout * k
                z = max(0.0, vup * k - 0.04 * k * k)
                keys.append((round(ts) + k, Vector((math.cos(ang) * rr, math.sin(ang) * rr, z + sz / 2)) + base))
            o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=round(ts) - 1)
            o.scale = (sz,) * 3; o.keyframe_insert("scale", frame=round(ts))
            o.keyframe_insert("scale", frame=round(ts) + 8)
            o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=round(ts) + 13)
            for fr, loc in keys:
                o.location = loc
                o.keyframe_insert("location", frame=fr)
    # ---- optional: the cracked-ground decal in hard light, flat, centred on the feet ----------------------
    dm = bpy.data.materials.new(f"sj crack decal T{n}")
    dm.use_nodes = True
    N, L = dm.node_tree.nodes, dm.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 3.2
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    edge = N.new("ShaderNodeMapRange"); edge.inputs["From Min"].default_value = 0.0
    edge.inputs["From Max"].default_value = 0.035; edge.inputs["To Min"].default_value = 1.0
    edge.inputs["To Max"].default_value = 0.0
    L.new(vor.outputs["Distance"], edge.inputs["Value"])
    grad = N.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
    L.new(tc.outputs["Object"], grad.inputs["Vector"])
    m1 = N.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    L.new(edge.outputs[0], m1.inputs[0]); L.new(grad.outputs["Fac"], m1.inputs[1])
    fade = N.new("ShaderNodeValue"); fade.outputs[0].default_value = 0.0
    m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.use_clamp = True
    L.new(m1.outputs[0], m2.inputs[0]); L.new(fade.outputs[0], m2.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*GREEN, 1); em.inputs["Strength"].default_value = 5
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(m2.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    try:
        dm.surface_render_method = "BLENDED"
    except Exception:
        pass
    keyed_socket(fade.outputs[0], [(T_LAND - 1, 0), (T_LAND, 1.6), (T_UP, 1.0), (T_END, 0.0)])
    bpy.ops.mesh.primitive_plane_add(size=5.0)
    dec = bpy.context.active_object
    for c in list(dec.users_collection):
        c.objects.unlink(dec)
    col.objects.link(dec)
    dec.name = f"SJ crack decal T{n} (optional)"
    dec.location = base + Vector((0, 0, 0.01))
    dec.data.materials.append(dm)
    # labels
    cu = bpy.data.curves.new(f"sj label T{n}", "FONT")
    cu.body = f"{n}:  " + " ".join(SEQ[n][b] for b in "ABCDEF")
    cu.size = 0.28; cu.align_x = "CENTER"
    lb = link(bpy.data.objects.new(f"SJ label T{n}", cu))
    lb.location = base + Vector((0, 1.6, 2.7)); lb.rotation_euler = (R(90), 0, 0)
    lm, _, _ = emissive(f"sj label T{n}", (0.85, 1, 0.9), 1.5)
    cu.materials.append(lm)
    lb.parent = rig; lb.matrix_parent_inverse = rig.matrix_world.inverted()

# ---- the poses for the game ----------------------------------------------------------------------------
for k in ["idle"] + list(POSES):
    p, d = SOLVED[k]
    POSE_DUMP[k] = {"note": POSES.get(k, {}).get("note", "standing"), "hip_drop_px": round(d, 2),
                    "torso_sink_px": round(SINK.get(k, 0.0), 2),
                    "parts": {part: {"rot": [round(float(v), 3) for v in p[part][0]],
                                     "offset_px": [round(float(v), 2) for v in p[part][1]]} for part in PARTS}}
POSE_DUMP["_about"] = {
    "space": "Minecraft model space, right-handed player: rarm is the ring arm. rot = (xRot, yRot, zRot) radians, "
             "applied as ModelPart rotations; offset_px is added to the part's x, y, z (model px, y down). "
             "Left-handed: swap rarm<->larm and rleg<->lleg, negate every yRot and zRot and every x offset.",
    "timing_ticks": {"armed": T_ARMED - T_CROUCH, "full": T_FULL - T_CROUCH, "launch": T_RISE - T_GO,
                     "rising": T_APEX - T_RISE, "falling": T_LAND - T_APEX, "landing_hold": T_UP - T_LAND,
                     "stand_up": T_IDLE - T_UP},
    "blends_ticks": {"into_launch": 2, "into_rising": 3, "into_falling": 8, "into_landing": 2,
                     "windup": "35% of the pose when armed, 100% at full, eased"},
}
with open(os.path.join(FOLDER, "super_jump_poses.json"), "w") as fh:
    json.dump(POSE_DUMP, fh, indent=1)

# ---- room, lights, cameras ------------------------------------------------------------------------------
world = bpy.data.worlds.new("SJ World"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.045, 0.06, 0.09, 1); bg.inputs[1].default_value = 1.0
scene.world = world
fl = bpy.data.meshes.new("sj ground")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60); bm.to_mesh(fl); bm.free()
fo = link(bpy.data.objects.new("SJ ground", fl))
gm = mat("sj grass", (0.07, 0.11, 0.045), rough=0.9)
fl.materials.append(gm)
key = bpy.data.lights.new("sj sun", "SUN"); key.energy = 2.2; key.angle = R(8)
ko = link(bpy.data.objects.new("SJ sun", key)); ko.rotation_euler = (R(50), R(10), R(-35))

follow = link(bpy.data.objects.new("SJ follow", None))
for f in range(T_END + 1):
    follow.location = (0, 0, pose_at(f, TAKES[0])[1]); follow.keyframe_insert("location", frame=f)


def camera(name, eye, target, lens=50, clip=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    if clip:
        cd.clip_start, cd.clip_end = clip
    c = link(bpy.data.objects.new(name, cd))
    c.location = eye
    c.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    c.parent = follow
    return c


cams = {"all": camera("Cam 3/4 all", Vector((-12.5, -19.0, 3.6)), Vector((0, 0, 0.9)), 40)}
for n in TAKES:
    t = Vector((X0[n], 0, 0.75))
    # the side camera stands between this take and the next, clipping the takes either side of it
    cams[f"side{n}"] = camera(f"Cam side T{n}", t + Vector((4.2, 0, 0.15)), t, 40, (0.5, 6.5))
    cams[f"34_{n}"] = camera(f"Cam 3/4 T{n}", t + Vector((-2.4, -3.6, 0.55)), t, 40, (0.5, 7.0))
    cams[f"back{n}"] = camera(f"Cam back T{n}", t + Vector((0.5, 4.3, 0.9)), t, 40, (0.5, 7.0))
scene.camera = cams["all"]
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("SJ Glow", "CompositorNodeTree")
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

BEATS = {"A_windup": T_FULL + 3, "B_launch": T_GO + 3, "C_rising": T_APEX - 4, "D_falling": T_LAND - 6,
         "E_landing": T_LAND + 8, "F_standup": (T_UP + T_IDLE) // 2}
rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    scene.camera = cams["all"]
    for beat, fr in BEATS.items():
        scene.frame_set(fr)
        scene.render.filepath = os.path.join(rdir, f"82_{beat}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["all"]
scene.frame_set(0)
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
                    sp.shading.type = "RENDERED"
                    try:
                        sp.shading.use_compositor = "ALWAYS"
                    except Exception:
                        pass
            a.tag_redraw()


def _tidy():
    for o in bpy.context.scene.objects:
        if not o.name.startswith(("SJ", "Cam")):
            o.hide_viewport = True; o.hide_render = True


def _after():
    try:
        _tidy()
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


bpy.app.timers.register(_after, first_interval=4.0)
bpy.app.timers.register(lambda: (_tidy(), None)[1], first_interval=8.0)
print("saved", OUT)
