# Pass 508: flight slam tiers S2 + S3, lock picked, mobs launched on contact (Chat C, combat, 2026-10-14).
# J on 501: "locked .7s" (L2 PICKED) and "mobs should be sent away as soon as i make contact instead of sending out a
# shockwave that does a small amount of time to reach the mobs, they are all sent away while my particles are already
# fading which they should send sooner so the construct stays a little after the area is immediately clear so just make
# the mobs launch instantly or almost".
# KEEP from 501: S2 medium + S3 big, the dive, the slam pose, the 0.7 s lock (14 ticks), the landing block held for the
# lock, the release pixels, the stand-up. NEW mob timing (same launch strength and direction as 501):
#   M1 instant: every mob in range launches the tick after touchdown.
#   M2 almost: a near-instant ripple, 1 tick per 3 blocks (the far edge of S3 by tick 3).
#   M3 instant + the crater construct holds 6 ticks longer, so the cleared area stays lit a moment after it is empty.
# The ground pulse stays as a look only; it no longer times the hits. Cameras "Cam <tier> <M>" (over the right
# shoulder), "... side", "... front", "Cam all". Builds LanternLive\combat\flight_slam3.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "flight_slam3.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Flight Slam 3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Flight Slam 3")
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


# ------------------------------------------------------------------ construct material, pixels, pulse, glow (from pass 400)
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


# ================================================================== pass 500: flight slams
T_LAND, T_END = 34, 100
TOP = 1.0
V_FLY = 1.0                                   # flat flight, blocks a tick (20 b/s)
LANE_W = 34
GRID = 11                                      # lane block grid half size (blocks)
# take, name, dive height (blocks), crater half size, dive ticks, shockwave radius, pulse ticks, knock (out, up) b/tick
TIERS = [("S2", "medium slam - 5x5 crater, dive from 12", 12.0, 2, 12, 5.0, 10, (0.75, 0.55)),
         ("S3", "big slam - 7x7 crater, dive from 20", 20.0, 3, 16, 7.0, 12, (0.95, 0.65))]
LOCKS = [("M1", 14), ("M2", 14), ("M3", 14)]   # all L2 0.7 s; M = mob timing
STAND_T = 8                                    # ticks to stand once the lock lets go
MNAME = {"M1": "mobs launch instantly", "M2": "mobs launch almost instantly", "M3": "instant, crater lit longer"}
TAKES = [(f"{t[0]} {l}", f"{t[1]}, {MNAME[l]}",) + t[2:] + (lk,) for t in TIERS for l, lk in LOCKS]
LANES = {t[0]: i * LANE_W for i, t in enumerate(TAKES)}
# mob stand-ins: (angle deg from forward, distance in blocks) per take; ahead and to the sides so the
# over-the-shoulder camera stays clear
MOBS = {"S2": [(-85, 3.6), (-40, 4.4), (0, 3.0), (45, 2.4), (90, 4.6)],
        "S3": [(-95, 5.0), (-55, 3.0), (-15, 5.6), (25, 4.0), (60, 6.2), (100, 2.8)]}

# --------------------------------------------------------------- poses (absolute part rotations; ring = right side)
FLY = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-1.57, 0, 0.02), free=(1.35, 0, -0.12),
           ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
# head-down dive: the ring arm points along the body (body pitch - pi), so the ring fist leads; legs trail
DIVEF = dict(body=(2.25, 0, 0), head=(0.0, 0, 0), ring=(2.25 - math.pi, 0, 0.04), free=(2.05, 0, -0.2),
             ringleg=(2.25, 0, 0.03), ringknee=0.15, freeleg=(2.15, 0, -0.05), freeknee=0.35, grounded=False)
# legs swing under, ring fist cocked down at the ground
PRESLAM = dict(body=(1.05, 0, 0), head=(0.0, 0, 0), ring=(-1.2, 0, 0.1), free=(0.4, 0, -0.6),
               ringleg=(-0.55, 0, 0.08), ringknee=1.1, freeleg=(-0.85, 0, -0.08), freeknee=0.9, grounded=False)
# one knee down, ring fist into the ground (K3 slam)
SLAM = dict(body=(1.1, 0, 0), head=(-0.4, 0, 0), ring=(-0.3, 0, 0.1), free=(0.9, 0, -0.5),
            ringleg=(0.3, 0, 0.06), ringknee=1.6, freeleg=(-1.3, 0, -0.08), freeknee=1.5, sink=2.0)
STAND = dict(body=(0.05, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.12), free=(0.05, 0, -0.1),
             ringleg=(0.05, 0, 0.03), ringknee=0.1, freeleg=(0.05, 0, -0.03), freeknee=0.1)


def dive_path(H, D):
    """Per tick (y, z) for flat flight then a curved dive: a quadratic Bezier from the pitch-over point, through a
    control point ahead at full height, down to the touchdown block. Forward is -y; touchdown at y = 0."""
    t0 = T_LAND - D
    reach = 0.55 * H + 2.0                     # forward distance covered in the dive
    P0, P1, P2 = np.array([reach, H]), np.array([reach * 0.45, H]), np.array([0.0, 0.0])
    out = []
    for t in range(T_END + 1):
        if t < t0:
            out.append((reach + V_FLY * (t0 - t), H))
        elif t < T_LAND:
            s = (t - t0) / D
            s = s ** 1.25                       # accelerating into the ground
            p = (1 - s) ** 2 * P0 + 2 * (1 - s) * s * P1 + s * s * P2
            out.append((float(p[0]), float(p[1])))
        else:
            out.append((0.0, 0.0))
    return out, t0


def simulate(H, D, lock):
    path, t0 = dive_path(H, D)
    sim = []
    for t, (y, z) in enumerate(path):
        if t < t0:
            p = dict(FLY); glow = 7.0
        elif t < T_LAND - 4:
            w = smooth(min(1.0, (t - t0) / 4)); p = mixp(FLY, DIVEF, w); glow = 7 + 9 * (t - t0) / D
        elif t < T_LAND:
            p = mixp(DIVEF, PRESLAM, smooth((t - (T_LAND - 4)) / 4)); glow = 7 + 9 * (t - t0) / D
        else:
            k = t - T_LAND
            if k <= 3:
                p = mixp(PRESLAM, SLAM, smooth(k / 3)); glow = 18 - 2 * k
            elif k <= lock:
                p = dict(SLAM); glow = 12 - 0.3 * (k - 3)
            else:
                p = mixp(SLAM, STAND, smooth(min(1, (k - lock) / STAND_T))); glow = 6.5
        p["grounded"] = t >= T_LAND
        sim.append((p, y, z, glow))
    return sim, t0


# --------------------------------------------------------------- mob stand-ins (hurt flash from the object's ["hurt"])
def mob_mat():
    m = bpy.data.materials.new("FS mob"); m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    pb = N.get("Principled BSDF"); pb.inputs["Roughness"].default_value = 0.85
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.16, 0.32, 0.2, 1); mix.inputs[7].default_value = (0.75, 0.08, 0.06, 1)
    Lk.new(obj_attr(N, "hurt"), mix.inputs["Factor"]); Lk.new(mix.outputs[2], pb.inputs["Base Color"])
    return m


MOBM = mob_mat()


def mob_mesh():
    """A plain upright stand-in (0.6 x 0.6 x 1.9 blocks: body and a head cube), origin at the feet."""
    me = bpy.data.meshes.new("FS mob")
    verts, faces = [], []
    for (a, b) in (((-0.3, -0.2, 0.0), (0.3, 0.2, 1.4)), ((-0.25, -0.25, 1.4), (0.25, 0.25, 1.9))):
        base = len(verts)
        verts += [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        faces += [tuple(base + i for i in f) for f in
                  ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))]
    me.from_pydata(verts, [], faces); me.update(); me.materials.append(MOBM)
    return me


MOBME = mob_mesh()


def ring_radius(k, R, life):
    """The ground pulse's radius k ticks after the slam (matches pulse(): 0.3 + R * smooth)."""
    return 0.3 + R * smooth(min(1.0, max(0.0, k / life)))


def lane_grid(tag, ox, holes):
    me = bpy.data.meshes.new(tag)
    verts, faces = [], []
    for ix in range(-GRID, GRID + 1):
        for iy in range(-GRID, GRID + 1):
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


# --------------------------------------------------------------- build every take
dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, forward and up in "
                  "blocks (forward 0 = touchdown block centre, positive = still ahead of it), ring glow. 'cells': per "
                  "crater block (dx, dz in blocks from the landing block) the tick it lights ('lit') and the tick it is "
                  "gone ('cleared'), relative to touchdown. 'mobs': hit tick and launch velocity. 20 ticks a second.",
        "crater_rule": "landing block turns construct 0.8 s and stays; ring d = round(euclid distance) lights at tick d-1, "
                       "is gone at tick 4 + 2d", "takes": {}}

for take, name, H, half, D, Rw, plife, (k_out, k_up), lock in TAKES:
    tier = take.split()[0]
    ox = LANES[take]
    rng = np.random.default_rng(500 + ox)
    sim, t0 = simulate(H, D, lock)
    cells = [(dx, j) for j in range(-half, half + 1) for dx in range(-half, half + 1)]
    holes = {(dx, j) for dx, j in cells if (dx, j) != (0, 0)}
    holes.add((0, 0))                                         # the landing block is its own object
    lane_grid(f"FS {take} ground", ox, holes)
    objs = make_player(take)
    rm = mat(f"FS ring {take}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"FS {take} mover", None)); mover.empty_display_size = 0.1
    ticks = []
    for t, (p, y, z, glow) in enumerate(sim):
        origin = np.array([ox, y, TOP + z])
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1)
        mover.location = (ox, y, TOP + z); mover.keyframe_insert("location", frame=t + 1)
        s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = glow; s.keyframe_insert("default_value", frame=t + 1)
        if t0 <= t < T_LAND and (t - t0) % 2 == 0:
            # a short trail of construct pixels shed by the ring fist through the dive
            hp = to_bl(hand_point(sol)) + origin
            pixel_burst(f"FS {take} trail{t}", hp, t + 1, rng, n=3)
        ticks.append({"locked": T_LAND <= t <= T_LAND + lock, "forward": round(y, 3), "up": round(z, 3), "glow": round(float(glow), 2),
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    # the crater: D0 rules, scaled out ring by ring
    cell_log = []
    npx = 10 if half == 1 else (8 if half == 2 else 6)
    for dx, j in cells:
        c = np.array([ox + dx, float(j), 0.5])
        o = link(bpy.data.objects.new(f"FS {take} cell {dx} {j}", UNIT)); o["cx"] = 0.0
        o.scale = (0.999, 0.999, 0.999); o.location = tuple(c)
        d = int(round(math.hypot(dx, j)))
        t_lit = T_LAND - 1 + d; t_gone = T_LAND + 4 + 2 * d + (6 if take.endswith("M3") else 0)
        f_lit, f_gone = t_lit + 1, t_gone + 1
        key_prop(o, "cx", 0.0, 1); key_obj(o, 1, sc=1.0, loc=tuple(c))
        if (dx, j) == (0, 0):
            key_prop(o, "cx", 0.0, f_lit - 1); key_prop(o, "cx", 1.0, f_lit + 1)
            f_rel = T_LAND + lock + 1                         # the lock lets go
            key_prop(o, "cx", 1.0, f_rel); key_prop(o, "cx", 0.0, f_rel + 6)
            # release cue: a small ring of pixels popping off the feet
            for q in range(8):
                a = q * math.pi / 4
                pixel_burst(f"FS {take} release{q}", (ox + 0.45 * math.cos(a), 0.45 * math.sin(a), TOP + 0.05), f_rel,
                            rng, n=2, drift=(0.05 * math.cos(a), 0.05 * math.sin(a), 0.02))
            cell_log.append({"dx": 0, "dz": 0, "lit": t_lit - T_LAND, "cleared": None, "release": lock,
                             "note": "landing block: construct for the whole lock, fades back over 6 ticks after it"})
            continue
        key_prop(o, "cx", 0.0, f_lit - 1); key_prop(o, "cx", 1.0, f_lit + 1)
        key_obj(o, f_gone - 1, sc=1.0); key_obj(o, f_gone + 1, sc=0.0001)
        out = np.array([dx, j], float); out = out / (np.linalg.norm(out) or 1.0)
        pixel_burst(f"FS {take} c{dx}{j}", c, f_gone, rng, n=npx, drift=(0.06 * out[0], 0.06 * out[1], 0))
        cell_log.append({"dx": dx, "dz": j, "lit": t_lit - T_LAND, "cleared": t_gone - T_LAND})
    pulse(f"FS {take} pulse", (ox, 0.0), T_LAND + 1, Rw, life=plife)
    # mobs: hit when the pulse reaches them, knocked up and out (harder the nearer), Minecraft-style drag and gravity
    mob_log = []
    for mi, (ang, dist) in enumerate(MOBS[tier]):
        a = math.radians(ang)
        dirv = np.array([math.sin(a), -math.cos(a)])           # angle 0 = straight ahead (-y)
        pos = np.array([ox + dirv[0] * dist, dirv[1] * dist, TOP])
        o = link(bpy.data.objects.new(f"FS {take} mob {mi}", MOBME)); o["hurt"] = 0.0
        face = math.atan2(-dirv[0], dirv[1])                    # facing the player
        key_obj(o, 1, loc=tuple(pos), rotv=(0, 0, face)); key_prop(o, "hurt", 0.0, 1)
        k_hit = 0 if not take.endswith("M2") else int(dist // 3)
        f_hit = T_LAND + 1 + k_hit
        near = max(0.25, 1.0 - dist / (Rw + 1.5))
        vel = np.array([dirv[0] * k_out * near, dirv[1] * k_out * near, k_up * (0.55 + 0.45 * near)])
        key_obj(o, f_hit, loc=tuple(pos)); key_prop(o, "hurt", 0.0, f_hit)
        key_prop(o, "hurt", 1.0, f_hit + 1); key_prop(o, "hurt", 1.0, f_hit + 8); key_prop(o, "hurt", 0.0, f_hit + 10)
        landed, tilt = None, 0.0
        for k in range(1, T_END - f_hit + 1):
            f = f_hit + k
            if landed is None:
                pos = pos + vel; vel[2] -= 0.08; vel *= 0.98
                inside = abs(pos[0] - ox) <= half + 0.5 and abs(pos[1]) <= half + 0.5 and f > T_LAND + 4
                floor = 0.0 if inside else TOP
                tilt = min(0.35, tilt + 0.06)
                if pos[2] <= floor and vel[2] < 0:
                    pos[2] = floor; landed = k; tilt = 0.0
            else:
                vel[:2] *= 0.55; pos[:2] = pos[:2] + vel[:2]
            ax = np.array([-dirv[1], dirv[0]])                   # tip backwards, away from the slam, while airborne
            key_obj(o, f, loc=tuple(pos), rotv=(tilt * ax[0] * -1, tilt * ax[1] * -1, face))
        mob_log.append({"angle_deg": ang, "distance": dist, "hit_tick": f_hit - 1 - T_LAND,
                        "launch_bpt": [round(float(q), 3) for q in (dirv[0] * k_out * near, k_up * (0.55 + 0.45 * near),
                                                                    dirv[1] * k_out * near)]})
    dump["takes"][take] = {"name": name, "dive_height": H, "dive_ticks": D, "touchdown_tick": T_LAND,
                           "crater": f"{2 * half + 1}x{2 * half + 1}", "shockwave_radius": Rw, "pulse_ticks": plife,
                           "knock_out_up_bpt": [k_out, k_up], "lock_ticks": lock, "stand_ticks": STAND_T,
                           "free_at_tick": lock + STAND_T, "cells": cell_log, "mobs": mob_log, "ticks": ticks}
    cu = bpy.data.curves.new("FS label " + take, "FONT"); cu.body = f"{take}  {name}"; cu.size = 0.5
    cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FS label " + take, cu)); tl.location = (ox, -GRID + 1.0, TOP + 0.01)
    tl.data.materials.append(LABEL)
    # over the right shoulder, from the mover's frame-1 position, parented so it follows the flight and the dive
    y_s, z_s = sim[0][1], TOP + sim[0][2]
    c = cam(f"Cam {take}", (ox - 1.1, y_s + 4.6, z_s + 2.4), (ox + 0.1, y_s - 5.0, z_s - 1.2), 30)
    c.parent = mover; c.matrix_parent_inverse = Matrix.Translation((ox, y_s, z_s)).inverted()
    dv = 0.55 * H + 2.0                        # forward length of the dive
    cam(f"Cam {take} side", (ox + 1.1 * H + 6, dv * 0.5, TOP + H * 0.55),
        (ox, dv * 0.5, TOP + H * 0.45), 22)
    cam(f"Cam {take} front", (ox + 3.0, -half - 8.5, TOP + 3.2), (ox, 0.0, TOP + 0.8), 30)
    print(take, "built:", len(cells), "cells,", len(MOBS[tier]), "mobs", flush=True)

with open(os.path.join(FOLDER, "flight_slam3_poses.json"), "w") as fh:
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
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE_W * 2.5, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "FS far ground"; g.scale = (300, 300, 1)
g.data.materials.append(mat("FS far ground", (0.2, 0.33, 0.13), rough=0.95))
world = bpy.data.worlds.new("FS world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("FS sun", bpy.data.lights.new("FS sun", "SUN")))
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
cam("Cam all", (LANE_W * 2.5, 70, 40), (LANE_W * 2.5, -2, 2), 32)
scene.camera = bpy.data.objects["Cam S2 M1"]
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
