# Pass 18: the Dark Lantern (E1, lit) carried and swinging exactly as the game swings a lantern in
# your off hand. The swing is the mod's own LanternSway, run tick by tick (20 per second): every tick
# the swing speed keeps 86% of itself, is pulled back by 14% of the angle, and is pushed by how the
# player speeds up, turns and steps; the angle never passes 40 degrees.
# The walk, 10 s: stand, start walking, walk, turn right while walking, walk, stop, stand.
# Camera "Swing Camera" rides along; press Space to play.
import math, os
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
FPS = scene.render.fps
TICKS = 200
START = Vector((-14.0, 24.0, 0.0))

for n in ("Swing Carrier", "Swing Pivot", "Dark E1", "Swing Camera", "Swing Ground"):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)

# ---- the walk and the sway, as the game computes them --------------------------------------------
STIFF, DAMP = 0.14, 0.86
vel = np.zeros((TICKS, 2))
yaw = np.zeros(TICKS)
for t in range(TICKS):
    walking = 20 <= t < 150
    target = 0.215 if walking else 0.0                     # blocks per tick, a normal walk
    prev = np.hypot(*vel[t - 1]) if t else 0.0
    speed = prev + np.clip(target - prev, -0.08, 0.05)     # speeding up takes a few ticks, stopping is quicker
    yaw[t] = (yaw[t - 1] if t else 0.0) + (4.5 if 70 <= t < 90 else 0.0)
    a = math.radians(yaw[t])
    vel[t] = (speed * math.cos(a), speed * math.sin(a))
pos = np.cumsum(vel, axis=0)
roll = pitch = rollV = pitchV = 0.0
rolls, pitches = [], []
for t in range(TICKS):
    pv = vel[t - 1] if t else np.zeros(2)
    acc = vel[t] - pv
    a = math.radians(yaw[t])
    fwd = acc[0] * math.cos(a) + acc[1] * math.sin(a)
    right = acc[0] * math.sin(a) - acc[1] * math.cos(a)
    dyaw = yaw[t] - (yaw[t - 1] if t else 0.0)
    speed = np.hypot(*vel[t])
    rollV += -STIFF * roll + dyaw * 0.35 + right * 90
    pitchV += -STIFF * pitch - fwd * 120 + math.sin(t * 0.65) * speed * 6
    rollV *= DAMP
    pitchV *= DAMP
    roll = max(-40, min(40, roll + rollV))
    pitch = max(-40, min(40, pitch + pitchV))
    rolls.append(roll)
    pitches.append(pitch)

# ---- objects: a carrier walking the path, the pivot at the handle, the lantern hanging from it ----
carrier = bpy.data.objects.new("Swing Carrier", None)
scene.collection.objects.link(carrier)
pivot = bpy.data.objects.new("Swing Pivot", None)
pivot.empty_display_type = "SPHERE"
pivot.empty_display_size = 0.05
scene.collection.objects.link(pivot)
pivot.parent = carrier
pivot.location = (0, 0, 2.3)

d = np.load(os.path.join(FOLDER, "dark2_e1_lit.npz"))
q = d["quads"]
verts = q.reshape(-1, 3)
me = bpy.data.meshes.new("dark_e1")
me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
at = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
at.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
for mname in ("stone", "metal", "glow"):
    me.materials.append(bpy.data.materials.get(mname))
me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
top = float(verts[:, 2].max())
lantern = bpy.data.objects.new("Dark E1", me)
lantern.scale = (1 / 16,) * 3
lantern.rotation_euler = (0, 0, math.radians(-90))       # its front (the port) faces the walking side
lantern.location = (0, 0, -top / 16)                     # hang it from the top of its handle
scene.collection.objects.link(lantern)
lantern.parent = pivot

# ground with a grid so the walking shows
gm = bpy.data.meshes.new("swing_ground")
gm.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new("Swing Ground", gm)
ground.location = START + Vector((10, 0, -0.001))
scene.collection.objects.link(ground)
gmat = bpy.data.materials.get("swing_grid") or bpy.data.materials.new("swing_grid")
gmat.use_nodes = True
nt = gmat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
chk = nt.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 120
chk.inputs["Color1"].default_value = (0.03, 0.035, 0.04, 1)
chk.inputs["Color2"].default_value = (0.05, 0.06, 0.07, 1)
nt.links.new(chk.outputs["Color"], bs.inputs["Base Color"])
nt.links.new(bs.outputs[0], out.inputs["Surface"])
gm.materials.append(gmat)

# ---- keyframes, one per frame, from the 20-per-second ticks ----------------------------------------
frames = int(TICKS / 20 * FPS)
for f in range(frames + 1):
    tk = f / FPS * 20
    i = min(int(tk), TICKS - 2)
    w = tk - i
    lerp = lambda arr: arr[i] * (1 - w) + arr[i + 1] * w
    p = (1 - w) * pos[i] + w * pos[i + 1]
    carrier.location = START + Vector((p[0], p[1], 0))
    carrier.rotation_euler = (0, 0, math.radians(lerp(yaw)))
    carrier.keyframe_insert("location", frame=f + 1)
    carrier.keyframe_insert("rotation_euler", frame=f + 1)
    # the carrier walks along its own +x. Pitch (negative while speeding up) swings the bottom back:
    # a turn about the side axis y. Roll (positive when pushed right) swings the bottom left (+y):
    # a turn about the walking axis x.
    pivot.rotation_mode = "XYZ"
    pivot.rotation_euler = (math.radians(lerp(rolls)), math.radians(-lerp(pitches)), 0.0)
    pivot.keyframe_insert("rotation_euler", frame=f + 1)
for ob in (carrier, pivot):
    if ob.animation_data and ob.animation_data.action:
        try:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        except Exception:
            pass
scene.frame_start, scene.frame_end = 1, frames + 1

# ---- a camera riding alongside -----------------------------------------------------------------------
cam = bpy.data.objects.new("Swing Camera", bpy.data.cameras.new("Swing Camera"))
cam.data.lens = 40
scene.collection.objects.link(cam)
cam.parent = carrier
cam.location = (0.4, -4.2, 1.9)
cam.rotation_euler = (Vector((0, 0, 1.55)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.frame_set(1)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
            a.tag_redraw()
