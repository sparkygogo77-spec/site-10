"""Builds Lantern Live, a ready-to-open Blender scene of the pixel-grid Blue Lantern for J's own PC
(his GPU renders it live): the lantern on a dark stone floor, key and rim lights, the lantern's own
blue light spilling from its windows, bloom on the glass, and a charge animation driven by one
"charge" control (rest, build-up, flash at the climax, settle), with a turntable to switch on.
Also writes lantern_model.npz, the model data the Lantern Live Link add-on reloads whenever
Claude changes the lantern.

    python tools/blender/live_scene.py <out dir>

Writes <out dir>/lantern_live.blend and <out dir>/lantern_model.npz.
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pixel_blue_lantern as L
import bpy
from mathutils import Vector

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
L.build(0.5)
quads, qcol, qkind = L.pixel_quads()
np.savez_compressed(os.path.join(OUT, "lantern_model.npz"), quads=np.asarray(quads, np.float32),
                    col=np.asarray(qcol, np.float32), kind=np.asarray(qkind, np.int8))

bpy.ops.wm.read_factory_settings()
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
scene.name = "Lantern Live"
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 240

# ---- the lantern (in blocks: the model's units are 1/16 block) --------------------------------------
verts = np.array(quads).reshape(-1, 3)
me = bpy.data.meshes.new("lantern")
me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
lin = (np.array(qcol) / 255) ** 2.2
attr = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
attr.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())


def material(name, metal, glow):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Ln = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute")
    at.attribute_name = "col"
    if glow:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        Ln.new(at.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.6
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["Coat Weight"].default_value = 1.0
    else:
        Ln.new(at.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.42 if metal else 0.88
        bsdf.inputs["Metallic"].default_value = 0.8 if metal else 0.0
    return m


MATS = [material("stone", False, False), material("metal", True, False), material("glow", False, True)]
for m in MATS:
    me.materials.append(m)
me.polygons.foreach_set("material_index", qkind)
lantern = bpy.data.objects.new("Lantern", me)
lantern.scale = (1 / 16,) * 3
scene.collection.objects.link(lantern)

# ---- the controls: one empty with the charge and turntable sliders -----------------------------------
ctl = bpy.data.objects.new("Lantern Controls", None)
ctl.empty_display_type = "SPHERE"
ctl.empty_display_size = 0.1
ctl.location = (1.4, 0, 0.1)
scene.collection.objects.link(ctl)
ctl["charge"] = 0.0
ctl["turntable"] = 1.0
ui = ctl.id_properties_ui("charge")
ui.update(min=0.0, max=1.5, soft_min=0.0, soft_max=1.3, description="0 at rest, 1 fully charged, above 1 the climax flash")
ctl.id_properties_ui("turntable").update(min=0.0, max=1.0, description="1 spins the camera round the lantern, 0 holds it still")


def drive(owner, path, expr, index=-1):
    fc = owner.driver_add(path, index) if index >= 0 else owner.driver_add(path)
    d = fc.driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "c"
    v.type = "SINGLE_PROP"
    v.targets[0].id_type = "OBJECT"
    v.targets[0].id = ctl
    v.targets[0].data_path = '["charge"]'
    t = d.variables.new()
    t.name = "tt"
    t.type = "SINGLE_PROP"
    t.targets[0].id_type = "OBJECT"
    t.targets[0].id = ctl
    t.targets[0].data_path = '["turntable"]'
    d.expression = expr
    return fc


# the glass: a steady glow at rest that builds, breathes once lit and blazes at the climax
glow_in = MATS[2].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
drive(glow_in, "default_value", "1.6 + 2.4 * c + 0.3 * min(c, 1) * sin(frame * 0.21)")

# ---- the room ---------------------------------------------------------------------------------------------
fm = bpy.data.meshes.new("floor")
fm.from_pydata([(-12, -12, 0), (12, -12, 0), (12, 12, 0), (-12, 12, 0)], [], [[0, 1, 2, 3]])
floor = bpy.data.objects.new("Floor", fm)
scene.collection.objects.link(floor)
f_mat = bpy.data.materials.new("floor")
f_mat.use_nodes = True
fb = f_mat.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.018, 0.02, 0.026, 1)
fb.inputs["Roughness"].default_value = 0.35
fm.materials.append(f_mat)

world = bpy.data.worlds.new("Night")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.008, 0.016, 1)


def light(kind, name, loc, power, size=1.0, color=(1, 1, 1), target=(0, 0, 0.72)):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = power
    ld.color = color
    if kind == "AREA":
        ld.size = size
    else:
        ld.shadow_soft_size = size
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ld


light("AREA", "Key", (-1.9, -2.4, 2.6), 35, 1.6)
light("AREA", "Rim", (1.4, 2.1, 1.9), 27, 1.1, (0.55, 0.7, 1.0))
# the lantern's own light, just outside each window: it spills onto the floor and the frame
for i, p in enumerate([(0, -0.52, 0.71), (0, 0.52, 0.71), (0.52, 0, 0.71), (-0.52, 0, 0.71)]):
    ld = light("POINT", f"Window light {i + 1}", p, 3.5, 0.12, (0.25, 0.55, 1.0))
    drive(ld, "energy", "3.5 + 16 * c")

# ---- the camera on a turntable --------------------------------------------------------------------------
rig = bpy.data.objects.new("Turntable", None)
scene.collection.objects.link(rig)
drive(rig, "rotation_euler", "tt * frame / 240 * 6.2832", 2)
cam_d = bpy.data.cameras.new("Camera")
cam_d.lens = 85
cam = bpy.data.objects.new("Camera", cam_d)
scene.collection.objects.link(cam)
cam.parent = rig
cam.location = (-2.1, -3.9, 1.6)
cam.rotation_euler = (Vector((0, 0, 0.78)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# ---- the charge, keyframed on the control: rest, build-up, flash, settle --------------------------------
for f, c in ((1, 0.0), (30, 0.0), (170, 1.0), (176, 1.3), (200, 0.45), (240, 0.25)):
    ctl["charge"] = c
    ctl.keyframe_insert('["charge"]', frame=f)
for kp in ctl.animation_data.action.fcurves[0].keyframe_points if hasattr(ctl.animation_data.action, "fcurves") else []:
    kp.interpolation = "BEZIER"
scene.frame_set(1)

# ---- render settings: real-time on the GPU, bloom in the compositor -------------------------------------
for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.cycles.device = "GPU"
scene.cycles.samples = 128
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.resolution_x, scene.render.resolution_y = 1080, 1350
try:
    tree = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
    scene.compositing_node_group = tree
except Exception:
    scene.use_nodes = True
    tree = scene.node_tree
for n in list(tree.nodes):
    tree.nodes.remove(n)
rl = tree.nodes.new("CompositorNodeRLayers")
glare = tree.nodes.new("CompositorNodeGlare")
for key, val in (("Type", "Bloom"), ("Quality", "High"), ("Threshold", 0.85), ("Strength", 0.55), ("Size", 0.7)):
    try:
        glare.inputs[key].default_value = val
    except Exception:
        pass
try:
    out = tree.nodes.new("NodeGroupOutput")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
except Exception:
    out = tree.nodes.new("CompositorNodeComposite")
tree.links.new(rl.outputs["Image"], glare.inputs[0])
tree.links.new(glare.outputs[0], out.inputs[0])

# open looking through the camera, in the live render view, with bloom showing
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "RENDERED"
                    try:
                        sp.shading.use_compositor = "ALWAYS"
                    except Exception:
                        pass
                    sp.region_3d.view_perspective = "CAMERA"
                    sp.overlay.show_overlays = False

# the Lantern Live Link add-on, inside the file too, so it can be run from the Text Editor
here = os.path.dirname(os.path.abspath(__file__))
txt = bpy.data.texts.new("lantern_live_link.py")
txt.from_string(open(os.path.join(here, "lantern_live_link.py")).read())

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "lantern_live.blend"), compress=True)
print("wrote", os.path.join(OUT, "lantern_live.blend"))
