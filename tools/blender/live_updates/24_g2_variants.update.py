# Pass 24: variations on J's pick G2, all with more gold cracks: G2A engraved port band, G2B dark bronze
# metal like the film, G2C long lightning veins. Stills to renders/.
# replacing F1-F3 in the row. Charging no longer lights the whole body: each pixel carries a glow
# weight, so the light gathers at the centre of the waist (hot yellow-green at its heart) and fades
# toward the collars, the ribs only faintly lit, like the film stills. Stills to renders/.
import os
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
ctl = bpy.data.objects["Lantern Controls"]
ROW = Vector((-16.5, 34.0, 0.0))


def charge_value(N, expr):
    v = N.new("ShaderNodeValue")
    d = v.outputs[0].driver_add("default_value").driver
    d.type = "SCRIPTED"
    var = d.variables.new(); var.name = "c"; var.type = "SINGLE_PROP"
    var.targets[0].id_type = "OBJECT"; var.targets[0].id = ctl; var.targets[0].data_path = '["charge"]'
    d.expression = expr
    return v.outputs[0]


def centre_glow_material(name, metal, base_strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    col = N.new("ShaderNodeAttribute"); col.attribute_name = "col"
    gw = N.new("ShaderNodeAttribute"); gw.attribute_name = "glow"
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(col.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25 if metal else 0.18
    b.inputs["Metallic"].default_value = 0.9 if metal else 0.0
    b.inputs["Coat Weight"].default_value = 0.0 if metal else 0.9
    # colour: deep green at the edge of the glow, yellow-green at its heart
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.02, 0.6, 0.18, 1)
    ramp.color_ramp.elements[1].color = (0.75, 1.0, 0.35, 1)
    ramp.color_ramp.elements.new(0.6).color = (0.15, 1.0, 0.35, 1)
    L.new(gw.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    # strength: charge x glow weight squared, so the centre is much hotter than the fringe
    sq = N.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = 2.0
    L.new(gw.outputs["Fac"], sq.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(sq.outputs[0], mul.inputs[0])
    L.new(charge_value(N, f"c * {base_strength}"), mul.inputs[1])
    L.new(mul.outputs[0], b.inputs["Emission Strength"])
    L.new(b.outputs[0], out.inputs["Surface"])
    return m


body = centre_glow_material("dark_body_centre", False, 9.0)
crack = centre_glow_material("dark_crack_centre", True, 12.0)
mats = [bpy.data.materials.get("stone"), bpy.data.materials.get("metal"), bpy.data.materials.get("glow"),
        bpy.data.materials.get("dark_fleck"), body, crack]

for n in ("Dark F1", "Dark F2", "Dark F3", "Dark G1", "Dark G2", "Dark G3", "Dark G2A", "Dark G2B", "Dark G2C"):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)
for i, v in enumerate(("g2a", "g2b", "g2c")):
    name = f"Dark {v.upper()}"
    d = np.load(os.path.join(FOLDER, f"dark5_{v}.npz"))
    q = d["quads"]
    verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    g = me.attributes.new("glow", "FLOAT", "CORNER")
    g.data.foreach_set("value", np.repeat(np.asarray(d["glow"], np.float32), 4))
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
    o = bpy.data.objects.new(name, me)
    o.scale = (1 / 16,) * 3
    o.location = ROW + Vector((i * 1.6, 0, 0))
    o.rotation_euler = (0, 0, np.radians(-20))
    scene.collection.objects.link(o)

out = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage)
scene.camera = bpy.data.objects["Dark Camera"]
scene.render.resolution_percentage = 60
for f, tag in ((12, "rest"), (120, "half"), (170, "charged")):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"dark6_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage = keep[1], keep[2]
