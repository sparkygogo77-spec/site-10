# Pass 22: the Dark Lantern recreated from J's two concept renders: F1 as in the renders, F2 deeper
# waist and a wider glow, F3 more gold. Standing in a row with their own camera ("Dark Camera") and
# lights, using the charge-lit jade materials from pass 21. Stills at rest and charged go to renders/.
import os
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
ROW = Vector((-16.5, 34.0, 0.0))
mats = [bpy.data.materials.get(n) for n in ("stone", "metal", "glow", "dark_fleck", "dark_body", "dark_crack")]
for i, v in enumerate(("f1", "f2", "f3")):
    name = f"Dark {v.upper()}"
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o)
    d = np.load(os.path.join(FOLDER, f"dark4_{v}.npz"))
    q = d["quads"]
    verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
    o = bpy.data.objects.new(name, me)
    o.scale = (1 / 16,) * 3
    o.location = ROW + Vector((i * 1.8, 0, 0))
    o.rotation_euler = (0, 0, np.radians(-20))
    scene.collection.objects.link(o)

centre = ROW + Vector((1.8, 0, 1.1))
for name, off, e, size, col in (("Dark Key", (-2.2, -3.4, 3.4), 220, 3.0, (1, 0.95, 0.88)),
                                ("Dark Rim", (2.6, 2.4, 2.6), 140, 2.0, (0.6, 0.75, 1.0)),
                                ("Dark Fill", (0.5, -4.5, 0.6), 50, 4.0, (0.9, 0.95, 1.0))):
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
        scene.collection.objects.link(o)
    o.data.energy, o.data.size, o.data.color = e, size, col
    o.location = centre + Vector(off)
    o.rotation_euler = (centre - o.location).to_track_quat("-Z", "Y").to_euler()

cam = bpy.data.objects.get("Dark Camera")
if cam is None:
    cam = bpy.data.objects.new("Dark Camera", bpy.data.cameras.new("Dark Camera"))
    scene.collection.objects.link(cam)
cam.data.lens = 45
cam.location = centre + Vector((0.0, -7.2, 0.9))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()

out = os.path.join(FOLDER, "renders")
os.makedirs(out, exist_ok=True)
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 60
for f, tag in ((12, "rest"), (170, "charged")):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out, f"dark4_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage = keep[1], keep[2]
scene.camera = cam
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
            a.tag_redraw()
