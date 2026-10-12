# Pass 11:
#  - Removes the glow volume inside the jade (EEVEE drew it as flat grey slabs); the jade stays
#    see-through from its texture.
#  - Viewport back to full resolution (Pixel Size 1x) and EEVEE.
#  - Replaces the big dry-ice cloud with a thin skin of smoke hugging every construct: a band about a
#    fifth of a block thick right over every face (front, back, sides, top), thickest at the surface,
#    curling and drifting every way at once (4D noise evolving in place), so it never repeats.
import bpy
from mathutils import Vector

scene = bpy.context.scene
ORIGIN = Vector((40.0, 0.0, 0.0))

# ---- the jade: no inner volume -----------------------------------------------------------------
for mat in bpy.data.materials:
    if mat.name.startswith("jade_") and mat.node_tree:
        nt = mat.node_tree
        for n in [n for n in nt.nodes if n.type == "PRINCIPLED_VOLUME"]:
            nt.nodes.remove(n)

# ---- the smoke skin -------------------------------------------------------------------------------
for name in ("Dry Ice", "Smoke Skin Wall", "Smoke Skin Cube"):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o)

THICK = 0.2        # how far out the smoke hovers (blocks)
PAD = 0.7          # the volume box reaches this far past the construct


def skin_material():
    mat = bpy.data.materials.get("smoke_skin") or bpy.data.materials.new("smoke_skin")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links

    def m(op, a, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, src in enumerate((a, b)):
            if src is None:
                continue
            if isinstance(src, (int, float)):
                n.inputs[i].default_value = src
            else:
                L.new(src, n.inputs[i])
        return n.outputs[0]

    def v(op, a, b=None):
        n = N.new("ShaderNodeVectorMath")
        n.operation = op
        for i, src in enumerate((a, b)):
            if src is None:
                continue
            if isinstance(src, tuple):
                n.inputs[i].default_value = src
            else:
                L.new(src, n.inputs[i])
        return n

    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    # half size of the construct inside this box, read from the object's own "half" property
    attr = N.new("ShaderNodeAttribute")
    attr.attribute_type = "OBJECT"
    attr.attribute_name = "half"
    p = tc.outputs["Object"]
    # distance from the construct's surface (a box): outside > 0, inside < 0
    q = v("SUBTRACT", v("ABSOLUTE", p).outputs[0], attr.outputs["Vector"]).outputs[0]
    outside = v("LENGTH", v("MAXIMUM", q, (0.0, 0.0, 0.0)).outputs[0]).outputs["Value"]
    sq = N.new("ShaderNodeSeparateXYZ")
    L.new(q, sq.inputs[0])
    inside = m("MINIMUM", m("MAXIMUM", m("MAXIMUM", sq.outputs[0], sq.outputs[1]), sq.outputs[2]), 0.0)
    d = m("ADD", outside, inside)
    # thickest right at the surface, gone a few tenths of a block out; nothing inside the jade
    shell = m("MULTIPLY", m("EXPONENT", m("MULTIPLY", m("MAXIMUM", d, 0.0), -1.0 / THICK)), m("GREATER_THAN", d, -0.01))
    # the smoke itself: fine curling wisps that change in place, every direction at once
    clock = N.new("ShaderNodeValue")
    fc = clock.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"
    fc.driver.expression = f"frame / {scene.render.fps}"
    noise = N.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 2.4
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6
    noise.inputs["Distortion"].default_value = 1.4
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    L.new(m("MULTIPLY", clock.outputs[0], 0.22), noise.inputs["W"])
    wisps = m("POWER", m("MAXIMUM", m("SUBTRACT", noise.outputs["Fac"], 0.44), 0.0), 1.3)
    dens = m("MULTIPLY", m("MULTIPLY", wisps, shell), 30.0)
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.7, 1.0, 0.78, 1)
    vol.inputs["Emission Color"].default_value = (0.25, 1.0, 0.45, 1)
    L.new(dens, vol.inputs["Density"])
    L.new(m("MULTIPLY", dens, 0.5), vol.inputs["Emission Strength"])
    L.new(vol.outputs[0], out.inputs["Volume"])
    return mat


SKIN = skin_material()


def skin(name, lo, hi):
    lo, hi = Vector(lo), Vector(hi)
    half = (hi - lo) / 2
    c = ORIGIN + (lo + hi) / 2
    e = half + Vector((PAD, PAD, PAD))
    vs = [(sx * e.x, sy * e.y, sz * e.z) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(SKIN)
    o = bpy.data.objects.new(name, me)
    o.location = c
    o["half"] = tuple(half)
    scene.collection.objects.link(o)


skin("Smoke Skin Wall", (-3, 0, 0), (3, 1, 4))
skin("Smoke Skin Cube", (5, -1, 0), (7, 1, 2))

# the viewport at full resolution (no big square preview pixels), EEVEE for live viewing
try:
    scene.render.preview_pixel_size = "1"
except Exception:
    pass
for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
try:
    scene.eevee.volumetric_tile_size = "2"     # fine enough to show a thin layer
    scene.eevee.volumetric_samples = 96
except Exception:
    pass

if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception:
        pass
