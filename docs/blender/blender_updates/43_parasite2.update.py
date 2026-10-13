# Pass 43: fear parasite iteration 2: 18 segments, a stronger S-coil and vertical undulation, a closer camera.
import os, math
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
R = math.radians
out_dir = os.path.join(FOLDER, "renders")
for o in list(bpy.data.objects):
    if o.name.startswith("Parasite"):
        bpy.data.objects.remove(o, do_unlink=True)
# 3. The fear parasites.
MATS = [bpy.data.materials.get(n) for n in ("runner_dark", "runner_dark", "runner_dark", "runner_dark",
                                           "runner_amber", "runner_amber", "runner_edge", "runner_eye")]
PBASE = Vector((-30.0, 62.0, 0.0))
FR = 24
for vi, v in enumerate("abc"):
    d = np.load(os.path.join(FOLDER, f"fear_parasite_{v}.npz"))
    pn = [str(n) for n in d["names"]]; par = d["parents"]; piv = d["pivots"]
    root = bpy.data.objects.new(f"Parasite {v}", None)
    root.location = PBASE + Vector(((vi - 1) * 7.0, 0, 0)); root.scale = (1 / 16,) * 3
    scene.collection.objects.link(root)
    E = []
    for n, name in enumerate(pn):
        e = bpy.data.objects.new(f"Parasite {v} pivot {name}", None)
        p = int(par[n])
        e.parent = root if p < 0 else E[p]
        e.location = Vector(piv[n]) - (Vector((0, 0, 0)) if p < 0 else Vector(piv[p]))
        scene.collection.objects.link(e)
        E.append(e)
        q = d[f"q{n}"]
        if not len(q):
            continue
        verts = q.reshape(-1, 3)
        me = bpy.data.meshes.new(f"Parasite {v} {name}")
        me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
        lin = (np.asarray(d[f"c{n}"], np.float32) / 255.0) ** 2.2
        a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
        a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
        for m in MATS:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", np.asarray(d[f"k{n}"], np.int32))
        o = bpy.data.objects.new(f"Parasite {v} {name}", me)
        o.parent = e
        scene.collection.objects.link(o)
    byname = dict(zip(pn, E))
    for f in range(FR + 1):
        p = 2 * math.pi * f / FR
        for i in range(sum(1 for x in pn if x.startswith("seg"))):
            e = byname[f"seg{i}"]
            e.rotation_euler = (R(9 * math.sin(2 * p - 0.45 * i)), 0, R(19 * math.sin(p - 0.42 * i)))
            e.keyframe_insert("rotation_euler", frame=1 + f)
        h = byname["head"]
        h.rotation_euler = (R(4 * math.sin(2 * p)), 0, R(-9 * math.sin(p + 0.4)))
        h.keyframe_insert("rotation_euler", frame=1 + f)
        j = byname["jaw"]
        j.rotation_euler = (R(-(6 + 34 * max(0.0, math.sin(2 * p)) ** 0.6)), 0, 0)
        j.keyframe_insert("rotation_euler", frame=1 + f)
        root.location.z = PBASE.z + 0.15 * math.sin(p)
        root.keyframe_insert("location", index=2, frame=1 + f)
    lamp = bpy.data.lights.new(f"Parasite {v} glow", "POINT")
    lamp.color = (1.0, 0.72, 0.12); lamp.energy = 90
    lo = bpy.data.objects.new(f"Parasite {v} glow", lamp)
    lo.parent = byname["head"]; lo.location = (0, 8, 2)
    scene.collection.objects.link(lo)


cd = bpy.data.cameras.new("Parasite Camera"); cam = bpy.data.objects.new("Parasite Camera", cd)
scene.collection.objects.link(cam)
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 70


def shoot(tag, at, target, lens):
    cd.lens = lens
    cam.location = at
    cam.rotation_euler = (target - at).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out_dir, tag + ".png")
    bpy.ops.render.render(write_still=True)


for vi, v in enumerate("abc"):
    c = PBASE + Vector(((vi - 1) * 7.0, -2.0, 1.4))
    for f in (4, 13):
        scene.frame_set(f)
        shoot(f"parasite2_{v}_f{f:02d}", c + Vector((5.5, 5.0, 2.6)), c, 35)
scene.frame_set(7)
shoot("parasite2_maw", PBASE + Vector((0, 6.5, 1.7)), PBASE + Vector((0, 0, 1.5)), 45)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
