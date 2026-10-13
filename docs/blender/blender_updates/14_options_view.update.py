# Pass 14: tidy the options view: smaller labels centred over each wall, the old jade wall and its
# smoke hidden while comparing (not deleted), and a camera that frames all four walls.
import bpy
from mathutils import Vector
scene = bpy.context.scene
for o in bpy.data.objects:
    if o.type == "FONT" and o.data.body[:1] in "ABCD" and "  " in o.data.body:
        o.data.size = 0.55
        o.data.align_x = "CENTER"
for name in ("Jade Blocks", "Smoke Skin Wall", "Smoke Skin Cube", "Jade Light"):
    o = bpy.data.objects.get(name)
    if o:
        o.hide_set(True)
        o.hide_render = True
walls = [bpy.data.objects.get(f"Option {s}") for s in "ABCD"]
walls = [w for w in walls if w]
lo = min(w.location.x for w in walls)
hi = max(w.location.x for w in walls) + 4
centre = Vector(((lo + hi) / 2, walls[0].location.y + 0.5, 1.9))
cam = bpy.data.objects["Options Camera"]
cam.data.lens = 30
cam.location = centre + Vector((0.0, -24.0, 4.0))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
                    sp.shading.type = "RENDERED"
            a.tag_redraw()
