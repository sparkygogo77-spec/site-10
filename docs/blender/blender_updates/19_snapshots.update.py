# Pass 19: Claude looks without screen access. Renders a few stills of the swing on your graphics card
# into LanternLive/renders/, which Claude reads straight from the folder. Leaves your view as it was.
import os
import bpy
scene = bpy.context.scene
out = os.path.join(FOLDER, "renders")
os.makedirs(out, exist_ok=True)
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
cam = bpy.data.objects.get("Swing Camera")
if cam:
    scene.camera = cam
scene.render.resolution_percentage = 50
for f in (12, 34, 60, 110, 190, 215):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"swing_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
