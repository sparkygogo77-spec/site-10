# Pass 54: more crown options (J picked ring B): B as is, B1 cathedral (6 tall prongs), B2 gold claws,
# B3 a halo of small gems, B4 emerald cut on a black band.
# Pass 47 (take 3 again: faces tilted TOWARD the camera, and the calmer rifle file). Was pass 46 (rings take 3: camera back, faces tilted up to it, softer light; and the construct rifle take 2). Was pass 44 (rings take 2: looking down on the faces, brighter, clear background). Was pass 42: three Power Ring options on a turntable (J: "I need a better lantern ring model"), shown 3x size:
#   A forged (bevelled band, hexagonal bezel, flame sigil), B crown (claw prongs on a glowing gem),
#   C sleek (black band with a glowing channel, ring-of-light face). Original emblems.
# Also re-runs pass 40 for the 1911 with its full-length grip and smaller trigger guard.
import os, math
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
R = math.radians
BASE = Vector((-70.0, 54.0, 0.0))
for o in list(bpy.data.objects):
    if o.name.startswith("Ring option"):
        bpy.data.objects.remove(o, do_unlink=True)


def mat(name, metallic, rough, emit, base=None):
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


dark = mat("ring_dark", 0.0, 0.5, 0)
metal = mat("ring_metal", 0.9, 0.22, 0)
green = mat("ring_green", 0.0, 0.1, 4.0)
bright = mat("ring_bright", 0.0, 0.1, 10.0)
MATS = [dark, metal, dark, dark, green, green, bright]

FR = 48
rings = []
for i, v in enumerate(("b", "b1", "b2", "b3", "b4")):
    d = np.load(os.path.join(FOLDER, f"ring_{v}.npz"))
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new(f"Ring option {v}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for m in MATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
    o = bpy.data.objects.new(f"Ring option {v}", me)
    o.scale = (3 / 16,) * 3
    o.location = BASE + Vector(((i - 2) * 2.7, 0, 1.4))
    o.rotation_euler = (R(58), 0, 0)
    scene.collection.objects.link(o)
    for f in (1, FR + 1):
        o.rotation_euler.z = R(360 * (f - 1) / FR)
        o.keyframe_insert("rotation_euler", index=2, frame=f)
    ad = o.animation_data
    for fc in getattr(ad.action, "fcurves", []):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
    rings.append(o)
    lamp = bpy.data.lights.new(f"Ring option {v} glow", "POINT")
    lamp.color = (0.3, 1.0, 0.4); lamp.energy = 15
    lo = bpy.data.objects.new(f"Ring option {v} glow", lamp)
    lo.location = o.location + Vector((0, 0, 1.6))
    scene.collection.objects.link(lo)

key = bpy.data.lights.new("Ring option key", "AREA"); key.energy = 350; key.size = 6
ko = bpy.data.objects.new("Ring option key", key)
ko.location = BASE + Vector((2, -5, 6))
ko.rotation_euler = (BASE + Vector((0, 0, 1)) - ko.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(ko)

cd = bpy.data.cameras.new("Ring option Camera"); cd.lens = 50
cam = bpy.data.objects.new("Ring option Camera", cd)
scene.collection.objects.link(cam)
out_dir = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 70
cam.location = BASE + Vector((0, -14.5, 6.5))
cam.rotation_euler = (BASE + Vector((0, 0, 1.3)) - cam.location).to_track_quat("-Z", "Y").to_euler()
for f in (1, 7, 13, 25):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"crowns_f{f:02d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]


