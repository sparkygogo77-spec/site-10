# Pass 4: the White Constructs walls, as the game draws them. Six 9x9 Wall-mode walls edge to
# edge (27 x 18 blocks), off to the side of the lantern, with their own camera. The smoke texture
# spans 8 x 8 blocks and is sliced by world position like the mod does, so it runs across every
# block seam; it flows at the game's speed (one texture frame per 6 ticks, blended like the game's
# "interpolate"). Lantern view: set the "Camera" back as the scene camera.
import os
import bpy
import numpy as np

scene = bpy.context.scene
tex_path = os.path.join(FOLDER, "construct_flow.png")
FRAMES = 48
PERIOD = 8.0                                # blocks the texture spans
SEC_PER_FRAME = 6 / 20                      # 6 game ticks
ORIGIN = (40.0, 0.0, 0.0)                   # walls stand here, away from the lantern

# ---- the walls: one mesh of 27 x 18 one-block cubes ---------------------------------------------
old = bpy.data.objects.get("Construct Walls")
if old:
    bpy.data.objects.remove(old)
W, H = 27, 18
verts, faces = [], []
def cube(x, z):
    b = len(verts)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                verts.append((x + dx, dy, z + dz))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        faces.append(tuple(b + i for i in f))
for x in range(W):
    for z in range(H):
        cube(x - W // 2, z)
me = bpy.data.meshes.new("construct_walls")
me.from_pydata(verts, [], faces)
me.validate()
walls = bpy.data.objects.new("Construct Walls", me)
walls.location = ORIGIN
scene.collection.objects.link(walls)

# ---- the material: the flow strip, sampled at (world x, world z) / 4 blocks ---------------------
img = bpy.data.images.get("construct_flow.png")
if img is None:
    img = bpy.data.images.load(tex_path)
else:
    img.filepath = tex_path
    img.reload()
mat = bpy.data.materials.get("construct_flow") or bpy.data.materials.new("construct_flow")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
N, L = nt.nodes, nt.links
out = N.new("ShaderNodeOutputMaterial")
emit = N.new("ShaderNodeEmission")
emit.inputs["Strength"].default_value = 1.6
L.new(emit.outputs[0], out.inputs["Surface"])

geo = N.new("ShaderNodeNewGeometry")
sep = N.new("ShaderNodeSeparateXYZ")
L.new(geo.outputs["Position"], sep.inputs[0])

def math(op, a, b=None, val=None):
    n = N.new("ShaderNodeMath")
    n.operation = op
    for i, src in enumerate((a, b)):
        if src is None:
            continue
        if isinstance(src, (int, float)):
            n.inputs[i].default_value = src
        else:
            L.new(src, n.inputs[i])
    return n.outputs[0]

# frame clock: f = time / SEC_PER_FRAME; a = floor(f) mod 48, b = a + 1, blend = fract(f)
clock = N.new("ShaderNodeValue")
clock.label = "frame clock"
fc = clock.outputs[0].driver_add("default_value")
fc.driver.type = "SCRIPTED"
fc.driver.expression = f"frame / ({scene.render.fps} * {SEC_PER_FRAME})"
fl = math("FLOOR", clock.outputs[0])
blend = math("SUBTRACT", clock.outputs[0], fl)

u = math("FRACT", math("DIVIDE", sep.outputs["X"], PERIOD))
v = math("FRACT", math("DIVIDE", sep.outputs["Z"], PERIOD))

def frame_sample(index):
    # frame i sits (47 - i) frames up from the bottom of the strip
    i = math("MODULO", index, float(FRAMES))
    vv = math("DIVIDE", math("ADD", v, math("SUBTRACT", float(FRAMES - 1), i)), float(FRAMES))
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(u, comb.inputs[0])
    L.new(vv, comb.inputs[1])
    t = N.new("ShaderNodeTexImage")
    t.image = img
    t.interpolation = "Closest"
    t.extension = "CLIP"
    L.new(comb.outputs[0], t.inputs["Vector"])
    return t.outputs["Color"]

ca = frame_sample(fl)
cb = frame_sample(math("ADD", fl, 1.0))
mix = N.new("ShaderNodeMix")
mix.data_type = "RGBA"
L.new(blend, mix.inputs["Factor"])
L.new(ca, mix.inputs[6])
L.new(cb, mix.inputs[7])
L.new(mix.outputs[2], emit.inputs["Color"])
me.materials.append(mat)

# ---- a camera looking straight at the walls -----------------------------------------------------
cam = bpy.data.objects.get("Walls Camera")
if cam is None:
    cd = bpy.data.cameras.new("Walls Camera")
    cam = bpy.data.objects.new("Walls Camera", cd)
    scene.collection.objects.link(cam)
cam.data.lens = 35
cam.location = (ORIGIN[0], -40.0, 9.0)
cam.rotation_euler = (1.5708, 0.0, 0.0)
scene.camera = cam
scene.frame_end = max(scene.frame_end, int(FRAMES * SEC_PER_FRAME * scene.render.fps))
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
            a.tag_redraw()
