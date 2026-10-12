# Pass 17, round three. J: the ripples are the thing; the still cracks go, the smoke hugs closer.
# Faces row (camera "Options Camera"), all on plain cloudy jade (J) with no fixed lines; the line work
# is moving ripples, broken into small pieces, in several sizes at once:
#   R1 mixed sizes        R2 small fragments (more, quicker)
#   R3 large and slow     R4 mixed sizes that pulse brighter and dimmer
# Smoke row (camera "Smoke Camera"), all much thinner and tighter to the blocks:
#   T1 skin   T2 dry ice (sinks, settles low)   T3 haze (soft glow)
import os
import bpy
from mathutils import Vector

scene = bpy.context.scene
WW, WH, GAP = 4, 3, 2
FACE_ROW = Vector((29.0, -9.0, 0.0))
SMOKE_ROW = Vector((57.0, -9.0, 0.0))
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

# ---- clear round one -----------------------------------------------------------------------------
for o in list(bpy.data.objects):
    n = o.name
    if n.startswith("Option ") or (o.type == "FONT" and n[:1] in "ABCDSRT" and "  " in n):
        bpy.data.objects.remove(o)


# ---- helpers --------------------------------------------------------------------------------------
class G:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.N, self.L = self.nt.nodes, self.nt.links

    def m(self, op, a, b=None, c=None):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        for i, src in enumerate((a, b, c)):
            if src is None:
                continue
            if isinstance(src, (int, float)):
                n.inputs[i].default_value = src
            else:
                self.L.new(src, n.inputs[i])
        return n.outputs[0]

    def v(self, op, a, b=None, scale=None):
        n = self.N.new("ShaderNodeVectorMath")
        n.operation = op
        for i, src in enumerate((a, b)):
            if src is None:
                continue
            if isinstance(src, tuple):
                n.inputs[i].default_value = src
            else:
                self.L.new(src, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                n.inputs["Scale"].default_value = scale
            else:
                self.L.new(scale, n.inputs["Scale"])
        return n.outputs["Vector"] if op != "DOT_PRODUCT" and op != "LENGTH" else n.outputs["Value"]

    def clock(self):
        c = self.N.new("ShaderNodeValue")
        fc = c.outputs[0].driver_add("default_value")
        fc.driver.type = "SCRIPTED"
        fc.driver.expression = f"frame / {scene.render.fps}"
        return c.outputs[0]

    def noise(self, vec, w, scale, detail=6.0, rough=0.6, dist=0.0):
        n = self.N.new("ShaderNodeTexNoise")
        n.noise_dimensions = "4D"
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = dist
        self.L.new(vec, n.inputs["Vector"])
        if isinstance(w, (int, float)):
            n.inputs["W"].default_value = w
        else:
            self.L.new(w, n.inputs["W"])
        return n.outputs["Fac"]


def add_gloss(mat):
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    gl = N.new("ShaderNodeBsdfGlossy")
    gl.label = "emerald gloss"
    gl.inputs["Color"].default_value = (0.82, 1.0, 0.88, 1)
    gl.inputs["Roughness"].default_value = 0.05
    fr = N.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.58
    mix = N.new("ShaderNodeMixShader")
    L.new(fr.outputs[0], mix.inputs[0])
    L.new(src, mix.inputs[1])
    L.new(gl.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])


def face_material(style, kind):
    name = f"opt_{style}_{kind}"
    fname = f"{style}_{kind}.png"
    img = bpy.data.images.get(fname)
    if img is None:
        img = bpy.data.images.load(os.path.join(FOLDER, fname))
    else:
        img.filepath = os.path.join(FOLDER, fname)
        img.reload()
    img.alpha_mode = "STRAIGHT"
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    N, L = g.N, g.L
    out = N.new("ShaderNodeOutputMaterial")
    tex = N.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(tex.outputs["Color"], b.inputs["Base Color"])
    L.new(tex.outputs["Color"], b.inputs["Emission Color"])
    L.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.04
    bw = N.new("ShaderNodeRGBToBW")
    L.new(tex.outputs["Color"], bw.inputs[0])
    L.new(g.m("MULTIPLY_ADD", g.m("POWER", bw.outputs[0], 2.2), 6.0, 0.45), b.inputs["Emission Strength"])
    L.new(b.outputs[0], out.inputs["Surface"])
    add_gloss(mat)
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


def box(name, half, mat, loc, pad):
    e = Vector(half) + Vector((pad, pad, pad))
    vs = [(sx * e.x, sy * e.y, sz * e.z) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o["half"] = tuple(half)
    scene.collection.objects.link(o)
    return o


def label(text, loc):
    cu = bpy.data.curves.new(text, "FONT")
    cu.body = text
    cu.size = 0.55
    cu.align_x = "CENTER"
    o = bpy.data.objects.new(text, cu)
    o.location = loc
    o.rotation_euler = (1.5708, 0, 0)
    m = bpy.data.materials.get("label_glow") or bpy.data.materials.new("label_glow")
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    if p:
        p.inputs["Emission Color"].default_value = (0.75, 1.0, 0.8, 1)
        p.inputs["Emission Strength"].default_value = 4.0
    cu.materials.append(m)
    scene.collection.objects.link(o)


# ---- streaks: glowing strands just over the faces, each area drifting its own way ---------------
def streak_material(name, layers, amount, pulse=0.0):
    """Ripples floating over the face. Each layer: (size, speed, thinness, weight). A layer's ripples
    lie along a direction that changes slowly from area to area, slide along it, are cut into short
    pieces, and fade in and out; several sizes are laid over each other."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    N, L = g.N, g.L
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    p = tc.outputs["Object"]
    t = g.clock()
    total = None
    for li, (size, speed, thin, weight) in enumerate(layers):
        ps = g.v("SCALE", p, None, 1.0 / size)
        ang = g.m("MULTIPLY", g.noise(ps, g.m("ADD", g.m("MULTIPLY", t, 0.03), li * 7.0), 0.35, 1.0), 12.566)
        dvec = N.new("ShaderNodeCombineXYZ")
        L.new(g.m("COSINE", ang), dvec.inputs[0])
        L.new(g.m("MULTIPLY", g.m("SINE", ang), 0.3), dvec.inputs[1])
        L.new(g.m("SINE", ang), dvec.inputs[2])
        d = g.v("NORMALIZE", dvec.outputs[0])
        moved = g.v("SUBTRACT", ps, g.v("SCALE", d, None, g.m("MULTIPLY", t, speed / size)))
        along = g.v("SCALE", d, None, g.v("DOT_PRODUCT", moved, d))
        across = g.v("SUBTRACT", moved, along)
        q = g.v("ADD", g.v("SCALE", along, None, 0.3), g.v("SCALE", across, None, 3.0))
        # slow morphing so the ripples travel rather than boil
        n = g.noise(q, g.m("ADD", g.m("MULTIPLY", t, 0.06), li * 3.0), 2.0, 2.0, 0.5)
        ridge = g.m("SUBTRACT", 1.0, g.m("ABSOLUTE", g.m("SUBTRACT", g.m("MULTIPLY", n, 2.0), 1.0)))
        strand = g.m("POWER", ridge, thin)
        # cut into short pieces along their length, pieces that come and go
        cut = g.noise(g.v("SCALE", moved, None, 2.2), g.m("ADD", g.m("MULTIPLY", t, 0.2), li * 5.0), 1.6, 1.0)
        piece = N.new("ShaderNodeMapRange")
        piece.inputs["From Min"].default_value = 0.48
        piece.inputs["From Max"].default_value = 0.62
        L.new(cut, piece.inputs["Value"])
        life = g.noise(ps, g.m("ADD", g.m("MULTIPLY", t, 0.25), li * 11.0), 0.6, 2.0)
        fade = N.new("ShaderNodeMapRange")
        fade.inputs["From Min"].default_value = 0.46
        fade.inputs["From Max"].default_value = 0.64
        L.new(life, fade.inputs["Value"])
        k = g.m("MULTIPLY", g.m("MULTIPLY", g.m("MULTIPLY", strand, piece.outputs[0]), fade.outputs[0]), weight)
        total = k if total is None else g.m("ADD", total, k)
    glow = g.m("MULTIPLY", total, amount)
    if pulse:
        beat = g.m("ADD", 1.0, g.m("MULTIPLY", g.m("SINE", g.m("MULTIPLY", t, 2.2)), pulse))
        glow = g.m("MULTIPLY", glow, beat)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.55, 1.0, 0.65, 1)
    L.new(glow, em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    add = N.new("ShaderNodeAddShader")
    L.new(tr.outputs[0], add.inputs[0])
    L.new(em.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs["Surface"])
    try:
        mat.surface_render_method = "BLENDED"
    except Exception:
        pass
    mat.use_backface_culling = False
    return mat


# ---- smoke: a volume round the wall, shaped by distance to its faces ---------------------------
def smoke_material(name, thick, scale, thr, density, drift=(0, 0, 0), stretch=1.0, pool=0.0, glow=0.5,
                   color=(0.7, 1.0, 0.78), wspeed=0.22):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    N, L = g.N, g.L
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    p = tc.outputs["Object"]
    attr = N.new("ShaderNodeAttribute")
    attr.attribute_type = "OBJECT"
    attr.attribute_name = "half"
    h = attr.outputs["Vector"]
    q = g.v("SUBTRACT", g.v("ABSOLUTE", p), h)
    outside = g.v("LENGTH", g.v("MAXIMUM", q, (0.0, 0.0, 0.0)))
    sq = N.new("ShaderNodeSeparateXYZ")
    L.new(q, sq.inputs[0])
    inside = g.m("MINIMUM", g.m("MAXIMUM", g.m("MAXIMUM", sq.outputs[0], sq.outputs[1]), sq.outputs[2]), 0.0)
    dist = g.m("ADD", outside, inside)
    shell = g.m("MULTIPLY", g.m("EXPONENT", g.m("MULTIPLY", g.m("MAXIMUM", dist, 0.0), -1.0 / thick)),
                g.m("GREATER_THAN", dist, -0.01))
    t = g.clock()
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(p, sp.inputs[0])
    sv = N.new("ShaderNodeCombineXYZ")
    L.new(g.m("SUBTRACT", sp.outputs[0], g.m("MULTIPLY", t, drift[0])), sv.inputs[0])
    L.new(g.m("SUBTRACT", sp.outputs[1], g.m("MULTIPLY", t, drift[1])), sv.inputs[1])
    L.new(g.m("MULTIPLY", g.m("SUBTRACT", sp.outputs[2], g.m("MULTIPLY", t, drift[2])), stretch), sv.inputs[2])
    n = g.noise(sv.outputs[0], g.m("MULTIPLY", t, wspeed), scale, 8.0, 0.6, 1.4)
    wisps = g.m("POWER", g.m("MAXIMUM", g.m("SUBTRACT", n, thr), 0.0), 1.3)
    dens = g.m("MULTIPLY", g.m("MULTIPLY", wisps, shell), density)
    if pool:
        # pooling: thicker toward the bottom of the wall, as heavy smoke settles
        hz = N.new("ShaderNodeSeparateXYZ")
        L.new(h, hz.inputs[0])
        from_bottom = g.m("ADD", sp.outputs[2], hz.outputs[2])
        dens = g.m("MULTIPLY", dens, g.m("ADD", 1.0, g.m("MULTIPLY", g.m("EXPONENT", g.m("MULTIPLY", from_bottom, -1.6)), pool)))
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Emission Color"].default_value = (0.25, 1.0, 0.45, 1)
    L.new(dens, vol.inputs["Density"])
    L.new(g.m("MULTIPLY", dens, glow), vol.inputs["Emission Strength"])
    L.new(vol.outputs[0], out.inputs["Volume"])
    return mat


SKIN = smoke_material("smoke_T1_skin", 0.1, 2.6, 0.46, 34)
FACE_SET = {"J": [face_material("J", k) for k in KINDS]}
RIPPLES = [
    ("R1", "mixed sizes", streak_material("ripples_R1", [(1.0, 0.4, 20, 1.0), (0.45, 0.35, 26, 0.8), (0.2, 0.3, 30, 0.6)], 4.5)),
    ("R2", "small fragments", streak_material("ripples_R2", [(0.3, 0.6, 26, 1.0), (0.16, 0.5, 30, 0.9)], 5.5)),
    ("R3", "large and slow", streak_material("ripples_R3", [(1.4, 0.2, 16, 1.0), (0.7, 0.18, 22, 0.6)], 4.0)),
    ("R4", "pulsing", streak_material("ripples_R4", [(1.0, 0.4, 20, 1.0), (0.45, 0.35, 26, 0.8), (0.2, 0.3, 30, 0.6)], 4.5, pulse=0.55)),
]
HALF = (WW / 2, 0.5, WH / 2)


def wall(tag, title, row, i, faces, smoke, ripples=None, pad=0.5):
    base = row + Vector((i * (WW + GAP), 0, 0))
    o = bpy.data.objects.new(f"Option {tag}", wall_mesh(f"option_{tag}", faces))
    o.location = base
    scene.collection.objects.link(o)
    ctr = base + Vector(HALF)
    box(f"Option {tag} Smoke", HALF, smoke, ctr, pad)
    if ripples:
        box(f"Option {tag} Ripples", HALF, ripples, ctr, 0.04)
    label(f"{tag}  {title}", base + Vector((WW / 2, 0.5, WH + 0.6)))


for i, (tag, title, mat) in enumerate(RIPPLES):
    wall(tag, title, FACE_ROW, i, FACE_SET["J"], SKIN, mat, pad=0.4)

SMOKES = [
    ("T1", "skin", SKIN, 0.4),
    ("T2", "dry ice", smoke_material("smoke_T2_dryice", 0.16, 1.8, 0.42, 34, drift=(0, 0, -0.3), pool=1.5,
                                       color=(0.85, 1.0, 0.88), glow=0.35), 0.6),
    ("T3", "haze", smoke_material("smoke_T3_haze", 0.22, 1.3, 0.34, 12, glow=1.2, wspeed=0.12), 0.8),
]
for i, (tag, title, mat, pad) in enumerate(SMOKES):
    wall(tag, title, SMOKE_ROW, i, FACE_SET["J"], mat, RIPPLES[0][2], pad=pad)


# ---- cameras ---------------------------------------------------------------------------------------
def camera(name, row):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        scene.collection.objects.link(cam)
    cam.data.lens = 30
    centre = row + Vector(((4 * WW + 3 * GAP) / 2, 0.5, 1.9))
    cam.location = centre + Vector((0.0, -24.0, 4.0))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


face_cam = camera("Options Camera", FACE_ROW)
camera("Smoke Camera", SMOKE_ROW)
scene.camera = face_cam
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
                    sp.shading.type = "RENDERED"
            a.tag_redraw()
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception:
        pass
