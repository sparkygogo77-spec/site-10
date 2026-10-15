# Pass 403: double-jump take-off, round 2 (Blender designer chat, 2026-10-14). From J's notes on 402:
# "the snap to hover is great, the spring may be better on the way up but it should slow down no higher than snap goes,
# make it faster for both though but more for the speed spring goes up, Running dart seems to be the most accurate,
# the arm should be angled about where the players arm is a little more accurately than a thrown back and up arm".
# Also: "is the animation gonna drag me or allow me to fly once im flying?" -> it never drags: the take-off owns 3 ticks
# standing / 6 ticks running, then it is your own flight; every take here steers after the take-off to show it.
#   S1   snap (KEEP), faster: 3.2 blocks in 3 ticks (was 4).
#   S2a  spring, faster: shoots up (90% in 2 ticks) and eases into 3.2, never above the snap height.
#   S2b  spring, fastest: 90% in 1.5 ticks, same no-overshoot settle.
#   R3   dart (J's pick), flat at 5 in 6 ticks, with the free arm where a player's arm sits instead of thrown back:
#        A1 along the side (parallel to the body), A2 a little forward of the body line, A3 forward and slightly out.
#        R3A2 090 shows the same running right of your look.
#   L1-L3 soft landing (J: R1 played backwards "was not bad if i wanted to double tap space soft land"): flying flat
#        at 5 blocks, double tap space, arc down to a running touchdown with a small construct cushion, run out, stop.
#        L1 = R1 exactly reversed, L2 softer (eased into the ground), L3 the dart reversed (straight ramp down).
# Cameras "Cam S1".."Cam R3A2 090", "Cam <take> close" (running/landing: side, following, close), (over the right shoulder, following), "Cam <take> side", "Cam all".
# Writes LanternLive\takeoff_small2_poses.json and builds LanternLive\takeoff_small2.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "takeoff_small2.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Takeoff Small 2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Takeoff Small 2")
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

def driver_frame(sock, scale):
    fc = sock.driver_add("default_value")
    fc.driver.type = "SCRIPTED"; fc.driver.expression = f"frame*{scale}"


def construct_nodes(m, nodes, links):
    """Dark-jade fragments (R2 K1 family), fixed texel density in world space, gliding slowly (never static)."""
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    links.new(tc.outputs["Object"] if False else tc.outputs["Generated"], mp.inputs[0])
    geo = nodes.new("ShaderNodeNewGeometry")
    vor = nodes.new("ShaderNodeTexVoronoi"); vor.voronoi_dimensions = "4D"
    vor.inputs["Scale"].default_value = 4.0
    links.new(geo.outputs["Position"], vor.inputs["Vector"])
    wv = nodes.new("ShaderNodeValue"); driver_frame(wv.outputs[0], 0.011); links.new(wv.outputs[0], vor.inputs["W"])
    edge = nodes.new("ShaderNodeTexVoronoi"); edge.voronoi_dimensions = "4D"; edge.feature = "DISTANCE_TO_EDGE"
    edge.inputs["Scale"].default_value = 4.0
    links.new(geo.outputs["Position"], edge.inputs["Vector"]); links.new(wv.outputs[0], edge.inputs["W"])
    ramp = nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    stops = [(0.0, (0.002, 0.025, 0.011)), (0.3, (0.006, 0.085, 0.03)), (0.55, (0.018, 0.22, 0.075)),
             (0.8, (0.05, 0.42, 0.14)), (1.0, (0.12, 0.62, 0.22))]
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    els[1].position, els[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, c in stops[1:-1]:
        e = els.new(pos); e.color = (*c, 1)
    ramp.color_ramp.interpolation = "EASE"
    sep = nodes.new("ShaderNodeSeparateColor")
    links.new(vor.outputs["Color"], sep.inputs[0]); links.new(sep.outputs[1], ramp.inputs[0])
    # dark jade lines between fragments (J dislikes white lines)
    mr = nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.08
    mr.inputs[3].default_value = 0.15; mr.inputs[4].default_value = 1.0
    links.new(edge.outputs["Distance"], mr.inputs[0])
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    links.new(ramp.outputs["Color"], mix.inputs[6]); links.new(mr.outputs[0], mix.inputs[7])
    return mix.outputs[2]


def obj_attr(nodes, name):
    a = nodes.new("ShaderNodeAttribute"); a.attribute_type = "OBJECT"; a.attribute_name = name
    return a.outputs["Fac"]


def fx_mat(name="PS construct fx", strength=2.2):
    """Construct pixels, pad, blade, pulse: see-through (at most 95%), alpha from the object's ["fade"]."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    out = N.get("Material Output"); N.remove(N.get("Principled BSDF"))
    con = construct_nodes(m, N, Lk)
    em = N.new("ShaderNodeEmission"); Lk.new(con, em.inputs["Color"]); em.inputs["Strength"].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent")
    fa = obj_attr(N, "fade")
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.95
    Lk.new(fa, mul.inputs[0])
    ms = N.new("ShaderNodeMixShader"); Lk.new(mul.outputs[0], ms.inputs[0])
    Lk.new(tr.outputs[0], ms.inputs[1]); Lk.new(em.outputs[0], ms.inputs[2])
    Lk.new(ms.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def cube_mesh(name, size=1.0):
    h = size / 2
    verts = [(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    return me


def key_prop(o, name, val, f):
    o[name] = float(val); o.keyframe_insert(f'["{name}"]', frame=f)


def key_obj(o, f, loc=None, sc=None, rotv=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if sc is not None:
        o.scale = (sc, sc, sc) if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)
    if rotv is not None:
        o.rotation_euler = rotv; o.keyframe_insert("rotation_euler", frame=f)




# ================================================================== pass 402
T_END = 100
FLY = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-2.95, 0, 0.02), free=(0.35, 0, -0.12),
           ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
STAND = dict(body=(0.02, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.12), free=(0.05, 0, -0.1),
             ringleg=(0.03, 0, 0.03), ringknee=0.08, freeleg=(0.03, 0, -0.03), freeknee=0.08)
JUMP = dict(body=(0.1, 0, 0), head=(-0.05, 0, 0), ring=(-0.5, 0, 0.25), free=(-0.3, 0, -0.3),
            ringleg=(-0.55, 0, 0.05), ringknee=1.1, freeleg=(-0.2, 0, -0.05), freeknee=0.6, grounded=False)
TUCK = dict(body=(0.15, 0, 0), head=(-0.1, 0, 0), ring=(-1.2, 0, 0.3), free=(0.3, 0, -0.5),
            ringleg=(-0.9, 0, 0.06), ringknee=1.7, freeleg=(-0.75, 0, -0.06), freeknee=1.6, grounded=False)
HERO = dict(body=(0.02, 0, 0), head=(-0.1, 0, 0), ring=(-1.55, 0, 0.15), free=(0.25, 0, -0.45),
            ringleg=(0.12, 0, 0.04), ringknee=0.35, freeleg=(-0.05, 0, -0.06), freeknee=0.15, grounded=False)
SPRING = dict(body=(0.75, 0, 0), head=(-0.6, 0, 0), ring=(-2.6, 0, 0.05), free=(0.9, 0, -0.15),
              ringleg=(0.6, 0, 0.04), ringknee=0.5, freeleg=(0.95, 0, -0.04), freeknee=1.0, grounded=False)
DART = dict(body=(1.25, 0, 0), head=(-1.0, 0, 0), ring=(-2.9, 0, 0.0), free=(0.9, 0, -0.1),
            ringleg=(1.15, 0, 0.03), ringknee=0.2, freeleg=(1.05, 0, -0.03), freeknee=0.35, grounded=False)


def legs(ph, amp=0.85, lean=0.0):
    thigh = 0.15 - amp * math.sin(ph) - lean * 0.5
    knee = 0.12 + 1.45 * ((1 + math.cos(ph + 0.35)) / 2) ** 2
    return thigh, knee


def run_pose(t):
    ph = 2 * math.pi * t / 12; lean = 0.26
    tr, kr = legs(ph, 0.85, lean); tf, kf = legs(ph + math.pi, 0.85, lean); swing = math.sin(ph)
    return dict(body=(lean + 0.03 * math.sin(2 * ph), 0.07 * swing, 0.0), head=(-lean * 0.8, 0, 0.0),
                ringleg=(tr, 0, 0.02), ringknee=kr, freeleg=(tf, 0, -0.02), freeknee=kf,
                ring=(-1.42 + 0.06 * math.sin(2 * ph), 0.06, 0.05), free=(0.15 - 0.95 * swing, 0, -0.08))


def vanilla_jump(k):
    """Minecraft jump height after k ticks (vy 0.42, gravity 0.08, drag 0.98)."""
    z, vz = 0.0, 0.42
    for _ in range(k):
        z += vz; vz = (vz - 0.08) * 0.98
    return max(0.0, z)


def ease_out(w):
    return 1 - (1 - w) ** 3


def hover_rise(take, k):
    """Share of the climb from the jump-2 height to 3.2 done after k ticks. Never above 1 (no overshoot)."""
    if take == "S1":
        return ease_out(min(1, k / 3)), None
    a = 2.6 if take == "S2a" else 3.5           # critically damped: faster than the snap off the jump, never above it
    return 1 - (1 + a * k) * math.exp(-a * k), None


T_STAND0, J2_STAND = 8, 4      # standing: first jump at tick 8, second 4 ticks into it
T_RUN, J2_RUN = 16, 3          # running: jump at tick 16, second 3 ticks into it
ARC = 6
HOVER_Z, FLAT_Z = 3.2, 5.0
STANDING = ["S1", "S2a", "S2b"]
RUNNING = [("R3A1", 0), ("R3A2", 0), ("R3A3", 0), ("R3A2", 90), ("L1", 0), ("L2", 0), ("L3", 0)]
NAMES = {"S1": "standing, snap to hover (faster)", "S2a": "standing, fast spring, no overshoot",
         "S2b": "standing, fastest spring, no overshoot", "R3A1": "running dart, arm along the side",
         "R3A2": "running dart, arm a little forward", "R3A3": "running dart, arm forward and out",
         "L1": "soft landing, R1 reversed", "L2": "soft landing, eased", "L3": "soft landing, dart reversed"}
ARM = {"A1": (0.0, -0.06), "A2": (-0.3, -0.08), "A3": (-0.45, -0.32)}   # free arm = body pitch + dx, splay z
TURN0, TURN_T, TURN = ARC + 10, 14, 35.0     # after the take-off: a 35 degree turn right, to show it's your flight


def sim_standing(take):
    out = []; y = 0.0
    t1 = T_STAND0; t2 = T_STAND0 + J2_STAND
    z2 = vanilla_jump(J2_STAND)
    for t in range(T_END + 1):
        ev = None
        if t < t1:
            p = dict(STAND); z = 0.0; glow = 3.0
        elif t < t2:
            k = t - t1; z = vanilla_jump(k)
            p = mixp(STAND, JUMP, smooth(min(1, k / 2))); glow = 4.0
        else:
            k = t - t2
            if k == 0:
                ev = "burst"
            w, _ = hover_rise(take, k)
            z = z2 + (HOVER_Z - z2) * w
            if k < 3:
                p = mixp(JUMP, TUCK, smooth(k / 2)); glow = 18 - 2 * k
            else:
                p = mixp(TUCK, HERO, smooth(min(1, (k - 3) / 6))); glow = 9.0
            if k >= 12:
                z += 0.07 * math.sin(2 * math.pi * (k - 12) / 30)          # gentle hover bob
            # free flight: 34 ticks after the puff he simply flies off forward (no locked animation)
            kf = k - 22
            if kf >= 0:
                wf = smooth(min(1, kf / 6))
                p = mixp(p, FLY, wf); glow = 9 + 3 * wf
                y -= 0.02 + 0.55 * wf * min(1, kf / 10)
                z += 0.6 * wf
        p["grounded"] = t < t1
        out.append((p, 0.0, y, z, glow, ev))
    return out


def sim_running(take, theta):
    out = []; d = 0.0; v = 0.28; theta_t = theta
    t2 = T_RUN + J2_RUN
    for t in range(T_END + 1):
        ev = None
        if t < T_RUN:
            p = run_pose(t); z = 0.0; v = 0.28; glow = 3 + 3 * t / T_RUN
        elif t < t2:
            k = t - T_RUN; z = vanilla_jump(k); v = 0.3
            p = mixp(run_pose(t), JUMP, smooth(min(1, k / 2))); glow = 6.0
        else:
            k = t - t2
            if k == 0:
                ev = "burst"
            z0 = vanilla_jump(J2_RUN)
            w = min(1.0, k / ARC)
            if take == "R1":
                z = z0 + (FLAT_Z - z0) * ease_out(w)
                p = mixp(JUMP, SPRING, smooth(min(1, k / 2))) if k < 2 else mixp(SPRING, FLY, smooth(min(1, (k - 2) / 4)))
            elif take == "R2":
                z = z0 + (FLAT_Z - z0) * ease_out(w) + 0.9 * math.sin(math.pi * w) * (1 if k <= ARC else 0)
                p = mixp(JUMP, SPRING, smooth(min(1, k / 3))) if k < 3 else mixp(SPRING, FLY, smooth(min(1, (k - 3) / 3)))
            else:
                z = z0 + (FLAT_Z - z0) * w
                p = mixp(JUMP, DART, smooth(min(1, k / 2))) if k < ARC else mixp(DART, FLY, smooth(min(1, (k - ARC) / 4)))
                dx, sz = ARM[take[2:4]]
                aw = smooth(min(1, k / 2))
                f0 = p["free"]; tgt = (p["body"][0] + dx, 0.0, sz)
                p["free"] = tuple(f0[i] + (tgt[i] - f0[i]) * aw for i in range(3))
                if k >= TURN0:
                    theta_t = theta + TURN * smooth(min(1, (k - TURN0) / TURN_T))
            # super fast: 0.3 -> 0.95 a tick through the arc, easing to a 0.7 cruise after
            v = 0.3 + 0.65 * smooth(w) if k <= ARC else 0.95 - 0.25 * smooth(min(1, (k - ARC) / 30))
            glow = 18 if k < 3 else (13 if k <= ARC else 9)
        d += v
        p["grounded"] = t < T_RUN
        out.append((p, theta_t, v, z, glow, ev))
    return out


def sim_land(take):
    """Double-tap-space soft landing: flat flight at 5 blocks, then the take-off arc in reverse, touchdown, run-out."""
    T_FLY = 16; D = {"L1": 6, "L2": 8, "L3": 6}[take]
    z0 = vanilla_jump(J2_RUN)
    out = []
    for t in range(T_END + 1):
        ev = None; grounded = False
        if t < T_FLY:
            p = dict(FLY); z = FLAT_Z; v = 0.8; glow = 9.0
        elif t < T_FLY + D:
            k = t - T_FLY; w = k / D; kr = (1 - w) * ARC          # the matching take-off tick, played backwards
            if take == "L1":
                z = z0 + (FLAT_Z - z0) * ease_out(1 - w)
            elif take == "L2":
                z = z0 + (FLAT_Z - z0) * (1 - smooth(w))
            else:
                z = z0 + (FLAT_Z - z0) * (1 - w)
            if take == "L3":
                p = mixp(JUMP, DART, smooth(min(1, kr / 2)))
            else:
                p = mixp(JUMP, SPRING, smooth(min(1, kr / 2))) if kr < 2 else mixp(SPRING, FLY, smooth(min(1, (kr - 2) / 4)))
            v = 0.3 + 0.5 * (1 - smooth(w)); glow = 12.0
        elif t < T_FLY + D + J2_RUN:
            j = t - (T_FLY + D); kj = J2_RUN - j                    # the first jump, backwards, onto the feet
            z = vanilla_jump(kj); v = 0.3
            p = mixp(run_pose(t), JUMP, smooth(min(1, kj / 2))); glow = 9.0
        else:
            k = t - (T_FLY + D + J2_RUN); z = 0.0; grounded = True
            if k == 0:
                ev = "burst"
            if k < 12:
                p = run_pose(t); v = 0.3 - 0.02 * k; glow = 8 - 0.3 * k
            else:
                w = smooth(min(1, (k - 12) / 8))
                p = mixp(run_pose(t), STAND, w); v = max(0.0, 0.06 * (1 - w)); glow = 4.0
        p["grounded"] = grounded
        out.append((p, 0.0, v, z, glow, ev))
    return out


# --------------------------------------------------------------- construct helpers, glow
FX = fx_mat("TS construct fx", 2.4)
PIX = cube_mesh("TS pixel"); PIX.materials.append(FX)
LABEL = mat("TS label", (0.85, 1.0, 0.9), emit=2.0)
LOOKM = mat("TS look arrow", (0.9, 0.95, 1.0), emit=1.5)
RUNM = mat("TS run arrow", (0.15, 1.0, 0.35), emit=2.5)
try:
    tree = bpy.data.node_groups.new("TS Glow", "CompositorNodeTree")
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


def burst_ring(tag, center, t0, rng, r1=2.6, n=28, trail=(0.0, 0.0)):
    """The second-jump puff: a flat construct ring blooming out under the feet, plus pixels flung outward."""
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.06, major_segments=48, minor_segments=6)
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = f"{tag} ring"; o.data.materials.append(FX); o["fade"] = 0.0
    key_obj(o, t0 - 1, loc=tuple(center), sc=(0.01, 0.01, 0.01)); key_prop(o, "fade", 0.0, t0 - 1)
    for k in range(0, 11):
        w = k / 10
        rr = 0.3 + r1 * ease_out(w)
        key_obj(o, t0 + k, loc=(center[0] + trail[0] * k, center[1] + trail[1] * k, center[2] - 0.08 * k),
                sc=(rr, rr, 0.6 + 0.6 * (1 - w)))
        key_prop(o, "fade", 0.95 * (1 - w) ** 1.4, t0 + k)
    for i in range(n):
        q = link(bpy.data.objects.new(f"{tag} px{i}", PIX)); q["fade"] = 0.0
        a = 2 * math.pi * i / n + rng.uniform(-0.1, 0.1)
        sp = rng.uniform(0.22, 0.34); s0 = rng.uniform(0.1, 0.18); life = int(rng.integers(10, 16))
        pos = np.array(center, float) + np.array([math.cos(a), math.sin(a), 0]) * 0.4
        vel = np.array([math.cos(a) * sp + trail[0], math.sin(a) * sp + trail[1], rng.uniform(-0.03, 0.03)])
        key_obj(q, t0 - 1, loc=tuple(pos), sc=0.0001); key_prop(q, "fade", 0.0, t0 - 1)
        for k in range(life + 1):
            key_obj(q, t0 + k, loc=tuple(pos), sc=s0 * (1 - (k / life) ** 2) + 0.0001)
            key_prop(q, "fade", 1.0 - (k / life) ** 2, t0 + k)
            pos = pos + vel; vel *= 0.85; vel[2] -= 0.01
        key_obj(q, t0 + life + 1, sc=0.0001); key_prop(q, "fade", 0.0, t0 + life + 1)


def flat_arrow(name, origin, ang, length, m, width=0.25):
    d = np.array([-math.sin(ang), -math.cos(ang), 0.0]); s = np.array([-d[1], d[0], 0.0])
    o = np.asarray(origin, float) + np.array([0, 0, 0.02])
    tip = o + d * length; base = o + d * (length - 0.7)
    vs = [o + s * width / 2, o - s * width / 2, base - s * width / 2, base + s * width / 2, base + s * 0.45, tip,
          base - s * 0.45]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], [(0, 1, 2, 3), (4, 6, 5)]); me.update()
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


# --------------------------------------------------------------- build
dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, pos [right, forward, "
                  "up] blocks from the start, glow, cam_shake [pitch, yaw] degrees, event ('burst' = the second-jump "
                  "puff). Body yaw = the run direction (deg clockwise from the look in 'run_deg'). 20 ticks a second.",
        "rules": {"second_jump": "a jump pressed while airborne from the first jump (any tick of it)",
                  "standing_vs_running": "horizontal speed under 0.15 blocks/tick at the second jump = standing puff; "
                                         "at or over = running arc along the horizontal velocity (only that way)",
                  "standing": "puff to 3.2 blocks above the jump-start ground, hero hover with a 0.07 bob (1.5 s), "
                              "subtle shake 0.5 deg over 4 ticks; free flight on any movement input",
                  "running": "flat flight at 5 blocks 6 ticks after the second jump, speed 0.3 -> 0.95 blocks/tick "
                             "through the arc, easing to 0.7 cruise; free flight after"},
        "takes": {}}

LANE = 14.0
lanes = [(s, None) for s in STANDING] + RUNNING
for li, (take, theta) in enumerate(lanes):
    tag = take if theta is None else (take if theta == 0 else f"{take} {theta:03d}")
    ox = li * LANE; oy = 0.0
    rng = np.random.default_rng(403 + li)
    sim = sim_standing(take) if theta is None else (sim_land(take) if take.startswith("L") else sim_running(take, theta))
    objs = make_player(tag.replace(" ", "_"))
    rm = mat(f"TS ring {tag}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"TS {tag} mover", None)); mover.empty_display_size = 0.1
    shaker = link(bpy.data.objects.new(f"TS {tag} shake", None)); shaker.empty_display_size = 0.05
    shaker.parent = mover
    mfull = link(bpy.data.objects.new(f"TS {tag} mover full", None)); mfull.empty_display_size = 0.05
    phi = -R(theta or 0)
    dvec = np.array([-math.sin(phi), -math.cos(phi), 0.0])
    ticks = []
    pxy = np.zeros(3)
    for t, (p, th, dist, z, glow, ev) in enumerate(sim):
        if theta is not None:
            phi = -R(th); dvec = np.array([-math.sin(phi), -math.cos(phi), 0.0])
            pxy = pxy + dvec * dist
            pos = pxy + np.array([0, 0, z])
        else:
            pos = np.array([0.0, dist, 0.0]) + np.array([0, 0, z])
        origin = np.array([ox, oy, 0.0]) + pos
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1, side=phi)
        mover.location = tuple(np.array([ox, oy, 0.0]) + pos * np.array([1, 1, 0.55]))
        mover.keyframe_insert("location", frame=t + 1)
        mfull.location = tuple(np.array([ox, oy, 0.0]) + pos); mfull.keyframe_insert("location", frame=t + 1)
        s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = glow; s.keyframe_insert("default_value", frame=t + 1)
        shake = (0.0, 0.0)
        if ev == "burst":
            if theta is None:
                burst_ring(f"TS {tag} puff", origin + np.array([0, 0, 0.05]), t + 1, rng, r1=2.6, n=28)
            else:
                v = 0.3
                burst_ring(f"TS {tag} puff", origin + np.array([0, 0, 0.05]), t + 1, rng, r1=1.4 if take.startswith("L") else 1.8, n=20,
                           trail=tuple(-dvec[:2] * 0.12))
        ticks.append({"pos": [round(float(-pos[0]), 3), round(float(-pos[1]), 3), round(float(pos[2]), 3)],
                      "glow": round(float(glow), 1), "event": ev,
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    # subtle shake on the standing puff only: about 0.5 degrees, decaying over 4 ticks
    t_burst = next(i for i, x in enumerate(sim) if x[5] == "burst")
    phi = -R(theta or 0); dvec = np.array([-math.sin(phi), -math.cos(phi), 0.0])
    shaker.rotation_mode = "XYZ"
    shaker.rotation_euler = (0, 0, 0); shaker.keyframe_insert("rotation_euler", frame=t_burst)
    if theta is None:
        for k in range(5):
            a = R(0.5) * (1 - k / 4)
            pr, yw = a * (1 if k % 2 == 0 else -1), a * 0.6 * (-1 if k % 2 == 0 else 1)
            shaker.rotation_euler = (pr, 0, yw); shaker.keyframe_insert("rotation_euler", frame=t_burst + 1 + k)
            ticks[t_burst + k]["cam_shake"] = [round(math.degrees(pr), 2), round(math.degrees(yw), 2)]
    shaker.rotation_euler = (0, 0, 0); shaker.keyframe_insert("rotation_euler", frame=t_burst + 6)
    dump["takes"][tag] = {"name": NAMES[take], "run_deg": theta, "heading_deg": [round(x[1], 1) for x in sim], "burst_tick": t_burst, "ticks": ticks}
    # ground marks: look (white, -y) and run direction (green)
    flat_arrow(f"TS {tag} look", (ox, oy + 1.5, 0), 0.0, 2.5, LOOKM)
    if theta is not None:
        flat_arrow(f"TS {tag} run", (ox, oy, 0), phi, 3.0, RUNM, 0.3)
    lb = bpy.data.curves.new(f"TS label {tag}", "FONT")
    lb.body = f"{tag}  {NAMES[take]}" + ("" if not theta else f" ({theta} deg from look)")
    lb.size = 0.45; lb.align_x = "CENTER"
    tl = link(bpy.data.objects.new(f"TS label {tag}", lb)); tl.location = (ox, oy + 3.2, 0.02)
    tl.data.materials.append(LABEL)
    # over the right shoulder, looking where the player looks (-y), riding the mover through the shaker
    c = cam(f"Cam {tag}", (ox - 1.0, oy + 5.5, 2.6), (ox + 0.1, oy - 6.0, 1.6), 28)
    c.parent = shaker; c.matrix_parent_inverse = Matrix.Translation((ox, oy, 0.0)).inverted()
    # side camera framing the second jump and the arc (along the run direction, from the right of it)
    d_b = sum(x[2] for x in sim[:t_burst + 1]) if theta is not None else 0.0
    focus = np.array([ox, oy, 0.0]) + (dvec * (d_b + 3.0) if theta is not None else np.array([0, -2.0, 0]))
    side_v = np.array([-dvec[1], dvec[0], 0.0]) * -1
    cam(f"Cam {tag} side", tuple(focus + side_v * 13 + np.array([0, 0, 4.0])), tuple(focus + np.array([0, 0, 2.8])), 30)
    if theta is not None:
        # close, following, from the right of the run: for judging the arm and body line
        st = np.array([ox, oy, 0.0])
        cc = cam(f"Cam {tag} close", tuple(st - side_v * 6.0 + dvec * 1.5 + np.array([0, 0, 1.6])), tuple(st + dvec * 0.8 + np.array([0, 0, 1.1])), 35)
        cc.parent = mfull; cc.matrix_parent_inverse = Matrix.Translation((ox, oy, 0.0)).inverted()
    print(tag, "built, burst at tick", t_burst, flush=True)

with open(os.path.join(FOLDER, "takeoff_small2_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

for o in scene.objects:
    ad = o.animation_data
    if ad and ad.action:
        try:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        except Exception:
            pass

scene.frame_start, scene.frame_end = 1, T_END
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE * 3.5, -20, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "TS ground"; g.scale = (300, 300, 1)
gm = bpy.data.materials.new("TS ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 300
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("TS world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("TS sun", bpy.data.lights.new("TS sun", "SUN")))
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
cam("Cam all", (LANE * 3.5, 40, 22), (LANE * 3.5, -10, 2), 30)
scene.camera = bpy.data.objects["Cam S1"]
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
