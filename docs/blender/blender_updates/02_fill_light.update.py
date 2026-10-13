# Pass 2: a soft cool fill from the front so the stone frame edges read at night,
# and a slightly gentler key so the bronze cap stops washing out.
import bpy
from mathutils import Vector
scene = bpy.context.scene
key = bpy.data.objects.get("Key")
if key:
    key.data.energy = 26
fill = bpy.data.objects.get("Fill")
if fill is None:
    ld = bpy.data.lights.new("Fill", "AREA")
    fill = bpy.data.objects.new("Fill", ld)
    scene.collection.objects.link(fill)
fill.data.energy = 14
fill.data.size = 2.5
fill.data.color = (0.62, 0.72, 1.0)
fill.location = (1.6, -3.2, 0.9)
fill.rotation_euler = (Vector((0, 0, 0.7)) - fill.location).to_track_quat("-Z", "Y").to_euler()
scene.frame_set(1)
