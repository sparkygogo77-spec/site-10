# Pass 40: the 1911 item (J), three finishes side by side: blued with walnut, stainless with black grips,
# yellow hard-light construct. Real metal for the steel ones (metallic, low roughness), glowing for the
# construct. Stills to renders/pistol_side.png and renders/pistol_34.png.
import os
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
BASE = Vector((-30.0, 46.0, 1.0))
for o in list(bpy.data.objects):
    if o.name.startswith("Pistol"):
        bpy.data.objects.remove(o, do_unlink=True)


def mat(name, metallic, rough, emit):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    col = N.new("ShaderNodeAttribute"); col.attribute_name = "col"
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(col.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        L.new(col.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    L.new(b.outputs[0], out.inputs["Surface"])
    return m


matte = mat("pistol_matte", 0.0, 0.6, 0)
metal = mat("pistol_metal", 0.85, 0.3, 0)
hard = mat("pistol_hard", 0.0, 0.25, 0.8)
edge = mat("pistol_edge", 0.0, 0.25, 3.0)
MATS = [matte, metal, matte, matte, hard, hard, edge]

for i, f in enumerate(("blued", "steel", "construct")):
    d = np.load(os.path.join(FOLDER, f"pistol_1911_{f}.npz"))
    q = d["quads"]
    verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(f"Pistol {f}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for m in MATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
    o = bpy.data.objects.new(f"Pistol {f}", me)
    o.scale = (1 / 16,) * 3
    o.location = BASE + Vector((i * 1.4, 0, 0))
    scene.collection.objects.link(o)

lamp = bpy.data.lights.get("Pistol key") or bpy.data.lights.new("Pistol key", "AREA")
lamp.energy = 120; lamp.size = 2.0
lo = bpy.data.objects.new("Pistol key", lamp)
lo.location = BASE + Vector((1.4, -2.0, 2.5))
lo.rotation_euler = (BASE + Vector((1.4, 0, 0)) - lo.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(lo)

cd = bpy.data.cameras.new("Pistol Camera"); cd.lens = 60
cam = bpy.data.objects.new("Pistol Camera", cd)
scene.collection.objects.link(cam)
out_dir = os.path.join(FOLDER, "renders")
keep = (scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 60
centre = BASE + Vector((1.4, 0, 0))
for tag, at in (("side", Vector((0, -4.6, 0.1))), ("34", Vector((2.4, -3.0, 1.7)))):
    cam.location = centre + at
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out_dir, f"pistol_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep
