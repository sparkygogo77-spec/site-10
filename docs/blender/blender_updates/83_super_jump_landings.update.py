# Pass 83: super jump landings (J: landings should differ by what you land in or on; a fall deeper than meant
# becomes the Take 3 landing; the others land like Take 1 with the ring fist on the ground, but Take 1's body
# looked odd from behind; the pane wall and ground cracks are out: instead a barrier of hard-light particles
# forms where you land, that you land on top of, pressed against the blocks the crater destroyed. Also: the
# ring fist starts coming down as soon as the rise loses momentum; Take 2 is out; falls 1a, 1b, 1c all fine).
# Row 1: L1 grass, L2 stone, L3 sand, L4 water (a barrier pad on the water), L5 a pit deeper than meant (E3).
# Row 2: J1a, J1b, J1c: Take 1 full jumps with the rising fix and the new landing, one per fall arm.
# Cameras: Cam all; Cam 3/4 / side / back / above + L1..L5, J1a..J1c. Builds LanternLive\super_jump_landings.blend.
import json, math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

R = math.radians
OUT = os.path.join(FOLDER, "super_jump_landings.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Super Jump Landings")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Super Jump Landings")
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



# ======================================================================================================
# Pass 83: landings by surface. Poses from rounds 1-2 plus E1b (Take 1 fixed from behind: no torso sink, a
# real low split stance). Fall pose D1a (Take 1's fall, the ring arm aimed down like Take 2's).
# ======================================================================================================
POSES["E1b"] = dict(note="E1 fixed from behind: no torso sink; the hips drop into a low split, ring foot "
                         "forward, back knee down, ring fist planted", grounded=True, plant=True,
                    body=(0.55, 0, 0), head=(-0.6, 0, 0), ring=(0, 0, 0.15), free=(1.25, 0, 0.5),
                    ringleg=(-1.2, 0, 0.12), freeleg=(1.3, 0, 0.1))
pp, d, sk = solve(POSES["E1b"])
SOLVED["E1b"] = (pp, d)
SINK["E1b"] = sk

# Every landing is Take 1's (E1b, fixed from behind) except a fall deeper than meant, which becomes Take 3's (E3).
# Row 1 (y = 0): landings by surface, falling into view. Row 2 (y = 16): Take 1 full jumps with the rising
# fix (the ring fist starts coming down as soon as the rise loses momentum), one per fall arm 1a, 1b, 1c.
CASES = [
    dict(key="L1", surface="grass", E="E1b", F="F1", D="D1a", h0=8.0, z=0.0, note="grass: crater, dirt thrown"),
    dict(key="L2", surface="stone", E="E1b", F="F1", D="D1a", h0=8.0, z=0.0, note="stone: shallow crater, sparks"),
    dict(key="L3", surface="sand", E="E1b", F="F1", D="D1a", h0=8.0, z=0.0, note="sand: wide shallow crater, spray"),
    dict(key="L4", surface="water", E="E1b", F="F1", D="D1a", h0=8.0, z=-0.15, note="water: lands on a barrier pad"),
    dict(key="L5", surface="pit", E="E3", F="F3", D="D1a", h0=14.0, z=-6.0, note="pit, deeper than meant: Take 3 landing"),
    dict(key="J1a", surface="grass", E="E1b", F="F1", D="D1a", full=True, z=0.0, note="full jump, fall 1a"),
    dict(key="J1b", surface="grass", E="E1b", F="F1", D="D1b", full=True, z=0.0, note="full jump, fall 1b"),
    dict(key="J1c", surface="grass", E="E1b", F="F1", D="D1c", full=True, z=0.0, note="full jump, fall 1c"),
]
SPACING = 12.0
POS = {}
for i, c in enumerate(c for c in CASES if not c.get("full")):
    POS[c["key"]] = ((i - 2) * SPACING, 0.0)
for i, c in enumerate(c for c in CASES if c.get("full")):
    POS[c["key"]] = ((i - 1) * SPACING, 16.0)
FALL = {"L5": 26}                                        # ticks of falling in view
HOLD = {"L5": 24}                                        # landing hold (0.8 s; deeper: 1.2 s)
T_END = T_END + 8
scene.frame_start, scene.frame_end = 0, T_END


def timing(c):
    hold = HOLD.get(c["key"], 16)
    return T_LAND, T_LAND + hold, T_LAND + hold + 8


def pose_at(f, c):
    t_land, t_up, t_idle = timing(c)
    I, D, E = SOLVED["idle"], SOLVED[c["D"]], SOLVED[c["E"]]
    if f < t_land:
        if c.get("full"):
            return full_air(f, c)
        fall = FALL.get(c["key"], 18)
        u = max(0.0, (f - (t_land - fall)) / fall)
        return mix(D, D, 0), c["h0"] * (1 - u * u)
    if f < t_up:
        return mix((mix(D, D, 0), 0), E, smooth((f - t_land) / 2.0)), 0.0
    if f < t_idle:
        u = (f - t_up) / (t_idle - t_up)
        mid = SOLVED.get(c["F"])
        if mid is None:
            return mix(E, I, smooth(u)), 0.0
        return (mix(E, mid, smooth(u * 2)) if u < 0.5 else mix(mid, I, smooth(u * 2 - 1))), 0.0
    return mix(I, I, 0), 0.0


def full_air(f, c):
    """Take 1 from the ground to touchdown. The rise: the ring fist punches up, and as the climb slows (from
    halfway up) the arms ease down toward the fall pose, reaching it at the apex; body and legs follow after."""
    I, A, B, C, D = (SOLVED[x] for x in ("idle", "A1", "B1", "C1", c["D"]))
    if f < T_CROUCH:
        return mix(I, I, 0), 0.0
    if f < T_GO:
        w = 0.35 * smooth((f - T_CROUCH) / (T_ARMED - T_CROUCH)) if f < T_ARMED else \
            0.35 + 0.65 * smooth((f - T_ARMED) / (T_FULL - T_ARMED))
        return mix(I, A, w), 0.0
    if f < T_APEX:
        h = APEX_H * (1 - (1 - (f - T_GO) / (T_APEX - T_GO)) ** 2)
    else:
        h = APEX_H * (1 - ((f - T_APEX) / (T_LAND - T_APEX)) ** 2)
    if f < T_RISE:
        return mix(A, B, smooth((f - T_GO) / 2.0)), h
    BC = mix((mix(A, B, 1), 0), C, smooth((f - T_RISE) / 3.0))
    if f < T_APEX:
        half = T_RISE + (T_APEX - T_RISE) * 0.45            # momentum fading: the arms start down
        wa = smooth((f - half) / (T_APEX - half))
        for part in ("rarm", "larm"):
            r0, o0 = BC[part]
            r1, o1 = D[0][part]
            BC[part] = (r0 * (1 - wa) + r1 * wa, o0 * (1 - wa) + o1 * wa)
        return BC, h
    p = mix((mix(C, C, 0), 0), D, smooth((f - T_APEX) / 8.0))
    for part in ("rarm", "larm"):
        p[part] = D[0][part]
    return p, h


rng = np.random.default_rng(83)

# ---- blocks ---------------------------------------------------------------------------------------------
BLOCK = {
    "grass_top": mat("sj grass top", (0.16, 0.3, 0.08), rough=0.9), "dirt": mat("sj dirt", (0.26, 0.16, 0.09), rough=0.95),
    "stone": mat("sj stone", (0.3, 0.3, 0.31), rough=0.85), "sand": mat("sj sand", (0.62, 0.55, 0.36), rough=0.95),
    "sandstone": mat("sj sandstone", (0.55, 0.47, 0.3), rough=0.9),
}


def block_mats(surface, k):
    """(top material, side material) of a block k layers down."""
    if surface == "stone":
        return BLOCK["stone"], BLOCK["stone"]
    if surface in ("sand", "water"):
        m = BLOCK["sand"] if k < 3 else BLOCK["sandstone"]
        return m, m
    if k >= 3:
        return BLOCK["stone"], BLOCK["stone"]
    return (BLOCK["grass_top"] if k == 0 else BLOCK["dirt"]), BLOCK["dirt"]


def add_block(bm, mats, x, y, ztop, top, side, size=1.0):
    res = bmesh.ops.create_cube(bm, size=size)
    for v in res["verts"]:
        v.co += Vector((x, y, ztop - size / 2))
    for fc in {f for v in res["verts"] for f in v.link_faces}:
        m = top if fc.normal.z > 0.5 else side
        if m not in mats:
            mats.append(m)
        fc.material_index = mats.index(m)


def crater_radii(key, surface):
    """Radius of the hole in each layer, from the top: the crater the landing blasts out."""
    return {"stone": [2.2, 1.2], "sand": [3.6, 2.4, 1.0], "water": [], "pit": [3.6, 2.8, 1.9, 1.0]}.get(
        surface, [3.0, 2.0, 1.0])


def build_ground(case):
    key, surface = case["key"], case["surface"]
    cx, cy = POS[key]
    ground_z = 0.0
    radii = crater_radii(key, surface)
    pit_r, pit_depth = (2.6, 6) if surface == "pit" else (0, 0)
    pool_r, pool_depth = (5.2, 2) if surface == "water" else (0, 0)
    bm = bmesh.new(); mats = []
    flying = []
    H = 6
    for i in range(-H, H):
        for j in range(-H, H):
            x, y = cx + i + 0.5, cy + j + 0.5
            r = math.hypot(i + 0.5, j + 0.5)
            depth = 4 if r < 5.5 else 1
            if surface == "pit":
                depth = 11 if r < 4.5 else 1
            for k in range(depth):
                ztop = ground_z - k
                if r < pit_r and k < pit_depth:
                    continue                                   # the pit was already there
                if r < pool_r and k < pool_depth:
                    continue                                   # the pool
                kk = k - pit_depth                             # layers below the landing level
                top, side = block_mats(surface if surface != "pit" else "grass", k)
                if 0 <= kk < len(radii) and r < radii[kk] and not (surface == "pit" and r >= pit_r):
                    flying.append((x, y, ztop, top, side, r))  # blasted out by the landing
                    continue
                add_block(bm, mats, x, y, ztop, top, side)
    me = bpy.data.meshes.new(f"sj ground {key}")
    bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    link(bpy.data.objects.new(f"SJ ground {key}", me))
    return flying


def keyframes(o, path, fv):
    for f, v in fv:
        setattr(o, path, v)
        o.keyframe_insert(path, frame=f)


def throw(name, mesh, start, ang, t0, size, vout, vup, life, spin=True, base_z=0.0):
    o = link(bpy.data.objects.new(name, mesh))
    keyframes(o, "scale", [(t0 - 1, (0, 0, 0)), (t0, (size,) * 3), (t0 + int(life * 0.4), (size * 0.8,) * 3),
                           (t0 + life, (0, 0, 0))])
    for k in range(0, life + 1, 2):
        rr = vout * k
        z = max(base_z - start.z, vup * k - 0.045 * k * k)
        o.location = start + Vector((math.cos(ang) * rr, math.sin(ang) * rr, z))
        o.keyframe_insert("location", frame=t0 + k)
    if spin:
        sp = rng.normal(0, 0.35, 3)
        keyframes(o, "rotation_euler", [(t0, (0, 0, 0)), (t0 + life, tuple(sp * life))])
    return o


def cube_mesh(name, m):
    return box_mesh(name, [((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), m)])


# ---- the hard-light particle barrier ---------------------------------------------------------------------
def barrier_material(name, gain=1.0, opacity=0.85):
    """Each particle switches on as the wave from the impact reaches it (t0, with a bright front), flickers while
    it holds, and pops bright as it dissolves at its own random time (t1)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()

    def op(o, a, b=None, clamp=False):
        n = N.new("ShaderNodeMath"); n.operation = o; n.use_clamp = clamp
        for i, s_ in enumerate((a, b)):
            if s_ is None:
                continue
            if isinstance(s_, (int, float)):
                n.inputs[i].default_value = s_
            else:
                L.new(s_, n.inputs[i])
        return n.outputs[0]

    fr = N.new("ShaderNodeValue")
    dr = fr.outputs[0].driver_add("default_value").driver
    dr.type = "SCRIPTED"; dr.expression = "frame"
    f = fr.outputs[0]
    at = {}
    for nm in ("t0", "t1", "seed"):
        a = N.new("ShaderNodeAttribute"); a.attribute_type = "GEOMETRY"; a.attribute_name = nm
        at[nm] = a.outputs["Fac"]
    on = op("MULTIPLY", op("MULTIPLY", op("SUBTRACT", f, at["t0"]), 2.0, True),
            op("MULTIPLY", op("SUBTRACT", at["t1"], f), 2.0, True))
    front = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", op("SUBTRACT", f, at["t0"]), 1.4), 2.0)))
    pop = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", op("SUBTRACT", f, at["t1"]), 1.0), 2.0)))
    flick = op("ADD", 0.7, op("MULTIPLY", 0.3, op("SINE", op("ADD", op("MULTIPLY", f, 0.9), op("MULTIPLY", at["seed"], 40.0)))))
    strength = op("MULTIPLY", op("ADD", op("MULTIPLY", on, op("ADD", op("MULTIPLY", flick, 2.4), op("MULTIPLY", front, 7.0))),
                  op("MULTIPLY", pop, 6.0)), gain)
    alpha = op("ADD", op("MULTIPLY", on, opacity), op("MULTIPLY", pop, opacity), True)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.3, 1.0, 0.5, 1)
    L.new(strength, em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(alpha, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def build_barrier(case, radii):
    """A barrier of hard-light motes the player lands on: a slightly sagging membrane spanning the crater,
    its rim pressed against the broken blocks, and a lining down the crater walls."""
    key, surface, land_z = case["key"], case["surface"], case["z"]
    t_land, t_up, _ = timing(case)
    cx, cy = POS[key]
    r_top = (radii[0] if radii else 2.2) + 0.25
    depth = len(radii)
    pts = []                                              # (x, y, z, size)
    step = 0.17
    for i in np.arange(-r_top, r_top + step, step):
        for j in np.arange(-r_top, r_top + step, step):
            r = math.hypot(i, j)
            if r > r_top:
                continue
            jx, jy = rng.normal(0, 0.04, 2)
            sag = 0.12 * (1 - (r / r_top) ** 2)
            pts.append((i + jx, j + jy, 0.03 - sag, 0.1 + 0.04 * rng.random()))
    for ang in np.linspace(0, 2 * math.pi, int(2 * math.pi * r_top / 0.16), endpoint=False):
        for z in (0.06, 0.2, 0.33):                       # the rim, standing against the broken edge
            rr = r_top + rng.normal(0, 0.03)
            pts.append((math.cos(ang) * rr, math.sin(ang) * rr, z, 0.12))
    for kk, rk in enumerate(radii):                       # lining down the crater walls, layer by layer
        for ang in np.linspace(0, 2 * math.pi, max(8, int(2 * math.pi * rk / 0.22)), endpoint=False):
            for zz in (0.15, 0.5, 0.85):
                rr = rk + 0.05
                pts.append((math.cos(ang) * rr, math.sin(ang) * rr, -kk - zz, 0.13))
    bm = bmesh.new()
    t0s, t1s, seeds = [], [], []
    for x, y, z, s in pts:
        a = rng.random() * math.pi
        c, sn = math.cos(a) * s / 2, math.sin(a) * s / 2
        vs = [bm.verts.new((x + dx, y + dy, z)) for dx, dy in ((c, sn), (-sn, c), (-c, -sn), (sn, -c))]
        bm.faces.new(vs)
        r = math.hypot(x, y) + max(0.0, -z) * 0.6
        t0 = t_land + r / 0.75 * 0.6 + rng.random() * 0.8   # spreads out from the impact
        t1 = t_up + 3 + rng.random() * 14                    # dissolves in its own random moment
        sd = rng.random()
        t0s += [t0] * 4; t1s += [t1] * 4; seeds += [sd] * 4
    me = bpy.data.meshes.new(f"sj barrier {key}")
    bm.to_mesh(me); bm.free()
    for nm, vals in (("t0", t0s), ("t1", t1s), ("seed", seeds)):
        at = me.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", np.asarray(vals, np.float32))
    me.materials.append(barrier_material(f"sj barrier {key}"))
    o = link(bpy.data.objects.new(f"SJ barrier {key}", me))
    o.location = (cx, cy, land_z if surface != "water" else -0.12)
    # the faint surface the motes make up: the same sagging membrane, switching on with the same wave
    bm = bmesh.new()
    rings, segs = 14, 56
    centre = bm.verts.new((0, 0, 0.03 - 0.12))
    prev = None
    vt = {centre: 0.0}
    for ri in range(1, rings + 1):
        r = r_top * ri / rings
        ring_v = [bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0.03 - 0.12 * (1 - (r / r_top) ** 2)))
                  for a in np.linspace(0, 2 * math.pi, segs, endpoint=False)]
        for v in ring_v:
            vt[v] = r
        for k in range(segs):
            a, b = ring_v[k], ring_v[(k + 1) % segs]
            if prev is None:
                bm.faces.new((centre, a, b))
            else:
                bm.faces.new((prev[k], a, b, prev[(k + 1) % segs]))
        prev = ring_v
    sm = bpy.data.meshes.new(f"sj barrier surface {key}")
    bm.verts.index_update()
    order = sorted(vt, key=lambda v: v.index)
    t0v = [t_land + vt[v] / 0.75 * 0.6 for v in order]
    bm.to_mesh(sm); bm.free()
    for nm, vals in (("t0", t0v), ("t1", [t_up + 10.0] * len(t0v)), ("seed", [0.5] * len(t0v))):
        at = sm.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", np.asarray(vals, np.float32))
    sm.materials.append(barrier_material(f"sj barrier surface {key}", gain=0.25, opacity=0.22))
    so = link(bpy.data.objects.new(f"SJ barrier surface {key}", sm))
    so.location = o.location
    return o


# ---- the cases -------------------------------------------------------------------------------------------
water_m = bpy.data.materials.new("sj water"); water_m.use_nodes = True
wp = water_m.node_tree.nodes.get("Principled BSDF")
wp.inputs["Base Color"].default_value = (0.05, 0.18, 0.3, 1); wp.inputs["Roughness"].default_value = 0.05
wp.inputs["Alpha"].default_value = 0.65
try:
    water_m.surface_render_method = "BLENDED"
except Exception:
    pass
spark_m, _, _ = emissive("sj spark", (1.0, 0.85, 0.45), 12.0)
drop_m, _, _ = emissive("sj droplet", (0.75, 0.9, 1.0), 1.5)
mote_m, _, _ = emissive("sj mote", (0.35, 1.0, 0.55), 6.0)
cubes = {k: cube_mesh(f"sj chunk {k}", m) for k, m in BLOCK.items()}
spark_c, drop_c, mote_c = cube_mesh("sj spark", spark_m), cube_mesh("sj droplet", drop_m), cube_mesh("sj mote", mote_m)

for case in CASES:
    key, surface, epose, land_z, note = case["key"], case["surface"], case["E"], case["z"], case["note"]
    t_land, t_up, t_idle = timing(case)
    cx, cy = POS[key]
    base = Vector((cx, cy, land_z))
    flying = build_ground(case)
    # the blocks the landing blasts out, thrown up and outward
    for x, y, ztop, top, side, r in flying:
        ang = math.atan2(y - cy, x - cx) + rng.normal(0, 0.25)
        mesh = cubes[{BLOCK["grass_top"]: "dirt", BLOCK["dirt"]: "dirt", BLOCK["stone"]: "stone",
                      BLOCK["sand"]: "sand", BLOCK["sandstone"]: "sandstone"}[side]]
        lift = 0.35 - 0.05 * r if surface != "sand" else 0.22
        throw(f"SJ block {key}", mesh, Vector((x, y, ztop - 0.5)), ang, t_land + int(r * 0.5),
              0.55, 0.05 + 0.04 * rng.random(), max(0.12, lift * 0.75 + rng.normal(0, 0.04)), 10)
    # the finer debris for each surface
    if surface in ("grass", "pit"):
        for _ in range(26):
            throw(f"SJ dirt {key}", cubes["dirt"], base + Vector((0, 0, 0.05)), rng.random() * 6.283, t_land,
                  0.1 + 0.08 * rng.random(), 0.1 + 0.12 * rng.random(), 0.2 + 0.2 * rng.random(), 16)
    if surface == "stone":
        for _ in range(24):
            throw(f"SJ spark {key}", spark_c, base + Vector((0, 0, 0.05)), rng.random() * 6.283, t_land,
                  0.035, 0.3 + 0.25 * rng.random(), 0.12 + 0.18 * rng.random(), 7)
        for _ in range(12):
            throw(f"SJ chip {key}", cubes["stone"], base + Vector((0, 0, 0.05)), rng.random() * 6.283, t_land,
                  0.1 + 0.06 * rng.random(), 0.1 + 0.1 * rng.random(), 0.25 + 0.15 * rng.random(), 14)
    if surface == "sand":
        for _ in range(60):
            throw(f"SJ spray {key}", cubes["sand"], base + Vector((0, 0, 0.05)), rng.random() * 6.283,
                  t_land + int(rng.random() * 3), 0.05 + 0.05 * rng.random(), 0.18 + 0.2 * rng.random(),
                  0.1 + 0.15 * rng.random(), 16, spin=False)
    if surface == "water":
        wme = bpy.data.meshes.new(f"sj water {key}")
        bmw = bmesh.new(); bmesh.ops.create_grid(bmw, x_segments=1, y_segments=1, size=5.2); bmw.to_mesh(wme); bmw.free()
        wme.materials.append(water_m)
        wo = link(bpy.data.objects.new(f"SJ water {key}", wme)); wo.location = (cx, cy, -0.2)
        for _ in range(50):
            throw(f"SJ splash {key}", drop_c, base + Vector((0, 0, 0.0)), rng.random() * 6.283,
                  t_land + int(rng.random() * 3), 0.03 + 0.03 * rng.random(), 0.08 + 0.14 * rng.random(),
                  0.3 + 0.25 * rng.random(), 16, spin=False, base_z=-0.25)
        rm_, rs, ra = emissive(f"sj ripple {key}", (0.8, 0.95, 1.0), 1.2)
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=64, minor_segments=5)
        rp = bpy.context.active_object
        for c in list(rp.users_collection):
            c.objects.unlink(rp)
        col.objects.link(rp); rp.name = f"SJ ripple {key}"; rp.data.materials.append(rm_)
        rp.location = (cx, cy, -0.18)
        keyframes(rp, "scale", [(t_land - 1, (0.1, 0.1, 1)), (t_land + 22, (5.0, 5.0, 1))])
        keyed_socket(ra, [(t_land - 1, 0), (t_land, 0.8), (t_land + 22, 0)])
    # motes rising from the barrier
    for _ in range(14):
        throw(f"SJ mote {key}", mote_c, base + Vector((rng.normal(0, 1.2), rng.normal(0, 1.2), 0.1)),
              rng.random() * 6.283, t_land + 2 + int(rng.random() * 8), 0.05, 0.01, 0.07 + 0.04 * rng.random(), 18,
              spin=False, base_z=-1)
    build_barrier(case, crater_radii(key, surface))

    # the player
    rig = link(bpy.data.objects.new(f"SJ rig {key}", None))
    rig.rotation_euler = (R(-90), 0, 0); rig.scale = (1 / 16,) * 3
    gem_m, gem_s, _ = emissive(f"sj ring gem {key}", GREEN, 4.0)
    parts = {}
    for part in PARTS:
        extra = [((-3.75, 7.2, -0.7), (-3.3, 8.0, 0.7), gem_m)] if part == "rarm" else None
        o = link(bpy.data.objects.new(f"SJ {part} {key}", box_mesh(f"sj {part} {key}", LOOK[part], extra)))
        o.parent = rig; o.rotation_mode = "XYZ"
        parts[part] = o
    li = bpy.data.lights.new(f"sj ring light {key}", "POINT"); li.color = GREEN; li.shadow_soft_size = 0.05
    lo = link(bpy.data.objects.new(f"SJ ring light {key}", li)); lo.parent = parts["rarm"]; lo.location = (-4.5, 8.5, 0)
    for f in range(T_END + 1):
        p, h = pose_at(f, case)
        rig.location = base + Vector((0, 0, 1.5 + h)); rig.keyframe_insert("location", frame=f)
        for part, o in parts.items():
            r_, off = p[part]
            o.location = Vector(np.asarray(PIVOT[part]) + off); o.rotation_euler = tuple(r_)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    flare = ([(0, 0), (T_CROUCH, 0), (T_FULL, 40), (T_GO + 1, 420), (T_GO + 6, 30), (T_APEX, 30)]
             if case.get("full") else [(0, 120)]) + [(t_land - 2, 160), (t_land, 600), (t_land + 8, 60), (t_up, 25), (t_idle, 0), (T_END, 0)]
    keyed(li, "energy", flare)
    keyed_socket(gem_s, [(f, 3 + v / 12) for f, v in flare])
    # label behind the player
    cu = bpy.data.curves.new(f"sj label {key}", "FONT")
    cu.body = f"{key}  {surface.upper()}  {case['D']} {epose}\n{note}"
    cu.size = 0.3; cu.align_x = "CENTER"
    lb = link(bpy.data.objects.new(f"SJ label {key}", cu))
    lb.location = Vector((cx, cy + 6.2, 3.2)); lb.rotation_euler = (R(90), 0, 0)
    lm, _, _ = emissive(f"sj label {key}", (0.85, 1, 0.9), 1.5)
    cu.materials.append(lm)

# ---- the poses for the game ------------------------------------------------------------------------------
dump = {}
for k in ["idle", "D1a", "E1b", "E2", "E3", "F2", "F3"]:
    p, d = SOLVED[k]
    dump[k] = {"note": POSES.get(k, {}).get("note", "standing"), "hip_drop_px": round(d, 2),
               "torso_sink_px": round(SINK.get(k, 0.0), 2),
               "parts": {part: {"rot": [round(float(v), 3) for v in p[part][0]],
                                "offset_px": [round(float(v), 2) for v in p[part][1]]} for part in PARTS}}
with open(os.path.join(FOLDER, "super_jump_landings_poses.json"), "w") as fh:
    json.dump(dump, fh, indent=1)

# ---- room, lights, cameras -------------------------------------------------------------------------------
world = bpy.data.worlds.new("SJ World"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.045, 0.06, 0.09, 1); bg.inputs[1].default_value = 1.0
scene.world = world
key_l = bpy.data.lights.new("sj sun", "SUN"); key_l.energy = 2.4; key_l.angle = R(8)
ko = link(bpy.data.objects.new("SJ sun", key_l)); ko.rotation_euler = (R(50), R(10), R(-35))


def camera(name, eye, target, lens=40):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 300
    c = link(bpy.data.objects.new(name, cd))
    c.location = eye
    c.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    return c


cams = {"all": camera("Cam all", Vector((-6, -40, 22)), Vector((0, 8, -1)), 35)}
for case in CASES:
    key, land_z = case["key"], case["z"]
    cx, cy = POS[key]
    t = Vector((cx, cy, land_z + 0.7))
    if case["surface"] == "pit":                       # from above the rim, looking down into the pit
        cams[f"34_{key}"] = camera(f"Cam 3/4 {key}", t + Vector((-1.6, -2.3, 11.5)), t, 32)
        cams[f"side_{key}"] = camera(f"Cam side {key}", t + Vector((2.4, 0, 11.5)), t, 32)
        cams[f"back_{key}"] = camera(f"Cam back {key}", t + Vector((0.3, 2.4, 11.5)), t, 32)
    else:
        cams[f"34_{key}"] = camera(f"Cam 3/4 {key}", t + Vector((-3.6, -5.2, 2.6)), t)
        cams[f"side_{key}"] = camera(f"Cam side {key}", t + Vector((6.0, 0, 1.4)), t)
        cams[f"back_{key}"] = camera(f"Cam back {key}", t + Vector((0.8, 6.0, 2.2)), t)
    cams[f"top_{key}"] = camera(f"Cam above {key}", t + Vector((0, -3.0, 8.5)), t)
scene.camera = cams["34_L1"]
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

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for case in CASES:
        scene.camera = cams[f"34_{case['key']}"]
        scene.frame_set(timing(case)[0] + 8)
        scene.render.filepath = os.path.join(rdir, f"83_{case['key']}_{case['surface']}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["34_L1"]
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
