# Pass 518: primed slams, instant craters, rebuild, slide trench (Chat C, combat, 2026-10-14).
# J (after testing in game): "if im flying fast and i hold shift and fly into the ground it should be a primed slam and
# it should lock me into the landing motion, i need to see the crater happen instantly though, I want the construct to
# last for a little longer too after making the crater, AFTER the crater though i should be able to look at it and left
# click and rebuild the blocks as the construct dissolves away. the slam should also work that way if im super jumping
# holding crouch as im coming down should prime me for the locked in larger slam ... the crater still is only
# constructed in the center when i need it to spread if i slight off the construct i need that sliding animation for
# the small crater if i dont lock into place".
#   P1 primed flight slam: flying fast (20 b/s, 10 blocks up), hold shift -> locked at once into the dive (ring fist
#      first), fly into the ground: the whole 7x7 crater opens the tick you land (every block at once), lined with
#      construct, mobs launched on contact, 0.7 s lock. The construct lining lasts 3 s. At 2 s you look at the crater
#      and left click: the blocks rebuild from where you look, rippling outward (construct blocks re-forming, fading to
#      their real look). Blocks not yet rebuilt dissolve away at 3 s.
#   P2 primed super-jump slam: super jump to 24 blocks; hold crouch on the way down -> locked head-down dive, a bigger
#      9x9 crater, same rules; the rebuild follows your crosshair sweeping across it (left click held).
#   U1 unprimed landing (no shift): fast and low, you touch down and slide 5 blocks on one knee; the small crater is a
#      trench 3 wide that spreads with you: each block lights as you reach it, opens 2 ticks later, and the construct
#      lining spreads one block out round the whole trench (not only the centre), holds 2 s, dissolves.
# Cameras "Cam <take>" (over the right shoulder, following), "Cam <take> side", "Cam <take> top".
# Builds LanternLive\combat\primed_slam.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "primed_slam.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Primed Slam")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Primed Slam")
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



# ================================================================== pass 518
TOP = 1.0
GRID = 12
LANE_W = 40
END = 150
FLY = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-1.57, 0, 0.02), free=(1.35, 0, -0.12),
           ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
DIVEF = dict(body=(2.25, 0, 0), head=(0.0, 0, 0), ring=(2.25 - math.pi, 0, 0.04), free=(2.05, 0, -0.2),
             ringleg=(2.25, 0, 0.03), ringknee=0.15, freeleg=(2.15, 0, -0.05), freeknee=0.35, grounded=False)
HEADDOWN = dict(body=(2.9, 0, 0), head=(0.6, 0, 0), ring=(2.9 - math.pi, 0, 0.04), free=(2.6, 0, -0.3),
                ringleg=(2.8, 0, 0.05), ringknee=0.3, freeleg=(2.7, 0, -0.05), freeknee=0.5, grounded=False)
TUCK = dict(body=(0.6, 0, 0), head=(-0.3, 0, 0), ring=(-0.6, 0, 0.3), free=(-0.5, 0, -0.3),
            ringleg=(-1.2, 0, 0.1), ringknee=2.0, freeleg=(-1.2, 0, -0.1), freeknee=2.0, grounded=False)
CROUCH = dict(body=(0.4, 0, 0), head=(-0.2, 0, 0), ring=(0.6, 0, 0.3), free=(0.6, 0, -0.3),
              ringleg=(-0.9, 0, 0.1), ringknee=1.6, freeleg=(-0.9, 0, -0.1), freeknee=1.6)
PRESLAM = dict(body=(1.05, 0, 0), head=(0.0, 0, 0), ring=(-1.2, 0, 0.1), free=(0.4, 0, -0.6),
               ringleg=(-0.55, 0, 0.08), ringknee=1.1, freeleg=(-0.85, 0, -0.08), freeknee=0.9, grounded=False)
SLAM = dict(body=(1.1, 0, 0), head=(-0.4, 0, 0), ring=(-0.3, 0, 0.1), free=(0.9, 0, -0.5),
            ringleg=(0.3, 0, 0.06), ringknee=1.6, freeleg=(-1.3, 0, -0.08), freeknee=1.5, sink=2.0)
SLIDE = dict(body=(0.55, 0, 0), head=(-0.3, 0, 0), ring=(-0.9, 0, 0.5), free=(-0.2, 0, -0.9),
             ringleg=(0.9, 0, 0.1), ringknee=1.2, freeleg=(-1.3, 0, -0.08), freeknee=1.6, sink=2.0)
STAND = dict(body=(0.05, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.12), free=(0.05, 0, -0.1),
             ringleg=(0.05, 0, 0.03), ringknee=0.1, freeleg=(0.05, 0, -0.03), freeknee=0.1)
AIMDOWN = dict(body=(0.15, 0, 0), head=(0.55, 0, 0), ring=(-1.1, 0, 0.05), free=(0.05, 0, -0.1),
               ringleg=(0.05, 0, 0.03), ringknee=0.1, freeleg=(0.05, 0, -0.03), freeknee=0.1)

FLOOR = cube_mesh("PS floor cube"); FLOOR.materials.append(BLOCK)


def grid_with_holes(tag, ox, holes):
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


def cell(tag, at, mesh=None):
    o = link(bpy.data.objects.new(tag, mesh or UNIT)); o["cx"] = 0.0
    o.scale = (0.999, 0.999, 0.999); o.location = tuple(at)
    return o


def launch_mobs(tag, ox, oy, mobs, t_hit, rng, k_out=0.95, k_up=0.65, R_=7.0, half=3):
    out = []
    for mi, (ang, dist) in enumerate(mobs):
        a = math.radians(ang); dv = np.array([math.sin(a), -math.cos(a)])
        pos = np.array([ox + dv[0] * dist, oy + dv[1] * dist, TOP])
        o = link(bpy.data.objects.new(f"{tag} mob {mi}", MOBME)); o["hurt"] = 0.0
        face = math.atan2(-dv[0], dv[1])
        key_obj(o, 1, loc=tuple(pos), rotv=(0, 0, face)); key_prop(o, "hurt", 0.0, 1)
        near = max(0.25, 1.0 - dist / (R_ + 1.5))
        vel = np.array([dv[0] * k_out * near, dv[1] * k_out * near, k_up * (0.55 + 0.45 * near)])
        key_obj(o, t_hit, loc=tuple(pos)); key_prop(o, "hurt", 0.0, t_hit)
        key_prop(o, "hurt", 1.0, t_hit + 1); key_prop(o, "hurt", 1.0, t_hit + 8); key_prop(o, "hurt", 0.0, t_hit + 10)
        landed, tilt = False, 0.0
        for kk in range(1, END - t_hit + 1):
            f = t_hit + kk
            if not landed:
                pos = pos + vel; vel[2] -= 0.08; vel *= 0.98; tilt = min(0.35, tilt + 0.06)
                inside = abs(pos[0] - ox) <= half + 0.5 and abs(pos[1] - oy) <= half + 0.5
                floor = 0.0 if inside else TOP
                if pos[2] <= floor and vel[2] < 0:
                    pos[2] = floor; landed = True; tilt = 0.0
            else:
                vel[:2] *= 0.55; pos[:2] = pos[:2] + vel[:2]
            ax = np.array([-dv[1], dv[0]])
            key_obj(o, f, loc=tuple(pos), rotv=(-tilt * ax[0], -tilt * ax[1], face))
        out.append({"angle_deg": ang, "distance": dist, "hit_tick_after_touchdown": 1})
    return out


def crater_instant(tag, ox, oy, half, t0, rng, hold, rebuild=None, look=(0, 0), sweep=False):
    """Every top block of a (2 half + 1)^2 crater: lit construct and gone at t0 + 1 (instant). The floor under it and the
    ring of blocks round the rim turn construct (the lining), hold for `hold` ticks, then dissolve to pixels (the rim
    goes back to normal, the floor stays). With `rebuild` (a tick), from then on the removed blocks re-form as construct
    and fade to their real look, rippling out from `look` (or sweeping across in x with `sweep`), 1 tick a block."""
    cells = []
    for dx in range(-half, half + 1):
        for dy in range(-half, half + 1):
            top = cell(f"{tag} top {dx} {dy}", (ox + dx, oy + dy, 0.5))
            flr = cell(f"{tag} floor {dx} {dy}", (ox + dx, oy + dy, -0.5), FLOOR)
            key_prop(top, "cx", 0.0, 1); key_obj(top, 1, sc=0.999)
            key_prop(flr, "cx", 0.0, 1)
            centre = dx == 0 and dy == 0
            key_prop(top, "cx", 0.0, t0 - 1); key_prop(top, "cx", 1.0, t0)
            if not centre:
                key_obj(top, t0, sc=0.999); key_obj(top, t0 + 1, sc=0.0001)
                pixel_burst(f"{tag} c{dx}{dy}", (ox + dx, oy + dy, 0.6), t0 + 1, rng, n=4,
                            drift=(0.05 * np.sign(dx), 0.05 * np.sign(dy), 0))
            key_prop(flr, "cx", 0.0, t0); key_prop(flr, "cx", 1.0, t0 + 1)
            if rebuild is not None:
                d = math.hypot(dx - look[0], dy - look[1]) if not sweep else (dx + half)
                tr = int(rebuild + round(d * (1.0 if not sweep else 2.0)))
            else:
                tr = None
            end = t0 + hold
            if tr is not None and tr < end:
                # rebuilt: the block re-forms as construct, then fades to its real look
                if not centre:
                    key_obj(top, tr, sc=0.0001); key_obj(top, tr + 3, sc=0.999)
                key_prop(top, "cx", 1.0, tr + 3); key_prop(top, "cx", 0.0, tr + 13)
                key_prop(flr, "cx", 1.0, tr + 3); key_prop(flr, "cx", 0.0, tr + 13)
                cells.append({"dx": dx, "dy": dy, "removed": 1, "rebuilt": tr - t0})
            else:
                key_prop(top, "cx", 1.0, end)
                key_prop(flr, "cx", 1.0, end); key_prop(flr, "cx", 0.0, end + 4)
                if centre:
                    key_obj(top, end, sc=0.999); key_obj(top, end + 1, sc=0.0001)
                    key_prop(top, "cx", 0.0, end + 1)
                pixel_burst(f"{tag} d{dx}{dy}", (ox + dx, oy + dy, -0.2), end, rng, n=3)
                cells.append({"dx": dx, "dy": dy, "removed": 1, "dissolved": hold})
    # the rim lining: one ring of blocks round the crater turns construct and back
    rim = []
    for dx in range(-half - 1, half + 2):
        for dy in range(-half - 1, half + 2):
            if max(abs(dx), abs(dy)) == half + 1:
                rim.append((dx, dy))
    return cells, rim


def rim_overlay(tag, ox, oy, rim, t0, end, rng):
    for dx, dy in rim:
        o = cell(f"{tag} rim {dx} {dy}", (ox + dx, oy + dy, 0.5))
        o.scale = (1.002, 1.002, 1.002)
        d = max(abs(dx), abs(dy))
        key_obj(o, 1, sc=0.0001); key_obj(o, t0, sc=0.0001); key_obj(o, t0 + 1, sc=1.002)
        key_prop(o, "cx", 1.0, 1)
        key_obj(o, end, sc=1.002); key_obj(o, end + 4, sc=0.0001)


rng = np.random.default_rng(518)
dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, forward/up in "
                  "blocks, the lock, crater cells (removed tick, rebuilt or dissolved tick). 20 ticks a second.",
        "primed_rule": "fast (>= 1 b/tick) and shift (flight) or crouch (super jump fall) held -> locked into the dive "
                       "at once; touchdown -> instant crater, 0.7 s lock",
        "unprimed_rule": "no shift: touch down and slide (5 blocks), the trench spreads with you", "takes": {}}
MOBS7 = [(-95, 5.0), (-55, 3.0), (-15, 5.6), (25, 4.0), (60, 6.2), (100, 2.8)]
MOBS9 = [(-100, 6.0), (-60, 3.5), (-20, 6.5), (20, 4.5), (60, 7.0), (110, 3.2), (160, 5.5)]
TAKES = [("P1", "primed flight slam (shift), 7x7 instant, rebuild ripples from your look"),
         ("P2", "primed super-jump slam (crouch), 9x9 instant, rebuild follows your sweep"),
         ("U1", "unprimed landing, slide 5 blocks, trench spreads with you")]

for li, (take, name) in enumerate(TAKES):
    ox = li * LANE_W
    objs = make_player(take)
    rm = mat(f"FS ring {take}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"FS {take} mover", None)); mover.empty_display_size = 0.1
    ticks = []
    if take == "P1":
        T_PRIME, T_LAND, LOCK = 18, 30, 14
        half, hold, rebuild, sweep, look = 3, 60, 30 + 40, False, (0, -2)
    elif take == "P2":
        T_PRIME, T_LAND, LOCK = 40, 56, 14
        half, hold, rebuild, sweep, look = 4, 60, 56 + 40, False, (0, -2)   # J (site): "should rebuild ripple like P1"
    else:
        T_PRIME, T_LAND, LOCK = None, 30, 0
        half, hold, rebuild, sweep, look = 1, 40, None, False, (0, 0)
    holes = set()
    if take == "U1":
        trench = [(dx, iy) for iy in range(-2, 4) for dx in (-1, 0, 1)]
        holes = set(trench)
    else:
        holes = {(dx, dy) for dx in range(-half, half + 1) for dy in range(-half, half + 1)}
    grid_with_holes(f"FS {take} ground", ox, holes)
    # ---- the path
    for t in range(END + 1):
        side = 0.0
        if take == "P1":
            if t < T_PRIME:
                y, z = 12.0 + (T_PRIME - t) * 1.0, 10.0; p = dict(FLY); glow = 7.0
            elif t < T_LAND:
                u = (t - T_PRIME) / (T_LAND - T_PRIME)
                y, z = 12.0 * (1 - u), 10.0 * (1 - u ** 1.3)
                p = mixp(FLY, DIVEF, smooth(min(1, (t - T_PRIME) / 3)))     # locked into the dive at once
                if t >= T_LAND - 3:
                    p = mixp(DIVEF, PRESLAM, smooth((t - (T_LAND - 3)) / 3))
                glow = 10 + 8 * u
            else:
                y, z = 0.0, 0.0
        elif take == "P2":
            if t < 6:
                y, z = 6.0, 0.0; p = mixp(STAND, CROUCH, smooth(t / 6)); p["grounded"] = True; glow = 4.0
            elif t < 30:
                u = (t - 6) / 24; y, z = 6.0 - 3.0 * u, 24.0 * (1 - (1 - u) ** 2)
                p = mixp(CROUCH, TUCK, smooth(min(1, (t - 6) / 6))); glow = 6.0
            elif t < T_PRIME:
                u = (t - 30) / (T_PRIME - 30); y, z = 3.0 - 1.0 * u, 24.0 - 3.0 * u * u
                p = dict(TUCK); glow = 6.0
            elif t < T_LAND:
                u = (t - T_PRIME) / (T_LAND - T_PRIME); y, z = 2.0 * (1 - u), 21.0 * (1 - u * u)
                p = mixp(TUCK, HEADDOWN, smooth(min(1, (t - T_PRIME) / 3)))   # crouch: locked head-down at once
                if t >= T_LAND - 3:
                    p = mixp(HEADDOWN, PRESLAM, smooth((t - (T_LAND - 3)) / 3))
                glow = 10 + 8 * u
            else:
                y, z = 0.0, 0.0
        else:
            if t < T_LAND:
                y, z = 3.0 + (T_LAND - t) * 1.0, 3.0 * min(1, (T_LAND - t) / 10.0)
                p = dict(FLY) if t < T_LAND - 6 else mixp(FLY, SLIDE, smooth((t - (T_LAND - 6)) / 6)); glow = 7.0
            elif t < T_LAND + 12:
                u = (t - T_LAND) / 12; y, z = 3.0 - 5.0 * (1 - (1 - u) ** 2), -1.0
                p = dict(SLIDE); p["grounded"] = True; glow = 9.0
            else:
                y, z = -2.0, -1.0
        if t >= T_LAND and take != "U1":
            k = t - T_LAND
            if k <= 3:
                p = mixp(PRESLAM, SLAM, smooth(k / 3)); glow = 26 - 3 * k
            elif k <= LOCK:
                p = dict(SLAM); glow = 12.0
            elif t < rebuild - 4:
                p = mixp(SLAM, STAND, smooth(min(1, (k - LOCK) / 8))); glow = 6.0
            elif t < rebuild + 20:
                p = mixp(STAND, AIMDOWN, smooth(min(1, (t - (rebuild - 4)) / 4))); glow = 12.0 if t >= rebuild else 6.0
            else:
                p = mixp(AIMDOWN, STAND, smooth(min(1, (t - (rebuild + 20)) / 6))); glow = 5.0
            p["grounded"] = True
        if take == "U1" and t >= T_LAND + 12:
            p = mixp(SLIDE, STAND, smooth(min(1, (t - T_LAND - 12) / 10))); p["grounded"] = True; glow = 5.0
        origin = np.array([ox, y, TOP + z])
        if t >= T_LAND and take != "U1":
            origin = np.array([ox, 0.0, TOP])                     # standing on the held landing block
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1, side=side)
        mover.location = tuple(origin); mover.keyframe_insert("location", frame=t + 1)
        sk = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        sk.default_value = glow; sk.keyframe_insert("default_value", frame=t + 1)
        ticks.append({"forward": round(float(y), 3), "up": round(float(z), 3), "glow": round(float(glow), 2),
                      "parts": {kk: {"rot": [round(float(q), 4) for q in sol[kk][0]],
                                     "offset_px": [round(float(q), 3) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    info = {"name": name, "prime_tick": T_PRIME, "touchdown_tick": T_LAND, "lock_ticks": LOCK, "ticks": ticks}
    f_hit = T_LAND + 1
    if take != "U1":
        cells, rim = crater_instant(f"FS {take} crater", ox, 0, half, f_hit, rng, hold, rebuild=rebuild, look=look,
                                    sweep=sweep)
        rim_overlay(f"FS {take}", ox, 0, rim, f_hit, f_hit + hold, rng)
        pulse(f"FS {take} pulse", (ox, 0.0), f_hit, 2 * half + 1, life=10)
        mobs = launch_mobs(f"FS {take}", ox, 0.0, MOBS7 if half == 3 else MOBS9, f_hit, rng, R_=2 * half + 1, half=half)
        info.update(crater=f"{2 * half + 1}x{2 * half + 1}", opened_tick_after_touchdown=1, construct_hold_ticks=hold,
                    rebuild_click_tick_after_touchdown=rebuild - T_LAND, rebuild="ripple from look, 1 tick a block"
                    if not sweep else "follows the crosshair sweep, 2 ticks a column", cells=cells, mobs=mobs)
        cam(f"Cam {take} top", (ox + 0.0, 9.0, 16.0), (ox, -1.0, 0.0), 30)
    else:
        # the slide trench: each block lights as you reach it, opens 2 ticks later; lining spreads one block out
        cells = []
        for (dx, iy) in sorted(trench, key=lambda c: -c[1]):
            reach = T_LAND + int(round(12 * (1 - math.sqrt(max(0.0, 1 - (3.0 - iy) / 5.0)))))
            top = cell(f"FS U1 top {dx} {iy}", (ox + dx, iy, 0.5)); flr = cell(f"FS U1 floor {dx} {iy}", (ox + dx, iy, -0.5), FLOOR)
            key_prop(top, "cx", 0.0, 1); key_prop(top, "cx", 0.0, reach - 1); key_prop(top, "cx", 1.0, reach)
            key_obj(top, 1, sc=0.999); key_obj(top, reach + 1, sc=0.999); key_obj(top, reach + 2, sc=0.0001)
            pixel_burst(f"FS U1 c{dx}{iy}", (ox + dx, iy, 0.6), reach + 2, rng, n=4, drift=(0.06 * dx, -0.05, 0))
            key_prop(flr, "cx", 0.0, 1); key_prop(flr, "cx", 0.0, reach + 1); key_prop(flr, "cx", 1.0, reach + 2)
            key_prop(flr, "cx", 1.0, reach + 2 + hold); key_prop(flr, "cx", 0.0, reach + 6 + hold)
            pixel_burst(f"FS U1 d{dx}{iy}", (ox + dx, iy, -0.2), reach + 2 + hold, rng, n=3)
            cells.append({"dx": dx, "forward": iy, "lit": reach - T_LAND, "opened": reach + 2 - T_LAND,
                          "dissolved": reach + 2 + hold - T_LAND})
        # lining spreading one block out all round the trench
        ring_ = {(dx, iy) for dx in range(-2, 3) for iy in range(-3, 5)} - set(trench)
        for (dx, iy) in ring_:
            o = cell(f"FS U1 rim {dx} {iy}", (ox + dx, iy, 0.5)); o.scale = (1.002, 1.002, 1.002)
            near = min(range(-2, 4), key=lambda yy: abs(yy - iy))
            reach = T_LAND + int(round(12 * (1 - math.sqrt(max(0.0, 1 - (3.0 - near) / 5.0))))) + 3
            key_prop(o, "cx", 1.0, 1); key_obj(o, 1, sc=0.0001); key_obj(o, reach, sc=0.0001)
            key_obj(o, reach + 2, sc=1.002); key_obj(o, reach + 2 + hold, sc=1.002); key_obj(o, reach + 6 + hold, sc=0.0001)
        launch_mobs("FS U1", ox, 0.0, [(-60, 2.5), (0, 3.5), (60, 2.5)], T_LAND + 6, rng, k_out=0.7, k_up=0.45, R_=4, half=1)
        info.update(slide_blocks=5, slide_ticks=12, trench="3 wide, 6 long", construct_hold_ticks=hold, cells=cells)
        cam(f"Cam {take} top", (ox + 0.0, 10.0, 14.0), (ox, 0.0, 0.0), 30)
    dump["takes"][take] = info
    cu = bpy.data.curves.new("FS label " + take, "FONT"); cu.body = f"{take}  {name}"; cu.size = 0.45
    cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FS label " + take, cu)); tl.location = (ox, -GRID + 1.0, TOP + 0.01)
    tl.data.materials.append(LABEL)
    st = np.array([ox, ticks[0]["forward"], TOP + ticks[0]["up"]])
    c = cam(f"Cam {take}", (ox - 1.1, st[1] + 4.6, st[2] + 2.4), (ox + 0.1, st[1] - 5.0, st[2] - 1.2), 30)
    c.parent = mover; c.matrix_parent_inverse = Matrix.Translation(tuple(st)).inverted()
    cam(f"Cam {take} side", (ox + 18.0, 4.0, 8.0), (ox, 2.0, 3.0), 26)
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "primed_slam_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE_W, 0, -1.02))
g = bpy.context.active_object
for c_ in g.users_collection:
    c_.objects.unlink(g)
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
scene.camera = bpy.data.objects["Cam P1"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
