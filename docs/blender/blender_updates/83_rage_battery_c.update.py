# Pass 83: the Red corps battery, round three (J: "make a diamond block texture that it will use, but in a nice
# crimson red, provide me three different reds ... with small design differences", "maybe try a new handle but
# surely new effects", "the blood ... better just long stretchy pixel lines falling down and when you fly they flow
# a little higher because of the wind"). Models: tools/pixel_rage_battery3.py.
#   C1 crimson - classic cut-gem facets, the arched rune handle
#   C2 ruby    - brighter ruby, double bevel and more sparkle, a round ring handle
#   C3 garnet  - dark garnet with hairline cracks, two curved horns for a handle
# Effects:
#   - Blood: long thin pixel streaks running down from the port and the channels (the default, always).
#   - Flight: a wind blows when you fly, and the streaks lift and trail back and up. Scene property "flight"
#     (0 standing, 1 flying); the demo flies from 6 to 11 s. Change it in the N panel > Item > Properties or on the
#     timeline keys.
#   - Charge (8 s): the plate slides away, the claw light builds, red pixel lightning crackles round the port,
#     more and more of it as the charge rises, and the light rays come out of the claws.
# Builds LanternLive\rage_battery_c.blend. Cameras: Cam C1, Cam C2, Cam C3, Cam port, Cam all.
import math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector

R = math.radians
SRC = os.path.join(FOLDER, "rage_battery")
OUT = os.path.join(FOLDER, "rage_battery_c.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Rage Battery C")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Rage Battery C")
col = scene.collection
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 288
win = bpy.context.window
if win:
    win.scene = scene
BEAT = "pow(max(0, sin(frame / 7.64)), 12) + 0.6 * pow(max(0, sin(frame / 7.64 - 0.55)), 12)"

# ---- the charge: one scene property, eased 0 -> 1 over 8 s, then let go ----------------------------------
scene["charge"] = 0.0
for f, v in ((1, 0.0), (48, 0.0), (240, 1.0), (252, 1.0), (288, 0.0)):
    scene["charge"] = v; scene.keyframe_insert('["charge"]', frame=f)
try:
    for fc in scene.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"; k.easing = "AUTO"
except Exception:
    pass


scene["flight"] = 0.0
for f, v in ((1, 0.0), (144, 0.0), (168, 1.0), (252, 1.0), (276, 0.0)):
    scene["flight"] = v; scene.keyframe_insert('["flight"]', frame=f)


def charge_driver(target, path, expr, index=-1, prop="charge", var="c"):
    fc = target.driver_add(path, index) if index >= 0 else target.driver_add(path)
    d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = var; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = '["%s"]' % prop
    d.expression = expr
    return d


def kind_materials():
    mats = {}
    spec = {0: (0.85, None), 1: (0.75, None), 3: (0.5, None),
            4: (0.25, f"0.5 + 1.2 * ({BEAT})"), 5: (0.4, f"1.0 + 2.6 * ({BEAT})"), 6: (0.3, f"2.5 + 5 * ({BEAT})"),
            7: (0.3, "0.6 + 45 * c * c")}
    for k, (rough, emit) in spec.items():
        m = bpy.data.materials.new(f"battery2 kind {k}"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "col"
        nt.links.new(a.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = rough
        if emit:
            nt.links.new(a.outputs["Color"], p.inputs["Emission Color"])
            if k == 7:
                charge_driver(p.inputs["Emission Strength"], "default_value", emit)
            else:
                d = p.inputs["Emission Strength"].driver_add("default_value").driver
                d.type = "SCRIPTED"; d.expression = emit
            if k == 4:
                p.inputs["Coat Weight"].default_value = 0.8
        mats[k] = m
    return mats


MATS = None


def voxel_object(path, name, at):
    global MATS
    MATS = MATS or kind_materials()
    d = np.load(path)
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    ca.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    order = [0, 1, 3, 4, 5, 6, 7]
    for k in order:
        me.materials.append(MATS[k])
    me.polygons.foreach_set("material_index", np.searchsorted(order, np.asarray(d["kind"])).astype(np.int32))
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    o.scale = (1 / 16,) * 3; o.location = at
    return o


PORT = Vector((0, -12.4 / 16, 24.0 / 16))
WALL_BACK = Vector((0, -9.0 / 16, 24.0 / 16))       # just behind the claw wall


def blood_material(name, glow=0.8, rough=0.08):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (0.45, 0.0, 0.015, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = 1.0; p.inputs["Coat Roughness"].default_value = 0.03
    p.inputs["Emission Color"].default_value = (0.9, 0.02, 0.03, 1); p.inputs["Emission Strength"].default_value = glow
    p.inputs["Subsurface Weight"].default_value = 0.3
    return m


def drop_mesh(name, shape):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if shape == "tear":
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.05)
        for v in bm.verts:
            if v.co.z > 0:
                v.co.z *= 2.4; v.co.x *= 0.55; v.co.y *= 0.55     # a teardrop with its tail up
    elif shape == "glob":
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.075)
        r = np.random.default_rng(3)
        for v in bm.verts:
            v.co *= 1 + r.uniform(-0.18, 0.18)
    else:
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.018)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = (0, 0, -50)
    return o


def emitter(name, at, size, rot=(0, 0, 0), segs=16):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=segs, radius=size); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    o.location = at; o.rotation_euler = rot
    o.show_instancer_for_render = False
    o.show_instancer_for_viewport = False
    return o


def particles(o, name, inst, count, life, normal_v, rand_v, gravity, damping, size=1.0, size_rand=0.4, align=False):
    mod = o.modifiers.new(name, "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.count = count; ps.frame_start = -60; ps.frame_end = 288; ps.lifetime = life; ps.lifetime_random = 0.45
    ps.emit_from = "FACE"; ps.normal_factor = normal_v; ps.factor_random = rand_v
    ps.effector_weights.gravity = gravity; ps.damping = damping
    ps.render_type = "OBJECT"; ps.instance_object = inst
    ps.particle_size = size; ps.size_random = size_rand
    ps.use_rotations = True
    if align:
        ps.rotation_mode = "VEL"; ps.rotation_factor_random = 0.0
    else:
        ps.rotation_factor_random = 1.0
    return ps


def plinth(at, r=1.4):
    me = bpy.data.meshes.new("plinth")
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r, depth=0.14); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Plinth", me); o.location = at + Vector((0, 0, -0.07)); col.objects.link(o)
    m = bpy.data.materials.get("plinth") or bpy.data.materials.new("plinth"); m.use_nodes = True
    m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.03, 0.025, 0.025, 1)
    me.materials.append(m)


def label(text, at, size=0.24):
    cu = bpy.data.curves.new("lab " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = bpy.data.objects.new("Label " + text, cu); o.location = at; o.rotation_euler = (R(90), 0, 0)
    m = bpy.data.materials.new("lab " + text); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value = (1, 0.75, 0.7, 1); p.inputs["Emission Strength"].default_value = 2.0
    cu.materials.append(m); col.objects.link(o)


def camera(name, target, dist, height, lens=50):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); col.objects.link(c)
    c.location = target + Vector((0, -dist, height))
    c.rotation_euler = (target - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


def light_rays(at):
    """A spot light behind the claw wall, so the light leaves through the claws, and a thin haze in front of the
    port so the shafts show."""
    sp = bpy.data.lights.new("claw light", "SPOT"); sp.color = (1, 0.1, 0.06)
    sp.spot_size = R(70); sp.spot_blend = 0.6; sp.shadow_soft_size = 0.02
    charge_driver(sp, "energy", "9000 * c * c")
    so = bpy.data.objects.new("Claw light", sp); so.location = at + WALL_BACK + Vector((0, 0.15, 0))
    so.rotation_euler = (R(90), 0, 0)                       # points down -y, out of the port
    col.objects.link(so)
    pt = bpy.data.lights.new("battery glow", "POINT"); pt.color = (1, 0.12, 0.08); pt.shadow_soft_size = 0.5
    charge_driver(pt, "energy", "20 + 140 * c * c")
    po = bpy.data.objects.new("Battery glow", pt); po.location = at + PORT + Vector((0, -0.6, 0)); col.objects.link(po)
    me = bpy.data.meshes.new("haze")
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new("Ray haze", me); col.objects.link(hz)
    hz.scale = (3.2, 4.0, 2.8); hz.location = at + Vector((0, -3.0, 1.5))
    m = bpy.data.materials.new("ray haze"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (1, 0.5, 0.45, 1)
    vol.inputs["Anisotropy"].default_value = 0.6
    # the haze thins out toward the edges of its box, so the box itself never shows
    tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (-0.5, -0.5, -0.5)
    mp.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    mp2 = nt.nodes.new("ShaderNodeMapping"); mp2.vector_type = "POINT"
    nt.links.new(tc.outputs["Generated"], mp2.inputs["Vector"])
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    nt.links.new(tc.outputs["Generated"], sub.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(sub.outputs[0], ln.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.5; fall.inputs["From Max"].default_value = 0.1
    fall.inputs["To Min"].default_value = 0.0; fall.inputs["To Max"].default_value = 0.05
    nt.links.new(ln.outputs["Value"], fall.inputs["Value"]); nt.links.new(fall.outputs["Result"], vol.inputs["Density"])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(vol.outputs[0], out.inputs["Volume"])
    me.materials.append(m)


def plate_slide(plate, at):
    """Closed until the charge starts; then it eases forward off its seat, slides down and away, and is gone.
    It comes back up once the light has faded."""
    base = at.copy()
    keys = ((1, base, 1.0), (50, base, 1.0), (58, base + Vector((0, -0.08, 0)), 1.0),
            (80, base + Vector((0, -0.12, -0.75)), 1.0), (92, base + Vector((0, -0.12, -0.95)), 0.0),
            (262, base + Vector((0, -0.12, -0.95)), 0.0), (270, base + Vector((0, -0.12, -0.75)), 1.0),
            (284, base + Vector((0, -0.08, 0)), 1.0), (288, base, 1.0))
    for f, loc, s in keys:
        plate.location = loc; plate.keyframe_insert("location", frame=f)
        plate.scale = (s / 16,) * 3; plate.keyframe_insert("scale", frame=f)


def streak_object():
    """A long thin line of blood pixels: eight little cubes in a row along X (the particles turn X to their motion)."""
    me = bpy.data.meshes.new("blood streak")
    bm = bmesh.new()
    for j in range(8):
        w = 0.026 * (1.0 - 0.06 * j)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for vv in r["verts"]:
            vv.co.x = vv.co.x * 0.05 - j * 0.05
            vv.co.y *= w; vv.co.z *= w
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Blood streak", me); col.objects.link(o); o.location = (0, 0, -50)
    return o


def streaks(o, name, inst, count, normal_v):
    mod = o.modifiers.new(name, "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.count = count; ps.frame_start = -80; ps.frame_end = 288; ps.lifetime = 120; ps.lifetime_random = 0.4
    ps.emit_from = "FACE"; ps.normal_factor = normal_v; ps.factor_random = 0.02
    ps.effector_weights.gravity = 0.28; ps.damping = 0.18
    ps.render_type = "OBJECT"; ps.instance_object = inst
    ps.particle_size = 1.0; ps.size_random = 0.45
    ps.use_rotations = True; ps.rotation_mode = "VEL"; ps.rotation_factor_random = 0.0
    try:
        ps.effector_weights.wind = 1.0
    except Exception:
        pass
    return ps


def wind(at):
    """Flying: wind from below and in front, so the streaks lift and trail back; strength from "flight"."""
    bpy.ops.object.effector_add(type="WIND", location=at + Vector((0, -2.0, -0.6)))
    w = bpy.context.active_object
    for c in list(w.users_collection):
        c.objects.unlink(w)
    col.objects.link(w)
    w.name = "Flight wind"; w.rotation_euler = (R(-60), 0, 0)          # blowing up and toward the back
    w.field.flow = 0.6
    charge_driver(w.field, "strength", "7 * f", prop="flight", var="f")


def lightning(at, seed):
    """Red pixel lightning round the port: jagged chains of little cubes, three versions of each arc swapped
    every few frames so they crackle; more of them show as the charge rises."""
    rng = np.random.default_rng(seed)
    centre = at + PORT + Vector((0, -0.12, 0))
    for k in range(10):
        a0 = rng.uniform(0, 2 * math.pi)
        for ver in range(3):
            me = bpy.data.meshes.new(f"arc {k} {ver}")
            bm = bmesh.new()
            r = 0.40
            p = Vector((math.cos(a0) * r, 0, math.sin(a0) * r))
            ang = a0
            for step in range(int(rng.integers(10, 22))):
                ang += rng.uniform(-0.5, 0.5)
                d = Vector((math.cos(ang), rng.uniform(-0.35, 0.1), math.sin(ang))) * 0.045
                p = p + d + Vector((rng.uniform(-0.02, 0.02), 0, rng.uniform(-0.02, 0.02)))
                cb = bmesh.ops.create_cube(bm, size=0.028)
                for vv in cb["verts"]:
                    vv.co += p
            bm.to_mesh(me); bm.free()
            o = bpy.data.objects.new(f"Lightning {k}.{ver}", me); col.objects.link(o)
            o.location = centre
            me.materials.append(ARC_MAT)
            thr = 0.15 + 0.07 * k                       # each arc switches on at its own charge
            expr = f"(fmod(floor(frame / 2) + {k}, 3) == {ver}) * (c > {thr:.2f}) * (sin(frame * {1.3 + 0.37 * k:.2f}) > {0.6 - 0.5:.2f} - c)"
            for ax in range(3):
                charge_driver(o, "scale", expr, index=ax)


ARC_MAT = None


cams = {}
OPTIONS = [("C1", "C1  crimson  -  classic facets, arched handle"), ("C2", "C2  ruby  -  double bevel, ring handle"),
           ("C3", "C3  garnet  -  cracked facets, horn handle")]
blood = blood_material("blood", glow=1.2, rough=0.1)
ARC_MAT = blood_material("lightning", glow=0.0)
ARC_MAT.node_tree.nodes.get("Principled BSDF").inputs["Emission Color"].default_value = (1, 0.12, 0.08, 1)
charge_driver(ARC_MAT.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"], "default_value", "12 + 20 * c")
streak = streak_object()
streak.data.materials.append(blood)
for i, (pid, title) in enumerate(OPTIONS):
    at = Vector((i * 5.0, 0, 0))
    plinth(at)
    voxel_object(os.path.join(SRC, f"battery3_{pid.lower()}_body.npz"), "Battery " + pid, at)
    plate = voxel_object(os.path.join(SRC, f"battery3_{pid.lower()}_plate.npz"), "Port plate " + pid, at)
    plate_slide(plate, at)
    light_rays(at)
    lightning(at, 10 + i)
    label(title, at + Vector((0, -1.2, 4.1)))
    drip = emitter(f"Drip emitter {pid}", at + PORT + Vector((0, -0.12, -0.40)), 0.28)
    chan = emitter(f"Channel emitter {pid}", at + Vector((0, -0.70, 0.62)), 0.2, rot=(R(90), 0, 0))
    streaks(drip, "streaks", streak, 140, 0.0)
    streaks(chan, "channel streaks", streak, 70, 0.06)
    wind(at)
    cams[pid] = camera("Cam " + pid, at + Vector((0, 0, 1.8)), 11.5, 0.6)
cams["port"] = camera("Cam port", PORT + Vector((0, 0, 0)), 3.4, 0.25, lens=50)
cams["all"] = camera("Cam all", Vector((5, 0, 1.8)), 19.0, 1.5, lens=40)

# ---- room, glow ---------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("Battery World"); world.use_nodes = True
world.node_tree.nodes.get("Background").inputs[0].default_value = (0.01, 0.006, 0.006, 1)
scene.world = world
fl = bpy.data.meshes.new("battery floor")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=25); bm.to_mesh(fl); bm.free()
fo = bpy.data.objects.new("Battery floor", fl); fo.location = (5, 3, -0.14); col.objects.link(fo)
fm = bpy.data.materials.new("battery floor"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.03, 0.02, 0.02, 1)
fm.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.3
fl.materials.append(fm)
key = bpy.data.lights.new("battery key", "AREA"); key.energy = 900; key.size = 8
ko = bpy.data.objects.new("battery key", key); ko.location = (5, -9, 8); ko.rotation_euler = (R(48), 0, 0); col.objects.link(ko)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
for attr, val in (("use_volumetric_shadows", True), ("volumetric_tile_size", "4"), ("volumetric_samples", 64),
                  ("volumetric_end", 40.0)):
    try:
        setattr(scene.eevee, attr, val)
    except Exception:
        pass
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("Battery Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.7), ("Strength", 0.55), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for f in (30, 140, 236):
        scene.camera = cams["C1"]; scene.frame_set(f)
        scene.render.filepath = os.path.join(rdir, f"83_C1_f{f}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["all"]
scene.frame_set(1)
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


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
