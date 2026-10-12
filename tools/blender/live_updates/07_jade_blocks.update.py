# Pass 7: Green Lantern construct blocks, one block at a time, every face the same crystal jade.
# A face gets a bright outline on each side where the construct ends (no neighbour block that way),
# so outlines trace the construct's outer edges on every face, the ends and top included; the
# texture is turned so they land in the right place. A 6 x 4 wall and a 2 x 2 x 2 cube beside it. The outline glows hardest, the cracks less,
# the jade itself least. Dry-ice smoke bleeds off the faces and spills down onto the ground.
import os
import bpy
from mathutils import Vector

scene = bpy.context.scene
ORIGIN = Vector((40.0, 0.0, 0.0))
W, H = 6, 4

for name in ("Construct Walls", "Light Barrier", "Barrier Light", "Jade Blocks", "Dry Ice", "Construct Floor"):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o)


# ---- materials: the same jade, outlined on 0 to 4 sides -----------------------------------------
KINDS = ["plain", "edge", "corner", "strip", "three", "frame"]
TEX_SIDES = {"plain": "", "edge": "L", "corner": "LT", "strip": "LR", "three": "LTR", "frame": "LTRB"}


def jade_material(kind):
    name = "jade_" + kind
    path = os.path.join(FOLDER, name + ".png")
    img = bpy.data.images.get(name + ".png")
    if img is None:
        img = bpy.data.images.load(path)
    else:
        img.filepath = path
        img.reload()
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    tex = N.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"           # Minecraft pixels
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Roughness"].default_value = 0.18
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.04
    # glow by brightness: outline (near white) strongest, cracks next, the jade itself softly
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
    return mat


MATS = [jade_material(k) for k in KINDS]

# ---- the rule, the same for every face of every block (and what the game will use) -------------
# A face's side gets the outline when the construct ends there: no block next door in that
# direction, so the surface turns a corner. Every face is the same jade; only its outlined sides
# differ, and the texture is turned so they land in the right place.
ROT = {   # face corner (s, t) -> texture (u, v)
    "id": lambda s, t: (s, t),
    "top": lambda s, t: (1 - t, s),
    "right": lambda s, t: (1 - s, 1 - t),
    "bottom": lambda s, t: (t, 1 - s),
}
# where each texture side (L u=0, R u=1, B v=0, T v=1) lands on the face under each turn
LANDS = {
    "id": {"L": "left", "R": "right", "B": "bottom", "T": "top"},
    "top": {"L": "top", "R": "bottom", "B": "left", "T": "right"},
    "right": {"L": "right", "R": "left", "B": "top", "T": "bottom"},
    "bottom": {"L": "bottom", "R": "top", "B": "right", "T": "left"},
}
PICK = {}
for ki, kind in enumerate(KINDS):
    for rot, land in LANDS.items():
        PICK.setdefault(frozenset(land[c] for c in TEX_SIDES[kind]), (ki, rot))

# the face's own axes (s right, t up as seen from outside; s x t = the outward normal)
FACES = [((0, -1, 0), (1, 0, 0), (0, 0, 1)), ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
         ((-1, 0, 0), (0, -1, 0), (0, 0, 1)), ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (1, 0, 0), (0, -1, 0))]

# the constructs: a 6 x 4 wall, and a 2 x 2 x 2 cube beside it to show every side outlined
cells = {(i, 0, j) for i in range(-3, 3) for j in range(H)}
cells |= {(i, j, k) for i in (5, 6) for j in (-1, 0) for k in (0, 1)}

verts, faces, uvs, mats = [], [], [], []
ST = [(0, 0), (1, 0), (1, 1), (0, 1)]
add3 = lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2])
neg = lambda a: (-a[0], -a[1], -a[2])
for c in cells:
    for n, sa, ta in FACES:
        if add3(c, n) in cells:
            continue                         # hidden face
        out_sides = frozenset(name for name, d in (("left", neg(sa)), ("right", sa), ("bottom", neg(ta)), ("top", ta))
                              if add3(c, d) not in cells)
        ki, rot = PICK[out_sides]
        ctr = tuple(c[q] + 0.5 + 0.5 * n[q] for q in range(3))
        b0 = len(verts)
        for s, t in ST:
            verts.append(tuple(ctr[q] + (s - 0.5) * sa[q] + (t - 0.5) * ta[q] for q in range(3)))
        faces.append((b0, b0 + 1, b0 + 2, b0 + 3))
        uvs.append([ROT[rot](s, t) for s, t in ST])
        mats.append(ki)

me = bpy.data.meshes.new("jade_blocks")
me.from_pydata(verts, [], faces)
uvl = me.uv_layers.new(name="UVMap")
for f, quad in zip(me.polygons, uvs):
    for li, uv in zip(f.loop_indices, quad):
        uvl.data[li].uv = uv
for m_ in MATS:
    me.materials.append(m_)
me.polygons.foreach_set("material_index", mats)
me.update()
blocks = bpy.data.objects.new("Jade Blocks", me)
blocks.location = ORIGIN
scene.collection.objects.link(blocks)

# ---- ground to catch the smoke ------------------------------------------------------------------
fm = bpy.data.meshes.new("construct_floor")
fm.from_pydata([(-14, -12, 0), (14, -12, 0), (14, 12, 0), (-14, 12, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("Construct Floor", fm)
floor.location = ORIGIN
scene.collection.objects.link(floor)
fmat = bpy.data.materials.get("floor")
if fmat:
    fm.materials.append(fmat)

# ---- dry-ice smoke: a volume hugging the wall, thickest at its faces, sinking and pooling --------
vm = bpy.data.meshes.new("dry_ice")
X0, X1, Y0, Y1, Z0, Z1 = -W / 2 - 2.5, W / 2 + 2.5, -3.5, 4.5, 0.0, H + 1.0
vm.from_pydata([(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0), (X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)], [],
               [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)])
ice = bpy.data.objects.new("Dry Ice", vm)
ice.location = ORIGIN
scene.collection.objects.link(ice)
vmat = bpy.data.materials.get("dry_ice") or bpy.data.materials.new("dry_ice")
vmat.use_nodes = True
nt = vmat.node_tree
nt.nodes.clear()
N, L = nt.nodes, nt.links


def m(op, a, b=None, c=None):
    n = N.new("ShaderNodeMath")
    n.operation = op
    for i, src in enumerate((a, b, c)):
        if src is None:
            continue
        if isinstance(src, (int, float)):
            n.inputs[i].default_value = src
        else:
            L.new(src, n.inputs[i])
    return n.outputs[0]


out = N.new("ShaderNodeOutputMaterial")
tc = N.new("ShaderNodeTexCoord")
sep = N.new("ShaderNodeSeparateXYZ")
L.new(tc.outputs["Object"], sep.inputs[0])
x, y, z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
clock = N.new("ShaderNodeValue")
fc = clock.outputs[0].driver_add("default_value")
fc.driver.type = "SCRIPTED"
fc.driver.expression = f"frame / {scene.render.fps}"          # seconds
t = clock.outputs[0]
# the smoke sinks (sample point rises with time) and spreads away from the faces as it falls
sink = m("MULTIPLY", t, 0.45)
comb = N.new("ShaderNodeCombineXYZ")
L.new(x, comb.inputs[0])
L.new(m("MULTIPLY", y, 0.8), comb.inputs[1])
L.new(m("ADD", z, sink), comb.inputs[2])
noise = N.new("ShaderNodeTexNoise")
noise.noise_dimensions = "4D"
noise.inputs["Scale"].default_value = 0.9
noise.inputs["Detail"].default_value = 6.0
noise.inputs["Roughness"].default_value = 0.62
noise.inputs["Distortion"].default_value = 0.6
L.new(comb.outputs[0], noise.inputs["Vector"])
L.new(m("MULTIPLY", t, 0.12), noise.inputs["W"])
wisps = m("POWER", m("MAXIMUM", m("SUBTRACT", noise.outputs["Fac"], 0.42), 0.0), 1.6)
# distance from the wall's faces (it is 1 block thick, from y = 0 to 1)
dy = m("MAXIMUM", m("MAXIMUM", m("SUBTRACT", 0.0, y), m("SUBTRACT", y, 1.0)), 0.0)
# how far the smoke reaches out grows the lower it is: it clings up high and pools at the ground
reach = m("ADD", 0.35, m("MULTIPLY", m("MAXIMUM", m("SUBTRACT", float(H), z), 0.0), 0.45))
near = m("EXPONENT", m("MULTIPLY", m("DIVIDE", dy, reach), -1.0))
# none above the wall's top, a thin fade at the very bottom of the box
top = m("SUBTRACT", 1.0, m("MINIMUM", m("MAXIMUM", m("SUBTRACT", z, float(H) - 0.3), 0.0), 1.0))
side = m("EXPONENT", m("MULTIPLY", m("MAXIMUM", m("SUBTRACT", m("ABSOLUTE", x), W / 2), 0.0), -1.4))
dens = m("MULTIPLY", m("MULTIPLY", m("MULTIPLY", wisps, near), m("MULTIPLY", top, side)), 9.0)
vol = N.new("ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (0.75, 1.0, 0.82, 1)
vol.inputs["Emission Color"].default_value = (0.25, 1.0, 0.45, 1)
L.new(dens, vol.inputs["Density"])
L.new(m("MULTIPLY", dens, 0.35), vol.inputs["Emission Strength"])
L.new(vol.outputs[0], out.inputs["Volume"])
vm.materials.append(vmat)
try:
    scene.eevee.volumetric_tile_size = "4"
    scene.eevee.volumetric_samples = 64
    scene.eevee.volumetric_end = 120.0
except Exception:
    pass

# ---- green light off the wall onto the smoke and ground; a closer three-quarter view ------------
lamp = bpy.data.objects.get("Jade Light")
if lamp is None:
    ld = bpy.data.lights.new("Jade Light", "AREA")
    lamp = bpy.data.objects.new("Jade Light", ld)
    scene.collection.objects.link(lamp)
lamp.data.shape = "RECTANGLE"
lamp.data.size, lamp.data.size_y = float(W), float(H)
lamp.data.energy = 220
lamp.data.color = (0.3, 1.0, 0.45)
lamp.location = ORIGIN + Vector((0, -0.05, H / 2))
lamp.rotation_euler = (-1.5708, 0, 0)        # shining out from the front face

cam = bpy.data.objects["Walls Camera"]
cam.data.lens = 35
cam.location = ORIGIN + Vector((-7.5, -10.5, 3.6))
cam.rotation_euler = (ORIGIN + Vector((0.3, 0, 1.7)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
