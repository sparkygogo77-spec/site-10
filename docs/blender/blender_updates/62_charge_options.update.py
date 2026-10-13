# Pass 62: charging animation options (J: "the light coming into the ring should be subtle but smooth; the
# lantern getting super bright, in an even cooler way, is the most important"). Four Dark Lanterns (L1) side
# by side, each with its own charge running 0 -> full over 6 s (the game's charge time), a 1.5 s overcharge
# climax, then letting go. The ring floats beside each lantern with a thin, slow thread of light into it.
#   A  heartbeat to white star: beats that speed up as it fills, the core turning white-hot at the top
#   B  lightning first: the gold cracks light up and run with lightning, then the glass fills behind them
#   C  rising tide: light fills the glass like liquid with a moving surface, then brims over into a halo
#   D  storm: the swirl spins faster and tighter as it charges until it blurs into one blaze
# Builds its own file (LanternLive\charge_options.blend), plays it, and keeps the watcher on.
import os, math
import bpy
import numpy as np
from mathutils import Vector

R = math.radians
FPS = 24
OUT = os.path.join(FOLDER, "charge_options.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()

old = bpy.data.scenes.get("Charge Options")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Charge Options")
col = scene.collection
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, 236
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


# ---- the lantern and the ring meshes (the same model files as the game) -------------------------------------
def npz_mesh(name, path, extra_glow=False):
    d = np.load(path)
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    if extra_glow and "glow" in d.files:
        g = me.attributes.new("glow", "FLOAT", "CORNER")
        g.data.foreach_set("value", np.repeat(np.asarray(d["glow"], np.float32), 4))
    kind = np.asarray(d["kind"], np.int32)
    for _ in range(int(kind.max()) + 1):
        me.materials.append(None)
    me.polygons.foreach_set("material_index", kind)
    return me, kind


lantern_me, lantern_kind = npz_mesh("charge lantern", os.path.join(FOLDER, "dark5_l1.npz"), True)
ring_me, ring_kind = npz_mesh("charge ring", os.path.join(FOLDER, "ring_sq.npz"))
ZMIN, ZMAX, PZ = 0.75, 29.25, 11.75


# ---- node helpers ---------------------------------------------------------------------------------------------
class G:
    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.m.use_nodes = True
        self.N, self.L = self.m.node_tree.nodes, self.m.node_tree.links
        self.N.clear()

    def op(self, o, a, b=None, clamp=False):
        n = self.N.new("ShaderNodeMath"); n.operation = o; n.use_clamp = clamp
        for i, s in enumerate((a, b)):
            if s is None:
                continue
            if isinstance(s, (int, float)):
                n.inputs[i].default_value = s
            else:
                self.L.new(s, n.inputs[i])
        return n.outputs[0]

    def drv(self, expr, ctl=None):
        v = self.N.new("ShaderNodeValue")
        d = v.outputs[0].driver_add("default_value").driver
        d.type = "SCRIPTED"
        if ctl is not None:
            var = d.variables.new(); var.name = "c"; var.type = "SINGLE_PROP"
            var.targets[0].id_type = "OBJECT"; var.targets[0].id = ctl; var.targets[0].data_path = '["charge"]'
        d.expression = expr
        return v.outputs[0]

    def green_ramp(self, fac, white=None):
        r = self.N.new("ShaderNodeValToRGB")
        els = r.color_ramp.elements
        els[0].position, els[0].color = 0.0, (0.0, 0.08, 0.02, 1)
        els[1].position, els[1].color = 1.0, (0.8, 1.0, 0.62, 1)
        for pos, cc in ((0.2, (0.0, 0.3, 0.07, 1)), (0.42, (0.02, 0.72, 0.17, 1)), (0.62, (0.16, 1.0, 0.3, 1)),
                        (0.82, (0.62, 1.0, 0.45, 1))):
            e = els.new(pos); e.color = cc
        self.L.new(fac, r.inputs["Fac"])
        return r.outputs["Color"]


def lantern_material(mode, part, ctl):
    g = G(f"charge {mode} {part}")
    N, L, op = g.N, g.L, g.op
    out = N.new("ShaderNodeOutputMaterial")
    colA = N.new("ShaderNodeAttribute"); colA.attribute_name = "col"
    gw = N.new("ShaderNodeAttribute"); gw.attribute_name = "glow"
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    x, y, z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    t = g.drv(f"frame / {FPS}")
    c = g.drv("min(max(c, 0), 1.4)", ctl)
    hot = g.drv("min(max((c - 0.85) / 0.45, 0), 1)", ctl)          # the overcharge climax, 0 -> 1
    dz = op("SUBTRACT", z, PZ); adz = op("ABSOLUTE", dz)
    rad = op("SQRT", op("ADD", op("MULTIPLY", x, x), op("MULTIPLY", y, y)))
    d3 = op("SQRT", op("ADD", op("MULTIPLY", dz, dz), op("MULTIPLY", op("MULTIPLY", rad, rad), 0.25)))
    reach = op("ADD", 2.0, op("MULTIPLY", c, 7.0))
    ball = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", d3, reach), 2.0)))
    core = op("EXPONENT", op("MULTIPLY", -1.0, op("DIVIDE", d3, op("ADD", 3.0, op("MULTIPLY", hot, 10.0)))))
    noise = N.new("ShaderNodeTexNoise"); noise.noise_dimensions = "4D"; noise.inputs["Scale"].default_value = 0.3
    L.new(tc.outputs["Object"], noise.inputs["Vector"]); L.new(op("MULTIPLY", t, 0.5), noise.inputs["W"])
    nz = noise.outputs["Fac"]

    if mode == "A":       # heartbeat to white star
        phase = g.drv("c * 7 + c * c * c * 15", ctl)
        beat = op("POWER", op("MULTIPLY", op("ADD", op("COSINE", op("MULTIPLY", phase, 2 * math.pi)), 1.0), 0.5), 10.0)
        light = op("ADD", op("MULTIPLY", ball, op("ADD", 0.65, op("MULTIPLY", beat, 0.9))), op("MULTIPLY", core, op("MULTIPLY", hot, 1.6)))
    elif mode == "B":     # lightning in the cracks first, then the glass fills behind
        front = op("ADD", ZMIN - 2, op("MULTIPLY", op("SUBTRACT", c, 0.25), (ZMAX - ZMIN) * 1.5))
        filled = op("MINIMUM", op("MAXIMUM", op("DIVIDE", op("SUBTRACT", front, z), 3.0), 0.0), 1.0)
        bolt = op("POWER", op("MULTIPLY", op("ADD", op("SINE", op("SUBTRACT", op("MULTIPLY", z, 0.9), op("MULTIPLY", t, 9.0))), 1.0), 0.5), 6.0)
        if part == "crack":
            light = op("ADD", op("MULTIPLY", op("MINIMUM", op("MULTIPLY", c, 3.0), 1.0), op("ADD", 0.5, op("MULTIPLY", bolt, 1.4))), op("MULTIPLY", hot, 1.5))
        else:
            light = op("ADD", op("MULTIPLY", filled, op("ADD", 0.55, op("MULTIPLY", nz, 0.45))), op("MULTIPLY", core, op("MULTIPLY", hot, 1.5)))
    elif mode == "C":     # rising tide with a moving surface, brimming over at the top
        wave = op("MULTIPLY", op("SINE", op("ADD", op("MULTIPLY", x, 0.8), op("MULTIPLY", t, 2.5))), op("SINE", op("ADD", op("MULTIPLY", y, 0.7), op("MULTIPLY", t, 1.9))))
        surface = op("ADD", op("ADD", ZMIN, op("MULTIPLY", op("MINIMUM", c, 1.0), (ZMAX - ZMIN) * 1.04)), op("MULTIPLY", wave, 0.8))
        depth = op("SUBTRACT", surface, z)
        lit = op("MINIMUM", op("MAXIMUM", op("MULTIPLY", depth, 0.5), 0.0), 1.0)
        menisc = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", depth, 0.7), 2.0)))
        light = op("ADD", op("ADD", op("MULTIPLY", lit, op("ADD", 0.6, op("MULTIPLY", nz, 0.4))), op("MULTIPLY", menisc, 1.1)),
                   op("MULTIPLY", core, op("MULTIPLY", hot, 1.4)))
    else:                 # D storm: the swirl spins faster and tighter until it blurs into one blaze
        ang = op("ARCTAN2", y, x)
        spin = g.drv("c * 9 + c * c * 22", ctl)
        ph = op("ADD", op("MULTIPLY", ang, 3.0), op("ADD", op("MULTIPLY", dz, 0.55), spin))
        swirl = op("POWER", op("MULTIPLY", op("ADD", op("SINE", ph), 1.0), 0.5), 3.0)
        blur = op("ADD", op("MULTIPLY", swirl, op("SUBTRACT", 1.0, hot)), op("MULTIPLY", hot, 0.9))
        light = op("ADD", op("MULTIPLY", ball, 0.7), op("MULTIPLY", blur, op("ADD", 0.25, op("MULTIPLY", ball, 0.9))))
        light = op("ADD", light, op("MULTIPLY", core, op("MULTIPLY", hot, 1.4)))

    light = op("MULTIPLY", light, op("ADD", 0.4 if part == "body" else 0.8, gw.outputs["Fac"]))
    fac = op("MINIMUM", op("ADD", op("MULTIPLY", light, 0.75), op("MULTIPLY", hot, 0.2)), 0.9)  # stays green at the top
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(colA.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.85 if part == "crack" else 0.0
    b.inputs["Roughness"].default_value = 0.28 if part == "crack" else 0.16
    b.inputs["Coat Weight"].default_value = 0.0 if part == "crack" else 0.9
    L.new(g.green_ramp(fac), b.inputs["Emission Color"])
    s = 4.0 if part == "body" else 6.0
    strength = op("MULTIPLY", op("MULTIPLY", op("MULTIPLY", light, light), op("MULTIPLY", c, c)), op("ADD", s, op("MULTIPLY", hot, s * 0.8)))
    L.new(strength, b.inputs["Emission Strength"])
    L.new(b.outputs[0], out.inputs["Surface"])
    return g.m


def plain(name, metallic, rough, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "col"
    L.new(a.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Metallic"].default_value = metallic; p.inputs["Roughness"].default_value = rough
    if emit:
        L.new(a.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m


def ring_material(ctl):
    g = G("charge ring glow")
    N, L, op = g.N, g.L, g.op
    out = N.new("ShaderNodeOutputMaterial")
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "col"
    c = g.drv("min(max(c, 0), 1.4)", ctl)
    p = N.new("ShaderNodeBsdfPrincipled")
    L.new(a.outputs["Color"], p.inputs["Base Color"]); L.new(a.outputs["Color"], p.inputs["Emission Color"])
    L.new(op("ADD", 1.5, op("MULTIPLY", c, 4.0)), p.inputs["Emission Strength"])      # the ring warms gently
    L.new(p.outputs[0], out.inputs["Surface"])
    return g.m


def stream_material(ctl):
    """The thread of light into the ring: thin, faint, slow beads gliding along it."""
    g = G("charge stream")
    N, L, op = g.N, g.L, g.op
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    u = sep.outputs[0]
    t = g.drv(f"frame / {FPS}")
    c = g.drv("min(max(c, 0), 1.0) * (1 if c < 1.4 else 0)", ctl)
    bead = op("POWER", op("MULTIPLY", op("ADD", op("SINE", op("SUBTRACT", op("MULTIPLY", u, 40.0), op("MULTIPLY", t, 3.0))), 1.0), 0.5), 4.0)
    ends = op("MULTIPLY", op("MINIMUM", op("MULTIPLY", u, 6.0), 1.0), op("MINIMUM", op("MULTIPLY", op("SUBTRACT", 1.0, u), 6.0), 1.0))
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 1.0, 0.5, 1)
    L.new(op("MULTIPLY", op("MULTIPLY", op("ADD", 0.25, op("MULTIPLY", bead, 0.75)), ends), op("MULTIPLY", c, 3.0)), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(op("ADD", 0.15, op("MULTIPLY", c, 0.5), clamp=True), mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    try:
        g.m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return g.m


def halo_material(ctl):
    g = G("charge halo")
    N, L, op = g.N, g.L, g.op
    out = N.new("ShaderNodeOutputMaterial")
    hot = g.drv("min(max((c - 1.0) / 0.3, 0), 1) * (1 if c < 1.42 else 0)", ctl)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.5, 1.0, 0.55, 1)
    L.new(op("MULTIPLY", hot, 12.0), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    L.new(hot, mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return g.m


# ---- one option: lantern + charge control + ring + stream + inner light --------------------------------------
OPTIONS = [("A", "A  heartbeat to white star"), ("B", "B  lightning first, then it fills"),
           ("C", "C  rising tide, brims over"), ("D", "D  storm spinning into a blaze")]
SPACING = 3.4
matte = plain("charge matte", 0.0, 0.6)
fleck = plain("charge fleck", 1.0, 0.15)
gold = plain("charge gold", 0.85, 0.28)
for i, (mode, title) in enumerate(OPTIONS):
    base = Vector((i * SPACING, 0, 0))
    ctl = link(bpy.data.objects.new(f"Charge control {mode}", None))
    ctl.location = base + Vector((0, 0, -0.4))
    ctl["charge"] = 0.0
    # the charge: 0.5 s rest, 6 s to full (eased), 1.5 s climax to overcharge, hold, let go, rest
    for f, v in ((12, 0.0), (156, 1.0), (192, 1.4), (208, 1.4), (222, 0.0), (236, 0.0)):
        ctl["charge"] = v
        ctl.keyframe_insert('["charge"]', frame=f)
    body = lantern_material(mode, "body", ctl)
    crack = lantern_material(mode, "crack", ctl)
    o = link(bpy.data.objects.new(f"Charge lantern {mode}", lantern_me))
    o.scale = (1 / 16,) * 3
    o.location = base
    # per-object materials so each lantern has its own charge
    for k, m in enumerate((matte, gold, matte, fleck, body, crack)):
        slot = o.material_slots[k]
        slot.link = "OBJECT"
        slot.material = m
    # the light inside, lighting the floor and the hand
    li = bpy.data.lights.new(f"charge inner {mode}", "POINT")
    li.color = (0.45, 1.0, 0.5); li.shadow_soft_size = 0.3
    d = li.driver_add("energy").driver
    d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "c"; v.targets[0].id = ctl; v.targets[0].data_path = '["charge"]'
    d.expression = "max(c, 0) ** 2 * 60 + max(c - 1, 0) * 300"
    lo = link(bpy.data.objects.new(f"Charge inner light {mode}", li))
    lo.location = base + Vector((0, 0, PZ / 16))
    # the ring, beside the lantern at hand height, facing it
    r = link(bpy.data.objects.new(f"Charge ring {mode}", ring_me))
    rm = ring_material(ctl)
    for k, m in enumerate((matte, fleck, matte, matte, rm, rm, rm)[:len(r.material_slots)]):
        r.material_slots[k].link = "OBJECT"; r.material_slots[k].material = m
    r.scale = (1 / 14,) * 3
    r.location = base + Vector((1.15, -0.35, 1.0))
    r.rotation_euler = (R(80), 0, R(65))
    # the thread of light from the lantern's heart to the ring
    cu = bpy.data.curves.new(f"charge stream {mode}", "CURVE")
    cu.dimensions = "3D"; cu.bevel_depth = 0.006
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(1)
    p0, p1 = base + Vector((0.12, 0, PZ / 16)), r.location
    for bp, p, hnd in ((sp.bezier_points[0], p0, Vector((0.35, -0.1, 0.25))), (sp.bezier_points[1], p1, Vector((-0.25, 0, -0.2)))):
        bp.co = p; bp.handle_left = p - hnd; bp.handle_right = p + hnd
    cu.materials.append(stream_material(ctl))
    link(bpy.data.objects.new(f"Charge stream {mode}", cu))
    # option C: the halo it brims over into
    if mode == "C":
        bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.025, location=base + Vector((0, 0, ZMAX / 16 + 0.25)))
        h = bpy.context.active_object
        for cc in list(h.users_collection):
            cc.objects.unlink(h)
        col.objects.link(h)
        h.name = "Charge halo C"
        h.data.materials.append(halo_material(ctl))
    # label
    cu2 = bpy.data.curves.new(title, "FONT"); cu2.body = title; cu2.size = 0.17; cu2.align_x = "CENTER"
    lb = link(bpy.data.objects.new("Label " + title, cu2))
    lb.location = base + Vector((0.4, 0, 2.35)); lb.rotation_euler = (R(90), 0, 0)
    lm = bpy.data.materials.new("charge label " + mode); lm.use_nodes = True
    lp = lm.node_tree.nodes.get("Principled BSDF")
    lp.inputs["Emission Color"].default_value = (0.85, 1, 0.9, 1); lp.inputs["Emission Strength"].default_value = 2.0
    cu2.materials.append(lm)

# ---- room, cameras, glow -----------------------------------------------------------------------------------------
world = bpy.data.worlds.new("Charge World"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.01, 0.012, 0.016, 1); bg.inputs[1].default_value = 1.0
scene.world = world
import bmesh
fl = bpy.data.meshes.new("charge floor")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12); bm.to_mesh(fl); bm.free()
fo = link(bpy.data.objects.new("Charge floor", fl)); fo.location = (SPACING * 1.5, 0, 0)
fm = bpy.data.materials.new("charge floor"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.05, 0.055, 0.06, 1)
fm.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.35
fl.materials.append(fm)
sun = bpy.data.lights.new("charge key", "AREA"); sun.energy = 40; sun.size = 4
so = link(bpy.data.objects.new("charge key", sun)); so.location = (SPACING * 1.5, -4, 5); so.rotation_euler = (R(40), 0, 0)


def camera(name, target, dist, lens=50, height=0.9):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = link(bpy.data.objects.new(name, cd))
    c.location = target + Vector((0, -dist, height))
    c.rotation_euler = (target - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


cams = {"row": camera("Cam all four", Vector((SPACING * 1.5 + 0.4, 0, 1.0)), 19.0, 50, 1.4)}
for i, (mode, _) in enumerate(OPTIONS):
    cams[mode] = camera(f"Cam {mode}", Vector((i * SPACING + 0.45, 0, 1.0)), 4.2, 50, 0.6)
scene.camera = cams["row"]
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
try:
    scene.eevee.use_raytracing = True
except Exception:
    pass

# bloom: a fog-glow glare in the compositor (Blender 5 node groups, with a fallback for older versions)
try:
    tree = bpy.data.node_groups.new("Charge Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    gi = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:                      # Blender 5: the glare type is a menu socket
        try:
            gl.inputs["Type"].default_value = "Bloom"
        except Exception:
            gl.inputs["Type"].default_value = "Fog Glow"
    else:
        gl.glare_type = "BLOOM"
    for nm, val in (("Size", 0.6), ("Strength", 0.35), ("Threshold", 1.2)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(gi.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no compositor glow:", e)

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for f in (90, 150, 190):
        scene.frame_set(f)
        scene.camera = cams["row"]
        scene.render.filepath = os.path.join(rdir, f"62_charge_row_f{f}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["row"]
scene.frame_set(1)

# its own file, then keep watching and play
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
                    try:
                        sp.shading.use_compositor = "ALWAYS"
                    except Exception:
                        pass
            a.tag_redraw()


def _after():
    try:
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
    except Exception as e:
        print("watch:", e)
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("play:", e)
    return None


bpy.app.timers.register(_after, first_interval=1.5)
print("charge options saved as", OUT)
