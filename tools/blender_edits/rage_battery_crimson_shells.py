import bpy, bmesh, math, os
from mathutils import Vector
S = os.environ["S"]
bpy.ops.wm.open_mainfile(filepath=S + "/t84/rage_battery_c_diamond.blend")
sc = bpy.context.scene; col = sc.collection
R = math.radians

# ---- 1. crimson diamond cladding on all three batteries --------------------------------------------------
img = bpy.data.images.get("diamond_c1.png") or bpy.data.images.load(S + "/diamond_c1.png")
img.pack()
for k, dark in ((0, 0.55), (1, 1.0), (3, 1.15)):
    m = bpy.data.materials.get(f"battery2 kind {k}")
    nt = m.node_tree; N, L = nt.nodes, nt.links
    p = N.get("Principled BSDF")
    for n in [n for n in N if n.type in ("ATTRIBUTE",)]:
        N.remove(n)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 16, 1 / 16, 1 / 16)          # the battery's object space is model px: 16 = 1 block
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    t = N.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Closest"; t.projection = "BOX"; t.projection_blend = 0.0
    L.new(mp.outputs["Vector"], t.inputs["Vector"])
    br = N.new("ShaderNodeBrightContrast"); br.inputs["Bright"].default_value = 0.0
    mul = N.new("ShaderNodeMixRGB"); mul.blend_type = "MULTIPLY"; mul.inputs["Fac"].default_value = 1.0
    mul.inputs["Color2"].default_value = (dark, dark, dark, 1)
    L.new(t.outputs["Color"], mul.inputs["Color1"]); L.new(mul.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.22
    p.inputs["Specular IOR Level"].default_value = 0.7
    p.inputs["Coat Weight"].default_value = 0.35

# ---- 2. passing-surface options for the particle barrier shell ----------------------------------------------
src = bpy.data.objects["Construct barrier (green)"]
GREEN = (0.1, 1, 0.3)


def shell_material(name, kind):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; N.clear()
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    fr = N.new("ShaderNodeValue"); d = fr.outputs[0].driver_add("default_value").driver; d.type = "SCRIPTED"; d.expression = "frame / 24"
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = GREEN + (1,); em.inputs["Strength"].default_value = 1.4
    tr = N.new("ShaderNodeBsdfTransparent")
    base_f = N.new("ShaderNodeMath"); base_f.operation = "MULTIPLY"; base_f.inputs[1].default_value = 0.5
    L.new(lw.outputs["Facing"], base_f.inputs[0])
    shell = N.new("ShaderNodeMixShader"); L.new(base_f.outputs[0], shell.inputs[0]); L.new(tr.outputs[0], shell.inputs[1]); L.new(em.outputs[0], shell.inputs[2])

    def math(op, a, b=None, val=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    t = fr.outputs[0]
    if kind == "S1":       # thin black lines rising slowly
        ph = math("FRACT", math("SUBTRACT", math("MULTIPLY", sep.outputs["Z"], 4.0), math("MULTIPLY", t, 0.6)))
        line = math("LESS_THAN", ph, 0.08)
        mark_col, mark_alpha, mark_glow = (0, 0, 0), 0.92, 0.0
    elif kind == "S2":     # wide soft dark-green bands sweeping on the diagonal
        ph = math("FRACT", math("SUBTRACT", math("MULTIPLY", math("ADD", sep.outputs["X"], sep.outputs["Z"]), 0.8), math("MULTIPLY", t, 0.25)))
        line = math("MULTIPLY", math("SINE", math("MULTIPLY", ph, 3.14159)), 1.0)
        line = math("POWER", line, 6.0)
        mark_col, mark_alpha, mark_glow = (0.0, 0.12, 0.04), 0.7, 0.3
    elif kind == "S3":     # the block grid in black, darkening as a band passes up through it
        gx = math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", math("FRACT", sep.outputs["X"]), 0.5)), 0.03)
        gz = math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", math("FRACT", sep.outputs["Z"]), 0.5)), 0.03)
        grid = math("MAXIMUM", gx, gz)
        band = math("POWER", math("SINE", math("MULTIPLY", math("FRACT", math("SUBTRACT", math("MULTIPLY", sep.outputs["Z"], 0.33), math("MULTIPLY", t, 0.2))), 3.14159)), 4.0)
        line = math("MULTIPLY", grid, math("ADD", math("MULTIPLY", band, 0.8), 0.15))
        mark_col, mark_alpha, mark_glow = (0, 0, 0), 0.85, 0.0
    elif kind == "S4":     # a lighter shimmer band passing over, no lines
        ph = math("FRACT", math("SUBTRACT", math("MULTIPLY", math("ADD", sep.outputs["Z"], math("MULTIPLY", sep.outputs["X"], 0.4)), 0.35), math("MULTIPLY", t, 0.22)))
        line = math("POWER", math("SINE", math("MULTIPLY", ph, 3.14159)), 10.0)
        mark_col, mark_alpha, mark_glow = (0.5, 1.0, 0.65), 0.35, 2.5
    elif kind == "S6":     # J: "almost glinting" - a thin bright glint line racing across now and then
        ph = math("FRACT", math("SUBTRACT", math("MULTIPLY", math("ADD", sep.outputs["X"], math("MULTIPLY", sep.outputs["Z"], 0.6)), 0.25), math("MULTIPLY", t, 0.45)))
        line = math("POWER", math("SINE", math("MULTIPLY", ph, 3.14159)), 400.0)
        mark_col, mark_alpha, mark_glow = (0.85, 1.0, 0.9), 0.55, 5.0
    else:                  # S5: dark-green veins drifting through, like smoke under the surface
        nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 1.6
        nz.inputs["Detail"].default_value = 3.0
        L.new(tc.outputs["Object"], nz.inputs["Vector"]); L.new(math("MULTIPLY", t, 0.12), nz.inputs["W"])
        line = math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", nz.outputs["Fac"], 0.5)), 0.035)
        mark_col, mark_alpha, mark_glow = (0.0, 0.18, 0.05), 0.8, 0.6
    mk = N.new("ShaderNodeEmission"); mk.inputs["Color"].default_value = mark_col + (1,); mk.inputs["Strength"].default_value = mark_glow
    tr2 = N.new("ShaderNodeBsdfTransparent")
    mk_mix = N.new("ShaderNodeMixShader"); mk_mix.inputs[0].default_value = mark_alpha
    L.new(tr2.outputs[0], mk_mix.inputs[1]); L.new(mk.outputs[0], mk_mix.inputs[2])
    final = N.new("ShaderNodeMixShader"); L.new(line, final.inputs[0])
    L.new(shell.outputs[0], final.inputs[1]); L.new(mk_mix.outputs[0], final.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(final.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


OPTS = [("S1", "S1  thin black lines rising"), ("S2", "S2  dark-green bands sweeping"), ("S3", "S3  black block grid, a band passing"),
        ("S4", "S4  light shimmer passing, no lines"), ("S5", "S5  dark-green veins drifting"), ("S6", "S6  almost glinting: a thin glint racing over")]
for i, (k, title) in enumerate(OPTS):
    o = src.copy(); o.data = src.data.copy(); col.objects.link(o)
    o.name = f"Barrier option {k}"
    o.location = Vector((40.0 + i * 4.2, 0, 0))
    o.data.materials.clear(); o.data.materials.append(shell_material("barrier shell " + k, k))
    cu = bpy.data.curves.new("lab " + k, "FONT"); cu.body = title; cu.size = 0.2; cu.align_x = "CENTER"
    lo = bpy.data.objects.new("Label " + k, cu); lo.location = o.location + Vector((1.0, -0.8, 3.5)); lo.rotation_euler = (R(90), 0, 0)
    lm = bpy.data.materials.new("lab " + k); lm.use_nodes = True
    lp = lm.node_tree.nodes.get("Principled BSDF"); lp.inputs["Emission Color"].default_value = (0.8, 1, 0.85, 1); lp.inputs["Emission Strength"].default_value = 2
    cu.materials.append(lm); col.objects.link(lo)
cd = bpy.data.cameras.new("Cam shells"); cd.lens = 24
cam = bpy.data.objects.new("Cam shells", cd); col.objects.link(cam)
cam.location = (52.8, -15.0, 3.4); cam.rotation_euler = (Vector((52.8, 0, 1.3)) - cam.location).to_track_quat("-Z", "Y").to_euler()
fo = bpy.data.objects.get("Battery floor")
if fo:
    fo.scale = (2.2, 1.0, 1.0); fo.location.x = 30
bpy.ops.wm.save_as_mainfile(filepath="/mnt/user-data/outputs/rage_battery_c.blend", compress=True)
# check renders
sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.render.resolution_x = 1100; sc.render.resolution_y = 420
for f in range(1, 101):
    sc.frame_set(f)
for camn, outn in (("Cam shells", "shells"),):
    sc.camera = bpy.data.objects[camn]; sc.render.filepath = f"{S}/{outn}.png"; bpy.ops.render.render(write_still=True)
