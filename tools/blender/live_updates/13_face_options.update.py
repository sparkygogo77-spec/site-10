# Pass 13: four construct face options side by side, each its own 4 x 3 wall with a glowing letter
# above it, from J's reference panels:
#   A constellation   B swirl   C crystal cells   D hexagons
# Every face uses the same outline rule (bright outline where the construct ends), see-through jade,
# and the thin smoke skin. A new camera looks at all four; the old jade wall stays behind them.
import os
import bpy
from mathutils import Vector

scene = bpy.context.scene
ROW = Vector((29.0, -9.0, 0.0))      # left end of the row, in front of the old jade wall
WW, WH, GAP = 4, 3, 2
STYLES = [("A", "constellation"), ("B", "swirl"), ("C", "crystal cells"), ("D", "hexagons")]
KINDS = ["plain", "edge", "corner", "strip", "three", "frame"]
TEX_SIDES = {"plain": "", "edge": "L", "corner": "LT", "strip": "LR", "three": "LTR", "frame": "LTRB"}
ROT = {"id": lambda s, t: (s, t), "top": lambda s, t: (1 - t, s),
       "right": lambda s, t: (1 - s, 1 - t), "bottom": lambda s, t: (t, 1 - s)}
LANDS = {"id": {"L": "left", "R": "right", "B": "bottom", "T": "top"},
         "top": {"L": "top", "R": "bottom", "B": "left", "T": "right"},
         "right": {"L": "right", "R": "left", "B": "top", "T": "bottom"},
         "bottom": {"L": "bottom", "R": "top", "B": "right", "T": "left"}}
PICK = {}
for ki, kind in enumerate(KINDS):
    for rot, land in LANDS.items():
        PICK.setdefault(frozenset(land[c] for c in TEX_SIDES[kind]), (ki, rot))
FACES = [((0, -1, 0), (1, 0, 0), (0, 0, 1)), ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
         ((-1, 0, 0), (0, -1, 0), (0, 0, 1)), ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (1, 0, 0), (0, -1, 0))]


def material(style, kind):
    name = f"opt_{style}_{kind}"
    fname = f"{style}_{kind}.png"
    path = os.path.join(FOLDER, fname)
    img = bpy.data.images.get(fname)
    if img is None:
        img = bpy.data.images.load(path)
    else:
        img.filepath = path
        img.reload()
    img.alpha_mode = "STRAIGHT"
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    tex = N.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    L.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.04
    bw = N.new("ShaderNodeRGBToBW")
    L.new(tex.outputs["Color"], bw.inputs[0])
    p = N.new("ShaderNodeMath"); p.operation = "POWER"; p.inputs[1].default_value = 2.2
    L.new(bw.outputs[0], p.inputs[0])
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY_ADD"
    k.inputs[1].default_value = 6.0
    k.inputs[2].default_value = 0.45
    L.new(p.outputs[0], k.inputs[0])
    L.new(k.outputs[0], bsdf.inputs["Emission Strength"])
    L.new(bsdf.outputs[0], out.inputs["Surface"])
    mat.use_backface_culling = False
    for attr, val in (("surface_render_method", "DITHERED"), ("blend_method", "HASHED")):
        try:
            setattr(mat, attr, val)
        except Exception:
            pass
    return mat


def wall_mesh(name, mats):
    cells = {(i, 0, j) for i in range(WW) for j in range(WH)}
    add3 = lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2])
    neg = lambda a: (-a[0], -a[1], -a[2])
    verts, faces, uvs, mi = [], [], [], []
    for c in cells:
        for n, sa, ta in FACES:
            if add3(c, n) in cells:
                continue
            out = frozenset(nm for nm, d in (("left", neg(sa)), ("right", sa), ("bottom", neg(ta)), ("top", ta))
                            if add3(c, d) not in cells)
            ki, rot = PICK[out]
            ctr = tuple(c[q] + 0.5 + 0.5 * n[q] for q in range(3))
            b0 = len(verts)
            for s, t in ((0, 0), (1, 0), (1, 1), (0, 1)):
                verts.append(tuple(ctr[q] + (s - 0.5) * sa[q] + (t - 0.5) * ta[q] for q in range(3)))
            faces.append((b0, b0 + 1, b0 + 2, b0 + 3))
            uvs.append([ROT[rot](s, t) for s, t in ((0, 0), (1, 0), (1, 1), (0, 1))])
            mi.append(ki)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for f, quad in zip(me.polygons, uvs):
        for li, uv in zip(f.loop_indices, quad):
            uvl.data[li].uv = uv
    for m_ in mats:
        me.materials.append(m_)
    me.polygons.foreach_set("material_index", mi)
    me.update()
    return me


def label(text, loc):
    cu = bpy.data.curves.new(text, "FONT")
    cu.body = text
    cu.size = 1.1
    cu.align_x = "CENTER"
    o = bpy.data.objects.new(text, cu)
    o.location = loc
    o.rotation_euler = (1.5708, 0, 0)
    m = bpy.data.materials.get("label_glow") or bpy.data.materials.new("label_glow")
    m.use_nodes = True
    em = m.node_tree.nodes.get("Principled BSDF")
    em.inputs["Emission Color"].default_value = (0.75, 1.0, 0.8, 1)
    em.inputs["Emission Strength"].default_value = 4.0
    cu.materials.append(m)
    scene.collection.objects.link(o)


smoke = bpy.data.materials.get("smoke_skin")
for i, (st, title) in enumerate(STYLES):
    for nm in (f"Option {st}", f"Option {st} Smoke", f"{st}  {title}"):
        o = bpy.data.objects.get(nm)
        if o:
            bpy.data.objects.remove(o)
    base = ROW + Vector((i * (WW + GAP), 0, 0))
    wall = bpy.data.objects.new(f"Option {st}", wall_mesh(f"option_{st}", [material(st, k) for k in KINDS]))
    wall.location = base
    scene.collection.objects.link(wall)
    label(f"{st}  {title}", base + Vector((WW / 2, 0.5, WH + 0.5)))
    if smoke is not None:
        PAD = 0.7
        half = Vector((WW / 2, 0.5, WH / 2))
        e = half + Vector((PAD, PAD, PAD))
        vs = [(sx * e.x, sy * e.y, sz * e.z) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        sm = bpy.data.meshes.new(f"option_{st}_smoke")
        sm.from_pydata(vs, [], fs)
        sm.materials.append(smoke)
        so = bpy.data.objects.new(f"Option {st} Smoke", sm)
        so.location = base + half
        so["half"] = tuple(half)
        scene.collection.objects.link(so)

# a camera on the whole row
cam = bpy.data.objects.get("Options Camera")
if cam is None:
    cam = bpy.data.objects.new("Options Camera", bpy.data.cameras.new("Options Camera"))
    scene.collection.objects.link(cam)
cam.data.lens = 32
centre = ROW + Vector(((4 * WW + 3 * GAP) / 2, 0.5, WH / 2 + 0.3))
cam.location = centre + Vector((-3.0, -19.0, 3.5))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
            a.tag_redraw()
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception:
        pass
