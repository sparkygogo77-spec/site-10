# Pass 39: three runner options side by side, all sprinting (J wants several options every round):
#   A gaunt (pass 38's), B brute (thicker, bigger horns and spines), C wraith (thin, long claws, tall spines).
# Builds each from dread_runner_<v>.npz with pass 38's rig, stride and trail, then renders a lineup.
import os
import bpy
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name.startswith("Runner"):
        bpy.data.objects.remove(o, do_unlink=True)

src = open(os.path.join(FOLDER, "38_dread_runner2.update.py"), encoding="utf-8").read()
rig = src[:src.index("out_dir = ")]                 # everything but pass 38's renders
OFFSETS = {"a": -4.5, "b": 0.0, "c": 4.5}
for v, dx in OFFSETS.items():
    code = (rig.replace('"dread_runner.npz"', f'"dread_runner_{v}.npz"')
               .replace("ORIGIN = Vector((-30.0, 34.0, 0.0))", f"ORIGIN = Vector(({-30.0 + dx}, 34.0, 0.0))")
               .replace('"Runner', f'"Runner{v.upper()}'))
    exec(compile(code, f"runner_{v}", "exec"), {"bpy": bpy, "np": np, "FOLDER": FOLDER, "__name__": "runner"})

cam_data = bpy.data.cameras.new("RunnerLineup Camera"); cam_data.lens = 35
cam = bpy.data.objects.new("RunnerLineup Camera", cam_data)
scene.collection.objects.link(cam)
out_dir = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 60
shots = {
    "side": (Vector((-30 + 12.0, 34 + 6.0, 2.2)), Vector((-30, 34, 1.3))),
    "front": (Vector((-30 + 1.0, 34 + 13.0, 1.0)), Vector((-30, 34, 1.4))),
}
for tag, (at, target) in shots.items():
    cam.location = at
    cam.rotation_euler = (target - at).to_track_quat("-Z", "Y").to_euler()
    for f in (2, 5, 8):
        scene.frame_set(f)
        scene.render.filepath = os.path.join(out_dir, f"options_{tag}_f{f:02d}.png")
        bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
