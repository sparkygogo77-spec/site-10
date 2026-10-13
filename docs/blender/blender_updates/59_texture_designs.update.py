# Pass 59: construct designs, round two, ANIMATED (J: "why do the designs all look so similar? ... none of
# this is even animated in blender yet ... I need tons of variety"). Nineteen designs built different ways
# (tools/construct_designs.py) plus J's two keepers for reference (K5 = R1 K5, K1 = R2 K1). Each wall plays
# the real 24-frame game loop (press Space to play; the timeline is set to loop). The bottom row is the
# Rage Bull in red: J's R2 K1 pick and six of the new designs.
# Builds a "Texture Designs" scene, saves the open file, then saves this as LanternLive\texture_designs.blend.
import json, os
import bpy, bmesh
from mathutils import Vector

TEX = os.path.join(FOLDER, "texture_designs")
OUT = os.path.join(FOLDER, "texture_designs.blend")
designs = json.load(open(os.path.join(TEX, "designs.json")))
COLS = 6
STEP = 5.5
HOLD = 2                      # Blender frames per game frame (24 fps): a 2 s loop

if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER, "lantern_work_backup.blend"), copy=True)

old = bpy.data.scenes.get("Texture Designs")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Texture Designs")
col = scene.collection


def link(o):
    col.objects.link(o)
    return o


def principled(m, colour_out, alpha_out, emit=0.9):
    nt = m.node_tree
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(colour_out, p.inputs["Base Color"])
    nt.links.new(colour_out, p.inputs["Emission Color"])
    nt.links.new(alpha_out, p.inputs["Alpha"])
    p.inputs["Emission Strength"].default_value = emit
    p.inputs["Roughness"].default_value = 0.2
    nt.links.new(p.outputs[0], out.inputs[0])
    return p


def animated_material(key):
    """The 24-frame strip on a wall's front face, stepping one game frame every HOLD Blender frames."""
    m = bpy.data.materials.new("design " + key)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, f"face_{key}.png"), check_existing=True)
    img.interpolation = "Closest"
    img.extension = "REPEAT"
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    frame = N.new("ShaderNodeValue")
    frame.label = "game frame"
    d = frame.outputs[0].driver_add("default_value").driver
    d.type = "SCRIPTED"
    d.expression = f"floor(fmod(frame - 1, {24 * HOLD}) / {HOLD})"
    # v in the strip: frame 0 is the top 1/24th of the image
    v1 = N.new("ShaderNodeMath"); v1.operation = "MULTIPLY"; v1.inputs[1].default_value = 1 / 24
    L.new(sep.outputs["Z"], v1.inputs[0])
    v2 = N.new("ShaderNodeMath"); v2.operation = "SUBTRACT"; v2.inputs[0].default_value = 23
    L.new(frame.outputs[0], v2.inputs[1])
    v3 = N.new("ShaderNodeMath"); v3.operation = "MULTIPLY_ADD"; v3.inputs[1].default_value = 1 / 24
    L.new(v2.outputs[0], v3.inputs[0]); L.new(v1.outputs[0], v3.inputs[2])
    cmb = N.new("ShaderNodeCombineXYZ")
    L.new(sep.outputs["X"], cmb.inputs["X"]); L.new(v3.outputs[0], cmb.inputs["Y"])
    L.new(cmb.outputs[0], img.inputs["Vector"])
    principled(m, img.outputs["Color"], img.outputs["Alpha"])
    return m


def still_material(name, path):
    """A still on a solid (the bull): box projection in object space, 4 blocks per texture."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(path, check_existing=True)
    img.interpolation = "Closest"
    img.projection = "BOX"; img.projection_blend = 0.15
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], img.inputs["Vector"])
    a = N.new("ShaderNodeMath"); a.operation = "MULTIPLY_ADD"; a.use_clamp = True
    L.new(img.outputs["Alpha"], a.inputs[0]); a.inputs[1].default_value = 1.2; a.inputs[2].default_value = 0.35
    principled(m, img.outputs["Color"], a.outputs[0])
    return m


def wall(key, loc):
    me = bpy.data.meshes.new("design wall " + key)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new("Design " + key, me))
    o.scale = (4.0, 0.3, 4.0); o.location = loc
    me.materials.append(animated_material(key))
    return o


def label(text, loc, size=0.4, colr=(0.85, 1.0, 0.9)):
    cu = bpy.data.curves.new(text, "FONT")
    cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = link(bpy.data.objects.new("Label " + text, cu))
    o.location = loc; o.rotation_euler = (1.5708, 0, 0)
    m = bpy.data.materials.new("label " + text); m.use_nodes = True
    pr = m.node_tree.nodes.get("Principled BSDF")
    pr.inputs["Emission Color"].default_value = colr + (1,)
    pr.inputs["Emission Strength"].default_value = 3.0
    cu.materials.append(m)
    return o


rows = (len(designs) + COLS - 1) // COLS
for i, d in enumerate(designs):
    c, r = i % COLS, i // COLS
    loc = Vector((c * STEP, 0, -r * STEP))
    wall(d["key"], loc)
    keeper = d["key"] in ("K1", "K5")
    label(d["label"], loc + Vector((0, -0.2, 2.35)), 0.3, (1.0, 0.95, 0.6) if keeper else (0.85, 1.0, 0.9))

# the Rage Bull row
win = bpy.context.window
if win:
    win.scene = scene
zb = -rows * STEP - 2.5
glb = os.path.join(TEX, "rage_bull.glb")
bulls = [("K1", "R2 K1 (J's pick)"), ("P1", "P1 plating"), ("F1", "F1 facets"), ("X1", "X1 fractured"),
         ("G2", "G2 caustic glass"), ("C2", "C2 cel"), ("M1", "M1 mech")]
for i, (key, name) in enumerate(bulls):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    holder = link(bpy.data.objects.new("Bull " + key, None))
    mat = still_material("bull " + key, os.path.join(TEX, f"red_{key}.png"))
    for o in new:
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None:
            o.parent = holder
        if o.type == "MESH":
            o.data.materials.clear(); o.data.materials.append(mat)
    holder.scale = (1.7, 1.7, 1.7)
    holder.location = Vector((i * STEP * 0.95 - 1.0, 0, zb - 1.4))
    holder.rotation_euler = (0, 0, 1.25)
    label("bull: " + name, Vector((i * STEP * 0.95 - 1.0, -0.2, zb + 2.2)), 0.36, (1, 0.85, 0.8))

# room, light, cameras
world = bpy.data.worlds.new("Designs World"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.03, 0.04, 0.055, 1); bg.inputs[1].default_value = 1.0
scene.world = world
sun = bpy.data.lights.new("Designs Sun", "SUN"); sun.energy = 2.0
link(bpy.data.objects.new("Designs Sun", sun)).rotation_euler = (0.9, 0.2, 0.4)
fl = bpy.data.meshes.new("designs backdrop")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=70); bm.to_mesh(fl); bm.free()
fo = link(bpy.data.objects.new("Backdrop", fl)); fo.rotation_euler = (1.5708, 0, 0)
fo.location = (STEP * 2.5, 3.0, -15)
fm = bpy.data.materials.new("designs backdrop"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.07, 0.09, 0.11, 1)
fl.materials.append(fm)


def camera(name, target, dist, lens=35):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    cam = link(bpy.data.objects.new(name, cd))
    cam.location = target + Vector((0, -dist, 0)); cam.rotation_euler = (1.5708, 0, 0)
    return cam


cx = STEP * 2.5
cams = {"rows12": camera("Cam rows 1-2", Vector((cx, 0, -STEP * 0.5)), 34),
        "rows34": camera("Cam rows 3-4", Vector((cx, 0, -STEP * 2.5)), 34),
        "bulls": camera("Cam bulls", Vector((STEP * 2.7, 0, zb - 0.5)), 42),
        "overview": camera("Cam overview", Vector((cx, 0, -STEP * 2.2)), 66)}
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.frame_start, scene.frame_end = 1, 24 * HOLD
scene.render.fps = 24
try:
    scene.view_settings.view_transform = "AgX"
except Exception:
    pass

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
for k, cam in (cams.items() if not os.environ.get("LL_NO_RENDER") else ()):
    scene.camera = cam
    scene.frame_set(1)
    scene.render.filepath = os.path.join(rdir, f"59_designs_{k}.png")
    bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["rows12"]
scene.frame_set(1)

# its own file: drop the other scenes from memory (they're saved in the old file) and save as
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


def _play():
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("couldn't start playback", e)
    return None


bpy.app.timers.register(_play, first_interval=1.5)
print("texture designs saved as", OUT)
