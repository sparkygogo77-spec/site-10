# Pass 813: corps suits - the armour designs in Red, Yellow, Violet, Blue and Orange (Chat C, 2026-10-15, range 800-899).
# J picked "corps suits (the armour designs in Red, Yellow, Violet, Blue and Orange textures)". Same builds as pass 594
# (one animated texture per suit, KEEP: A2+ Heavy intricate - oversized pauldrons, thick breastplate, big gauntlets,
# knee guards, greaves, ridges, glowing seams, rivets, collar, buckle, knuckles, shoulder trim; band mask, white eyes,
# square emblem), now in each corps' own textures from the texture library, with the undersuit, emblem and ring in
# that corps' colour:
#   A1 Plates in the corps' H1 hex     A2++ Heavy enhanced in its BR1 bricks     A4 Knight in its W1 weave
# One row per corps (Red, Yellow, Violet, Blue, Orange), three suits each. Forms from the ring as before.
# Cameras "Cam row <corps>" (+ " back"), per suit "Cam <corps> <design>" (+ " shoulder", " back"), "Cam grid".
# Builds LanternLive\suit\corps_suits.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "suit", "corps_suits.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
TEXDIR = os.path.join(FOLDER, "suit_tex")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Corps Suits")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Corps Suits")
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
STRIPS = [("W1", "w1_neon", "W1 neon weave", 24, 4), ("W1E", "w1_emerald", "W1 emerald weave", 24, 4),
          ("H1", "h1_neon", "H1 neon hex", 24, 4), ("BRJ", "br1_jade", "BR1 jade bricks", 24, 4),
          ("BRE", "br1_emerald", "BR1 emerald bricks", 24, 4)]


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


TEXLIB = os.path.join(FOLDER, "texture_library")
if not os.path.isdir(TEXLIB):
    TEXLIB = os.path.join(os.getcwd(), "docs", "texture_library")
CORPS = {"Red": ("crimson", (1.0, 0.05, 0.08)), "Yellow": ("yellow", (1.0, 0.8, 0.04)), "Violet": ("violet", (0.6, 0.1, 1.0)),
         "Blue": ("blue", (0.08, 0.35, 1.0)), "Orange": ("orange", (1.0, 0.4, 0.03))}


def lib_strip(lib, look):
    nm = f"construct_{look}_{lib}.png"
    im = bpy.data.images.get(nm)
    if im is None:
        im = bpy.data.images.load(os.path.join(TEXLIB, lib, look, nm))
        try:
            im.pack()
        except Exception:
            pass
    return im


ARMOR, SEAM = {}, {}
for _c, (_lib, _rgb) in CORPS.items():
    for _look in ("h1", "br1", "w1"):
        _im = lib_strip(_lib, _look); _n = max(1, _im.size[1] // _im.size[0])
        ARMOR[(_c, _look)] = strip_mat(f"Suit armour {_c} {_look}", _im, _n, 4, 1.2)
        SEAM[(_c, _look)] = strip_mat(f"Suit seam {_c} {_look}", _im, _n, 4, 4.5)


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


def detailed(objs, tag, T, Sm):
    """A plate with ridges on its top and bottom edges, a glowing seam across the middle and rivets on its front."""
    def make(part, nm, a, b, inf):
        a = np.array(a, float); b = np.array(b, float)
        child_box(objs[part], f"{tag} {nm}", a, b, T, inf)
        h = b[1] - a[1]
        if h >= 2.0:
            r = min(0.55, h * 0.16)
            child_box(objs[part], f"{tag} {nm} ridge t", (a[0], a[1], a[2]), (b[0], a[1] + r, b[2]), T, inf + 0.2)
            child_box(objs[part], f"{tag} {nm} ridge b", (a[0], b[1] - r, a[2]), (b[0], b[1], b[2]), T, inf + 0.2)
            ym = (a[1] + b[1]) / 2
            child_box(objs[part], f"{tag} {nm} seam", (a[0], ym - 0.14, a[2]), (b[0], ym + 0.14, b[2]), Sm, inf + 0.06)
        w = b[0] - a[0]
        if w >= 2.5 and h >= 2.5:
            for xx in (a[0] + 0.55, b[0] - 0.95):
                for yy in (a[1] + 0.75, b[1] - 1.15):
                    child_box(objs[part], f"{tag} {nm} rivet", (xx, yy, a[2] - inf - 0.32), (xx + 0.4, yy + 0.4, a[2] - inf),
                              Sm)
    return make


def extras(objs, tag, d, T, Sm, box):
    """Per-design intricate extras."""
    box("body", "collar", (-3.0, -1.0, -2.3), (3.0, 0.6, 2.3), 0.35)
    box("body", "belt", (-4, 10.7, -2), (4, 12, 2), 0.55)
    child_box(objs["body"], f"{tag} buckle", (-1.0, 10.6, -2.9), (1.0, 12.1, -2.5), Sm)
    for part in ("rarm", "larm"):
        x0, x1 = arm_x(part)
        child_box(objs[part], f"{tag} knuckles {part}", (x0 - 0.2, 8.8, -2.9), (x1 + 0.2, 9.8, -2.2), T, 0.2)
        if d in ("A2", "A4", "A5"):
            o0, o1 = out_in(part, 1.6 if d == "A5" else 1.2)
            child_box(objs[part], f"{tag} trim {part}", (o0, 1.4, -2.9), (o1, 2.0, 2.9), Sm, 0.3)
    if d in ("A1", "A3"):
        for part in ("rshin", "lshin"):
            child_box(objs[part], f"{tag} kneecap {part}", (-1.2, -0.8, -2.9), (1.2, 0.8, -2.0), T, 0.25)
    if d == "A5":
        child_box(objs["body"], f"{tag} chest ridge", (-0.5, -0.4, -4.4), (0.5, 7.0, -3.6), Sm, 0.2)


def dress(objs, tag, d, T, fine=False, Sm=None):
    for part in ("body",) + LIMBS:
        a, b = BOX[part]
        child_box(objs[part], f"{tag} under {part}", a, b, UNDER, 0.12)
    box = (detailed(objs, tag, T, Sm) if fine else
           (lambda part, nm, a, b, inf: child_box(objs[part], f"{tag} {nm}", a, b, T, inf)))
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
    if fine:
        extras(objs, tag, d, T, Sm, lambda part, nm, a, b, inf: child_box(objs[part], f"{tag} {nm}", a, b, T, inf))
        front -= 0.35
    face_marks(objs, tag, front)



# ================================================================== pass 594: enhanced picks + a ton of new designs
def enhance_heavy(objs, tag, T, Sm):
    """A2+ Heavy intricate, a little more (J's pick): two-tier pauldron trims, a raised sternum plate with a glowing
    keel, side rib plates, gauntlet cuffs, small tassets, toe caps, a back plate with glowing vents."""
    cb = lambda part, nm, a, b, m, inf=0.0: child_box(objs[part], f"{tag} {nm}", a, b, m, inf)
    cb("body", "sternum", (-1.6, 0.6, -3.7), (1.6, 6.6, -2.6), T, 0.25)
    cb("body", "keel", (-0.35, 0.8, -4.2), (0.35, 2.2, -3.7), Sm, 0.1)
    for sx in (-1, 1):
        x0, x1 = (-4.6, -3.6) if sx < 0 else (3.6, 4.6)
        for k, y in enumerate((1.2, 3.4, 5.6)):
            cb("body", f"rib {sx} {k}", (x0, y, -2.0), (x1, y + 1.4, 2.0), T, 0.2)
    cb("body", "backplate", (-3.4, 0.6, 2.4), (3.4, 9.4, 3.2), T, 0.25)
    for k, y in enumerate((2.0, 4.2, 6.4)):
        cb("body", f"vent {k}", (-2.4, y, 3.4), (2.4, y + 0.5, 3.6), Sm)
    for part in ("rarm", "larm"):
        o0, o1 = out_in(part, 1.5)
        cb(part, "tier2 " + part, (o0, 2.1, -3.0), (o1, 2.7, 3.0), Sm, 0.3)
        o0, o1 = out_in(part, 0.9, 0.5)
        cb(part, "cuff " + part, (o0, 4.7, -2.9), (o1, 5.4, 2.9), T, 0.4)
    for part in ("rleg", "lleg"):
        cb(part, "tasset " + part, (-2.4, -0.4, -2.9), (2.4, 1.6, -1.6), T, 0.3)
    for part in ("rshin", "lshin"):
        cb(part, "toe " + part, (-2.2, 5.0, -4.1), (2.2, 6.0, -3.2), Sm, 0.1)


def new_design(objs, tag, d, T, Sm):
    """Each new design once, intricate plates (ridges, glowing seam, rivets) in one texture."""
    for part in ("body",) + LIMBS:
        a, b = BOX[part]
        child_box(objs[part], f"{tag} under {part}", a, b, UNDER, 0.12)
    box = detailed(objs, tag, T, Sm)
    plain = lambda part, nm, a, b, inf, m=None: child_box(objs[part], f"{tag} {nm}", a, b, m or T, inf)
    front = -2.75
    AX = arm_x
    if d == "N1":      # Sentinel: high collar, stepped round pauldrons (three shrinking tiers), full greaves
        plain("body", "collar", (-3.6, -1.6, -2.6), (3.6, 1.0, 2.6), 0.4)
        box("body", "chest", (-4, 0.8, -2), (4, 7.2, 2), 0.5)
        box("body", "abs", (-3.2, 7.6, -2), (3.2, 10.6, 2), 0.45)
        for part in ("rarm", "larm"):
            for k, (o, y0, y1) in enumerate(((1.6, -2.6, -0.6), (1.1, -0.6, 1.2), (0.6, 1.2, 2.8))):
                x0, x1 = out_in(part, o)
                plain(part, f"tier{k} {part}", (x0, y0, -2.6 + 0.3 * k), (x1, y1, 2.6 - 0.3 * k), 0.4)
            box(part, "fore " + part, (*AX(part)[:1], 5.0, -2), (AX(part)[1], 9.6, 2), 0.5)
        for part in ("rleg", "lleg", "rshin", "lshin"):
            box(part, "greave " + part, (-2, 0.3, -2), (2, 5.7, 2), 0.45)
        front -= 0.4
    elif d == "N2":    # Ranger: asymmetric, one huge pauldron on the ring arm, light free arm, chest strap
        x0, x1 = out_in("rarm", 2.2)
        box("rarm", "great pauldron", (x0, -3.2, -3.0), (x1, 2.4, 3.0), 0.5)
        box("rarm", "great vambrace", (x0 + 1.0, 4.4, -2.6), (x1, 10.0, 2.6), 0.45)
        plain("larm", "light cap", (-1, -2, -2), (3, 0.4, 2), 0.35)
        plain("larm", "bracer", (-1, 6.4, -2), (3, 8.4, 2), 0.35)
        for k in range(7):
            plain("body", f"strap {k}", (-3.6 + k * 1.05, 0.2 + k * 1.3, -2), (-2.4 + k * 1.05, 1.6 + k * 1.3, 2), 0.5, Sm)
        box("body", "chest r", (-4, 0.5, -2), (0, 5.5, 2), 0.45)
        for part in ("rleg", "lleg"):
            plain(part, "kneepad " + part, (-1.5, 4.4, -2.7), (1.5, 6.4, -1.4), 0.35)
        for part in ("rshin", "lshin"):
            box(part, "shin " + part, (-2, 0.8, -2), (2, 5.0, 2), 0.4)
    elif d == "N3":    # Vanguard: a tower shield plate on the free forearm, heavy ring gauntlet
        plain("larm", "shield", (3.0, 0.5, -3.6), (4.6, 11.0, 3.6), 0.2)
        plain("larm", "shield boss", (4.6, 4.0, -1.2), (5.2, 7.0, 1.2), 0.1, Sm)
        g0, g1 = out_in("rarm", 1.0, 0.5)
        box("rarm", "gauntlet", (g0, 4.6, -2.8), (g1, 10.4, 2.8), 0.45)
        box("rarm", "cap", (*out_in("rarm", 1.0)[:1], -2.4, -2.6), (out_in("rarm", 1.0)[1], 1.6, 2.6), 0.45)
        box("body", "breast", (-4, 0.0, -2.4), (4, 7.4, 2.2), 0.5)
        plain("body", "belt", (-4, 10.6, -2), (4, 12, 2), 0.55)
        for part in ("rleg", "lleg", "rshin", "lshin"):
            box(part, "plate " + part, (-2, 0.4, -2), (2, 5.6, 2), 0.45)
    elif d == "N4":    # Warden: long back plates hanging like a cape, mantle over the shoulders
        plain("body", "mantle", (-4.6, -0.8, -2.6), (4.6, 1.4, 2.6), 0.45)
        for k, x in enumerate((-3.6, -1.2, 1.2)):
            plain("body", f"cape {k}", (x, 1.0, 2.4), (x + 2.4, 12.0 + 0.8 * (k == 1), 3.0), 0.2)
        for part in ("rleg", "lleg"):
            plain(part, "cape low " + part, (-2.2, 0.0, 2.8), (2.2, 5.6, 3.3), 0.15)
        box("body", "chest", (-3.6, 1.0, -2), (3.6, 7.0, 2), 0.45)
        for part in ("rarm", "larm"):
            box(part, "cap " + part, (*out_in(part, 0.8)[:1], -2.4, -2.4), (out_in(part, 0.8)[1], 1.4, 2.4), 0.45)
            box(part, "fore " + part, (*AX(part)[:1], 5.0, -2), (AX(part)[1], 9.4, 2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "shin " + part, (-2, 0.4, -2), (2, 5.0, 2), 0.45)
    elif d == "N5":    # Paladin: a long tabard panel front and back to the knees, big square pauldrons
        plain("body", "tabard f", (-2.0, 2.0, -2.9), (2.0, 12.0, -2.5), 0.1)
        plain("body", "tabard b", (-2.0, 2.0, 2.5), (2.0, 12.0, 2.9), 0.1)
        for part in ("rleg", "lleg"):
            xs = (-0.1, 2.0) if part == "rleg" else (-2.0, 0.1)
            plain(part, "tabard low f " + part, (xs[0] if part == "lleg" else -2.0, 0.0, -3.0), (xs[1] if part == "rleg" else 2.0, 5.5, -2.6), 0.1)
        plain("body", "tabard trim", (-2.2, 1.6, -3.3), (2.2, 2.3, -2.9), 0.05, Sm)
        box("body", "breast", (-4, 0.0, -2.2), (4, 6.0, 2.2), 0.5)
        for part in ("rarm", "larm"):
            box(part, "pauldron " + part, (*out_in(part, 1.4)[:1], -2.8, -2.8), (out_in(part, 1.4)[1], 1.8, 2.8), 0.5)
            box(part, "fore " + part, (*AX(part)[:1], 5.0, -2), (AX(part)[1], 9.6, 2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-2, 0.4, -2), (2, 5.8, 2), 0.45)
        front = -3.4
    elif d == "N6":    # Striker: light, a V harness on the chest, knee and elbow pads, glowing bands
        for k in range(5):
            for sx in (-1, 1):
                xa = sx * (3.6 - k * 0.75)
                plain("body", f"v {sx}{k}", (min(xa, xa - sx * 1.2), k * 1.4, -2), (max(xa, xa - sx * 1.2), k * 1.4 + 1.5, 2), 0.45)
        plain("body", "waist band", (-4, 9.6, -2), (4, 10.4, 2), 0.4, Sm)
        for part in ("rarm", "larm"):
            plain(part, "elbow " + part, (*AX(part)[:1], 3.4, -2), (AX(part)[1], 5.4, 2), 0.45)
            plain(part, "band " + part, (*AX(part)[:1], 7.0, -2), (AX(part)[1], 7.6, 2), 0.35, Sm)
        for part in ("rshin", "lshin"):
            plain(part, "knee " + part, (-2, -0.6, -2.6), (2, 1.6, 2), 0.45)
            plain(part, "band " + part, (-2, 3.2, -2), (2, 3.8, 2), 0.35, Sm)
    elif d == "N7":    # Juggernaut: everything one size up, slab on slab
        box("body", "breast", (-4.8, -0.6, -3.4), (4.8, 8.0, 3.0), 0.5)
        box("body", "skirt", (-4.8, 8.2, -3.0), (4.8, 12.4, 3.0), 0.5)
        for part in ("rarm", "larm"):
            box(part, "pauldron " + part, (*out_in(part, 2.4, 0.2)[:1], -3.4, -3.4), (out_in(part, 2.4, 0.2)[1], 3.0, 3.4), 0.5)
            box(part, "gauntlet " + part, (*out_in(part, 1.4, 0.8)[:1], 4.0, -3.2), (out_in(part, 1.4, 0.8)[1], 10.8, 3.2), 0.45)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2.8, 0.0, -3.0), (2.8, 5.8, 2.8), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-3.0, 0.0, -3.4), (3.0, 6.2, 3.0), 0.45)
        front = -4.4
    elif d == "N8":    # Crest: a glowing fin spine up the back and along the shoulders, swept plates
        for k in range(6):
            plain("body", f"spine {k}", (-0.4, 10.5 - k * 1.9, 2.6), (0.4, 12.0 - k * 1.9, 3.6 + k * 0.35), 0.1, Sm)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 0.8)
            box(part, "cap " + part, (x0, -2.4, -2.4), (x1, 1.4, 2.4), 0.45)
            for k in range(3):
                fx = (x0 - 0.3, x0 + 0.5) if part == "rarm" else (x1 - 0.5, x1 + 0.3)
                plain(part, f"fin {k} {part}", (fx[0], -3.4 - k * 0.6, -1.6 + k * 1.2), (fx[1], -2.4, -0.6 + k * 1.2), 0.1, Sm)
            box(part, "fore " + part, (x0 + 0.8, 5.0, -2), (x1 - 0.8, 9.6, 2), 0.45)
        box("body", "chest", (-4, 0.4, -2), (4, 7.0, 2), 0.5)
        for part in ("rleg", "lleg", "rshin", "lshin"):
            box(part, "plate " + part, (-2, 0.6, -2), (2, 5.4, 2), 0.45)
    elif d == "N9":    # Monk: a stepped diagonal sash, wrapped forearms and shins (many thin bands), light chest
        for k in range(9):
            plain("body", f"sash {k}", (-4 + k * 0.9, k * 1.3, -2), (-2.6 + k * 0.9, k * 1.3 + 1.5, 2), 0.42, Sm if k % 3 == 1 else T)
        for part in ("rarm", "larm", "rshin", "lshin"):
            y0, y1 = (4.6, 10.0) if part.endswith("arm") else (0.4, 5.6)
            x0, x1 = AX(part) if part.endswith("arm") else (-2, 2)
            k = 0; y = y0
            while y < y1:
                plain(part, f"wrap {k} {part}", (x0, y, -2), (x1, y + 0.6, 2), 0.3 + 0.08 * (k % 2)); y += 0.8; k += 1
        plain("body", "belt", (-4, 10.4, -2), (4, 11.6, 2), 0.45)
    elif d == "N10":   # Sentry: a layered skirt of tassets, banded chest, high pauldrons
        for k, y in enumerate((0.0, 2.2, 4.4, 6.6)):
            box("body", f"band {k}", (-4, y, -2), (4, y + 2.0, 2), 0.45)
        plain("body", "belt", (-4, 8.8, -2), (4, 10.2, 2), 0.5, Sm)
        for part in ("rleg", "lleg"):
            for k, y in enumerate((-1.6, 0.6, 2.8)):
                plain(part, f"tasset {k} {part}", (-2.4, y, -2.4), (2.4, y + 2.4, 2.4), 0.3 + 0.1 * k)
        for part in ("rarm", "larm"):
            box(part, "pauldron " + part, (*out_in(part, 1.0)[:1], -3.6, -2.6), (out_in(part, 1.0)[1], 1.0, 2.6), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-2, 0.6, -2), (2, 5.8, 2), 0.45)
    elif d == "N11":   # Spiked: rows of small spikes on the pauldrons, forearms and knees
        box("body", "chest", (-4, 0.4, -2), (4, 7.4, 2), 0.5)
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 1.0)
            box(part, "cap " + part, (x0, -2.4, -2.6), (x1, 1.8, 2.6), 0.45)
            for k in range(3):
                for zz in (-1.6, 0.0, 1.6):
                    sx = x0 - 0.9 if part == "rarm" else x1 + 0.1
                    plain(part, f"spike {k}{zz} {part}", (sx, -1.6 + k * 1.2, zz - 0.3), (sx + 0.8, -1.0 + k * 1.2, zz + 0.3), 0.05, Sm)
            box(part, "fore " + part, (*AX(part)[:1], 5.0, -2), (AX(part)[1], 9.6, 2), 0.45)
            for k in range(3):
                plain(part, f"fspike {k} {part}", (AX(part)[0] + 1.6, 5.6 + k * 1.4, -3.4), (AX(part)[0] + 2.4, 6.2 + k * 1.4, -2.6), 0.05, Sm)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-2, 0.4, -2), (2, 5.6, 2), 0.45)
            plain(part, "knee spike " + part, (-0.4, -0.4, -3.8), (0.4, 0.6, -2.6), 0.05, Sm)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2, 0.4, -2), (2, 5.2, 2), 0.45)
    elif d == "N12":   # Ribcage: horizontal rib bars round the torso with glowing gaps, sternum bar
        for k in range(7):
            plain("body", f"rib {k}", (-4, 0.3 + k * 1.4, -2), (4, 1.2 + k * 1.4, 2), 0.5)
            plain("body", f"gap {k}", (-3.6, 1.2 + k * 1.4, -2), (3.6, 1.7 + k * 1.4, 2), 0.3, Sm)
        plain("body", "sternum", (-0.6, 0.0, -2.9), (0.6, 10.2, -2.4), 0.1)
        for part in ("rarm", "larm"):
            for k in range(4):
                plain(part, f"rib {k} {part}", (*AX(part)[:1], -1.6 + k * 2.6, -2), (AX(part)[1], -0.6 + k * 2.6, 2), 0.45)
        for part in ("rleg", "lleg", "rshin", "lshin"):
            for k in range(3):
                plain(part, f"rib {k} {part}", (-2, 0.4 + k * 2.0, -2), (2, 1.4 + k * 2.0, 2), 0.45)
        front = -3.2
    elif d == "N13":   # Bastion: wide flat rectangular shoulder slabs, a square chest slab, square knee slabs
        for part in ("rarm", "larm"):
            x0, x1 = out_in(part, 2.6, 0.6)
            box(part, "slab " + part, (x0, -2.8, -2.4), (x1, -1.2, 2.4), 0.4)
            plain(part, "slab edge " + part, (x0, -1.2, -2.4), (x1, -0.8, 2.4), 0.4, Sm)
            box(part, "fore " + part, (*AX(part)[:1], 4.8, -2), (AX(part)[1], 9.8, 2), 0.45)
        box("body", "slab", (-4.2, 0.6, -2.9), (4.2, 8.0, 2.2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "knee slab " + part, (-2.4, -1.0, -3.2), (2.4, 2.6, -1.2), 0.4)
            box(part, "shin " + part, (-2, 2.6, -2), (2, 6.0, 2), 0.45)
        for part in ("rleg", "lleg"):
            box(part, "thigh " + part, (-2, 0.4, -2), (2, 4.4, 2), 0.45)
        front = -3.5
    elif d == "N14":   # Gladiator: a banded sleeve on the ring arm only, a belt, greaves, bare-ish rest
        for k in range(6):
            o0, o1 = out_in("rarm", 0.4 + 0.12 * (5 - k))
            plain("rarm", f"manica {k}", (o0, -2.2 + k * 2.0, -2.2), (o1, -0.4 + k * 2.0, 2.2), 0.4)
        x0, x1 = out_in("rarm", 1.2)
        box("rarm", "galerus", (x0, -3.0, -2.6), (x1, 0.6, 2.6), 0.45)
        plain("body", "belt", (-4, 9.4, -2), (4, 11.4, 2), 0.55)
        plain("body", "buckle", (-1.2, 9.2, -3.0), (1.2, 11.6, -2.5), 0.05, Sm)
        plain("body", "strap", (-4, 0.0, -2), (-2.6, 9.4, 2), 0.45)
        for part in ("rshin", "lshin"):
            box(part, "greave " + part, (-2, 0.0, -2.4), (2, 5.6, 2), 0.45)
    elif d == "N15":   # Scout: thin straps, a light chest plate, knee and elbow pads, a glowing belt pouch line
        box("body", "chest", (-3.0, 1.0, -2), (3.0, 5.6, 2), 0.42)
        for sx in (-1, 1):
            plain("body", f"strap {sx}", (sx * 2.4 - 0.4, 0.0, -2), (sx * 2.4 + 0.4, 9.6, 2), 0.46)
        plain("body", "belt", (-4, 9.4, -2), (4, 10.4, 2), 0.45)
        for k, xx in enumerate((-3.4, -1.6, 0.2, 2.0)):
            plain("body", f"pouch {k}", (xx, 9.6, -2.9), (xx + 1.2, 11.0, -2.4), 0.05, Sm)
        for part in ("rarm", "larm"):
            plain(part, "elbow " + part, (*AX(part)[:1], 3.6, -2), (AX(part)[1], 5.4, 2), 0.42)
        for part in ("rshin", "lshin"):
            plain(part, "knee " + part, (-2, -0.6, -2.5), (2, 1.4, 2), 0.42)
        front = -2.75 - 0.42
    extras(objs, tag, "A1" if d in ("N6", "N9", "N14", "N15") else "A2", T, Sm,
           lambda part, nm, a, b, inf: child_box(objs[part], f"{tag} {nm}", a, b, T, inf))
    face_marks(objs, tag, front - 0.35)


NEW = [("N1", "Sentinel"), ("N2", "Ranger"), ("N3", "Vanguard"), ("N4", "Warden"), ("N5", "Paladin"),
       ("N6", "Striker"), ("N7", "Juggernaut"), ("N8", "Crest"), ("N9", "Monk"), ("N10", "Sentry"),
       ("N11", "Spiked"), ("N12", "Ribcage"), ("N13", "Bastion"), ("N14", "Gladiator"), ("N15", "Scout")]
TEXS = [s[0] for s in STRIPS]
SPX, GAP = 2.6, 18.0
cams = {}
LBL = mat("S594 label", (0.85, 1.0, 0.9), emit=2.0)


def place(key, label_txt, sub, gx, j, dressfn):
    origin = np.array([gx + j * SPX, 0.0, 0.0])
    tag = f"S594 {key}"
    objs = make_player(tag)
    set_pose(objs, solve(STANCE), origin, 1)
    dressfn(objs, tag)
    cam(f"Cam {key}", tuple(origin + np.array([1.9, -4.6, 1.5])), tuple(origin + np.array([0, 0, 1.0])), 45)
    cam(f"Cam {key} shoulder", tuple(origin + np.array([0.55, 2.3, 2.15])), tuple(origin + np.array([-0.1, -3.0, 1.0])), 35)
    cam(f"Cam {key} back", tuple(origin + np.array([-1.6, 4.6, 1.5])), tuple(origin + np.array([0, 0, 1.0])), 45)
    for txt, z, sz in ((label_txt, 2.95, 0.18), (sub, 2.65, 0.13)):
        cu = bpy.data.curves.new("S594 l " + key, "FONT"); cu.body = txt; cu.size = sz; cu.align_x = "CENTER"
        tl = link(bpy.data.objects.new("S594 label " + key + txt[:6], cu)); tl.location = (origin[0], 0.6, z)
        tl.rotation_euler = (R(90), 0, 0); tl.data.materials.append(LBL)


DES = [("A1", "Plates", "h1", "H1 hex"), ("A2++", "Heavy enhanced", "br1", "BR1 bricks"), ("A4", "Knight", "w1", "W1 weave")]
groups = []
for g, (cname, (lib, rgb)) in enumerate(CORPS.items()):
    gx = g * GAP
    dark = tuple(c * 0.07 for c in rgb)
    UNDER = suit_mat(f"Suit undersuit {cname}", None, dark, solid=True)
    EMBLEM = suit_mat(f"Suit emblem {cname}", None, rgb, emit=6.0, solid=True)
    RINGM_C = mat(f"KL ring {cname}", rgb, emit=3.0)
    for j, (dk, dname, look, tname) in enumerate(DES):
        T, Sm = ARMOR[(cname, look)], SEAM[(cname, look)]
        if dk == "A1":
            fn = lambda objs, tag, T=T, Sm=Sm: dress(objs, tag, "A1", T, True, Sm)
        elif dk == "A2++":
            fn = lambda objs, tag, T=T, Sm=Sm: (dress(objs, tag, "A2", T, True, Sm), enhance_heavy(objs, tag, T, Sm))
        else:
            fn = lambda objs, tag, T=T, Sm=Sm: dress(objs, tag, "A4", T, True, Sm)
        place(f"{cname} {dk}", f"{cname}  {dk} {dname}", tname, gx, j * 1.6, fn)
        for o in bpy.data.objects:                                # this corps' ring on the hand
            if o.name.startswith(f"KL S594 {cname} {dk}") and o.type == "MESH":
                for k_, ms in enumerate(o.material_slots):
                    if ms.material == RINGM:
                        o.material_slots[k_].material = RINGM_C
                if o.data.materials and o.data.materials[0] == RINGM:
                    o.data.materials[0] = RINGM_C
    groups.append((cname, f"{cname} corps", gx))
    cx = gx + 1.6 * SPX
    cam(f"Cam row {cname}", (cx, -9.5, 2.0), (cx, 0, 1.15), 30)
    cam(f"Cam row {cname} back", (cx, 9.5, 2.0), (cx, 0, 1.15), 30)
MIDX = (len(groups) - 1) * GAP / 2 + 1.6 * SPX


# J: a ring flare marks the end of the forming
_rs = RINGM.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for _f, _e in ((1, 3.0), (FORM_END - 3, 3.0), (FORM_END + 1, 30.0), (FORM_END + 10, 3.0), (LOOP, 3.0)):
    _rs.default_value = _e; _rs.keyframe_insert("default_value", frame=_f)
cams["all"] = cam("Cam grid", (MIDX, -70.0, 12.0), (MIDX, 0.0, 1.2), 40)

scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=300, location=(MIDX, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "S594 floor"; g.data.materials.append(mat("S594 floor", (0.05, 0.055, 0.06), rough=0.8))
world = bpy.data.worlds.new("S594 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.045, 1)
scene.world = world
key = bpy.data.lights.new("S594 key", "AREA"); key.energy = 30000; key.size = 160
ko = link(bpy.data.objects.new("S594 key", key)); ko.location = (MIDX, -14, 9); ko.rotation_euler = (R(50), 0, 0)
rim = bpy.data.lights.new("S594 rim", "AREA"); rim.energy = 12000; rim.size = 160
ro = link(bpy.data.objects.new("S594 rim", rim)); ro.location = (MIDX, 14, 7); ro.rotation_euler = (R(-50), 0, 0)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam row Red"]
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
