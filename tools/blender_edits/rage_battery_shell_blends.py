"""Blender edit for rage_battery_c.blend (J, 2026-10-13): from his picks S2 (dark-green bands), S4 (light shimmer)
and S5 (dark-green veins): "make the lines more obscure and blend better, bigger effects, in every direction, give
me 9 variants of those". Adds a row of nine green barriers T1-T9 behind the S row, cameras "Cam blends 1-5" and
"Cam blends 5-9". Every mark is soft (smooth falloff, low contrast) and moves in more than one direction.

  T1 bands x3      : three sets of wide soft dark bands, along x, y and z, each drifting its own way
  T2 warped bands  : dark bands bent by slow noise, sliding along a tilted 3D direction
  T3 radial bands  : soft dark rings breathing outward from the shape's middle, every direction at once
  T4 shimmer x3    : three big light sweeps from three directions at different speeds
  T5 radial glow   : a soft ring of light expanding from the middle every few seconds
  T6 light clouds  : patches of light drifting through the surface like moving clouds
  T7 soft veins    : S5's veins, wider and softer, in two noise layers drifting opposite ways
  T8 veins + light : soft dark veins with a light shimmer passing through them
  T9 bands + veins : crossing soft bands with faint veins over them

Run headless: S=<scratch dir> bpython this file (opens and re-saves /mnt/user-data/outputs/rage_battery_c.blend).
"""
import math, os
import bpy
from mathutils import Vector

S = os.environ["S"]
SRC = os.environ.get("SRC_BLEND", "/mnt/user-data/outputs/rage_battery_c.blend")
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene; col = sc.collection
R = math.radians
GREEN = (0.1, 1, 0.3)
DARK = (0.0, 0.10, 0.035)
LIGHT = (0.55, 1.0, 0.7)


class Builder:
    def __init__(self, m):
        self.nt = m.node_tree; self.N = self.nt.nodes; self.L = self.nt.links
        self.tc = self.N.new("ShaderNodeTexCoord")
        fr = self.N.new("ShaderNodeValue")
        d = fr.outputs[0].driver_add("default_value").driver; d.type = "SCRIPTED"; d.expression = "frame / 24"
        self.t = fr.outputs[0]

    def m(self, op, a, b=None):
        n = self.N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                self.L.new(x, n.inputs[i])
        return n.outputs[0]

    def dot(self, vec, direction):
        n = self.N.new("ShaderNodeVectorMath"); n.operation = "DOT_PRODUCT"
        self.L.new(vec, n.inputs[0]); n.inputs[1].default_value = direction
        return n.outputs["Value"]

    def pos(self):
        return self.tc.outputs["Object"]

    def centred_len(self, centre):
        sub = self.N.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"
        self.L.new(self.pos(), sub.inputs[0]); sub.inputs[1].default_value = centre
        ln = self.N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; self.L.new(sub.outputs[0], ln.inputs[0])
        return ln.outputs["Value"]

    def soft_wave(self, coord, freq, speed, sharp):
        """0..1 soft band: (0.5 + 0.5 sin(2pi(coord*freq - t*speed)))^sharp."""
        ph = self.m("SUBTRACT", self.m("MULTIPLY", coord, freq), self.m("MULTIPLY", self.t, speed))
        s = self.m("ADD", self.m("MULTIPLY", self.m("SINE", self.m("MULTIPLY", ph, 6.28318)), 0.5), 0.5)
        return self.m("POWER", s, sharp)

    def noise(self, scale, speed, w0=0.0, warp_vec=None):
        nz = self.N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
        nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 2.0
        self.L.new(warp_vec or self.pos(), nz.inputs["Vector"])
        self.L.new(self.m("ADD", self.m("MULTIPLY", self.t, speed), w0), nz.inputs["W"])
        return nz.outputs["Fac"]

    def veins(self, scale, speed, width, w0=0.0):
        n = self.noise(scale, speed, w0)
        d = self.m("ABSOLUTE", self.m("SUBTRACT", n, 0.5))
        # smooth falloff instead of a hard line: 1 at the vein, 0 by `width`
        mr = self.N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = width; mr.inputs["From Max"].default_value = 0.0
        mr.interpolation_type = "SMOOTHSTEP"; self.L.new(d, mr.inputs["Value"])
        return mr.outputs["Result"]

    def clamp01(self, x):
        c = self.N.new("ShaderNodeClamp"); self.L.new(x, c.inputs["Value"]); return c.outputs[0]


def shell_material(name, kind):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    b = Builder(m); N, L = b.N, b.L
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = GREEN + (1,); em.inputs["Strength"].default_value = 1.4
    tr = N.new("ShaderNodeBsdfTransparent")
    bf = b.m("MULTIPLY", lw.outputs["Facing"], 0.5)
    shell = N.new("ShaderNodeMixShader"); L.new(bf, shell.inputs[0]); L.new(tr.outputs[0], shell.inputs[1]); L.new(em.outputs[0], shell.inputs[2])
    p = b.pos()
    layers = []                                     # (factor 0..1, colour, opacity, glow)
    if kind == "T1":
        f = b.m("MAXIMUM", b.m("MAXIMUM", b.soft_wave(b.dot(p, (1, 0, 0)), 0.45, 0.10, 3.0),
                                          b.soft_wave(b.dot(p, (0, 1, 0)), 0.45, -0.08, 3.0)),
                b.soft_wave(b.dot(p, (0, 0, 1)), 0.4, 0.12, 3.0))
        layers.append((f, DARK, 0.42, 0.3))
    elif kind == "T2":
        nz = b.noise(0.9, 0.06)
        coord = b.m("ADD", b.dot(p, (0.6, 0.3, 0.75)), b.m("MULTIPLY", nz, 1.6))
        layers.append((b.soft_wave(coord, 0.5, 0.14, 4.0), DARK, 0.45, 0.3))
    elif kind == "T3":
        r = b.centred_len((1.0, 0.0, 1.2))
        layers.append((b.soft_wave(r, 0.6, 0.18, 3.5), DARK, 0.45, 0.3))
    elif kind == "T4":
        f = b.m("MAXIMUM", b.m("MAXIMUM", b.soft_wave(b.dot(p, (0.8, 0, 0.6)), 0.18, 0.07, 14.0),
                                          b.soft_wave(b.dot(p, (-0.5, 0.3, 0.8)), 0.15, 0.05, 14.0)),
                b.soft_wave(b.dot(p, (0.2, 0.9, -0.4)), 0.2, 0.09, 14.0))
        layers.append((f, LIGHT, 0.32, 2.2))
    elif kind == "T5":
        r = b.centred_len((1.0, 0.0, 1.2))
        layers.append((b.soft_wave(r, 0.25, 0.12, 12.0), LIGHT, 0.35, 2.4))
    elif kind == "T6":
        n = b.noise(0.8, 0.08)
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.55; mr.inputs["From Max"].default_value = 0.75
        mr.interpolation_type = "SMOOTHSTEP"; L.new(n, mr.inputs["Value"])
        layers.append((mr.outputs["Result"], LIGHT, 0.3, 2.0))
    elif kind == "T7":
        f = b.m("MAXIMUM", b.veins(1.3, 0.10, 0.09), b.veins(0.8, -0.07, 0.07, 5.0))
        layers.append((f, DARK, 0.5, 0.4))
    elif kind == "T8":
        layers.append((b.veins(1.2, 0.09, 0.08), DARK, 0.48, 0.4))
        layers.append((b.soft_wave(b.dot(p, (0.7, 0.2, 0.7)), 0.18, 0.08, 12.0), LIGHT, 0.3, 2.2))
    else:  # T9
        f = b.m("MAXIMUM", b.soft_wave(b.dot(p, (1, 0, 0.3)), 0.4, 0.09, 3.0), b.soft_wave(b.dot(p, (-0.3, 0.2, 1)), 0.4, -0.07, 3.0))
        layers.append((f, DARK, 0.36, 0.3))
        layers.append((b.veins(1.4, 0.08, 0.06), DARK, 0.3, 0.4))
    cur = shell.outputs[0]
    for fac, rgb, alpha, glow in layers:
        mk = N.new("ShaderNodeEmission"); mk.inputs["Color"].default_value = rgb + (1,); mk.inputs["Strength"].default_value = glow
        t2 = N.new("ShaderNodeBsdfTransparent")
        mm = N.new("ShaderNodeMixShader"); mm.inputs[0].default_value = alpha
        L.new(t2.outputs[0], mm.inputs[1]); L.new(mk.outputs[0], mm.inputs[2])
        layer = N.new("ShaderNodeMixShader"); L.new(b.clamp01(fac), layer.inputs[0])
        L.new(cur, layer.inputs[1]); L.new(mm.outputs[0], layer.inputs[2])
        cur = layer.outputs[0]
    out = N.new("ShaderNodeOutputMaterial"); L.new(cur, out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


src = bpy.data.objects["Construct barrier (green)"]
OPTS = [("T1", "T1  bands x3"), ("T2", "T2  warped bands"), ("T3", "T3  radial bands"), ("T4", "T4  shimmer x3"),
        ("T5", "T5  radial glow"), ("T6", "T6  light clouds"), ("T7", "T7  soft veins"), ("T8", "T8  veins + light"),
        ("T9", "T9  bands + veins")]
for i, (k, title) in enumerate(OPTS):
    old = bpy.data.objects.get(f"Barrier blend {k}")
    if old:
        bpy.data.objects.remove(old)
    o = src.copy(); o.data = src.data.copy(); col.objects.link(o)
    o.name = f"Barrier blend {k}"
    o.location = Vector((40.0 + i * 4.2, 22.0, 0))
    o.data.materials.clear(); o.data.materials.append(shell_material("barrier blend " + k, k))
    cu = bpy.data.curves.new("lab " + k, "FONT"); cu.body = title; cu.size = 0.24; cu.align_x = "CENTER"
    lo = bpy.data.objects.new("Label " + k, cu); lo.location = o.location + Vector((1.0, -0.8, 3.5)); lo.rotation_euler = (R(90), 0, 0)
    lm = bpy.data.materials.new("lab " + k); lm.use_nodes = True
    lp = lm.node_tree.nodes.get("Principled BSDF"); lp.inputs["Emission Color"].default_value = (0.8, 1, 0.85, 1); lp.inputs["Emission Strength"].default_value = 2
    cu.materials.append(lm); col.objects.link(lo)


def cam(name, x):
    cd = bpy.data.cameras.new(name); cd.lens = 24
    c = bpy.data.objects.new(name, cd); col.objects.link(c)
    c.location = (x, 10.5, 3.2); c.rotation_euler = (Vector((x, 22.0, 1.3)) - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


for nm in ("Cam blends 1-5", "Cam blends 5-9"):
    o = bpy.data.objects.get(nm)
    if o:
        bpy.data.objects.remove(o)
c1 = cam("Cam blends 1-5", 49.4); c2 = cam("Cam blends 5-9", 66.2)
fo = bpy.data.objects.get("Battery floor")
if fo:
    fo.scale = (3.0, 2.2, 1.0); fo.location = (40, 12, fo.location.z)
bpy.ops.wm.save_as_mainfile(filepath="/mnt/user-data/outputs/rage_battery_c.blend", compress=True)
if os.environ.get("RENDER"):
    sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.render.resolution_x = 1100; sc.render.resolution_y = 420
    for f in range(1, 73):
        sc.frame_set(f)
    for c, n in ((c1, "blends_a"), (c2, "blends_b")):
        sc.camera = c; sc.render.filepath = f"{S}/{n}.png"; bpy.ops.render.render(write_still=True)
