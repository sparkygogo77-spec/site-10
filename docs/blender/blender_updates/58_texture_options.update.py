# Pass 58: texture options in their own file (J: "do R2 and several new texture variants", "the white
# smoke lines can be a better colour, maybe dark so it blends in with the jade", "the bull also needs our
# better textures", "make a ton of new texture options in its own blender file you open for me").
# Every face is the real game texture (tools/construct_texture_options.py): the ripple frame over the
# cloudy jade, 4 x 4 blocks. Rows are styles, columns colourways; the last row is the red set on walls
# and on the Rage Bull. Builds a "Texture Options" scene, writes LanternLive\texture_options.blend,
# saves your current file and opens the new one. Your old file is untouched apart from that save.
import json, os
import bpy
from mathutils import Vector

TEX = os.path.join(FOLDER, "texture_options")
OUT = os.path.join(FOLDER, "texture_options.blend")
opts = json.load(open(os.path.join(TEX, "options.json")))
STYLE_ROWS = ["R1", "R2", "R3", "S1", "S2"]
COLS = ["W", "K1", "K2", "K3", "K4", "K5"]
STYLE_NAMES = {"R1": "R1 mixed (today)", "R2": "R2 small fragments", "R3": "R3 large, slow",
               "S1": "S1 silk", "S2": "S2 grain"}
COL_NAMES = {"W": "W white (today)", "K1": "K1 dark jade", "K2": "K2 deep forest", "K3": "K3 dark + mint rim",
             "K4": "K4 jade tone", "K5": "K5 shadow haze"}
STEP = 5.5

if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER, "lantern_work_backup.blend"), copy=True)

old = bpy.data.scenes.get("Texture Options")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Texture Options")
col = scene.collection


def link(o):
    col.objects.link(o)
    return o


def material(key, solid=False):
    m = bpy.data.materials.new("tex " + key)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    p = N.new("ShaderNodeBsdfPrincipled")
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, f"face_{key}.png"), check_existing=True)
    img.interpolation = "Closest"
    tc = N.new("ShaderNodeTexCoord")
    if solid:          # the bull: box projection in object space, 4 blocks per texture
        img.projection = "BOX"
        img.projection_blend = 0.15
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
        L.new(tc.outputs["Object"], mp.inputs["Vector"])
        L.new(mp.outputs["Vector"], img.inputs["Vector"])
    else:              # a wall: its front face, x across and z up
        sep = N.new("ShaderNodeSeparateXYZ")
        cmb = N.new("ShaderNodeCombineXYZ")
        L.new(tc.outputs["Generated"], sep.inputs[0])
        L.new(sep.outputs["X"], cmb.inputs["X"])
        L.new(sep.outputs["Z"], cmb.inputs["Y"])
        L.new(cmb.outputs[0], img.inputs["Vector"])
    L.new(img.outputs["Color"], p.inputs["Base Color"])
    L.new(img.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = 0.9
    p.inputs["Roughness"].default_value = 0.25
    if solid:
        mth = N.new("ShaderNodeMath")
        mth.operation = "MULTIPLY_ADD"
        mth.use_clamp = True
        L.new(img.outputs["Alpha"], mth.inputs[0])
        mth.inputs[1].default_value = 1.2
        mth.inputs[2].default_value = 0.35
        L.new(mth.outputs[0], p.inputs["Alpha"])
    else:
        L.new(img.outputs["Alpha"], p.inputs["Alpha"])
    L.new(p.outputs[0], out.inputs[0])
    return m


def wall(key, loc):
    me = bpy.data.meshes.new("wall " + key)
    o = link(bpy.data.objects.new("Option " + key, me))
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    o.scale = (4.0, 0.3, 4.0)
    o.location = loc
    me.materials.append(material(key))
    return o


def label(text, loc, size=0.42, colr=(0.85, 1.0, 0.9)):
    cu = bpy.data.curves.new(text, "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    o = link(bpy.data.objects.new("Label " + text, cu))
    o.location = loc
    o.rotation_euler = (1.5708, 0, 0)
    m = bpy.data.materials.new("label " + text)
    m.use_nodes = True
    pr = m.node_tree.nodes.get("Principled BSDF")
    pr.inputs["Emission Color"].default_value = colr + (1,)
    pr.inputs["Emission Strength"].default_value = 3.0
    cu.materials.append(m)
    return o


by_key = {o["key"]: o for o in opts}
for r, sk in enumerate(STYLE_ROWS):
    z = -r * STEP
    label(STYLE_NAMES[sk], Vector((-STEP * 0.95, 0, z)), 0.5)
    for c, ck in enumerate(COLS):
        key = f"{sk}_{ck}"
        if key in by_key:
            x = c * STEP
            wall(key, Vector((x, 0, z)))
            label(key, Vector((x, -0.2, z + 2.3)))
for c, ck in enumerate(COLS):
    label(COL_NAMES[ck], Vector((c * STEP, 0, 3.3)), 0.45, (1.0, 1.0, 0.8))

# the red set: walls, then the Rage Bull in three of them
reds = [o["key"] for o in opts if o["red"]]
zr = -len(STYLE_ROWS) * STEP - 1.0
label("RED (Rage Bull / Red constructs)", Vector((-STEP * 0.95, 0, zr)), 0.42, (1, 0.8, 0.75))
for i, key in enumerate(reds):
    x = i * (STEP * 0.75)
    w = wall(key, Vector((x, 0, zr)))
    w.scale = (3.0, 0.3, 3.0)
    label(key, Vector((x, -0.2, zr + 1.8)), 0.36, (1, 0.85, 0.8))

zb = zr - STEP * 1.25
bulls = ["RED_R2_K1", "RED_R2_K3", "RED_R1_K1", "RED_R1_W"]
glb = os.path.join(TEX, "rage_bull.glb")
win = bpy.context.window
if win:
    win.scene = scene
for i, key in enumerate(bulls):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    holder = link(bpy.data.objects.new("Bull " + key, None))
    mat = material(key, solid=True)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None:
            o.parent = holder
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(mat)
    holder.scale = (2.0, 2.0, 2.0)
    holder.location = Vector((i * STEP * 1.4, 0, zb - 1.6))
    holder.rotation_euler = (0, 0, 1.25)
    label(key + " bull", Vector((i * STEP * 1.4, -0.2, zb + 2.6)), 0.45, (1, 0.85, 0.8))

# room, light, cameras
world = bpy.data.worlds.new("Options World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.035, 0.045, 0.06, 1)
bg.inputs[1].default_value = 1.0
scene.world = world
sun = bpy.data.lights.new("Options Sun", "SUN")
sun.energy = 2.5
so = link(bpy.data.objects.new("Options Sun", sun))
so.rotation_euler = (0.9, 0.2, 0.4)
floor = bpy.data.meshes.new("backdrop")
import bmesh
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
bm.to_mesh(floor)
bm.free()
fo = link(bpy.data.objects.new("Backdrop", floor))
fo.rotation_euler = (1.5708, 0, 0)
fo.location = (STEP * 2.5, 3.0, -15)
fm = bpy.data.materials.new("backdrop")
fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.08, 0.1, 0.12, 1)
floor.materials.append(fm)


def camera(name, target, dist, lens=35):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cam = link(bpy.data.objects.new(name, cd))
    cam.location = target + Vector((0, -dist, 0))
    cam.rotation_euler = (1.5708, 0, 0)
    return cam


centre_x = STEP * 2.5
cams = {
    "overview": camera("Cam overview", Vector((centre_x, 0, -STEP * 2.6)), 62),
    "R1R2": camera("Cam R1 R2", Vector((centre_x, 0, -STEP * 0.5)), 34),
    "R3S1S2": camera("Cam R3 S1 S2", Vector((centre_x, 0, -STEP * 3)), 44),
    "red": camera("Cam red + bull", Vector((STEP * 3.2, 0, zr - STEP * 0.9)), 40),
}
scene.camera = cams["R1R2"]
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = "AgX"
except Exception:
    pass

rdir = os.path.join(FOLDER, "renders")
os.makedirs(rdir, exist_ok=True)
for k, cam in (cams.items() if not os.environ.get('LL_NO_RENDER') else ()):
    scene.camera = cam
    scene.render.filepath = os.path.join(rdir, f"58_tex_{k}.png")
    bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["R1R2"]

# make this its own file: your current file was saved above; drop its scenes from memory and save as
# texture_options.blend (your old file on disk keeps everything)
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
                    sp.shading.type = "MATERIAL"
            a.tag_redraw()
print("texture options saved as", OUT)
