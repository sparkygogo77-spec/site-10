# Pass 591: Lantern suit armour, five designs x five textures, one texture per suit, animated (Chat C, 2026-10-14; suits
# are Chat D's area, built here because J asked in this chat). J on 590: "the rest of the models are a poor mismatch of
# textures it should be one single really well defined texture, the armored one here is great, if we can make another
# several designs of armor within the texture like this with other texture types, only use one texture at once, if we
# can make some bigger armor variants then lets try it, I also need it animated".
# KEEP (V3 Plates, word for word): dark undersuit, raised plates on chest, shoulders, forearms, thighs and shins, band
# mask with white eyes, square chest emblem. Each suit wears ONE construct texture, playing as its game strip does
# (24 or 32 frames, frametime 4/5, interpolated), over the plain dark undersuit.
# Rows (designs): A1 Plates (V3), A2 Heavy, A3 Lamellar, A4 Knight, A5 Titan (biggest).
# Columns (texture): W1 neon weave, H1 neon hex, BR1 emerald bricks, BR1 jade bricks, X3D1 emerald glass.
# All 25 form feet first upward (frames 1-34) with the ring flare, hold while the textures play, loop at 200.
# Each design stands in its own group of five (left to right A1..A5). Cameras "Cam grid", "Cam row <design>", per suit "Cam A# <tex>" (front three-quarter) and
# "Cam A# <tex> shoulder". Strips from LanternLive\suit_tex\*_strip.png (packed). Builds LanternLive\suit\suit_armour.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "suit", "suit_armour.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
TEXDIR = os.path.join(FOLDER, "suit_tex")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Suit Armour")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Suit Armour")
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



LOOKS = [("W1", "w1_neon", "W1 neon")]
TILE = 32.0                 # model px per texture tile (2 blocks)
FORM_END, LOOP = 34, 200

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

# ------------------------------------------------------------------ one animated construct texture per suit (J: "only use
# one texture at once", "I also need it animated"). Each strip plays like the game: frame k of N, frametime ft ticks,
# interpolated into the next frame, looping.
STRIPS = [("W1", "w1_neon", "W1 neon weave", 24, 4), ("H1", "h1_neon", "H1 neon hex", 24, 4),
          ("BRE", "br1_emerald", "BR1 emerald bricks", 24, 4), ("BRJ", "br1_jade", "BR1 jade bricks", 24, 4),
          ("X3", "x3d1_emerald", "X3D1 emerald glass", 32, 5)]


def strip_mat(name, image, n, ft, emit):
    m = suit_mat(name, image, emit=emit)
    N, L = m.node_tree.nodes, m.node_tree.links
    t0 = next(nd for nd in N if nd.type == "TEX_IMAGE"); uvn = next(nd for nd in N if nd.type == "UVMAP")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uvn.outputs["UV"], sep.inputs[0])
    fu = N.new("ShaderNodeMath"); fu.operation = "FRACT"; L.new(sep.outputs[0], fu.inputs[0])
    fv = N.new("ShaderNodeMath"); fv.operation = "FRACT"; L.new(sep.outputs[1], fv.inputs[0])
    tick = N.new("ShaderNodeValue"); fc = tick.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"; fc.driver.expression = f"frame/{ft}"
    fl = N.new("ShaderNodeMath"); fl.operation = "FLOOR"; L.new(tick.outputs[0], fl.inputs[0])
    wv = N.new("ShaderNodeMath"); wv.operation = "SUBTRACT"; L.new(tick.outputs[0], wv.inputs[0]); L.new(fl.outputs[0], wv.inputs[1])
    outs = []
    for step, tex in ((0, t0), (1, N.new("ShaderNodeTexImage"))):
        tex.image = image; tex.interpolation = "Closest"
        k = N.new("ShaderNodeMath"); k.operation = "ADD"; k.inputs[1].default_value = step; L.new(fl.outputs[0], k.inputs[0])
        km = N.new("ShaderNodeMath"); km.operation = "FLOORED_MODULO"; km.inputs[1].default_value = n; L.new(k.outputs[0], km.inputs[0])
        # strip frame k sits at v in [1-(k+1)/n, 1-k/n]: v' = (fract(v) + n - 1 - k) / n
        a = N.new("ShaderNodeMath"); a.operation = "SUBTRACT"; a.inputs[0].default_value = n - 1; L.new(km.outputs[0], a.inputs[1])
        b = N.new("ShaderNodeMath"); b.operation = "ADD"; L.new(fv.outputs[0], b.inputs[0]); L.new(a.outputs[0], b.inputs[1])
        c = N.new("ShaderNodeMath"); c.operation = "DIVIDE"; c.inputs[1].default_value = n; L.new(b.outputs[0], c.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(fu.outputs[0], cmb.inputs[0]); L.new(c.outputs[0], cmb.inputs[1])
        L.new(cmb.outputs[0], tex.inputs["Vector"])
        outs.append(tex)
    # crossfade colour and alpha between frame k and k+1 (the game's "interpolate": true)
    mc = N.new("ShaderNodeMix"); mc.data_type = "RGBA"; L.new(wv.outputs[0], mc.inputs["Factor"])
    L.new(outs[0].outputs["Color"], mc.inputs[6]); L.new(outs[1].outputs["Color"], mc.inputs[7])
    ma = N.new("ShaderNodeMix"); ma.data_type = "FLOAT"; L.new(wv.outputs[0], ma.inputs["Factor"])
    olds = [lk.to_socket for lk in L if lk.from_node == outs[0] and lk.from_socket.name == "Alpha"]
    for lk in [lk for lk in L if lk.from_node == outs[0] and lk.from_socket.name == "Alpha"]:
        L.remove(lk)
    L.new(outs[0].outputs["Alpha"], ma.inputs[2]); L.new(outs[1].outputs["Alpha"], ma.inputs[3])
    for to in olds:
        L.new(ma.outputs[0], to)
    p = N.get("Principled BSDF")
    L.new(mc.outputs[2], p.inputs["Base Color"]); L.new(mc.outputs[2], p.inputs["Emission Color"])
    return m


def load_strip(key):
    im = bpy.data.images.get("suit strip " + key)
    if im is None:
        im = bpy.data.images.load(os.path.join(TEXDIR, key + "_strip.png")); im.name = "suit strip " + key
        try:
            im.pack()
        except Exception:
            pass
    return im


ARMOR = {k: strip_mat(f"Suit armour {k}", load_strip(f), n, ft, 1.2) for k, f, _, n, ft in STRIPS}


# ================================================================== pass 591: armour designs, one texture each
# J on 590: "the armored one here is great" (V3 Plates). KEEP word for word: V3's dark undersuit with raised plates on
# chest, shoulders, forearms, thighs and shins, the band mask with white eyes, the square emblem. "make another several
# designs of armor ... only use one texture at once ... bigger armor variants ... animated".
DESIGNS = [("A1", "Plates", "V3 as J picked it"),
           ("A2", "Heavy", "bigger: oversized pauldrons, thick breastplate, big gauntlets, knee guards, greaves"),
           ("A3", "Lamellar", "overlapping bands down the torso, arms and legs, dark gaps between"),
           ("A4", "Knight", "full cuirass, gorget collar, two-tier pauldrons, tassets over the thighs, long sabatons"),
           ("A5", "Titan", "biggest: towering pauldrons with fins, protruding breastplate, huge gauntlets and boots")]
LIMBS = ("rarm", "larm", "rleg", "lleg", "rshin", "lshin")


def face_marks(objs, tag, front=-2.75):
    for (a, b) in (((-1.5, 3.0), (1.5, 3.6)), ((-1.5, 6.4), (1.5, 7.0)), ((-1.5, 3.0), (-0.9, 7.0)), ((0.9, 3.0), (1.5, 7.0))):
        child_box(objs["body"], f"{tag} emblem", (a[0], a[1], front), (b[0], b[1], front + 0.2), EMBLEM)
    child_box(objs["head"], f"{tag} mask", (-4, -5.4, -4), (4, -3.0, 4), MASK, 0.08)
    child_box(objs["head"], f"{tag} eye r", (-3.0, -4.7, -4.2), (-1.0, -3.7, -4.12), EYES)
    child_box(objs["head"], f"{tag} eye l", (1.0, -4.7, -4.2), (3.0, -3.7, -4.12), EYES)


def arm_x(part):
    return (-3, 1) if part == "rarm" else (-1, 3)


def out_in(part, outer, inner=0.0):
    """Widen an arm box outward (away from the body) by `outer` and inward by `inner`."""
    x0, x1 = arm_x(part)
    return (x0 - outer, x1 + inner) if part == "rarm" else (x0 - inner, x1 + outer)


def dress(objs, tag, d, T):
    for part in ("body",) + LIMBS:
        a, b = BOX[part]
        child_box(objs[part], f"{tag} under {part}", a, b, UNDER, 0.12)
    box = lambda part, nm, a, b, inf: child_box(objs[part], f"{tag} {nm}", a, b, T, inf)
    front = -2.75
    if d == "A1":                                             # V3 Plates, unchanged
        P = 0.5
        box("body", "chest", (-3.5, 0.5, -2), (3.5, 6.5, 2), P)
        box("body", "abs", (-3.0, 7.2, -2), (3.0, 10.2, 2), P - 0.1)
        for part in ("rarm", "larm"):
            x0, x1 = arm_x(part)
            box(part, "cap " + part, (x0, -2, -2), (x1, 1.2, 2), P + 0.1)
            box(part, "fore " + part, (x0, 5.0, -2), (x1, 9.0, 2), P)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2, 0.6, -2), (2, 5.2, 2), P)
        for part in ("rshin", "lshin"):
            box(part, "shin " + part, (-2, 0.4, -2), (2, 4.8, 2), P)
    elif d == "A2":                                           # Heavy
        box("body", "breast", (-4, 0.0, -2.6), (4, 7.0, 2.4), 0.5)
        box("body", "abs", (-3.4, 7.4, -2.2), (3.4, 10.4, 2.2), 0.45)
        box("body", "belt", (-4, 10.6, -2), (4, 12, 2), 0.6)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 1.2)
            box(part, "pauldron " + part, (x0, -2.6, -2.8), (x1, 1.8, 2.8), 0.5)
            g0, g1 = out_in(part, 0.7, 0.4)
            box(part, "gauntlet " + part, (g0, 5.2, -2.6), (g1, 10.2, 2.6), 0.4)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2.3, 0.4, -2.3), (2.3, 5.0, 2.3), 0.45)
            box(part, "knee " + part, (-1.6, 4.6, -2.9), (1.6, 6.6, -1.2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-2.4, 0.6, -2.5), (2.4, 4.4, 2.4), 0.45)
            box(part, "boot " + part, (-2.5, 4.4, -3.2), (2.5, 6.0, 2.5), 0.4)
        front = -3.3
    elif d == "A3":                                           # Lamellar bands
        for i, y in enumerate((0.0, 2.3, 4.6, 6.9, 9.2)):
            box("body", f"band{i}", (-4, y, -2), (4, y + 2.0, 2), 0.45 + 0.05 * i)
        for part in ("rarm", "larm"):
            x0, x1 = arm_x(part)
            for i, y in enumerate((-2.0, 0.6, 3.2, 5.8)):
                box(part, f"band{i} {part}", (x0, y, -2), (x1, y + 2.2, 2), 0.5 - 0.04 * i)
        for part in ("rleg", "lleg", "rshin", "lshin"):
            for i, y in enumerate((0.2, 2.3, 4.4) if part.endswith("leg") else (0.2, 2.3)):
                box(part, f"band{i} {part}", (-2, y, -2), (2, y + 1.8, 2), 0.45)
            if part.endswith("shin"):
                box(part, "boot " + part, (-2, 4.3, -2.4), (2, 6, 2), 0.4)
        front = -2.75 - 0.4
    elif d == "A4":                                           # Knight
        box("body", "cuirass", (-4, 0.0, -2), (4, 10.6, 2), 0.6)
        box("body", "gorget", (-3.2, -0.9, -2.4), (3.2, 0.8, 2.4), 0.4)
        box("body", "fauld", (-4.2, 10.6, -2.2), (4.2, 12.0, 2.2), 0.5)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 1.0)
            box(part, "pauldron " + part, (x0, -2.5, -2.6), (x1, 0.8, 2.6), 0.5)
            x0, x1 = out_in(part, 0.6)
            box(part, "pauldron2 " + part, (x0, 0.8, -2.3), (x1, 2.6, 2.3), 0.45)
            box(part, "vambrace " + part, (*arm_x(part)[:1], 5.6, -2), (arm_x(part)[1], 9.4, 2), 0.5)
        for part in ("rleg", "lleg"):
            box(part, "tasset " + part, (-2.3, -0.2, -2.6), (2.3, 3.0, 2.2), 0.4)
            box(part, "cuisse " + part, (-2, 3.0, -2), (2, 5.8, 2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "poleyn " + part, (-1.5, -0.6, -2.8), (1.5, 1.2, -1.4), 0.4)
            box(part, "greave " + part, (-2, 1.2, -2), (2, 4.6, 2), 0.45)
            box(part, "sabaton " + part, (-2.1, 4.6, -3.6), (2.1, 6.0, 2.1), 0.4)
        front = -2.75 - 0.4
    elif d == "A5":                                           # Titan
        box("body", "breast", (-4.4, -0.4, -3.4), (4.4, 7.4, 2.6), 0.5)
        box("body", "spine", (-1.0, 0.0, 2.6), (1.0, 10.0, 3.6), 0.4)
        box("body", "abs", (-3.6, 7.6, -2.6), (3.6, 10.6, 2.4), 0.45)
        box("body", "belt", (-4.4, 10.6, -2.4), (4.4, 12.2, 2.4), 0.5)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 2.0)
            box(part, "pauldron " + part, (x0, -3.6, -3.2), (x1, 2.2, 3.2), 0.5)
            fx = (x0 - 0.2, x0 + 1.0) if part == "rarm" else (x1 - 1.0, x1 + 0.2)
            box(part, "fin " + part, (fx[0], -5.6, -0.6), (fx[1], -3.6, 1.6), 0.35)
            g0, g1 = out_in(part, 1.0, 0.6)
            box(part, "gauntlet " + part, (g0, 4.6, -3.0), (g1, 10.6, 3.0), 0.45)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2.6, 0.0, -2.8), (2.6, 5.4, 2.6), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "knee " + part, (-1.8, -0.8, -3.4), (1.8, 1.6, -1.4), 0.45)
            box(part, "greave " + part, (-2.6, 1.0, -2.8), (2.6, 4.2, 2.6), 0.45)
            box(part, "boot " + part, (-2.8, 4.2, -3.8), (2.8, 6.1, 2.8), 0.4)
        front = -3.4 - 0.75
    face_marks(objs, tag, front)


SPX, GAP = 2.3, 14.0
cams = {}
LBL = suit_mat("S591 label", None, (0.85, 1.0, 0.9), emit=2.0, solid=True)
for i, (dk, dname, _) in enumerate(DESIGNS):
    for j, (tk, _, tname, _, _) in enumerate(STRIPS):
        tag = f"S591 {dk} {tk}"
        origin = np.array([i * GAP + j * SPX, 0.0, 0.0])
        objs = make_player(tag)
        set_pose(objs, solve(STANCE), origin, 1)
        dress(objs, tag, dk, ARMOR[tk])
        cams[(dk, tk)] = cam(f"Cam {dk} {tk}", tuple(origin + np.array([1.9, -4.6, 1.5])), tuple(origin + np.array([0, 0, 1.0])), 45)
        cam(f"Cam {dk} {tk} shoulder", tuple(origin + np.array([0.55, 2.3, 2.15])), tuple(origin + np.array([-0.1, -3.0, 1.0])), 35)
    cu = bpy.data.curves.new("S591 row " + dk, "FONT"); cu.body = f"{dk} {dname}"; cu.size = 0.35; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("S591 row label " + dk, cu)); tl.location = (i * GAP + 2 * SPX, 0.6, 2.9); tl.rotation_euler = (R(90), 0, 0)
    tl.data.materials.append(LBL)
    cam(f"Cam row {dk} {dname}", (i * GAP + 2 * SPX, -13.0, 2.4), (i * GAP + 2 * SPX, 0, 1.1), 32)
for i, (dk, _, _) in enumerate(DESIGNS):
    for j, (tk, _, tname, _, _) in enumerate(STRIPS):
        cu = bpy.data.curves.new(f"S591 col {dk} {tk}", "FONT"); cu.body = tname; cu.size = 0.14; cu.align_x = "CENTER"
        tl = link(bpy.data.objects.new(f"S591 col label {dk} {tk}", cu)); tl.location = (i * GAP + j * SPX, 0.6, 2.45)
        tl.rotation_euler = (R(90), 0, 0); tl.data.materials.append(LBL)
MIDX = 2 * GAP + 2 * SPX


# J: a ring flare marks the end of the forming
_rs = RINGM.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for _f, _e in ((1, 3.0), (FORM_END - 3, 3.0), (FORM_END + 1, 30.0), (FORM_END + 10, 3.0), (LOOP, 3.0)):
    _rs.default_value = _e; _rs.keyframe_insert("default_value", frame=_f)
cams["all"] = cam("Cam grid", (MIDX, -52.0, 9.0), (MIDX, 0.0, 1.2), 50)
cam("Cam grid back", (MIDX, 52.0, 9.0), (MIDX, 0.0, 1.2), 50)

scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=140, location=(MIDX, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "S591 floor"; g.data.materials.append(suit_mat("S591 floor", None, (0.05, 0.055, 0.06), solid=True))
world = bpy.data.worlds.new("S591 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.045, 1)
scene.world = world
key = bpy.data.lights.new("S591 key", "AREA"); key.energy = 6000; key.size = 70
ko = link(bpy.data.objects.new("S591 key", key)); ko.location = (MIDX, -14, 9); ko.rotation_euler = (R(50), 0, 0)
rim = bpy.data.lights.new("S591 rim", "AREA"); rim.energy = 2500; rim.size = 70
ro = link(bpy.data.objects.new("S591 rim", rim)); ro.location = (MIDX, 14, 7); ro.rotation_euler = (R(-50), 0, 0)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = cams["all"]
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
