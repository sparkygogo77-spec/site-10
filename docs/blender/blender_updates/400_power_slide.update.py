# Pass 400: power landing - stop dead, or a strong one-foot slide (Blender designer chat, 2026-10-14).
# J: "a power landing that either stops you dead or if you are moving above a certain limit create a slide animation
# ... a construct texture animation clearing the blocks i slide to until i come to a halt and the animation for the
# slide should be a strong one foot stop". Picks: show all 3 thresholds (8 / 15 / 25 blocks/s), both clearing styles,
# LEFT foot plants (ring hand free), short and brutal (5 blocks at most; length = 5 x speed / 28).
#   D0  stop dead: under the threshold. Two-foot squat, ring fist to the ground, the 3x3 under you turns construct and
#       dissolves into pixels, ground pulse.
#   A1-A3 dissolve: blocks ahead of the planted left foot light up in construct texture, then break into pixel particles
#       as the foot reaches them. A construct pad catches the foot so you skid level over the trench.
#   B1-B3 plough: a construct bow-wave blade in front of the left foot shoves the blocks out of the path; they tumble
#       aside in construct texture, land, and dissolve into pixels a moment later.
# A1/B1 land at 10 b/s (threshold 8), A2/B2 at 18 (threshold 15), A3/B3 at 28 (threshold 25).
# Cameras "Cam <take>" (over the right shoulder, following), "Cam <take> side", "Cam <take> front", "Cam all".
# Writes LanternLive\power_slide_poses.json and builds LanternLive\power_slide.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "power_slide.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Power Slide")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Power Slide")
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



# ================================================================== pass 400
T_AIR, H_AIR = 20, 6.0            # dive ticks and start height (blocks) before touchdown
T_LAND = T_AIR
T_END = 100
MAXL = 5.0
TAKES = [("D0", "stop dead (under threshold)", 5.0, None, "D"),
         ("A1", "dissolve - threshold 8 b/s, lands at 10", 10.0, 8, "A"),
         ("A2", "dissolve - threshold 15 b/s, lands at 18", 18.0, 15, "A"),
         ("A3", "dissolve - threshold 25 b/s, lands at 28", 28.0, 25, "A"),
         ("B1", "plough - threshold 8 b/s, lands at 10", 10.0, 8, "B"),
         ("B2", "plough - threshold 15 b/s, lands at 18", 18.0, 15, "B"),
         ("B3", "plough - threshold 25 b/s, lands at 28", 28.0, 25, "B")]
LANE_W = 13
LANES = {t[0]: i * LANE_W for i, t in enumerate(TAKES)}
Y0, Y1 = 16, -14                   # lane block grid, forward is -y; touchdown at y = 0, on top of the layer (z = 1)
TOP = 1.0


def slide_len(v, thr):
    return 0.0 if thr is None else min(MAXL, MAXL * v / 28.0)


# --------------------------------------------------------------- poses (ring = right side, LEFT foot plants)
DIVE = dict(body=(0.95, 0, 0), head=(-0.75, 0, 0), ring=(-2.7, 0, 0.1), free=(0.9, 0, -0.3),
            ringleg=(0.45, 0, 0.03), ringknee=0.6, freeleg=(0.3, 0, -0.03), freeknee=0.5, grounded=False)
REACH = dict(body=(0.05, 0, 0), head=(0.0, 0, 0), ring=(0.6, 0, 0.6), free=(-1.1, 0, -0.35),
             ringleg=(0.35, 0, 0.06), ringknee=1.3, freeleg=(-1.0, 0, -0.06), freeknee=0.25, grounded=False)
REACH2 = dict(body=(0.25, 0, 0), head=(-0.15, 0, 0), ring=(-0.5, 0, 0.3), free=(0.3, 0, -0.5),
              ringleg=(-0.6, 0, 0.1), ringknee=0.6, freeleg=(-0.6, 0, -0.1), freeknee=0.6, grounded=False)
IMPACT = dict(body=(-0.15, 0.1, 0), head=(0.05, 0, 0), ring=(0.85, 0, 0.8), free=(-1.35, 0, -0.5),
              ringleg=(0.55, 0, 0.12), ringknee=1.95, freeleg=(-0.95, 0, -0.08), freeknee=0.95, sink=1.5)
SKID = dict(body=(-0.32, 0.12, 0), head=(0.08, 0, 0), ring=(0.75, 0, 0.75), free=(-1.3, 0, -0.45),
            ringleg=(0.7, 0, 0.1), ringknee=1.55, freeleg=(-1.05, 0, -0.08), freeknee=0.35)
HALT = dict(body=(0.45, 0.05, 0), head=(-0.3, 0, 0), ring=(0.3, 0, 0.5), free=(-0.6, 0, -0.3),
            ringleg=(0.85, 0, 0.1), ringknee=1.6, freeleg=(-0.55, 0, -0.08), freeknee=1.25)
SQUAT = dict(body=(0.75, 0, 0), head=(-0.6, 0, 0), ring=(-0.2, 0, 0.1), free=(0.6, 0, -0.5),
             ringleg=(-1.2, 0, 0.12), ringknee=2.1, freeleg=(-1.1, 0, -0.12), freeknee=2.0, sink=1.0)
STAND = dict(body=(0.05, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.12), free=(0.05, 0, -0.1),
             ringleg=(0.05, 0, 0.03), ringknee=0.1, freeleg=(0.05, 0, -0.03), freeknee=0.1)


def simulate(v, thr):
    """Per tick: (pose, y, z, glow). y = 0 at touchdown, forward is -y; z is height above the top of the blocks."""
    L = slide_len(v, thr)
    n = max(4, int(round(2 * L / v * 20))) if L > 0 else 0
    out = []
    for t in range(T_END + 1):
        if t < T_LAND:
            s = t / T_AIR
            y = v / 20.0 * (T_AIR - t)
            z = H_AIR * (1 - s ** 1.7)
            reach = REACH if L > 0 else REACH2
            p = mixp(DIVE, reach, smooth(max(0.0, (t - (T_AIR - 8)) / 8)))
            p["grounded"] = False
            glow = 6 + 6 * s
        else:
            k = t - T_LAND
            z = 0.0
            if L == 0:                                    # stop dead
                y = 0.0
                if k <= 3:
                    p = mixp(REACH2, SQUAT, smooth(k / 3)); glow = 18 - 2 * k
                elif k <= 20:
                    p = dict(SQUAT); glow = 12 - 0.3 * (k - 3)
                else:
                    p = mixp(SQUAT, STAND, smooth(min(1, (k - 20) / 14))); glow = 6.5
            else:
                w = min(1.0, k / n)
                y = -L * (1 - (1 - w) ** 2)
                if k <= 2:
                    p = mixp(REACH, IMPACT, smooth(k / 2)); glow = 18
                elif k <= n:
                    p = mixp(IMPACT, SKID, smooth(min(1, (k - 2) / 3))); glow = 16
                elif k <= n + 4:
                    p = mixp(SKID, HALT, smooth((k - n) / 4)); glow = 16 - 1.5 * (k - n)
                elif k <= n + 14:
                    p = dict(HALT); glow = 10
                else:
                    p = mixp(HALT, STAND, smooth(min(1, (k - n - 14) / 14))); glow = 7
            p["grounded"] = True
        out.append((p, y, z, glow))
    return out, L, n


def foot_point(sol):
    r, pv = sol["lshin"]
    return np.array([0.0, 6.0, -0.5]) @ rot(*r).T + pv


# --------------------------------------------------------------- materials
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


def block_mat():
    """Grass top / dirt sides with a per-block checker, blended to construct by the object's ["cx"] (0..1)."""
    m = bpy.data.materials.new("PS block"); m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    out = N.get("Material Output"); pb = N.get("Principled BSDF")
    pb.inputs["Roughness"].default_value = 0.9
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Normal"], sp.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
    Lk.new(sp.outputs["Z"], gt.inputs[0])
    ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 1.0
    mp = N.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (0.5, 0.5, 0.5)
    mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5)
    Lk.new(geo.outputs["Position"], mp.inputs[0]); Lk.new(mp.outputs[0], ck.inputs["Vector"])
    ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
    dirt = N.new("ShaderNodeMix"); dirt.data_type = "RGBA"
    Lk.new(gt.outputs[0], dirt.inputs["Factor"])
    dirt.inputs[6].default_value = (0.26, 0.16, 0.09, 1); Lk.new(ck.outputs["Color"], dirt.inputs[7])
    Lk.new(dirt.outputs[2], pb.inputs["Base Color"])
    con = construct_nodes(m, N, Lk)
    em = N.new("ShaderNodeEmission"); Lk.new(con, em.inputs["Color"])
    cx = obj_attr(N, "cx")
    st = N.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = 1.8
    Lk.new(cx, st.inputs[0]); Lk.new(st.outputs[0], em.inputs["Strength"])
    ms = N.new("ShaderNodeMixShader"); Lk.new(cx, ms.inputs[0])
    Lk.new(pb.outputs[0], ms.inputs[1]); Lk.new(em.outputs[0], ms.inputs[2])
    Lk.new(ms.outputs[0], out.inputs["Surface"])
    return m


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


BLOCK = block_mat()
FX = fx_mat()
LABEL = mat("PS label", (0.8, 1.0, 0.85), emit=2.0)


def cube_mesh(name, size=1.0):
    h = size / 2
    verts = [(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    return me


UNIT = cube_mesh("PS unit cube"); UNIT.materials.append(BLOCK)
PIX = cube_mesh("PS pixel"); PIX.materials.append(FX)


def lane_grid(tag, ox, holes):
    me = bpy.data.meshes.new(tag)
    verts, faces = [], []
    for ix in range(-(LANE_W // 2), LANE_W // 2 + 1):
        for iy in range(Y1, Y0 + 1):
            if (ix, iy) in holes:
                continue
            x, y = ox + ix - 0.5, iy - 0.5
            b = len(verts)
            verts += [(x + dx, y + dy, dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
            faces += [(b, b + 1, b + 3, b + 2), (b + 4, b + 6, b + 7, b + 5), (b, b + 4, b + 5, b + 1),
                      (b + 2, b + 3, b + 7, b + 6), (b, b + 2, b + 6, b + 4), (b + 1, b + 5, b + 7, b + 3)]
    me.from_pydata(verts, [], faces); me.update(); me.materials.append(BLOCK)
    o = link(bpy.data.objects.new(tag, me)); o["cx"] = 0.0
    return o


def key_prop(o, name, val, f):
    o[name] = float(val); o.keyframe_insert(f'["{name}"]', frame=f)


def key_obj(o, f, loc=None, sc=None, rotv=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if sc is not None:
        o.scale = (sc, sc, sc) if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)
    if rotv is not None:
        o.rotation_euler = rotv; o.keyframe_insert("rotation_euler", frame=f)


def pixel_burst(tag, center, t0, rng, n=10, drift=(0, 0, 0), side=0.0):
    """A block breaking into construct pixels: n cubes from inside the block, up and out under gravity, shrinking."""
    for i in range(n):
        o = link(bpy.data.objects.new(f"{tag} px{i}", PIX)); o["fade"] = 0.0
        p0 = np.array(center, float) + rng.uniform(-0.4, 0.4, 3)
        vel = np.array([drift[0] + side * rng.uniform(0.02, 0.1) + rng.uniform(-0.06, 0.06),
                        drift[1] + rng.uniform(-0.05, 0.05), rng.uniform(0.08, 0.24)])
        life = int(rng.integers(12, 22)); s0 = rng.uniform(0.12, 0.22)
        key_obj(o, t0, loc=tuple(p0), sc=0.0001); key_prop(o, "fade", 0.0, t0)
        pos = p0.copy()
        for k in range(1, life + 1):
            pos = pos + vel; vel[2] -= 0.02; vel[:2] *= 0.9
            if pos[2] < s0 / 2 + TOP * 0:     # pixels can fall into the trench, not through the floor
                pos[2] = s0 / 2; vel[2] = abs(vel[2]) * 0.3
            f = t0 + k
            key_obj(o, f, loc=tuple(pos), sc=s0 * (1 - (k / life) ** 2) + 0.0001)
            key_prop(o, "fade", 1.0 - (k / life) ** 3, f)
        key_obj(o, t0 + life + 1, sc=0.0001); key_prop(o, "fade", 0.0, t0 + life + 1)


def pulse(tag, center, t0, r1, life=8):
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1.0, fill_type="NGON")
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = tag; o.data.materials.append(FX); o["fade"] = 0.0
    o.location = (center[0], center[1], TOP + 0.03)
    key_obj(o, t0 - 1, sc=(0.01, 0.01, 1)); key_prop(o, "fade", 0.0, t0 - 1)
    for k in range(life + 1):
        w = k / life
        key_obj(o, t0 + k, sc=(0.3 + r1 * smooth(w), 0.3 + r1 * smooth(w), 1))
        key_prop(o, "fade", 0.9 * (1 - w) ** 1.5, t0 + k)
    return o


# --------------------------------------------------------------- glow (bloom from Render Layers, Standard view)
try:
    tree = bpy.data.node_groups.new("PS Glow", "CompositorNodeTree")
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

# --------------------------------------------------------------- build every take
dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, forward and up in "
                  "blocks (forward 0 = touchdown block centre), ring glow. 'cells': per cleared block (dx, forward) the "
                  "tick it turns construct ('lit') and the tick it is gone ('cleared'). 20 ticks a second.",
        "slide_len_rule": "len = min(5, 5 * speed / 28) blocks; slide ticks = round(2 * len / speed * 20)",
        "thresholds_bps": [8, 15, 25], "takes": {}}

for take, name, v, thr, style in TAKES:
    ox = LANES[take]
    rng = np.random.default_rng(400 + LANES[take])
    sim, L, n = simulate(v, thr)
    width = 3 if (style == "D" or v >= 15) else 1
    # which cells clear: D0 the 3x3 under you; slides the path from touchdown to the halt block
    if style == "D":
        cells = [(dx, j) for j in (-1, 0, 1) for dx in (-1, 0, 1)]
    else:
        # the trench runs to the halt block; the halt block itself stays, so you stop on solid ground
        cells = [(dx, j) for j in range(0, int(math.ceil(L - 0.2))) for dx in range(-(width // 2), width // 2 + 1)]
    holes = {(dx, -j) for dx, j in cells}
    lane_grid(f"PS {take} ground", ox, holes)
    objs = make_player(take)
    rm = mat(f"PS ring {take}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"PS {take} mover", None)); mover.empty_display_size = 0.1
    ticks, feet = [], []
    for t, (p, y, z, glow) in enumerate(sim):
        origin = np.array([ox, y, TOP + z])
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1)
        fp = to_bl(foot_point(sol)) + origin
        feet.append(fp)
        mover.location = (ox, y, TOP + z * 0.5); mover.keyframe_insert("location", frame=t + 1)
        s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = glow; s.keyframe_insert("default_value", frame=t + 1)
        ticks.append({"forward": round(-y, 3), "up": round(z, 3), "glow": round(float(glow), 2),
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    t_halt = T_LAND + n
    cell_log = []
    for dx, j in cells:
        cy = -float(j)
        c = np.array([ox + dx, cy, 0.5])
        o = link(bpy.data.objects.new(f"PS {take} cell {dx} {j}", UNIT)); o["cx"] = 0.0
        o.scale = (0.999, 0.999, 0.999)
        o.location = tuple(c)
        if style == "D":
            dist = abs(dx) + abs(j)
            t_lit = T_LAND - 1 + dist; t_gone = T_LAND + 4 + 2 * dist
        elif style == "A":
            # lights when the planted foot is within 1.6 blocks, breaks as the foot reaches it (sides a tick later)
            t_lit = next((t for t in range(len(feet)) if feet[t][1] - 1.6 <= cy + 0.5 and t >= T_LAND - 3), T_LAND)
            t_gone = next((t for t in range(T_LAND, len(feet)) if feet[t][1] <= cy + 0.35), t_halt)
            t_gone = max(t_gone, t_lit + 2) + abs(dx)
            t_lit = min(t_lit, t_gone - 2)
        else:
            # the blade, half a block ahead of the foot, reaches the cell
            t_gone = next((t for t in range(T_LAND, len(feet)) if feet[t][1] - 0.6 <= cy + 0.5), t_halt) + abs(dx)
            t_lit = t_gone
        cell_log.append({"dx": dx, "forward": j, "lit": t_lit - T_LAND, "cleared": t_gone - T_LAND})
        f_lit, f_gone = t_lit + 1, t_gone + 1
        key_prop(o, "cx", 0.0, 1); key_obj(o, 1, sc=1.0, loc=tuple(c), rotv=(0, 0, 0))
        if style == "D" and dx == 0 and j == 0:
            # the block you land on turns construct under your feet and holds you, then fades back
            key_prop(o, "cx", 0.0, f_lit - 1); key_prop(o, "cx", 1.0, f_lit + 1)
            key_prop(o, "cx", 1.0, f_lit + 16); key_prop(o, "cx", 0.0, f_lit + 36)
            cell_log[-1]["cleared"] = None; cell_log[-1]["note"] = "landing block: construct for 0.8 s, fades back"
            continue
        if style in ("A", "D"):
            key_prop(o, "cx", 0.0, f_lit - 1); key_prop(o, "cx", 1.0, f_lit + 1)
            key_obj(o, f_gone - 1, sc=1.0); key_obj(o, f_gone + 1, sc=0.0001)
            pixel_burst(f"PS {take} c{dx}{j}", c, f_gone, rng, n=10, drift=(0.0, -v / 20 * 0.25, 0), side=float(dx))
        else:
            # shoved: lifted out of the trench, thrown aside and forward, tumbling, lands on the surface, dissolves
            side = float(dx) if dx else (1.0 if (j % 2 == 0) else -1.0)
            pos = c.copy(); vel = np.array([side * rng.uniform(0.24, 0.32), -v / 20 * rng.uniform(0.08, 0.16),
                                            rng.uniform(0.24, 0.3)])
            spin = rng.uniform(-0.5, 0.5, 3); ang = np.zeros(3)
            key_prop(o, "cx", 0.0, f_gone - 1); key_obj(o, f_gone - 1, loc=tuple(pos), rotv=(0, 0, 0))
            key_prop(o, "cx", 1.0, f_gone + 1)
            landed, f = None, f_gone
            for k in range(1, 40):
                f = f_gone + k
                if landed is None:
                    pos = pos + vel; vel[2] -= 0.045; vel[:2] *= 0.93; ang = ang + spin
                    outside = abs(pos[0] - ox) > width / 2 + 0.5
                    floor = TOP + 0.5 if outside else 0.5
                    if pos[2] <= floor and vel[2] < 0:
                        pos[2] = floor; landed = k
                        ang = np.round(ang / (math.pi / 2)) * (math.pi / 2)       # settles square
                    key_obj(o, f, loc=tuple(pos), rotv=tuple(ang))
                elif k - landed >= 12:
                    break
            key_obj(o, f, sc=1.0); key_obj(o, f + 2, sc=0.0001)
            pixel_burst(f"PS {take} c{dx}{j}", pos, f + 1, rng, n=10)
        cell_log[-1]["landed_dissolve"] = (f - T_LAND) if style == "B" else None
    # the construct under the planted foot (A: a skid pad; B: the bow-wave blade ahead of it)
    if style == "A":
        pad = link(bpy.data.objects.new(f"PS {take} pad", PIX)); pad["fade"] = 0.0
        for t in range(T_LAND - 2, t_halt + 12):
            fp = feet[min(t, len(feet) - 1)]
            a = 0.85 if t <= t_halt else 0.85 * (1 - (t - t_halt) / 11)
            key_obj(pad, t + 1, loc=(fp[0], fp[1] - 0.1, TOP - 0.03), sc=(0.55, 1.1, 0.06))
            key_prop(pad, "fade", max(0.0, a) if t >= T_LAND else 0.0, t + 1)
    elif style == "B":
        bw = 1.5 if width == 1 else 3.3
        me = bpy.data.meshes.new(f"PS {take} blade")
        # a shallow V (point forward) that curls up at the top, from the trench floor to just over the top
        vs, fs = [], []
        for i, (xx, yy) in enumerate([(-0.5, 0.45), (0.0, 0.0), (0.5, 0.45)]):
            for zz, curl in ((0.0, 0.0), (1.0, 0.0), (1.35, 0.25)):
                vs.append((xx * bw, yy - curl, zz))
        for i in range(2):
            for r_ in range(2):
                a = i * 3 + r_; fs.append((a, a + 3, a + 4, a + 1))
        me.from_pydata(vs, [], fs); me.update(); me.materials.append(FX)
        blade = link(bpy.data.objects.new(f"PS {take} blade", me)); blade["fade"] = 0.0
        for t in range(T_LAND - 2, t_halt + 10):
            fp = feet[min(t, len(feet) - 1)]
            a = 0.9 if t <= t_halt else 0.9 * (1 - (t - t_halt) / 9)
            push = 0.0 if t <= t_halt else 0.25 * (t - t_halt)
            key_obj(blade, t + 1, loc=(ox, fp[1] - 0.65 - push, 0.0))
            key_prop(blade, "fade", max(0.0, a) if t >= T_LAND else 0.0, t + 1)
    # ground pulse: at touchdown for D0, at the halt for the slides (around the planted foot)
    if style == "D":
        pulse(f"PS {take} pulse", (ox, 0.0), T_LAND + 1, 3.0)
    else:
        fp = feet[t_halt]
        pulse(f"PS {take} pulse", (fp[0], fp[1]), t_halt + 1, 2.2)
    dump["takes"][take] = {"name": name, "speed_bps": v, "threshold_bps": thr, "style": style,
                           "touchdown_tick": T_LAND, "slide_blocks": round(L, 3), "slide_ticks": n,
                           "trench_width": width if style != "D" else 3, "cells": cell_log, "ticks": ticks}
    cu = bpy.data.curves.new("PS label " + take, "FONT"); cu.body = f"{take}  {name}"; cu.size = 0.4
    cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("PS label " + take, cu)); tl.location = (ox, 3.0, TOP + 0.01)
    tl.data.materials.append(LABEL)
    # over the right shoulder, placed relative to where the mover is on frame 1, then parented so it follows
    y_s, z_s = sim[0][1], TOP + sim[0][2] * 0.5
    c = cam(f"Cam {take}", (ox - 0.9, y_s + 4.2, z_s + 2.3), (ox + 0.1, y_s - 4.0, z_s + 0.2), 30)
    c.parent = mover; c.matrix_parent_inverse = Matrix.Translation((ox, y_s, z_s)).inverted()
    end = -max(L, 1.0)
    cam(f"Cam {take} side", (ox + 7.0, end / 2 + 1.0, TOP + 2.6), (ox, end / 2, TOP + 0.6), 32)
    cam(f"Cam {take} front", (ox + 2.2, end - 6.5, TOP + 2.2), (ox, end + 0.5, TOP + 0.9), 30)
    print(take, "built: slide", round(L, 2), "blocks in", n, "ticks;", len(cells), "cells", flush=True)

with open(os.path.join(FOLDER, "power_slide_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

# linear keys so the per-tick motion is exact
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
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE_W * 3, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "PS far ground"; g.scale = (200, 200, 1)
g.data.materials.append(mat("PS far ground", (0.2, 0.33, 0.13), rough=0.95))
world = bpy.data.worlds.new("PS world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("PS sun", bpy.data.lights.new("PS sun", "SUN")))
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
cam("Cam all", (LANE_W * 3, 26, 16), (LANE_W * 3, -3, 0), 30)
scene.camera = bpy.data.objects["Cam A2"]
scene.frame_current = T_LAND + 4
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
