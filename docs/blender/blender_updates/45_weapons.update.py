# Pass 45: the yellow construct weapons the fear gas hands out (an AK-style rifle and a crossbow) and the
# 1911 again from the side (pass 40's side camera looked down the barrel). Renders renders/weapons_*.png.
import os
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
BASE = Vector((-70.0, 70.0, 1.2))
for o in list(bpy.data.objects):
    if o.name.startswith("Weapon"):
        bpy.data.objects.remove(o, do_unlink=True)
M = {k: bpy.data.materials.get(n) for k, n in ((0, "pistol_matte"), (1, "pistol_metal"), (4, "pistol_hard"), (6, "pistol_edge"))}
MATS = [M[0], M[1], M[0], M[0], M[4], M[4], M[6]]


def load(name, at, rot=(0, 0, 0)):
    d = np.load(os.path.join(FOLDER, name + ".npz"))
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new(f"Weapon {name}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for m in MATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
    o = bpy.data.objects.new(f"Weapon {name}", me)
    o.scale = (1 / 16,) * 3
    o.location = at
    o.rotation_euler = rot
    scene.collection.objects.link(o)
    return o


load("construct_rifle", BASE + Vector((0, 0, 0)))
load("construct_crossbow", BASE + Vector((2.6, 0, 0)))
for i, f in enumerate(("blued", "steel", "construct")):
    load(f"pistol_1911_{f}", BASE + Vector((-0.5 + i * 1.2, 0, -0.9)))

key = bpy.data.lights.new("Weapon key", "AREA"); key.energy = 500; key.size = 5
ko = bpy.data.objects.new("Weapon key", key)
ko.location = BASE + Vector((1.0, -4.0, 4.0))
ko.rotation_euler = (BASE + Vector((1.0, 0, 0)) - ko.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(ko)

cd = bpy.data.cameras.new("Weapon Camera"); cd.lens = 50
cam = bpy.data.objects.new("Weapon Camera", cd)
scene.collection.objects.link(cam)
out_dir = os.path.join(FOLDER, "renders")
keep = (scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 70
centre = BASE + Vector((1.0, 0, -0.3))
for tag, at in (("side", Vector((0, -5.5, 0.3))), ("34", Vector((3.0, -4.0, 2.2)))):
    cam.location = centre + at
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out_dir, f"weapons_{tag}.png")
    bpy.ops.render.render(write_still=True)
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep
