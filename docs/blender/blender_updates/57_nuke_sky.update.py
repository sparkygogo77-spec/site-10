# Pass 57 (J: the nuke is held and formed in the sky; stay within 30 blocks or it cancels): the raised ring
# hand on the ground, a hard-light tether up to the bomb assembling 16 blocks overhead, 14 blocks ahead, the
# 30-block range marked on the ground. Was pass 52 (nuke take 5: plate positions match their turn, closing the gap). Was pass 51 (nuke take 4: the first plates no longer stay hidden). Was pass 50 (nuke take 3: thin seams, a closed shell). Was pass 49 (nuke take 2: twice the pixels, a fat bomb shape, a clear plate grid, bigger fins, calmer light). Was pass 48: the Fear Nuke being constructed in the ring hand (J): the arm raised and locked, the ring on the
# fist, a dark core forming, then yellow hard-light plates flying in from all round and locking into place,
# tail first, the fins and tail ring last, the light building as it closes up. 48 frames.
# Stills renders/nukesky_f*.png. Also rifle take 3 (glow back on its edges) via pass 45 -> weapons4_*.
import os, math, random
import bpy
import numpy as np
from mathutils import Vector, Euler

scene = bpy.context.scene
R = math.radians
BASE = Vector((-90.0, 54.0, 0.0))
S = 8.0 / 16                       # in the sky the bomb is huge: about 7 blocks long
for o in list(bpy.data.objects):
    if o.name.startswith("Nukebuild"):
        bpy.data.objects.remove(o, do_unlink=True)
MATS = [bpy.data.materials.get(n) for n in ("runner_dark", "runner_dark", "runner_dark", "runner_dark",
                                           "runner_amber", "runner_amber", "runner_edge", "runner_eye")]

# The arm: a Minecraft arm, raised straight up, skin and a green sleeve.
def box(name, size, at, colour, emit=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = colour
    b.inputs["Roughness"].default_value = 0.8
    if emit:
        b.inputs["Emission Color"].default_value = colour; b.inputs["Emission Strength"].default_value = emit
    o.data.materials.append(m)
    return o


box("Nukebuild arm", (0.25, 0.25, 0.5), BASE + Vector((0, 0, 0.55)), (0.12, 0.45, 0.16, 1))
box("Nukebuild hand", (0.25, 0.25, 0.25), BASE + Vector((0, 0, 0.92)), (0.85, 0.62, 0.48, 1))
ring = bpy.data.objects.get("Ring option a")
if ring:
    r2 = ring.copy(); r2.data = ring.data; r2.animation_data_clear()
    r2.name = "Nukebuild ring"; r2.scale = (1 / 16,) * 3
    r2.location = BASE + Vector((0, -0.05, 0.95)); r2.rotation_euler = (R(90), 0, 0)
    scene.collection.objects.link(r2)

d = np.load(os.path.join(FOLDER, "nuke_build.npz"))
centre = BASE + Vector((0, 14, 16))
rnd = random.Random(7)
FR = 48
for n in range(int(d["count"])):
    q = d[f"q{n}"]
    if not len(q):
        continue
    verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(f"Nukebuild plate {n}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d[f"c{n}"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for m in MATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d[f"k{n}"], np.int32))
    o = bpy.data.objects.new(f"Nukebuild plate {n}", me)
    scene.collection.objects.link(o)
    piv = Vector(d[f"pivot{n}"])
    home = centre + Vector((-piv.z, piv.y, piv.x)) * S         # stand the bomb up (matches the -90 deg turn about y)
    o.rotation_mode = "XYZ"
    home_rot = Euler((0, R(-90), 0))
    order = float(d[f"order{n}"])
    o.scale = (S,) * 3
    if n == 49:                                                        # the dark core (part 49): grows in place
        for f, s in ((1, 0.0), (10, 1.0)):
            o.location = home; o.rotation_euler = home_rot; o.scale = (S * max(s, 0.001),) * 3
            o.keyframe_insert("scale", frame=f)
        o.keyframe_insert("location", frame=1); o.keyframe_insert("rotation_euler", frame=1)
        continue
    arrive = 13 + order * 30          # take 4: the first plates no longer key before frame 1 (they stayed hidden)
    out = (home - centre).normalized() if (home - centre).length > 1e-3 else Vector((0, 0, 1))
    start = home + out * (8.0 + rnd.random() * 6.0) + Vector((0, 0, 3.0))
    spin = Euler((R(rnd.uniform(-160, 160)), R(rnd.uniform(-160, 160)), R(rnd.uniform(-160, 160))))
    o.scale = (S * 0.001,) * 3; o.keyframe_insert("scale", frame=max(1, arrive - 11))
    o.scale = (S,) * 3; o.keyframe_insert("scale", frame=arrive - 10)
    o.location = start; o.rotation_euler = spin
    o.keyframe_insert("location", frame=arrive - 10); o.keyframe_insert("rotation_euler", frame=arrive - 10)
    o.location = home; o.rotation_euler = home_rot
    o.keyframe_insert("location", frame=arrive); o.keyframe_insert("rotation_euler", frame=arrive)

# The tether: a beam of hard light from the raised ring up to the forming bomb.
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1.0)
teth = bpy.context.active_object; teth.name = "Nukebuild tether"
a, b = BASE + Vector((0, -0.05, 1.05)), centre + Vector((0, 0, -3.2))
teth.location = (a + b) / 2
teth.scale = (1, 1, (b - a).length)
teth.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
tm = bpy.data.materials.new("nukebuild_tether"); tm.use_nodes = True
tb = tm.node_tree.nodes.get("Principled BSDF")
tb.inputs["Emission Color"].default_value = (1.0, 0.8, 0.2, 1); tb.inputs["Emission Strength"].default_value = 12.0
teth.data.materials.append(tm)
for f, s_ in ((1, 0.001), (4, 1.0)):
    teth.scale = (1, 1, (b - a).length * s_); teth.keyframe_insert("scale", frame=f)
# The 30-block range around the nuke, on the ground.
bpy.ops.mesh.primitive_torus_add(major_radius=30.0, minor_radius=0.12, location=Vector((centre.x, centre.y, BASE.z + 0.05)))
rng = bpy.context.active_object; rng.name = "Nukebuild range"
rm = bpy.data.materials.new("nukebuild_range"); rm.use_nodes = True
rb = rm.node_tree.nodes.get("Principled BSDF")
rb.inputs["Emission Color"].default_value = (1.0, 0.65, 0.1, 1); rb.inputs["Emission Strength"].default_value = 6.0
rng.data.materials.append(rm)
lamp = bpy.data.lights.new("Nukebuild glow", "POINT"); lamp.color = (1.0, 0.75, 0.15)
lo = bpy.data.objects.new("Nukebuild glow", lamp); lo.location = centre + Vector((0, -1.2, 0))
scene.collection.objects.link(lo)
for f, e in ((1, 50), (20, 1500), (40, 4000), (48, 6000)):
    lamp.energy = e; lamp.keyframe_insert("energy", frame=f)

cd = bpy.data.cameras.new("Nukebuild Camera"); cd.lens = 22
cam = bpy.data.objects.new("Nukebuild Camera", cd)
scene.collection.objects.link(cam)
cam.location = BASE + Vector((1.6, -4.5, 1.4))
cam.rotation_euler = (centre + Vector((0, -2, -6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
out_dir = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 60
for f in (6, 18, 30, 42, 48):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"nukesky_f{f:02d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]

