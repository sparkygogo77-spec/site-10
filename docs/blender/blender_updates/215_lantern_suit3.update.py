# Pass 215: lantern suit, round 3 (lead Blender chat, 2026-10-14). J: "mix my picked textures, try every variation you
# can between these"; mask "just the band over the eyes and white eyes"; forming "feet first upward".
# The suit is a dark undersuit with a hard-light shell over it, both built on the player's boxes. Five of J's picked
# construct looks (frame 1 of each animated strip): H1 neon hex, X3D1 glass aura, BR1 emerald, BR1 jade, W1 neon.
# A 5 x 5 grid: the ROW is the shell (body, arms, legs), the COLUMN is the accent (stripes down the arms and legs,
# chest panel, belt, gloves, boots, shoulder caps). The diagonal is one look all over. Every suit wears the same mask:
# a black band round the head across the eyes, with white eyes, and a glowing emblem on the chest.
# All 25 form together, feet first upward, with a bright line at the forming edge (frames 1-34), hold, and loop.
# Cameras "Cam grid" (front), "Cam <shell> + <accent>" for each suit (front three-quarter), "Cam row <shell>".
# Textures from LanternLive\suit_tex\ (packed into the saved file). Builds LanternLive\lantern_suit3.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "lantern_suit3.blend")
TEXDIR = os.path.join(FOLDER, "suit_tex")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Lantern Suit 3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Lantern Suit 3")
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



LOOKS = [("H1", "h1_neon", "H1 neon hex"), ("X3D1", "green_x3d1_emerald", "X3D1 glass"), ("BRE", "br1_emerald", "BR1 emerald"),
         ("BRJ", "br1_jade", "BR1 jade"), ("W1", "w1_neon", "W1 neon")]
TILE = 32.0                 # model px per texture tile (2 blocks)
FORM_END, LOOP = 34, 110

# ------------------------------------------------------------------ the forming height, shared by every suit material
form = bpy.data.node_groups.new("Suit forming", "ShaderNodeTree")
form.interface.new_socket("Height", in_out="OUTPUT", socket_type="NodeSocketFloat")
fv = form.nodes.new("ShaderNodeValue"); fo = form.nodes.new("NodeGroupOutput")
form.links.new(fv.outputs[0], fo.inputs[0])
for f, h in ((1, -0.05), (FORM_END, 2.15), (LOOP - 10, 2.15), (LOOP - 9, -0.05)):
    fv.outputs[0].default_value = h
    fv.outputs[0].keyframe_insert("default_value", frame=f)


def suit_mat(name, image=None, rgb=(0.02, 0.12, 0.06), emit=0.0, alpha_tex=True, solid=False):
    """A suit surface that only exists below the forming height, with a bright band at the edge."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF"); out = N.get("Material Output")
    p.inputs["Roughness"].default_value = 0.35
    g = N.new("ShaderNodeGroup"); g.node_tree = form
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    below = N.new("ShaderNodeMath"); below.operation = "LESS_THAN"
    L.new(sep.outputs["Z"], below.inputs[0]); L.new(g.outputs[0], below.inputs[1])
    dz = N.new("ShaderNodeMath"); dz.operation = "SUBTRACT"; L.new(sep.outputs["Z"], dz.inputs[0]); L.new(g.outputs[0], dz.inputs[1])
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(dz.outputs[0], ab.inputs[0])
    band = N.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.0; band.inputs["From Max"].default_value = 0.05
    band.inputs["To Min"].default_value = 1.0; band.inputs["To Max"].default_value = 0.0; L.new(ab.outputs[0], band.inputs["Value"])
    if image is not None:
        t = N.new("ShaderNodeTexImage"); t.image = image; t.interpolation = "Closest"
        uv = N.new("ShaderNodeUVMap"); uv.uv_map = "box"; L.new(uv.outputs["UV"], t.inputs["Vector"])
        L.new(t.outputs["Color"], p.inputs["Base Color"]); L.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emit
        a_src = t.outputs["Alpha"]
    else:
        p.inputs["Base Color"].default_value = (*rgb, 1)
        if emit:
            p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
        a_src = None
    am = N.new("ShaderNodeMath"); am.operation = "MULTIPLY"; L.new(below.outputs[0], am.inputs[0])
    if a_src is not None and alpha_tex:
        a2 = N.new("ShaderNodeMath"); a2.operation = "MAXIMUM"; a2.inputs[1].default_value = 0.0
        L.new(a_src, a2.inputs[0]); L.new(a2.outputs[0], am.inputs[1])
    else:
        am.inputs[1].default_value = 1.0
    # the forming edge: a bright mint band that runs up the body
    edge = N.new("ShaderNodeEmission"); edge.inputs["Color"].default_value = (0.5, 1.0, 0.65, 1)
    L.new(band.outputs["Result"], edge.inputs["Strength"])
    es = N.new("ShaderNodeMath"); es.operation = "MULTIPLY"; L.new(band.outputs["Result"], es.inputs[0]); es.inputs[1].default_value = 12.0
    L.new(es.outputs[0], edge.inputs["Strength"])
    add = N.new("ShaderNodeAddShader"); L.new(p.outputs[0], add.inputs[0]); L.new(edge.outputs[0], add.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    L.new(am.outputs[0], mix.inputs["Fac"]); L.new(tr.outputs[0], mix.inputs[1]); L.new(add.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED" if not solid else "DITHERED"
    except Exception:
        pass
    return m


def load_img(key):
    im = bpy.data.images.get("suit " + key)
    if im is None:
        im = bpy.data.images.load(os.path.join(TEXDIR, key + ".png")); im.name = "suit " + key
        try:
            im.pack()
        except Exception:
            pass
    return im


SHELL = {k: suit_mat(f"Suit shell {k}", load_img(f), emit=1.2) for k, f, _ in LOOKS}
ACCENT = {k: suit_mat(f"Suit accent {k}", load_img(f), emit=2.2) for k, f, _ in LOOKS}
UNDER = suit_mat("Suit undersuit", None, (0.015, 0.07, 0.035), solid=True)
MASK = suit_mat("Suit mask band", None, (0.01, 0.012, 0.012), solid=True)
EYES = suit_mat("Suit eyes", None, (1.0, 1.0, 1.0), emit=4.0, solid=True)
EMBLEM = suit_mat("Suit emblem", None, (0.3, 1.0, 0.45), emit=8.0, solid=True)


def uv_box_mesh(name, a, b, m):
    """A box in model px with box-projected UVs (TILE px per texture tile), so the pattern keeps square pixels."""
    a = np.array(a, float); b = np.array(b, float)
    pts = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    axes = [(1, 2), (1, 2), (0, 2), (0, 2), (0, 1), (0, 1)]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(A @ p / 16.0) for p in pts], [], faces); me.update()
    uvl = me.uv_layers.new(name="box")
    i = 0
    for fi, poly in enumerate(me.polygons):
        u, v = axes[fi]
        for li in poly.loop_indices:
            pv = pts[me.loops[li].vertex_index]
            uvl.data[li].uv = (pv[u] / TILE, -pv[v] / TILE)
    me.materials.append(m)
    return me


def child_box(parent, name, a, b, m, inflate=0.0):
    a = np.array(a, float) - inflate; b = np.array(b, float) + inflate
    o = link(bpy.data.objects.new(name, uv_box_mesh(name, a, b, m))); o.parent = parent
    return o


STANCE = dict(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(-0.08, 0, 0.12), free=(0.05, 0, -0.1),
              ringleg=(0.0, 0, 0.04), freeleg=(0.0, 0, -0.04))


def dress(objs, tag, shell, accent):
    S, Ac = SHELL[shell], ACCENT[accent]
    for part in ("body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin"):
        a, b = BOX[part]
        child_box(objs[part], f"{tag} under {part}", a, b, UNDER, 0.12)
        child_box(objs[part], f"{tag} shell {part}", a, b, S, 0.28)
    # accents: stripes down the outer arms and legs, gloves, boots, belt, chest panel, shoulder caps
    child_box(objs["rarm"], f"{tag} stripe r", (-3, -2, -0.6), (-3, 10, 0.6), Ac, 0.4)
    child_box(objs["larm"], f"{tag} stripe l", (3, -2, -0.6), (3, 10, 0.6), Ac, 0.4)
    child_box(objs["rarm"], f"{tag} glove r", (-3, 7.2, -2), (1, 10, 2), Ac, 0.36)
    child_box(objs["larm"], f"{tag} glove l", (-1, 7.2, -2), (3, 10, 2), Ac, 0.36)
    child_box(objs["rarm"], f"{tag} cap r", (-3, -2, -2), (1, 0.5, 2), Ac, 0.42)
    child_box(objs["larm"], f"{tag} cap l", (-1, -2, -2), (3, 0.5, 2), Ac, 0.42)
    child_box(objs["rleg"], f"{tag} legstripe r", (-2, 0, -0.6), (-2, 6, 0.6), Ac, 0.4)
    child_box(objs["lleg"], f"{tag} legstripe l", (2, 0, -0.6), (2, 6, 0.6), Ac, 0.4)
    child_box(objs["rshin"], f"{tag} shinstripe r", (-2, 0, -0.6), (-2, 3.5, 0.6), Ac, 0.4)
    child_box(objs["lshin"], f"{tag} shinstripe l", (2, 0, -0.6), (2, 3.5, 0.6), Ac, 0.4)
    child_box(objs["rshin"], f"{tag} boot r", (-2, 3.5, -2), (2, 6, 2), Ac, 0.36)
    child_box(objs["lshin"], f"{tag} boot l", (-2, 3.5, -2), (2, 6, 2), Ac, 0.36)
    child_box(objs["body"], f"{tag} belt", (-4, 10.6, -2), (4, 12, 2), Ac, 0.4)
    child_box(objs["body"], f"{tag} panel", (-2.5, 1.5, -2), (2.5, 9.5, -2), Ac, 0.36)
    # the emblem: a glowing ring on the chest panel
    for (a, b) in (((-1.5, 3.0, -2.75), (1.5, 3.6, -2.55)), ((-1.5, 6.4, -2.75), (1.5, 7.0, -2.55)),
                   ((-1.5, 3.0, -2.75), (-0.9, 7.0, -2.55)), ((0.9, 3.0, -2.75), (1.5, 7.0, -2.55))):
        child_box(objs["body"], f"{tag} emblem", a, b, EMBLEM)
    # the mask: a black band round the head across the eyes, white eyes
    child_box(objs["head"], f"{tag} mask", (-4, -5.4, -4), (4, -3.0, 4), MASK, 0.08)
    child_box(objs["head"], f"{tag} eye r", (-3.0, -4.7, -4.2), (-1.0, -3.7, -4.12), EYES)
    child_box(objs["head"], f"{tag} eye l", (1.0, -4.7, -4.2), (3.0, -3.7, -4.12), EYES)


SPX, SPY = 1.6, 2.4
cams = {}
for i, (sk, _, sname) in enumerate(LOOKS):
    for j, (ak, _, aname) in enumerate(LOOKS):
        tag = f"S3 {sk}+{ak}"
        origin = np.array([j * SPX, -i * SPY, 0.0])
        objs = make_player(tag)
        sol = solve(STANCE)
        set_pose(objs, sol, origin, 1)
        dress(objs, tag, sk, ak)
        name = sname if sk == ak else f"{sname} + {aname}"
        cams[(sk, ak)] = cam(f"Cam {name}", tuple(origin + np.array([1.7, -4.2, 1.45])), tuple(origin + np.array([0, 0, 1.0])), 45)
    cu = bpy.data.curves.new("S3 row " + sk, "FONT"); cu.body = sname; cu.size = 0.3; cu.align_x = "RIGHT"
    tl = link(bpy.data.objects.new("S3 row label " + sk, cu)); tl.location = (-0.8, -i * SPY, 1.0); tl.rotation_euler = (R(90), 0, 0)
    tl.data.materials.append(suit_mat("S3 label", None, (0.85, 1.0, 0.9), emit=2.0, solid=True))
    cam(f"Cam row {sname}", (3.2, -i * SPY - 7.5, 1.6), (3.2, -i * SPY, 1.0), 40)
for j, (ak, _, aname) in enumerate(LOOKS):
    cu = bpy.data.curves.new("S3 col " + ak, "FONT"); cu.body = "accent: " + aname; cu.size = 0.2; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("S3 col label " + ak, cu)); tl.location = (j * SPX, 0.6, 2.35); tl.rotation_euler = (R(90), 0, 0)
    tl.data.materials.append(bpy.data.materials["S3 label"])
cams["grid"] = cam("Cam grid", (3.2, -26, 9), (3.2, -4.8, 1.0), 35)

scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=60, location=(3.2, -5, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "S3 floor"; g.data.materials.append(suit_mat("S3 floor", None, (0.05, 0.055, 0.06), solid=True))
world = bpy.data.worlds.new("S3 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.045, 1)
scene.world = world
key = bpy.data.lights.new("S3 key", "AREA"); key.energy = 1500; key.size = 12
ko = link(bpy.data.objects.new("S3 key", key)); ko.location = (3.2, -12, 8); ko.rotation_euler = (R(50), 0, 0)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = cams["grid"]
scene.frame_set(60)
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
