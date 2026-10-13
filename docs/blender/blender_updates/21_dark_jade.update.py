# Pass 21: J's colour pass on the Dark Lantern (the swinging E1): natural green jade, the ribbed bands
# an even darker jade. Neither glows at rest; both light up with the charge (the raised bands
# brighter). The gold trace cracks are gold at rest and glow green while charging, and a few gold
# flecks in them glint now and then, each on its own rhythm. All driven by the Charge slider.
# Then stills into renders/ at rest, charging, full and the flash.
import os
import bpy
import numpy as np

scene = bpy.context.scene
ctl = bpy.data.objects["Lantern Controls"]


def driven_value(N, expr, with_charge=True):
    v = N.new("ShaderNodeValue")
    fc = v.outputs[0].driver_add("default_value")
    d = fc.driver
    d.type = "SCRIPTED"
    if with_charge:
        var = d.variables.new()
        var.name = "c"
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "OBJECT"
        var.targets[0].id = ctl
        var.targets[0].data_path = '["charge"]'
    d.expression = expr
    return v.outputs[0]


def mat_new(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree.nodes, m.node_tree.links


# jade body: the attribute colour at rest, glowing green with the charge
body, N, L = mat_new("dark_body")
out = N.new("ShaderNodeOutputMaterial")
at = N.new("ShaderNodeAttribute"); at.attribute_name = "col"
b = N.new("ShaderNodeBsdfPrincipled")
L.new(at.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.22
b.inputs["Coat Weight"].default_value = 0.8
boost = N.new("ShaderNodeMix"); boost.data_type = "RGBA"; boost.blend_type = "MULTIPLY"
boost.inputs["Factor"].default_value = 1.0
L.new(at.outputs["Color"], boost.inputs[6])
boost.inputs[7].default_value = (2.4, 3.4, 2.6, 1)
L.new(boost.outputs[2], b.inputs["Emission Color"])
L.new(driven_value(N, "c * 3.2"), b.inputs["Emission Strength"])
L.new(b.outputs[0], out.inputs["Surface"])

# gold trace cracks: gold at rest, green light while charging
crack, N, L = mat_new("dark_crack")
out = N.new("ShaderNodeOutputMaterial")
at = N.new("ShaderNodeAttribute"); at.attribute_name = "col"
b = N.new("ShaderNodeBsdfPrincipled")
L.new(at.outputs["Color"], b.inputs["Base Color"])
b.inputs["Metallic"].default_value = 0.9
b.inputs["Roughness"].default_value = 0.3
b.inputs["Emission Color"].default_value = (0.35, 1.0, 0.5, 1)
L.new(driven_value(N, "c * 6.0"), b.inputs["Emission Strength"])
L.new(b.outputs[0], out.inputs["Surface"])

# gold flecks: each flashes briefly on its own rhythm, charged or not (and green-gold when charged)
fleck, N, L = mat_new("dark_fleck")
out = N.new("ShaderNodeOutputMaterial")
at = N.new("ShaderNodeAttribute"); at.attribute_name = "col"
b = N.new("ShaderNodeBsdfPrincipled")
L.new(at.outputs["Color"], b.inputs["Base Color"])
b.inputs["Metallic"].default_value = 0.95
b.inputs["Roughness"].default_value = 0.15
b.inputs["Emission Color"].default_value = (1.0, 0.86, 0.5, 1)
tc = N.new("ShaderNodeTexCoord")
snap = N.new("ShaderNodeVectorMath"); snap.operation = "SNAP"
snap.inputs[1].default_value = (0.25, 0.25, 0.25)
L.new(tc.outputs["Object"], snap.inputs[0])
wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
L.new(snap.outputs["Vector"], wn.inputs["Vector"])


def m(op, a, b_=None):
    n = N.new("ShaderNodeMath"); n.operation = op
    for i, s in enumerate((a, b_)):
        if s is None:
            continue
        if isinstance(s, (int, float)):
            n.inputs[i].default_value = s
        else:
            L.new(s, n.inputs[i])
    return n.outputs[0]


t = driven_value(N, f"frame / {scene.render.fps}", with_charge=False)
phase = m("ADD", m("MULTIPLY", t, 0.9), m("MULTIPLY", wn.outputs["Value"], 62.83))
glint = m("MULTIPLY", m("POWER", m("MAXIMUM", m("SINE", phase), 0.0), 60.0), 30.0)
L.new(m("ADD", glint, driven_value(N, "c * 3.0")), b.inputs["Emission Strength"])
L.new(b.outputs[0], out.inputs["Surface"])

# ---- swap the swinging lantern's mesh for the new colours ------------------------------------------
lantern = bpy.data.objects.get("Dark E1")
d = np.load(os.path.join(FOLDER, "dark3_e1.npz"))
q = d["quads"]
verts = q.reshape(-1, 3)
me = bpy.data.meshes.new("dark_e1_jade")
me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
for mat in (bpy.data.materials.get("stone"), bpy.data.materials.get("metal"), bpy.data.materials.get("glow"),
            fleck, body, crack):
    me.materials.append(mat)
me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
old = lantern.data
lantern.data = me
if old.users == 0:
    bpy.data.meshes.remove(old)

# ---- stills: at rest, charging, full, the flash ----------------------------------------------------
outdir = os.path.join(FOLDER, "renders")
os.makedirs(outdir, exist_ok=True)
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = bpy.data.objects.get("Swing Camera") or scene.camera
scene.render.resolution_percentage = 50
for f in (12, 120, 170, 176):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(outdir, f"darkjade_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
