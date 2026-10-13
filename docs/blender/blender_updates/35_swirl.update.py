# Pass 35: the charging light J described, on L1 and L2. Not one pulse any more:
#  - a ball of light in the middle, at the bulge behind the port, that swells with the charge: many
#    greens with a yellow-white heart
#  - light swirling round the centre (spirals turning round the body)
#  - flares running out of the centre up and down through the ribbed levels, in every direction
# All on the Charge slider (dark at rest), the same light the game will get as baked frames.
# Stills to renders/: 25%, 50%, 75%, full, and two moments a quarter second apart at full.
import os, math
import bpy
from mathutils import Vector

scene = bpy.context.scene
ctl = bpy.data.objects["Lantern Controls"]
PZ = 11.75          # the bulge centre, model units (the object space of the lantern meshes)


def mat_new(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree.nodes, m.node_tree.links


def swirl_material(name, metal, strength):
    m, N, L = mat_new(name)

    def mth(op, a, b=None, clamp=False):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, s in enumerate((a, b)):
            if s is None:
                continue
            if isinstance(s, (int, float)):
                n.inputs[i].default_value = s
            else:
                L.new(s, n.inputs[i])
        return n.outputs[0]

    def drv(expr, charge=True):
        v = N.new("ShaderNodeValue")
        d = v.outputs[0].driver_add("default_value").driver
        d.type = "SCRIPTED"
        if charge:
            var = d.variables.new(); var.name = "c"; var.type = "SINGLE_PROP"
            var.targets[0].id_type = "OBJECT"; var.targets[0].id = ctl; var.targets[0].data_path = '["charge"]'
        d.expression = expr
        return v.outputs[0]

    out = N.new("ShaderNodeOutputMaterial")
    col = N.new("ShaderNodeAttribute"); col.attribute_name = "col"
    gw = N.new("ShaderNodeAttribute"); gw.attribute_name = "glow"
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    x, y, z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    t = drv(f"frame / {scene.render.fps}", charge=False)
    c = drv("min(c, 1.25)")
    dz = mth("SUBTRACT", z, PZ)
    adz = mth("ABSOLUTE", dz)
    ang = mth("ARCTAN2", y, x)
    rad = mth("SQRT", mth("ADD", mth("MULTIPLY", x, x), mth("MULTIPLY", y, y)))
    # the ball: brightest at the bulge centre, its reach growing with the charge
    reach = mth("ADD", 2.0, mth("MULTIPLY", c, 6.5))
    d3 = mth("SQRT", mth("ADD", mth("MULTIPLY", dz, dz), mth("MULTIPLY", mth("MULTIPLY", rad, rad), 0.25)))
    ball = mth("EXPONENT", mth("MULTIPLY", -1.0, mth("POWER", mth("DIVIDE", d3, reach), 2.0)))
    # the swirl: spirals turning round the body, twisting with height
    sw_phase = mth("ADD", mth("MULTIPLY", ang, 3.0), mth("ADD", mth("MULTIPLY", dz, 0.55), mth("MULTIPLY", t, 2.6)))
    swirl = mth("POWER", mth("MULTIPLY", mth("ADD", mth("SINE", sw_phase), 1.0), 0.5), 3.0)
    # flares: waves leaving the centre up and down, broken up round the body
    fl_phase = mth("SUBTRACT", mth("MULTIPLY", adz, 0.9), mth("MULTIPLY", t, 5.0))
    flare = mth("POWER", mth("MULTIPLY", mth("ADD", mth("SINE", fl_phase), 1.0), 0.5), 6.0)
    brk = N.new("ShaderNodeTexNoise"); brk.noise_dimensions = "4D"; brk.inputs["Scale"].default_value = 0.35
    L.new(tc.outputs["Object"], brk.inputs["Vector"]); L.new(mth("MULTIPLY", t, 0.6), brk.inputs["W"])
    flare = mth("MULTIPLY", flare, mth("POWER", brk.outputs["Fac"], 2.0))
    flare = mth("MULTIPLY", flare, mth("EXPONENT", mth("MULTIPLY", -1.0, mth("DIVIDE", adz, mth("ADD", 1.5, mth("MULTIPLY", c, 7.0))))))
    # the light: the ball, plus swirl and flares that need the charge to reach them
    light = mth("ADD", mth("MULTIPLY", ball, 1.2),
                mth("MULTIPLY", mth("ADD", mth("MULTIPLY", swirl, 0.45), mth("MULTIPLY", flare, 1.3)), mth("ADD", 0.2, ball)))
    light = mth("MULTIPLY", light, mth("ADD", 0.35, gw.outputs["Fac"]))          # the pixel's own glow weight
    # many shades of green, deep at the fringe to a yellow-white heart
    ramp = N.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.0, 0.10, 0.03, 1)
    els[1].position, els[1].color = 1.0, (1.0, 1.0, 0.55, 1)
    for pos, cc in ((0.2, (0.0, 0.35, 0.08, 1)), (0.42, (0.02, 0.75, 0.18, 1)), (0.62, (0.18, 1.0, 0.3, 1)),
                    (0.8, (0.6, 1.0, 0.35, 1))):
        e = els.new(pos); e.color = cc
    jit = N.new("ShaderNodeTexWhiteNoise"); jit.noise_dimensions = "3D"
    snap = N.new("ShaderNodeVectorMath"); snap.operation = "SNAP"; snap.inputs[1].default_value = (0.25, 0.25, 0.25)
    L.new(tc.outputs["Object"], snap.inputs[0]); L.new(snap.outputs["Vector"], jit.inputs["Vector"])
    shade = mth("ADD", mth("MULTIPLY", light, 0.85), mth("MULTIPLY", jit.outputs["Value"], 0.15), clamp=True)
    L.new(shade, ramp.inputs["Fac"])
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(col.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.9 if metal else 0.0
    b.inputs["Roughness"].default_value = 0.28 if metal else 0.18
    b.inputs["Coat Weight"].default_value = 0.0 if metal else 0.9
    L.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    cc = mth("MULTIPLY", mth("MULTIPLY", c, c), strength)
    L.new(mth("MULTIPLY", mth("MULTIPLY", light, light), cc), b.inputs["Emission Strength"])
    L.new(b.outputs[0], out.inputs["Surface"])
    return m


body = swirl_material("dark_body_swirl", False, 2.6)
crack = swirl_material("dark_crack_swirl", True, 4.0)
for v in ("L1", "L2"):
    ob = bpy.data.objects.get(f"Dark {v}")
    if ob is None:
        continue
    ms = ob.data.materials
    for i, m in enumerate(ms):
        if m and m.name.startswith("dark_body"):
            ms[i] = body
        elif m and m.name.startswith("dark_crack"):
            ms[i] = crack

out = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera, ctl["charge"])
scene.camera = bpy.data.objects["Dark Camera"]
scene.render.resolution_percentage = 60
anim = ctl.animation_data.action if ctl.animation_data else None
if ctl.animation_data:
    ctl.animation_data.action = None          # hold the charge by hand for the stills
for tag, chg, frame in (("25", 0.25, 100), ("50", 0.5, 100), ("75", 0.75, 100), ("full", 1.0, 100),
                        ("full_b", 1.0, 106)):
    ctl["charge"] = chg
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(out, f"swirl_{tag}.png")
    bpy.ops.render.render(write_still=True)
if anim:
    ctl.animation_data.action = anim
ctl["charge"] = keep[4]
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
