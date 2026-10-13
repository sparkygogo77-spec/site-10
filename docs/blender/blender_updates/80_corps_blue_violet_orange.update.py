# Pass 80: corps look kits, part two - BLUE (hope), VIOLET (love), ORANGE (avarice). Same layout as pass 79:
# each corps' lantern with its flare in the corps colour, its ring, and three construct textures made for it
# (tools/construct_designs8.py), front row main shade, back row second shade:
#   BLUE     B1 hope hex, B2 dawn, B3 renewal
#   VIOLET   V1 crystal, V2 bloom, V3 silk
#   ORANGE   O1 coins, O2 chains, O3 molten gold
# Builds LanternLive\corps_blue_violet_orange.blend. Cameras: Cam blue / violet / orange (+ " lantern"), Cam all.
import json, math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector

R = math.radians
TEX = os.path.join(FOLDER, "corps_blue_violet_orange")
OUT = os.path.join(FOLDER, "corps_blue_violet_orange.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Corps Blue Violet Orange")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Corps Blue Violet Orange")
col = scene.collection
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 384               # 16 s: every texture loops at least once
win = bpy.context.window
if win:
    win.scene = scene
ITEMS = {it["key"]: it for it in json.load(open(os.path.join(TEX, "set.json")))["items"]}


def link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def label(text, at, size=0.35, colr=(0.95, 0.95, 0.95)):
    cu = bpy.data.curves.new("lab " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = bpy.data.objects.new("Label " + text, cu); o.location = at; o.rotation_euler = (R(90), 0, 0)
    m = bpy.data.materials.new("lab " + text); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value = colr + (1,); p.inputs["Emission Strength"].default_value = 2.5
    cu.materials.append(m)
    col.objects.link(o)


def cyc(o, path, index, v0, v1, frames):
    setattr_path = getattr(o, path)
    setattr_path[index] = v0; o.keyframe_insert(path, index=index, frame=1)
    setattr_path[index] = v1; o.keyframe_insert(path, index=index, frame=frames + 1)
    try:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
            if not fc.modifiers:
                fc.modifiers.new("CYCLES")
    except Exception:
        pass


def plinth(at, r=0.9):
    me = bpy.data.meshes.new("plinth")
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=r, radius2=r, depth=0.12); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Plinth", me); o.location = at + Vector((0, 0, -0.06)); col.objects.link(o)
    m = bpy.data.materials.get("plinth") or bpy.data.materials.new("plinth"); m.use_nodes = True
    m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.04, 0.042, 0.046, 1)
    me.materials.append(m)


def camera(name, target, dist, height, lens=50):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); col.objects.link(c)
    c.location = target + Vector((0, -dist, height))
    c.rotation_euler = (target - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


# ---- textures on walls ---------------------------------------------------------------------------------------
def animated_material(key):
    it = ITEMS[key]; nf = it["frames"]; hold = it["frametime"] * 24 / 20.0     # game frametime ticks -> Blender frames
    m = bpy.data.materials.new("corps " + key); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.join(TEX, f"face_{key}.png"), check_existing=True)
    img.interpolation = "Closest"; img.extension = "REPEAT"
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    frame = N.new("ShaderNodeValue"); frame.label = "game frame"
    d = frame.outputs[0].driver_add("default_value").driver
    d.type = "SCRIPTED"; d.expression = f"floor(fmod(frame - 1, {nf * hold}) / {hold})"
    v1 = N.new("ShaderNodeMath"); v1.operation = "MULTIPLY"; v1.inputs[1].default_value = 1 / nf
    L.new(sep.outputs["Z"], v1.inputs[0])
    v2 = N.new("ShaderNodeMath"); v2.operation = "SUBTRACT"; v2.inputs[0].default_value = nf - 1
    L.new(frame.outputs[0], v2.inputs[1])
    v3 = N.new("ShaderNodeMath"); v3.operation = "MULTIPLY_ADD"; v3.inputs[1].default_value = 1 / nf
    L.new(v2.outputs[0], v3.inputs[0]); L.new(v1.outputs[0], v3.inputs[2])
    cmb = N.new("ShaderNodeCombineXYZ")
    L.new(sep.outputs["X"], cmb.inputs["X"]); L.new(v3.outputs[0], cmb.inputs["Y"])
    L.new(cmb.outputs[0], img.inputs["Vector"])
    p = N.new("ShaderNodeBsdfPrincipled"); out = N.new("ShaderNodeOutputMaterial")
    L.new(img.outputs["Color"], p.inputs["Base Color"]); L.new(img.outputs["Color"], p.inputs["Emission Color"])
    L.new(img.outputs["Alpha"], p.inputs["Alpha"])
    p.inputs["Emission Strength"].default_value = 1.1; p.inputs["Roughness"].default_value = 0.2
    L.new(p.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def wall(key, loc, size=3.0):
    me = bpy.data.meshes.new("wall " + key)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Wall " + key, me); col.objects.link(o)
    o.scale = (size, 0.25, size); o.location = loc
    me.materials.append(animated_material(key))
    return o


# ---- lantern, flare, ring ------------------------------------------------------------------------------------
def light_glb(path, name, at, glow=3.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new(name, None); col.objects.link(holder)
    for o in new:
        link(o)
        if o.parent is None:
            o.parent = holder
        if o.type == "MESH":
            for m in o.data.materials:
                if not m or not m.use_nodes:
                    continue
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE":
                        n.interpolation = "Closest"
                if "_glow" in m.name:
                    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                    tex = next((n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"), None)
                    if bsdf and tex:
                        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
                        bsdf.inputs["Emission Strength"].default_value = glow
    holder.location = at
    return holder


def flare(name, at, rgb, radius=0.13):
    """The G3 heart, in the corps colour: a ball of noisy light spinning one way, breathing, hottest at the core."""
    me = bpy.data.meshes.new("flare " + name)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=radius); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Flare " + name, me); col.objects.link(o); o.location = at
    m = bpy.data.materials.new("flare " + name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 6.0
    d = nz.inputs["W"].driver_add("default_value").driver; d.type = "SCRIPTED"; d.expression = "frame / 60"
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = tuple(c * 0.15 for c in rgb) + (1,)
    ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (min(1, rgb[0] * 1.2 + 0.15), min(1, rgb[1] * 1.2 + 0.15), min(1, rgb[2] * 1.2 + 0.1), 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    em = N.new("ShaderNodeEmission"); L.new(ramp.outputs["Color"], em.inputs["Color"])
    d = em.inputs["Strength"].driver_add("default_value").driver; d.type = "SCRIPTED"
    d.expression = "28 + 10 * sin(frame / 14) + 4 * sin(frame / 3.1)"
    out = N.new("ShaderNodeOutputMaterial"); L.new(em.outputs[0], out.inputs[0])
    me.materials.append(m)
    cyc(o, "rotation_euler", 2, 0, 2 * math.pi, 96)                       # one way only, a turn every 4 s
    li = bpy.data.lights.new("flare light " + name, "POINT"); li.color = rgb; li.shadow_soft_size = 0.15
    d = li.driver_add("energy").driver; d.type = "SCRIPTED"; d.expression = "30 + 10 * sin(frame / 14)"
    lo = bpy.data.objects.new("Flare light " + name, li); lo.location = at; col.objects.link(lo)
    return o


def ring(name, at, rgb, metal):
    d = np.load(os.path.join(TEX, "ring_sq.npz"))
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new("ring " + name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    kind = np.asarray(d["kind"])
    c = np.asarray(d["col"], np.float32) / 255.0
    lum = c.mean(1, keepdims=True)
    glow = np.isin(kind, (4, 6))
    c = np.where(glow[:, None], np.clip(np.array(rgb)[None] * (0.4 + 1.2 * lum), 0, 1),
                 np.where(kind[:, None] == 1, np.clip(np.array(metal)[None] * (0.5 + lum), 0, 1), c * 0.6))
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    ca.data.foreach_set("color", np.hstack([np.repeat(c ** 2.2, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for k, (rough, metal_w, emit) in {0: (0.6, 0.0, 0.0), 1: (0.22, 1.0, 0.0), 4: (0.3, 0.0, 3.0), 6: (0.3, 0.0, 8.0)}.items():
        m = bpy.data.materials.new(f"ring {name} {k}"); m.use_nodes = True
        p = m.node_tree.nodes.get("Principled BSDF")
        a = m.node_tree.nodes.new("ShaderNodeAttribute"); a.attribute_name = "col"
        m.node_tree.links.new(a.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal_w
        if emit:
            m.node_tree.links.new(a.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.searchsorted([0, 1, 4, 6], kind).astype(np.int32))
    o = bpy.data.objects.new("Ring " + name, me); col.objects.link(o)
    o.scale = (1 / 14,) * 3; o.location = at; o.rotation_euler = (R(90), 0, 0)
    cyc(o, "rotation_euler", 2, 0, 2 * math.pi, 192)
    return o


CORPS = [
    ("blue", "BLUE  -  hope", "blue_lantern.glb", 0.85, (0.15, 0.5, 1.0), (0.75, 0.78, 0.85), ["B1", "B2", "B3"], ("hope", "sky"), 0.0),
    ("violet", "VIOLET  -  love", "violet_lantern.glb", 0.62, (0.65, 0.2, 1.0), (0.8, 0.6, 0.9), ["V1", "V2", "V3"], ("love", "rose"), 22.0),
    ("orange", "ORANGE  -  avarice", "orange_lantern.glb", 0.72, (1.0, 0.45, 0.05), (0.95, 0.65, 0.2), ["O1", "O2", "O3"], ("avarice", "gold"), 44.0),
]
cams = {}
for cid, title, glb, mid, rgb, metal, designs, pals, x0 in CORPS:
    base = Vector((x0, 0, 0))
    plinth(base)
    h = light_glb(os.path.join(TEX, glb), "Lantern " + cid, base, glow=12.0 if cid == "blue" else 3.0)
    if cid == "blue":                                   # its light sits deep in a dark housing: let it out the front
        fl = bpy.data.lights.new("blue front", "POINT"); fl.color = rgb; fl.energy = 25; fl.shadow_soft_size = 0.4
        fo_ = bpy.data.objects.new("Blue front light", fl); fo_.location = base + Vector((0, -0.9, 0.85)); col.objects.link(fo_)
    cyc(h, "rotation_euler", 2, 0, 2 * math.pi, 384)
    flare(cid, base + Vector((0, 0, mid)), rgb)
    plinth(base + Vector((1.9, 0, 0)), 0.45)
    ring(cid, base + Vector((1.9, 0, 0.45)), rgb, metal)
    label(title, base + Vector((0, 0, 2.4)), 0.4, tuple(min(1, c + 0.3) for c in rgb))
    for i, dk in enumerate(designs):
        x = x0 + 5.0 + i * 3.6
        wall(f"{dk}_{pals[0]}", Vector((x, 0, 1.6)))
        wall(f"{dk}_{pals[1]}", Vector((x, 3.0, 1.6)), size=2.2)
        label(f"{dk}  {ITEMS[dk + '_' + pals[0]]['name']}", Vector((x, -0.3, 3.45)), 0.24)
    cams[cid] = camera("Cam " + cid, base + Vector((5.6, 0, 1.4)), 17.5, 1.4, lens=40)
    cams[cid + " lantern"] = camera(f"Cam {cid} lantern", base + Vector((0.95, 0, 0.85)), 5.0, 0.5)

world = bpy.data.worlds.new("Corps World"); world.use_nodes = True
world.node_tree.nodes.get("Background").inputs[0].default_value = (0.012, 0.012, 0.016, 1)
scene.world = world
fl = bpy.data.meshes.new("corps floor")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=40); bm.to_mesh(fl); bm.free()
fo = bpy.data.objects.new("Corps floor", fl); fo.location = (29, 2, -0.12); col.objects.link(fo)
fm = bpy.data.materials.new("corps floor"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
fm.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.35
fl.materials.append(fm)
key = bpy.data.lights.new("corps key", "AREA"); key.energy = 320; key.size = 12
ko = bpy.data.objects.new("corps key", key); ko.location = (29, -12, 8); ko.rotation_euler = (R(52), 0, 0); col.objects.link(ko)
cams["all"] = camera("Cam all", Vector((29.5, 0, 1.4)), 44.0, 4.0, lens=40)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("Corps Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.6), ("Strength", 0.45), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for k in ("blue", "violet", "orange", "blue lantern", "violet lantern", "orange lantern"):
        scene.camera = cams[k]; scene.frame_set(40)
        scene.render.filepath = os.path.join(rdir, f"80_{k.replace(' ', '_')}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["blue"]
scene.frame_set(1)
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
                    sp.shading.type = "RENDERED"
            a.tag_redraw()


def _after():
    try:
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
