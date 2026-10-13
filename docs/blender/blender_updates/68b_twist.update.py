# Pass 68b (68 again, finding objects by name prefix): a slight spiral in the lantern's pinched glass (J: "just a slight spiral in the pinched part for
# more depth and feel, as slight as it can be twisted, a few options"). A row left of the charge row, each a
# copy of G1 (same charge, same light) with the glass twisted round its axis; the handle and top stay put.
#   T0  no twist (to compare)   T1 4 degrees   T2 8 degrees   T3 14 degrees, top to bottom
# Camera "Cam twist" looks at them; still to renders/68_twist.png.
import os, math
import bpy
from mathutils import Vector

scene = bpy.context.scene
def find(prefix):
    """By name prefix: after a file switch Blender may have added .001 to the names."""
    for o in scene.objects:
        if o.name.startswith(prefix):
            return o
    return None


src = find("Charge lantern F1")
for o in list(bpy.data.objects):
    if o.name.startswith(("Twist T", "Label T")):
        bpy.data.objects.remove(o, do_unlink=True)
ROW = Vector((-14.0, 0.0, 0.0))     # to the left of the charge row
for i, (name, deg) in enumerate((("T0", 0), ("T1", 4), ("T2", 8), ("T3", 14))):
    o = src.copy()
    o.animation_data_clear()
    o.name = f"Twist {name}"
    scene.collection.objects.link(o)
    o.location = ROW + Vector((i * 2.6, 0, 0))
    if deg:
        m = o.modifiers.new("twist", "SIMPLE_DEFORM")
        m.deform_method = "TWIST"
        m.deform_axis = "Z"
        m.angle = math.radians(deg)
        m.limits = (0.03, 0.80)          # the glass only: the handle and top plate stay straight
    cu = bpy.data.curves.new(f"T label {name}", "FONT")
    cu.body = f"{name}  {deg} deg" if deg else "T0  no twist"
    cu.size = 0.2; cu.align_x = "CENTER"
    lb = bpy.data.objects.new(f"Label T {name}", cu)
    lb.location = o.location + Vector((0, 0, 2.3)); lb.rotation_euler = (math.radians(90), 0, 0)
    lm = bpy.data.materials.get("charge label F1") or bpy.data.materials.new("twist label")
    cu.materials.append(lm)
    scene.collection.objects.link(lb)

fl = find("Charge floor")
if fl and not bpy.data.objects.get("Twist floor"):
    f2 = fl.copy(); f2.name = "Twist floor"; scene.collection.objects.link(f2)
    f2.location = ROW + Vector((3.9, 0, 0))
cd = bpy.data.cameras.new("Cam twist"); cd.lens = 50
cam = bpy.data.objects.new("Cam twist", cd)
scene.collection.objects.link(cam)
target = ROW + Vector((3.9, 0, 1.0))
cam.location = target + Vector((0, -14.0, 1.0))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
keep = scene.camera
scene.camera = cam
scene.frame_set(250)
scene.render.filepath = os.path.join(FOLDER, "renders", "68_twist.png")
bpy.ops.render.render(write_still=True)
scene.frame_set(1)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
            a.tag_redraw()
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
