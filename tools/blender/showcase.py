"""A showcase render of the pixel-grid Blue Lantern in Blender: standing on dark stone with its own
blue light spilling onto the floor and the frame, the glass glowing and blooming, at rest and at
the height of a charge.

    python tools/blender/showcase.py <out dir> [--samples 128]

Writes blue_lantern_rest.png, blue_lantern_charged.png and blue_lantern_showcase.png (both side
by side).
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pixel_blue_lantern as L
import bpy
from mathutils import Vector

OUT = sys.argv[1]
SAMPLES = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 128
os.makedirs(OUT, exist_ok=True)
L.build(0.5)
quads, qcol, qkind = L.pixel_quads()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
verts = np.array(quads).reshape(-1, 3)
me = bpy.data.meshes.new("lantern")
me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
lin = (np.array(qcol) / 255) ** 2.2
attr = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
cols = np.repeat(lin, 4, axis=0)
attr.data.foreach_set("color", np.hstack([cols, np.ones((len(cols), 1))]).ravel())


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
        bsdf.inputs["Emission Strength"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["Coat Weight"].default_value = 1.0
    else:
        Ln.new(at.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.42 if metal else 0.88
        bsdf.inputs["Metallic"].default_value = 0.8 if metal else 0.0
    return m


GLOW = material("glow", False, True)
for m in (material("stone", False, False), material("metal", True, False), GLOW):
    me.materials.append(m)
me.polygons.foreach_set("material_index", qkind)
lantern = bpy.data.objects.new("lantern", me)
scene.collection.objects.link(lantern)

# a dark polished stone floor that catches the lantern's light
fm = bpy.data.meshes.new("floor")
fm.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [[0, 1, 2, 3]])
floor = bpy.data.objects.new("floor", fm)
scene.collection.objects.link(floor)
f_mat = bpy.data.materials.new("floor")
f_mat.use_nodes = True
fb = f_mat.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.018, 0.02, 0.026, 1)
fb.inputs["Roughness"].default_value = 0.35
fm.materials.append(f_mat)

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.008, 0.016, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0


def light(kind, name, loc, power, size=1.0, color=(1, 1, 1), target=(0, 0, 11)):
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


key = light("AREA", "key", (-30, -38, 42), 9000, 26)
rim = light("AREA", "rim", (22, 34, 30), 7000, 18, (0.55, 0.7, 1.0))
# the lantern's own light, just outside each window so it spills onto the floor and the frame
inner = [light("POINT", f"window_{i}", p, 0, 2.0, (0.25, 0.55, 1.0))
         for i, p in enumerate([(0, -8.2, 11.4), (0, 8.2, 11.4), (8.2, 0, 11.4), (-8.2, 0, 11.4)])]

scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.resolution_x, scene.render.resolution_y = 1080, 1350
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 85
cam = bpy.data.objects.new("cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (-34, -62, 26)
cam.rotation_euler = (Vector((0, 0, 12.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()

# bloom in the compositor: a soft fog glow over everything bright
try:
    tree = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    scene.compositing_node_group = tree
except Exception:
    scene.use_nodes = True
    tree = scene.node_tree
N = tree.nodes
for n in list(N):
    N.remove(n)
rl = N.new("CompositorNodeRLayers")
glare = N.new("CompositorNodeGlare")
glare.inputs["Type"].default_value = "Bloom"
glare.inputs["Quality"].default_value = "High"
glare.inputs["Threshold"].default_value = 0.85
glare.inputs["Strength"].default_value = 0.55
glare.inputs["Size"].default_value = 0.7
try:
    out = N.new("NodeGroupOutput")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    tree.links.new(rl.outputs["Image"], glare.inputs[0])
    tree.links.new(glare.outputs[0], out.inputs[0])
except Exception:
    out = N.new("CompositorNodeComposite")
    tree.links.new(rl.outputs["Image"], glare.inputs[0])
    tree.links.new(glare.outputs[0], out.inputs[0])

shots = []
for name, glow, spill in (("rest", 1.6, 900), ("charged", 3.6, 4500)):
    GLOW.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = glow
    for l in inner:
        l.energy = spill
    scene.render.filepath = os.path.join(OUT, f"blue_lantern_{name}.png")
    bpy.ops.render.render(write_still=True)
    shots.append(scene.render.filepath)

from PIL import Image
ims = [Image.open(p).convert("RGB") for p in shots]
both = Image.new("RGB", (ims[0].width * 2, ims[0].height))
for i, im in enumerate(ims):
    both.paste(im, (i * im.width, 0))
both.save(os.path.join(OUT, "blue_lantern_showcase.png"))
print("wrote", os.path.join(OUT, "blue_lantern_showcase.png"))
