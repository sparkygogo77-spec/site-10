# Pass 69: G3 on its own (J: "G3 looks great"), with:
#  - the top and bottom of the glass fading much harder, to near-black emerald at the very edges, while the
#    cracks keep their bright yellow glow
#  - the slightest helix twist in the pinched glass (3 degrees top to bottom)
#  - the ring docking: it flies in, turns to face the port and pushes physically into it; the charge starts the
#    moment it seats, spreading out from the port; after the fade it pulls back out
#  - the yellow cracks hold their own glow (they no longer scale with the green) until the green swallows them;
#    the climax is a very bright green, not white
# Builds LanternLive\charge_g3.blend, plays it, keeps the watcher on.
import os, math
import bpy
import numpy as np
from mathutils import Vector

R = math.radians
FPS = 24
OUT = os.path.join(FOLDER, "charge_g3.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()

old = bpy.data.scenes.get("Charge G3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Charge G3")
col = scene.collection
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, 680
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

    def drv(self, expr, ctl=None, prop="charge"):
        v = self.N.new("ShaderNodeValue")
        d = v.outputs[0].driver_add("default_value").driver
        d.type = "SCRIPTED"
        if ctl is not None:
            var = d.variables.new(); var.name = "c"; var.type = "SINGLE_PROP"
            var.targets[0].id_type = "OBJECT"; var.targets[0].id = ctl; var.targets[0].data_path = f'["{prop}"]'
        d.expression = expr
        return v.outputs[0]

    def green_ramp(self, fac, white=None):
        r = self.N.new("ShaderNodeValToRGB")
        els = r.color_ramp.elements
        els[0].position, els[0].color = 0.0, (0.0, 0.08, 0.02, 1)
        els[1].position, els[1].color = 1.0, (0.12, 1.0, 0.22, 1)
        for pos, cc in ((0.2, (0.0, 0.3, 0.07, 1)), (0.42, (0.02, 0.72, 0.17, 1)), (0.62, (0.06, 1.0, 0.2, 1)),
                        (0.82, (0.1, 1.0, 0.22, 1))):
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
    hot = g.drv("min(max((c - 0.9) / 0.4, 0), 1)", ctl)          # the overcharge climax, 0 -> 1
    dz = op("SUBTRACT", z, PZ); adz = op("ABSOLUTE", dz)
    rad = op("SQRT", op("ADD", op("MULTIPLY", x, x), op("MULTIPLY", y, y)))
    d3 = op("SQRT", op("ADD", op("MULTIPLY", dz, dz), op("MULTIPLY", op("MULTIPLY", rad, rad), 0.25)))
    reach = op("ADD", 2.0, op("MULTIPLY", c, 7.0))
    ball = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", d3, reach), 2.0)))
    core = op("EXPONENT", op("MULTIPLY", -1.0, op("DIVIDE", d3, op("ADD", 3.0, op("MULTIPLY", hot, 10.0)))))
    noise = N.new("ShaderNodeTexNoise"); noise.noise_dimensions = "4D"; noise.inputs["Scale"].default_value = 0.3
    L.new(tc.outputs["Object"], noise.inputs["Vector"]); L.new(op("MULTIPLY", t, 0.5), noise.inputs["W"])
    nz = noise.outputs["Fac"]

    band = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", adz, op("ADD", 3.5, op("MULTIPLY", c, 2.4))), 4.0)))
    strand_band = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", adz, op("ADD", 2.2, op("MULTIPLY", c, 1.8))), 3.0)))
    ang = op("ARCTAN2", y, x)
    spin = g.drv("c", ctl, "spin")
    rel = g.drv("c", ctl, "release")
    lit_on = g.drv("1 if c > 0.001 else 0", ctl)                    # on the instant the ring touches
    ign = g.drv("min((c - 0.04) / 0.14, 1) if c > 0.04 else 0", ctl)   # the touch spreading out over the first ~3 s
    fl = N.new("ShaderNodeTexNoise"); fl.noise_dimensions = "4D"; fl.inputs["Scale"].default_value = 0.9
    fl.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], fl.inputs["Vector"]); L.new(op("MULTIPLY", t, 2.2), fl.inputs["W"])
    flare = op("POWER", fl.outputs["Fac"], 3.0)
    # where the ring connects: the port, front and centre
    dyp = op("ADD", y, 5.0)
    dP = op("SQRT", op("ADD", op("ADD", op("MULTIPLY", x, x), op("MULTIPLY", dyp, dyp)), op("MULTIPLY", dz, dz)))
    front = op("MULTIPLY", ign, 30.0)
    spread = op("MINIMUM", op("MAXIMUM", op("DIVIDE", op("SUBTRACT", front, dP), 3.0), 0.0), 1.0)
    wave = op("MULTIPLY", op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", op("SUBTRACT", front, dP), 2.0), 2.0))), op("SUBTRACT", 1.0, ign))
    if part == "crack":
        cfront = op("MULTIPLY", op("MINIMUM", op("DIVIDE", c, 0.85), 1.0), max(ZMAX - PZ, PZ - ZMIN) + 1.0)
        age = op("SUBTRACT", cfront, adz)
        lit = op("MINIMUM", op("MAXIMUM", op("MULTIPLY", age, 1.2), 0.0), 1.0)
        bolt = op("POWER", op("MULTIPLY", op("ADD", op("SINE", op("SUBTRACT", op("MULTIPLY", adz, 0.9), op("MULTIPLY", t, 9.0))), 1.0), 0.5), 6.0)
        tip = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", age, 1.6), 2.0)))
        light = op("ADD", op("MULTIPLY", lit, op("ADD", 0.8, op("MULTIPLY", bolt, 0.9))), op("MULTIPLY", tip, 1.5))
        light = op("ADD", light, op("ADD", op("MULTIPLY", hot, 1.2), op("MULTIPLY", rel, 1.5)))
        light = op("ADD", light, op("MULTIPLY", wave, 1.2))
        touch = op("MULTIPLY", wave, 1.2)
        # J: the yellow cracks don't grow with the green; they hold their own glow, then the green swallows them
        consume = g.drv("min(max((c - 0.95) / 0.35, 0), 1)", ctl)
        crack_fixed = op("ADD", op("MULTIPLY", lit, op("ADD", 0.8, op("MULTIPLY", bolt, 0.6))), tip)
        yel = op("SUBTRACT", 1.0, consume)
    else:
        big = 1.6 if mode == "F2" else 1.0
        reach = op("ADD", 1.4, op("MULTIPLY", c, 3.8 * big))
        ball = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", d3, reach), 2.0)))
        ph = op("ADD", op("MULTIPLY", ang, 3.0), op("ADD", op("MULTIPLY", dz, 0.55), spin))
        sw = op("POWER", op("MULTIPLY", op("ADD", op("SINE", ph), 1.0), 0.5), 3.0)
        rays = op("MULTIPLY", flare, op("EXPONENT", op("MULTIPLY", -1.0, op("DIVIDE", d3, op("ADD", 1.5, op("MULTIPLY", c, 4.0 * big))))))
        centre = op("MULTIPLY", op("POWER", ball, 2.0), op("ADD", 0.7, op("MULTIPLY", flare, 1.6 * big)))   # the flaring heart
        light = op("ADD", op("ADD", op("MULTIPLY", ball, 0.6), centre), op("MULTIPLY", rays, 1.5 * big))
        light = op("ADD", light, op("MULTIPLY", op("MULTIPLY", sw, strand_band), op("ADD", 0.35, op("MULTIPLY", ball, 0.9))))
        light = op("ADD", light, op("MULTIPLY", core, op("MULTIPLY", hot, 1.7)))
        light = op("ADD", light, op("MULTIPLY", rel, op("MULTIPLY", core, 2.2)))          # the flash as it lets go
        light = op("MULTIPLY", light, band)
        ends = op("EXPONENT", op("MULTIPLY", -1.0, op("POWER", op("DIVIDE", adz, op("ADD", 4.4, op("MULTIPLY", c, 1.6))), 2.6)))
        # lit at the touch: a soft glow spreading from the ring's side, in the lantern's own greens
        glow0 = op("MULTIPLY", spread, op("MULTIPLY", lit_on, op("ADD", 0.28, op("MULTIPLY", nz, 0.2))))
        roll = op("MULTIPLY", wave, 2.4 if mode == "F3" else 1.0)
        light = op("ADD", light, op("ADD", op("MULTIPLY", glow0, op("SUBTRACT", 1.0, op("MULTIPLY", band, 0.5))), roll))
        touch = op("ADD", glow0, roll)
        light = op("MULTIPLY", light, op("ADD", 0.015, op("MULTIPLY", ends, 0.985)))   # near-black emerald at the very ends
        touch = op("MULTIPLY", touch, op("ADD", 0.04, op("MULTIPLY", ends, 0.96)))
        yel = op("MULTIPLY", op("MINIMUM", op("ADD", op("MULTIPLY", centre, 0.55), op("MULTIPLY", rays, 0.35)), 0.75),
                 op("SUBTRACT", 1.0, hot))                       # yellow in the flow, gone to pure green at the climax
    light = op("MULTIPLY", light, op("ADD", 0.4 if part == "body" else 0.8, gw.outputs["Fac"]))
    fac = op("MINIMUM", op("ADD", op("MULTIPLY", light, 0.75), op("MULTIPLY", hot, 0.2)), 0.9)  # stays green at the top
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(colA.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.85 if part == "crack" else 0.0
    b.inputs["Roughness"].default_value = 0.28 if part == "crack" else 0.16
    b.inputs["Coat Weight"].default_value = 0.0 if part == "crack" else 0.9
    col_out = g.green_ramp(fac)
    if yel is not None:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
        L.new(yel, mx.inputs["Factor"])
        L.new(col_out, mx.inputs[6]); mx.inputs[7].default_value = (1.0, 0.82, 0.12, 1) if part == "crack" else (1.0, 0.9, 0.38, 1)
        col_out = mx.outputs[2]
    L.new(col_out, b.inputs["Emission Color"])
    s = 4.0 if part == "body" else 6.0
    strength = op("MULTIPLY", op("MULTIPLY", op("MULTIPLY", light, light), op("ADD", 0.08, op("MULTIPLY", c, c))), op("ADD", s, op("MULTIPLY", hot, s * 1.6)))
    strength = op("ADD", strength, op("MULTIPLY", touch, 1.8))       # the touch shows at once, not after the charge builds
    if part == "crack":
        strength = op("ADD", op("MULTIPLY", op("MULTIPLY", crack_fixed, 5.0), op("SUBTRACT", 1.0, consume)),
                      op("MULTIPLY", strength, consume))
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
OPTIONS = [("F3", "G3")]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


DOCK = 48          # the ring takes 2.5 s to fly in and seat; the charge starts as it seats (frame 60)


def charge_at(f):
    """12 s to full, 2 s climax, hold, a slow 7.5 s fade (J), starting when the ring seats in the port."""
    f -= DOCK
    if f < 12:
        return 0.0
    if f < 300:
        return 0.04 + 0.96 * ease((f - 12) / 288) if f > 12 else 0.0
    if f < 348:
        return 1.0 + 0.4 * ease((f - 300) / 48)
    if f < 380:
        return 1.4
    if f < 560:
        return 1.4 * (1 - ease((f - 380) / 180))       # twice as long as F (J)
    return 0.0
SPACING = 3.4
matte = plain("charge matte", 0.0, 0.6)
fleck = plain("charge fleck", 1.0, 0.15)
gold = plain("charge gold", 0.85, 0.28)
for i, (mode, title) in enumerate(OPTIONS):
    base = Vector((i * SPACING, 0, 0))
    ctl = link(bpy.data.objects.new(f"Charge control {mode}", None))
    ctl.location = base + Vector((0, 0, -0.4))
    ctl["charge"] = 0.0; ctl["spin"] = 0.0; ctl["release"] = 0.0
    # the charge: 0.5 s rest, 6 s to full (eased), 1.5 s climax to overcharge, hold, let go, rest
    spin_acc = 0.0
    for f in range(1, 681, 2):
        cv = charge_at(f)
        spin_acc += (0.5 + 4.5 * min(cv, 1.4)) * 2 / FPS     # radians: faster as it fills, never backwards
        ctl["charge"] = cv; ctl.keyframe_insert('["charge"]', frame=f)
        ctl["spin"] = spin_acc; ctl.keyframe_insert('["spin"]', frame=f)
        ctl["release"] = math.exp(-((f - 396 - DOCK) / 16.0) ** 2); ctl.keyframe_insert('["release"]', frame=f)
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
    d.expression = "pow(max(c, 0), 2) * 60 + max(c - 1, 0) * 300 + 6 * min(c * 1000, 1)"
    lo = link(bpy.data.objects.new(f"Charge inner light {mode}", li))
    lo.location = base + Vector((0, 0, PZ / 16))
    # the ring, beside the lantern at hand height, facing it
    r = link(bpy.data.objects.new(f"Charge ring {mode}", ring_me))
    rm = ring_material(ctl)
    for k, m in enumerate((matte, fleck, matte, matte, rm, rm, rm)[:len(r.material_slots)]):
        r.material_slots[k].link = "OBJECT"; r.material_slots[k].material = m
    RS = 1 / 25.6                       # the ring's face (5 px) fits the port (about 6 px across)
    r.scale = (RS,) * 3
    port = base + Vector((0, -5.0 / 16, 11.7 / 16))
    seated = port + Vector((0, 1.9 / 16 - 5 * RS, 0))      # the face pushed down into the 2 px deep port
    ready = port + Vector((0, -0.28, 0))
    for f, loc, rot in ((1, base + Vector((0.9, -1.7, 1.15)), (R(-55), R(25), R(35))),
                        (38, ready, (R(-90), 0, 0)), (DOCK + 12, seated, (R(-90), 0, 0)),
                        (600 + DOCK, seated, (R(-90), 0, 0)), (630 + DOCK, ready, (R(-90), 0, 0))):
        r.location = loc; r.rotation_euler = rot
        r.keyframe_insert("location", frame=f); r.keyframe_insert("rotation_euler", frame=f)
    # the slightest helix in the pinched glass
    tw = o.modifiers.new("twist", "SIMPLE_DEFORM")
    tw.deform_method = "TWIST"; tw.deform_axis = "Z"; tw.angle = R(3); tw.limits = (0.03, 0.80)
    # option C: the halo it brims over into
    if mode == "C_none":
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


cams = {"row": camera("Cam G3 side", Vector((0.0, -0.3, 0.73)), 2.0, 35, 0.15)}
cams["row"].location = Vector((1.4, -1.6, 0.95))
cams["row"].rotation_euler = (Vector((0.0, -0.32, 0.73)) - cams["row"].location).to_track_quat("-Z", "Y").to_euler()
for i, (mode, _) in enumerate(OPTIONS):
    cams[mode] = camera("Cam G3 close", Vector((0.1, 0, 0.95)), 6.0, 50, 0.5)
scene.camera = cams["F3"]
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"     # keeps the brightest light green instead of washing to white
    scene.view_settings.look = "None"
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
    for f in (60, 250, 380, 460, 560):
        scene.frame_set(f)
        scene.camera = cams["F3"]
        scene.render.filepath = os.path.join(rdir, f"69_g3_f{f}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["F3"]
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
    try:   # hide the lantern the watcher reloads after a file switch
        for ob in bpy.context.scene.objects:
            if ob.type in {"MESH", "EMPTY"} and not ob.name.startswith(("Charge", "charge", "Cam", "Label")):
                ob.hide_viewport = True; ob.hide_render = True
    except Exception:
        pass
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


bpy.app.timers.register(_after, first_interval=4.0)
print("charge options saved as", OUT)
