# Pass 87: super jump ribbon, round 3 (J: "all of these still trail very long when it should really never trail
# more than a block or two"). The ribbon is now capped by length, not time: a piece lives only as long as the
# ring takes to move the cap distance at that moment's speed (and never over 2 ticks), so the streak behind the
# fist is the same short length fast or slow, and it tapers to nothing at its tail. It now trails on the way
# down as well as up (J: "it also doesn't trail when coming down").
#   R1  1 block   R2  1.5 blocks   R3  2 blocks
# Also (J): the crater's blocks crumble and drop into it instead of flying up, to match his block-drop mod.
# Builds LanternLive\\super_jump_ribbon2.blend.
import json, math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

R = math.radians
OUT = os.path.join(FOLDER, "super_jump_ribbon2.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Super Jump Ribbon 2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Super Jump Ribbon 2")
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

WALLS = {"W1": dict(t=0.5, h=0.5), "W2": dict(t=3 / 16, h=0.5), "W3": dict(t=3 / 32, h=0.375)}
LINING = 3 / 16                                          # the plates lining the crater: trapdoor thin
CASES = [
    dict(key="R1", surface="grass", E="E1", F="F1", D="D1a", W="W2", full=True, trail="ribbon", cap=1.0, note="ribbon, 1 block"),
    dict(key="R2", surface="grass", E="E1", F="F1", D="D1a", W="W2", full=True, trail="ribbon", cap=1.5, note="ribbon, 1.5 blocks"),
    dict(key="R3", surface="grass", E="E1", F="F1", D="D1a", W="W2", full=True, trail="ribbon", cap=2.0, note="ribbon, 2 blocks"),
]
SPACING = 16.0
POS = {}
for i, c in enumerate(CASES):
    POS[c["key"]] = ((i - 1) * SPACING, 0.0)
FALL = {"L5": 26}                                        # ticks of falling in view
HOLD = {"L5": 30}                                        # landing hold (0.8 s; deeper: 1.2 s)
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
    return {"stone": [2.2, 1.1], "sand": [3.6, 2.3], "water": [], "pit": [4.6, 3.8, 2.8, 1.6]}.get(
        surface, [3.0, 1.7])


def build_ground(case):
    """The blocks, minus the pit or pool that was there and the crater the landing blasts out. Returns the
    blasted blocks (to throw) and each column's (surface before the crater, layers blasted out)."""
    key, surface = case["key"], case["surface"]
    cx, cy = POS[key]
    radii = crater_radii(key, surface)
    pit_r, pit_depth = (5.6, 6) if surface == "pit" else (0, 0)
    pool_r, pool_depth = (6.2, 2) if surface == "water" else (0, 0)
    bm = bmesh.new(); mats = []
    flying, cols = [], {}
    H = 7
    for i in range(-H, H):
        for j in range(-H, H):
            x, y = cx + i + 0.5, cy + j + 0.5
            r = math.hypot(i + 0.5, j + 0.5)
            depth = 5 if r < 6.5 else 1
            if surface == "pit":
                depth = 12 if r < 6.8 else 1
            top, n = 0.0, 0
            if r < pit_r:
                top = -float(pit_depth)
            if r < pool_r:
                top = -float(pool_depth)
            for k in range(depth):
                ztop = -k
                if r < pit_r and k < pit_depth:
                    continue                                   # the pit was already there
                if r < pool_r and k < pool_depth:
                    continue                                   # the pool
                kk = k - pit_depth
                mk = block_mats(surface if surface != "pit" else "grass", k)
                if 0 <= kk < len(radii) and r < radii[kk]:
                    flying.append((x, y, ztop, mk[0], mk[1], r))
                    n += 1
                    continue
                add_block(bm, mats, x, y, ztop, *mk)
            cols[(i, j)] = (top, n)
    me = bpy.data.meshes.new(f"sj ground {key}")
    bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    link(bpy.data.objects.new(f"SJ ground {key}", me))
    if surface == "water":                                 # the construct pad on the water: lined, no crater
        for (i, j), (top, n) in list(cols.items()):
            if math.hypot(i + 0.5, j + 0.5) < 2.7:
                cols[(i, j)] = (-0.12, 0)
    return flying, cols


def keyframes(o, path, fv):
    for f, v in fv:
        setattr(o, path, v)
        o.keyframe_insert(path, frame=f)


def throw(name, mesh, start, ang, t0, size, vout, vup, life, spin=True, base_z=0.0, hold=0.4):
    o = link(bpy.data.objects.new(name, mesh))
    keyframes(o, "scale", [(t0 - 1, (0, 0, 0)), (t0, (size,) * 3), (t0 + int(life * hold), (size * 0.8,) * 3),
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
def construct_material(name, glow=1.0, snap=1.5, tail=None, clean=False):
    """Hard-light jade: a glassy jade surface with a soft inner glow. Each piece switches on at its own t0 (a brief
    bright edge as it forms), holds with a slow shimmer, then dissolves at its own random t1 with a small pop."""
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
    on = op("MULTIPLY", op("MULTIPLY", op("SUBTRACT", f, at["t0"]), snap, True),
            op("MULTIPLY", op("SUBTRACT", at["t1"], f), 1.0, True) if tail is None else
            op("MULTIPLY", op("DIVIDE", op("SUBTRACT", at["t1"], f), op("MAXIMUM", op("SUBTRACT", at["t1"], at["t0"]), 0.01)), tail, True))
    front = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", op("SUBTRACT", f, at["t0"]), 1.6), 2.0)))
    pop = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", op("SUBTRACT", f, at["t1"]), 1.2), 2.0)))
    shim = op("ADD", 0.8, op("MULTIPLY", 0.2, op("SINE", op("ADD", op("MULTIPLY", f, 0.25), op("MULTIPLY", at["seed"], 30.0)))))
    strength = op("MULTIPLY", op("ADD", op("MULTIPLY", on, op("ADD", op("MULTIPLY", shim, 0.9), op("MULTIPLY", front, 1.6))),
                                 op("MULTIPLY", pop, 1.4)), glow)
    alpha = op("ADD", op("MULTIPLY", on, 0.7), op("MULTIPLY", pop, 0.4), True)
    if clean:                                              # a trail: only what exists right now, no flashes
        strength = op("MULTIPLY", on, 1.4 * glow)
        alpha = op("MULTIPLY", on, 0.85)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.3, (0.02, 0.2, 0.1, 1)
    e[1].position, e[1].color = 0.75, (0.07, 0.42, 0.24, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    p = N.new("ShaderNodeBsdfPrincipled")
    L.new(ramp.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.22
    p.inputs["Coat Weight"].default_value = 0.6
    p.inputs["Emission Color"].default_value = (0.06, 0.5, 0.28, 1)
    L.new(strength, p.inputs["Emission Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(alpha, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(p.outputs[0], mx.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


class Pieces:
    """Thin construct boxes in one mesh, each with its own appear (t0) and dissolve (t1) times."""
    def __init__(self):
        self.bm = bmesh.new(); self.t0, self.t1, self.seed = [], [], []

    def box(self, x0, x1, y0, y1, z0, z1, t0, t1):
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in res["verts"]:
            v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 if v.co.z < 0 else z1))
        sd = rng.random()
        self.t0 += [t0] * 8; self.t1 += [t1] * 8; self.seed += [sd] * 8

    def object(self, name, material, loc):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        for nm, vals in (("t0", self.t0), ("t1", self.t1), ("seed", self.seed)):
            a = me.attributes.new(nm, "FLOAT", "POINT")
            a.data.foreach_set("value", np.asarray(vals, np.float32))
        me.materials.append(material)
        o = link(bpy.data.objects.new(name, me))
        o.location = loc
        return o


NB = ((1, 0), (-1, 0), (0, 1), (0, -1))


def edge_plate(P, i, j, di, dj, t, z0, z1, t0, t1, inset=0.03):
    """A plate of thickness t standing on the edge of cell (i, j) that faces (di, dj), inside the cell."""
    if di:
        x = i + (1 if di > 0 else 0)
        xa, xb = (x - t, x) if di > 0 else (x, x + t)
        P.box(xa, xb, j + inset, j + 1 - inset, z0, z1, t0, t1)
    else:
        y = j + (1 if dj > 0 else 0)
        ya, yb = (y - t, y) if dj > 0 else (y, y + t)
        P.box(i + inset, i + 1 - inset, ya, yb, z0, z1, t0, t1)


def build_construct(case, cols):
    """The construct the landing forms, in the middle of the crater: a small pad of jade construct where you land
    (thin plates on the crater floor, following its steps), and a low wall, slab-low and trapdoor thin, along
    the pad's edge around you. On a deep landing the pad is wider and its edge walls rise high around you for
    protection. It all dissolves piece by piece after the stand-up, leaving the crater."""
    key = case["key"]
    t_land, t_up, _ = timing(case)
    cx, cy = POS[key]
    deep = case.get("deep")
    W = WALLS[case["W"]]
    PAD = 2.3 if deep else (2.2 if case["surface"] == "water" else 1.6)
    pad_p, walls, guard = Pieces(), Pieces(), Pieces()
    surf = {k: top - n for k, (top, n) in cols.items()}
    pad = {k for k, (top, n) in cols.items() if math.hypot(k[0] + 0.5, k[1] + 0.5) < PAD}
    for (i, j) in pad:
        s_ = surf[(i, j)]
        r = math.hypot(i + 0.5, j + 0.5)
        t0 = t_land + r / 0.75 * 0.6 + rng.random() * 0.5
        t1 = t_up + 4 + rng.random() * (16 if deep else 12)
        pad_p.box(i + 0.02, i + 0.98, j + 0.02, j + 0.98, s_, s_ + LINING, t0, t1)
        for di, dj in NB:
            nk = (i + di, j + dj)
            if nk in pad:
                ns = surf[nk]
                if ns > s_ + 0.01:                         # a step inside the pad: lined up to the next level
                    edge_plate(pad_p, i, j, di, dj, LINING, s_ + LINING, ns + LINING, t0, t1)
                continue
            base = s_ + LINING                             # the pad's edge: the small wall around you
            if deep:
                edge_plate(guard, i, j, di, dj, 3 / 16, base, base + 2.6, t_land + 1, t_up + 6 + rng.random() * 14)
            else:
                edge_plate(walls, i, j, di, dj, W["t"], base, base + W["h"], t_land + 1, t1 + 2)
    pad_p.object(f"SJ construct pad {key}", construct_material(f"sj pad {key}", 0.6), (cx, cy, 0))
    if walls.t0:
        wo = walls.object(f"SJ construct wall {key}", construct_material(f"sj wall {key}", 0.7), (cx, cy, 0))
        keyframes(wo, "location", [(t_land, (cx, cy, -W["h"] - 0.05)), (t_land + 4, (cx, cy, 0))])
    else:
        walls.bm.free()
    if guard.t0:                                           # protective walls rising high around the player
        go = guard.object(f"SJ construct guard {key}", construct_material(f"sj guard {key}", 0.7), (cx, cy, 0))
        keyframes(go, "location", [(t_land, (cx, cy, -2.7)), (t_land + 7, (cx, cy, 0.12)), (t_land + 9, (cx, cy, 0))])
    else:
        guard.bm.free()
    centre = [surf[k] for k in ((0, 0), (-1, 0), (0, -1), (-1, -1)) if k in surf]
    return (min(centre) if centre else 0.0) + LINING


def build_air(case, fist, t_land):
    """The trail off the ring fist and the glow round it, sampled from the animated fist every half tick."""
    key = case["key"]
    pts = []
    for f4 in range(T_GO * 4, t_land * 4):
        scene.frame_set(f4 // 4, subframe=(f4 % 4) * 0.25)
        pts.append((f4 / 4, fist.matrix_world.translation.copy()))
    rib, motes = Pieces(), Pieces()
    want_rib = case["trail"] in ("ribbon", "both")
    want_mote = case["trail"] in ("motes", "both")
    for k in range(1, len(pts)):
        f, p = pts[k]
        q = pts[k - 1][1]
        rising = f < T_APEX
        if want_rib and (rising or case["trail"] == "ribbon"):      # J: it trails coming down too
            seg = max(1, int((p - q).length / 0.03))       # pieces close enough to read as one streak
            speed = max(1e-3, (p - q).length / 0.25)        # blocks a tick right now
            life = min(2.0, case.get("cap", 1.5) / speed)
            for n in range(seg):
                u = n / seg
                c = q.lerp(p, u)
                w = 0.032
                born = f - 0.25 * (1 - u)                  # exactly when the ring passed this point
                rib.box(c.x - w, c.x + w, c.y - w, c.y + w, c.z - w, c.z + w, born, born + life)
        if want_mote and (case["trail"] == "motes" or not rising) and k % 2 == 0:
            for _ in range(2):
                c = p + Vector(rng.normal(0, 0.08, 3))
                w = 0.03 + 0.02 * rng.random()
                motes.box(c.x - w, c.x + w, c.y - w, c.y + w, c.z - w, c.z + w, f, f + 10 + rng.random() * 6)
    for pc, nm, glow in ((rib, "ribbon", 1.6), (motes, "motes", 1.8)):
        if pc.t0:
            pc.object(f"SJ trail {nm} {key}", construct_material(f"sj {nm} {key}", glow, snap=20.0 if nm == "ribbon" else 1.5, tail=1.0 if nm == "ribbon" else None, clean=nm == "ribbon"), (0, 0, 0))
        else:
            pc.bm.free()
    # a soft glow round the fist that grows and pulses faster as the ground nears (sizes in the arm's model px)
    gm, gs, ga = emissive(f"sj fist glow {key}", (0.12, 0.85, 0.42), 1.0, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=16, ring_count=8)
    g = bpy.context.active_object
    for c in list(g.users_collection):
        c.objects.unlink(g)
    col.objects.link(g); g.name = f"SJ fist glow {key}"; g.data.materials.append(gm)
    g.parent = fist; g.location = (0, 0, 0)
    sc_keys, a_keys = [(T_APEX - 1, 0.0)], [(T_APEX - 1, 0.0)]
    f, period = float(T_APEX), 8.0
    while f < t_land - 1:
        u = (f - T_APEX) / (t_land - T_APEX)
        size = 1.5 + 3.5 * u * u
        sc_keys += [(f, size), (f + period / 2, size * 1.3)]
        a_keys += [(f, 0.1 + 0.3 * u), (f + period / 2, 0.18 + 0.45 * u)]
        period = max(2.0, 8.0 - 6.0 * u)
        f += period
    sc_keys += [(t_land, 6.0), (t_land + 4, 0.0)]
    a_keys += [(t_land, 0.85), (t_land + 4, 0.0)]
    for fr, v in sc_keys:
        g.scale = (v, v, v); g.keyframe_insert("scale", frame=round(fr))
    keyed_socket(ga, [(round(fr), v) for fr, v in a_keys])
    keyed_socket(gs, [(round(fr), 1.5 + 3 * v) for fr, v in a_keys])


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
mote_m, _, _ = emissive("sj mote", (0.12, 0.62, 0.36), 1.8)
cubes = {k: cube_mesh(f"sj chunk {k}", m) for k, m in BLOCK.items()}
spark_c, drop_c, mote_c = cube_mesh("sj spark", spark_m), cube_mesh("sj droplet", drop_m), cube_mesh("sj mote", mote_m)

for case in CASES:
    key, surface, epose, note = case["key"], case["surface"], case["E"], case["note"]
    t_land, t_up, t_idle = timing(case)
    cx, cy = POS[key]
    flying, cols = build_ground(case)
    land_z = build_construct(case, cols)
    case["z"] = land_z
    base = Vector((cx, cy, land_z))
    # the blocks the landing blasts out, thrown up and outward
    # J: the blocks crumble and drop instead of flying up (his block-physics mod drops broken blocks to the
    # ground): each blasted block breaks into a few chunks that slump outward a little, fall into the crater
    # and settle on its floor, then crumble away.
    for x, y, ztop, top, side, r in flying:
        mesh = cubes[{BLOCK["grass_top"]: "dirt", BLOCK["dirt"]: "dirt", BLOCK["stone"]: "stone",
                      BLOCK["sand"]: "sand", BLOCK["sandstone"]: "sandstone"}[side]]
        ci, cj = math.floor(x - cx), math.floor(y - cy)
        top_c, n_c = cols.get((ci, cj), (0.0, 0))
        floor_z = top_c - n_c
        for _ in range(3):
            st = Vector((x + rng.normal(0, 0.2), y + rng.normal(0, 0.2), ztop - 0.5 + rng.normal(0, 0.15)))
            ang = math.atan2(y - cy, x - cx) + rng.normal(0, 0.6)
            sz = 0.32 + 0.12 * rng.random()
            throw(f"SJ block {key}", mesh, st, ang, t_land + int(r * 0.4) + int(rng.random() * 2), sz,
                  0.01 + 0.025 * rng.random(), 0.02 + 0.05 * rng.random(), 26, base_z=floor_z + sz / 2, hold=0.75)
    # the finer debris for each surface
    if surface in ("grass", "pit"):
        for _ in range(26):
            throw(f"SJ dirt {key}", cubes["dirt"], base + Vector((0, 0, 0.05)), rng.random() * 6.283, t_land,
                  0.08 + 0.06 * rng.random(), 0.08 + 0.1 * rng.random(), 0.08 + 0.1 * rng.random(), 14, base_z=base.z)
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
        rm_, rs, ra = emissive(f"sj ripple {key}", (0.8, 0.95, 1.0), 0.6)
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=64, minor_segments=5)
        rp = bpy.context.active_object
        for c in list(rp.users_collection):
            c.objects.unlink(rp)
        col.objects.link(rp); rp.name = f"SJ ripple {key}"; rp.data.materials.append(rm_)
        rp.location = (cx, cy, -0.18)
        keyframes(rp, "scale", [(t_land - 1, (0.1, 0.1, 1)), (t_land + 22, (5.0, 5.0, 1))])
        keyed_socket(ra, [(t_land - 1, 0), (t_land, 0.8), (t_land + 22, 0)])
    # motes rising from the barrier
    for _ in range(8):
        throw(f"SJ mote {key}", mote_c, base + Vector((rng.normal(0, 1.2), rng.normal(0, 1.2), 0.1)),
              rng.random() * 6.283, t_land + 2 + int(rng.random() * 8), 0.05, 0.01, 0.07 + 0.04 * rng.random(), 18,
              spin=False, base_z=-1)

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
    # the ring builds up as the ground nears: low at the apex, climbing steeply over the last third of the fall
    fall = [(T_APEX + round((t_land - T_APEX) * u), 20 + 150 * u ** 2.2) for u in (0, 0.25, 0.5, 0.7, 0.85, 0.95)]
    flare = [(0, 0), (T_CROUCH, 0), (T_FULL, 40), (T_GO + 1, 420), (T_GO + 6, 30)] + fall + \
            [(t_land - 1, 190), (t_land, 320), (t_land + 8, 40), (t_up, 25), (t_idle, 0), (T_END, 0)]
    keyed(li, "energy", flare)
    keyed_socket(gem_s, [(f, 3 + v / 12) for f, v in flare])
    build_air(case, lo, t_land)
    # label behind the player
    cu = bpy.data.curves.new(f"sj label {key}", "FONT")
    cu.body = f"{key}  {surface.upper()}  {case['D']} {epose} {case['W']}\n{note}"
    cu.size = 0.3; cu.align_x = "CENTER"
    lb = link(bpy.data.objects.new(f"SJ label {key}", cu))
    lb.location = Vector((cx, cy + 6.2, 3.2)); lb.rotation_euler = (R(90), 0, 0)
    lm, _, _ = emissive(f"sj label {key}", (0.85, 1, 0.9), 1.5)
    cu.materials.append(lm)

# ---- the poses for the game ------------------------------------------------------------------------------
dump = {}
for k in ["idle"]:
    p, d = SOLVED[k]
    dump[k] = {"note": POSES.get(k, {}).get("note", "standing"), "hip_drop_px": round(d, 2),
               "torso_sink_px": round(SINK.get(k, 0.0), 2),
               "parts": {part: {"rot": [round(float(v), 3) for v in p[part][0]],
                                "offset_px": [round(float(v), 2) for v in p[part][1]]} for part in PARTS}}
with open(os.path.join(FOLDER, "super_jump_ribbon2_poses.json"), "w") as fh:
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
        cams[f"34_{key}"] = camera(f"Cam 3/4 {key}", t + Vector((-3.4, -5.0, 4.2)), t)
        cams[f"side_{key}"] = camera(f"Cam side {key}", t + Vector((6.0, 0, 1.4)), t)
        cams[f"back_{key}"] = camera(f"Cam back {key}", t + Vector((0.8, 5.6, 3.8)), t)
    cams[f"top_{key}"] = camera(f"Cam above {key}", t + Vector((0, -3.0, 8.5)), t)
# the take cameras ride along with their jump (height only), so the player stays in frame
for case in CASES:
    key = case["key"]
    fol = link(bpy.data.objects.new(f"SJ follow {key}", None))
    for f in range(T_END + 1):
        fol.location = (0, 0, pose_at(f, case)[1])
        fol.keyframe_insert("location", frame=f)
    for nm in (f"34_{key}", f"side_{key}", f"back_{key}"):
        if nm in cams:
            cams[nm].parent = fol
scene.camera = cams["34_R1"]
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
        scene.render.filepath = os.path.join(rdir, f"87_{case['key']}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["34_R1"]
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
