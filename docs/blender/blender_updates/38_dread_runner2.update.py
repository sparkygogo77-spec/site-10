# Pass 38 (37 redone: hips under the lean, feet on the ground, darker scarier light, soft trail): the Yellow Blast's runner (J: "sprinting in a scary pace blasting through whatever I aim him at,
# he destroys things and leaves fear on the ground"). An original gaunt fear construct of yellow hard
# light, in jointed parts from dread_runner.npz (tools/pixel_dread_runner.py), with:
#  - a sprint cycle: 12 frames = 0.5 s a stride, hunched forward, clawed arms raking back and forth
#  - a fear trail on the ground behind it: yellow-black smoke light
#  - a "Runner Camera"
# Stills of the stride go to renders/runner_f*.png, and an action shot to renders/runner_action.png.
import os, math
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
ORIGIN = Vector((-30.0, 34.0, 0.0))
STRIDE = 12

d = np.load(os.path.join(FOLDER, "dread_runner.npz"))
names = [str(n) for n in d["names"]]
parents = d["parents"]
pivots = d["pivots"]

for o in list(bpy.data.objects):
    if o.name.startswith("Runner"):
        bpy.data.objects.remove(o, do_unlink=True)


def mat(name, base_emit, alpha=1.0, rough=0.3):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    col = N.new("ShaderNodeAttribute"); col.attribute_name = "col"
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(col.outputs["Color"], b.inputs["Base Color"])
    L.new(col.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = base_emit
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.6
    b.inputs["Alpha"].default_value = alpha
    L.new(b.outputs[0], out.inputs["Surface"])
    if alpha < 1.0:
        m.surface_render_method = "BLENDED"
    return m


dark = mat("runner_dark", 0.05)
amber = mat("runner_amber", 0.35, alpha=0.92)
edge = mat("runner_edge", 2.2)
eye = mat("runner_eye", 30.0)
MATS = [dark, dark, dark, dark, amber, amber, edge, eye]

root = bpy.data.objects.new("Runner", None)
root.location = ORIGIN
root.scale = (1 / 16,) * 3
scene.collection.objects.link(root)

piv_obj = []
for n, name in enumerate(names):
    e = bpy.data.objects.new(f"Runner pivot {name}", None)
    e.empty_display_size = 1.5
    p = int(parents[n])
    e.parent = root if p < 0 else piv_obj[p]
    e.location = Vector(pivots[n]) - (Vector((0, 0, 0)) if p < 0 else Vector(pivots[p]))
    e.rotation_mode = "XYZ"
    scene.collection.objects.link(e)
    piv_obj.append(e)

    q = d[f"q{n}"]
    verts = q.reshape(-1, 3)
    me = bpy.data.meshes.new(f"Runner {name}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d[f"c{n}"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for m in MATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.asarray(d[f"k{n}"], np.int32))
    o = bpy.data.objects.new(f"Runner {name}", me)
    o.parent = e
    scene.collection.objects.link(o)

P = {name: piv_obj[i] for i, name in enumerate(names)}
R = math.radians


def pose(f):
    """The stride at frame f (0..STRIDE): angles in degrees about each joint."""
    p = 2 * math.pi * f / STRIDE
    s, c = math.sin(p), math.cos(p)
    return {
        "torso": (-38 + 4 * math.sin(2 * p), 0, 6 * s),
        "head": (34 + 5 * math.sin(2 * p + 1.2), 0, -5 * s),
        # The hips flex to bring the legs back under the forward lean.
        "thigh_l": (34 + 48 * s, 0, 0), "thigh_r": (34 - 48 * s, 0, 0),
        "shin_l": (-20 - 70 * (0.5 + 0.5 * math.cos(p + 0.9)), 0, 0),
        "shin_r": (-20 - 70 * (0.5 - 0.5 * math.cos(p + 0.9)), 0, 0),
        # Clawed arms raking back and forth, held low and wide.
        "arm_l": (20 - 50 * s, -18, 0), "arm_r": (20 + 50 * s, 18, 0),
        "fore_l": (45 + 30 * max(0.0, s), 0, 0), "fore_r": (45 + 30 * max(0.0, -s), 0, 0),
    }, 1.6 * abs(math.sin(p))


for f in range(STRIDE + 1):
    angles, bob = pose(f)
    frame = 1 + f
    for name, (rx, ry, rz) in angles.items():
        e = P[name]
        e.rotation_euler = (R(rx), R(ry), R(rz))
        e.keyframe_insert("rotation_euler", frame=frame)
    # Feet on the ground: drop the body until the lowest foot touches the floor.
    t = P["torso"]
    t.location = Vector(pivots[0])
    bpy.context.view_layer.update()
    low = min((o.matrix_world @ Vector(c)).z for nm in ("shin_l", "shin_r")
              for o in [bpy.data.objects[f"Runner {nm}"]] for c in o.bound_box)
    t.location = Vector(pivots[0]) + Vector((0, 0, -(low - ORIGIN.z) * 16 + 0.6 * bob))
    t.keyframe_insert("location", frame=frame)
for e in piv_obj:
    ad = e.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            fc.modifiers.new("CYCLES")

# The fear left on the ground behind it: a strip of yellow-black smoke light.
for nm in ("Runner fear trail",):
    o = bpy.data.objects.get(nm)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=1, location=ORIGIN + Vector((0, -7.5, 0.02)))
trail = bpy.context.active_object
trail.name = "Runner fear trail"
trail.scale = (3.6, 14, 1)
fm = bpy.data.materials.get("runner_fear") or bpy.data.materials.new("runner_fear")
fm.use_nodes = True
N, L = fm.node_tree.nodes, fm.node_tree.links
N.clear()
out = N.new("ShaderNodeOutputMaterial")
tc = N.new("ShaderNodeTexCoord")
noise = N.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 6.0; noise.inputs["Detail"].default_value = 8.0
L.new(tc.outputs["Object"], noise.inputs["Vector"])
ramp = N.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.38; ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (1.0, 0.62, 0.02, 1)
L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
em = N.new("ShaderNodeEmission"); L.new(ramp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 3.0
tr = N.new("ShaderNodeBsdfTransparent")
grad = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], grad.inputs[0])
def m_(op, a, b=None):
    n = N.new("ShaderNodeMath"); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]
side = m_("POWER", m_("SUBTRACT", 1.0, m_("ABSOLUTE", m_("SUBTRACT", m_("MULTIPLY", grad.outputs[0], 2.0), 1.0))), 0.8)
along = m_("POWER", grad.outputs[1], 1.5)                     # strongest right behind the runner
mask = m_("MULTIPLY", m_("MULTIPLY", side, along), m_("ADD", 0.3, noise.outputs["Fac"]))
class _F: pass
fade = _F(); fade.outputs = [mask]
mix = N.new("ShaderNodeMixShader")
L.new(fade.outputs[0], mix.inputs["Fac"])
L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
L.new(mix.outputs[0], out.inputs["Surface"])
fm.surface_render_method = "BLENDED"
trail.data.materials.append(fm)

light = bpy.data.lights.get("Runner glow") or bpy.data.lights.new("Runner glow", "POINT")
light.color = (1.0, 0.72, 0.1); light.energy = 140; light.shadow_soft_size = 0.6
lo = bpy.data.objects.new("Runner glow", light)
lo.parent = P["torso"]; lo.location = (0, 6, 8)
scene.collection.objects.link(lo)

cam_data = bpy.data.cameras.new("Runner Camera"); cam_data.lens = 42
cam = bpy.data.objects.new("Runner Camera", cam_data)
cam.location = ORIGIN + Vector((7.5, 4.5, 2.0))
scene.collection.objects.link(cam)
look = ORIGIN + Vector((0, 0, 1.3)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()

out_dir = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 50
for f in (1, 3, 5, 7, 9, 11):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"runner2_f{f:02d}.png")
    bpy.ops.render.render(write_still=True)
# An action shot: low, from ahead and to the side, mid-stride.
cam.location = ORIGIN + Vector((-3.5, 6.5, 0.6))
look = ORIGIN + Vector((0, -1.0, 1.4)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
scene.frame_set(4)
scene.render.filepath = os.path.join(out_dir, "runner2_action.png")
bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
