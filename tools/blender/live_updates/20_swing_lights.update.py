# Pass 20: lights that walk with the swinging lantern (it was walking through the dark), then fresh
# stills into renders/ so Claude can check.
import os
import bpy
from mathutils import Vector
scene = bpy.context.scene
carrier = bpy.data.objects["Swing Carrier"]
for name, loc, e, size, col in (("Swing Key", (-1.5, -3.0, 3.6), 180, 2.5, (1, 0.95, 0.88)),
                                ("Swing Rim", (1.8, 2.6, 2.8), 120, 1.6, (0.6, 0.75, 1.0))):
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
        scene.collection.objects.link(o)
    o.data.energy, o.data.size, o.data.color = e, size, col
    o.parent = carrier
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 1.4)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
out = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = bpy.data.objects.get("Swing Camera") or scene.camera
scene.render.resolution_percentage = 50
for f in (12, 34, 190):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"swinglit_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
