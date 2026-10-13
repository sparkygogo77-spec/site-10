# Pass 76: construct designs, round five (J: "W1 neon from afar is how I'd want every face of my constructs to
# look, translucent, a dark good colour, details not favourable" + "more super elaborate design texture flows").
# Ten designs, each with W1 neon's far look (dark neon green, big soft patches, fine detail only just there),
# translucent, with an elaborate flow moving slowly through it; dark neon row and emerald row. Speeds chosen:
# 4.8 s loops for shimmer, 8 s loops (half a block a second) for glides. tools/construct_designs5.py.
# Saves this as LanternLive\texture_round5.blend.
import json, os
import bpy, bmesh
from mathutils import Vector

TEX = os.path.join(FOLDER, "texture_round5")
OUT = os.path.join(FOLDER, "texture_round5.blend")
SET = json.load(open(os.path.join(TEX, "set.json")))
COLS = 6
STEP = 5.5
HOLD = 2                      # Blender frames per game frame (24 fps): a 2 s loop

if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER, "lantern_work_backup.blend"), copy=True)

old = bpy.data.scenes.get("Texture Round 5")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Texture Round 5")
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


def animated_material(key, nf=24, hold=2):
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
    d.expression = f"floor(fmod(frame - 1, {nf * hold}) / {hold})"
    # v in the strip: frame 0 is the top 1/24th of the image
    v1 = N.new("ShaderNodeMath"); v1.operation = "MULTIPLY"; v1.inputs[1].default_value = 1 / nf
    L.new(sep.outputs["Z"], v1.inputs[0])
    v2 = N.new("ShaderNodeMath"); v2.operation = "SUBTRACT"; v2.inputs[0].default_value = nf - 1
    L.new(frame.outputs[0], v2.inputs[1])
    v3 = N.new("ShaderNodeMath"); v3.operation = "MULTIPLY_ADD"; v3.inputs[1].default_value = 1 / nf
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


def jelly_material(key, nf=24, hold=2):
    """See-through jelly: the texture drives colour and how solid it is, with real refraction and a glossy coat."""
    m = animated_material(key, nf, hold)
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Transmission Weight"].default_value = 0.65
    p.inputs["Roughness"].default_value = 0.06
    p.inputs["IOR"].default_value = 1.34
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.03
    p.inputs["Emission Strength"].default_value = 0.55
    m.name = "jelly " + key
    return m


def wall(key, loc, jelly=False, depth=0.3, nf=24, hold=2):
    me = bpy.data.meshes.new("design wall " + key)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new("Design " + key, me))
    o.scale = (4.0, depth, 4.0); o.location = loc
    me.materials.append(jelly_material(key, nf, hold) if jelly else animated_material(key, nf, hold))
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


SECTIONS = [("neon", "DARK NEON (W1's far look)"), ("emerald", "EMERALD")]
items = SET["items"]
z = 0.0
for sec, title in SECTIONS:
    row = [it for it in items if it["section"] == sec]
    if not row:
        continue
    label(title, Vector((-STEP * 1.1, 0, z)), 0.55, (1.0, 1.0, 0.75))
    for i, it in enumerate(row):
        c, r = i % 5, i // 5
        loc = Vector((c * STEP, 0, z - r * STEP))
        hold = max(1, round(it["frametime"] * 1.2))          # game ticks (20/s) -> Blender frames (24/s)
        depth = 1.0 if it["jelly"] else 0.3
        wall(it["key"], loc, it["jelly"], depth, it["frames"], hold)
        label(it["key"].replace("_", " "), loc + Vector((0, -depth - 0.1, 2.55)), 0.3)
        label(it["note"], loc + Vector((0, -depth - 0.1, 2.2)), 0.22, (0.8, 0.95, 0.85))
    z -= STEP * (1 + (len(row) - 1) // 5) + 1.2
Z_END = z
win = bpy.context.window
if win:
    win.scene = scene
# room, light, cameras
world = bpy.data.worlds.new("Designs World"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.03, 0.04, 0.055, 1); bg.inputs[1].default_value = 1.0
scene.world = world
sun = bpy.data.lights.new("Designs Sun", "SUN"); sun.energy = 2.0
link(bpy.data.objects.new("Designs Sun", sun)).rotation_euler = (0.9, 0.2, 0.4)
fl = bpy.data.meshes.new("designs backdrop")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=140); bm.to_mesh(fl); bm.free()
fo = link(bpy.data.objects.new("Backdrop", fl)); fo.rotation_euler = (1.5708, 0, 0)
fo.location = (STEP * 3.5, 3.0, Z_END / 2)
fm = bpy.data.materials.new("designs backdrop"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.07, 0.09, 0.11, 1)
fl.materials.append(fm)


def camera(name, target, dist, lens=35):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    cam = link(bpy.data.objects.new(name, cd))
    cam.location = target + Vector((0, -dist, 0)); cam.rotation_euler = (1.5708, 0, 0)
    return cam


cams = {"neon": camera("Cam dark neon", Vector((STEP * 2.0, 0, -STEP * 0.5)), 40),
        "emerald": camera("Cam emerald", Vector((STEP * 2.0, 0, -STEP * 3.0)), 40),
        "overview": camera("Cam overview", Vector((STEP * 2.0, 0, Z_END / 2)), 66)}
scene.render.engine = "BLENDER_EEVEE"
try:
    scene.eevee.use_raytracing = True       # refraction for the jelly
except Exception:
    pass
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.frame_start, scene.frame_end = 1, 32 * 5 * 24
scene.render.fps = 24
try:
    scene.view_settings.view_transform = "AgX"
except Exception:
    pass

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
for k, cam in (cams.items() if not os.environ.get("LL_NO_RENDER") else ()):
    scene.camera = cam
    scene.frame_set(1)
    scene.render.filepath = os.path.join(rdir, f"76_round5_{k}.png")
    bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["neon"]
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
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
    except Exception as e:
        print("watch:", e)
    try:
        info = []
        try:
            info.append("ops: " + ", ".join(dir(bpy.ops.lantern_live)))
        except Exception as e:
            info.append("no lantern_live ops: %s" % e)
        try:
            st = bpy.types.LANTERN_LIVE_OT_render.execute.__globals__.get("_state")
            info.append("state keys: %s" % (list(st.keys()) if isinstance(st, dict) else type(st)))
        except Exception as e:
            info.append("state: %s" % e)
        open(os.path.join(FOLDER, "addon_info.txt"), "w").write("\n".join(info))
    except Exception:
        pass
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
