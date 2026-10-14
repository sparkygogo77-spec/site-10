# Pass 305 (from 304): the long rays with more detail, at Minecraft scale. J (2026-10-14): the Blender chats should build
# as detailed as the Cowork chats. Every take keeps 304's 4-block glow, every side glowing and beams from every side, and
# adds: a block-grid ground (16 px per block), a plain 1.8-block figure for scale, and dust motes drifting in the light.
#   D1 streaks+   - L3 streaks with the detail.
#   D2 shafts+    - L2 shafts with the detail.
#   D3 pixel smoke - L3 with Minecraft-style pixel smoke puffs rising off the top instead of soft wisps; the puffs carry
#                    the corps light and lose it over 4 blocks.
#   D3c           - D3 in H1 crimson.
# Watch in Rendered view (Z > Rendered). Builds LanternLive\smoke_rays_detail.blend. Needs LanternLive\texture_library.
import json, math, os
import bpy
import numpy as np
from mathutils import Vector

R = math.radians
LIB = os.path.join(FOLDER, "texture_library")
OUT = os.path.join(FOLDER, "smoke_rays_detail.blend")
INDEX = json.load(open(os.path.join(LIB, "index.json")))
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Smoke Rays Detail")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Smoke Rays Detail")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 160
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


def frame_driver(sock, expr):
    d = sock.driver_add("default_value").driver
    d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "f"; v.type = "SINGLE_PROP"
    v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = "frame_current"
    d.expression = expr


def srgb(c):
    c = np.array(c, float) / 255
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)) + (1.0,)


def light_rgb(colour):
    return srgb(INDEX["ramps"][colour][3])


def wall_mat(tex, colour):
    nm = f"blender_{tex}_{colour}.mp4"
    m = bpy.data.materials.new(f"SR wall {tex} {colour}"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
    t = N.new("ShaderNodeTexImage"); t.projection = "BOX"; t.interpolation = "Closest"
    im = bpy.data.images.get(nm) or bpy.data.images.load(os.path.join(LIB, "blender_mp4", nm))
    im.source = "MOVIE"; im.filepath = "//texture_library/blender_mp4/" + nm
    t.image = im
    iu = t.image_user; iu.frame_duration = INDEX["textures"][tex]["colours"][colour]["mp4_frames"]
    iu.frame_start = 1; iu.use_cyclic = True; iu.use_auto_refresh = True
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], t.inputs["Vector"])
    L.new(t.outputs["Color"], p.inputs["Base Color"]); L.new(t.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = 2.2; p.inputs["Roughness"].default_value = 0.35
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


def box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = name; o.scale = size
    bpy.ops.object.select_all(action="DESELECT")
    if mat:
        o.data.materials.append(mat)
    return o


def smoke_mat(name, colour, style):
    """Noise smoke: rises (S1), rolls forward and sideways (S2) or puffs slowly (S3); glows near the wall."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled")
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs["Vector"])
    mp = N.new("ShaderNodeMapping")
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    if style == "S1":
        mp.inputs["Scale"].default_value = (2.6, 2.6, 0.7)     # stretched up: thin streaming wisps
        d = mp.inputs["Location"].driver_add("default_value", 2).driver
        d.type = "SCRIPTED"; v = d.variables.new(); v.name = "f"; v.targets[0].id_type = "SCENE"
        v.targets[0].id = scene; v.targets[0].data_path = "frame_current"; d.expression = "-f*0.035"
    elif style == "S2":
        mp.inputs["Scale"].default_value = (1.2, 1.6, 1.2)
        for i, e in ((0, "-f*0.02"), (1, "-f*0.012"), (2, "-f*0.01")):
            d = mp.inputs["Location"].driver_add("default_value", i).driver
            d.type = "SCRIPTED"; v = d.variables.new(); v.name = "f"; v.targets[0].id_type = "SCENE"
            v.targets[0].id = scene; v.targets[0].data_path = "frame_current"; d.expression = e
    else:
        mp.inputs["Scale"].default_value = (0.9, 0.9, 0.9)
        d = mp.inputs["Location"].driver_add("default_value", 2).driver
        d.type = "SCRIPTED"; v = d.variables.new(); v.name = "f"; v.targets[0].id_type = "SCENE"
        v.targets[0].id = scene; v.targets[0].data_path = "frame_current"; d.expression = "-f*0.012"
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 6.0; nz.inputs["Roughness"].default_value = 0.62
    frame_driver(nz.inputs["W"], "f*0.008")
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeMapRange")                            # wisps: only the dense parts of the noise
    cr.inputs["From Min"].default_value = {"S1": 0.46, "S2": 0.44, "S3": 0.5}[style]
    cr.inputs["From Max"].default_value = 0.78; cr.inputs["To Max"].default_value = 1.0
    L.new(nz.outputs["Fac"], cr.inputs["Value"])
    # height fade: born at the wall, thinning as it rises (object z from -0.5 at the bottom to 0.5 at the top)
    hz = N.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = -0.5; hz.inputs["From Max"].default_value = 0.5
    hz.inputs["To Min"].default_value = 1.0; hz.inputs["To Max"].default_value = 0.0
    L.new(sep.outputs["Z"], hz.inputs["Value"])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.4
    L.new(hz.outputs["Result"], pw.inputs[0])
    def edge(axis, inner):                                       # 1 in the middle, 0 at the box's side
        ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(sep.outputs[axis], ab.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = inner; mr.inputs["From Max"].default_value = 0.5
        mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
        mr.interpolation_type = "SMOOTHSTEP"; L.new(ab.outputs[0], mr.inputs["Value"])
        return mr.outputs["Result"]
    ex = N.new("ShaderNodeMath"); ex.operation = "MULTIPLY"
    L.new(edge("X", 0.2), ex.inputs[0]); L.new(edge("Y", 0.1), ex.inputs[1])
    ez = N.new("ShaderNodeMath"); ez.operation = "MULTIPLY"; L.new(ex.outputs[0], ez.inputs[0]); L.new(pw.outputs[0], ez.inputs[1])
    dens = N.new("ShaderNodeMath"); dens.operation = "MULTIPLY"
    L.new(cr.outputs["Result"], dens.inputs[0]); L.new(ez.outputs[0], dens.inputs[1])
    amt = N.new("ShaderNodeMath"); amt.operation = "MULTIPLY"; amt.inputs[1].default_value = {"S1": 5.0, "S2": 3.5, "S3": 5.0}[style]
    L.new(dens.outputs[0], amt.inputs[0]); L.new(amt.outputs[0], vol.inputs["Density"])
    vol.inputs["Color"].default_value = (0.75, 0.78, 0.8, 1)
    vol.inputs["Anisotropy"].default_value = 0.55               # forward scattering: the shafts read from the front
    # glow: the smoke carries the construct's light, strongest where it leaves the wall
    gl = N.new("ShaderNodeMath"); gl.operation = "POWER"; gl.inputs[1].default_value = 3.0
    L.new(hz.outputs["Result"], gl.inputs[0])
    ge = N.new("ShaderNodeMath"); ge.operation = "MULTIPLY"; L.new(gl.outputs[0], ge.inputs[0]); L.new(dens.outputs[0], ge.inputs[1])
    gs = N.new("ShaderNodeMath"); gs.operation = "MULTIPLY"; gs.inputs[1].default_value = 7.0
    L.new(ge.outputs[0], gs.inputs[0]); L.new(gs.outputs[0], vol.inputs["Emission Strength"])
    vol.inputs["Emission Color"].default_value = light_rgb(colour)
    L.new(vol.outputs["Volume"], out.inputs["Volume"])
    return m


def box_dist(N, L, centre, half):
    """Distance from the shading point to the wall box (0 on and inside it), and the point's offset from the centre."""
    geo = N.new("ShaderNodeNewGeometry")
    sub = N.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = centre
    L.new(geo.outputs["Position"], sub.inputs[0])
    ab = N.new("ShaderNodeVectorMath"); ab.operation = "ABSOLUTE"; L.new(sub.outputs[0], ab.inputs[0])
    sh = N.new("ShaderNodeVectorMath"); sh.operation = "SUBTRACT"; sh.inputs[1].default_value = half
    L.new(ab.outputs[0], sh.inputs[0])
    mx = N.new("ShaderNodeVectorMath"); mx.operation = "MAXIMUM"; mx.inputs[1].default_value = (0, 0, 0)
    L.new(sh.outputs[0], mx.inputs[0])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(mx.outputs[0], ln.inputs[0])
    return ln.outputs["Value"], sub.outputs[0]


def fade(N, L, dist, reach, power, reach_expr=None):
    fall = N.new("ShaderNodeMapRange"); fall.interpolation_type = "SMOOTHSTEP"
    fall.inputs["From Min"].default_value = 0.0; fall.inputs["From Max"].default_value = reach
    fall.inputs["To Min"].default_value = 1.0; fall.inputs["To Max"].default_value = 0.0
    if reach_expr:
        frame_driver(fall.inputs["From Max"], reach_expr)
    L.new(dist, fall.inputs["Value"])
    sq = N.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = power
    L.new(fall.outputs["Result"], sq.inputs[0])
    return sq.outputs[0]


def glow_mat(name, colour, reach, centre, half, k=0.28, streaks=False, pulse=False):
    """Light in the air round the wall: full at its surface, fading smoothly to nothing 'reach' blocks out.
    streaks: the glow is broken into soft rays fanning out from the wall, drifting slowly.
    pulse: the reach breathes between reach-1 and reach+1 every 4 s, and the strength with it."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission")
    dist, off = box_dist(N, L, centre, half)
    v = fade(N, L, dist, reach, 1.8, f"{reach}+sin(f*0.0785)" if pulse else None)
    if streaks:
        sc = N.new("ShaderNodeVectorMath"); sc.operation = "MULTIPLY"
        sc.inputs[1].default_value = (1 / (half[0] + 1), 1 / (half[1] + 1), 1 / (half[2] + 1))
        L.new(off, sc.inputs[0])
        nm = N.new("ShaderNodeVectorMath"); nm.operation = "NORMALIZE"; L.new(sc.outputs[0], nm.inputs[0])
        nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
        nz.inputs["Scale"].default_value = 7.0; nz.inputs["Detail"].default_value = 1.0
        frame_driver(nz.inputs["W"], "f*0.006")
        L.new(nm.outputs[0], nz.inputs["Vector"])
        rr = N.new("ShaderNodeMapRange"); rr.interpolation_type = "SMOOTHSTEP"
        rr.inputs["From Min"].default_value = 0.42; rr.inputs["From Max"].default_value = 0.68
        rr.inputs["To Min"].default_value = 0.06; rr.inputs["To Max"].default_value = 2.0
        L.new(nz.outputs["Fac"], rr.inputs["Value"])
        mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(v, mu.inputs[0]); L.new(rr.outputs["Result"], mu.inputs[1])
        v = mu.outputs[0]
    gk = k
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = gk
    if pulse:
        frame_driver(k.inputs[1], f"{gk}*(1+0.3*sin(f*0.0785))")
    L.new(v, k.inputs[0]); L.new(k.outputs[0], em.inputs["Strength"])
    em.inputs["Color"].default_value = light_rgb(colour)
    L.new(em.outputs["Emission"], out.inputs["Volume"])
    return m


def local_haze_mat(name, centre, half):
    """Haze thickest at the wall, thinning to a trace 6 blocks out: beams show near the construct and fade away."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); sc = N.new("ShaderNodeVolumeScatter")
    sc.inputs["Anisotropy"].default_value = 0.45
    dist, _ = box_dist(N, L, centre, half)
    v = fade(N, L, dist, 6.0, 1.3)
    k = N.new("ShaderNodeMapRange"); k.inputs["To Min"].default_value = HAZE_FAR; k.inputs["To Max"].default_value = HAZE_NEAR
    L.new(v, k.inputs["Value"]); L.new(k.outputs["Result"], sc.inputs["Density"])
    L.new(sc.outputs["Volume"], out.inputs["Volume"])
    return m


def haze_mat():
    m = bpy.data.materials.new("SR haze"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); sc = N.new("ShaderNodeVolumeScatter")
    sc.inputs["Density"].default_value = 0.09; sc.inputs["Anisotropy"].default_value = 0.45
    L.new(sc.outputs["Volume"], out.inputs["Volume"])
    return m


def mote_mat(colour):
    m = bpy.data.materials.new(f"SR ember {colour}"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = srgb(np.array(INDEX["ramps"][colour][3]) * 0.5 + np.array(INDEX["ramps"][colour][4]) * 0.5)
    e.inputs["Strength"].default_value = 8.0
    L.new(e.outputs["Emission"], out.inputs["Surface"])
    return m


def embers(name, at, colour, count=60):
    """Pixel embers rising in the smoke: small glowing cubes on a particle system."""
    em = box(name + " emitter", (3.8, 0.6, 0.1), (at[0], at[1], at[2] + 3.05), None)
    em.hide_render = True; em.display_type = "WIRE"
    px = box(name + " pixel", (0.07, 0.07, 0.07), (at[0], at[1], -50), mote_mat(colour))
    ps = em.modifiers.new("embers", "PARTICLE_SYSTEM").particle_system.settings
    ps.count = count; ps.frame_start = -60; ps.frame_end = 160; ps.lifetime = 70; ps.lifetime_random = 0.5
    ps.emit_from = "FACE"; ps.normal_factor = 0.0; ps.factor_random = 0.3
    ps.object_align_factor = (0, 0, 0.7); ps.effector_weights.gravity = -0.06
    ps.render_type = "OBJECT"; ps.instance_object = px; ps.particle_size = 1.0; ps.size_random = 0.5
    ps.use_rotations = True; ps.angular_velocity_mode = "RAND"; ps.angular_velocity_factor = 2.0
    ps.brownian_factor = 0.15
    return em


def label(text, at):
    cu = bpy.data.curves.new("SR label " + text, "FONT"); cu.body = text; cu.size = 0.42; cu.align_x = "CENTER"
    t = link(bpy.data.objects.new("SR label " + text, cu)); t.location = (at[0], at[1] - 2.2, 0.02)
    m = bpy.data.materials.new("SR label"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 1, 1, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5
    t.data.materials.append(m)


def pixel_ground_mat():
    """Minecraft-scale ground: 1-block tiles of 16x16 pixel noise in dark stone shades, with a faint seam per block."""
    m = bpy.data.materials.new("SR block ground"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    px = N.new("ShaderNodeVectorMath"); px.operation = "SNAP"; px.inputs[1].default_value = (1 / 16, 1 / 16, 1 / 16)
    L.new(tc.outputs["Object"], px.inputs[0])
    sc = N.new("ShaderNodeVectorMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = (1, 1, 0)
    L.new(px.outputs[0], sc.inputs[0])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"; L.new(sc.outputs[0], wn.inputs["Vector"])
    bk = N.new("ShaderNodeVectorMath"); bk.operation = "FLOOR"; L.new(tc.outputs["Object"], bk.inputs[0])
    bm = N.new("ShaderNodeVectorMath"); bm.operation = "MULTIPLY"; bm.inputs[1].default_value = (1, 1, 0)
    L.new(bk.outputs[0], bm.inputs[0])
    wb = N.new("ShaderNodeTexWhiteNoise"); wb.noise_dimensions = "3D"; L.new(bm.outputs[0], wb.inputs["Vector"])
    mix = N.new("ShaderNodeMath"); mix.operation = "MULTIPLY_ADD"; mix.inputs[1].default_value = 0.7
    L.new(wn.outputs["Value"], mix.inputs[0]); L.new(wb.outputs["Value"], mix.inputs[2])
    mx2 = N.new("ShaderNodeMath"); mx2.operation = "MULTIPLY"; mx2.inputs[1].default_value = 0.6
    L.new(mix.outputs[0], mx2.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    cr.elements[0].color = (0.045, 0.048, 0.05, 1); cr.elements[1].position = 0.35; cr.elements[1].color = (0.075, 0.08, 0.085, 1)
    e = cr.elements.new(0.62); e.color = (0.11, 0.115, 0.12, 1)
    e = cr.elements.new(0.85); e.color = (0.15, 0.155, 0.16, 1)
    L.new(mx2.outputs[0], ramp.inputs["Fac"])
    # seam: darken the outer pixel row of every block
    fr = N.new("ShaderNodeVectorMath"); fr.operation = "FRACTION"; L.new(tc.outputs["Object"], fr.inputs[0])
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(fr.outputs[0], sx.inputs[0])
    def edge(o):
        a = N.new("ShaderNodeMath"); a.operation = "PINGPONG"; a.inputs[1].default_value = 0.5; L.new(o, a.inputs[0])
        b = N.new("ShaderNodeMath"); b.operation = "LESS_THAN"; b.inputs[1].default_value = 1 / 16; L.new(a.outputs[0], b.inputs[0])
        return b.outputs[0]
    mxe = N.new("ShaderNodeMath"); mxe.operation = "MAXIMUM"; L.new(edge(sx.outputs["X"]), mxe.inputs[0]); L.new(edge(sx.outputs["Y"]), mxe.inputs[1])
    dk = N.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.inputs["B"].default_value = (0.012, 0.013, 0.015, 1)
    mf = N.new("ShaderNodeMath"); mf.operation = "MULTIPLY"; mf.inputs[1].default_value = 0.55; L.new(mxe.outputs[0], mf.inputs[0])
    L.new(mf.outputs[0], dk.inputs["Factor"]); L.new(ramp.outputs["Color"], dk.inputs["A"])
    L.new(dk.outputs["Result"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.85
    return m


def figure(name, at, facing):
    """A plain block figure, 1.8 blocks tall, for scale (no character's likeness)."""
    m = bpy.data.materials.new(name + " mat"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.42, 0.44, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    x, y = at
    parts = [("head", (0.5, 0.5, 0.5), (0, 0, 1.55)), ("body", (0.5, 0.25, 0.75), (0, 0, 0.925)),
             ("arm L", (0.25, 0.25, 0.75), (-0.375, 0, 0.925)), ("arm R", (0.25, 0.25, 0.75), (0.375, 0, 0.925)),
             ("leg L", (0.25, 0.25, 0.75), (-0.125, 0, 0.275)), ("leg R", (0.25, 0.25, 0.75), (0.125, 0, 0.275))]
    root = link(bpy.data.objects.new(name, None)); root.location = (x, y, 0.1); root.rotation_euler = (0, 0, facing)
    for nm, s, o in parts:
        b = box(f"{name} {nm}", s, o, m); b.parent = root
    return root


def motes(name, centre, colour, count, size=0.035, spread=(9, 6, 7)):
    """Dust motes hanging in the light: tiny glowing pixels drifting slowly through the beams."""
    em = box(name + " volume", spread, (centre[0], centre[1], spread[2] / 2 + 0.1), None)
    em.display_type = "WIRE"                                     # emitter stays renderable or its particles hide too
    m = bpy.data.materials.new(name + " mat"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = srgb(np.array(INDEX["ramps"][colour][4]) * 0.6 + np.array(INDEX["ramps"][colour][3]) * 0.4)
    e.inputs["Strength"].default_value = 5.0
    L.new(e.outputs["Emission"], out.inputs["Surface"])
    px = box(name + " pixel", (size, size, size), (centre[0], centre[1], -50), m)
    ps = em.modifiers.new("motes", "PARTICLE_SYSTEM").particle_system.settings
    em.show_instancer_for_render = False
    ps.count = count; ps.frame_start = 1; ps.frame_end = 1; ps.lifetime = 400
    ps.emit_from = "VOLUME"; ps.normal_factor = 0.0; ps.distribution = "RAND"
    ps.effector_weights.gravity = -0.004; ps.brownian_factor = 0.04
    ps.render_type = "OBJECT"; ps.instance_object = px; ps.particle_size = 1.0; ps.size_random = 0.6
    ps.use_rotations = True; ps.angular_velocity_mode = "RAND"; ps.angular_velocity_factor = 1.0
    return em


def pixel_smoke(name, at, colour, count=140):
    """Minecraft-style smoke: little cubes rising off the top in puffs, grey with the corps light in them near the wall."""
    em = box(name + " emitter", (3.8, 0.8, 0.05), (at[0], at[1], 3.05), None)
    em.display_type = "WIRE"
    m = bpy.data.materials.new(name + " mat"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.5, 0.52, 0.53, 1); p.inputs["Roughness"].default_value = 1.0
    p.inputs["Emission Color"].default_value = light_rgb(colour)
    # height in the world: the light fades out of the smoke 4 blocks above the wall
    geo = N.new("ShaderNodeObjectInfo"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Location"], sx.inputs[0])
    fr = N.new("ShaderNodeMapRange"); fr.inputs["From Min"].default_value = 3.0; fr.inputs["From Max"].default_value = 7.0
    fr.inputs["To Min"].default_value = 3.0; fr.inputs["To Max"].default_value = 0.0; fr.interpolation_type = "SMOOTHSTEP"
    L.new(sx.outputs["Z"], fr.inputs["Value"]); L.new(fr.outputs["Result"], p.inputs["Emission Strength"])
    al = N.new("ShaderNodeMapRange"); al.inputs["From Min"].default_value = 3.0; al.inputs["From Max"].default_value = 10.0
    al.inputs["To Min"].default_value = 0.75; al.inputs["To Max"].default_value = 0.0
    L.new(sx.outputs["Z"], al.inputs["Value"]); L.new(al.outputs["Result"], p.inputs["Alpha"])
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    px = box(name + " puff", (0.18, 0.18, 0.18), (at[0], at[1], -50), m)
    ps = em.modifiers.new("smoke", "PARTICLE_SYSTEM").particle_system.settings
    em.show_instancer_for_render = False
    ps.count = count; ps.frame_start = -80; ps.frame_end = 160; ps.lifetime = 80; ps.lifetime_random = 0.4
    ps.emit_from = "FACE"; ps.normal_factor = 0.0; ps.factor_random = 0.15
    ps.object_align_factor = (0, 0, 0.9); ps.effector_weights.gravity = -0.02; ps.brownian_factor = 0.25
    ps.render_type = "OBJECT"; ps.instance_object = px; ps.particle_size = 1.0; ps.size_random = 0.7
    return em


def spot(key, n, x, y, off, rot, energy, size, c, blend=0.55):
    sd = bpy.data.lights.new(f"SR rays {key} {n}", "SPOT"); sd.energy = energy; sd.color = c
    sd.spot_size = R(size); sd.spot_blend = blend; sd.shadow_soft_size = 0.1
    so = link(bpy.data.objects.new(sd.name, sd)); so.location = (x + off[0], y + off[1], off[2]); so.rotation_euler = rot
    so.visible_camera = False


def take(key, kind, tex, colour, at, note, pixels=False):
    """kind: L1 as picked, L2 shafts, L3 streaks, L4 breathing."""
    x, y = at
    centre, half = (x, y, 1.5), (2.0, 0.5, 1.5)
    wall = box(f"SR wall {key}", (4, 1, 3), (x, y, 1.5), wall_mat(tex, colour))
    c = light_rgb(colour)[:3]
    reach = 4.0
    faces = [((0, 0.505, 1.5), (R(-90), 0, 0), 3.8, 2.8), ((0, -0.505, 1.5), (R(90), 0, 0), 3.8, 2.8),
             ((2.005, 0, 1.5), (0, R(90), 0), 2.8, 0.9), ((-2.005, 0, 1.5), (0, R(-90), 0), 2.8, 0.9),
             ((0, 0, 3.005), (0, 0, 0), 3.8, 0.9)]
    for n, (off, rot, w, h) in enumerate(faces):                   # every side glows (shader packs: block light)
        ld = bpy.data.lights.new(f"SR face {key} {n}", "AREA"); ld.shape = "RECTANGLE"; ld.size = w; ld.size_y = h
        ld.energy = FACE_W * (1.0 if n < 2 else 0.45); ld.color = c
        lo = link(bpy.data.objects.new(ld.name, ld)); lo.location = (x + off[0], y + off[1], off[2]); lo.rotation_euler = rot
    g = box(f"SR glow {key}", (4 + 2 * reach + 2, 1 + 2 * reach + 2, 3 + reach + 1), (x, y, (3 + reach + 1) / 2),
            glow_mat(f"SR glow {key}", colour, reach, centre, half, k=0.28 if kind == "L1" else 0.13, streaks=kind in ("L3", "L4"), pulse=kind == "L4"))
    g.display_type = "BOUNDS"; g.hide_select = True
    if kind == "L1":                                             # pass 94: one wide cone out of the top and each side
        spots = [((0, 0, 3.02), (0, 0, 0), SPOT_W, 60), ((0, -0.52, 1.5), (R(90), 0, 0), SPOT_W / 2, 60),
                 ((0, 0.52, 1.5), (R(-90), 0, 0), SPOT_W / 2, 60), ((2.02, 0, 1.5), (0, R(90), 0), SPOT_W / 2, 60),
                 ((-2.02, 0, 1.5), (0, R(-90), 0), SPOT_W / 2, 60)]
    else:                                                        # a row of narrow beams per side, fanned apart
        spots = []
        for i, dx in enumerate((-1.3, 0.0, 1.3)):
            fan = R(-14 * (i - 1))
            spots += [((dx, -0.52, 1.6), (R(90), 0, fan), SPOT_W / 2, 16),
                      ((dx, 0.52, 1.6), (R(-90), 0, -fan), SPOT_W / 2, 16),
                      ((dx, 0, 3.02), (0, -fan, 0), SPOT_W / 1.5, 16)]
        for sx in (1, -1):
            for dz, tilt in ((0.9, -10), (2.1, 10)):
                spots.append(((2.02 * sx, 0, dz), (0, R(90) * sx + R(tilt) * sx * -1, 0), SPOT_W / 2.5, 16))
    for n, (off, rot, e, size) in enumerate(spots):
        spot(key, n, x, y, off, rot, e, size, c, 0.55 if kind == "L1" else 0.3)
    if pixels:
        pixel_smoke(f"SR pixel smoke {key}", (x, y), colour)
    else:
        sm = box(f"SR smoke {key}", (4.6, 1.6, 7.0), (x, y, 3.0 + 3.5), smoke_mat(f"SR smoke {key}", colour, "S1"))
        sm.display_type = "WIRE"
    motes(f"SR motes {key}", (x, y), colour, 170)
    figure(f"SR figure {key}", (x - 4.2, y - 2.2), math.radians(-35))
    hm = HAZE if kind == "L1" else local_haze_mat(f"SR haze {key}", centre, half)
    hz = box(f"SR haze {key}", (34, 34, 20), (x, y, 10.0), hm); hz.display_type = "BOUNDS"; hz.hide_select = True
    label(f"{key}  {note}", (x, y))
    cam = bpy.data.objects.new(f"Cam {key}", bpy.data.cameras.new(f"Cam {key}")); link(cam)
    cam.data.lens = 28
    eye = Vector((x + 8.5, y - 11.0, 3.2)); tgt = Vector((x, y, 3.4))
    cam.location = eye; cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
    return cam


FACE_W, SPOT_W = 400.0, 9000.0
HAZE_NEAR, HAZE_FAR = 0.16, 0.012
HAZE = haze_mat()
GAP = 40.0
TAKES = [("D1", "L3", "br1", "green", "streaks+", False), ("D2", "L2", "br1", "green", "shafts+", False),
         ("D3", "L3", "br1", "green", "pixel smoke", True), ("D3c", "L3", "h1", "crimson", "pixel smoke, H1 crimson", True)]
cams = {}
for i, (key, kind, tex, colour, note, pixels) in enumerate(TAKES):
    cams[key] = take(key, kind, tex, colour, ((i - 1.5) * GAP, 0.0), note, pixels)

# ground and haze
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
ground = bpy.context.active_object
for c in ground.users_collection:
    c.objects.unlink(ground)
link(ground); ground.name = "SR ground"; ground.scale = (200, 120, 1); bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.update()
ground.data.transform(ground.matrix_basis); ground.scale = (1, 1, 1)         # object coords = world blocks
ground.data.materials.append(pixel_ground_mat())

world = bpy.data.worlds.new("SR night"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.005, 0.008, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world
allc = bpy.data.objects.new("Cam all", bpy.data.cameras.new("Cam all")); link(allc); allc.data.lens = 28
eye, tgt = Vector((0, -80, 30)), Vector((0, 0, 3)); allc.location = eye
allc.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
cams["all"] = allc
scene.camera = cams["D1"]

for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
ee = scene.eevee
for attr, v in (("use_volumetric_shadows", True), ("volumetric_tile_size", "4"), ("volumetric_samples", 96),
                ("volumetric_end", 120.0), ("use_shadows", True), ("volumetric_light_clamp", 0.0)):
    try:
        setattr(ee, attr, v)
    except Exception:
        pass
try:
    scene.cycles.volume_step_rate = 2.0; scene.cycles.volume_max_steps = 256
except Exception:
    pass
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"                # AgX washes bright green toward white
except Exception:
    pass
try:                                                             # bloom: Render Layers > Glare (Bloom) > output
    tree = bpy.data.node_groups.new("SR bloom", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); rl.scene = scene
    gl = tree.nodes.new("CompositorNodeGlare")
    try:
        gl.inputs["Type"].default_value = "Bloom"
    except Exception:
        gl.glare_type = "BLOOM"
    for nm, v in (("Threshold", 0.6), ("Strength", 0.7), ("Size", 0.5)):
        try:
            gl.inputs[nm].default_value = v
        except Exception:
            pass
    go = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("bloom:", e)

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(80)
        scene.render.filepath = os.path.join(rdir, f"305_detail_{key}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["D1"]
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
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
