# Pass 30: fully metallic gold went black in this dark room (it only reflects the room). Back to a
# bright gold that still reflects: metallic 0.8, roughness 0.28, a faint warm sheen from the world.
# Then fresh stills, and the top close-up re-aimed.
import os
import bpy
from mathutils import Vector
scene = bpy.context.scene
gm = bpy.data.materials.get("metal")
for n_ in gm.node_tree.nodes:
    if n_.type == "BSDF_PRINCIPLED":
        n_.inputs["Metallic"].default_value = 0.8
        n_.inputs["Roughness"].default_value = 0.28
        n_.inputs["Coat Weight"].default_value = 0.4
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.03, 0.033, 0.045, 1)
out = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.render.resolution_percentage = 60
scene.camera = bpy.data.objects["Dark Camera"]
for f, tag in ((12, "rest"), (170, "charged")):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"dark12_{tag}.png")
    bpy.ops.render.render(write_still=True)
ob = bpy.data.objects["Dark L1"]
cam2 = bpy.data.objects["Detail Camera"]
scene.camera = cam2
scene.frame_set(12)
for tag, local, off in (("top", (0, 0, 23.0), (0.25, -1.9, 2.4)), ("front", (0, 0, 11.75), (0.25, -1.6, 0.1))):
    target = ob.matrix_world @ Vector(local)
    cam2.location = target + Vector(off)
    cam2.rotation_euler = (target - cam2.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out, f"dark12_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
