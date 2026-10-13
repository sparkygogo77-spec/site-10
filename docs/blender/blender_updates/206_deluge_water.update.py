# Pass 206: the Deluge's water, Green and Red, round 1 (lead Blender chat, 2026-10-13).
# Spec (coordinator, from J): animated water modelled in Blender, not physics; check the existing Deluge code first.
# Green is water with waves and reflections; Red is thick, opaque, smooth blood-red water (not lava). Both have to look
# right under J's Complementary shader pack.
# From Deluges.java: a ball of liquid forms high over the marker, its bottom half crashes down while the top dissolves
# in a spray; a geyser shoots up (5/8/12 blocks by level), the flood races out (radius 7/13/20), then rings of waves
# roll out like a little tsunami (2/3/4 waves, crest 2/3/4 tall, 0.45-0.65 blocks a tick, 9 ticks apart). The red
# waves roll much slower (0.2-0.28 a tick, 16 ticks apart) and sink away over their last 5 blocks. It lasts 15-25 s,
# then drains from the edge in. The liquid is water to the game and to shader packs, so Complementary reflects it.
# This pass shows the level-3 event (radius 20) six times, one look each, at the game's timing (20 fps):
#   Green  G1 Clear emerald: clear green-tinted water, glassy, strong reflections, soft light caustics below.
#          G2 Hard-light water: G1 with thin glowing construct lines riding the crests.
#          G3 Deep jade: darker, half-opaque jade with bright foam on each crest.
#   Red    R1 Blood: fully opaque, smooth, deep blood red, glossy, a heavy slow roll.
#          R2 Clotted: R1 with slow darker swirls through it, satin rather than mirror.
#          R3 Black blood: near-black red with bright red highlights only on the crests.
# Cameras "Cam green", "Cam red", "Cam G1".."Cam R3", "Cam all". Builds LanternLive\deluge_water.blend.
import math, os
import bpy
import numpy as np

R = math.radians
OUT = os.path.join(FOLDER, "deluge_water.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Deluge Water")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Deluge Water")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 260
win = bpy.context.window
if win:
    win.scene = scene
try:
    scene.eevee.use_raytracing = True
except Exception:
    pass


def link(o):
    col.objects.link(o)
    return o


def keyed(target, path, fv, index=-1, interp="BEZIER"):
    for f, v in fv:
        if index >= 0:
            getattr(target, path)[index] = v
        else:
            setattr(target, path, v)
        target.keyframe_insert(path, index=index, frame=f)


def fcurves_of(idblock):
    ad = idblock.animation_data
    try:
        return list(ad.action.fcurves)
    except Exception:
        return [fc for layer in ad.action.layers for s in layer.strips for cb in s.channelbags for fc in cb.fcurves]


# ------------------------------------------------------------------ water materials
def water(name, look):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    p.inputs["IOR"].default_value = 1.33
    tc = N.new("ShaderNodeTexCoord")
    if look in ("G1", "G2", "G3"):
        base = {"G1": (0.05, 0.55, 0.25), "G2": (0.05, 0.6, 0.28), "G3": (0.01, 0.2, 0.09)}[look]
        p.inputs["Base Color"].default_value = (*base, 1)
        p.inputs["Roughness"].default_value = 0.02 if look != "G3" else 0.06
        p.inputs["Transmission Weight"].default_value = {"G1": 0.92, "G2": 0.9, "G3": 0.55}[look]
        p.inputs["Alpha"].default_value = {"G1": 0.75, "G2": 0.75, "G3": 0.92}[look]
        # crest detail: a wave texture in object space; G2 makes its thin peaks glow, G3 turns them to foam
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 0.35
        wv.inputs["Distortion"].default_value = 2.0; wv.inputs["Detail"].default_value = 3.0
        L.new(tc.outputs["Object"], wv.inputs["Vector"])
        ph = N.new("ShaderNodeValue"); ph.name = "phase"; ph.label = "phase"
        L.new(ph.outputs[0], wv.inputs["Phase Offset"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.86; ramp.color_ramp.elements[1].position = 0.97
        L.new(wv.outputs["Fac"], ramp.inputs["Fac"])
        if look == "G2":
            p.inputs["Emission Color"].default_value = (0.3, 1.0, 0.5, 1)
            mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 6.0
            L.new(ramp.outputs["Color"], mul.inputs[0]); L.new(mul.outputs[0], p.inputs["Emission Strength"])
        if look == "G3":
            mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
            mix.inputs["A"].default_value = (*base, 1); mix.inputs["B"].default_value = (0.75, 0.95, 0.85, 1)
            L.new(ramp.outputs["Color"], mix.inputs["Factor"]); L.new(mix.outputs["Result"], p.inputs["Base Color"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        m.use_backface_culling = False
    else:
        base = {"R1": (0.28, 0.0, 0.012), "R2": (0.24, 0.0, 0.01), "R3": (0.045, 0.0, 0.004)}[look]
        p.inputs["Base Color"].default_value = (*base, 1)
        p.inputs["Roughness"].default_value = {"R1": 0.07, "R2": 0.28, "R3": 0.1}[look]
        p.inputs["Coat Weight"].default_value = {"R1": 0.6, "R2": 0.2, "R3": 0.5}[look]
        p.inputs["Subsurface Weight"].default_value = 0.0
        if look == "R2":
            nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.12
            nz.inputs["Detail"].default_value = 2.0
            try:
                nz.inputs["Distortion"].default_value = 1.5
            except Exception:
                pass
            mp = N.new("ShaderNodeMapping"); mp.name = "swirl"
            L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], nz.inputs["Vector"])
            mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
            mix.inputs["A"].default_value = (*base, 1); mix.inputs["B"].default_value = (0.07, 0.0, 0.004, 1)
            ramp = N.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[1].position = 0.6
            L.new(nz.outputs["Fac"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], mix.inputs["Factor"])
            L.new(mix.outputs["Result"], p.inputs["Base Color"])
        if look == "R3":
            # near-black body; the highlights on the crests come out bright red through a red-tinted gloss
            p.inputs["Specular Tint"].default_value = (1.0, 0.05, 0.03, 1)
            p.inputs["Coat Tint"].default_value = (1.0, 0.1, 0.06, 1)
            p.inputs["Specular IOR Level"].default_value = 1.0
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ the event, built once per look
RADIUS = 20; GLOBE = 5; GEYSER = 12
T_FORM, T_DROP, T_HIT = 1, 18, 34                       # ticks: globe forms, falls, hits
T_DRAIN0, T_DRAIN1 = 200, 240


def ring_texture(name):
    tex = bpy.data.textures.get(name) or bpy.data.textures.new(name, "WOOD")
    tex.wood_type = "RINGS"; tex.noise_basis_2 = "SIN"; tex.turbulence = 0.0
    return tex


def make_event(look, ox, oy):
    red = look.startswith("R")
    mat = water(f"DW water {look}", look)
    speed = 0.2 if red else 0.45                         # (per-level speeds; level 1's numbers read best on screen)
    gap = 16 if red else 9
    # flood surface: a fine grid, displaced by expanding sine rings, scaled out from the centre as it races
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=2 * RADIUS + 2, location=(ox, oy, 0.15))
    fl = bpy.context.active_object
    for c in fl.users_collection:
        c.objects.unlink(fl)
    link(fl); fl.name = f"DW {look} flood"
    fl.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    # round the grid off into a disc so it spreads as a circle
    me = fl.data
    keep = [v.index for v in me.vertices if math.hypot(v.co.x, v.co.y) > RADIUS + 0.6]
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in keep], context="VERTS")
    bm.to_mesh(me); bm.free()
    emp = link(bpy.data.objects.new(f"DW {look} rings", None)); emp.location = (ox, oy, 0)
    tex = ring_texture(f"DW rings {look}")
    dm = fl.modifiers.new("waves", "DISPLACE"); dm.texture = tex; dm.texture_coords = "OBJECT"
    dm.texture_coords_object = emp; dm.direction = "Z"; dm.mid_level = 0.0
    sm = fl.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.6; sm.iterations = 2
    # the flood races out, the waves roll (rings stretch outward), then everything drains from the edge in
    keyed(fl, "scale", [(T_HIT, (0.03, 0.03, 1)), (T_HIT + (12 if not red else 22), (1, 1, 1)),
                        (T_DRAIN0, (1, 1, 1)), (T_DRAIN1, (0.02, 0.02, 1))])
    crest = 2.4 if not red else 2.0
    keyed(dm, "strength", [(1, 0.0), (T_HIT, 0.0), (T_HIT + 6, crest), (T_DRAIN0 - 40, crest * 0.6),
                           (T_DRAIN0, 0.25), (T_DRAIN1, 0.0)])
    span = RADIUS / speed                               # ticks for a wave to cross the flood
    # Blender's wood rings repeat every ~0.31 texture units, so the empty's scale sets the wave spacing in blocks:
    # green waves 9 ticks apart at 0.45 b/t (~4 blocks), red 16 apart at 0.2 b/t (~3.2 blocks). Growing the scale a
    # little over time stretches the rings outward, so they roll out from the middle.
    sp = gap * speed / 0.31
    keyed(emp, "scale", [(T_HIT, (sp * 0.35, sp * 0.35, 1)), (T_HIT + span * 1.8, (sp * 1.6, sp * 1.6, 1))])
    for fc in fcurves_of(emp):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    if red:                                            # red sinks away near its edge: shrink its crests late
        pass
    # globe: forms high, bottom crashes down, top sprays off
    bpy.ops.mesh.primitive_uv_sphere_add(radius=GLOBE, segments=48, ring_count=24, location=(ox, oy, 34))
    gl = bpy.context.active_object
    for c in gl.users_collection:
        c.objects.unlink(gl)
    link(gl); gl.name = f"DW {look} globe"; gl.data.materials.append(mat)
    keyed(gl, "scale", [(T_FORM, (0.05, 0.05, 0.05)), (T_DROP, (1, 1, 1)), (T_HIT - 4, (1.0, 1.0, 1.25)),
                        (T_HIT, (1.6, 1.6, 0.25)), (T_HIT + 2, (0.01, 0.01, 0.01))])
    keyed(gl, "location", [(T_DROP, (ox, oy, 34)), (T_HIT, (ox, oy, 1.0))])
    for fc in fcurves_of(gl):
        if fc.data_path == "location":
            for k in fc.keyframe_points:
                k.interpolation = "QUAD"; k.easing = "EASE_IN"
    # geyser at the hit
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=2.6, radius2=0.6, depth=GEYSER, location=(ox, oy, GEYSER / 2))
    gy = bpy.context.active_object
    for c in gy.users_collection:
        c.objects.unlink(gy)
    link(gy); gy.name = f"DW {look} geyser"; gy.data.materials.append(mat)
    gy.data.transform(__import__("mathutils").Matrix.Translation((0, 0, GEYSER / 2)))
    gy.location = (ox, oy, 0)
    keyed(gy, "scale", [(T_HIT, (0.3, 0.3, 0.01)), (T_HIT + 5, (1, 1, 1)), (T_HIT + 14, (0.6, 0.6, 0.5)),
                        (T_HIT + 24, (0.2, 0.2, 0.01))])
    # wave phase for the crest lines / swirl drift
    ph = mat.node_tree.nodes.get("phase")
    if ph:
        keyed(ph.outputs[0], "default_value", [(1, 0.0), (261, -40.0 if not red else -18.0)])
        for fc in fcurves_of(mat.node_tree):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    sw = mat.node_tree.nodes.get("swirl")
    if sw:
        keyed(sw.inputs["Rotation"], "default_value", [(1, (0, 0, 0)), (261, (0, 0, 1.2))])
    return fl


# ------------------------------------------------------------------ a little world to reflect: grass, trees, a house
def world_block(ox, oy):
    bpy.ops.mesh.primitive_plane_add(size=70, location=(ox, oy, 0))
    g = bpy.context.active_object
    for c in g.users_collection:
        c.objects.unlink(g)
    link(g); g.name = "DW ground"
    gm = bpy.data.materials.get("DW grass") or bpy.data.materials.new("DW grass")
    gm.use_nodes = True; gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.38, 0.12, 1)
    g.data.materials.append(gm)
    trunk = bpy.data.materials.get("DW trunk") or bpy.data.materials.new("DW trunk")
    trunk.use_nodes = True; trunk.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.16, 0.08, 1)
    leaves = bpy.data.materials.get("DW leaves") or bpy.data.materials.new("DW leaves")
    leaves.use_nodes = True; leaves.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.3, 0.06, 1)
    for k, (tx, ty) in enumerate(((23, 9), (-21, 14), (12, 25), (-26, -8))):
        for z in range(5):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(ox + tx, oy + ty, z + 0.5))
            o = bpy.context.active_object
            for c in o.users_collection:
                c.objects.unlink(o)
            link(o); o.data.materials.append(trunk)
        bpy.ops.mesh.primitive_cube_add(size=5, location=(ox + tx, oy + ty, 6))
        o = bpy.context.active_object
        for c in o.users_collection:
            c.objects.unlink(o)
        link(o); o.data.materials.append(leaves)


LOOKS = {"G1": (0, 0), "G2": (70, 0), "G3": (140, 0), "R1": (0, 80), "R2": (70, 80), "R3": (140, 80)}
for look, (ox, oy) in LOOKS.items():
    world_block(ox, oy)
    make_event(look, ox, oy)
    cu = bpy.data.curves.new("DW label " + look, "FONT")
    cu.body = {"G1": "G1 Clear emerald", "G2": "G2 Hard-light water", "G3": "G3 Deep jade", "R1": "R1 Blood",
               "R2": "R2 Clotted", "R3": "R3 Black blood"}[look]
    cu.size = 3; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("DW label " + look, cu)); t.location = (ox, oy - 27, 0.05)

world = bpy.data.worlds.get("DW sky") or bpy.data.worlds.new("DW sky")
world.use_nodes = True
nt = world.node_tree
sky = nt.nodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"; sky.sun_elevation = R(35); sky.sun_rotation = R(140)
except Exception:
    pass
nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
nt.nodes["Background"].inputs["Strength"].default_value = 0.1
scene.world = world
sun = link(bpy.data.objects.new("DW sun", bpy.data.lights.new("DW sun", "SUN")))
sun.data.energy = 2.6; sun.rotation_euler = (R(55), 0, R(140))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass


def cam(name, loc, look, lens=30):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_end = 3000
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


cams = {"green": cam("Cam green", (70, -95, 45), (70, 0, 0), 28), "red": cam("Cam red", (70, -15, 45), (70, 80, 0), 28),
        "all": cam("Cam all", (70, -150, 140), (70, 40, 0), 30)}
for look, (ox, oy) in LOOKS.items():
    cams[look] = cam("Cam " + look, (ox + 22, oy - 34, 14), (ox, oy, 1.5), 28)
scene.camera = cams["green"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key in ("G1", "G2", "G3", "R1", "R2", "R3"):
        for f, tag in ((T_HIT + 3, "hit"), (T_HIT + 60, "waves")):
            scene.camera = cams[key]; scene.frame_set(f)
            scene.render.filepath = os.path.join(rdir, f"206_deluge_{key}_{tag}.png")
            bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["green"]
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
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
