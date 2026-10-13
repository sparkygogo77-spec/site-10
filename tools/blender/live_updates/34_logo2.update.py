# Pass 34: the logo with a dark pixel all round it, so the brackets stand clear of the port rim.
# Pass 31: the gold cracks as branching lightning (J's film still), forking as they run.
# Pass 29: J's notes on K: square port with a round bronze plug, long gold lines spaced apart on the
# ribbed halves, the glow a column up the middle of each face (his sketch), 15% dimmer with darker
# pixels kept darker, polished gold, and green light spilling from it. L1 K1's ribs, L2 K2's deeper ribs.
# Pass 28: J's notes on H2: glassy ribs (lit lips, dark undersides, a glossy streak), the lantern emblem
# on the ring's port with a glowing socket, a cleaner top (smooth rim, teardrop holes, stepped boss).
# K1 glassy ribs, K2 ribs two pixels proud, K3 with gold hairlines.
# Pass 27: deeper green glow that varies pixel to pixel (no flat wash). Pass 26: finer, sparser gold cracks over dark glass (like the film), and the glow spread through the
# whole glass (brightest at the bulge, still lit near the collars) instead of a band in the middle.
# the wire loops and the plated top. H1 gentle bulge, H2 as the stills, H3 fuller in antique brass.
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
    ramp.color_ramp.elements[0].color = (0.0, 0.25, 0.06, 1)
    ramp.color_ramp.elements[1].color = (0.45, 1.0, 0.25, 1)
    ramp.color_ramp.elements.new(0.55).color = (0.02, 0.8, 0.18, 1)
    L.new(gw.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    # strength: charge x glow weight squared, so the centre is much hotter than the fringe
    sq = N.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = 1.2
    L.new(gw.outputs["Fac"], sq.inputs[0])
    # darker pixels (rib undersides, grooves) stay darker when lit: scale by the pixel's own brightness
    bw = N.new("ShaderNodeRGBToBW")
    L.new(col.outputs["Color"], bw.inputs[0])
    lum = N.new("ShaderNodeMath"); lum.operation = "MULTIPLY_ADD"; lum.use_clamp = True
    L.new(bw.outputs[0], lum.inputs[0]); lum.inputs[1].default_value = 12.0; lum.inputs[2].default_value = 0.35
    sq2 = N.new("ShaderNodeMath"); sq2.operation = "MULTIPLY"
    L.new(sq.outputs[0], sq2.inputs[0]); L.new(lum.outputs[0], sq2.inputs[1])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(sq2.outputs[0], mul.inputs[0])
    L.new(charge_value(N, f"min(c, 1.2) ** 2 * {base_strength} * 0.65"), mul.inputs[1])
    L.new(mul.outputs[0], b.inputs["Emission Strength"])
    L.new(b.outputs[0], out.inputs["Surface"])
    return m


body = centre_glow_material("dark_body_centre", False, 3.2 * 0.85 * 1.6)
crack = centre_glow_material("dark_crack_centre", True, 8.0 * 0.85)
mats = [bpy.data.materials.get("stone"), bpy.data.materials.get("metal"), bpy.data.materials.get("glow"),
        bpy.data.materials.get("dark_fleck"), body, crack]

for n in ("Dark F1", "Dark F2", "Dark F3", "Dark G1", "Dark G2", "Dark G3", "Dark G2A", "Dark G2B", "Dark G2C", "Dark H1", "Dark H2", "Dark H3", "Dark K1", "Dark K2", "Dark K3", "Dark L1", "Dark L2"):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)
for i, v in enumerate(("l1", "l2")):
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
    o.location = ROW + Vector((0.8 + i * 1.6, 0, 0))
    o.rotation_euler = (0, 0, np.radians(-20))
    scene.collection.objects.link(o)

# green light spilling from each lantern, following the charge
ctl_ = bpy.data.objects["Lantern Controls"]
for v in ("l1", "l2"):
    ob = bpy.data.objects[f"Dark {v.upper()}"]
    ln = f"Spill {v.upper()}"
    lo = bpy.data.objects.get(ln)
    if lo is None:
        lo = bpy.data.objects.new(ln, bpy.data.lights.new(ln, "POINT"))
        scene.collection.objects.link(lo)
    lo.data.color = (0.2, 1.0, 0.35)
    lo.data.shadow_soft_size = 0.4
    lo.location = ob.matrix_world @ Vector((0, -7.0, 11.75))
    fc = lo.data.driver_add("energy")
    dv = fc.driver; dv.type = "SCRIPTED"
    vv = dv.variables.new(); vv.name = "c"; vv.type = "SINGLE_PROP"
    vv.targets[0].id_type = "OBJECT"; vv.targets[0].id = ctl_; vv.targets[0].data_path = '["charge"]'
    dv.expression = "min(c, 1.2) ** 2 * 9"

out = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage)
scene.camera = bpy.data.objects["Dark Camera"]
scene.render.resolution_percentage = 60
for f, tag in ((12, "rest"), (120, "half"), (170, "charged")):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"dark16_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage = keep[1], keep[2]

# a close look at H2's top and its front, for checking against the stills
h2 = bpy.data.objects["Dark L1"]
top = h2.matrix_world @ Vector((0, 0, 23.0))
mid = h2.matrix_world @ Vector((0, 0, 11.75))
cam2 = bpy.data.objects.get("Detail Camera")
if cam2 is None:
    cam2 = bpy.data.objects.new("Detail Camera", bpy.data.cameras.new("Detail Camera"))
    scene.collection.objects.link(cam2)
cam2.data.lens = 60
keep_cam = scene.camera
scene.camera = cam2
scene.render.resolution_percentage = 60
scene.frame_set(12)
for tag, target, off in (("top", top, Vector((0.25, -1.9, 2.4))), ("front", mid, Vector((0.1, -1.1, 0.05)))):
    cam2.location = target + off
    cam2.rotation_euler = (target - cam2.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out, f"dark16_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage = keep[1], keep[2]
scene.camera = keep_cam

# the logo up close while charged
scene.camera = cam2
scene.render.resolution_percentage = 60
scene.frame_set(170)
cam2.location = mid + Vector((0.1, -1.1, 0.05))
cam2.rotation_euler = (mid - cam2.location).to_track_quat("-Z", "Y").to_euler()
scene.render.filepath = os.path.join(out, "dark16_logo_lit.png")
bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0]); scene.render.filepath, scene.render.resolution_percentage = keep[1], keep[2]
